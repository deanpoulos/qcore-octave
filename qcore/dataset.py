""" """

from typing import Union

import numpy as np

from qcore.expvariable import ExpVar
from qcore.sweep import Sweep


class Dataset(ExpVar):
    """ """

    def __init__(
        self,
        axes: list[Union[Sweep, int]],  # defines the dataset's dimension(s)
        name: str = None,  # name of the dataset, as it will appear in the datafile
        dtype: str = "f4",  # dtype used to save dataset
        units: str = None,  # units attribute sweep points dataset is saved with
        data: np.ndarray = None,  # initial data for this dataset
        var_type: type = None,
        create_stream: bool = True,
        is_adc: bool = False,
    ) -> None:
        """ """
        super().__init__(name, var_type, create_stream, is_adc)
        self.axes = axes
        self.name = name
        self.dtype = dtype
        self.units = units

        # the current batch of data assigned to this dataset
        # can be used during live fetching to store intermediate values for analysis
        self.data: np.ndarray = data

    @property
    def shape(self) -> list[int]:
        """ """
        return [item.length if isinstance(item, Sweep) else item for item in self.axes]

    @property
    def metadata(self) -> dict:
        """ """
        x = ("data", "axes", "var_type")  # excluded keys
        return {k: v for k, v in self.__dict__.items() if k not in x and v is not None}
