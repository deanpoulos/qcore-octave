""" """

from ctypes import CDLL, c_int
from pathlib import Path

from qcore.instrument import Instrument, ConnectionError

# DLL driver must be placed in the same folder as this file
DLL = CDLL(str(Path(__file__).parent / "lms.dll"))

# LMS encodes frequency as an integer of 10Hz steps
UNIT_FREQUENCY = 10.0


def to_frequency(value: int) -> float:
    """Convert LMS coded frequency to actual frequency"""
    return value * UNIT_FREQUENCY


def from_frequency(value: int) -> int:
    """Convert frequency to LMS coded frequency"""
    return int(value / UNIT_FREQUENCY)


# LMS encodes power level as an integer of 0.25dB steps
UNIT_POWER = 0.25


def to_power(value: int) -> float:
    """Convert LMS encoded power to actual power"""
    return value * UNIT_POWER


def from_power(value: float) -> int:
    """Convert actual power to LMS encoded power"""
    return int(value / UNIT_POWER)


class LMS(Instrument):
    """ """

    def __init__(
        self,
        name: str,
        id: int,
        frequency: float = 6e9,
        power: float = 0.0,
        output: bool = False,
    ) -> None:
        """ """
        self._handle = None
        super().__init__(id, name=name, frequency=frequency, power=power, output=output)

        DLL.fnLMS_SetTestMode(False)  # we are using actual hardware
        DLL.fnLMS_SetUseInternalRef(self._handle, False)  # use external 10MHz reference

    def _errorcheck(self, errorcode: int) -> None:
        """Only if we get bad values during setting params"""
        if errorcode:  # non-zero return values indicate error
            message = f"Got {errorcode = } from {self}, reconnect device."
            self._handle = None
            raise ConnectionError(message)

    @property
    def status(self) -> bool:
        """A connected LMS responds with an integer status code of 16395"""
        return DLL.fnLMS_GetDeviceStatus(self._handle) == 16395

    def connect(self) -> None:
        """ """
        # close any existing connection
        if self._handle is not None:
            self.disconnect()

        numdevices = DLL.fnLMS_GetNumDevices()
        deviceinfo = (c_int * numdevices)()
        DLL.fnLMS_GetDevInfo(deviceinfo)
        ids = [DLL.fnLMS_GetSerialNumber(deviceinfo[i]) for i in range(numdevices)]
        if self.id in ids:  # LMS is found, try opening it
            handle = deviceinfo[ids.index(self.id)]
            error = DLL.fnLMS_InitDevice(handle)
            if not error:  # 0 indicates successful device initialization
                self._handle = handle
                return
            raise ConnectionError(f"Failed to connect {self}.")
        raise ConnectionError(f"{self} is not available for connection.")

    def disconnect(self):
        """ """
        self._errorcheck(DLL.fnLMS_CloseDevice(self._handle))
        self._handle = None

    @property
    def clocked(self) -> bool:
        """The hex code for PLL_LOCKED flag is 0x00000040 in vnx_LMS_api.h"""
        return bool(int(hex(DLL.fnLMS_GetDeviceStatus(self._handle))[-2]))

    @property
    def output(self) -> bool:
        """ """
        value = DLL.fnLMS_GetRF_On(self._handle)
        bounds = (0, 1)
        if value not in bounds:
            message = f"Output {value = } out of {bounds = }, check USB connection."
            raise ConnectionError(message)
        return bool(value)

    @output.setter
    def output(self, value: bool) -> None:
        """ """
        if not isinstance(value, bool):
            message = f"Expect boolean output value, not {value = } of {type(value)}."
            raise ValueError(message)
        self._errorcheck(DLL.fnLMS_SetRFOn(self._handle, value))

    @property
    def min_frequency(self) -> float:
        """ """
        return to_frequency(DLL.fnLMS_GetMinFreq(self._handle))

    @property
    def max_frequency(self) -> float:
        """ """
        return to_frequency(DLL.fnLMS_GetMaxFreq(self._handle))

    @property
    def frequency(self) -> float:
        """ """
        value = to_frequency(DLL.fnLMS_GetFrequency(self._handle))
        in_bounds = self.min_frequency <= value <= self.max_frequency
        if not in_bounds:
            bounds = f"[{self.min_frequency:.2E}, {self.max_frequency:.2E}]"
            message = f"Frequency {value = :E} out of {bounds = }, check USB connection"
            raise ConnectionError(message)
        return value

    @frequency.setter
    def frequency(self, value: float) -> None:
        """ """
        try:
            in_bounds = self.min_frequency <= value <= self.max_frequency
        except TypeError:
            message = f"Expect frequency of {float}, got {value = } of {type(value)}."
            raise ValueError(message)
        else:
            if not in_bounds:
                bounds = f"[{self.min_frequency:.2E}, {self.max_frequency:.2E}]"
                raise ValueError(f"Frequency {value = :E} out of {bounds = }.")
        self._errorcheck(DLL.fnLMS_SetFrequency(self._handle, from_frequency(value)))

    @property
    def min_power(self) -> float:
        """ """
        return to_power(DLL.fnLMS_GetMinPwr(self._handle))

    @property
    def max_power(self) -> float:
        """ """
        return to_power(DLL.fnLMS_GetMaxPwr(self._handle))

    @property
    def power(self) -> float:
        """ """
        value = to_power(DLL.fnLMS_GetAbsPowerLevel(self._handle))
        in_bounds = self.min_power <= value <= self.max_power
        if not in_bounds:
            bounds = f"[{self.min_power:}, {self.max_power:}]"
            message = f"Power {value = } out of {bounds = }, check USB connection."
            raise ConnectionError(message)
        return value

    @power.setter
    def power(self, value: float) -> None:
        """ """
        try:
            in_bounds = self.min_power <= value <= self.max_power
        except TypeError:
            message = f"Expect power of {float}, got {value = } of {type(value)}."
            raise ValueError(message)
        else:
            if not in_bounds:
                bounds = f"[{self.min_power:}, {self.max_power:}]"
                raise ValueError(f"Power {value = } out of {bounds = }.")
        self._errorcheck(DLL.fnLMS_SetPowerLevel(self._handle, from_power(value)))
