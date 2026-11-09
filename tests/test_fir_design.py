import json
import pathlib
import re
from math import ceil, log2

import numpy as np
import pytest

from multiplierless.fir_design import (
    create_lowpass_case_params,
    csd_coeffs_to_fixed,
    csd_to_float,
    format_csd,
    main,
)
from multiplierless.lowpass_oracle_q import csd_quantize, csd_quantize_parts


def _raw_to_int(raw: str) -> int:
    value = 0
    for i, ch in enumerate(raw):
        power = len(raw) - 1 - i
        if ch == "+":
            value += 1 << power
        elif ch == "-":
            value -= 1 << power
    return value


class TestFixedPointAlignment:
    def test_csd_coeffs_share_one_scale(self) -> None:
        csd_list = ["0.000000+0+000+000+", "0.+", "0.000+0-0+00+"]
        raws, max_power = csd_coeffs_to_fixed(csd_list)

        assert {len(raw) for raw in raws} == {max_power + 1}
        for csd, raw in zip(csd_list, raws):
            expected = csd_to_float(csd) * 2.0**max_power
            assert _raw_to_int(raw) == int(round(expected))

    def test_short_csd_is_right_padded(self) -> None:
        # Regression: left-padding scaled each coefficient by a different
        # power of two (0.5 became 2**16 instead of 2**17 at max_power=17).
        raws, max_power = csd_coeffs_to_fixed(["0.000000+0+000+000+", "0.+"])

        assert max_power == 17
        assert _raw_to_int(raws[1]) == int(0.5 * 2.0**max_power)

    @pytest.mark.parametrize(
        "value", [0.0, 1.0, -1.0, 0.5, -0.5, 3.25, 0.9127555772777217]
    )
    def test_csd_string_roundtrips_exact_value(self, value: float) -> None:
        quantized = csd_quantize(value, 7)
        _, parts = csd_quantize_parts(value, 7)
        csd = format_csd(parts)

        assert re.fullmatch(r"[0+-]+\.[0+-]*", csd)
        assert csd_to_float(csd) == quantized


class TestCreateLowpassCaseParams:
    def test_returns_oracle_with_correct_interface(self) -> None:
        oracle = create_lowpass_case_params(32, 0.12, 0.20, 0.125, 0.125, 15)
        assert hasattr(oracle, "assess_feas")
        assert hasattr(oracle, "assess_optim")
        assert hasattr(oracle, "spectrum")
        assert hasattr(oracle, "sp_sq")
        assert oracle.sp_sq > 0
        assert oracle.spectrum.shape[1] == 32

    def test_assess_feas_returns_cut_for_violation(self) -> None:
        oracle = create_lowpass_case_params(16, 0.12, 0.20, 0.125, 0.125, 15)
        x = np.zeros(16)
        result = oracle.assess_feas(x)
        # Zero response is below the passband lower bound -> violation
        assert result is not None
        grad, intercept = result
        assert isinstance(grad, np.ndarray)
        assert len(grad) == 16

    def test_assess_feas_large_vector_violates(self) -> None:
        oracle = create_lowpass_case_params(16, 0.12, 0.20, 0.125, 0.125, 15)
        x = np.ones(16) * 10.0
        result = oracle.assess_feas(x)
        assert result is not None
        grad, intercept = result
        assert isinstance(grad, np.ndarray)
        assert len(grad) == 16

    def test_assess_optim_returns_cut_and_value(self) -> None:
        oracle = create_lowpass_case_params(16, 0.12, 0.20, 0.125, 0.125, 15)
        x = np.zeros(16)
        gamma = oracle.sp_sq
        result = oracle.assess_optim(x, gamma)
        assert result is not None
        (gc, hc), fmax = result
        assert isinstance(gc, np.ndarray)
        assert len(gc) == 16

    def test_assess_feas_negative_x0_triggers_gradient(self) -> None:
        oracle = create_lowpass_case_params(16, 0.12, 0.20, 0.125, 0.125, 15)
        x = np.zeros(16)
        x[0] = -1.0
        result = oracle.assess_feas(x)
        assert result is not None
        grad, intercept = result
        assert grad[0] == -1.0

    def test_assess_feas_with_different_parameters(self) -> None:
        oracle = create_lowpass_case_params(24, 0.15, 0.25, 0.1, 0.1, 10)
        x = np.ones(24) * 100.0
        result = oracle.assess_feas(x)
        assert result is not None


class TestMain:
    def test_main_no_args_returns_one(self) -> None:
        ret = main([])
        assert ret == 1

    def test_main_file_not_found(self, capsys: pytest.CaptureFixture[str]) -> None:
        assert main(["nonexistent_file.json"]) == 1
        assert "cannot read" in capsys.readouterr().err

    def test_main_default_argv_empty(self, monkeypatch: pytest.MonkeyPatch) -> None:
        import sys

        monkeypatch.setattr(sys, "argv", ["prog"])
        ret = main()
        assert ret == 1

    def test_main_optimization_failure(self, tmp_path: pathlib.Path) -> None:
        import json

        spec = {
            "filter_order": 32,
            "passband_edge": 0.10,
            "stopband_edge": 0.12,
            "passband_ripple": 0.001,
            "stopband_attenuation": 0.001,
            "csd_nnz": 3,
            "discretization_factor": 15,
            "max_iters": 100,
            "tolerance": 1e-14,
            "ellipsoid_radius": 1.0,
            "parallel_cut": False,
        }
        spec_file = tmp_path / "impossible_spec.json"
        spec_file.write_text(json.dumps(spec))
        ret = main([str(spec_file)])
        assert ret == 1

    def test_main_with_valid_spec(self, tmp_path: pathlib.Path) -> None:
        spec = {
            "filter_order": 32,
            "passband_edge": 0.12,
            "stopband_edge": 0.20,
            "passband_ripple": 0.125,
            "stopband_attenuation": 0.125,
            "csd_nnz": 7,
            "discretization_factor": 15,
            "max_iters": 5000,
            "tolerance": 1e-14,
            "ellipsoid_radius": 4.0,
            "parallel_cut": True,
            "spectral_method": "fft",
        }
        spec_file = tmp_path / "filter_spec.json"
        spec_file.write_text(json.dumps(spec))
        ret = main([str(spec_file)])
        assert ret == 0

    def test_main_with_root_spectral_method(self, tmp_path: pathlib.Path) -> None:
        spec = {
            "filter_order": 32,
            "passband_edge": 0.12,
            "stopband_edge": 0.20,
            "passband_ripple": 0.125,
            "stopband_attenuation": 0.125,
            "csd_nnz": 7,
            "discretization_factor": 15,
            "max_iters": 5000,
            "tolerance": 1e-14,
            "ellipsoid_radius": 4.0,
            "parallel_cut": True,
            "spectral_method": "root",
            "root_tolerance": 1e-8,
        }
        spec_file = tmp_path / "filter_spec_root.json"
        spec_file.write_text(json.dumps(spec))
        ret = main([str(spec_file)])
        assert ret == 0

    def test_main_guard_via_subprocess(self) -> None:
        import subprocess
        import sys

        result = subprocess.run(
            [sys.executable, "-m", "multiplierless.fir_design"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        assert result.returncode == 1
        assert "usage" in result.stderr.lower()

    def test_main_with_verilog_output(self, tmp_path: pathlib.Path) -> None:
        spec = {
            "filter_order": 32,
            "passband_edge": 0.12,
            "stopband_edge": 0.20,
            "passband_ripple": 0.125,
            "stopband_attenuation": 0.125,
            "csd_nnz": 7,
            "discretization_factor": 15,
            "max_iters": 5000,
            "tolerance": 1e-14,
            "ellipsoid_radius": 4.0,
            "parallel_cut": True,
            "spectral_method": "fft",
            "verilog": {"input_width": 16, "module_name": "fir_test"},
        }
        spec_file = tmp_path / "filter_spec_v.json"
        spec_file.write_text(json.dumps(spec))
        ret = main([str(spec_file)])
        assert ret == 0

    def test_output_value_matches_csd_and_verilog_scale(
        self, tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        spec = {
            "filter_order": 32,
            "passband_edge": 0.12,
            "stopband_edge": 0.20,
            "passband_ripple": 0.125,
            "stopband_attenuation": 0.125,
            "csd_nnz": 7,
            "discretization_factor": 15,
            "max_iters": 5000,
            "tolerance": 1e-14,
            "ellipsoid_radius": 4.0,
            "parallel_cut": True,
            "spectral_method": "fft",
            "verilog": {"input_width": 16, "module_name": "fir_test"},
        }
        spec_file = tmp_path / "filter_spec_consistency.json"
        spec_file.write_text(json.dumps(spec))

        assert main([str(spec_file)]) == 0
        payload = json.loads(capsys.readouterr().out)
        coefficients = payload["coefficients"]

        for coeff in coefficients:
            assert re.fullmatch(r"[0+-]+\.[0+-]*", coeff["csd"])
            assert coeff["value"] == csd_to_float(coeff["csd"])

        raws, max_power = csd_coeffs_to_fixed([c["csd"] for c in coefficients])
        for coeff, raw in zip(coefficients, raws):
            assert _raw_to_int(raw) == int(round(coeff["value"] * 2.0**max_power))

        headroom = int(ceil(log2(len(coefficients))))
        width = 16 + max_power + headroom
        assert f"output signed [{width - 1}:0] y" in payload["verilog"]

    def test_main_help_returns_zero(self, capsys: pytest.CaptureFixture[str]) -> None:
        assert main(["--help"]) == 0
        assert "usage" in capsys.readouterr().out.lower()

    def test_main_invalid_json(
        self, tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        spec_file = tmp_path / "bad.json"
        spec_file.write_text("{not json")

        assert main([str(spec_file)]) == 1
        assert "invalid JSON" in capsys.readouterr().err

    def test_main_invalid_numeric_spec(
        self, tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        spec = {"filter_order": 32, "csd_nnz": 4, "passband_edge": "oops"}
        spec_file = tmp_path / "bad_numeric.json"
        spec_file.write_text(json.dumps(spec))

        assert main([str(spec_file)]) == 1
        assert "invalid filter specification" in capsys.readouterr().err

    def test_main_unknown_spectral_method(
        self, tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        spec_file = tmp_path / "bad_method.json"
        spec_file.write_text(
            json.dumps({"filter_order": 32, "csd_nnz": 4, "spectral_method": "nope"})
        )

        assert main([str(spec_file)]) == 1
        assert "unknown spectral_method" in capsys.readouterr().err

    def test_main_writes_output_file(self, tmp_path: pathlib.Path) -> None:
        spec = {
            "filter_order": 32,
            "csd_nnz": 7,
            "max_iters": 5000,
            "ellipsoid_radius": 4.0,
        }
        spec_file = tmp_path / "spec.json"
        spec_file.write_text(json.dumps(spec))
        out_file = tmp_path / "out.json"

        assert main([str(spec_file), "-o", str(out_file)]) == 0
        payload = json.loads(out_file.read_text())
        assert len(payload["coefficients"]) == 32

    def test_main_writes_verilog_file(self, tmp_path: pathlib.Path) -> None:
        spec = {
            "filter_order": 32,
            "csd_nnz": 4,
            "max_iters": 5000,
            "ellipsoid_radius": 4.0,
            "verilog": {"input_width": 16, "module_name": "fir_test"},
        }
        spec_file = tmp_path / "spec.json"
        spec_file.write_text(json.dumps(spec))
        out_file = tmp_path / "out.json"
        v_file = tmp_path / "dut.v"

        args = [str(spec_file), "-o", str(out_file), "--verilog-out", str(v_file)]
        assert main(args) == 0
        assert "module fir_test" in v_file.read_text()

    def test_main_verilog_out_requires_section(
        self, tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        spec = {
            "filter_order": 32,
            "csd_nnz": 4,
            "max_iters": 5000,
            "ellipsoid_radius": 4.0,
        }
        spec_file = tmp_path / "spec.json"
        spec_file.write_text(json.dumps(spec))

        args = [str(spec_file), "--verilog-out", str(tmp_path / "dut.v")]
        assert main(args) == 1
        assert "requires a 'verilog' section" in capsys.readouterr().err

    def test_main_unknown_verilog_form(
        self, tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        spec = {
            "filter_order": 32,
            "csd_nnz": 4,
            "max_iters": 5000,
            "ellipsoid_radius": 4.0,
            "verilog": {"form": "fir"},
        }
        spec_file = tmp_path / "bad_form.json"
        spec_file.write_text(json.dumps(spec))

        assert main([str(spec_file)]) == 1
        assert "unknown verilog form" in capsys.readouterr().err

    def test_main_direct_verilog(
        self, tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        spec = {
            "filter_order": 32,
            "csd_nnz": 4,
            "max_iters": 5000,
            "ellipsoid_radius": 4.0,
            "verilog": {
                "input_width": 16,
                "module_name": "fir_direct",
                "form": "direct",
            },
        }
        spec_file = tmp_path / "direct.json"
        spec_file.write_text(json.dumps(spec))

        assert main([str(spec_file)]) == 0
        verilog = json.loads(capsys.readouterr().out)["verilog"]
        assert "module fir_direct" in verilog
        assert "h0" in verilog
