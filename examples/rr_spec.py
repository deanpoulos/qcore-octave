""" How to run a simple experiment using the qcore codebase """

from pathlib import Path

# resources = Elements, Instruments, Pulses, any 'entities' used in an Experiment
# Resource configuration should be done in users' project folders prior to running the experiment
# Data will be saved to project_folder/data/{date}/{time}{experiment_name}.hdf5

experiment_parameters = {
    # for staging project-specific Resources from yml files and saving hdf5 datafiles
    "project_folder": Path.cwd() / "examples/project_folder",
    # to select experiment-specific Resources by name from all staged Resources
    "resources": ["RR1", "RR2"],
    # number of repetitions of this experiment run
    "repetitions": 100,
    # wait time between successive repetitions of the experiment's pulse sequence
    "wait_time": 20000,  # in nanoseconds
    # wait time between successive calls to fetch data during live save/plot
    "fetch_interval": 1,  # in seconds
}












from qcore.helpers.stage import Stage
from qcore.helpers.datasaver import Datasaver
from qcore.pulses.pulse import Pulse
import pprint

readout_configpath = experiment_parameters["project_folder"] / "readout.yml"
with Stage(readout_configpath) as stage:
    readout = stage.get("RR")
    temp_path = experiment_parameters["project_folder"] / "1.hdf5"
    snapshot = readout.snapshot()
    p,  = readout.get_operations("readout_pulse")
    pprint.pp(snapshot)
    pprint.pp(p.snapshot())

