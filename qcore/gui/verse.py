""" """

from PyQt5 import QtWidgets as qtw
from PyQt5 import QtCore as qtc

from qcore.gui.instrument_widget import InstrumentWidget
from qcore.gui.server_widget import ServerWidget
from qcore.gui.ui_verse import Ui_verse
from qcore.helpers import logger

class Verse(qtw.QWidget):
    """ """

    def __init__(self, *args, **kwargs) -> None:
        """ """
        super().__init__(*args, **kwargs)

        self.ui = Ui_verse()
        self.ui.setupUi(self)

        nominal_size = (1000, 600)
        self.resize(*nominal_size)
        self.setMinimumSize(qtc.QSize(*nominal_size))

        self.server_widget = ServerWidget()
        self.ui.tabs.addTab(self.server_widget, "Server")

        self.server_widget.is_serving.connect(self.handle_serving)

        logger.remove()
        logfmt = "[{time:YY-MM-DD  HH:mm:ss}]   [{level}]   [{module}]   {message}"
        sink = self.ui.logbox.append
        logger.add(sink, format=logfmt, level="INFO", backtrace=False, diagnose=False)

    def handle_serving(self, is_serving: bool) -> None:
        """ """
        if is_serving:
            instrument_types = self.get_instrument_types()
            for idx, instrument in enumerate(self.server_widget.instruments):
                widget = InstrumentWidget(instrument, type=instrument_types[idx])
                widget.name_edited.connect(self.update_instrument_name)
                self.ui.tabs.addTab(widget, instrument.name)
        else:
            num_tabs = self.ui.tabs.count()
            for i in range(1, num_tabs):
                self.ui.tabs.removeTab(i)

    def get_instrument_types(self) -> list[str]:
        """ """
        instrument_types = []
        for cls, instruments in self.server_widget.config.items():
            for _ in range(len(instruments)):
                instrument_types.append(cls)
        return instrument_types

    def update_instrument_name(self, new_name: str):
        """ """
        self.ui.tabs.setTabText(self.ui.tabs.currentIndex(), new_name)

if __name__ == "__main__":
    app = qtw.QApplication([])
    verse = Verse()
    verse.show()
    app.exec()
