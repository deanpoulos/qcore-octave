""" How to run a simple experiment using the qcore codebase """

from pathlib import Path

from qcore.experiment import Experiment
from qcore.elements import Readout

# resources = Elements, Instruments, Pulses, any 'entities' used in an Experiment
# Resource configuration to be done in users' project folders before running experiment
# Data will be saved to project_folder/data/{date}/{time}{experiment_name}.hdf5


class RR_Spec(Experiment):
    def __init__(self, readout: str, **kwargs):
        super().__init__("rr_spec", readout, wait_element=readout, **kwargs)
        (self.rr,) = self._get_elements()


experiment_parameters = {
    # for staging project-specific Resources from yml files and saving hdf5 datafiles
    "project_folder": Path.cwd() / "examples/project_folder",
    # map experiment-specific Resource keywords to appropriate names of staged Resources
    "readout": "RR",
    # number of repetitions of this experiment run
    "repetitions": 100,
    # wait time between successive repetitions of the experiment's pulse sequence
    "wait_time": 20000,  # in nanoseconds
}

experiment = RR_Spec(**experiment_parameters)
experiment.run()
