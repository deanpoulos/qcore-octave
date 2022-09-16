""" Instrument server """

from typing import Type

import Pyro5.api as pyro
import Pyro5.errors

from qcore.instruments.instrument import Instrument, ConnectionError
from qcore.instruments.config import InstrumentConfig
from qcore.resource import Resource


class ServerError(Exception):
    """ """

@pyro.expose
class Server:
    """ """

    NAME = "SERVER"
    PORT = 9090  # port to bind a remote server on, used to initialize Pyro Daemon
    URI = f"PYRO:{NAME}@localhost:{PORT}"  # unique resource identifier (URI)

    def __init__(self, config: dict[Type[Instrument], list[str]] = None) -> None:
        """ """
        config = InstrumentConfig() if config is None else config
        self._instruments: list[Instrument] = self._connect(config)
        self._daemon = None  # will be set by _serve()
        self._services: list[pyro.URI] = []  # list of instrument URIs, set by _serve()

    @property
    def services(self) -> list[pyro.URI]:
        """ """
        return self._services.copy()

    def serve(self) -> None:
        """blocking function"""
        instrument_classes = {instrument.__class__ for instrument in self._instruments}
        instrument_classes |= {Resource, Instrument}
        for instrument_class in instrument_classes:
            pyro.expose(instrument_class)

        self._daemon = pyro.Daemon(port=Server.PORT)
        for instrument in self._instruments:
            uri = self._daemon.register(instrument, objectId=instrument.name)
            self._services.append(uri)
        self._daemon.register(self, objectId=Server.NAME)

        with self._daemon:
            self._daemon.requestLoop()

    def teardown(self) -> None:
        """ """
        self._disconnect()
        if self._daemon is not None:
            with self._daemon:
                self._daemon.shutdown()

    def _connect(self, config: dict[Type[Instrument], list[str]]) -> list[Instrument]:
        """ """
        instruments = []
        for cls, ids in config.items():
            for id in ids:
                name = f"{cls.__name__}#{id}"
                try:
                    instrument = cls(id=id, name=name)
                except ConnectionError:
                    pass
                else:
                    instruments.append(instrument)
        return instruments

    def _disconnect(self) -> None:
        """ """
        for instrument in self._instruments:
            if instrument.status:
                instrument.disconnect()


class Client:
    """ """

    def link(self) -> tuple[pyro.Proxy, list[pyro.Proxy]]:
        """ """
        print("Linking up to the instrument server...")
        server = pyro.Proxy(Server.URI)
        try:
            services = server.services
        except Pyro5.errors.CommunicationError:
            raise ServerError(f"No instrument server found at {Server.URI}.") from None
        else:
            instruments = [pyro.Proxy(uri) for uri in services]
            print(f"Found {len(instruments)} instrument(s) on the server.")
            return (server, instruments)

    def unlink(self, server: pyro.Proxy, *instruments: pyro.Proxy) -> None:
        """ """
        server._pyroRelease()
        for instrument in instruments:
            instrument._pyroRelease()
        print("Released the link to the instrument server.")
