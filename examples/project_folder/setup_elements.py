""" Script to update parameters of existing elements """

# %% define configfolder and configfile
from pathlib import Path
configfolder = Path.cwd()

# %% update existing readout element parameters
from qcore.helpers.stage import Stage
from qcore.pulses import *
readout_configpath = configfolder / "readout.yml"
with Stage(readout_configpath) as stage:
    readout = stage.get("RR")
    readout.ports = {"I": 3, "Q": 4}
    readout.int_freq = -50e6

    readout_pulse = readout.get_operations("readout_pulse")
    readout_pulse.length = 600
    readout_pulse.pad = 400
    readout_pulse.I_ampx = 0.2

# %% create new element and save it to yml by staging it with a given configpath
from qcore.helpers.stage import Stage
from qcore.elements import Qubit, Readout
configpath = configfolder / "elements.yml"
qubit = Qubit(name="QUBIT", lo_name="LO_QUBIT", ports={"I": 1, "Q": 2})
readout = Readout(name="RR", lo_name="LO_RR", ports={"I": 3, "Q": 4})
with Stage(qubit, readout, configpath=configpath) as stage:
    pass

# %%
