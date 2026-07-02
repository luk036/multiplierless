"""cocotb test for direct-form FIR multiplier bank."""

import json
import os
from pathlib import Path

import cocotb
from cocotb.triggers import Timer


def _csd_to_int(csd_str: str) -> int:
    """Convert a dotless CSD string to its integer value."""
    val = 0
    for i, ch in enumerate(csd_str):
        power = len(csd_str) - 1 - i
        if ch == "+":
            val += 1 << power
        elif ch == "-":
            val -= 1 << power
    return val


def _load_expected() -> list[int]:
    """Load expected coefficients from the JSON output file."""
    json_path = os.environ.get("COEFF_JSON", "../fir_filter_direct_output.json")
    with open(Path(__file__).resolve().parent / json_path) as f:
        data = json.load(f)
    coeffs = data["coefficients"]
    csd_raw = [c["csd"] for c in coeffs]
    max_len = max(len(s) for s in csd_raw)
    result = []
    for s in csd_raw:
        raw = s.replace(".", "")
        while len(raw) < max_len:
            raw = "0" + raw
        result.append(_csd_to_int(raw))
    return result


def _output_port_names(dut) -> list[str]:
    """Discover output port names matching h0..hN."""
    names = []
    i = 0
    while True:
        name = f"h{i}"
        if hasattr(dut, name):
            names.append(name)
            i += 1
        else:
            break
    return names


@cocotb.test()
async def test_direct_multipliers(dut):
    """Set x to various values; verify each h_i = coeff_i * x."""
    expected = _load_expected()
    N = len(expected)
    port_names = _output_port_names(dut)
    assert len(port_names) == N, f"Found {len(port_names)} output ports, expected {N}"
    dut._log.info("Testing %d-tap direct-form multiplier bank", N)

    # Output bit width: detect from first output port
    bits = len(dut.h0.value) if hasattr(dut, "h0") else 38
    test_values = [1, -1, 127, -128]
    errors = 0

    for tv in test_values:
        dut.x.value = tv
        await Timer(10, unit="ns")

        for name, coeff in zip(port_names, expected):
            exp_val = coeff * tv
            actual = int(getattr(dut, name).value)
            if actual >= (1 << (bits - 1)):
                actual -= 1 << bits
            if actual != exp_val:
                dut._log.error(
                    "FAIL x=%d, %s=%d, expected=%d", tv, name, actual, exp_val
                )
                errors += 1

    if errors:
        dut._log.error("FAILED: %d errors", errors)
    else:
        dut._log.info("ALL TESTS PASSED")

    assert errors == 0, f"{errors} test failures"
