""" """

from labctrl import Resource


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
    ) -> None:
        """ """
        self.length: int = length
        self.pad: int = pad

        self.I_ampx: float = I_ampx
        self.Q_ampx: float = Q_ampx

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
