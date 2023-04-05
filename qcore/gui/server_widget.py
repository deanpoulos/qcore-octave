""" """

from collections import defaultdict

from PyQt5 import QtWidgets as qtw
from PyQt5 import QtCore as qtc

from qcore.instruments.config import InstrumentConfig
from qcore.instruments.instrument import ConnectionError
from qcore.gui.ui_server_widget import Ui_server_widget
import qcore.helpers.server as server
from qcore.helpers.logger import logger


class SetupServerWorker(qtc.QObject):
    """ """

    server_ready = qtc.pyqtSignal(bool)

    def run(self, config) -> None:
        """ """
        try:
            instrument_server = server.Server(config)
        except ConnectionError as err:
            logger.error(err)  # TODO error logging
            self.server_ready.emit(False)
        else:
            self.server_ready.emit(True)
            instrument_server.serve()


class ServerWidget(qtw.QWidget):
    """ """

    server_requested = qtc.pyqtSignal(dict)
    is_serving = qtc.pyqtSignal(bool)

    def __init__(self, *args, **kwargs) -> None:
        """ """
        super().__init__(*args, **kwargs)

        self.ui = Ui_server_widget()
        self.ui.setupUi(self)

        instrumentspec = InstrumentConfig()
        self.instrument_types = {cls.__name__: cls for cls in instrumentspec}
        self.instrument_ids = {cls.__name__: ids for cls, ids in instrumentspec.items()}
        self.server, self.config, self.instruments = None, None, None

        self.ui.instrument_types_list.currentRowChanged.connect(self.show_instrument_id)
        self.ui.stage_button.clicked.connect(self.stage_instrument)
        self.ui.unstage_button.clicked.connect(self.unstage_instrument)
        self.ui.setup_button.clicked.connect(self.setup_server)
        self.ui.teardown_button.clicked.connect(self.teardown_server)

        self.setup_server_worker = SetupServerWorker()
        self.setup_server_thread = qtc.QThread()
        self.setup_server_worker.moveToThread(self.setup_server_thread)
        self.setup_server_thread.start()
        self.setup_server_worker.server_ready.connect(self.handle_server_ready)
        self.server_requested.connect(self.setup_server_worker.run)

        self.show_instrument_type()
        self.reset()

    def reset(self) -> None:
        """ """
        self.config, self.server, self.instruments = defaultdict(list), None, None
        self.ui.instrument_types_list.setCurrentRow(0)
        self.show_instrument_id()
        self.toggle_teardown_button()

    def freeze_buttons(self) -> None:
        """ """
        buttons = ("setup_button", "stage_button", "unstage_button", "teardown_button")
        for button in buttons:
            getattr(self.ui, button).setEnabled(False)

    def show_instrument_type(self) -> None:
        """ """
        instrument_types = sorted(list(self.instrument_types.keys()))
        self.ui.instrument_types_list.addItems(instrument_types)

    def toggle_stage_button(self) -> None:
        """ """
        self.ui.stage_button.setEnabled(bool(self.ui.instrument_ids_list.count()))

    def toggle_unstage_setup_buttons(self) -> None:
        """ """
        state = bool(self.ui.staged_instruments_list.count())
        self.ui.unstage_button.setEnabled(state)
        self.ui.setup_button.setEnabled(state)

    def toggle_teardown_button(self) -> None:
        """ """
        self.ui.teardown_button.setEnabled(self.server is not None)

    def show_instrument_id(self) -> None:
        """ """
        instrument_type_str = self.ui.instrument_types_list.currentItem().text()
        instrument_type = self.instrument_types[instrument_type_str]
        all_instrument_ids = self.instrument_ids[instrument_type_str]
        staged_instrument_ids = self.config[instrument_type]

        ids = sorted(list(set(all_instrument_ids) - set(staged_instrument_ids)))
        self.ui.instrument_ids_list.clear()
        self.ui.instrument_ids_list.addItems(ids)
        self.ui.instrument_ids_list.setCurrentRow(0)
        self.toggle_stage_button()

    def stage_instrument(self) -> None:
        """ """
        instrument_type = self.ui.instrument_types_list.currentItem().text()
        id_row = self.ui.instrument_ids_list.currentRow()
        instrument_id = self.ui.instrument_ids_list.takeItem(id_row).text()
        self.config[self.instrument_types[instrument_type]].append(instrument_id)
        self.ui.staged_instruments_list.addItem(f"{instrument_type}#{instrument_id}")
        self.toggle_stage_button()
        self.toggle_unstage_setup_buttons()

    def unstage_instrument(self) -> None:
        """ """
        selected_instruments = self.ui.staged_instruments_list.selectedItems()
        for selected_item in selected_instruments:
            selected_row = self.ui.staged_instruments_list.row(selected_item)
            instrument_item = self.ui.staged_instruments_list.takeItem(selected_row)
            instrument_type_str, instrument_id = instrument_item.text().split("#")
            instrument_type = self.instrument_types[instrument_type_str]
            self.config[instrument_type].remove(instrument_id)
        if selected_instruments:
            self.show_instrument_id()
            self.toggle_unstage_setup_buttons()

    def setup_server(self) -> None:
        """ """
        logger.info("Setting up Server, this may take up to 10s!!!")
        self.freeze_buttons()
        self.server_requested.emit(self.config)

    def handle_server_ready(self, is_ready: bool) -> None:
        """ """
        if is_ready:
            logger.info("Server is ready!!! Connecting instruments...")
            qtc.QTimer.singleShot(500, self.link_instruments)
        else:
            self.toggle_stage_button()
            self.toggle_unstage_setup_buttons()

    def link_instruments(self) -> None:
        """ """
        self.server, self.instruments = server.link()
        self.toggle_teardown_button()
        self.is_serving.emit(True)

    def teardown_server(self) -> None:
        """ """
        self.is_serving.emit(False)
        self.server.teardown()
        self.ui.staged_instruments_list.clear()
        self.reset()
        logger.info("Tore down Server!!!")


if __name__ == "__main__":
    app = qtw.QApplication([])
    server_widget = ServerWidget()
    server_widget.show()
    app.exec()
