from qm import qua

from qcore.elements import Readout, Qubit
from qcore.expvariable import ExpVar


def generate_power_rabi(
    pulse_name: str, qubit: Qubit, I_Var: ExpVar, Q_Var: ExpVar, rr: Readout
):
    def power_rabi(ampx: float):

        qubit.play(pulse_name, ampx=ampx)
        qua.align(qubit.name, rr.name)
        rr.measure((I_Var.q_var, Q_Var.q_var))

    return power_rabi
