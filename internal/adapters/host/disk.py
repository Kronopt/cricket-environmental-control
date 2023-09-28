import logging
import threading
import time
import warnings
import psutil
from .. import interfaces


class Disk(interfaces.HostInfo):
    """Disk usage"""

    def __init__(self):
        super().__init__()
        self._logger = logging.getLogger("adapters." + self.__class__.__name__)
        self._lock = threading.Lock()

        self.value = 0.0
        self._update()

        threading.Thread(target=self._update_every_second).start()

    def get(self) -> float:
        """Disk usage percentage"""
        with self._lock:
            return self.value

    def _update(self):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")

            with self._lock:
                self.value = psutil.disk_usage("/").percent

    def _update_every_second(self):
        while True:
            time.sleep(1)
            self._update()
