""" Instrument server """

from typing import Type

import Pyro5.api as pyro
import Pyro5.errors as pyro_errors

from qcore.helpers.logger import logger
from qcore.instruments.instrument import Instrument
from qcore.resource import Resource


@pyro.expose
class Server:
    """ """

    NAME = "SERVER"
    PORT = 9090  # port to bind a remote server on, used to initialize Pyro Daemon
    URI = f"PYRO:{NAME}@localhost:{PORT}"  # unique resource identifier (URI)

    def __init__(self, config: dict[Type[Instrument], list[str]]) -> None:
        """ """
        self._instruments: list[Instrument] = self._connect(config)
        self._daemon = pyro.Daemon(port=Server.PORT)
        self._services: list[pyro.URI] = []  # list of instrument URIs, set by _serve()

    def _connect(self, config: dict[Type[Instrument], list[str]]) -> list[Instrument]:
        """ """
        instruments = []
        for cls, ids in config.items():
            for id in ids:
                instrument = cls(id=id, name=f"{cls.__name__}#{id}")
                instruments.append(instrument)
        return instruments

    def serve(self) -> None:
        """blocking function"""
        self._expose()
        for instrument in self._instruments:
            uri = self._daemon.register(instrument, objectId=instrument.name)
            self._services.append(uri)
        self._daemon.register(self, objectId=Server.NAME)
        with self._daemon:
            self._daemon.requestLoop()

    def _expose(self) -> None:
        """ """
        instrument_classes = {instrument.__class__ for instrument in self._instruments}
        instrument_classes |= {Resource, Instrument}
        for instrument_class in instrument_classes:
            pyro.expose(instrument_class)

    @property
    def services(self) -> list[pyro.URI]:
        """ """
        return self._services.copy()

    def teardown(self) -> None:
        """ """
        self._disconnect()
        with self._daemon:
            self._daemon.shutdown()

    def _disconnect(self) -> None:
        """ """
        for instrument in self._instruments:
            if instrument.status:
                instrument.disconnect()


def link() -> tuple[pyro.Proxy, list[pyro.Proxy]]:
    """ """
    server = pyro.Proxy(Server.URI)
    try:
        services = server.services
    except pyro_errors.CommunicationError:  # no remote server found
        logger.warning(f"Remote server requested but not found at {Server.URI}")
        return (None, [])
    else:
        instruments = [pyro.Proxy(uri) for uri in services]
        return (server, instruments)


def unlink(server: pyro.Proxy, *instruments: pyro.Proxy) -> None:
    """ """
    server._pyroRelease()
    for instrument in instruments:
        instrument._pyroRelease()
