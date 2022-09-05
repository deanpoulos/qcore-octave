""" """

from pathlib import Path

from labctrl import Resource
from labctrl.logger import logger

from qcore.pulses.pulse import Pulse


class Mode(Resource):
    """ """

    PORTS_KEYS = ("I", "Q")
    OFFSETS_KEYS = ("I", "Q", "G", "P")

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
        self._ops: list[Pulse] = []

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
    def ops(self) -> list[Pulse]:
        """ """
        return self._ops.copy()

    @ops.setter
    def ops(self, value: list[Pulse]) -> None:
        """ """
        try:
            for pulse in value:
                if not isinstance(pulse, Pulse):
                    raise ValueError(f"Invalid value '{pulse}', must be of {Pulse}")
        except TypeError:
            raise ValueError(f"Setter expects {list[str, Pulse]}.") from None
        else:
            op_names = {op.name for op in value}
            if len(op_names) != len(value):
                raise ValueError(f"All Pulses must have a unique name in '{value}'.")
            self._ops = value
            logger.debug(f"Set {self} ops: {op_names}.")

    def add_ops(self, value: list[Pulse]) -> None:
        """ """
        try:
            self.ops = [*self._ops, *value]
        except TypeError:
            raise ValueError(f"Setter expects {list[Pulse]}.") from None

    def remove_ops(self, *names: str) -> None:
        """ """
        op_dict = {op.name: op for op in self._ops}
        for name in names:
            if name in op_dict:
                self._ops.remove(op_dict[name])
                logger.debug(f"Removed {self} op named '{name}'.")
            else:
                logger.warning(f"Op named '{name}' does not exist for {self}")

    def get_ops(self, *names: str) -> list[Pulse]:
        """ """
        op_dict = {op.name: op for op in self._ops}
        return [op_dict[name] for name in names if name in op_dict]

    def play(self) -> None:
        """ """
