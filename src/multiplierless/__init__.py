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

try:
    __version__ = version("multiplierless")
except PackageNotFoundError:
    __version__ = "unknown"

__all__ = ["__version__"]
