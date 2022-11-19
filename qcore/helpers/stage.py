"""
This module contains utilities for staging Resources prior to running experiments.

Either Resource objects or .yml config files containing Resource objects can be staged.
The Stage can link up to the Server to retrieve remotely served Resources.
"""

from __future__ import annotations

from pathlib import Path
from typing import Union

import Pyro5.api as pyro

from qcore.helpers.logger import logger
from qcore.helpers import server
import qcore.helpers.yamlizer as yml
from qcore.resource import Resource

# these imports are needed for yamlizing to work
from qcore.elements import *
from qcore.instruments import *
from qcore.pulses import *


class Stage:
    """ """

    def __init__(
        self,
        *sources: Union[Path, Resource],
        configpath: Path = None,
        remote: bool = False,
    ) -> None:
        """
        sources (Path | Resource): Resource objects or Path to .yml config files containing Resource objects to be staged
        configpath (Path): if provided, staged Resources without associated .yml config files will be saved to this configpath. If configpath doesn't already exist, it will be created.
        remote (bool): whether or not this stage stages remote Resources by linking up to the remote Server
        """
        self._configpath = configpath
        if configpath is not None:
            configfolder = self._configpath.parent
            configfolder.mkdir(exist_ok=True)
            self._configpath.touch(exist_ok=True)

        # _config is a dict with key: configpath, value: list[Resource] used for saving
        self._config: dict[Path, list[Resource]] = {self._configpath: []}

        # _resources is a dict with key: resource name and
        # value: Resource object for local and Resource proxy for remote resources
        self._resources: dict[str, Union[Resource, pyro.Proxy]] = {}

        if sources:
            self.add(*sources)

        self._server, self._proxies = None, []  # will be updated by _link()
        if remote:
            self._link()

        logger.debug(f"Set up a Stage with {remote = }")

    def _link(self) -> None:
        """ """
        self._server, self._proxies = server.link()
        for resource_proxy in self._proxies:
            name = resource_proxy.name
            self._resources[name] = resource_proxy
            logger.info(f"Staged remote resource with {name = }.")

    def __enter__(self) -> Stage:
        """ """
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback) -> None:
        """ """
        self.teardown()

    def teardown(self) -> None:
        """ """
        self.save()
        if self._server is not None:
            server.unlink(self._server, *self._proxies)
        logger.debug("Tore down the Stage gracefully!")

    def save(self) -> None:
        """ """
        for configpath, resources in self._config.items():
            if resources and configpath is not None:
                logger.debug(f"Saving state of staged resources to their configs...")
                yml.dump(configpath, *resources)

    @property
    def resources(self) -> set[str]:
        """ """
        return set(self._resources.keys())

    def add(self, *sources: Path | Resource) -> None:
        """ """
        for source in sources:
            if isinstance(source, Resource):  # 'source' is a Resource object
                self._add_resource(source, self._configpath)
            else:  # 'source' is a Path to a yml config file containing Resource objects
                resources = yml.load(source)
                for resource in resources:
                    self._add_resource(resource, source)

    def _add_resource(self, resource: Resource, configpath: Path) -> None:
        """ """
        name = resource.name
        if name in self._resources:
            message = (
                f"Unable to stage Resource '{resource}' with {name = } as another "
                f"resource with the same name exists on this stage."
            )
            logger.warning(message)
        else:
            self._resources[resource.name] = resource
            if configpath in self._config:
                self._config[configpath].append(resource)
            else:
                self._config[configpath] = [resource]
            logger.info(f"Staged {resource = }.")

    def remove(self, *names: str) -> None:
        """ """
        for name in names:
            if name in self._resources:
                resource = self._resources[name]
                if resource in self._proxies:  # resource is a Proxy object
                    server.release(resource)
                else:  # resource is a Resource object
                    for config in self._config.values():  # don't save Resource to yml
                        if resource in config:
                            config.remove(resource)
                del self._resources[name]
                logger.info(f"Unstaged {resource = }.")
            else:
                logger.warning(f"Resource with '{name = }' does not exist on Stage.")

    def get(self, *names: str) -> list[Resource]:
        """ """
        resources = []
        for name in names:
            if name in self._resources:
                resources.append(self._resources[name])
            else:
                logger.warning(f"Resource with {name = } does not exist on this stage.")
        return resources
