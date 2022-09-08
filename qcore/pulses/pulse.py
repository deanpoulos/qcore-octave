""" """

from labctrl import Resource
from labctrl.logger import logger

from qcore.pulses.digital_waveform import DigitalWaveform


class Pulse(Resource):
    """ """

    BASE_AMP = 0.2  # in V
    CLOCK_CYCLE = 4  # in ns

    def __init__(
        self,
        name: str,
        length: int,
        I_ampx: float,
        Q_ampx: None | float,  # set None for single waveform pulses
        pad: int,
        digital_markers: list[DigitalWaveform] = None,
    ) -> None:
        """ """
        self.length: int = length
        self.pad: int = pad

        self.I_ampx: float = I_ampx
        self.Q_ampx: float = Q_ampx

        self._digital_markers = [] if digital_markers is None else digital_markers

        super().__init__(name=name)

    @property
    def total_length(self) -> int:
        """ """
        return self.length + self.pad

    def has_mixed_waveforms(self) -> bool:
        """ """
        return self.Q_ampx is not None

    def sample(self) -> tuple[float, float | None] | tuple[list, list | None]:
        """ """
        raise NotImplementedError("Subclasses must implement 'sample()'.")

    @property
    def digital_markers(self) -> list[DigitalWaveform]:
        """ """
        return self._digital_markers.copy()

    @digital_markers.setter
    def digital_markers(self, value: list[DigitalWaveform]) -> None:
        """ """
        try:
            for marker in value:
                if not isinstance(marker, DigitalWaveform):
                    message = f"Invalid value '{marker}', must be of {DigitalWaveform}"
                    raise ValueError(message)
        except TypeError:
            raise ValueError(f"Setter expects {list[DigitalWaveform]}.") from None
        else:
            marker_names = {marker.name for marker in value}
            if len(marker_names) != len(value):
                message = f"All digital markers must have a unique name in '{value}'."
                raise ValueError(message)
            self._digital_markers = value
            logger.debug(f"Set {self} digital markers: {marker_names}.")

    def add_digital_markers(self, value: list[DigitalWaveform]) -> None:
        """ """
        try:
            self.digital_markers = [*self._digital_markers, *value]
        except TypeError:
            raise ValueError(f"Setter expects {list[DigitalWaveform]}.") from None

    def remove_digital_markers(self, *names: str) -> None:
        """ """
        marker_dict = {marker.name: marker for marker in self._digital_markers}
        for name in names:
            if name in marker_dict:
                self._digital_markers.remove(marker_dict[name])
                logger.debug(f"Removed {self} digital marker named '{name}'.")
            else:
                logger.warning(f"Digital marker '{name}' does not exist for {self}")
