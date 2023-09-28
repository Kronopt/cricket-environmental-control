import logging
import gpiozero

PWM_PIN = 12


class MockDevice:
    def __init__(self):
        self._value = 0.0

    @property
    def value(self) -> float:
        return self._value

    @value.setter
    def value(self, v: float):
        self._value = v


class FAN_5V_12V_PWM:
    """Standard Computer 5V-12V PWM Fan driver"""

    def __init__(self) -> None:
        """Initailizes fans in stopped state"""
        self._logger = logging.getLogger("drivers." + self.__class__.__name__)

        try:
            self._device = gpiozero.PWMOutputDevice(pin=PWM_PIN)
        except gpiozero.exc.BadPinFactory:
            self._logger.info(
                "'BadPinFactory' error. Not running on a Raspberry pi. Using mock..."
            )
            self._device = MockDevice()

    def set(self, percentage: float):
        """sets speed of fan to the given percentage (number between 0.0-1.0)"""
        self._device.value = percentage

    def get(self) -> float:
        """returns speed of fan (number between 0.0-1.0)"""
        return self._device.value
