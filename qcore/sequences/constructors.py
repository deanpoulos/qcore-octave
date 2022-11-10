from typing import Callable, List

from qm.qua import for_, while_, wait, assign

from qcore.elements import element, Readout
from qcore.expvariable import ExpVar
from qcore.sweep import Sweep

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
                # save sweep variables
                for var in ordered_sweep_list:
                    var.save()
            else:
                construct_sweep(curr_idx=(curr_idx + 1))

    construct_sweep_rec(curr_idx=0)

def repeat_until_true(q_var: ExpVar, pulse_seq: Callable):

    with while_(q_var):
        pulse_seq()

def wait_for_reset(I: ExpVar,
                   Q: ExpVar,
                   is_e_state: ExpVar,
                   thr: float,
                   wait_time: int,
                   rr: Readout
                   ):

    rr.measure((I.q_var, Q.q_var))
    assign(is_e_state, I.q_var > thr)
    with while_(is_e_state):
        wait(int(wait_time // 4), rr.name)
        rr.measure((I.q_var, Q.q_var))
        assign(is_e_state, I.q_var > thr)
