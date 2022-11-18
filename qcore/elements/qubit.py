""" """

from qcore.elements.element import Element
from qcore.pulses.ramped_constant_pulse import ConstantPulse
from qcore.pulses.gaussian_pulse import GaussianPulse


class Qubit(Element):
    """ """

    def __init__(self, **parameters) -> None:
        """ """
        if "operations" not in parameters:
            default_operations = {
                "saturation": ConstantPulse("constant_pulse"),
                "pi": GaussianPulse("gaussian_pulse"),
            }
            parameters["operations"] = default_operations

        super().__init__(**parameters)

    def rotate(self) -> None:
        """ """
