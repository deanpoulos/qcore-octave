""" """

from typing import Union

import numpy as np

from qcore.sweep import Sweep

class Dataset:
    """ """

    def __init__(
        self,
        axes: list[Union[Sweep, str]],  # defines the dataset's dimension(s)
        name: str = None,  # name of the dataset, as it will appear in the datafile
        dtype: str = "f4",  # dtype used to save dataset
        units: str = None,  # units attribute sweep points dataset is saved with
        data: np.ndarray = None,  # initial data for this dataset
    ) -> None:
        """ """
        self.axes = axes
        self.name = name
        self.dtype = dtype
        self.units = units

        # the current batch of data assigned to this dataset
        # can be used during live fetching to store intermediate values for analysis
        self.data: np.ndarray = data
