""" """

import numpy as np


def ramp_cos(length: int, up: bool = True) -> list[float]:
    """ """
    samples = 0.5 * (1 - np.cos(np.linspace(0, np.pi, length)))
    return samples if up else samples[::-1]


def ramp_tanh(length: int, up: bool = True) -> list[float]:
    """ """
    samples = (1 + np.tanh(np.linspace(-2, 2, length))) / 2
    return samples if up else samples[::-1]
