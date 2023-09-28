import logging
import threading
from .. import interfaces
from ...drivers import fan_5v_12v_pwm
from ...services import configurations


class Fan(interfaces.ActuatorPercentage):
    """Standard Computer 5v-12V PWM Fan"""

    def __init__(self, configs: configurations.Configurations):
        super().__init__()
        self._logger = logging.getLogger("adapters." + self.__class__.__name__)
        self._driver = fan_5v_12v_pwm.FAN_5V_12V_PWM()
        self._lock = threading.Lock()

        self.value = self.get()
        self.set(configs["fan"].getfloat("start_percentage"))

    def get(self) -> float:
        with self._lock:
            return self._driver.get() * 100.0

    def set(self, percent: float):
        with self._lock:
            if percent != self.value:
                self._logger.debug(f"setting fan speed to {percent}")
                self.value = percent
                self._driver.set(percent / 100.0)
