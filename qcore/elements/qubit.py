""" """

from qcore.elements.mode import Mode
from qcore.pulses.ramped_constant_pulse import ConstantPulse
from qcore.pulses.gaussian_pulse import GaussianPulse


class Qubit(Mode):
    """ """

    def __init__(self, **parameters) -> None:
        """ """
        if "operations" not in parameters:
            default_operations = [
                ConstantPulse("constant_pulse"),
                GaussianPulse("gaussian_pulse"),
            ]
            parameters["operations"] = default_operations

        super().__init__(**parameters)

    def rotate(self) -> None:
        """ """
