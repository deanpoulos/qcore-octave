""" """

from qcore.elements.mode import Mode
from qcore.pulses.ramped_constant_pulse import RampedConstantPulse
from qcore.pulses.gaussian_pulse import GaussianPulse


class Cavity(Mode):
    """ """

    def __init__(self, **parameters) -> None:
        """ """
        if "operations" not in parameters:
            default_operations = [
                RampedConstantPulse("cos_ramped_constant_pulse"),
                GaussianPulse("gaussian_pulse"),
            ]
            parameters["operations"] = default_operations

        super().__init__(**parameters)

    def displace(self) -> None:
        """ """
