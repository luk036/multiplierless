# -*- coding: utf-8 -*-
from __future__ import print_function

from typing import Tuple, Union

import numpy as np

from csdigit.csd import to_csdfixed, to_decimal
from .spectral_fact import inverse_spectral_fact, spectral_fact

Arr = Union[np.ndarray, float]
Cut = Tuple[Arr, float]


class LowpassOracleQ:
    """[summary]

    Returns:
        [type]: [description]
    """

    def __init__(self, nnz, lowpass):
        """[summary]

        Arguments:
            nnz ([type]): [description]
            lowpass ([type]): [description]
        """
        self.nnz = nnz
        self.lowpass = lowpass
        self.rcsd = np.array([0])

    def assess_optim_q(self, r: Arr, Spsq, retry: bool):
        """[summary]

        Arguments:
            r (Arr): [description]
            Spsq ([type]): [description]
            retry (int): [description]

        Returns:
            [type]: [description]
        """
        if not retry:  # retry due to no effect in the previous cut
            self.lowpass.retry = False
            if cut := self.lowpass.assess_feas(r, Spsq):
                return cut, r, None, True
            h = spectral_fact(r)
            hcsd = np.array([to_decimal(to_csdfixed(hi, self.nnz)) for hi in h])
            self.rcsd = inverse_spectral_fact(hcsd)

        (gc, hc), Spsq2 = self.lowpass.assess_optim(self.rcsd, Spsq)
        # no more alternative cuts?
        hc += gc.dot(self.rcsd - r)
        return (gc, hc), self.rcsd, Spsq2, not retry
