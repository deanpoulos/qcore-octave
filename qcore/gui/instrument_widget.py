""" """

from typing import get_type_hints, Type

from PyQt5 import QtWidgets as qtw
from PyQt5 import QtCore as qtc

from qcore.gui.ui_instrument_widget import Ui_instrument_widget
from qcore.instruments.instrument import Instrument, DummyInstrument, ConnectionError
from qcore.instruments.vaunix.lms import LMS

class InstrumentWidget(qtw.QWidget):
    """ """

    def __init__(self, instrument: Instrument, *args, **kwargs) -> None:
        """ """
        super().__init__(*args, **kwargs)

        self.ui = Ui_instrument_widget()
        self.ui.setupUi(self)
        self.setWindowTitle(f"{instrument}")

        self.instrument = instrument
        self.fields = {"name": self.ui.name, "id": self.ui.id}
        self.show_parameters()

        self.ui.refresh_button.clicked.connect(self.refresh_instrument)
        self.ui.connect_button.clicked.connect(self.connect_instrument)
        self.ui.disconnect_button.clicked.connect(self.disconnect_instrument)

        self.refresh_instrument()

    def show_parameters(self):
        """ """
        gettables = sorted(self.instrument.gettables)
        settables = sorted(self.instrument.settables)
        gettables.remove("status")
        for name in settables:
            if name not in self.fields:
                self.add_field(name, read_only=False)
            self.fields[name].returnPressed.connect(self.configure_instrument)
        for name in gettables:
            if name not in self.fields:
                self.add_field(name)

    def add_field(self, name, read_only=True):
        """ """
        label = qtw.QLabel(self.ui.scroll_area_contents)
        label.setText(name)
        field = qtw.QLineEdit(self.ui.scroll_area_contents)
        field.setReadOnly(read_only)
        self.fields[name] = field
        self.ui.p_layout.addWidget(label)
        self.ui.p_layout.addWidget(field)

    def refresh_instrument(self):
        """ """
        snapshot = self.instrument.snapshot()
        status = snapshot.pop("status")
        self.toggle_connection_buttons(status)
        self.update_fields(status, snapshot)

    def toggle_connection_buttons(self, status: bool):
        """ """
        self.ui.status_button.setChecked(status)
        self.ui.connect_button.setDisabled(status)
        self.ui.disconnect_button.setEnabled(status)

    def update_fields(self, status: bool, snapshot: dict):
        """ """
        for field in self.fields.values():
            field.setEnabled(status)
            field.clear()
        for name, value in snapshot.items():
            self.fields[name].setText(str(value))

    def connect_instrument(self):
        """ """
        try:
            self.instrument.connect()
        except ConnectionError as err:
            print(f"{err}")  # TODO error logging
        else:
            self.refresh_instrument()

    def disconnect_instrument(self):
        """ """
        self.instrument.disconnect()
        self.refresh_instrument()

    def configure_instrument(self):
        """TODO INPUT VALIDATION, PARAMETER CLASS"""
        settables = {k: v for k, v in self.fields.items() if not v.isReadOnly()}
        parameters = dict.fromkeys(settables)
        for name, field in settables.items():
            setter = getattr(self.cls, name).fset
            type_hints = get_type_hints(setter)
            # HARD CODED AND VERY HACKY, PLEASE CHANGE THIS
            cast = type_hints["value"] if "value" in type_hints else str
            text = field.text()
            if cast is bool:
                if text.lower() in ("t", "true"):
                    parameters[name] = True
                elif text.lower() in ("f", "false"):
                    parameters[name] = False
            else:
                try:
                    parameters[name] = cast(text)
                except (TypeError, ValueError):
                    parameters[name] = text
        try:
            self.instrument.configure(**parameters)
        except (ConnectionError, TypeError, ValueError) as err:
            print(err)
            pass
        self.refresh_instrument()


if __name__ == "__main__":
    app = qtw.QApplication([])
    instrument = DummyInstrument(name="dummy", id="0")
    instrument_widget = InstrumentWidget(instrument=instrument)
    instrument_widget.show()
    app.exec()
