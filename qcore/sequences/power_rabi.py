from qm import qua

from qcore.elements import Readout, Qubit
from qcore.variables.variable import Variable


def generate_power_rabi(
    pulse_name: str,
    qubit: Qubit,
    I_Var: Variable,
    Q_Var: Variable,
    rr: Readout,
    ampx: float,
):

    qubit.play(pulse_name, ampx=ampx)
    qua.align(qubit.name, rr.name)
    rr.measure((I_Var.q_var, Q_Var.q_var))

    I_Var.save()
    Q_Var.save()
