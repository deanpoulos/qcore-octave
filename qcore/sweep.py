""" """

from __future__ import annotations

import numpy as np

from qcore.expvariable import ExpVar

class Sweep(ExpVar):
    """ """

    def __init__(
        self,
        var_type: type,    # type of sweep variable
        create_stream: bool = True,
        is_adc: bool = False,
        name: str = None,  # name of sweep variable
        units: str = None,  # units attribute sweep points dataset is saved with
        dtype: str = "f4",  # dtype used to save sweep points dataset
        points: list[float] = None,  # discrete sweep points
        sweeps: tuple[Sweep] = None,  # sweep composed of other sweeps
        start: float = None,  # sweep start point
        stop: float = None,  # sweep end point
        step: float = None,  # distance between two sweep points
        endpoint: bool = True,  # whether or not to include end point in sweep
        num: int = None,  # number of points in sweep
        kind: str = "lin",  # "lin" or "log" (base 10) sweep
    ) -> None:
        """ """
        super().__init__(name, var_type, create_stream, is_adc)
        self.name = name
        self.units = units
        self.dtype = dtype
        self.points = points
        self.sweeps = sweeps
        self.start = start
        self.stop = stop
        self.step = step
        self.endpoint = endpoint
        self.num = num
        self.kind = kind

    @property
    def data(self) -> np.ndarray:
        """
        order of precedence when evaluating sweep specification:
        1. sweep with discrete points
        2. sweep composed of other sweeps
        3. sweep with start, stop, step
        4. lin/log sweep with start, stop, num
        """
        if self.points is not None:
            return np.array(self.points)
        elif self.sweeps is not None:
            return np.concatenate([sweep.data for sweep in self.sweeps])
        elif not None in (self.start, self.stop):
            if self.step is not None:
                if self.endpoint:
                    return np.arange(self.start, self.stop + self.step / 2, self.step)
                else:
                    return np.arange(self.start, self.stop - self.step / 2, self.step)
            elif self.num is not None:
                if self.kind == "lin":
                    return np.linspace(self.start, self.stop, self.num, self.endpoint)
                elif self.kind == "log":
                    return np.logspace(self.start, self.stop, self.num, self.endpoint)

        raise ValueError(f"Underspecified sweep: {self}.")
