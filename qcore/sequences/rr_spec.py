from qm import qua

from qcore.elements import Readout
from qcore.var_types.variable import Variable


def rr_spec(I_Var: Variable, Q_Var: Variable, rr: Readout, freq: Variable):

    qua.update_frequency(rr.name, freq.q_var)  # update resonator pulse frequency
    rr.measure((I_Var.q_var, Q_Var.q_var))

    I_Var.save()
    Q_Var.save()
