""" """

from collections import defaultdict
from copy import deepcopy
from typing import Any

from labctrl.logger import logger
import numpy as np

import qcore.elements.iq_mixer as iq_mixer
from qcore.elements.mode import Mode
from qcore.elements.readout import Readout
from qcore.instruments.vaunix.lms import LMS


class QMConfigBuildingError(Exception):
    """ """


class QMConfig(defaultdict):
    """
    https://qm-docs.qualang.io/introduction/config
    Single controller
    """

    MIN_OUTPUT_PORTS: int = 1
    MAX_OUTPUT_PORTS: int = 10
    MIN_INPUT_PORTS: int = 1
    MAX_INPUT_PORTS: int = 2
    MIN_WAVEFORM_VOLTAGE: float = -0.5  # V
    MAX_WAVEFORM_VOLTAGE: float = 0.5
    MIN_MCM_VALUE: float = -2.0  # MCM means mixer correction matrix
    MAX_MCM_VALUE: float = 2 - 2**-16
    CLOCK_CYCLE: int = 4  # ns, also defined in qcore.pulses.pulse.Pulse
    MIN_TIME_OF_FLIGHT: int = 24  # ns
    MIN_PULSE_LENGTH: int = 16  # ns

    def __init__(self) -> None:
        """ """
        super().__init__(QMConfig)
        self["version"] = 1
        self["controllers"] = {"con1": {"type": "opx1"}}

    def __repr__(self) -> str:
        """ """
        return repr(dict(self))

    def check_bounds(self, value: float, min: float, max: float, key: str) -> None:
        """ """
        try:
            in_bounds = min <= value <= max
        except TypeError:
            message = f"Invalid type for {key} {value = }, must be a number"
            raise ValueError(message) from None
        else:
            if not in_bounds:
                raise ValueError(f"{key} {value = } out of bounds: [{min}, {max}].")

    def check_voltage_bounds(self, value: float, key: str) -> None:
        """ """
        min, max = QMConfig.MIN_WAVEFORM_VOLTAGE, QMConfig.MAX_WAVEFORM_VOLTAGE
        self.check_bounds(value, min, max, key)

    def check_output_port_bounds(self, value: int, key: str) -> None:
        """ """
        min, max = QMConfig.MIN_OUTPUT_PORTS, QMConfig.MAX_OUTPUT_PORTS
        self.check_bounds(value, min, max, key)

    def check_input_port_bounds(self, value: int, key: str) -> None:
        """ """
        min, max = QMConfig.MIN_INPUT_PORTS, QMConfig.MAX_INPUT_PORTS
        self.check_bounds(value, min, max, key)

    def check_mcm_bounds(self, mcm: tuple[float, float, float, float]) -> None:
        """ """
        min, max = QMConfig.MIN_MCM_VALUE, QMConfig.MAX_MCM_VALUE
        for value in mcm:
            self.check_bounds(value, min, max, "Mixer correction matrix")

    def check_tof_bounds(self, value: int) -> None:
        """ """
        min, max = QMConfig.MIN_TIME_OF_FLIGHT, np.inf
        self.check_bounds(value, min, max, "Time of flight")

    def cast(self, value: Any, cls: Any, key: str) -> Any:
        """ """
        try:
            return cls(value)
        except (TypeError, ValueError):
            raise ValueError(f"Failed to cast {key} {value = } to {cls}, invalid type.")

    def set_ports(self, mode: Mode) -> None:
        """ """
        ports = mode.ports
        for port_key, port_num in ports.items():
            if port_num is not None:
                self.set_controller_port(mode, port_key, port_num)
                self.set_element_port(mode, port_key, port_num)

    def set_controller_port(self, mode: Mode, port_key: str, port_num: int) -> None:
        """ """
        dc_offset = mode.mixer_offsets[port_key]
        self.check_voltage_bounds(dc_offset, "DC offset voltage")

        if port_key in ("I", "Q"):
            self.set_analog_output_port(port_num, dc_offset)
        elif port_key == "out":
            self.set_analog_input_port(port_num, dc_offset)
        else:
            raise ValueError(f"Invalid {port_key = }, must be in ('I', 'Q', 'out').")

        rf_switch = mode.rf_switch
        if rf_switch is not None:
            self.set_digital_output_port(rf_switch.port, rf_switch.name)

    def set_analog_output_port(self, number: int, offset: float) -> None:
        """ """
        self.check_output_port_bounds(number, "Analog output port")
        controllers_config = self["controllers"][QMConfig.CONTROLLER_NAME]
        controllers_config["analog_outputs"][number]["offset"] = offset
        logger.debug(f"Set controller analog output port {number = } with {offset = }.")

    def set_analog_input_port(self, number: int, offset: float) -> None:
        """ """
        self.check_input_port_bounds(number, "Analog input port")
        controllers_config = self["controllers"][QMConfig.CONTROLLER_NAME]
        controllers_config["analog_inputs"][number]["offset"] = offset
        logger.debug(f"Set controller analog input port {number = } with {offset = }.")

    def set_digital_output_port(self, number: int) -> None:
        """ """
        self.check_output_port_bounds(number, "Digital output port")
        controllers_config = self["controllers"][QMConfig.CONTROLLER_NAME]
        controllers_config["digital_outputs"][number] = {}
        logger.debug(f"Set controller digital output port {number = }.")

    def set_element_port(self, mode: Mode, key: str, number: int) -> None:
        """ """
        if key not in Readout.PORTS_KEYS:
            raise ValueError(f"Invalid port {key = }, must be in {Readout.PORTS_KEYS}.")

        element_config = self["elements"][mode.name]
        port_config = (QMConfig.CONTROLLER_NAME, number)
        if key == "out":
            element_config["outputs"][key + str(number)] = port_config
        elif key in ("I", "Q") and mode.has_mix_inputs():
            element_config["mixInputs"][key] = port_config
        elif key == "I":
            element_config["singleInput"]["port"] = port_config
        else:
            raise ValueError(f"Invalid port {key = } and {number = } for {mode}.")
        logger.debug(f"Set '{mode.name}' port {key = } and {number = }.")

    def set_mixer(self, mode: Mode, int_freq: float, lo_freq: float) -> None:
        """ """
        ports, offsets = mode.ports, mode.mixer_offsets
        mixer_name = f"mixer_{ports['I']}{ports['Q']}"

        mixer_correction_matrix = iq_mixer.correction_matrix(offsets["G"], offsets["P"])
        self.check_mcm_bounds(mixer_correction_matrix)
        mixer_config = {
            "intermediate_frequency": int(int_freq),
            "lo_frequency": int(lo_freq),
            "correction": mixer_correction_matrix,
        }
        if mixer_name in self["mixers"]:
            self["mixers"][mixer_name].append(mixer_config)
        else:
            self["mixers"][mixer_name] = [mixer_config]

        self["elements"][mode.name]["mixInputs"]["mixer"] = mixer_name
        logger.debug(f"Set {mode} {mixer_config = }.")

    def set_intermediate_frequency(self, name: str, value: float) -> None:
        """ """
        int_freq = self.cast(value, int, "intermediate frequency")
        self["elements"][name]["intermediate_frequency"] = int_freq
        logger.debug(f"Set {name} {int_freq = }.")

    def set_lo_frequency(self, name: str, value: float) -> None:
        """ """
        lo_freq = self.cast(value, int, "lo frequency")
        self["elements"][name]["mixInputs"]["lo_frequency"] = lo_freq
        logger.debug(f"Set {name} {lo_freq = }.")

    def set_time_of_flight(self, name: str, value: int) -> None:
        """ """
        self.check_tof_bounds(value)
        tof, cycle = int(value), QMConfig.CLOCK_CYCLE
        if tof % cycle != 0:
            tof = cycle * round(tof / cycle)
            logger.warning(f"{name} time of flight rounded to multiple of {cycle}.")

        self["elements"][name]["time_of_flight"] = tof
        logger.debug(f"Set {name} time of flight from to {tof}.")

    def set_smearing(self, name: str, value: int) -> None:
        """ """
        smearing = self.cast(value, int, "smearing")
        self["elements"][name]["smearing"] = smearing
        logger.debug(f"Set {name} {smearing = }.")

    def set_operations(self, *modes: Mode) -> None:
        """ """


class QMConfigBuilder:
    """ """

    def __init__(self) -> None:
        """ """
        self._config: QMConfig = None  # built by build_config()
        self._modes: tuple[Mode] = None
        self._lo_frequencies: dict[str, float] = {}

    def build_config(self, modes: tuple[Mode], los: tuple[LMS]) -> QMConfig:
        """ """
        try:
            self._check_modes(*modes)
            self._check_local_oscillators(*los)
        except TypeError:
            message = f"Expect tuple arguments for 'modes' and 'los'."
            raise QMConfigBuildingError(message) from None
        else:
            self._config = QMConfig()
            self._build_config()
            return deepcopy(self._config)

    def _build_config(self) -> None:
        """ """
        config, modes, lo_freqs = self._config, self._modes, self._lo_frequencies
        for mode in modes:
            config.set_ports(mode)
            config.set_intermediate_frequency(mode.name, mode.int_freq)

            if mode.has_mix_inputs():
                if mode.name not in lo_freqs:
                    message = f"No LO frequency specified for {mode = }."
                    raise QMConfigBuildingError(message)
                config.set_lo_frequency(mode.name, lo_freqs[mode.name])

                config.set_mixer(mode, mode.int_freq, lo_freqs[mode.name])

            if isinstance(mode, Readout):
                config.set_time_of_flight(mode.name, mode.tof)
                config.set_smearing(mode.name, mode.smearing)

            # SET OPERATIONS

    def _check_modes(self, *modes: Mode) -> None:
        """ """
        mode_names = []
        for mode in modes:
            if not isinstance(mode, Mode):
                message = f"Invalid {mode = }, must be of {Mode}."
                raise QMConfigBuildingError(message)
            name = mode.name
            if name in mode_names:
                message = f"Found duplicate mode {name = }, mode names must be unique."
                raise QMConfigBuildingError(message)
            mode_names.append(name)
        self._modes = modes

    def _check_local_oscillators(self, *los: LMS) -> None:
        """ """
        for lo in los:
            try:
                self._lo_frequencies[lo.name] = lo.frequency
            except AttributeError:
                message = f"Invalid {lo = }, missing 'name' and 'frequency' attributes."
                raise QMConfigBuildingError(message) from None
