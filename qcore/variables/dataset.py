""" """

from typing import Union

import numpy as np

from qcore.variables.variable import Variable
from qcore.variables.sweep import Sweep


class Dataset(Variable):
    """ """

    def __init__(
        self,
        axes: list[Union[Sweep, int]],  # defines the dataset's dimension(s)
        name: str = None,  # name of the dataset, as it will appear in the datafile
        dtype: str = "f4",  # dtype used to save dataset
        units: str = None,  # units attribute sweep points dataset is saved with
        data: np.ndarray = None,  # initial data for this dataset
        index = None,  # to indicate the index of current data assigned to Dataset
        var_type: type = None,
        create_stream: bool = True,
        is_adc: bool = False,
        to_save: bool = False,  # whether or not to save this Dataset to a datafile
        to_plot: bool = False,  # whether or not to plot this Dataset during live plot
    ) -> None:
        """ """
        super().__init__(name, var_type, create_stream, is_adc)
        self.axes = axes
        self.name = name
        self.dtype = dtype
        self.units = units
        self.to_save = to_save
        self.to_plot = to_plot

        # the current batch of data assigned to this dataset at given index
        # can be used during live fetching to store intermediate values for analysis
        self.data: np.ndarray = data
        self.index = index

    @property
    def shape(self) -> list[int]:
        """ """
        return [item.length if isinstance(item, Sweep) else item for item in self.axes]

    @property
    def metadata(self) -> dict:
        """ """
        x = ("data", "axes", "var_type", "save", "index")  # excluded keys
        return {k: v for k, v in self.__dict__.items() if k not in x and v is not None}
