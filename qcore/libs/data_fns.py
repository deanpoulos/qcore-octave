""" """

from inspect import isfunction

import numpy as np


def mag(data):
    """absolute value of two inputs x and y"""
    x, y = data
    return np.sqrt(x**2 + y**2)


def phase(data, delay=None, freq=None):
    """running average"""
    if freq is None:  # freq-dependent phase, freq got from incoming data at index = 0
        x, y, freq = data
    else:  # constant frequency calculation, freq to be passed in by the user
        x, y = data
    return np.angle(np.exp(1j * 2 * np.pi * delay * freq) * (x + 1j * y))


"""
def fft(prev_data, incoming_data, prev_count, incoming_count, length=None):
    (adc_data,) = incoming_data
    adc_data -= np.average(adc_data)
    fft_data = np.abs(np.fft.fft(adc_data)) / length
    fft_data = fft_data[: int(length / 2 + 1)]
    return fft_data, ...
"""

DATAFN_MAP = {
    k: v for k, v in locals().items() if not k == "isfunction" and isfunction(v)
}
