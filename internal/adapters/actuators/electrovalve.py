import logging
import threading
from .. import interfaces
from ...drivers import electrovalve_12v
from ...services import configurations


class Electrovalve(interfaces.ActuatorOnOff):
    """Standard 12V Electrovalve"""

    def __init__(self, configs: configurations.Configurations):
        super().__init__()
        self._logger = logging.getLogger("adapters." + self.__class__.__name__)
        self._driver = electrovalve_12v.Electrovalve_12V()
        self._lock = threading.Lock()

        starts_open = configs["electrovalve"].getboolean("start_open")
        if starts_open:
            self.on()
        else:
            self.off()

        self.value = self.is_on()

    def on(self):
        if not self.is_on():
            self._logger.debug("turning valve on")
            with self._lock:
                self._driver.open()
                self.value = True

    def off(self):
        if self.is_on():
            self._logger.debug("turning valve off")
            with self._lock:
                self._driver.close()
                self.value = False

    def is_on(self) -> bool:
        with self._lock:
            return self._driver.is_opened()
