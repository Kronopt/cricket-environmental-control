import logging
import random
import threading
import time
import gpiozero
from .. import interfaces


class MockTemperature:
    @property
    def temperature(self) -> float:
        return random.gauss(50, 2)


class Temperature(interfaces.HostInfo):
    """Temperature"""

    def __init__(self):
        super().__init__()
        self._logger = logging.getLogger("adapters." + self.__class__.__name__)
        self._lock = threading.Lock()

        try:
            self._cpu = gpiozero.CPUTemperature()
        except gpiozero.BadPinFactory:  # code probably not running on linux
            self._logger.info("can't initialize CPU temperature reader. Using mock...")
            self._cpu = MockTemperature()

        self.value = 0.0
        self._update()

        threading.Thread(target=self._update_every_second).start()

    def get(self) -> float:
        with self._lock:
            return self.value

    def _update(self):
        with self._lock:
            self.value = self._cpu.temperature

    def _update_every_second(self):
        while True:
            time.sleep(1)
            self._update()
