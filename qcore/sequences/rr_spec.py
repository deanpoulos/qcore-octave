from qm import qua

from qcore.elements import Readout
from qcore.expvariable import ExpVar


def generate_rr_spec(I_Var: ExpVar, Q_Var: ExpVar, rr: Readout):
    def rr_spec(freq: int):
        qua.update_frequency(rr.name, freq)  # update resonator pulse frequency
        rr.measure((I_Var.q_var, Q_Var.q_var))

    return rr_spec
