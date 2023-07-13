""" """

from inspect import isfunction

import numpy as np


def mag(data):
    """absolute value of two inputs x and y"""
    x, y = data
    return np.sqrt(x.avg**2 + y.avg**2)


def phase(data, freq=None, delay=0):
    """ """
    if freq is None:  # freq-dependent phase, freq is a Sweep
        x, y, freq = data
        freq = freq.data
    else:  # constant frequency calculation, freq to be passed in by the user
        x, y = data
    return np.angle(np.exp(-1j * 2 * np.pi * delay * freq) * (x.avg + 1j * y.avg))


def fft(data, length):
    """ """
    (x,) = data
    x = x - np.average(x)
    return (np.abs(np.fft.fft(x)) / length)[:, : int(length / 2 + 1)]


DATAFN_MAP = {
    k: v for k, v in locals().items() if not k == "isfunction" and isfunction(v)
}
