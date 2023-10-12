import logging
import threading
import time
from .. import interfaces
from ...drivers import electrovalve_12v
from ...services import configurations


class Electrovalve(interfaces.ActuatorOnOff):
    """Standard 12V Electrovalve"""

    def __init__(self, configs: configurations.Configurations):
        super().__init__()
        self._logger = logging.getLogger("adapters." + self.__class__.__name__)
        self._configs = configs
        self._driver = electrovalve_12v.Electrovalve_12V()

        self._pump_lock = threading.Lock()  # for actual state of pumps

        self._enabled_lock = threading.Lock()  # for adapter abstraction of pumps state
        self._enabled = False

        starts_open = configs["electrovalve"].getboolean("start_open")
        if starts_open:
            self.on()
        else:
            self.off()

        self.value = self.is_on()

        threading.Thread(target=self._burst).start()

    def _open(self):
        if not self.is_on():
            self._logger.debug("turning valve on")
            with self._pump_lock:
                self._driver.open()
                self.value = True

    def on(self):
        """enables valve"""
        with self._enabled_lock:
            self._enabled = True

    def _close(self):
        if self.is_on():
            self._logger.debug("turning valve off")
            with self._pump_lock:
                self._driver.close()
                self.value = False

    def off(self):
        """disables valve"""
        with self._enabled_lock:
            self._enabled = False

    def is_on(self) -> bool:
        """is valve currently open"""
        with self._pump_lock:
            return self._driver.is_opened()

    def _burst(self):
        """opens pumps in burst"""
        self._burst_cycle_beginning = 0.0

        while True:
            time.sleep(1)

            with self._enabled_lock:
                if not self._enabled:
                    self._burst_cycle_beginning = 0.0
                    self._close()
                    continue

            if self._burst_cycle_beginning == 0.0:
                self._reset_burst_cycle()

            opened_secs = self._configs["electrovalve"].getint("burst_opened_for_secs")
            every_secs = self._configs["electrovalve"].getint("burst_every_secs")

            current_time = time.time()
            if current_time >= self._burst_cycle_beginning + opened_secs:
                self._close()

            if current_time >= self._burst_cycle_beginning + every_secs:
                self._reset_burst_cycle()

    def _reset_burst_cycle(self):
        self._burst_cycle_beginning = time.time()
        self._open()
