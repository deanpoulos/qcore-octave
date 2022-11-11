from qm.qua import fixed, program, stream_processing

from qcore.elements import Readout
from qcore.experiment import Experiment
from qcore.expvariable import ExpVar
from qcore.sweep import Sweep
from qcore.sequences.rr_spec import generate_rr_spec
from qcore.sequences.constructors import construct_sweep


class RR_Spec(Experiment):

    def __init__(self, rr: Readout):
        super().__init__()
        self.rr = rr
    
    def init_variables(self):

        self.I = ExpVar(name='I', var_type=fixed, is_adc=True)
        self.Q = ExpVar(name='Q', var_type=fixed, is_adc=True)
        
        self.freq = Sweep(
            name='freq',
            var_type=int,
            units='Hz',
            start=int(-53e6),
            stop=int(-47e6),
            step=int(0.1e6)
        )

        self.N = Sweep(
            name='N',
            var_type=int,
            start=0,
            stop=50000,
            step=1,
        )

        self.wait_time = 40000
        self.arg_mapping = {
            'freq' : self.freq.q_var
        }
    
    def process_streams(self):

        self.I.process_stream()
        self.Q.process_stream()
        self.freq.process_stream()
        self.N.process_stream()

    def construct_pulse_sequence(self):

        with program() as qua_program:
            self.init_variables()

            rr_spec = generate_rr_spec(self.I, self.Q, self.rr)
            ordered_sweep_list = [self.N, self.freq]

            construct_sweep(
                ordered_sweep_list=ordered_sweep_list,
                pulse_sequence=rr_spec,
                arg_mapping=self.arg_mapping,
                wait_time=self.wait_time,
                wait_elem=self.rr
            )

            with stream_processing:
                self.process_streams()
        
        # add with_stream context here
        return qua_program

