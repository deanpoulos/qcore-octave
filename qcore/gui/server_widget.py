""" """

from collections import defaultdict

from PyQt5 import QtWidgets as qtw
from PyQt5 import QtCore as qtc
import Pyro5.api as pyro

from qcore.instruments.config import InstrumentConfig
from qcore.instruments.instrument import Instrument, ConnectionError
from qcore.gui.ui_server_widget import Ui_server_widget
from qcore.helpers.logger import logger
from qcore.resource import Resource, ResourceMetaclass


class ServerWorker(qtc.QObject):
    """ """

    instrument_served = qtc.pyqtSignal(bool, str, str)

    PORT = 9090  # port to bind a remote server on, used to initialize Pyro Daemon

    def __init__(self, instrument_type, instrument_id, *args, **kwargs):
        """ """
        super().__init__(*args, **kwargs)
        self.instrument_type = instrument_type
        self.instrument_id = instrument_id
        self.daemon = pyro.Daemon(port=ServerWorker.PORT)

    def run(self):
        """ """
        name = f"{self.instrument_type.__name__}#{self.instrument_id}"
        success, uri = False, None

        # connect to instrument
        try:
            instrument = self.instrument_type(id=self.instrument_id, name=name)
        except ConnectionError as err:
            uri = str(err)  # replace uri with error message if success == False
        else:
            success = True

        # serve instrument
        if success:
            pyro.expose(self.instrument_type)
            uri = self.daemon.register(instrument, objectId=name)
        self.instrument_served.emit(success, name, str(uri))
        if success:
            with self.daemon:
                self.daemon.requestLoop()


class ServerWidget(qtw.QWidget):
    """ """

    all_selected_instruments_served = qtc.pyqtSignal()

    def __init__(self, *args, **kwargs) -> None:
        """ """
        super().__init__(*args, **kwargs)

        self.ui = Ui_server_widget()
        self.ui.setupUi(self)

        instrumentspec = InstrumentConfig()
        self.instrument_types = {cls.__name__: cls for cls in instrumentspec}
        self.instrument_ids = {cls.__name__: ids for cls, ids in instrumentspec.items()}
        self.staged_instruments_config = defaultdict(list)

        self.num_instruments_to_serve, self.num_instruments_served = 0, 0
        self.instrument_services = {}
        self.instrument_proxies = set()

        self.server_workers_threads = {}
        pyro.expose(Resource)
        pyro.expose(Instrument)

        self.all_selected_instruments_served.connect(self.link_instruments)

        self.ui.instrument_types_list.currentRowChanged.connect(self.show_instrument_id)
        instrument_types = sorted(list(self.instrument_types.keys()))
        self.ui.instrument_types_list.addItems(instrument_types)
        self.ui.instrument_types_list.setCurrentRow(0)

        self.ui.staged_instruments_list.itemSelectionChanged.connect(
            self.toggle_unstage_button
        )
        self.ui.staged_instruments_list.itemSelectionChanged.connect(
            self.toggle_serve_button
        )

        self.ui.stage_button.clicked.connect(self.stage_instrument)
        self.ui.unstage_button.clicked.connect(self.unstage_instrument)
        self.ui.serve_button.clicked.connect(self.serve_instruments)

    def toggle_ui_freeze(self, state: bool) -> None:
        """ """
        do_freeze = not state
        buttons = ("serve_button", "stage_button", "unstage_button")
        for button in buttons:
            getattr(self.ui, button).setEnabled(do_freeze)
        lists = (
            "instrument_types_list",
            "instrument_ids_list",
            "staged_instruments_list",
        )
        for list_ in lists:
            getattr(self.ui, list_).setEnabled(do_freeze)

    def show_instrument_id(self) -> None:
        """ """
        instrument_type_str = self.ui.instrument_types_list.currentItem().text()
        instrument_type = self.instrument_types[instrument_type_str]
        all_instr_ids = set(self.instrument_ids[instrument_type_str])
        staged_instr_ids = set(self.staged_instruments_config[instrument_type])
        connected_instr_ids = {k.split("#")[1] for k in self.instrument_services}

        ids = sorted(list(all_instr_ids - staged_instr_ids - connected_instr_ids))
        self.ui.instrument_ids_list.clear()
        self.ui.instrument_ids_list.addItems(ids)
        self.ui.instrument_ids_list.setCurrentRow(0)
        self.toggle_stage_button()

    def toggle_stage_button(self) -> None:
        """ """
        is_enabled = bool(self.ui.instrument_ids_list.count())
        self.ui.stage_button.setEnabled(is_enabled)

    def toggle_unstage_button(self) -> None:
        """ """
        state = bool(self.ui.staged_instruments_list.selectedItems())
        self.ui.unstage_button.setEnabled(state)

    def toggle_serve_button(self) -> None:
        """ """
        state = bool(self.ui.staged_instruments_list.selectedItems())
        self.ui.serve_button.setEnabled(state)

    def stage_instrument(self) -> None:
        """ """
        instrument_type_str = self.ui.instrument_types_list.currentItem().text()
        id_row = self.ui.instrument_ids_list.currentRow()
        instrument_id_str = self.ui.instrument_ids_list.takeItem(id_row).text()

        instrument_type = self.instrument_types[instrument_type_str]
        self.staged_instruments_config[instrument_type].append(instrument_id_str)

        staged_instrument_str = f"{instrument_type_str}#{instrument_id_str}"
        self.ui.staged_instruments_list.addItem(staged_instrument_str)

        self.toggle_stage_button()
        self.toggle_unstage_button()

    def unstage_instrument(self) -> None:
        """ """
        selected_instruments = self.ui.staged_instruments_list.selectedItems()
        for selected_item in selected_instruments:
            selected_row = self.ui.staged_instruments_list.row(selected_item)
            instrument_item = self.ui.staged_instruments_list.takeItem(selected_row)
            instrument_type_str, instrument_id = instrument_item.text().split("#")
            instrument_type = self.instrument_types[instrument_type_str]
            self.staged_instruments_config[instrument_type].remove(instrument_id)
        if selected_instruments:
            self.show_instrument_id()
            self.toggle_unstage_button()
            self.toggle_serve_button()

    def serve_instruments(self) -> None:
        """ """
        selected_instruments = self.ui.staged_instruments_list.selectedItems()
        self.toggle_ui_freeze(True)
        self.num_instruments_to_serve = len(selected_instruments)
        for selected_item in selected_instruments:
            selected_row = self.ui.staged_instruments_list.row(selected_item)
            instrument_str = self.ui.staged_instruments_list.item(selected_row).text()
            instrument_type_str, instrument_id = instrument_str.split("#")
            instrument_type = self.instrument_types[instrument_type_str]

            worker = self.create_server_worker_thread(
                instrument_str, instrument_type, instrument_id
            )

            logger.info(f"Serving {instrument_str}...")
            qtc.QTimer.singleShot(1000, worker.run)

    def create_server_worker_thread(
        self, instrument_str, instrument_type, instrument_id
    ) -> None:
        """ """
        server_worker = ServerWorker(instrument_type, instrument_id)
        serve_instrument_thread = qtc.QThread()
        server_worker.moveToThread(serve_instrument_thread)
        serve_instrument_thread.start()
        server_worker.instrument_served.connect(self.handle_instrument_served)
        self.server_workers_threads[instrument_str] = (
            server_worker,
            serve_instrument_thread,
        )
        return server_worker

    def handle_instrument_served(self, success, name, uri) -> None:
        """ """
        self.num_instruments_served += 1
        if not success:
            logger.error(uri)
            _, thread = self.server_workers_threads.pop(name)
            thread.quit()
            thread.wait()
        else:
            self.instrument_services[name] = uri
            logger.success(f"Connected to {name}!")

        if self.num_instruments_to_serve == self.num_instruments_served:
            qtc.QTimer.singleShot(1000, self.all_selected_instruments_served.emit)
            self.num_instruments_to_serve, self.num_instruments_served = 0, 0

    def link_instruments(self) -> None:
        """ """
        for name, uri in self.instrument_services.items():
            self.instrument_proxies.add(pyro.Proxy(uri))
            flag = qtc.Qt.MatchFlag.MatchContains
            instrument_items = self.ui.staged_instruments_list.findItems(name, flag)
            for instrument_item in instrument_items:
                instrument_row = self.ui.staged_instruments_list.row(instrument_item)
                self.ui.staged_instruments_list.takeItem(instrument_row)

        self.toggle_ui_freeze(False)
        self.toggle_stage_button()
        self.toggle_unstage_button()
        self.toggle_serve_button()


if __name__ == "__main__":
    app = qtw.QApplication([])
    server_widget = ServerWidget()
    server_widget.show()
    app.exec()
