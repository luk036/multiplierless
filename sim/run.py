"""Run cocotb verification for FIR filter Verilog modules.

Usage:
    python sim/run.py                           # run both tests
    python sim/run.py --form transpose          # transpose only
    python sim/run.py --form direct             # direct only
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path

import cocotb as _cocotb

COCOTB_PKG = Path(_cocotb.__file__).parent
COCOTB_LIBS = COCOTB_PKG / "libs"
VPI_LIB = "cocotbvpi_icarus"

PROJECT = Path(__file__).resolve().parent.parent


def build_and_run(
    verilog_file: str, top: str, test_module: str, coeff_json: str
) -> bool:
    """Compile Verilog and run cocotb test. Returns True on success."""
    vvp_file = Path("sim_build") / f"{top}.vvp"
    vvp_file.parent.mkdir(parents=True, exist_ok=True)

    # Prepend timescale and compile with iverilog
    src = PROJECT / verilog_file
    combined = vvp_file.parent / f"{top}_combined.v"
    combined.write_text(
        "`timescale 1ns/1ps\n" + src.read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    cmd_build = [
        "iverilog",
        "-g2012",
        "-o",
        str(vvp_file),
        str(combined),
    ]
    r = subprocess.run(cmd_build, capture_output=True, text=True)
    if r.returncode != 0:
        print(f"BUILD FAILED:\n{r.stdout}\n{r.stderr}")
        return False
    print(f"Built {vvp_file}")

    # Run with cocotb VPI
    env = os.environ.copy()
    env["TOPLEVEL"] = top
    env["COCOTB_TEST_MODULES"] = test_module
    env["COEFF_JSON"] = str(PROJECT / coeff_json)
    env["PYTHONPATH"] = str(PROJECT / "sim") + os.pathsep + env.get("PYTHONPATH", "")
    # Point cocotb to the Python DLL and interpreter on Windows
    conda_env = Path(r"D:\scoop\apps\miniconda3\current\envs\pyflow")
    py_dll = conda_env / "python314.dll"
    if py_dll.is_file():
        env["LIBPYTHON_LOC"] = str(py_dll)
    py_exe = conda_env / "python.exe"
    if py_exe.is_file():
        env["PYGPI_PYTHON_BIN"] = str(py_exe)

    cmd_run = [
        "vvp",
        "-M",
        str(COCOTB_LIBS),
        "-m",
        VPI_LIB,
        str(vvp_file),
    ]
    r = subprocess.run(cmd_run, capture_output=True, text=True, env=env)
    print(r.stdout)
    if r.stderr:
        print("STDERR:", r.stderr[:500], file=sys.stderr)

    success = r.returncode == 0 and "FAILED" not in r.stdout
    if success:
        print(f"[PASS] {top} ({test_module})")
    else:
        print(f"[FAIL] {top} ({test_module})")
    return success


def main() -> None:
    parser = argparse.ArgumentParser(description="Run cocotb verification")
    parser.add_argument(
        "--form", choices=["transpose", "direct", "both"], default="both"
    )
    args = parser.parse_args()

    tests = []
    if args.form in ("transpose", "both"):
        tests.append(
            (
                "fir_filter_py.v",
                "fir_filter",
                "test_transpose",
                "fir_filter_output.json",
                "Transpose-form",
            )
        )
    if args.form in ("direct", "both"):
        tests.append(
            (
                "fir_filter_direct_py.v",
                "fir_filter_direct_py",
                "test_direct",
                "fir_filter_direct_output.json",
                "Direct-form",
            )
        )

    all_ok = True
    for v_file, top, module, json_file, label in tests:
        print(f"\n{'='*50}")
        print(f"  {label}: {top}")
        print(f"{'='*50}")
        ok = build_and_run(v_file, top, module, json_file)
        if not ok:
            all_ok = False

    sys.exit(0 if all_ok else 1)


if __name__ == "__main__":
    main()
