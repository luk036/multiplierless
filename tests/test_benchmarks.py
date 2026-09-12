"""Run-time benchmarks for the optimization hot paths.

Measure with ``pytest --benchmark-only tests/test_benchmarks.py``.
"""

from typing import Any

import numpy as np

from multiplierless.lowpass_oracle import create_lowpass_case_params
from multiplierless.spectral_fact import spectral_fact


def test_bench_assess_feas(benchmark: Any) -> None:
    oracle = create_lowpass_case_params(32, 0.12, 0.20, 0.125, 0.125, 15)
    x = np.linspace(1.0, 0.1, 32)
    benchmark(oracle.assess_feas, x)


def test_bench_spectral_fact(benchmark: Any) -> None:
    r = np.full(32, 0.01)
    r[0] = 1.0
    benchmark(spectral_fact, r)
