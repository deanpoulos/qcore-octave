""" """

from labctrl import Resource


class DigitalWaveform(Resource):
    """ """

    DEFAULT_SAMPLES: list[tuple[int, int]] = [(1, 0)]

    def __init__(self, name: str, samples: list[tuple[int, int]] = None) -> None:
        """ """
        # [(value, length)] where value = 0 (LOW) or 1 (HIGH) and length is in ns
        # length = 0 means value will be played for remaining duration of the waveform
        self.samples = DigitalWaveform.DEFAULT_SAMPLES if samples is None else samples
        super().__init__(name=name)
