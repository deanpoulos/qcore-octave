""" """
import pathlib
from qcore.elements import Cavity, Qubit, Readout, RFSwitch
from qcore.instruments.quantum_machines import QMConfigBuilder
from qcore.pulses import (
    ConstantPulse,
    GaussianPulse,
    NumericalPulse,
    RampedConstantPulse,
    ConstantReadoutPulse,
    GaussianReadoutPulse,
)
from labctrl import Stage

# simulated LOs
class FakeLO:
    def __init__(self, name, frequency) -> None:
        self.name, self.frequency = name, frequency


lo_rr = FakeLO(name="lo_rr", frequency=8e9)
lo_qubit = FakeLO(name="lo_qubit", frequency=5e9)
lo_cavity = FakeLO(name="lo_cavity", frequency=7e9)

# Readout
rr = Readout(name="RR", lo_name="lo_rr", ports={"I": 1, "Q": 2})

# Qubit
qubit = Qubit(name="QUBIT", lo_name="lo_qubit", ports={"I": 3, "Q": 4})
qubit_rf_switch = RFSwitch(name="qubit_rf_switch", port=1)
qubit.rf_switch = qubit_rf_switch
qubit.rf_switch_on = True

# Cavity
cavity = Cavity(name="CAVITY", lo_name="lo_cavity", ports={"I": 5, "Q": 6})

# QM config
qcb = QMConfigBuilder()
config = qcb.build_config(modes=(rr, qubit, cavity), los=(lo_rr, lo_qubit, lo_cavity))
with open(pathlib.Path().cwd() / "config/qmc.py", "w+") as file:
    file.write("config = ")
    file.write(str(config))

with Stage("test", remote=False) as stage:
    print(stage.resources)
