from typing import Callable, List

from qm.qua import for_, while_, wait
from qcore.sweep import Sweep
from qcore.elements import element

def construct_sweep(ordered_sweep_list: List[Sweep],
                    pulse_sequence: Callable,
                    arg_mapping: dict,
                    wait_time: int,
                    wait_elem: element
                    ):

    def construct_sweep_rec(curr_idx: int):
        s_var = ordered_sweep_list[curr_idx]
        var = s_var.q_var
        with for_(var, s_var.start, var < s_var.stop, var + s_var.step):
            if curr_idx == (len(ordered_sweep_list) - 1):
                pulse_sequence(**arg_mapping)
                wait(int(wait_time // 4), wait_elem.name)
                #save sweep variables
                for var in ordered_sweep_list:
                    var.save()
            else:
                construct_sweep(curr_idx=(curr_idx + 1))

    construct_sweep_rec(curr_idx=0)





def repeat_until():
    pass