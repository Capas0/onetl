from __future__ import annotations

import logging

from onetl.base import BaseFileLimit, PathProtocol
from onetl.impl import FrozenModel
from onetl.log import log_with_indent

log = logging.getLogger(__name__)


class FileLimit(BaseFileLimit, FrozenModel):
    """Limits the number of uploaded files

    Parameters
    ----------

    count_limit : int, default = 100

        Number of downloaded files at a time.

    Examples
    --------

    Create a FileLimit object and set the amount in it:

    .. code:: python

        limit = FileLimit(count_limit=1500)

    If you create a :obj:`onetl.core.file_downloader.file_downloader.FileDownloader` object without
    specifying the limit option, it will download with a limit of 100 files.
    """

    count_limit: int = 100

    _counter: int = 0

    def reset(self):
        self._counter = 0  # noqa: WPS601

    def stops_at(self, path: PathProtocol) -> bool:
        if self.is_reached:
            return True

        if path.is_dir():
            return False

        # directories count does not matter
        self._counter += 1  # noqa: WPS601
        return self.is_reached

    @property
    def is_reached(self) -> bool:
        return self._counter >= self.count_limit

    def log_options(self, indent: int = 0):
        for key, value in self.dict(by_alias=True).items():  # noqa: WPS528
            log_with_indent(f"{key} = {value!r}", indent=indent)
