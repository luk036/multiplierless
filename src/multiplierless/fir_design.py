"""CLI for multiplierless FIR filter design — JSON-in, CSD-out.

Reads filter specifications from a JSON file, runs the ellipsoid-method
optimization with CSD-quantized coefficients, and outputs:
  - CSD-quantized impulse response coefficients (numeric + CSD string)
  - Optionally, a synthesizable Verilog module via csdigit.csd_multiplier
"""

import json
import sys
from typing import Any, Optional

import numpy as np
from csdigit.csd import to_csdnnz
from csdigit.csd_multiplier import generate_csd_multipliers
from ellalgo.cutting_plane import Options, cutting_plane_optim_q
from ellalgo.ell import Ell

from multiplierless.lowpass_oracle_q import LowpassOracleQ
from multiplierless.spectral_fact import spectral_fact_fft, spectral_fact_root

# experiment/lowpass_oracle is not a package module; import by path if needed,
# but we replicate create_lowpass_case_with_params inline to avoid coupling.


def create_lowpass_case_params(
    N: int,
    wpass: float,
    wstop: float,
    delta0_wpass: float,
    delta0_wstop: float,
    discretization_factor: int,
) -> Any:
    """Build a LowpassOracle with fully parameterized filter specs."""
    from math import floor

    mdim = discretization_factor * N
    w = np.linspace(0, np.pi, mdim)
    temp = 2 * np.cos(np.outer(w, np.arange(1, N)))
    spectrum = np.concatenate((np.ones((mdim, 1)), temp), axis=1)

    nwpass = floor(wpass * np.pi * (mdim - 1) / np.pi) + 1
    nwstop = floor(wstop * np.pi * (mdim - 1) / np.pi) + 1

    delta1 = 20 * np.log10(1 + delta0_wpass)
    delta2 = 20 * np.log10(delta0_wstop)

    low_pass = pow(10, -delta1 / 20)
    up_pass = pow(10, +delta1 / 20)
    stop_pass = pow(10, +delta2 / 20)

    lp_sq = low_pass * low_pass
    up_sq = up_pass * up_pass
    sp_sq = stop_pass * stop_pass

    class Oracle:
        def __init__(self) -> None:
            self.spectrum = spectrum
            self.nwpass = nwpass
            self.nwstop = nwstop
            self.lp_sq = lp_sq
            self.up_sq = up_sq
            self.sp_sq = sp_sq
            self.idx1 = 0
            self.idx2 = nwpass
            self.idx3 = nwstop
            self.fmax = float("-inf")
            self.kmax = 0
            self._mdim = mdim
            self._ndim = N

        def assess_feas(self, x: np.ndarray) -> Any:
            mdim, ndim = self.spectrum.shape
            for _ in range(self.nwpass):
                self.idx1 += 1
                if self.idx1 == self.nwpass:
                    self.idx1 = 0
                col_k = self.spectrum[self.idx1]
                v = col_k.dot(x)
                if v > self.up_sq:
                    return col_k, (v - self.up_sq, v - self.lp_sq)
                if v < self.lp_sq:
                    return -col_k, (-v + self.lp_sq, -v + self.up_sq)
            self.fmax = float("-inf")
            self.kmax = 0
            for _ in range(self.nwstop, mdim):
                self.idx3 += 1
                if self.idx3 == mdim:
                    self.idx3 = self.nwstop
                col_k = self.spectrum[self.idx3]
                v = col_k.dot(x)
                if v > self.sp_sq:
                    return col_k, (v - self.sp_sq, v)
                if v < 0:
                    return -col_k, (-v, -v + self.sp_sq)
                if v > self.fmax:
                    self.fmax = v
                    self.kmax = self.idx3
            for _ in range(self.nwpass, self.nwstop):
                self.idx2 += 1
                if self.idx2 == self.nwstop:
                    self.idx2 = self.nwpass
                col_k = self.spectrum[self.idx2]
                v = col_k.dot(x)
                if v < 0:
                    return -col_k, -v
            if x[0] < 0:
                grad = np.zeros(ndim)
                grad[0] = -1.0
                return grad, -x[0]
            return None

        def assess_optim(self, xc: np.ndarray, gamma: float) -> Any:
            self.sp_sq = gamma
            if cut := self.assess_feas(xc):
                return cut, None
            return (self.spectrum[self.kmax], (0.0, self.fmax)), self.fmax

    return Oracle()


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
    if method == "fft":
        h = spectral_fact_fft(r)
    else:
        h = spectral_fact_root(r, tol)
    csd_strings = [to_csdnnz(hi, csd_nnz) for hi in h]

    coefficients = []
    for i, (hi, csd_str) in enumerate(zip(h, csd_strings)):
        coefficients.append({"index": i, "value": float(hi), "csd": csd_str})

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

        max_len = max(len(s) for s in csd_strings)
        max_power = max_len - 1

        coeff_tuples = []
        for i, csd_str in enumerate(csd_strings):
            raw = csd_str.replace(".", "")
            while len(raw) < max_len:
                raw = "0" + raw
            coeff_tuples.append((f"h{i}", raw, input_width, max_power))

        output["verilog"] = generate_csd_multipliers(coeff_tuples, module_name)

    json.dump(output, sys.stdout, indent=2)
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
