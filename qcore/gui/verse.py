""" """

from PyQt5 import QtWidgets as qtw
from PyQt5 import QtCore as qtc

from qcore.gui.instrument_widget import InstrumentWidget
from qcore.gui.server_widget import ServerWidget


class Verse(qtw.QTabWidget):
    """ """

    def __init__(self, *args, **kwargs) -> None:
        """ """
        super().__init__(*args, **kwargs)

        self.setWindowTitle("Verse")
        nominal_size = (900, 400)
        self.resize(*nominal_size)
        self.setMinimumSize(qtc.QSize(*nominal_size))

        self.server_widget = ServerWidget()
        self.addTab(self.server_widget, "Server")

        self.server_widget.is_serving.connect(self.update_instrument_tabs)

    def update_instrument_tabs(self, is_serving: bool) -> None:
        """ """
        if is_serving:
            for instrument in self.server_widget.instruments:
                self.addTab(InstrumentWidget(instrument), instrument.name)
        else:
            num_tabs = self.count()
            for i in range(1, num_tabs):
                self.removeTab(i)


if __name__ == "__main__":
    app = qtw.QApplication([])
    verse = Verse()
    verse.show()
    app.exec()
