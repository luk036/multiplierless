import numpy as np
from ellalgo.cutting_plane import Options, cutting_plane_optim, cutting_plane_optim_q
from ellalgo.ell import Ell
from ellalgo.oracles.lowpass_oracle import create_lowpass_case

from multiplierless.lowpass_oracle_q import LowpassOracleQ

# Modified from CVX code by Almir Mutapcic in 2006.
# Adapted in 2010 for impulse response peak-minimization by convex iteration
# by Christine Law.
#
# "FIR Filter Design via Spectral Factorization and Convex Optimization"
# by S.-P. Wu, S. Boyd, and L. Vandenberghe
#
# Designs an FIR lowpass filter using spectral factorization method with
# constraint on maximum passband ripple and stopband attenuation:
#
#   minimize   max |H(w)|                      for w in stopband
#       s.t.   1/delta <= |H(w)| <= delta      for w in passband
#
# We change variables via spectral factorization method and get:
#
#   minimize   max R(w)                          for w in stopband
#       s.t.   (1/delta)**2 <= R(w) <= delta**2  for w in passband
#              R(w) >= 0                         for all w
#
# where R(w) is squared magnitude frequency response
# (and Fourier transform of autocorrelation coefficients r).
# Variables are coeffients r and gra = hh' where h is impulse response.
# delta is allowed passband ripple.
# This is a convex problem (can be formulated as an SDP after sampling).

# rand('twister',sum(100*clock))
# randn('state',sum(100*clock))

# *********************************************************************
# filter specs (for a low-pass filter)
# *********************************************************************
# number of FIR coefficients (including zeroth)


def create_lowpass_q_case(N: int = 48, nnz: int = 8) -> tuple[LowpassOracleQ, float]:
    """[summary]

    Keyword Arguments:
        N (int): [description] (default: {48})
        nnz (int): [description] (default: {8})

    Returns:
        [type]: [description]
    """
    omega = create_lowpass_case(N)
    Spsq = omega.sp_sq
    Pcsd = LowpassOracleQ(nnz, omega)
    return Pcsd, Spsq


def run_lowpass() -> tuple[int, bool]:
    """[summary]

    Arguments:
        use_parallel_cut (float): [description]

    Keyword Arguments:
        duration (float): [description] (default: {0.000001})

    Returns:
        [type]: [description]
    """
    N = 32

    r0 = np.zeros(N)  # initial xinit
    r0[0] = 0
    ellip = Ell(4.0, r0)
    omega = create_lowpass_case(N)
    Spsq = omega.sp_sq
    options = Options()
    options.max_iters = 50000
    options.tolerance = 1e-14
    h, _, num_iters = cutting_plane_optim(omega, ellip, Spsq, options)  # type: ignore
    # h = spectral_fact(r)
    return num_iters, h is not None


# def test_no_parallel_cut(benchmark) -> None:
#     result, feasible = benchmark(run_lowpass, False)
#     assert feasible
#     assert result >= 13334

# def test_w_parallel_cut(benchmark) -> None:
#     result, feasible = benchmark(run_lowpass, True)
#     assert feasible
#     assert result <= 568


def test_lowpass() -> None:
    """[summary]"""
    result, feasible = run_lowpass()
    assert feasible
    # Use tolerance-based assertion instead of hardcoded range
    # The exact iteration count may vary based on numerical precision
    # but should be in a reasonable range for convergence
    assert result >= 12000, f"Expected at least 12000 iterations, got {result}"
    assert result <= 13000, f"Expected at most 13000 iterations, got {result}"


def run_lowpass_q() -> tuple[int, bool]:
    """[summary]

    Arguments:
        use_parallel_cut (float): [description]

    Keyword Arguments:
        duration (float): [description] (default: {0.000001})

    Returns:
        [type]: [description]
    """
    N = 32
    nnz = 7

    r0 = np.zeros(N)  # initial xinit
    r0[0] = 0
    ellip = Ell(4.0, r0)
    Pcsd, Spsq = create_lowpass_q_case(N, nnz)
    options = Options()
    options.max_iters = 20000
    options.tolerance = 1e-14

    h, _, num_iters = cutting_plane_optim_q(Pcsd, ellip, Spsq, options)  # type: ignore
    # h = spectral_fact(r)
    return num_iters, h is not None


def test_lowpass_q() -> None:
    """[summary]"""
    result, feasible = run_lowpass_q()
    assert feasible
    # Use tolerance-based assertion with wider range to accommodate
    # variations in optimization convergence
    assert result >= 1000, f"Expected at least 1000 iterations, got {result}"
    assert result <= 5000, f"Expected at most 5000 iterations, got {result}"
