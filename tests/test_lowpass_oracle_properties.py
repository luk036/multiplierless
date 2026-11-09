import numpy as np
from ellalgo.oracles.lowpass_oracle import create_lowpass_case
from hypothesis import given, settings
from hypothesis.strategies import integers

from multiplierless.lowpass_oracle_q import LowpassOracleQ


def _oracle(N: int = 32, nnz: int = 5) -> LowpassOracleQ:
    return LowpassOracleQ(nnz, create_lowpass_case(N))


def _ones(N: int = 32) -> np.ndarray:
    r = np.zeros(N)
    r[0] = 1.0
    return r


def test_initialization() -> None:
    lowpass = create_lowpass_case(32)
    oracle = LowpassOracleQ(5, lowpass)

    assert oracle.nnz == 5
    assert oracle.lowpass is lowpass
    assert isinstance(oracle.rcsd, np.ndarray)
    assert oracle.num_retries == 0
    assert oracle.max_retries == lowpass.spectrum.shape[0]


def test_rcsd_properties() -> None:
    oracle = _oracle()
    r = _ones()

    _, rcsd, _, can_retry = oracle.assess_optim_q(r, oracle.lowpass.sp_sq, False)

    assert isinstance(rcsd, np.ndarray)
    assert rcsd.shape == r.shape
    assert oracle.num_retries == 0
    assert isinstance(can_retry, bool)


def test_cut_properties() -> None:
    oracle = _oracle()

    (gc, hc), _, _, _ = oracle.assess_optim_q(_ones(), oracle.lowpass.sp_sq, False)

    assert isinstance(gc, np.ndarray)
    assert gc.shape == (32,)
    assert isinstance(hc, (float, np.floating, tuple))


def test_retry_increments() -> None:
    oracle = _oracle()
    oracle.assess_optim_q(_ones(), oracle.lowpass.sp_sq, False)
    before = oracle.num_retries

    oracle.assess_optim_q(_ones(), oracle.lowpass.sp_sq, True)

    assert oracle.num_retries == before + 1


def test_stopband_bound_is_non_negative() -> None:
    oracle = _oracle()

    _, _, stop_sq, _ = oracle.assess_optim_q(_ones(), oracle.lowpass.sp_sq, False)

    assert stop_sq is None or stop_sq >= 0


def test_retry_flag_is_bounded() -> None:
    oracle = _oracle()

    _, _, _, can_retry = oracle.assess_optim_q(_ones(), oracle.lowpass.sp_sq, False)
    assert isinstance(can_retry, bool)

    for _ in range(min(5, oracle.max_retries)):
        _, _, _, can_retry = oracle.assess_optim_q(_ones(), oracle.lowpass.sp_sq, True)
        if not can_retry:
            break

    assert oracle.num_retries <= oracle.max_retries


@given(integers(min_value=16, max_value=32), integers(min_value=3, max_value=8))
@settings(max_examples=5, deadline=5000)
def test_input_invariance(N: int, nnz: int) -> None:
    oracle = _oracle(N, nnz)

    (gc, _), rcsd, _, can_retry = oracle.assess_optim_q(
        _ones(N), oracle.lowpass.sp_sq, False
    )

    assert gc.shape == (N,)
    assert rcsd.shape == (N,)
    assert isinstance(can_retry, bool)


@given(integers(min_value=16, max_value=24), integers(min_value=3, max_value=6))
@settings(max_examples=3, deadline=5000)
def test_basic_functionality(N: int, nnz: int) -> None:
    oracle = _oracle(N, nnz)

    _, rcsd, _, _ = oracle.assess_optim_q(_ones(N), oracle.lowpass.sp_sq, False)

    assert oracle.nnz == nnz
    assert oracle.num_retries >= 0
    assert len(rcsd) == N
