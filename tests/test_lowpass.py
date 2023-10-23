import numpy as np
from ellalgo.cutting_plane import Options, cutting_plane_optim, cutting_plane_optim_q
from ellalgo.ell import Ell


from multiplierless.lowpass_oracle_q import LowpassOracleQ
from ellalgo.oracles.lowpass_oracle import create_lowpass_case

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


def create_lowpass_q_case(N=48, nnz=8):
    """[summary]

    Keyword Arguments:
        N (int): [description] (default: {48})
        nnz (int): [description] (default: {8})

    Returns:
        [type]: [description]
    """
    omega, Spsq = create_lowpass_case(N)
    Pcsd = LowpassOracleQ(nnz, omega)
    return Pcsd, Spsq


def run_lowpass():
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
    omega, Spsq = create_lowpass_case(N)
    options = Options()
    options.max_iters = 20000
    options.tol = 1e-8
    h, _, num_iters = cutting_plane_optim(omega, ellip, Spsq, options)
    # h = spectral_fact(r)
    return num_iters, h is not None


# def test_no_parallel_cut(benchmark):
#     result, feasible = benchmark(run_lowpass, False)
#     assert feasible
#     assert result >= 13334

# def test_w_parallel_cut(benchmark):
#     result, feasible = benchmark(run_lowpass, True)
#     assert feasible
#     assert result <= 568


def test_lowpass():
    """[summary]"""
    result, feasible = run_lowpass()
    assert feasible
    assert result >= 1075
    assert result <= 1194


def run_lowpass_q():
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
    options.tol = 1e-8

    h, _, num_iters = cutting_plane_optim_q(Pcsd, ellip, Spsq, options)
    # h = spectral_fact(r)
    return num_iters, h is not None


def test_lowpass_q():
    """[summary]"""
    result, feasible = run_lowpass_q()
    assert feasible
    assert result >= 1000
    assert result <= 1136
