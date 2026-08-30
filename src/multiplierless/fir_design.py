"""CLI for multiplierless FIR filter design — JSON-in, CSD-out.

Reads filter specifications from a JSON file, runs the ellipsoid-method
optimization with CSD-quantized coefficients, and outputs:
  - CSD-quantized impulse response coefficients (numeric + CSD string)
  - Optionally, a synthesizable Verilog module via csdigit.csd_multiplier
"""

import json
import sys
from typing import Callable, Optional

import numpy as np
from csdigit.csd import to_csdnnz
from csdigit.csd_multiplier import generate_csd_multipliers
from ellalgo.cutting_plane import Options, cutting_plane_optim_q
from ellalgo.ell import Ell

from multiplierless.lowpass_oracle import create_lowpass_case_params
from multiplierless.lowpass_oracle_q import LowpassOracleQ, csd_quantize
from multiplierless.spectral_fact import spectral_fact_select

# ============================================================
#  Internal helpers: transpose-form Verilog generator
# ============================================================


def _build_range_expr(csd: str, start: int, length: int, max_power: int) -> str:
    """Build a flat Verilog expression for csd[start:start+length]."""
    parts: list[str] = []
    for i in range(start, start + length):
        power = max_power - i
        ch = csd[i]
        if ch == "+":
            parts.append(f"x_shift{power}")
        elif ch == "-":
            parts.append(f"-x_shift{power}")
    if not parts:
        return ""
    result = parts[0]
    for part in parts[1:]:
        if part.startswith("-"):
            result += " - " + part[1:]
        else:
            result += " + " + part
    return result


def _find_pattern_occurrences(csd: str, pattern: str) -> list[int]:
    """Find all non-overlapping positions of pattern in csd."""
    positions: list[int] = []
    pos = 0
    while True:
        pos = csd.find(pattern, pos)
        if pos == -1:
            break
        positions.append(pos)
        pos += len(pattern)
    return positions


def _find_cross_patterns(
    csd_list: list[str], min_nnz: int = 2
) -> dict[str, list[tuple[int, int]]]:
    """Find substrings (NNZ >= min_nnz) appearing in >= 2 CSD strings."""
    patterns: dict[str, list[tuple[int, int]]] = {}
    for ci, csd in enumerate(csd_list):
        n = len(csd)
        for i in range(n):
            for j in range(i + 2, n + 1):
                sub = csd[i:j]
                nnz = sub.count("+") + sub.count("-")
                if nnz >= min_nnz:
                    patterns.setdefault(sub, []).append((ci, i))
    return {
        sub: occ for sub, occ in patterns.items() if len({ci for ci, _ in occ}) >= 2
    }


def _build_coeff_expr(
    csd: str,
    max_power: int,
    pattern: str | None,
    base_pos: int,
    cse_name: str,
) -> str:
    """Build a coefficient expression using CSE wire + flat gap terms."""
    if pattern is None:
        return _build_range_expr(csd, 0, len(csd), max_power)

    parts: list[str] = []
    cur = 0
    positions = _find_pattern_occurrences(csd, pattern)
    for pos in positions:
        if pos > cur:
            gap = _build_range_expr(csd, cur, pos - cur, max_power)
            if gap:
                parts.append(gap)
        shift = pos - base_pos
        if shift == 0:
            parts.append(cse_name)
        else:
            parts.append(f"({cse_name} >>> {shift})")
        cur = pos + len(pattern)
    if cur < len(csd):
        gap = _build_range_expr(csd, cur, len(csd) - cur, max_power)
        if gap:
            parts.append(gap)
    if not parts:
        return ""
    return " + ".join(parts)


def _generate_transpose_verilog(
    coeffs: list[tuple[str, str, int, int]],
    module_name: str = "fir_filter",
) -> str:
    """Generate a transpose-form FIR filter Verilog module with cross-CSE."""
    if not coeffs:
        raise ValueError("At least one coefficient is required")

    input_width = coeffs[0][2]
    max_power = coeffs[0][3]
    N = len(coeffs)
    output_width = input_width + max_power

    for name, csd, iw, mp in coeffs:
        if iw != input_width or mp != max_power:
            raise ValueError(
                "All coefficients must share input_width and max_power "
                f"for transpose form. Got ({iw},{mp}) for '{name}'."
            )
        if len(csd) != max_power + 1:
            raise ValueError(
                f"CSD length {len(csd)} doesn't match max_power={max_power} "
                f"for coefficient '{name}'"
            )
        if not all(ch in "+-0" for ch in csd):
            raise ValueError(
                f"CSD string '{csd}' for '{name}' can only contain '+', '-', or '0'"
            )

    all_powers: set[int] = set()
    for _, csd, _, _ in coeffs:
        for idx, ch in enumerate(csd):
            if ch != "0":
                all_powers.add(max_power - idx)
    all_powers_sorted = sorted(all_powers, reverse=True)

    csd_strings = [csd for _, csd, _, _ in coeffs]
    cross = _find_cross_patterns(csd_strings)

    best_pattern: str | None = None
    best_occurrences: list[tuple[int, int]] = []
    if cross:

        def _score(item):
            sub, occ = item
            nnz = sub.count("+") + sub.count("-")
            return (nnz - 1) * (len(occ) - 1)

        best_pattern, best_occurrences = max(cross.items(), key=_score)

    cse_base_pos = 0
    if best_pattern and best_occurrences:
        cse_base_pos = min(pos for _, pos in best_occurrences)
    cse_coeffs = {ci for ci, _ in best_occurrences}

    v = f"\nmodule {module_name} ("
    v += "\n    input clk,"
    v += "\n    input rst_n,"
    v += f"\n    input signed [{input_width - 1}:0] x,"
    v += f"\n    output signed [{output_width - 1}:0] y"
    v += "\n);"

    if all_powers:
        v += "\n\n    // Shifted versions of input"
        for p in all_powers_sorted:
            v += f"\n    wire signed [{output_width - 1}:0] x_shift{p} = x <<< {p};"

    if best_pattern:
        cse_expr = _build_range_expr(
            best_pattern, 0, len(best_pattern), max_power - cse_base_pos
        )
        v += f'\n\n    // Cross-CSE: shared pattern "{best_pattern}"'
        v += f"\n    wire signed [{output_width - 1}:0] _cse_0 = {cse_expr};"

    v += "\n\n    // Transpose-form pipeline registers"
    for idx in range(N):
        v += f"\n    reg signed [{output_width - 1}:0] sum{idx};"

    v += "\n\n    always @(posedge clk or negedge rst_n) begin"
    v += "\n        if (!rst_n) begin"
    for idx in range(N):
        v += f"\n            sum{idx} <= 0;"
    v += "\n        end else begin"

    for idx in range(N):
        coeff_idx = N - 1 - idx
        _name, csd_str, _iw, _mp = coeffs[coeff_idx]

        if best_pattern and coeff_idx in cse_coeffs:
            expr = _build_coeff_expr(
                csd_str, max_power, best_pattern, cse_base_pos, "_cse_0"
            )
        else:
            expr = _build_coeff_expr(csd_str, max_power, None, 0, "")

        if idx == 0:
            if not expr:
                v += "\n            sum0 <= 0;"
            else:
                v += f"\n            sum0 <= {expr};"
        else:
            if not expr:
                v += f"\n            sum{idx} <= sum{idx - 1};"
            else:
                v += f"\n            sum{idx} <= sum{idx - 1} + {expr};"

    v += "\n        end"
    v += "\n    end"

    v += f"\n\n    assign y = sum{N - 1};"
    v += "\nendmodule\n"
    return v


def _fix_verilog_ports(verilog: str) -> str:
    """Fix missing commas between port declarations (known csdigit issue)."""
    lines = verilog.splitlines(keepends=True)
    port_lines: list[int] = []
    module_start = -1
    paren_end = -1
    for i, line in enumerate(lines):
        if line.strip().startswith("module ") and "(" in line:
            module_start = i
        if module_start >= 0 and paren_end < 0:
            if ");" in line:
                paren_end = i
            elif module_start != i:
                port_lines.append(i)
    # Add commas to all port lines except the last
    for idx, pi in enumerate(port_lines):
        line = lines[pi]
        stripped = line.rstrip()
        code_part = stripped.split("//")[0].rstrip()
        if not code_part.endswith(",") and idx < len(port_lines) - 1:
            if "//" in stripped:
                ci = stripped.index("//")
                lines[pi] = code_part + ",\n" + stripped[ci:] + "\n"
            else:
                lines[pi] = code_part + ",\n"
    return "".join(lines)


def _generate_direct_verilog(
    coeffs: list[tuple[str, str, int, int]], module_name: str
) -> str:
    """Generate a direct-form FIR Verilog module via csdigit."""
    return _fix_verilog_ports(generate_csd_multipliers(coeffs, module_name))


# Strategy registry: verilog form -> generator (transpose / direct)
VerilogGenerator = Callable[[list[tuple[str, str, int, int]], str], str]
VERILOG_GENERATORS: dict[str, VerilogGenerator] = {
    "transpose": _generate_transpose_verilog,
    "direct": _generate_direct_verilog,
}


# experiment/lowpass_oracle is not a package module; import by path if needed,
# but we use the parameterized factory from multiplierless.lowpass_oracle.

DEFAULTS = {
    "filter_order": 32,
    "passband_edge": 0.12,
    "stopband_edge": 0.20,
    "passband_ripple": 0.125,
    "stopband_attenuation": 0.125,
    "csd_nnz": 7,
    "discretization_factor": 15,
    "max_iters": 50000,
    "tolerance": 1e-14,
    "ellipsoid_radius": 40.0,
    "parallel_cut": True,
}


def main(argv: Optional[list[str]] = None) -> int:
    """CLI entry point for multiplierless FIR filter design.

    Reads filter specifications from a JSON file, runs ellipsoid-method
    optimization with CSD-quantized coefficients, and outputs results
    as JSON to stdout.

    Args:
        argv: Command-line arguments (list of strings). If None, uses
            sys.argv[1:].

    Returns:
        Exit code — 0 on success, 1 on failure.
    """
    if argv is None:
        argv = sys.argv[1:]

    if len(argv) < 1:
        print(
            "Usage: python -m multiplierless.fir_design <filter_spec.json>",
            file=sys.stderr,
        )
        return 1

    with open(argv[0]) as f:
        spec = json.load(f)

    N = spec.get("filter_order", DEFAULTS["filter_order"])
    csd_nnz = spec.get("csd_nnz", DEFAULTS["csd_nnz"])

    oracle = create_lowpass_case_params(
        N,
        spec.get("passband_edge", DEFAULTS["passband_edge"]),
        spec.get("stopband_edge", DEFAULTS["stopband_edge"]),
        spec.get("passband_ripple", DEFAULTS["passband_ripple"]),
        spec.get("stopband_attenuation", DEFAULTS["stopband_attenuation"]),
        spec.get("discretization_factor", DEFAULTS["discretization_factor"]),
    )

    omega = LowpassOracleQ(csd_nnz, oracle)
    Spsq = oracle.sp_sq

    r0 = np.zeros(N)
    E = Ell(
        spec.get("ellipsoid_radius", DEFAULTS["ellipsoid_radius"]),
        r0,
    )
    E.helper.use_parallel_cut = spec.get("parallel_cut", DEFAULTS["parallel_cut"])

    opts = Options()
    opts.max_iters = spec.get("max_iters", DEFAULTS["max_iters"])
    opts.tolerance = spec.get("tolerance", DEFAULTS["tolerance"])

    r, _, num_iters = cutting_plane_optim_q(omega, E, Spsq, opts)

    if r is None:
        print(
            f"Optimization failed — no feasible solution after {num_iters} iterations.",
            file=sys.stderr,
        )
        return 1

    method = spec.get("spectral_method", "fft")
    tol = spec.get("root_tolerance", 1e-8)
    h = spectral_fact_select(r, method, tol)
    csd_strings = [to_csdnnz(hi, csd_nnz) for hi in h]
    coefficients = []
    for i, (hi, csd_str) in enumerate(zip(h, csd_strings)):
        coefficients.append(
            {"index": i, "value": csd_quantize(float(hi), csd_nnz), "csd": csd_str}
        )

    output = {
        "filter_order": N,
        "csd_nnz": csd_nnz,
        "iterations": num_iters,
        "spectral_method": method,
        "coefficients": coefficients,
    }

    if "verilog" in spec:
        vl = spec["verilog"]
        input_width = vl.get("input_width", 16)
        module_name = vl.get("module_name", "fir_filter")
        verilog_form = vl.get("form", "transpose")

        max_len = max(len(s) for s in csd_strings)
        max_power = max_len - 1

        coeff_tuples = []
        for i, csd_str in enumerate(csd_strings):
            raw = csd_str.replace(".", "")
            while len(raw) < max_len:
                raw = "0" + raw
            coeff_tuples.append((f"h{i}", raw, input_width, max_power))

        generator = VERILOG_GENERATORS.get(verilog_form)
        if generator is None:
            print(f"Unknown verilog form: {verilog_form}", file=sys.stderr)
            return 1
        output["verilog"] = generator(coeff_tuples, module_name)

    json.dump(output, sys.stdout, indent=2)
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
