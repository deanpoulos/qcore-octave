""" """

from qcore.modes.mode import Mode
from qcore.pulses.ramped_constant_pulse import RampedConstantPulse
from qcore.pulses.gaussian_pulse import GaussianPulse


class Cavity(Mode):
    """ """

    def __init__(self, **parameters) -> None:
        """ """
        if "ops" not in parameters:
            default_ops = {
                "constant_pulse": RampedConstantPulse(),
                "gaussian_pulse": GaussianPulse(),
            }
            parameters["ops"] = default_ops

        super().__init__(**parameters)

    def displace(self) -> None:
        """ """
