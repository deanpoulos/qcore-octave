from typing import Callable, List

from qm.qua import for_, while_
from qcore.sweep import Sweep

def construct_sweep(ordered_sweep_list: List[Sweep],
                    pulse_sequence: Callable,
                    arg_mapping: dict
                    ):

    def construct_sweep_rec(ordered_sweep_list: List[Sweep]):
        s_var = ordered_sweep_list.pop()
        var = s_var.q_var
        with for_(var, s_var.start, var < s_var.stop, var + s_var.step):
            if len(ordered_sweep_list) == 0:
                pulse_sequence(**arg_mapping)
            else:
                construct_sweep(ordered_sweep_list=ordered_sweep_list)

    construct_sweep_rec(ordered_sweep_list=ordered_sweep_list)





def repeat_until():
    pass