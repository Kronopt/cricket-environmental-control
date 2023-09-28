import logging
import threading
import time
import psutil
from .. import interfaces


class RAM(interfaces.HostInfo):
    """RAM usage"""

    def __init__(self):
        super().__init__()
        self._logger = logging.getLogger("adapters." + self.__class__.__name__)
        self._lock = threading.Lock()

        self.value = 0.0
        self._update()

        threading.Thread(target=self._update_every_second).start()

    def get(self) -> float:
        "RAM usage percentage"
        with self._lock:
            return self.value

    def _update(self):
        with self._lock:
            self.value = psutil.virtual_memory().percent

    def _update_every_second(self):
        while True:
            time.sleep(1)
            self._update()
