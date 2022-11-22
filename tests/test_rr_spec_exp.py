from qm.qua import fixed, program, stream_processing
from pathlib import Path
from qcore.elements import Readout
from qcore.experiment import Experiment
from qcore.variables.variable import Variable
from qcore.variables.sweep import Sweep
from qcore.sequences.rr_spec import rr_spec
from qcore.sequences.constructors import construct_sweep
from qcore.instruments import QM
from qcore.variables.dataset import Dataset
import numpy as np
from qcore.helpers.stage import Stage

from examples.project_folder.config import CONFIGPATHS


class RR_Spec(Experiment):
    def __init__(self, rr: Readout, **kwargs):
        self.rr = rr
        self.init_variables()
        super().__init__(name="rr_spec", **kwargs)

    def init_variables(self):

        self.freq = Sweep(
            start=int(-60e6),
            stop=int(-40e6),
            step=int(0.5e6),
            var_type=int,
            include_endpoint=True,
            name="freq",
            units="Hz",
        )

        # define datasets
        self.I = Dataset(axes=[self.N, self.freq], name="I", var_type=fixed)
        self.Q = Dataset(axes=[self.N, self.freq], name="Q", var_type=fixed)

        # for derived datasets, include initial data for calculating running total
        init_data = np.zeros(self.freq.length)
        self.iq_avg = Dataset(axes=[self.freq], name="IQ_AVG", data=init_data)
        self.magnitude = Dataset(
            axes=[self.freq], name="MAGNITUDE", units="dB", data=init_data
        )
        self.phase = Dataset(
            axes=[self.freq], name="PHASE", units="rad", data=init_data
        )

    def pulse_sequence(self):

        rr_spec(self.I, self.Q, self.rr, self.freq)

    def process_data(self, data, current_count, last_count):
        """this is INSIDE the fetch loop!!! use for live processing only!!!"""
        # while saving, assume sweep order and dimension and dataset axes order and dimension is consistent
        
        #self.I.data = data["I"]
        #self.I.index = (slice(last_count, current_count), slice(None, None)...)
        #self.I_avg.data = weighted_average(data["I_avg"])
        """
        # save frequency data
        datasaver.save_data(self.freq, data["freq"])

        # save raw I and Q data at the correct position
        pos = slice(last_count, current_count)
        datasaver.save_data(self.I, data["I"], index=(pos, ...))
        datasaver.save_data(self.Q, data["Q"], index=(pos, ...))

        # calculate and store derived datasets for plotting
        num_batches = current_count - last_count  # for weighted averages
        i_avg, q_avg = np.average(data["I"], axis=0), np.average(data["Q"], axis=0)
        iq_avg = i_avg + 1j * q_avg
        self.iq_avg.data = (
            last_count * self.iq_avg.data + num_batches * iq_avg
        ) / current_count

        phase = np.unwrap(np.angle(data["I"] + 1j * data["Q"]))
        phase_avg = np.average(phase, axis=0)
        self.phase.data = (
            last_count * self.phase.data + num_batches * phase_avg
        ) / current_count

        magnitude = 20 * np.log10(np.abs(data["I"] + 1j * data["Q"]))
        magnitude_avg = np.average(magnitude, axis=0)
        self.magnitude.data = (
            last_count * self.magnitude.data + num_batches * magnitude_avg
        ) / current_count

        # live plot datasets
        self.plotter.plot()
        """

if __name__ == "__main__":

    with Stage(*CONFIGPATHS, remote=False) as stage:

        # retrieve resources from stage
        rr, lo_rr = stage.get("RR", "LO_RR")

        # configure instruments
        lo_rr.configure(frequency=7.582e9, power=13.0, output=True)
        qm = QM(elements=(rr,), oscillators=(lo_rr,))

        qm_config = qm.get_config()

        # initialize experiments, choose which datasets to plot/save, and run!
        savefolder = Path.cwd() / "config/myproject/data"
        expt = RR_Spec(rr=rr, qm=qm, savefolder=savefolder)
        expt.run(save=(expt.I, expt.Q), plot=(expt.iq_avg, expt.magnitude, expt.phase))

    experiment_parameters = {
        "reps": 300000,
        "wait_time": 400000,
    }
