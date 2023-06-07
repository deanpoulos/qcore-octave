""" """

from PyQt5 import QtWidgets as qtw
from PyQt5 import QtCore as qtc
import Pyro5.api as pyro

from qcore.instruments.config import InstrumentConfig
from qcore.instruments.instrument import Instrument, ConnectionError
from qcore.instruments.gui.verse_ui import Ui_verse
from qcore.instruments.gui.instrument_widget import InstrumentWidget
from qcore.helpers.logger import logger
from qcore.resource import Resource


class RemoteInstrumentConfig:
    """ """

    DELIMITER: str = "#"  # default name "<instrument type><DELIMITER><instrument id>""

    def __init__(self, cls, id) -> None:
        """ """
        self.name = f"{cls.__name__}{RemoteInstrumentConfig.DELIMITER}{id}"
        self.type = cls
        self.id = id
        self.is_staged = False
        self.uri = None
        self.proxy = None
        self.worker = None
        self.thread = None

    @property
    def is_served(self) -> bool:
        """ """
        return self.proxy is not None


class ServerWorker(qtc.QObject):
    """ """

    instrument_served = qtc.pyqtSignal(bool, str, str)

    def __init__(self, type, id, name, *args, **kwargs):
        """ """
        super().__init__(*args, **kwargs)
        self.instrument_type = type
        self.instrument_id = id
        self.instrument_name = name
        self.daemon = pyro.Daemon()

    def run(self):
        """ """
        success, uri = False, None

        # connect to instrument
        try:
            id, name = self.instrument_id, self.instrument_name
            instrument = self.instrument_type(id=id, name=name)
        except ConnectionError as err:
            uri = str(err)  # replace uri with error message if success == False
        else:
            success = True

        # serve instrument
        if success:
            pyro.expose(self.instrument_type)
            uri = self.daemon.register(instrument, objectId=self.instrument_name)
        self.instrument_served.emit(success, self.instrument_name, str(uri))
        if success:
            with self.daemon:
                self.daemon.requestLoop()


class Verse(qtw.QWidget):
    """ """

    SINGLE_SHOT_DELAY: int = 1000  # to control server thread generation time

    def __init__(self, *args, **kwargs) -> None:
        """ """
        super().__init__(*args, **kwargs)

        # initialize the user interface
        self.ui = Ui_verse()
        self.ui.setupUi(self)

        # initialize with a nominal window and tab size
        nominal_size = (1500, 800)
        self.resize(*nominal_size)
        self.setMinimumSize(qtc.QSize(*nominal_size))
        self.ui.verse_tabs.setStyleSheet("QTabBar::tab {min-width: 150px}")

        # reroute the logger to the message box in the UI
        logger.remove()
        logfmt = "[{time:YY-MM-DD  HH:mm:ss}]   [{level}]   [{module}]   {message}"
        sink = self.ui.message_box.append
        logger.add(sink, format=logfmt, level="INFO", backtrace=False, diagnose=False)

        # create a dictionaries of instrument configs, types, and ids for easy access
        base_config = InstrumentConfig()
        self.instrument_configs: dict[str, RemoteInstrumentConfig] = {}
        for cls, ids in base_config.items():
            for id in ids:
                config = RemoteInstrumentConfig(cls, id)
                self.instrument_configs[config.name] = config
        self.instrument_types = {cls.__name__: cls for cls in base_config}
        self.instrument_ids = {cls.__name__: ids for cls, ids in base_config.items()}

        # temporary variables to keep track of server status while serving instruments
        self.instruments_to_serve, self.num_instruments_served = [], 0

        # expose parent classes to ensure all instrument types can be served remotely
        pyro.expose(Resource)
        pyro.expose(Instrument)

        # connect signals and slots in the buttons and lists in verse's user interface
        types_list = self.ui.instrument_types_list
        types_list.currentRowChanged.connect(self.show_instrument_ids)
        types_list.addItems(sorted(self.instrument_types.keys()))
        types_list.setCurrentRow(0)

        staged_list = self.ui.staged_instruments_list
        staged_list.itemSelectionChanged.connect(self.toggle_unstage_serve_button)

        self.ui.stage_button.clicked.connect(self.stage_instruments)
        self.ui.unstage_button.clicked.connect(self.unstage_instruments)
        self.ui.serve_button.clicked.connect(self.serve_instruments)
        
        self.ui.verse_tabs.tabCloseRequested.connect(self.handle_tab_close)

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

    def show_instrument_ids(self) -> None:
        """ """
        instrument_type_str = self.ui.instrument_types_list.currentItem().text()
        instrument_type = self.instrument_types[instrument_type_str]

        # get all available ids of current instrument type
        ids = []
        for cfg in self.instrument_configs.values():
            if cfg.type is instrument_type and not cfg.is_staged and not cfg.is_served:
                ids.append(cfg.id)

        self.ui.instrument_ids_list.clear()
        self.ui.instrument_ids_list.addItems(sorted(ids))
        self.ui.instrument_ids_list.setCurrentRow(0)
        self.toggle_stage_button()

    def toggle_stage_button(self) -> None:
        """ """
        is_enabled = bool(self.ui.instrument_ids_list.count())
        self.ui.stage_button.setEnabled(is_enabled)

    def toggle_unstage_serve_button(self) -> None:
        """ """
        state = bool(self.ui.staged_instruments_list.selectedItems())
        self.ui.unstage_button.setEnabled(state)
        self.ui.serve_button.setEnabled(state)

    def stage_instruments(self) -> None:
        """ """
        type_str = self.ui.instrument_types_list.currentItem().text()
        id_row = self.ui.instrument_ids_list.currentRow()
        id_str = self.ui.instrument_ids_list.takeItem(id_row).text()
        instrument_name = f"{type_str}{RemoteInstrumentConfig.DELIMITER}{id_str}"

        self.instrument_configs[instrument_name].is_staged = True
        self.ui.staged_instruments_list.addItem(instrument_name)

        self.toggle_stage_button()
        self.toggle_unstage_serve_button()

    def unstage_instruments(self) -> None:
        """ """
        staged_list = self.ui.staged_instruments_list
        for selected_item in staged_list.selectedItems():
            selected_row = staged_list.row(selected_item)
            instrument_name = staged_list.takeItem(selected_row).text()
            self.instrument_configs[instrument_name].is_staged = False
        self.show_instrument_ids()
        self.toggle_unstage_serve_button()

    def serve_instruments(self) -> None:
        """ """
        self.toggle_ui_freeze(True)
        staged_list = self.ui.staged_instruments_list
        selected_instruments = staged_list.selectedItems()
        self.instruments_to_serve = [item.text() for item in selected_instruments]
        for selected_item in selected_instruments:
            selected_row = staged_list.row(selected_item)
            instrument_name = staged_list.item(selected_row).text()
            worker = self.create_worker_thread(instrument_name)
            logger.info(f"Serving {instrument_name}...")
            qtc.QTimer.singleShot(Verse.SINGLE_SHOT_DELAY, worker.run)

    def create_worker_thread(self, instrument_name: str) -> ServerWorker:
        """ """
        config = self.instrument_configs[instrument_name]
        worker = ServerWorker(config.type, config.id, config.name)
        thread = qtc.QThread()
        worker.moveToThread(thread)
        thread.start()
        worker.instrument_served.connect(self.handle_instrument_served)
        config.worker, config.thread = worker, thread
        return worker

    def handle_instrument_served(self, success, name, uri) -> None:
        """ """
        self.num_instruments_served += 1
        config = self.instrument_configs[name]
        if not success:
            logger.error(uri)
            config.thread.quit()
            config.thread.wait()
        else:
            config.uri = uri

        if self.num_instruments_served == len(self.instruments_to_serve):
            self.num_instruments_served = 0  # reset counter
            qtc.QTimer.singleShot(Verse.SINGLE_SHOT_DELAY, self.link_instruments)

    def link_instruments(self) -> None:
        """ """
        staged_list = self.ui.staged_instruments_list
        for name in self.instruments_to_serve:
            config = self.instrument_configs[name]
            if config.uri is not None:  # instrument has been served successfully
                config.proxy = pyro.Proxy(config.uri)
                logger.success(f"Connected to {config.proxy.name}!")
                flag = qtc.Qt.MatchFlag.MatchExactly
                (instrument_item,) = staged_list.findItems(name, flag)
                instrument_row = staged_list.row(instrument_item)
                staged_list.takeItem(instrument_row)
                config.is_staged = False
                instrument_widget = InstrumentWidget(config.proxy, type=config.type)
                instrument_widget.name_edited.connect(self.update_instrument_name)
                self.ui.verse_tabs.addTab(instrument_widget, config.name)

        self.toggle_ui_freeze(False)
        self.toggle_stage_button()
        self.toggle_unstage_serve_button()

    def update_instrument_name(self, new_name: str) -> None:
        """ """
        self.ui.verse_tabs.setTabText(self.ui.verse_tabs.currentIndex(), new_name)

    def handle_tab_close(self, index: int) -> None:
        """ """
        widget = self.ui.verse_tabs.widget(index)
        
        if isinstance(widget, InstrumentWidget):
            self.close_instrument_widget(widget, index)
        else:
            self.close_server()
            self.close()

    def close_instrument_widget(self, widget, index):
        """ """
        key = f"{widget.instrument_type.__name__}#{widget.instrument.id}"
        config = self.instrument_configs[key]

        if widget.ui.disconnect_button.isEnabled():
            widget.disconnect_instrument()

        config.proxy._pyroRelease()
        config.proxy, config.uri = None, None

        config.worker.daemon.shutdown()
        config.thread.quit()
        config.thread.wait()
        config.thread, config.worker = None, None

        config.is_staged = False
        self.show_instrument_ids()
        
        self.ui.verse_tabs.removeTab(index)

    def close_server(self):
        """ """
        self.toggle_ui_freeze(True)
        # do while no more instrument widgets are open, then close server window 
        count, stop = 0, False
        while not stop:
            widget = self.ui.verse_tabs.widget(count)
            if isinstance(widget, InstrumentWidget):
                self.close_instrument_widget(widget, count)
            elif widget is None:
                stop = True
            else:
                self.ui.verse_tabs.removeTab(count)

    def closeEvent(self, event):
        """ """
        self.close_server()
        event.accept()

if __name__ == "__main__":
    app = qtw.QApplication([])
    verse = Verse()
    verse.show()
    app.exec()
