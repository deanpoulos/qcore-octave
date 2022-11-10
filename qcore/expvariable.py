import numpy as np
from qm import qua

class ExpVar:

    def __init__(self, name:str, var_type: type):

        self.name = name
        self.var_type = var_type
        self.q_var = qua.declare(var_type)
