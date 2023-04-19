""" """

from collections import defaultdict
from typing import Any

import numpy as np

from qcore.elements.element import Element
from qcore.elements.readout import Readout
from qcore.helpers.logger import logger
from qcore.instruments.drivers.vaunix_lms import LMS
from qcore.pulses.digital_waveform import DigitalWaveform
from qcore.pulses.pulse import Pulse
from qcore.pulses.readout_pulse import ReadoutPulse


class QMConfigBuildingError(Exception):
    """ """


class QMConfig(defaultdict):
    """https://qm-docs.qualang.io/introduction/config"""

    CONTROLLER_NAME: str = "con1"
    MIN_OUTPUT_PORTS: int = 1
    MAX_OUTPUT_PORTS: int = 10
    MIN_INPUT_PORTS: int = 1
    MAX_INPUT_PORTS: int = 2
    MIN_WAVEFORM_VOLTAGE: float = -0.5  # V
    MAX_WAVEFORM_VOLTAGE: float = 0.5
    MIN_MCM_VALUE: float = -2.0  # MCM means mixer correction matrix
    MAX_MCM_VALUE: float = 2 - 2 ** -16
    CLOCK_CYCLE: int = 4  # ns, also defined in qcore.pulses.pulse.Pulse
    MIN_TIME_OF_FLIGHT: int = 24  # ns
    MIN_PULSE_LENGTH: int = 16  # ns
    MAX_PULSE_LENGTH: int = 2 ** 31 - 1  # ns

    def __init__(self) -> None:
        """ """
        super().__init__(QMConfig)

    def __repr__(self) -> str:
        """ """
        return repr(dict(self))

    def set_version(self) -> None:
        """ """
        self["version"] = 1

    def set_ports(self, element: Element) -> None:
        """ """
        self.set_controllers()
        ports = element.ports
        for port_key, port_num in ports.items():
            if port_num is not None:
                self.set_controller_port(element, port_key, port_num)
                self.set_element_port(element, port_key, port_num)

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

    def set_mixer(self, element: Element, int_freq: float, lo_freq: float) -> None:
        """ """
        ports, offsets = element.ports, element.mixer_offsets
        mixer_name = f"mixer_{ports['I']}{ports['Q']}"

        mixer_correction_matrix = self.get_correction_matrix(offsets["G"], offsets["P"])
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

        self["elements"][element.name]["mixInputs"]["mixer"] = mixer_name
        logger.debug(f"Set {element} {mixer_config = }.")

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

    def set_operations(self, element: Element) -> None:
        """ """
        for op_name, pulse in element.operations.items():
            pulse_name = element.name + "." + pulse.name
            self["elements"][element.name]["operations"][op_name] = pulse_name
            self.set_pulse(pulse, pulse_name)

    def cast(self, value: Any, cls: Any, key: str) -> Any:
        """ """
        try:
            return cls(value)
        except (TypeError, ValueError):
            raise ValueError(f"Failed to cast {key} {value = } to {cls}, invalid type.")

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

    def check_pulse_length(self, value: int, key: str) -> None:
        """ """
        min, max = QMConfig.MIN_PULSE_LENGTH, QMConfig.MAX_PULSE_LENGTH
        self.check_bounds(value, min, max, key)

        clock_cycle = QMConfig.CLOCK_CYCLE
        if value % clock_cycle != 0:
            message = f"'{key}' length = {value} must be a multiple of {clock_cycle}"
            raise ValueError(message)

    def set_controllers(self) -> None:
        """ """
        self["controllers"][QMConfig.CONTROLLER_NAME]["type"] = "opx1"

    def set_controller_port(self, element: Element, key: str, port_num: int) -> None:
        """ """
        dc_offset = element.mixer_offsets[key]
        self.check_voltage_bounds(dc_offset, "DC offset voltage")

        if key in ("I", "Q"):
            self.set_analog_output_port(port_num, dc_offset)
        elif key == "out":
            self.set_analog_input_port(port_num, dc_offset)
        else:
            raise ValueError(f"Invalid port {key = }, must be in ('I', 'Q', 'out').")

        rf_switch = element.rf_switch
        if rf_switch is not None:
            self.set_digital_output_port(rf_switch.port)

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

    def set_element_port(self, element: Element, key: str, number: int) -> None:
        """ """
        if key not in Readout.PORTS_KEYS:
            raise ValueError(f"Invalid port {key = }, must be in {Readout.PORTS_KEYS}.")

        element_config = self["elements"][element.name]
        port_config = (QMConfig.CONTROLLER_NAME, number)
        if key == "out":
            element_config["outputs"][key + str(number)] = port_config
        elif key in ("I", "Q") and element.has_mixed_inputs():
            element_config["mixInputs"][key] = port_config
        elif key == "I":
            element_config["singleInput"]["port"] = port_config
        else:
            raise ValueError(f"Invalid port {key = } and {number = } for {element}.")
        logger.debug(f"Set '{element.name}' port {key = } and {number = }.")

    def get_correction_matrix(self, g: float, p: float) -> list[float]:
        """ """
        try:
            cos, sin = np.cos(p), np.sin(p)
            coefficient = 1 / ((1 - g ** 2) * (2 * cos ** 2 - 1))
        except TypeError:
            message = f"Invalid offset value(s): {g = }, {p = }, both must be {float}."
            raise ValueError(message) from None
        else:
            matrix = ((1 - g) * cos, (1 + g) * sin, (1 - g) * sin, (1 + g) * cos)
            return [coefficient * value for value in matrix]

    def set_pulse(self, pulse: Pulse, pulse_name: str) -> None:
        """ """
        pulse_config = self["pulses"][pulse_name]
        pulse_type = "measurement" if isinstance(pulse, ReadoutPulse) else "control"
        pulse_config["operation"] = pulse_type
        self.set_pulse_length(pulse_name, pulse.total_length)

        if pulse.has_mixed_waveforms():
            waveform_I_name = pulse_name + ".waveform." + "I"
            waveform_Q_name = pulse_name + ".waveform." + "Q"
            pulse_config["waveforms"]["I"] = waveform_I_name
            pulse_config["waveforms"]["Q"] = waveform_Q_name
            self.set_waveforms(pulse, waveform_I_name, waveform_Q_name)
        else:
            waveform_name = pulse_name + ".waveform"
            pulse_config["waveforms"]["single"] = waveform_name
            self.set_waveforms(pulse, waveform_name)

        digital_marker = pulse.digital_marker
        if digital_marker is not None:
            marker_name = pulse_name + "." + digital_marker.name
            pulse_config["digital_marker"] = marker_name
            self.set_digital_waveform(digital_marker, marker_name)

        if pulse_type == "measurement" and pulse.has_mixed_waveforms():
            iw_cos_name, iw_sin_name = pulse_name + ".cos", pulse_name + ".sin"
            pulse_config["integration_weights"]["cos"] = iw_cos_name
            pulse_config["integration_weights"]["sin"] = iw_sin_name
            self.set_integration_weights(pulse, iw_cos_name, iw_sin_name)

    def set_pulse_length(self, name: str, value: int) -> None:
        """ """
        length = self.cast(value, int, "pulse length")
        self.check_pulse_length(value, f"Pulse '{name}' length")
        self["pulses"][name]["length"] = length
        logger.debug(f"Set '{name}' {length = }.")

    def set_waveforms(self, pulse: Pulse, wf_i: str, wf_q: str = None) -> None:
        """ """
        i_wave, q_wave = pulse.sample()
        waveform_dict = {wf_i: i_wave, wf_q: q_wave}
        for name, wave in waveform_dict.items():
            if wave is not None:
                try:
                    wave_len = len(wave)
                except TypeError:
                    waveform_type = "constant"
                else:
                    waveform_type = "arbitrary"
                    pulse_len = pulse.total_length
                    if not pulse_len == wave_len:
                        message = f"Unequal '{name}' {wave_len = } and {pulse_len = }."
                        raise ValueError(message)

            self.set_waveform(name, waveform_type, wave)

    def set_waveform(self, name: str, type: str, sample) -> None:
        """ """
        self["waveforms"][name]["type"] = type
        if type == "constant":
            self.set_constant_waveform(name, sample)
        elif type == "arbitrary":
            self.set_arbitrary_waveform(name, sample)

    def set_constant_waveform(self, name: str, sample: float) -> None:
        """ """
        self.check_voltage_bounds(sample, f"'{name}' voltage")
        self["waveforms"][name]["sample"] = sample
        logger.debug(f"Set constant waveform '{name}' with {sample = }.")

    def set_arbitrary_waveform(self, name: str, samples: list[float]) -> None:
        """ """
        self.check_voltage_bounds(min(samples), f"'{name}' voltage")
        self.check_voltage_bounds(max(samples), f"'{name}' voltage")
        self["waveforms"][name]["samples"] = samples
        logger.debug(f"Set arbitrary waveform '{name}' with {len(samples)} samples.")

    def set_digital_waveform(self, waveform: DigitalWaveform, name: str) -> None:
        """ """
        self["digital_waveforms"][name]["samples"] = waveform.samples
        logger.debug(f"Set digital waveform '{name}'.")

    def set_integration_weights(self, pulse: ReadoutPulse, cos: str, sin: str) -> None:
        """ """
        cos_weights, sin_weights = pulse.sample_integration_weights()
        self["integration_weights"][cos] = cos_weights
        self["integration_weights"][sin] = sin_weights


class QMConfigBuilder:
    """ """

    def __init__(self) -> None:
        """ """
        self._config: QMConfig = None  # built by build_config()
        self._elements: tuple[Element] = None
        self._lo_frequencies: dict[str, float] = {}

    def build_config(self, elements: tuple[Element], los: tuple[LMS]) -> QMConfig:
        """ """
        try:
            self._check_elements(*elements)
            self._check_local_oscillators(*los)
        except TypeError:
            message = f"Expect tuple arguments for 'elements' and 'los'."
            raise QMConfigBuildingError(message) from None
        else:
            self._config = QMConfig()
            self._build_config()
            return self._config

    def _build_config(self) -> None:
        """ """
        config, elements, lo_freqs = self._config, self._elements, self._lo_frequencies
        config.set_version()
        config.set_controllers()
        for element in elements:
            config.set_ports(element)
            config.set_intermediate_frequency(element.name, element.int_freq)

            if element.has_mixed_inputs():
                if element.lo_name not in lo_freqs:
                    message = f"No LO frequency specified for {element = }."
                    raise QMConfigBuildingError(message)
                lo_freq = lo_freqs[element.lo_name]
                config.set_lo_frequency(element.name, lo_freq)
                config.set_mixer(element, element.int_freq, lo_freq)

            if isinstance(element, Readout):
                config.set_time_of_flight(element.name, element.time_of_flight)
                config.set_smearing(element.name, element.smearing)

            config.set_operations(element)

    def _check_elements(self, *elements: Element) -> None:
        """ """
        element_names = []
        for element in elements:
            if not isinstance(element, Element):
                message = f"Invalid {element = }, must be of {Element}."
                raise QMConfigBuildingError(message)
            name = element.name
            if name in element_names:
                message = (f"Found duplicate element {name = }, names must be unique.")
                raise QMConfigBuildingError(message)
            element_names.append(name)
        self._elements = elements

    def _check_local_oscillators(self, *los: LMS) -> None:
        """ """
        for lo in los:
            try:
                self._lo_frequencies[lo.name] = lo.frequency
            except AttributeError:
                message = f"Invalid {lo = }, missing 'name' and 'frequency' attributes."
                raise QMConfigBuildingError(message) from None
