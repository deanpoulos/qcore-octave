""" """

from inspect import isfunction

import numpy as np
from scipy import signal

# the 'data' argument must be a sequence of np arrays to be unpacked by the data_fn

def mag(data):
    """absolute value of two inputs x and y"""
    x, y = data
    return np.sqrt(x**2 + y**2)


def phase(data, freq=None, delay=0, unwrap=True):
    """ """
    if freq is None:  # freq-dependent phase, freq is a Sweep
        x, y, freq = data
    else:  # constant frequency calculation, freq to be passed in by the user
        x, y = data
    phase = np.angle(np.exp(-1j * 2 * np.pi * delay * freq) * (x + 1j * y))
    return np.unwrap(phase) if unwrap else phase


def fft(data, length):
    """ """
    (x,) = data
    x = x - np.average(x, axis=-1)[:, None]
    return (np.abs(np.fft.fft(x)) / length)[:, : int(length / 2 + 1)]
    # TODO make the slices more general


def demod(data, freq, length):
    """ """
    (x,) = data
    t_rel = np.linspace(0, length - 1, length)
    sig = x * np.exp(1j * (2 * np.pi * freq * 1e-9 * t_rel + 0.0))
    period_ns = int(1 / np.abs(freq) * 1e9)
    hann = signal.hann(period_ns * 2, sym=True)
    hann = hann / np.sum(hann)
    demod_signal = np.convolve(sig, hann, "same")
    return np.array([demod_signal.real, demod_signal.imag])


DATAFN_MAP = {
    k: v for k, v in locals().items() if not k == "isfunction" and isfunction(v)
}
