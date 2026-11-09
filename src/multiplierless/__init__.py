"""Multiplierless FIR filter design package.

Provides tools for designing FIR filters using CSD (Canonical Signed Digit)
representation and ellipsoid method optimization, avoiding multiplication
operations for hardware-constrained implementations.

.. svgbob::
   :align: center

        x[n] ──►z⁻¹──►z⁻¹──►z⁻¹──► ...
                  │      │      │
                  ▼      ▼      ▼
                 ╲│╭    ╲│╭    ╲│╭
               ───┼┤ ├───┼┤ ├───┼┤ ├──► y[n]
                 ╱│╯    ╱│╯    ╱│╯
                 CSD    CSD    CSD
"""

from importlib.metadata import PackageNotFoundError, version

from .lowpass_oracle import LowpassOracle, create_lowpass_case_params
from .lowpass_oracle_q import (
    LowpassOracleLike,
    LowpassOracleQ,
    csd_quantize,
    csd_quantize_parts,
)
from .spectral_fact import (
    SpectralMethod,
    inverse_spectral_fact,
    spectral_fact,
    spectral_fact_fft,
    spectral_fact_root,
    spectral_fact_select,
)

try:
    __version__ = version("multiplierless")
except PackageNotFoundError:
    __version__ = "unknown"

__all__ = [
    "__version__",
    "LowpassOracle",
    "LowpassOracleLike",
    "LowpassOracleQ",
    "SpectralMethod",
    "create_lowpass_case_params",
    "csd_quantize",
    "csd_quantize_parts",
    "inverse_spectral_fact",
    "spectral_fact",
    "spectral_fact_fft",
    "spectral_fact_root",
    "spectral_fact_select",
]
