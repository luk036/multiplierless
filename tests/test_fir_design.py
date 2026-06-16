import json
import pathlib

import numpy as np
import pytest

from multiplierless.fir_design import create_lowpass_case_params, main


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

    def test_main_file_not_found(self) -> None:
        with pytest.raises(FileNotFoundError):
            main(["nonexistent_file.json"])

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
        assert "Usage" in result.stderr

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
