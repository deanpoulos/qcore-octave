from qcore.instruments.instrument import Instrument
from qcore.variables.parameter import Parameter


class Octave(Instrument):
    """Dummy instrument containing relevant information for connecting to an Octave.

    The `id` should be configured to the IP address of the Octave if it is internally
    configured, or the main OPX+ IP if externally configured.
    """

    settings: dict = Parameter()
    """ 
    Raw dictionary which is indexed by the `octave_name` in the regular QM configruation file: 
    https://docs.quantum-machines.co/1.1.6/qm-qua-sdk/docs/Guides/octave/#configuring-the-octave
    """
    calibration_db_path: str = Parameter()
    """ Parent folder of the calibration_db.json file. """
    port: int = Parameter()
    """ 
    80 for internally connected Octave, otherwise 11XXX where XXX are the last three digits
    of the octave IP address.
    """

    def __init__(
        self,
        settings: dict,
        calibration_db_path: str,
        port: int,
        id: str,
        **parameters
    ):
        self._settings = settings
        self._calibration_db_path = calibration_db_path
        self._port = port
        super().__init__(id, **parameters)

    @property
    def status(self) -> bool:
        return True

    @calibration_db_path.setter
    def calibration_db_path(self, value: str) -> None:
        """ """
        self.calibration_db_path = value

    @calibration_db_path.getter
    def calibration_db_path(self) -> str:
        """ """
        return self._calibration_db_path

    @settings.getter
    def settings(self) -> dict:
        """ """
        return self._settings

    @settings.setter
    def settings(self, value: dict) -> None:
        """ """
        self._settings = value

    @port.getter
    def port(self) -> int:
        """ """
        return self._port

    @port.setter
    def port(self, value: int) -> None:
        """ """
        self._port = value

    def connect(self) -> None:
        pass

    def disconnect(self) -> None:
        pass
