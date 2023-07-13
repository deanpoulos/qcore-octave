""" """

from datetime import datetime

from contextlib import ExitStack
from pathlib import Path
import time

import qm.qua as qua
from qm.qua._dsl import _ProgramScope, _Variable, _ResultSource

from qcore.instruments.instrument import Instrument
from qcore.instruments import QM
from qcore.helpers.datasaver import Datasaver
from qcore.helpers.logger import logger
from qcore.helpers.plotter import Plotter
from qcore.helpers.stage import Stage
from qcore.libs.qua_macros import QuaVariable
from qcore.modes.mode import Mode
from qcore.pulses.pulse import Pulse
from qcore.resource import Resource
from qcore.variables.datasets import Dataset
from qcore.variables.sweeps import Sweep, BaseSweep, QuaSweep, QcoreSweep


class ExperimentInitializationError(Exception):
    """ """


class SweepValidationError(Exception):
    """ """


class DatasetInitializationError(Exception):
    """ """


class ExperimentManager:
    """handle Experiment setup tasks related to resources, sweeps, datasets"""

    def get_resources(self, folder) -> dict[str, Instrument]:
        """get all available resources from remote stage and local config"""
        with Stage(remote=True) as stage:
            instruments = {rsc.name: rsc for rsc in stage.get(*stage.resources)}

        modes_config = folder / "config/modes.yml"
        if not modes_config.exists():
            message = f"A file named 'modes.yml' must exist at path '{modes_config}'."
            raise ExperimentInitializationError(message)

        with Stage(modes_config) as stage:
            rscs = stage.get(*stage.resources)
            modes = {m.name: m for m in rscs if isinstance(m, Mode)}
        pulses = {p.name: p for m in modes.values() for p in m.operations.values()}
        return instruments, modes, pulses

    def select_resources(self, resources, map, cls) -> dict[str, Resource]:
        """ """
        selected_resources = {}
        for key, value in map.items():
            try:
                resource = resources[value]
            except KeyError:
                message = f"Resource named '{value}' does not exist on the stage."
                logger.error(message)
                raise ExperimentInitializationError(message)
            else:
                if not isinstance(resource, cls):
                    message = (
                        f"Expect Resource named '{value}' to be of {cls}, got "
                        f"{resource} of {type(resource)}."
                    )
                    logger.error(message)
                    raise ExperimentInitializationError(message)
                selected_resources[key] = resource
        return selected_resources

    def select_modes(self, all_modes, mode_map) -> dict[str, Mode]:
        """ """
        return self.select_resources(all_modes, mode_map, Mode)

    def select_pulses(self, all_pulses, pulse_map) -> dict[str, Pulse]:
        """ """
        return self.select_resources(all_pulses, pulse_map, Pulse)

    def validate_sweeps(
        self, sweeps: list[Sweep], primary_sweeps: list[str], **kwargs
    ) -> None:
        """ """
        sweep_dict = {sweep.name: sweep for sweep in sweeps}

        # check if maximum number of Sweeps is exceeded
        if len(sweep_dict) > Experiment.MAX_SWEEPS:
            message = (
                f"Maximum sweeps for an experiment run exceeded, we only allow "
                f"upto {Experiment.MAX_SWEEPS}D Sweeps."
            )
            logger.error(message)
            raise SweepValidationError(message)

        # check that all values are Sweep objects
        for sweep in sweep_dict.values():
            if not isinstance(sweep, Sweep):
                msg = f"Expect object of '{Sweep}', got '{sweep}' of '{type(sweep)}'."
                logger.error(msg)
                raise SweepValidationError(msg)

        # check that required primary sweep(s) are specified
        if not set(primary_sweeps) <= set(sweep_dict.keys()):
            missing_sweeps = set(primary_sweeps) - set(sweep_dict.keys())
            message = f"All {primary_sweeps = } must be specified, {missing_sweeps = }."
            logger.error(message)
            raise SweepValidationError(message)

        # check that there are no duplicate sweep names
        if len(sweeps) != len(sweep_dict):
            all_names = [sweep.name for sweep in sweeps]
            duplicate_sweeps = set(i for i in all_names if all_names.count(i) > 1)
            message = f"Found {duplicate_sweeps = }, all sweep names must be unique."
            logger.error(message)
            raise SweepValidationError(message)

        # sweep names cannot appear in any control parameters dict
        for key in kwargs.keys():
            if key in sweep_dict:
                message = (
                    f"The variable with name '{key}' cannot be both specified as "
                    f"a Sweep and as an experimental control parameter."
                )
                logger.error(message)
                raise SweepValidationError(message)

    def validate_base_sweeps(self, sweeps: list[BaseSweep]):
        """ """
        qcore_sweeps, qua_sweeps = [], []
        qcore_msg = "Among all sweeps, only 1 outermost Qcore Sweep can be specified."
        qua_msg = (
            "Among Qua Sweeps, atleast 1 outermost averaging Qua Sweep named 'N' must "
            "be specified."
        )

        for idx, sweep in enumerate(sweeps):
            if isinstance(sweep, QuaSweep):
                qua_sweeps.append(sweep)
            elif isinstance(sweep, QcoreSweep):
                if idx != 0:
                    logger.error(qcore_msg)
                    raise SweepValidationError(qcore_msg)
                qcore_sweeps.append(sweep)

        if len(qcore_sweeps) > 1:
            logger.error(qcore_msg)
            raise SweepValidationError(qcore_msg)

        try:
            outermost_qua_sweep = qua_sweeps[0]
        except IndexError:
            logger.error(qua_msg)
            raise SweepValidationError(qua_msg)
        else:
            if outermost_qua_sweep.name != "N":
                logger.error(qua_msg)
                raise SweepValidationError(qua_msg)

    def validate_datasets(
        self,
        datasets: list[Dataset],
        primary_datasets: list[str],
        sweep_dict: dict[str, BaseSweep],
    ) -> None:
        """ """
        dset_dict = {dataset.name: dataset for dataset in datasets}

        # check that all values are Dataset objects
        for dset in dset_dict.values():
            if not isinstance(dset, Dataset):
                msg = f"Expect object of '{Dataset}', got '{dset}' of '{type(dset)}'."
                logger.error(msg)
                raise DatasetInitializationError(msg)

        # all primary datasets must be specified
        if not set(primary_datasets) <= set(dset_dict.keys()):
            missing_datasets = set(primary_datasets) - set(dset_dict.keys())
            msg = f"All {primary_datasets = } must be specified, {missing_datasets = }."
            logger.error(msg)
            raise DatasetInitializationError(msg)

        # check that there are no duplicate dataset names
        if len(datasets) != len(dset_dict):
            all_names = [dset.name for dset in datasets]
            duplicate_datasets = set(i for i in all_names if all_names.count(i) > 1)
            msg = f"Found {duplicate_datasets = }, all dataset names must be unique."
            logger.error(msg)
            raise DatasetInitializationError(msg)

        # check that Datasets and Sweeps do not share any common names
        common_names = set(dset_dict.keys()) & set(sweep_dict.keys())
        if common_names:
            message = f"Datasets and Sweeps can't share names, found {common_names = }."
            logger.error(message)
            raise DatasetInitializationError(message)

    def init_datasets(
        self,
        datasets: dict[str, Dataset],
        primary_datasets: list[str],
        sweep_dict: dict[str, QuaSweep],
    ) -> None:
        """ """
        # prepare Dataset axes
        for dset in datasets.values():
            if dset.name in primary_datasets:
                if dset.stream is False:  # do not change stream value for ADC datasets
                    dset.stream = True  # by convention, only raw datasets are streamed
            else:
                if not dset.inputs:
                    dset.inputs = primary_datasets
                else:
                    for input_dset in dset.inputs:
                        if input_dset not in datasets:
                            message = (
                                f"Derived dataset '{dset.name}' has an "
                                f"unrecognized input dataset named '{input_dset}'."
                            )
                            logger.error(message)
                            raise DatasetInitializationError(message)

            if dset.axes is None:
                dset.initialize(axes=list(sweep_dict.values()))


class Experiment:
    """generic experiment class written for executing QUA sequences on the QM OPX"""

    # datasets with these names will be streamed by the OPX
    primary_datasets: list = []  # to be specified by child classes

    # these name(s) must be specified as Sweep objects in the 'sweeps' list
    primary_sweeps: list = []  # to be specified by child classes

    MAX_SWEEPS: int = 4  # maximum number of Sweeps allowed per experiment run
    DATAFILE_SUFFIX: str = ".hdf5"

    def __init__(
        self,
        folder: Path,
        modes: dict[str, str],
        pulses: dict[str, str],
        sweeps: list[Sweep],
        datasets: list[Dataset],
        fetch_interval: int = 1,
        **kwargs,
    ) -> None:
        """ """
        self.name = self.__class__.__name__

        self._folder = Path(folder)
        self._filepath = None  # will be set on run() with call to _get_filepath()

        self._manager = ExperimentManager()  # to handle Experiment setup tasks
        instruments, all_modes, all_pulses = self._manager.get_resources(self._folder)

        self._resources = {**instruments, **all_modes, **all_pulses}
        self._instruments = instruments
        self._modes = self._manager.select_modes(all_modes, modes)
        self._pulses = self._manager.select_pulses(all_pulses, pulses)
        self._configure_resources()

        # obtain BaseSweep instances from Sweeps specified by the user
        primary_sweeps, primary_datasets = self.primary_sweeps, self.primary_datasets
        self._manager.validate_sweeps(sweeps, primary_sweeps, **kwargs)
        self._sweeps: dict[str, BaseSweep] = {swp.name: swp.sweep for swp in sweeps}
        self._manager.validate_base_sweeps(list(self._sweeps.values()))

        # obtain BaseDataset instances from Datasets specified by the user
        self._manager.validate_datasets(datasets, primary_datasets, self._sweeps)
        self._datasets: dict[str, Dataset] = {dset.name: dset for dset in datasets}

        self.fetch_interval = fetch_interval

        # container for the various types of QuaVariables involved in this experiment
        self._qua_variables: dict[str, QuaVariable] = {}  # for all QuaVariables
        self._qua_sweeps: dict[str, QuaSweep] = {}
        self._qua_datasets = {}
        for k, v in kwargs.items():
            if isinstance(v, QuaVariable):
                v.tag = k
                self._qua_variables[k] = v
            else:
                setattr(self, k, v)  # set additional "kwargs" as Experiment attributes

        self.repetitions = 1
        for sweep in self._sweeps.values():
            if isinstance(sweep, QuaSweep):
                self._qua_variables[sweep.name] = sweep
                self._qua_sweeps[sweep.name] = sweep

                if sweep.name == "N":
                    self.repetitions = sweep.length

        self._manager.init_datasets(self._datasets, primary_datasets, self._qua_sweeps)
        for dataset in self._datasets.values():
            if dataset.stream:  # is qua dataset
                self._qua_variables[dataset.name] = dataset
                self._qua_datasets[dataset.name] = dataset

        # initialize experiment attributes that will be set on run()
        self._qm = None

    def sequence(self):
        raise NotImplementedError("Subclass(es) to implement sequence()")

    def _configure_resources(self) -> None:
        """
        # make Mode and Pulse objects Experiment attributes for easy access
        # for each Mode, select only the subset of Pulses required for this Experiment
        """
        for mode_name, mode in self._modes.items():
            if not hasattr(self, mode_name):
                setattr(self, mode_name, mode)
                logger.info(f"Set '{self.name}' attribute '{mode_name}'.")

            all_op_names = [p.name for p in mode.operations.values()]
            selected_operations = {}
            for pulse_name, pulse in self._pulses.items():
                if pulse.name in all_op_names:
                    selected_operations[pulse_name] = pulse
                    if not hasattr(self, pulse_name):
                        setattr(self, pulse_name, pulse)
                        logger.info(f"Set '{self.name}' attribute '{pulse_name}'.")
            mode.operations = selected_operations

    def run(self):
        """ """
        outermost_sweep = list(self._sweeps.values())[0]
        try:
            if isinstance(outermost_sweep, QcoreSweep):
                self._run_with_qcore_sweep(outermost_sweep)
            else:
                self._get_filepath()
                self._run_qua_sweeps()
        except KeyboardInterrupt:
            msg = f"Experiment '{self.name}' interrupted, closing QM now..."
            logger.info(msg)
            self._qm.disconnect()

    def _run_with_qcore_sweep(self, qcore_sweep: QcoreSweep):
        """ """
        name, target, points = qcore_sweep.name, qcore_sweep.target, qcore_sweep.data

        if isinstance(target, str):  # target is a resource
            try:
                target = self._resources[target]
            except KeyError:
                message = f"Target Resource named '{target}' not found on stage."
                logger.error(message)
                raise SweepValidationError(message)
            else:
                if isinstance(target, Mode):
                    self._modes[target.name] = target
                elif isinstance(target, Pulse):
                    self._pulses[target.name] = target
        elif target is not self:
            message = f"Invalid sweep {target = } of type {type(target)}."
            logger.error(message)
            raise SweepValidationError(message)

        if not hasattr(target, name):
            message = f"Target '{target}' doesn't have attribute '{name}' for sweeping."
            logger.error(message)
            raise SweepValidationError(message)

        if qcore_sweep.dtype is str:
            has_resource_sweep_points = True
            try:
                points = [self._resources[point] for point in points]
            except KeyError:
                message = (
                    f"All strings specified as Qcore Sweep '{name}' points must be "
                    f"names of resources on the stage."
                )
                logger.error(message)
                raise SweepValidationError(message)
            else:
                for point in points:
                    if isinstance(point, Mode):
                        self._modes[point.name] = point
                    elif isinstance(point, Pulse):
                        self._pulses[point.name] = point

        self._configure_resources()

        for point in points:
            setattr(target, name, point)
            suffix = point.name if has_resource_sweep_points else str(point)
            tag = f"_{target.name}_{suffix}"
            filepath = self._get_filepath()
            self._filepath = filepath.parent / (filepath.stem + tag + filepath.suffix)
            self._run_qua_sweeps(point, exit_plotter=True)
            time.sleep(self.fetch_interval)

    def _run_qua_sweeps(self, qcore_sweep_point=None, exit_plotter=False):
        """ """
        self._qm: QM = self._get_qm()
        qua_program = self._build_qua_program()
        self._qm.execute(qua_program)

        time.sleep(self.fetch_interval)

        dsets_to_save = {k: dset for k, dset in self._datasets.items() if dset.save}
        sweeps_to_save = {k: swp for k, swp in self._qua_sweeps.items() if swp.save}

        datasaver = Datasaver(self._filepath, *self._datasets.values())

        to_plot = [dset for dset in self._datasets.values() if dset.plot]
        plotter = Plotter(self.fetch_interval, self.name, self._filepath, *to_plot)

        with datasaver:
            datasaver.save_metadata(self._get_metadata())
            while self._qm.is_processing():
                if plotter.stop_expt:
                    break

                # fetch latest batch of partial data along with data counts
                data, prev_count, incoming_count = self._qm.fetch()                    # update sweep data and save to datafile
                for name, sweep in sweeps_to_save.items():
                    if isinstance(sweep, QuaSweep):
                        sweep.update(data[name])
                        datasaver.save_data(sweep)

                # update primary and derived datasets
                for name, dset in self._datasets.items():
                    if dset.inputs:  # is derived dataset with datafn and inputs
                        values = [data[i] for i in dset.inputs]
                    elif dset.stream:  # is primary dataset streamed by the OPX
                        values = data[name]
                    dset.update(values, prev_count, incoming_count)
                    data[name] = dset.data

                # process additional user-defined datasets in subclasses
                self.process_data(
                    data,
                    prev_count,
                    incoming_count,
                    self._qua_sweeps,
                    self._datasets,
                    qcore_sweep_point,
                )

                # save datasets and sweeps (after updating) to datafile
                for name, dataset in dsets_to_save.items():
                    datasaver.save_data(dataset)

                plot_msg = f": {incoming_count} / {self.repetitions} data batches"
                plotter.plot(message=plot_msg)  # update live plot

                time.sleep(self.fetch_interval)

            self._qm.disconnect()
            logger.info(f"{self.name} experiment has stopped running!")

            # plot final data batch and stop plotting loop
            if exit_plotter:
                plotter.plot(message=f"{plot_msg} [DONE]", stop=True, exit=True)
            else:
                plotter.plot(message=f"{plot_msg} [DONE]", stop=True)

    def process_data(
        self, data, prev_count, incoming_count, sweeps, datasets, qcorew_sweep_point
    ):
        """Subclass(es) to implement process_data()"""
        pass

    def _build_qua_program(self) -> _ProgramScope:
        """ """
        # enter QUA program scope
        with qua.program() as qua_program:
            # declare QUA variables and streams
            # set those as self attributes for easy access
            for name, var in self._qua_variables.items():
                qua_variable = var.declare_variable()
                qua_stream = var.declare_stream()
                if var.is_adc_trace:
                    setattr(self, name, qua_stream)
                else:
                    setattr(self, name, qua_variable)
                logger.info(f"Set QUA variable attribute {name} for {self.name}.")

            # generate and enter QUA loop contexts programmatically
            with ExitStack() as stack:
                for name, sweep in self._qua_sweeps.items():
                    logger.debug(f"Expect {sweep.length} '{name}' sweep points.")
                    fn, *args = sweep.generate_loop()
                    stack.enter_context(fn(*args))
                    sweep.save_to_stream()
                self.sequence()
                for dataset in self._qua_datasets.values():
                    dataset.save_to_stream()

            with qua.stream_processing():
                for idx, (sweep) in enumerate(self._qua_sweeps.values()):
                    if idx != 0:  # we don't save repetitions at all
                        sweep.process_stream()
                for dataset in self._qua_datasets.values():
                    dataset.process_stream()

        return qua_program

    def _get_qm(self):
        """pre-requisite: remote stage must already be setup and serving instruments"""
        mode_lo_map = {}
        for name, mode in self._modes.items():
            lo_name = mode.lo_name
            if lo_name is not None:
                try:
                    mode_lo_map[mode] = self._instruments[lo_name]
                except KeyError:
                    message = f"'{lo_name = }' for Mode '{name}' not found on stage."
                    logger.error(message)
                    raise ExperimentInitializationError(message)
        return QM(modes=mode_lo_map.keys(), oscillators=mode_lo_map.values())

    def _get_filepath(self) -> Path:
        """ """
        if self._filepath is None:
            date, time = datetime.now().strftime("%Y-%m-%d %H-%M-%S").split()
            folderpath = self._folder / "data" / date
            filename = f"{time}_{self.name}{Experiment.DATAFILE_SUFFIX}"
            self._filepath = folderpath / filename
            logger.debug(f"Generated filepath {self._filepath} for '{self.name}'")
        return self._filepath

    def _get_metadata(self):
        """ """
        inst_mdata = {k: i.snapshot() for k, i in self._instruments.items()}
        mode_mdata = {k: m.snapshot(flatten=True) for k, m in self._modes.items()}

        xcls = (_Variable, Resource, _ResultSource)  # excluded classes
        snapshot = {}
        for k, v in self.__dict__.items():
            if not isinstance(v, xcls) and not k.startswith("_"):
                snapshot[k] = v

        return {"instruments": inst_mdata, "modes": mode_mdata, None: snapshot}
