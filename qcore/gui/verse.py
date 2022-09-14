""" """

from collections import defaultdict
import time

from PyQt5 import QtWidgets, QtCore

from qcore.instruments.config import InstrumentConfig
from qcore.gui.verse_ui import Ui_verse
from qcore.helpers import logger
from qcore.helpers import Server
from qcore.instruments.instrument import Instrument


class SetupServerWorker(QtCore.QObject):
    """ """

    server_ready = QtCore.pyqtSignal(Server)

    def run(self, config) -> None:
        """ """
        server = Server(config)
        self.server_ready.emit(server)


class RunServerWorker(QtCore.QObject):
    """ """

    done_serving = QtCore.pyqtSignal()

    def run(self, server: Server) -> None:
        """ """
        server.register()
        self.done_serving.emit()
        server.serve()


class Verse(QtWidgets.QWidget):
    """ """

    server_requested = QtCore.pyqtSignal(dict)
    serve_signal = QtCore.pyqtSignal(Server)

    def __init__(self, *args, **kwargs) -> None:
        """ """
        super().__init__(*args, **kwargs)

        self.ui = Ui_verse()
        self.ui.setupUi(self)

        self.instrument_server: Server = None
        self.default_instrument_config = InstrumentConfig()
        self.instrument_types = {
            cls.__name__: cls for cls in self.default_instrument_config
        }
        self.show_instrument_types()

        self.ui.add_button.clicked.connect(self.add_instrument)
        self.ui.remove_button.clicked.connect(self.remove_instrument)
        self.ui.setup_button.clicked.connect(self.setup_server)
        self.ui.serve_button.clicked.connect(self.run_server)
        self.ui.teardown_button.clicked.connect(self.teardown_server)

        self.instrument_config = None
        self.setup_server_worker = SetupServerWorker()
        self.setup_server_thread = QtCore.QThread()
        self.setup_server_worker.moveToThread(self.setup_server_thread)
        self.setup_server_thread.start()
        self.setup_server_worker.server_ready.connect(self.receive_server)
        self.server_requested.connect(self.setup_server_worker.run)

        self.run_server_worker = RunServerWorker()
        self.run_server_thread = QtCore.QThread()
        self.run_server_worker.moveToThread(self.run_server_thread)
        self.run_server_thread.start()
        self.run_server_worker.done_serving.connect(self.post_run_server)
        self.serve_signal.connect(self.run_server_worker.run)

        logger.remove()
        logger.add(
            self.ui.logbox.append,
            format="[{time:YY-MM-DD  HH:mm:ss}]   [{level}]   [{module}]   {message}",
            level="INFO",
            backtrace=False,
            diagnose=False,
        )

    def show_instrument_types(self) -> None:
        """ """
        instrument_type_choices = sorted(list(self.instrument_types.keys()))
        self.ui.instrument_type_choices.addItems(instrument_type_choices)
        self.ui.instrument_type_choices.activated.connect(self.show_instrument_ids)
        self.ui.instrument_type_choices.setCurrentIndex(-1)

    def show_instrument_ids(self) -> None:
        """ """
        instrument_type = self.ui.instrument_type_choices.currentText()
        ids = self.default_instrument_config[self.instrument_types[instrument_type]]
        self.ui.instrument_id_choices.clear()
        self.ui.instrument_id_choices.addItems(sorted(ids))

    def add_instrument(self) -> None:
        """ """
        instrument_type = self.ui.instrument_type_choices.currentText()
        instrument_id = self.ui.instrument_id_choices.currentText()
        instrument_item = f"{instrument_type}#{instrument_id}"
        matching_items = self.ui.instruments_list.findItems(
            instrument_item, QtCore.Qt.MatchFlag.MatchFixedString
        )
        if instrument_type and instrument_id and not matching_items:
            self.ui.instruments_list.addItem(instrument_item)

    def remove_instrument(self) -> None:
        """ """
        selected_instruments = self.ui.instruments_list.selectedItems()
        for selected_item in selected_instruments:
            row = self.ui.instruments_list.row(selected_item)
            self.ui.instruments_list.takeItem(row)

    def setup_server(self) -> None:
        """ """
        instrument_items = []
        for _ in range(self.ui.instruments_list.count()):
            item = self.ui.instruments_list.takeItem(0)
            instrument_items.append(item.text())

        self.instrument_config = defaultdict(list)
        for item in instrument_items:
            name, id = item.split("#")
            self.instrument_config[self.instrument_types[name]].append(id)

        if self.instrument_config:
            self.ui.setup_button.setEnabled(False)
            self.ui.add_button.setEnabled(False)
            self.ui.remove_button.setEnabled(False)

            logger.info("Setting up the instrument server, this may take up to 15s...")
            self.server_requested.emit(self.instrument_config)

    def receive_server(self, server: Server) -> None:
        """ """
        self.instrument_server = server
        connected_instruments = {instrument.name for instrument in server.instruments}
        conf = self.instrument_config.items()
        chosen_instruments = {f"{cls.__name__}#{id}" for cls, ids in conf for id in ids}
        for instrument_name in connected_instruments:
            self.ui.instruments_list.addItem(instrument_name)
            logger.info(f"Connected instrument '{instrument_name}'.")
        for instrument_name in chosen_instruments - connected_instruments:
            logger.info(f"Failed to connect instrument '{instrument_name}'.")

        logger.info(f"Ready to serve {len(server.services)} instruments.")
        self.ui.teardown_button.setEnabled(True)
        self.ui.serve_button.setEnabled(True)

    def run_server(self) -> None:
        """ """
        if self.instrument_server is not None:
            self.ui.teardown_button.setEnabled(False)
            self.serve_signal.emit(self.instrument_server)
            self.ui.serve_button.setEnabled(False)

    def post_run_server(self) -> None:
        """ """
        # delay emitting done signal to ensure server daemon request loop has started
        QtCore.QTimer().singleShot(
            100, lambda: self.ui.teardown_button.setEnabled(True)
        )
        logger.info(f"The instrument server is now running!")

    def teardown_server(self) -> None:
        """ """
        if self.instrument_server is not None:
            self.instrument_server.teardown()
            self.ui.instruments_list.clear()
            logger.info("The instrument server has been torn down!")
            self.ui.setup_button.setEnabled(True)
            self.ui.add_button.setEnabled(True)
            self.ui.remove_button.setEnabled(True)
            self.ui.serve_button.setEnabled(False)
            self.ui.teardown_button.setEnabled(False)
            self.instrument_server, self.instrument_config = None, None


if __name__ == "__main__":
    app = QtWidgets.QApplication([])
    verse = Verse()
    verse.show()
    app.exec()
