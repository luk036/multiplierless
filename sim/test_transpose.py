"""cocotb test for transpose-form FIR filter impulse response."""
import json
import os
from pathlib import Path

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles, RisingEdge


def _csd_to_int(csd_str: str) -> int:
    val = 0
    for i, ch in enumerate(csd_str):
        power = len(csd_str) - 1 - i
        if ch == '+':
            val += 1 << power
        elif ch == '-':
            val -= 1 << power
    return val


def _load_expected() -> list[int]:
    json_path = os.environ.get("COEFF_JSON", "../fir_filter_output.json")
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


def _to_signed(val: int, bits: int) -> int:
    """Convert unsigned value to signed integer."""
    if val >= (1 << (bits - 1)):
        val -= 1 << bits
    return val


@cocotb.test()
async def test_impulse_response(dut):
    """Feed impulse; verify y = coefficients with 1-cycle pipeline latency."""
    expected = _load_expected()
    N = len(expected)
    # Output width: 38 bits (input_width=16 + max_power)
    bits = 38
    dut._log.info("Testing %d-tap transpose-form FIR", N)

    cocotb.start_soon(Clock(dut.clk, 10, unit="ns").start())

    dut.rst_n.value = 0
    dut.x.value = 0
    await ClockCycles(dut.clk, 2)
    dut.rst_n.value = 1
    await ClockCycles(dut.clk, 1)

    errors = 0
    for i in range(N + 1):
        if i < N:
            dut.x.value = 1 if i == 0 else 0
        else:
            dut.x.value = 0
        await RisingEdge(dut.clk)

        actual = _to_signed(int(dut.y.value), bits)

        # Pipeline latency: at cycle i, y = h[i-1] (with h[-1] = 0)
        exp = expected[i - 1] if 0 < i <= N else 0

        if actual != exp:
            dut._log.error("Cycle %d: y=%d, expected=%d", i, actual, exp)
            errors += 1
        else:
            dut._log.info("Cycle %d: y=%d OK", i, actual)

    if errors:
        dut._log.error("FAILED: %d/%d checks", errors, N + 1)
    else:
        dut._log.info("ALL %d CHECKS PASSED", N + 1)

    assert errors == 0, f"{errors}/{N+1} checks failed"
