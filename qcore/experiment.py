from qcore.instruments import QM
from qcore.helpers.datasaver import Datasaver
from qcore.helpers.plotter import Plotter

class Experiment():
    """
    Abstract class for experiments using QUA sequences.
    """

    def __init__(self):
        pass

    def init_variables(self):
        raise NotImplementedError
    
    def process_streams(self):
        raise NotImplementedError

    def construct_pulse_sequence(self):
        raise NotImplementedError

    def run(self, save, plot, qm:QM):
        """
        save (tuple[str] | bool): True to live save all datasets, False to save no data, and tuple of strings corresponding to dataset names to save specific data.
        plot: tuple[str] | bool: True to live plot all datasets, False to plot no data, and tuple of strings corresponding to dataset names to plot specific data.
        """
        if save:
            self.datasaver = Datasaver(*save)
        if plot:
            self.plotter = Plotter(self.wait, *plot)

        qm.execute(self)

        while qm.is_processing():
            ...




