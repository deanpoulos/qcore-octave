""" """

from typing import Callable

import numpy as np

from qm._results_01 import MultipleNamedJobResult, SingleNamedJobResult
from qm.QmJob import JobResults


class QMResultFetcher:
    """ """

    def __init__(self, handle: JobResults) -> None:
        """ """
        self._handle: JobResults = handle

        self._count: int = 0  # current number of results fetched
        self._last_count: int = -1  # only used in live fetch mode to fetch batches

        # set result specification for faster live fetching
        self._spec: dict[str, Callable] = {"single": {}, "multiple": {}}
        for tag, result in self._handle:
            if isinstance(result, SingleNamedJobResult):
                self._spec["single"][tag] = self._fetch_single
            elif isinstance(result, MultipleNamedJobResult):
                spec = self._spec["multiple"]
                is_live = self._handle.is_processing()  # we are not live fetching
                spec[tag] = self._fetch_batch if is_live else self._fetch_multiple

    @property
    def is_done_fetching(self) -> bool:
        """flag to indicate job fetch status, True if all results have been fetched"""
        return self._count == self._last_count and not self._handle.is_processing()

    @property
    def counts(self) -> tuple[int, int]:
        """return (current count, previous count) of fetched results during live fetching"""
        return (self._count, self._last_count)

    def fetch(self) -> dict[str, np.ndarray]:
        """ """
        self._last_count = self._count
        self._count = self._count_results()

        if self.is_done_fetching:
            return {}

        specs = self._spec.values()
        return {tag: fn(tag) for spec in specs for tag, fn in spec.items()}

    def _count_results(self):
        """ """
        return min(len(self._handle.get(tag)) for tag in self._spec["multiple"])

    def _fetch_single(self, tag):
        """ """
        return self._handle.get(tag).fetch_all(flat_struct=True)

    def _fetch_batch(self, tag):
        """ """
        slc = slice(self._last_count, self._count)
        return self._handle.get(tag).fetch(slc, flat_struct=True)

    def _fetch_multiple(self, tag):
        """ """
        return self._handle.get(tag).fetch_all(flat_struct=True)
