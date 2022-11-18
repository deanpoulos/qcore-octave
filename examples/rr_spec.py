""" How to run a simple experiment using the qcore codebase """

from pathlib import Path

# resources = Elements, Instruments, Pulses, any 'entities' used in an Experiment
# Resource configuration to be done in users' project folders before running experiment
# Data will be saved to project_folder/data/{date}/{time}{experiment_name}.hdf5

experiment_parameters = {
    # for staging project-specific Resources from yml files and saving hdf5 datafiles
    "project_folder": Path.cwd() / "examples/project_folder",
    # map experiment-specific Resource keywords to appropriate names of staged Resources
    "readout": "RR",
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

"""this is to test metadata saving
configpath = experiment_parameters["project_folder"] / "elements.yml"
with Stage(configpath) as stage:
    readout = stage.get("RR")
    temp_path = experiment_parameters["project_folder"] / "1.hdf5"
    snapshot = readout.snapshot(flatten=True)
    snapshot["new"] = [{"hi": 1, "bye": 2}, (4, 5, 3.4, 1.0), ["this", "is", "awesome"]]
    with Datasaver(temp_path) as datasaver:
        datasaver.save_metadata({readout.name: snapshot})
"""