"""CLI for multiplierless FIR filter design — JSON-in, CSD-out.

Reads filter specifications from a JSON file, runs the ellipsoid-method
optimization with CSD-quantized coefficients, and outputs:
  - CSD-quantized impulse response coefficients (numeric + CSD string)
  - Optionally, a synthesizable transpose- or direct-form Verilog module
"""

import argparse
import json
import re
import sys
from math import ceil, log2
from pathlib import Path
from typing import Callable, Optional

import numpy as np
from csdigit.csd_multiplier import generate_csd_multipliers
from ellalgo.cutting_plane import Options, cutting_plane_optim_q
from ellalgo.ell import Ell

from .lowpass_oracle import create_lowpass_case_params
from .lowpass_oracle_q import LowpassOracleQ, csd_quantize_parts
from .spectral_fact import SpectralMethod, spectral_fact_select

# ============================================================
#  Fixed-point helpers (shared by JSON output and Verilog)
# ============================================================


def format_csd(parts: list[tuple[int, int]]) -> str:
    """Render greedy-CSD digits as an exact ``int.frac`` string.

    A decimal point and at least one fractional digit are always emitted, so
    the output schema holds even for values needing no fraction (0 or ±1).
    """
    if not parts:
        return "0."
    digits = {exp: ("+" if sign > 0 else "-") for exp, sign in parts}
    max_exp = max(max(exp for exp, _ in parts), 0)
    min_exp = min(min(exp for exp, _ in parts), -1)
    int_part = "".join(digits.get(exp, "0") for exp in range(max_exp, -1, -1))
    frac_part = "".join(digits.get(exp, "0") for exp in range(-1, min_exp - 1, -1))
    return f"{int_part}.{frac_part}"


def csd_to_float(csd: str) -> float:
    """Exact numeric value of a CSD string (decimal point optional)."""
    int_part, _, frac_part = csd.partition(".")
    value = 0.0
    for i, ch in enumerate(int_part):
        exp = len(int_part) - 1 - i
        if ch == "+":
            value += 2.0**exp
        elif ch == "-":
            value -= 2.0**exp
    for i, ch in enumerate(frac_part):
        exp = -(i + 1)
        if ch == "+":
            value += 2.0**exp
        elif ch == "-":
            value -= 2.0**exp
    return value


def csd_coeffs_to_fixed(csd_list: list[str]) -> tuple[list[str], int]:
    """Right-align fractional digits to one shared fixed-point scale.

    Returns one integer-digit string per input, all the same length, plus the
    exponent of their most significant digit.  Each string represents
    ``round(value * 2**max_power)``, giving every coefficient the same units.
    """
    split = []
    for csd in csd_list:
        int_part, _, frac_part = csd.partition(".")
        split.append((int_part, frac_part))
    int_width = max(len(int_part) for int_part, _ in split)
    frac_width = max(len(frac_part) for _, frac_part in split)
    raws = [
        int_part.rjust(int_width, "0") + frac_part.ljust(frac_width, "0")
        for int_part, frac_part in split
    ]
    return raws, int_width + frac_width - 1


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
    # Summing N products can grow by log2(N) bits beyond a single product.
    headroom = int(ceil(log2(N))) if N > 1 else 0
    output_width = input_width + max_power + headroom

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


def _fix_output_wires(verilog: str, port_names: set[str]) -> str:
    """Turn port redeclarations from csdigit into continuous assignments."""
    fixed: list[str] = []
    for line in verilog.splitlines(keepends=True):
        match = re.match(r"^(\s*)wire signed \[[^\]]*\] (\w+) = (.*);\s*$", line)
        if match and match.group(2) in port_names:
            fixed.append(
                f"{match.group(1)}assign {match.group(2)} = {match.group(3)};\n"
            )
        else:
            fixed.append(line)
    return "".join(fixed)


def _generate_direct_verilog(
    coeffs: list[tuple[str, str, int, int]], module_name: str
) -> str:
    """Generate a direct-form FIR Verilog module via csdigit."""
    verilog = generate_csd_multipliers(coeffs, module_name)
    port_names = {name for name, *_ in coeffs}
    return _fix_output_wires(_fix_verilog_ports(verilog), port_names)


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


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="fir-design",
        description="Design a multiplierless (CSD) lowpass FIR filter from JSON.",
    )
    parser.add_argument("spec", help="path to the filter specification JSON")
    parser.add_argument(
        "-o",
        "--output",
        help="write result JSON to this file instead of stdout",
    )
    parser.add_argument(
        "--verilog-out",
        help="write the generated Verilog module to this file",
    )
    return parser


def main(argv: Optional[list[str]] = None) -> int:
    """CLI entry point for multiplierless FIR filter design.

    Reads filter specifications from a JSON file, runs ellipsoid-method
    optimization with CSD-quantized coefficients, and writes results as JSON
    to stdout (or to ``--output``).

    Args:
        argv: Command-line arguments (list of strings). If None, uses
            sys.argv[1:].

    Returns:
        Exit code — 0 on success, 1 on failure.
    """
    if argv is None:
        argv = sys.argv[1:]

    parser = _build_parser()
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        return 0 if exc.code == 0 else 1

    try:
        spec = json.loads(Path(args.spec).read_text(encoding="utf-8"))
    except OSError as exc:
        print(f"error: cannot read {args.spec}: {exc}", file=sys.stderr)
        return 1
    except json.JSONDecodeError as exc:
        print(f"error: invalid JSON in {args.spec}: {exc}", file=sys.stderr)
        return 1
    if not isinstance(spec, dict):
        print("error: filter specification must be a JSON object", file=sys.stderr)
        return 1

    N = spec.get("filter_order", DEFAULTS["filter_order"])
    csd_nnz = spec.get("csd_nnz", DEFAULTS["csd_nnz"])
    if not isinstance(N, int) or N < 1:
        print("error: filter_order must be a positive integer", file=sys.stderr)
        return 1
    if not isinstance(csd_nnz, int) or csd_nnz < 0:
        print("error: csd_nnz must be a non-negative integer", file=sys.stderr)
        return 1
    try:
        method = SpectralMethod(spec.get("spectral_method", "fft"))
    except ValueError:
        print(
            f"error: unknown spectral_method: {spec.get('spectral_method')!r}",
            file=sys.stderr,
        )
        return 1
    tol = spec.get("root_tolerance", 1e-8)

    try:
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
    except (TypeError, ValueError) as exc:
        print(f"error: invalid filter specification: {exc}", file=sys.stderr)
        return 1

    if r is None:
        print(
            f"Optimization failed — no feasible solution after {num_iters} iterations.",
            file=sys.stderr,
        )
        return 1

    try:
        h = spectral_fact_select(r, method, tol)
    except (TypeError, ValueError, RuntimeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    csd_strings: list[str] = []
    coefficients = []
    for i, hi in enumerate(h):
        _, parts = csd_quantize_parts(float(hi), csd_nnz)
        csd_str = format_csd(parts)
        csd_strings.append(csd_str)
        coefficients.append(
            {"index": i, "value": csd_to_float(csd_str), "csd": csd_str}
        )

    output = {
        "filter_order": N,
        "csd_nnz": csd_nnz,
        "iterations": num_iters,
        "spectral_method": method.value,
        "coefficients": coefficients,
    }

    verilog_text: Optional[str] = None
    if "verilog" in spec:
        vl = spec["verilog"]
        if not isinstance(vl, dict):
            print("error: 'verilog' must be a JSON object", file=sys.stderr)
            return 1
        input_width = vl.get("input_width", 16)
        module_name = vl.get("module_name", "fir_filter")
        verilog_form = vl.get("form", "transpose")
        if not isinstance(input_width, int) or input_width < 1:
            print(
                "error: verilog.input_width must be a positive integer",
                file=sys.stderr,
            )
            return 1
        if not isinstance(module_name, str) or not re.fullmatch(
            r"[A-Za-z_][A-Za-z0-9_]*", module_name
        ):
            print(
                f"error: invalid verilog.module_name: {module_name!r}",
                file=sys.stderr,
            )
            return 1

        raws, max_power = csd_coeffs_to_fixed(csd_strings)
        coeff_tuples = [
            (f"h{i}", raw, input_width, max_power) for i, raw in enumerate(raws)
        ]

        generator = VERILOG_GENERATORS.get(verilog_form)
        if generator is None:
            print(f"error: unknown verilog form: {verilog_form}", file=sys.stderr)
            return 1
        verilog_text = generator(coeff_tuples, module_name)
        output["verilog"] = verilog_text

    if args.verilog_out:
        if verilog_text is None:
            print(
                "error: --verilog-out requires a 'verilog' section",
                file=sys.stderr,
            )
            return 1
        try:
            Path(args.verilog_out).write_text(
                verilog_text, encoding="utf-8", newline="\n"
            )
        except OSError as exc:
            print(
                f"error: cannot write {args.verilog_out}: {exc}",
                file=sys.stderr,
            )
            return 1

    text = json.dumps(output, indent=2) + "\n"
    if args.output:
        try:
            Path(args.output).write_text(text, encoding="utf-8")
        except OSError as exc:
            print(f"error: cannot write {args.output}: {exc}", file=sys.stderr)
            return 1
    else:
        sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
