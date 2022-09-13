""" Instrument server """

from multiprocessing import Event, Process
import time
from typing import Any, Type

from labctrl import Instrument
from labctrl.errors import ConnectionError
from labctrl.logger import logger
import Pyro5.api as pyro
import Pyro5.errors

from qcore.instruments.anritsu import MS46522B
from qcore.instruments.quantum_machines import QM
from qcore.instruments.signalcore import SC5503B, SC5511A
from qcore.instruments.signalhound import SA124
from qcore.instruments.vaunix import LMS
from qcore.instruments.yokogawa import GS200

# key: Instrument class, value: list of ids of instruments qcrew has of the given class
INSTRUMENT_MAP = {
    MS46522B: ["VNA1"],
    QM: [None],
    SC5503B: [10002656],
    SC5511A: [10002657],
    SA124: [19184645, 20234154],
    LMS: list(range(25330, 25338)),
    GS200: ["90X823743", "91X336839"],
}


class ServerError(Exception):
    """ """


@pyro.expose
class Server:
    """ """

    NAME = "SERVER"
    PORT = 9090  # port to bind a remote server on, used to initialize Pyro Daemon
    URI = f"PYRO:{NAME}@localhost:{PORT}"  # unique resource identifier (URI)

    def __init__(self, daemon: pyro.Daemon, *instruments: Instrument) -> None:
        """ """
        self._instruments: tuple[Instrument] = instruments
        self._daemon = daemon
        self._services: list[pyro.URI] = []  # a list of remote resource URIs
        self._register()  # register instrument classes with pyro
        self._serve()

    @property
    def services(self) -> list[pyro.URI]:
        """ """
        return self._services.copy()

    def _register(self) -> None:
        """ """
        instrument_classes = {instrument.__class__ for instrument in self._instruments}
        for instrument_class in instrument_classes:
            pyro.expose(instrument_class)

    def _serve(self) -> None:
        """ """
        for instrument in self._instruments:
            uri = self._daemon.register(instrument, objectId=instrument.name)
            self._services.append(uri)
            logger.info(f"Served '{instrument}' remotely at '{uri}'.")

    def teardown(self) -> None:
        """ """
        for instrument in self._instruments:
            if instrument.status:
                instrument.disconnect()
        self._daemon.shutdown()


def serve(config: dict[Type[Instrument], list[Any]] = None, event=None) -> None:
    """ """
    logger.info("Setting up the instrument server...")

    config = INSTRUMENT_MAP if config is None else config
    instruments = []
    for cls, ids in config.items():
        for id in ids:
            name = f"{cls.__name__}#{id}"
            try:
                instrument = cls(id=id, name=name)
            except ConnectionError:
                logger.info(f"Failed to connect instrument '{name}'.")
            else:
                instruments.append(instrument)
                logger.info(f"Connected instrument '{name}'.")

    daemon = pyro.Daemon(port=Server.PORT)
    server = Server(daemon, *instruments)
    server_uri = daemon.register(server, objectId=Server.NAME)
    logger.info(f"Set up the instrument server at '{server_uri}'.")

    if event is not None:
        event.set()

    with daemon:
        daemon.requestLoop()


def link() -> tuple[pyro.Proxy, list[pyro.Proxy]]:
    """ """
    logger.info("Linking up to the instrument server...")

    server = pyro.Proxy(Server.URI)
    try:
        services = server.services
    except Pyro5.errors.CommunicationError:
        raise ServerError(f"No instrument server found at {Server.URI}.") from None
    else:
        instruments = [pyro.Proxy(uri) for uri in services]
        logger.info(f"Found {len(instruments)} instrument(s) on the server.")
        return server, instruments


def unlink(server: pyro.Proxy, *instruments: pyro.Proxy) -> None:
    """ """
    server._pyroRelease()
    for instrument in instruments:
        instrument._pyroRelease()
    logger.info("Released the link to the instrument server.")


def setup(config: dict[Type[Instrument], list[Any]] = None) -> None:
    """ """
    event = Event()
    server = Process(target=serve, args=(config, event))
    server.start()
    event.wait()
    time.sleep(0.1)  # to ensure server daemon request loop is entered


def teardown() -> None:
    """ """
    try:
        with pyro.Proxy(Server.URI) as server:
            server.teardown()
    except Pyro5.errors.CommunicationError:
        raise ServerError(f"No instrument server to teardown at {Server.URI}") from None
    else:
        logger.info(f"Tore down the instrument server at '{Server.URI}'.")
