""" """

from qcore.elements.rf_switch import RFSwitch
from qcore.helpers import logger
from qcore.pulses.pulse import Pulse
from qcore.pulses.digital_waveform import DigitalWaveform
from qcore.pulses.readout_pulse import ReadoutPulse
from qcore.resource import Resource


class Element(Resource):
    """ """

    PORTS_KEYS = ("I", "Q")
    OFFSETS_KEYS = (*PORTS_KEYS, "G", "P")
    RF_SWITCH_DIGITAL_MARKER = "RFSWITCH_ON"

    def __init__(
        self,
        name: str,
        lo_name: str,
        ports: dict[str, int],
        int_freq: float = -50e6,
        **parameters,
    ) -> None:
        """ """
        self.lo_name: str = str(lo_name)
        self.int_freq: float = int_freq

        self._ports: dict[str, int] = dict.fromkeys(Element.PORTS_KEYS)
        self._mixer_offsets: dict[str, float] = dict.fromkeys(Element.OFFSETS_KEYS, 0.0)
        self._rf_switch: RFSwitch = None
        self._rf_switch_on: bool = False
        self._operations: list[Pulse] = []

        super().__init__(name=name, ports=ports, **parameters)

    @property
    def ports(self) -> dict[str, int]:
        """ """
        return self._ports.copy()

    @ports.setter
    def ports(self, value: dict[str, int]) -> None:
        """ """
        try:
            for key in value.keys():
                if key not in Element.PORTS_KEYS:
                    message = f"Invalid port {key = }, valid keys: {Element.PORTS_KEYS}."
                    raise KeyError(message)
        except (AttributeError, TypeError):
            message = f"Expect {dict[str, int]} with keys: {Element.PORTS_KEYS}."
            raise ValueError(message) from None

        if value:
            self._ports = value
            logger.debug(f"Set {self} ports: {value}.")

    def has_mixed_inputs(self) -> bool:
        """ """
        return self._ports["I"] is not None and self._ports["Q"] is not None

    @property
    def mixer_offsets(self) -> dict[str, float]:
        """ """
        return self._mixer_offsets.copy()

    @mixer_offsets.setter
    def mixer_offsets(self, value: dict[str, float]) -> None:
        """ """
        try:
            for key in value.keys():
                if key not in Element.OFFSETS_KEYS:
                    msg = f"Invalid {key = }, valid offset keys: {Element.OFFSETS_KEYS}."
                    raise KeyError(msg)
        except (AttributeError, TypeError):
            message = f"Expect {dict[str, float]} with keys: {Element.OFFSETS_KEYS}."
            raise ValueError(message) from None

        if value:
            self._mixer_offsets = value
            logger.debug(f"Set {self} mixer offsets: {value}.")

    @property
    def rf_switch(self) -> RFSwitch:
        """ """
        return self._rf_switch

    @rf_switch.setter
    def rf_switch(self, value: RFSwitch) -> None:
        """ """
        if value is not None and not isinstance(value, RFSwitch):
            raise ValueError(f"Invalid {value = }, must be of {RFSwitch}")
        self._rf_switch = value
        logger.debug(f"Set {self} rf switch: {value}.")

    @property
    def rf_switch_on(self) -> bool:
        """ """
        return self._rf_switch_on

    @rf_switch_on.setter
    def rf_switch_on(self, value: bool) -> None:
        """ """
        if self._rf_switch is not None:
            for operation in self._operations:
                if not isinstance(operation, ReadoutPulse):
                    marker = DigitalWaveform(Element.RF_SWITCH_DIGITAL_MARKER)
                    operation.digital_marker = marker if value else None
            self._rf_switch_on = bool(value)

    @property
    def operations(self) -> list[Pulse]:
        """ """
        return self._operations.copy()

    @operations.setter
    def operations(self, value: list[Pulse]) -> None:
        """ """
        try:
            for pulse in value:
                if not isinstance(pulse, Pulse):
                    raise ValueError(f"Invalid value '{pulse}', must be of {Pulse}")
        except TypeError:
            raise ValueError(f"Setter expects {list[Pulse]}.") from None

        operation_names = {operation.name for operation in value}
        if len(operation_names) != len(value):
            raise ValueError(f"All Pulses must have a unique name in '{value}'.")

        if value:
            self._operations = value
            logger.debug(f"Set {self} ops: {operation_names}.")

    def add_operations(self, value: list[Pulse]) -> None:
        """ """
        try:
            self.operations = [*self._operations, *value]
        except TypeError:
            raise ValueError(f"Setter expects {list[Pulse]}.") from None

    def remove_operations(self, *names: str) -> None:
        """ """
        operation_dict = {operation.name: operation for operation in self._operations}
        for name in names:
            if name in operation_dict:
                self._operations.remove(operation_dict[name])
                logger.debug(f"Removed {self} operation named '{name}'.")
            else:
                logger.warning(f"Operation '{name}' does not exist for {self}")

    def get_operations(self, *names: str) -> list[Pulse]:
        """ """
        operation_dict = {operation.name: operation for operation in self._operations}
        return [operation_dict[name] for name in names if name in operation_dict]

    def play(self) -> None:
        """ """
