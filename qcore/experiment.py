from qcore.instruments import QM

class Experiment():
    """
    Abstract class for experiments using QUA sequences.
    """

    def __init__(self):
        pass

    def init_variables(self):
        raise NotImplementedError

    def pulse_sequence(self):
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

        qm.execute()

        while qm.is_processing():
            ...




