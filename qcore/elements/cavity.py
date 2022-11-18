""" """

from qcore.elements.element import Element
from qcore.pulses.ramped_constant_pulse import RampedConstantPulse
from qcore.pulses.gaussian_pulse import GaussianPulse


class Cavity(Element):
    """ """

    def __init__(self, **parameters) -> None:
        """ """
        if "operations" not in parameters:
            default_operations = {
                "displacement": RampedConstantPulse("cos_ramped_constant_pulse"),
            }
            parameters["operations"] = default_operations

        super().__init__(**parameters)

    def displace(self) -> None:
        """ """
