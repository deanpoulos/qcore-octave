import time

from qcore.instruments import QM
from qcore.helpers.datasaver import Datasaver
from qcore.helpers.plotter import Plotter
from pathlib import Path
from datetime import datetime
from qcore.resource import Resource
from qcore.sweep import Sweep
from qcore.dataset import Dataset
from qcore.helpers.logger import logger


class Experiment:
    """
    Abstract class for experiments using QUA sequences.
    """

    def __init__(
        self,
        name: str,
        qm: QM,
        savefolder: Path,
        nametag: str = "",
        fetch_interval: int = 1,
    ):
        self.name = name
        self._savefolder = savefolder
        self._nametag = nametag
        self._filepath = None

        self.qm = qm
        self.fetch_interval = fetch_interval

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
        snapshot includes instance attributes that do not start with "_" are are not instances of excluded classes - Resource, Sweep, Dataset, DataSaver, LivePlotter
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

    def init_variables(self):
        raise NotImplementedError

    def process_streams(self):
        raise NotImplementedError

    def construct_pulse_sequence(self):
        raise NotImplementedError

    def process_data(self):
        raise NotImplementedError

    def run(self, save: tuple = (), plot: tuple = ()) -> None:
        """ """

        self.datasaver = Datasaver(self.get_filepath(), *save)
        #self.plotter = Plotter(*plot)

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
