import time
from datetime import datetime
from typing import List
from pathlib import Path

from qm.qua import program, stream_processing
from qm.qua._dsl import _Program

from qcore.instruments import QM
from qcore.elements.element import Element
from qcore.helpers.datasaver import Datasaver
from qcore.helpers.plotter import Plotter
from qcore.resource import Resource
from qcore.sequences.constructors import construct_sweep
from qcore.helpers.logger import logger
from qcore.variables import Dataset, Sweep, Variable


class Experiment:
    """
    Abstract class for experiments using QUA sequences.
    """

    # experiment parameters
    fetch_interval: int
    name: str
    num_reps: int
    qm: QM
    sweep_order: List[Sweep]
    wait_element: Element
    wait_time: int
    _exp_vars: List[Variable]

    # saving and plotting config
    _filepath: str
    _nametag: str
    _savefolder: Path

    def __init__(
        self,
        name: str,
        reps: int,
        qm: QM,
        wait_element: Element,
        wait_time_ns: int,
        savefolder: Path,
        nametag: str = "",
        fetch_interval: int = 1,
    ):

        self.fetch_interval = fetch_interval
        self.name = name
        self.num_reps = reps
        self.qm = qm
        self.sweep_order = None
        self.wait_element = wait_element
        self.wait_time = wait_time_ns
        self._exp_vars = None

        self._filepath = None
        self._nametag = nametag
        self._savefolder = savefolder

    # -------------------------------------------------------------------------
    # User define methods
    # -------------------------------------------------------------------------

    def pulse_sequence(self):
        raise NotImplementedError

    def process_data(self):
        raise NotImplementedError

    # -------------------------------------------------------------------------
    # Builtin methods
    # -------------------------------------------------------------------------

    def get_filepath(self) -> Path:
        """ """
        if self._filepath is None:
            date, time = datetime.now().strftime("%Y-%m-%d %H-%M-%S").split()
            folderpath = self._savefolder / date
            filesuffix = f"_{self._nametag}" if self._nametag else ""
            filename = f"{time}_{self.name}{filesuffix}.h5"
            self._filepath = folderpath / filename
            logger.debug(f"Generated filepath {self._filepath} for '{self.name}'")
        return self._filepath

    def snapshot(self) -> dict:
        """
        snapshot includes instance attributes that do not start with "_" are
        are not instances of excluded classes - Resource, Sweep, Dataset,
        DataSaver, LivePlotter
        """

    def get_metadata(self) -> dict:
        """ """
        resources = [v for v in self.__dict__.values() if isinstance(v, Resource)]
        metadata = {resource.name: resource.snapshot() for resource in resources}

        xcls = (Resource, Sweep, Dataset)  # excluded classes
        xkeys = ("datasaver", "plotter")  # excluded keys
        snapshot = {}
        for k, v in self.__dict__.items():
            if not isinstance(v, xcls) and not k.startswith("_") and not k in xkeys:
                snapshot[k] = v

        return {**metadata, None: snapshot}

    def _construct_sweep_order(self) -> None:
        """
        Initializes variable N for number of repetitions and places it
        at the front of the sweep order list, so that it will be in the
        outer most for_ loop when construct_sweep is called.
        If no sweep order is given,
        """
        self.N = Sweep(
            name="N",
            var_type=int,
            start=0,
            stop=self.num_reps,
            step=1,
        )

        if self.sweep_order:
            self.sweep_order.insert(0, self.N)
        else:
            class_var_dict = self.__dict__
            self.sweep_order = [self.N]

            for var_name in class_var_dict.keys():
                var = class_var_dict[var_name]
                if isinstance(var, Sweep):
                    var.declare_var()
                    self.sweep_order.append(var)

    def _init_variables(self) -> None:
        """
        Identifies class variables that are ExpVars(including Sweeps and
        Datasets) and initializes their qua variables.

        Important: This method should only be called within a
        'with qua.program()' context.
        """

        # Initialize N and construct sweep order
        self._construct_sweep_order()

        class_var_dict = self.__dict__
        self._exp_vars = []

        for var_name in class_var_dict.keys():
            var = class_var_dict[var_name]
            if isinstance(var, Variable):
                var.declare_var()
                self._exp_vars.append(var)

    def _process_streams(self) -> None:
        """
        Generates the stream processing statements for the qua program.
        We don't have to check if the variable has a stream here as that check
        is done in  <ExpVar>.process_stream().
        """

        for qua_var in self._exp_vars:
            qua_var.process_stream()

    def _construct_sweep(self):
        """ """

        construct_sweep(
            ordered_sweep_list=self.sweep_order,
            pulse_sequence=self.pulse_sequence,
            wait_time=self.wait_time,
            wait_elem=self.rr,
        )

    def construct_pulse_sequence(self) -> _Program:
        """
        Wrapper to build the full qua sequence including initializing variables,
        for_ loops and processing streams.
        """

        with program() as qua_prog:
            self._init_variables()

            self._construct_sweep()

            with stream_processing():
                self._process_streams()

        return qua_prog

    def run(self, save: tuple = (), plot: tuple = ()) -> None:
        """ """

        self.datasaver = Datasaver(self.get_filepath(), *save)
        # self.plotter = Plotter(*plot)

        self.qm.execute(self.construct_pulse_sequence())

        time.sleep(self.fetch_interval)

        with self.datasaver as datasaver:
            datasaver.save_metadata(self.get_metadata())
            while self.qm.is_processing():
                # fetch latest batch of partial data along with data counts
                data, current_count, last_count = self.qm.fetch()
                if data:  # empty dict means no new results available
                    self.process_data(datasaver, data, current_count, last_count)
                time.sleep(self.fetch_interval)
