""" Let's write a functioning Power Rabi script with the new class organization """

from pathlib import Path
import pprint

from qcore.elements import Qubit, Readout
from qcore.helpers.stage import Stage
from qcore.instruments import QM
from qcore.pulses import ConstantPulse, GaussianPulse

if __name__ == "__main__":

    configfolder = Path.cwd() / "config/myproject"
    configfiles = ["readout.yml", "instruments.yml"]
    configpaths = [configfolder / configfile for configfile in configfiles]

    with Stage(*configpaths, remote=False) as stage:
        readout, lo_rr = stage.get("RR", "LO_RR")
        qm = QM(elements=(readout,), oscillators=(lo_rr,))
        pprint.pp(qm.snapshot())
        pprint.pp(qm.get_config())

    # assemble your device here
    # Device()
    # initialize elements Qubit()
    # add elements
    # initialize QM with elements

    # set run time param values
    # set sequence(), pick and choose qua snippets from library compose them
    # define raw datasets (depends for eg on number of resonators)
    # in the background, we run, fetch, save, and then load for live plot and analysis
    # live plot fn - ability to choose fit fn and display text
    # run ur experiment and get raw data
    # optional analysis fn where you can plot
    #
