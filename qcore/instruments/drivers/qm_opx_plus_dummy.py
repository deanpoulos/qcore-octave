from qcore.instruments.instrument import Instrument
from qcore.variables.parameter import Parameter


class OPXPlus(Instrument):
    """Dummy instrument containing relevant information for connecting to an OPX+.

    The `id` should be set to the IP address of the OPX+.
    """

    cluster_name: str = Parameter()

    def __init__(self, cluster_name: str, id: str, **parameters):
        self._cluster_name = cluster_name
        super().__init__(id, **parameters)

    @property
    def status(self) -> bool:
        return True

    @cluster_name.getter
    def cluster_name(self) -> str:
        """ """
        return self._cluster_name

    @cluster_name.setter
    def cluster_name(self, value: str) -> None:
        """ """
        self._cluster_name = value

    def connect(self) -> None:
        pass

    def disconnect(self) -> None:
        pass
