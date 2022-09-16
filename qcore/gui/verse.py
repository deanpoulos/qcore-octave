""" """

from collections import defaultdict

from PyQt5 import QtWidgets, QtCore

from qcore.instruments.config import InstrumentConfig
from qcore.gui.ui_verse import Ui_verse
from qcore.helpers import logger
from qcore.helpers import Client, Server


class SetupServerWorker(QtCore.QObject):
    """ """

    server_ready = QtCore.pyqtSignal()

    def run(self, config) -> None:
        """ """
        server = Server(config)
        self.server_ready.emit()
        server.serve()


class Verse(QtWidgets.QWidget):
    """ """

    server_requested = QtCore.pyqtSignal(dict)

    def __init__(self, *args, **kwargs) -> None:
        """ """
        super().__init__(*args, **kwargs)

        self.ui = Ui_verse()
        self.ui.setupUi(self)

        self.instrument_server: Server = None
        self.instruments: list = None
        self.instrument_config = defaultdict(list)

        instrumentspec = InstrumentConfig()
        self.instrument_types = {cls.__name__: cls for cls in instrumentspec}
        self.instrument_ids = {cls.__name__: ids for cls, ids in instrumentspec.items()}

        self.ui.instrument_types_list.currentRowChanged.connect(
            self.show_instrument_ids
        )
        self.show_instrument_types()

        self.ui.stage_button.clicked.connect(self.stage_instrument)
        self.ui.unstage_button.clicked.connect(self.unstage_instrument)
        self.ui.setup_button.clicked.connect(self.setup_server)
        self.ui.teardown_button.clicked.connect(self.teardown_server)

        self.setup_server_worker = SetupServerWorker()
        self.setup_server_thread = QtCore.QThread()
        self.setup_server_worker.moveToThread(self.setup_server_thread)
        self.setup_server_thread.start()
        self.setup_server_worker.server_ready.connect(self.handle_server_ready)
        self.server_requested.connect(self.setup_server_worker.run)

        logger.remove()
        logfmt = "[{time:YY-MM-DD  HH:mm:ss}]   [{level}]   [{module}]   {message}"
        sink = self.ui.logbox.append
        logger.add(sink, format=logfmt, level="INFO", backtrace=False, diagnose=False)

    def closeEvent(self, event) -> None:
        """ """
        if self.instrument_server is not None:
            self.instrument_server.teardown()
        self.setup_server_thread.quit()
        event.accept()

    def show_instrument_types(self) -> None:
        """ """
        instrument_types = sorted(list(self.instrument_types.keys()))
        self.ui.instrument_types_list.addItems(instrument_types)
        self.ui.instrument_types_list.setCurrentRow(0)

    def show_instrument_ids(self) -> None:
        """ """
        instrument_type_str = self.ui.instrument_types_list.currentItem().text()
        all_instrument_ids = self.instrument_ids[instrument_type_str]
        instrument_type = self.instrument_types[instrument_type_str]
        staged_instrument_ids = self.instrument_config[instrument_type]
        ids = sorted(list(set(all_instrument_ids) - set(staged_instrument_ids)))
        self.ui.instrument_ids_list.clear()
        if ids:
            self.ui.instrument_ids_list.addItems(sorted(ids))
            self.ui.instrument_ids_list.setCurrentRow(0)
        else:
            self.ui.stage_button.setEnabled(False)

        if ids and self.instrument_server is None:
            self.ui.stage_button.setEnabled(True)

    def stage_instrument(self) -> None:
        """ """
        instrument_type_str = self.ui.instrument_types_list.currentItem().text()
        instrument_type = self.instrument_types[instrument_type_str]
        id_row = self.ui.instrument_ids_list.currentRow()
        instrument_id = self.ui.instrument_ids_list.takeItem(id_row).text()
        self.instrument_config[instrument_type].append(instrument_id)

        instrument_item = f"{instrument_type_str}#{instrument_id}"
        self.ui.staged_instruments_list.addItem(instrument_item)
        self.ui.unstage_button.setEnabled(True)
        self.ui.setup_button.setEnabled(True)
        if not self.ui.instrument_ids_list.count():
            self.ui.stage_button.setEnabled(False)

    def unstage_instrument(self) -> None:
        """ """
        selected_instruments = self.ui.staged_instruments_list.selectedItems()
        for selected_item in selected_instruments:
            row = self.ui.staged_instruments_list.row(selected_item)
            self.ui.staged_instruments_list.takeItem(row)
            instrument_type_str, instrument_id = selected_item.text().split("#")
            instrument_type = self.instrument_types[instrument_type_str]
            self.instrument_config[instrument_type].remove(instrument_id)
            (instrument_type_item,) = self.ui.instrument_types_list.findItems(
                instrument_type_str, QtCore.Qt.MatchFlag.MatchFixedString
            )
            self.ui.instrument_types_list.setCurrentItem(instrument_type_item)
            self.show_instrument_ids()

        if not self.ui.staged_instruments_list.count():
            self.ui.unstage_button.setEnabled(False)
            self.ui.setup_button.setEnabled(False)

    def setup_server(self) -> None:
        """ """
        logger.info("Setting up the instrument server, this may take up to 10s...")
        self.ui.setup_button.setEnabled(False)
        self.ui.stage_button.setEnabled(False)
        self.ui.unstage_button.setEnabled(False)
        self.server_requested.emit(self.instrument_config)

    def handle_server_ready(self) -> None:
        """ """
        QtCore.QTimer.singleShot(200, self.show_instruments)

    def show_instruments(self) -> None:
        """ """
        self.instrument_server, self.instruments = Client().link()
        connected_instruments = {instrument.name for instrument in self.instruments}
        cfg = self.instrument_config.items()
        chosen_instruments = {f"{cls.__name__}#{id}" for cls, ids in cfg for id in ids}

        for instrument_name in connected_instruments:
            logger.info(f"Connected instrument '{instrument_name}'    :-)))")
        for instrument_name in chosen_instruments - connected_instruments:
            logger.info(f"Failed to connect instrument '{instrument_name}'    :-(((")
        num_connected, num_chosen = len(connected_instruments), len(chosen_instruments)
        logger.info(f"Now serving {num_connected} out of {num_chosen} instruments!!!")

        self.ui.teardown_button.setEnabled(True)

    def teardown_server(self) -> None:
        """ """
        self.instrument_server.teardown()
        self.instrument_config = defaultdict(list)
        self.ui.instrument_types_list.setCurrentRow(0)
        self.show_instrument_ids()
        self.ui.staged_instruments_list.clear()
        logger.info("The instrument server has been torn down!!!")
        self.ui.teardown_button.setEnabled(False)
        self.instrument_server = None
        self.ui.stage_button.setEnabled(True)


if __name__ == "__main__":
    app = QtWidgets.QApplication([])
    verse = Verse()
    verse.show()
    app.exec()
