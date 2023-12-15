""" """

from pathlib import Path
from typing import Union

import numpy as np

from qcore.pulses.constant_pulse import ConstantPulse
from qcore.pulses.gaussian_pulse import GaussianPulse
from qcore.pulses.digital_waveform import DigitalWaveform
from qcore.pulses.pulse import Pulse

# Integration weight dictionary
IW = dict[str, list]

# cos and sin integration weight tuple
CosSinWeightTuple = tuple[float, float, float, float]
# cos, sin and -sin integration weight tuple (used for dual-demodulation)
CosSinMinusSinWeightTuple = tuple[float, float, float, float, float, float]

class ReadoutPulse(Pulse):
    """ """

    def __init__(
        self,
        name: str,
        weights: Union[CosSinWeightTuple, CosSinMinusSinWeightTuple, str] = (
            1.0, 0.0,    # cos
            0.0, 1.0,    # sin
        ),
        threshold: Union[float, None] = None,  # not None only for Optimized weights
        **parameters,
    ) -> None:
        """ """
        # for constant Weights, specify tuple (i_cos, i_sin, q_cos, q_sin)
        # for optimized Weights, specify path string to npz file which must have
        # two arrays named "I" and "Q" which store cosine and sine weights respectively
        self.weights = weights
        self.threshold = threshold
        super().__init__(name=name, **parameters)

    @property
    def has_optimized_weights(self) -> bool:
        """ """
        try:
            return Path(self.weights).exists()
        except TypeError:
            return False

    def sample_integration_weights(self) -> tuple[IW, IW, IW]:
        """ """
        minus_sin_weights = {"cosine": 0., "sine": -1.}
        if self.has_optimized_weights:
            weights = np.load(self.weights)
            cos_weights = {"cosine": weights["I"][0], "sine": weights["I"][1]}
            sin_weights = {"cosine": weights["Q"][0], "sine": weights["Q"][1]}
            if len(weights["I"] > 1) and len(weights["Q"] > 1):
                # required for dual-demodulation
                minus_sin_weights = {"cosine": weights["Q"][2], "sine": weights["Q"][2]}
        else:
            weights = [[(weight, self.total_length)] for weight in self.weights]
            cos_weights = {"cosine": weights[0], "sine": weights[1]}
            sin_weights = {"cosine": weights[2], "sine": weights[3]}
            if len(weights) >= 6:
                # required for dual-demodulation
                minus_sin_weights = {"cosine": weights[4], "sine": weights[5]}

        return cos_weights, sin_weights, minus_sin_weights


class ConstantReadoutPulse(ConstantPulse, ReadoutPulse):
    """ """


class GaussianReadoutPulse(GaussianPulse, ReadoutPulse):
    """ """
