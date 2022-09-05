""" """

import time

from labctrl import Instrument
import numpy as np
import pyvisa


class GS200(Instrument):
    """Python driver to use Yokogawa GS200 as a current source"""

    # GS200 takes 10ms to change source level and 20ms for output relay to stabilize
    WAIT_TIME = 0.1  # we set it to 0.1s to be safe

    def __init__(
        self,
        name: str,
        id: str,
        current: float = 0.0,  # Ampere
        output_on: bool = False,
    ) -> None:
        """ """
        self._handle: pyvisa.resources.Resource = None
        super().__init__(id=id, name=name, current=current, output_on=output_on)

        # assume qcrew uses GS200 as a current source, so we hard code this for now
        self._handle.write("source:function current")

    @property
    def status(self) -> bool:
        """ """
        try:
            self._handle.query("*IDN?")
        except (pyvisa.errors.VisaIOError, pyvisa.errors.InvalidSession):
            return False
        else:
            return True

    def connect(self) -> None:
        """ """
        if self.status or self._handle is not None:  # close any existing connections
            self.disconnect()

        resource_name = f"USB::0xB21::0x39::{self.id}::INSTR"
        self._handle = pyvisa.ResourceManager().open_resource(resource_name)

    def disconnect(self) -> None:
        """ """
        self._handle.close()

    @property
    def current(self) -> float:
        """ """
        return float(self._handle.query(":source:level?"))

    @current.setter
    def current(self, value: float) -> None:
        """ """
        self._handle.write(f":source:level:auto {value}")
        time.sleep(GS200.WAIT_TIME)

    @property
    def output_on(self) -> bool:
        """ """
        return bool(int(self._handle.query(":output?")))

    @output_on.setter
    def output_on(self, value: bool) -> None:
        """ """
        self._handle.write(f"output {int(bool(value))}")
        time.sleep(GS200.WAIT_TIME)

    def ramp(self, stop, start=None, step=1e-4) -> None:
        """ """
        if start is None:  # start from the current level set right now
            start = self.current

        if start > stop:  # ramp down
            points = np.arange(stop, start + step / 2, step)[::-1]  # include endpoint
        else:  # ramp up
            points = np.arange(start, stop + step / 2, step)

        for point in points:
            self.current = point
            time.sleep(GS200.WAIT_TIME)
