import numpy as np
from pytest import approx
from multiplierless.spectral_fact import spectral_fact, inverse_spectral_fact


def test_spectral_fact() -> None:
    h = np.array(
        [
            0.76006445,
            0.54101887,
            0.42012073,
            0.3157191,
            0.10665804,
            0.04326203,
            0.01315678,
        ]
    )
    r = inverse_spectral_fact(h)
    h2 = spectral_fact(r)
    assert len(h) == len(h2)
    print(h2)
    assert h2 == approx(h)
