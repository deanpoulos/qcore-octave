""" """

from PyQt5 import QtWidgets as qtw
from PyQt5 import QtCore as qtc

from qcore.instruments.gui.instrument_widget_ui import Ui_instrument_widget
from qcore.helpers.logger import logger
from qcore.instruments.instrument import Instrument, DummyInstrument, ConnectionError
from qcore.instruments.drivers.vaunix_lms import LMS


class InstrumentWidget(qtw.QWidget):
    """ """

    RO_FIELD_STYLE = "background-color: lightGray"

    name_edited = qtc.pyqtSignal(str)

    def __init__(self, instrument: Instrument, type=None, *args, **kwargs) -> None:
        """ """
        super().__init__(*args, **kwargs)

        self.ui = Ui_instrument_widget()
        self.ui.setupUi(self)

        self.instrument = instrument
        self.instrument_type = type if type is not None else instrument.__class__
        self.setWindowTitle(f"{self.instrument_type.__name__}#{instrument.id}")

        # initialize top-level read-only fields
        self.ui.type_field.setStyleSheet(InstrumentWidget.RO_FIELD_STYLE)
        self.ui.id_field.setStyleSheet(InstrumentWidget.RO_FIELD_STYLE)
        self.ui.status_field.setStyleSheet(InstrumentWidget.RO_FIELD_STYLE)
        self.ui.type_field.setText(self.instrument_type.__name__)
        self.ui.id_field.setText(instrument.id)

        # initialize with a nominal window size
        nominal_size = (600, 300)
        self.resize(*nominal_size)
        self.setMinimumSize(qtc.QSize(*nominal_size))

        # disable get, set, and disconnect buttons until instrument is connected
        self.ui.get_button.setEnabled(False)
        self.ui.set_button.setEnabled(False)
        self.ui.disconnect_button.setEnabled(False)

        self.fields: dict[str, qtw.QLineEdit] = {
            "id": self.ui.id_field,
            "name": self.ui.name_field,
            "status": self.ui.status_field,
        }
        self.ui.name_field.setText(instrument.name)
        self.ui.status_field.setText("Not connected")
        self.create_parameters()

        self.fields["name"].textChanged.connect(self.name_edited.emit)
        self.ui.connect_button.clicked.connect(self.connect_instrument)
        self.ui.disconnect_button.clicked.connect(self.disconnect_instrument)
        self.ui.get_button.clicked.connect(self.refresh_instrument)
        self.ui.set_button.clicked.connect(self.configure_instrument)

    def create_parameters(self):
        """ """
        for name in self.instrument_type.params:
            if name not in self.fields:
                label = qtw.QLabel(self.ui.scroll_area_contents)
                label.setText(name)
                field = qtw.QLineEdit(self.ui.scroll_area_contents)
                if name in self.instrument_type.settable_params:
                    self.ui.settables_form.addRow(label, field)
                elif name in self.instrument_type.gettable_params:
                    self.ui.gettables_form.addRow(label, field)
                    field.setReadOnly(True)
                    field.setStyleSheet(InstrumentWidget.RO_FIELD_STYLE)
                self.fields[name] = field

    def connect_instrument(self):
        """ """
        try:
            self.instrument.connect()
        except ConnectionError as err:
            logger.error(err)  # TODO error handling
        else:
            self.refresh_instrument()

    def disconnect_instrument(self):
        """ """
        try:
            self.instrument.disconnect()
        except ConnectionError as err:
            logger.error(err)  # TODO error handling
        else:
            self.update_status(self.instrument.status)

    def refresh_instrument(self):
        """ """
        self.update_parameters(**self.instrument.snapshot())
        logger.info(f"Updated instrument '{self.instrument.name}' parameters!!!")

    def update_parameters(self, status: bool, **snapshot):
        """ """
        for field in self.fields.values():
            field.setEnabled(status)
            field.clear()
        self.update_status(status)
        for name, value in snapshot.items():
            self.fields[name].setText(str(value))

    def update_status(self, status: bool):
        """ """
        status_text = "Connected" if status else "Not connected"
        self.ui.status_field.setText(status_text)
        self.ui.connect_button.setDisabled(status)
        self.ui.disconnect_button.setEnabled(status)
        self.ui.get_button.setEnabled(status)
        self.ui.set_button.setEnabled(status)

    def configure_instrument(self):
        """ """
        # TODO input text -> parameter type conversion
        parameters = {k: v.text() for k, v in self.fields.items()}
        try:
            self.instrument.configure(**parameters)
        except (ConnectionError, TypeError, ValueError) as err:
            logger.error(err)
        self.refresh_instrument()


if __name__ == "__main__":
    app = qtw.QApplication([])
    instrument = DummyInstrument(name="dummy", id="0")
    instrument_widget = InstrumentWidget(instrument=instrument)
    instrument_widget.show()
    app.exec()
