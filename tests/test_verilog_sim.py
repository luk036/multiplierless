"""End-to-end simulation of the generated Verilog with Icarus Verilog."""

import json
import pathlib
import shutil
import subprocess
import sys

import pytest

from multiplierless.fir_design import main

IVERILOG = shutil.which("iverilog")
VVP = shutil.which("vvp")
TOOLS = pathlib.Path(__file__).resolve().parent.parent / "tools"

pytestmark = pytest.mark.skipif(
    IVERILOG is None or VVP is None, reason="iverilog/vvp not installed"
)


def _generate(tmp_path: pathlib.Path, form: str) -> pathlib.Path:
    spec = {
        "filter_order": 16,
        "passband_edge": 0.12,
        "stopband_edge": 0.20,
        "passband_ripple": 0.125,
        "stopband_attenuation": 0.125,
        "csd_nnz": 4,
        "discretization_factor": 15,
        "max_iters": 5000,
        "tolerance": 1e-14,
        "ellipsoid_radius": 4.0,
        "parallel_cut": True,
        "spectral_method": "fft",
        "verilog": {"input_width": 16, "module_name": "fir_dut", "form": form},
    }
    spec_file = tmp_path / "spec.json"
    spec_file.write_text(json.dumps(spec))
    out_file = tmp_path / "out.json"

    assert main([str(spec_file), "-o", str(out_file)]) == 0
    return out_file


@pytest.mark.parametrize(
    ("form", "tb_name"),
    [("transpose", "tb_fir_filter_transpose.v"), ("direct", "tb_fir_filter_direct.v")],
)
def test_generated_verilog_passes_testbench(
    tmp_path: pathlib.Path, form: str, tb_name: str
) -> None:
    out_file = _generate(tmp_path, form)
    payload = json.loads(out_file.read_text())
    dut_file = tmp_path / "dut.v"
    dut_file.write_text(payload["verilog"])

    subprocess.run(
        [sys.executable, str(TOOLS / "gen_test_bench.py"), str(out_file)],
        cwd=tmp_path,
        check=True,
        capture_output=True,
    )

    vvp_file = tmp_path / "sim.vvp"
    subprocess.run(
        [
            IVERILOG,
            "-g2012",
            "-o",
            str(vvp_file),
            str(tmp_path / tb_name),
            str(dut_file),
        ],
        cwd=tmp_path,
        check=True,
        capture_output=True,
    )
    result = subprocess.run(
        [VVP, str(vvp_file)],
        cwd=tmp_path,
        capture_output=True,
        text=True,
    )

    combined = result.stdout + result.stderr
    assert result.returncode == 0, combined
    assert "ALL TESTS PASSED" in combined
    assert "FAIL" not in combined
