""" """

from pathlib import Path

from labctrl import Resource
from labctrl.logger import logger
import labctrl.yamlizer as yml

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
        self._ops: dict[str, Pulse] = {}

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
                    logger.error(message)
                    raise KeyError(message)
        except (AttributeError, TypeError):
            message = f"Expect {dict[str, int]} with keys: {Mode.PORTS_KEYS}."
            logger.error(message)
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
                    logger.error(msg)
                    raise KeyError(msg)
        except (AttributeError, TypeError):
            message = f"Expect {dict[str, float]} with keys: {Mode.OFFSETS_KEYS}."
            logger.error(message)
            raise ValueError(message) from None
        else:
            self._mixer_offsets = value
            logger.debug(f"Set {self} mixer offsets: {value}.")

    @property
    def ops(self) -> list[str | Pulse]:
        """ """
        return self._ops.copy()

    @ops.setter
    def ops(self, value: dict[str | Pulse]) -> None:
        """ """
        try:
            for pulse in value.values():
                if not isinstance(pulse, Pulse):
                    message = f"Invalid value '{pulse}', must be of {Pulse}"
                    logger.error(message)
                    raise ValueError(message)
        except TypeError:
            message = f"Setter expects {dict[str, Pulse]}."
            logger.error(message)
            raise ValueError(message) from None
        else:
            self._ops = value
            logger.debug(f"Set {self} ops: {value}.")

    def add_ops(self, value: dict[str | Pulse]) -> None:
        """ """
        try:
            for name in value.keys():
                if name in self._ops:
                    message = f"An op with {name = } already exists for {self}."
                    logger.error(message)
                    raise ValueError(message)
        except TypeError:
            message = f"Setter expects {dict[str, Pulse]}."
            logger.error(message)
            raise ValueError(message) from None
        else:
            self.ops = self._ops | value

    def remove_ops(self, *names: str) -> None:
        """ """
        for name in names:
            if name in self._ops:
                del self._ops[name]
                logger.debug(f"Removed {self} op named '{name}'.")
            else:
                logger.warning(f"Op named '{name}' does not exist for {self}")

    def get_ops(self, *names: str) -> dict[str, Pulse]:
        """ """
        return {name: self._ops[name] for name in names if name in self._ops}

    def play(self) -> None:
        """ """
