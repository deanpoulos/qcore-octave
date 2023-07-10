""" """

from qcore.modes.mode import Mode
from qcore.pulses.ramped_constant_pulse import RampedConstantPulse


class Cavity(Mode):
    """ """

    def __init__(self, **parameters) -> None:
        """ """
        if "operations" not in parameters:
            default_operations = [RampedConstantPulse("cos_ramped_constant_pulse")]
            parameters["operations"] = default_operations

        super().__init__(**parameters)

    def displace(self) -> None:
        """ """
