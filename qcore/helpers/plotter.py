""" """

import threading
import time

import numpy as np
import pyqtgraph as pg
from PyQt5 import QtCore as qtc

from qcore.variables.dataset import Dataset
from qcore.variables.sweep import Sweep

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
        title = "Plotter DEMO"
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

    def __init__(self, interval: float, repetitions: int, *datasets: Dataset) -> None:
        """ """
        self.interval = interval
        self.repetitions = repetitions
        self.worker = PlotWorker(interval, *datasets)
        self.worker.start()

    def plot(self, count: int) -> None:
        """ """
        print(f"Plotting data after {count} / {self.repetitions} repetitions...")
        self.worker.message = f"({count} / {self.repetitions})"
        self.worker.new_data_event.set()

        if count == self.repetitions:
            time.sleep(self.interval)
            self.worker.done_event.set()
