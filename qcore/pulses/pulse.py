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
        digital_marker: DigitalWaveform | None = None,
    ) -> None:
        """ """
        self.length: int = length
        self.pad: int = pad

        self.I_ampx: float = I_ampx
        self.Q_ampx: float = Q_ampx

        self._digital_marker = digital_marker

        super().__init__(name=name)

    @property
    def total_length(self) -> int:
        """ """
        return self.length + self.pad

    def has_mixed_waveforms(self) -> bool:
        """ """
        return self.I_ampx is not None and self.Q_ampx is not None

    def sample(self) -> tuple[float, float | None] | tuple[list, list | None]:
        """ """
        raise NotImplementedError("Subclasses must implement 'sample()'.")

    @property
    def digital_marker(self) -> DigitalWaveform | None:
        """ """
        return self._digital_marker

    @digital_marker.setter
    def digital_marker(self, value: DigitalWaveform | None) -> None:
        """ """
        if not isinstance(value, (DigitalWaveform | None)):
            raise ValueError(f"Invalid {value = }, must be {DigitalWaveform | None}.")
        self._digital_marker = value
        logger.debug(f"Set {self} digital marker to {value}.")
