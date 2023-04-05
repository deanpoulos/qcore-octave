""" """

from typing import get_type_hints, Type

from PyQt5 import QtWidgets as qtw
from PyQt5 import QtCore as qtc

from qcore.gui.ui_instrument_widget import Ui_instrument_widget
from qcore.helpers.logger import logger
from qcore.instruments.instrument import Instrument, DummyInstrument, ConnectionError
from qcore.instruments.vaunix.lms import LMS


class InstrumentWidget(qtw.QWidget):
    """ """

    name_edited = qtc.pyqtSignal(str)

    def __init__(
        self, instrument: Instrument, type: Type[Instrument] = None, *args, **kwargs
    ) -> None:
        """ """
        super().__init__(*args, **kwargs)

        self.ui = Ui_instrument_widget()
        self.ui.setupUi(self)

        self.instrument = instrument
        self.instrument_type = type if type is not None else instrument.__class__
        self.ui.type_field.setText(self.instrument_type.__name__)
        self.ui.id_field.setText(instrument.id)
        self.setWindowTitle(f"{self.instrument_type.__name__}#{instrument.id}")

        self.fields = {"name": self.ui.name_field, "id": self.ui.id_field}
        self.create_parameters()

        for field in self.fields.values():
            field.returnPressed.connect(self.configure_instrument)

        self.ui.name_field.textChanged.connect(self.name_edited.emit)
        self.ui.refresh_button.clicked.connect(self.refresh_instrument)
        self.ui.connect_button.clicked.connect(self.connect_instrument)
        self.ui.disconnect_button.clicked.connect(self.disconnect_instrument)

        logger.info(f"Connected instrument '{self.instrument.name}'")
        self.refresh_instrument()

    def create_parameters(self):
        """ """
        parameters = self.instrument_type.params
        for name, param in parameters.items():
            if name not in self.fields:
                label = qtw.QLabel(self.ui.scroll_area_contents)
                label.setText(name)
                field = qtw.QLineEdit(self.ui.scroll_area_contents)
                if name in self.instrument_type.settable_params:
                    self.ui.settables_form.addRow(label, field)
                elif name in self.instrument_type.gettable_params:
                    self.ui.gettables_form.addRow(label, field)
                    field.setReadOnly(True)
                self.fields[name] = field

    def refresh_instrument(self):
        """ """
        self.update_parameters(**self.instrument.snapshot())
        logger.info(f"Updated instrument '{self.instrument.name}' parameters!!!")

    def update_parameters(self, status: bool, **snapshot):
        """ """
        self.update_status(status)
        for field in self.fields.values():
            field.setEnabled(status)
            field.clear()
        for name, value in snapshot.items():
            self.fields[name].setText(str(value))

    def update_status(self, status: bool):
        """ """
        status_text = "Connected" if status else "Not connected"
        self.ui.status_field.setText(status_text)
        self.ui.connect_button.setDisabled(status)
        self.ui.disconnect_button.setEnabled(status)

    def connect_instrument(self):
        """ """
        try:
            self.instrument.connect()
        except ConnectionError as err:
            logger.error(err)  # TODO error logging
        else:
            self.refresh_instrument()

    def disconnect_instrument(self):
        """ """
        self.instrument.disconnect()
        snapshot = {"name": self.instrument.name, "id": self.instrument.id}
        self.update_parameters(self.instrument.status, **snapshot)

    def configure_instrument(self):
        """ """
        parameters = {k: v.text() for k, v in self.fields.items() if not v.isReadOnly()}
        # TODO GET RID OF THIS HACK WITH BETTER INPUT VALIDATION AND PARSING
        for k, v in parameters.items():
            if v.lower() in ("t", "true"):
                parameters[k] = True
            elif v.lower() in ("f", "false"):
                parameters[k] = False

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
