import logging
import threading
import time
from .. import interfaces
from ...drivers import scd40_d_r2


class Humidity(interfaces.Sensor):
    """Humidity Sensor"""

    def __init__(self):
        super().__init__()
        self._logger = logging.getLogger("adapters." + self.__class__.__name__)
        self._lock = threading.Lock()
        self._driver = scd40_d_r2.SCD40_D_R2()

        self.value = 0.0
        self._update()

        threading.Thread(target=self._update_every_second).start()

    def read(self) -> float:
        with self._lock:
            return self.value

    def _update(self):
        with self._lock:
            self.value = self._driver.humidity()

    def _update_every_second(self):
        while True:
            time.sleep(1)
            self._update()
