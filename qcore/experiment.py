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
from qcore.helpers.stage import Stage
from qcore.resource import Resource
from qcore.sequences.constructors import construct_sweep
from qcore.helpers.logger import logger
from qcore.variables import Dataset, Sweep, Variable


class Experiment:
    """
    Abstract class for experiments using QUA sequences.
    """

    # experiment parameters
    name: str
    element_names: list[str]
    repetitions: int
    wait_time: int
    wait_element: str
    fetch_interval: int
    sweep_order: List[Sweep]
    _exp_vars: List[Variable]

    # saving and plotting config
    _filepath: str
    _project_folder: Path

    def __init__(
        self,
        name: str,
        project_folder: Path,
        *element_names: str,
        repetitions: int,
        wait_time: int,
        wait_element: str,
        fetch_interval: int = 2,
    ):
        self.name = name

        self._project_folder = project_folder
        self._filepath: Path = None  # will be set on run() with call to get_filepath()

        self.element_names = element_names
        self._elements: list[Element] = None  # will be set on call to get_elements()

        self.qm: QM = None  # will be set on run() by _get_qm()

        self.repetitions = repetitions
        self.wait_time = wait_time
        self.wait_element = wait_element
        self.fetch_interval = fetch_interval

        self.sweep_order = None
        self._exp_vars = None

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

    def _get_elements(self) -> list[Element]:
        """ """
        configpath = self._project_folder / "elements.yml"
        with Stage(configpath) as stage:
            self._elements = stage.get(*self.element_names)
        return self._elements.copy()

    def _get_qm(self) -> QM:
        """ """
        lo_names = (element.lo_name for element in self._elements)
        with Stage(remote=True) as remote_stage:
            local_oscillators = remote_stage.get(*lo_names)
        return QM(elements=self._elements, oscillators=local_oscillators)

    def _get_filepath(self) -> Path:
        """ """
        if self._filepath is None:
            date, time = datetime.now().strftime("%Y-%m-%d %H-%M-%S").split()
            folderpath = self._project_folder / "data" / date
            filename = f"{time}_{self.name}.hdf5"
            self._filepath = folderpath / filename
            logger.debug(f"Generated filepath {self._filepath} for '{self.name}'")
        return self._filepath

    def _get_metadata(self) -> dict:
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
            stop=self.repetitions,
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
        self.qm = self._get_qm()

        self.datasaver = Datasaver(self._get_filepath(), *save)
        self.plotter = Plotter(*plot)

        self.qm.execute(self.construct_pulse_sequence())

        time.sleep(self.fetch_interval)

        with self.datasaver as datasaver:
            datasaver.save_metadata(self._get_metadata())
            while self.qm.is_processing():
                # fetch latest batch of partial data along with data counts
                data, current_count, last_count = self.qm.fetch()
                if data:  # empty dict means no new results available
                    self.process_data(datasaver, data, current_count, last_count)
                time.sleep(self.fetch_interval)
