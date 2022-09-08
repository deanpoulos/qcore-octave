""" """

from labctrl import Resource
from labctrl.logger import logger

from qcore.elements.rf_switch import RFSwitch
from qcore.pulses.pulse import Pulse
from qcore.pulses.digital_waveform import DigitalWaveform


class Mode(Resource):
    """ """

    PORTS_KEYS = ("I", "Q")
    OFFSETS_KEYS = (*PORTS_KEYS, "G", "P")
    RF_SWITCH_DIGITAL_MARKER_NAME = "RFSWITCH ON"

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

        self._ports: dict[str, int] = dict.fromkeys(Mode.PORTS_KEYS)
        self._mixer_offsets: dict[str, float] = dict.fromkeys(Mode.OFFSETS_KEYS, 0.0)
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
                if key not in Mode.PORTS_KEYS:
                    message = f"Invalid port {key = }, valid keys: {Mode.PORTS_KEYS}."
                    raise KeyError(message)
        except (AttributeError, TypeError):
            message = f"Expect {dict[str, int]} with keys: {Mode.PORTS_KEYS}."
            raise ValueError(message) from None
        else:
            self._ports = value
            logger.debug(f"Set {self} ports: {value}.")

    @property
    def mixer_offsets(self) -> dict[str, float]:
        """ """
        return self._mixer_offsets.copy()

    @mixer_offsets.setter
    def mixer_offsets(self, value: dict[str, float]) -> None:
        """ """
        try:
            for key in value.keys():
                if key not in Mode.MIXER_OFFSETS_KEYS:
                    msg = f"Invalid {key = }, valid offset keys: {Mode.OFFSETS_KEYS}."
                    raise KeyError(msg)
        except (AttributeError, TypeError):
            message = f"Expect {dict[str, float]} with keys: {Mode.OFFSETS_KEYS}."
            raise ValueError(message) from None
        else:
            self._mixer_offsets = value
            logger.debug(f"Set {self} mixer offsets: {value}.")

    @property
    def rf_switch(self) -> RFSwitch:
        """ """
        return self._rf_switch

    @rf_switch.setter
    def rf_switch(self, value: RFSwitch) -> None:
        """ """
        if not isinstance(value, RFSwitch):
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
        if value:
            for operation in self._operations:
                digital_marker = DigitalWaveform(Mode.RF_SWITCH_DIGITAL_MARKER_NAME)
                operation.add_digital_markers(digital_marker)
            self._rf_switch_on = True
        else:
            for operation in self._operations:
                operation.remove_digital_markers(Mode.RF_SWITCH_DIGITAL_MARKER_NAME)
            self._rf_switch_on = False

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
        else:
            operation_names = {operation.name for operation in value}
            if len(operation_names) != len(value):
                raise ValueError(f"All Pulses must have a unique name in '{value}'.")
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
