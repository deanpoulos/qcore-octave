"""This example shows one way to reorganize our Experiment runtime flow"""

from __future__ import annotations

import threading
import time
from typing import Union

import numpy as np
import pyqtgraph as pg
from PyQt5 import QtCore as qtc


class Sweep:
    """ """

    def __init__(
        self,
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

        # this is to be updated by the experiment data handler if live saving/plotting
        self.data: np.ndarray = data


class Experiment:
    """ """

    def __init__(self, N: int, wait: int) -> None:
        """
        N: (int) number of repetitions of this experiment
        wait: (int) wait time between successive repetitions
        """
        self.N = N
        self.wait = wait
        self.datasaver = None
        self.plotter = None

    def run(self, save, plot) -> None:
        """
        save (tuple[str] | bool): True to live save all datasets, False to save no data, and tuple of strings corresponding to dataset names to save specific data.
        plot: tuple[str] | bool: True to live plot all datasets, False to plot no data, and tuple of strings corresponding to dataset names to plot specific data.
        """
        if save:
            self.datasaver = Datasaver(*save)
        if plot:
            self.plotter = Plotter(self.wait, *plot)
        self.sequence()

    def sequence(self) -> None:
        """ """
        raise NotImplementedError("Subclass(es) must implement sequence()!")


class ResonatorSpectroscopy(Experiment):
    """ """

    def __init__(self, freqs: Sweep, **parameters) -> None:
        """ """
        # initialize Sweep(s)
        freqs.name, freqs.units = "Frequency", "Hz"
        self.freqs = freqs.data

        # initialize Dataset(s)
        self.s21 = Dataset(axes=["Re(S21)", "Im(S21)"], name="s21")
        initial_data = np.zeros(len(self.freqs))
        self.s21_avg = Dataset(
            axes=["Re(S21)", "Im(S21)"], name="s21_avg", data=initial_data
        )
        self.s21_mlog = Dataset(
            axes=[freqs], name="s21_mlog", units="dBm", data=initial_data
        )
        self.s21_arg = Dataset(
            axes=[freqs], name="s21_arg", units="rad", data=initial_data
        )

        super().__init__(**parameters)

    def fetch_data(self, num: int) -> np.ndarray:
        """ """

        def s21(freqs, omega, Q, absQc, phi, a, alpha, tau, noisex):
            env = a * np.exp(1j * (alpha - 2 * np.pi * freqs * tau))
            res = (Q / absQc * np.exp(1j * phi)) / (1 + 2j * Q * (freqs / omega - 1))
            signal = env * (1 - res)  # hanger
            num = len(freqs)
            noise = noisex * (np.random.randn(num) + 1j * np.random.randn(num))
            return signal + noise

        # parameters hard-coded for convenience, hard-coding is inconsequential
        parameters = {
            "omega": 5e9,
            "Q": 1e4,
            "absQc": 1e2,
            "phi": 0,
            "a": 1,
            "alpha": 0,
            "tau": 0,
            "noisex": 0.4,
        }
        return np.array([s21(self.freqs, **parameters) for _ in range(num)])

    def sequence(self) -> np.ndarray:
        """ """
        count = 0
        while count < self.N:
            print(f"Experiment repetition count {count} of {self.N}...")
            # get data batch with random reps that are some fraction of total reps
            reps = np.random.randint(low=1, high=int(self.N * 0.1) + 1)
            if count + reps >= self.N:  # ensure we don't exceed total no. of reps
                reps = self.N - count
            new_count = count + reps
            data = self.fetch_data(reps)
            print(f"Fetched {reps} data batches! Data shape = {data.shape}.")
            self.handle_data(data, new_count, self.N)
            count = new_count
            time.sleep(self.wait)

    def handle_data(self, data: np.ndarray, count: int, reps: int) -> None:
        """ """
        # custom transformations which are experiment specfic
        
        
        #super().handle_data(data)
        
        self.s21.data = data

        s21_avg = np.average(data, axis=0)
        self.s21_avg.data = (self.s21_avg.data + s21_avg) / 2

        s21_mlog = 20 * np.log10(np.abs(s21_avg))
        self.s21_mlog.data = (self.s21_mlog.data + s21_mlog) / 2

        s21_arg = np.unwrap(np.angle(s21_avg))
        self.s21_arg.data = (self.s21_arg.data + s21_arg) / 2

        if self.plotter is not None:
            self.plotter.plot(count, reps)
        if self.datasaver is not None:
            self.datasaver.save()


class PlotWorker(threading.Thread):
    """ """

    def __init__(self, interval, *datasets) -> None:
        """ """
        super().__init__()
        self.interval = interval
        self.datasets: tuple[Dataset] = datasets
        self.plots: dict[Dataset, pg.PlotItem] = {}
        self.new_data_event = threading.Event()
        self.done_event = threading.Event()
        self.message: str = ""

    def run(self) -> None:
        """ """
        title = "Test experiment"
        app = pg.mkQApp(title)
        win = pg.GraphicsLayoutWidget(show=True, title=title)
        win.resize(1000, 600)
        win.setWindowTitle(title)
        pg.setConfigOptions(antialias=True)

        n = len(self.datasets)
        for i, dataset in enumerate(self.datasets):
            plot_item = pg.PlotItem()
            plot_data_item = pg.ScatterPlotItem(brush=(i, n), pen=None, size=5)
            plot_item.addItem(plot_data_item)
            axes = dataset.axes
            num_axes = len(axes)
            if num_axes == 1:
                xlabel = axes[0].name if isinstance(axes[0], Sweep) else axes[0]
                xunits = axes[0].units if isinstance(axes[0], Sweep) else None
                ylabel = dataset.name
                yunits = dataset.units
            elif num_axes == 2:
                xlabel = axes[0].name if isinstance(axes[0], Sweep) else axes[0]
                xunits = axes[0].units if isinstance(axes[0], Sweep) else None
                ylabel = axes[1].name if isinstance(axes[1], Sweep) else axes[1]
                yunits = axes[1].units if isinstance(axes[0], Sweep) else None
            else:
                raise RuntimeError("Can't handle 3D plots for now!!!")
            plot_item.setLabels(bottom=(xlabel, xunits), left=(ylabel, yunits))
            plot_item.showGrid(x=True, y=True, alpha=0.1)
            plot_item.setMenuEnabled(False)
            win.addItem(plot_item)
            self.plots[dataset] = plot_item

        self.timer = qtc.QTimer()
        self.timer.timeout.connect(self.update)
        self.timer.start(self.interval * 1000)
        print("Initialized plotter!")

        app.exec()

    def update(self) -> None:
        """ """
        if not self.done_event.is_set():
            if self.new_data_event.is_set():
                self.new_data_event.clear()
                print("Plotter found new data")
                for dataset, plot_item in self.plots.items():
                    new_data = dataset.data
                    plot_data_item = plot_item.listDataItems()[0]
                    # case: complex data
                    if np.iscomplexobj(new_data):
                        plot_data_item.setData(new_data.real, new_data.imag)
                    else:
                        plot_data_item.setData(x=dataset.axes[0].data, y=new_data)
                    plot_item.setTitle(f"{dataset.name} {self.message}")
            else:
                print("Plotter found no new data")
        else:
            self.timer.stop()
            print("Stopped plotting!")


class Plotter:
    """ """

    def __init__(self, interval: float, *datasets: Dataset) -> None:
        """ """
        self.interval = interval
        self.worker = PlotWorker(interval, *datasets)
        self.worker.start()

    def plot(self, count: int, reps: int) -> None:
        """ """
        print(f"Plotting data after {count} / {reps} repetitions...")
        self.worker.message = f"({count} / {reps})"
        self.worker.new_data_event.set()

        if count == reps:
            time.sleep(self.interval)
            self.worker.done_event.set()


class Datasaver:
    """We ignore data saving in this example, but it works similarly as the Plotter"""


if __name__ == "__main__":
    """ """

    parameters = {
        "N": 1000,
        "wait": 1,  # between successive repetitions
        "freqs": Sweep(start=4.975e9, stop=5.025e9, num=1001, endpoint=True),
    }
    expt = ResonatorSpectroscopy(**parameters)
    to_plot = (expt.s21_mlog, expt.s21_arg)
    expt.run(save=False, plot=to_plot)
