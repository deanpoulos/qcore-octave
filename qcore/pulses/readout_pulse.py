""" """

from pathlib import Path

import numpy as np

from qcore.pulses.constant_pulse import ConstantPulse
from qcore.pulses.pulse import Pulse


class ReadoutPulse(Pulse):
    """ """

    def __init__(
        self,
        name: str = "readout_pulse",
        weights: tuple[float, float, float, float] | str = (1.0, 0.0, 0.0, 1.0),
        threshold: float | None = None,  # not None only for Optimized weights
        **parameters,
    ) -> None:
        """ """
        # for constant Weights, specify tuple (i_cos, i_sin, q_cos, q_sin)
        # for optimized Weights, specify path string to npz file
        self.weights: tuple[float, float, float, float] | str = weights
        self.threshold: float | None = threshold
        super().__init__(name, **parameters)

    @property
    def has_optimized_weights(self) -> bool:
        """ """
        try:
            return Path(self.weights).exists()
        except TypeError:
            return False

    def sample_integration_weights(self) -> tuple[dict[str, list], dict[str, list]]:
        """ """
        if self.has_optimized_weights:
            weights = np.load(self.weights)  # assume these are the correct length
            I_weights = {"cosine": weights["I"][0], "sine": weights["I"][1]}
            Q_weights = {"cosine": weights["Q"][0], "sine": weights["Q"][1]}
            return (I_weights, Q_weights)
        else:
            length = self.total_length / Pulse.CLOCK_CYCLE
            weights = [[(self.weights[weight], length)] for weight in self.weights]
            I_weights = {"cosine": weights[0], "sine": weights[1]}
            Q_weights = {"cosine": weights[2], "sine": weights[3]}


class ConstantReadoutPulse(ConstantPulse, ReadoutPulse):
    """ """

    def __init__(self, name: str = "constant_readout_pulse", **parameters) -> None:
        """ """
        super().__init__(name, **parameters)
