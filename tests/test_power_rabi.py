""" Let's write a functioning Power Rabi script with the new class organization """

import pprint

from qcore.elements import Qubit, Readout
from qcore.instruments import QM
from qcore.pulses import ConstantPulse, GaussianPulse

if __name__ == "__main__":

    # initialize a Qubit element
    qubit = Qubit(
        name="QUBIT",
        lo_name="LB_QUBIT",
        ports={"I": 1, "Q": 2},
        int_freq=-50e6,
        operations=[
            ConstantPulse(name="saturation_pulse", length=5000, I_ampx=1.0, Q_ampx=0.0),
            GaussianPulse(name="gaussian_pulse", sigma=200, chop=6, I_ampx=1.0),
        ],
    )

    # initialize a Readout element
    readout = Readout(
        name="RR",
        lo_name="RR_QUBIT",
        ports={"I": 3, "Q": 4, "out": 1},
        int_freq=-50e6,
    )

    pprint.pp(qubit.snapshot())
    
    pprint.pp(readout.snapshot())

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
