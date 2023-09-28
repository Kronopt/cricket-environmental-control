import logging


class MockGPIO:
    BCM = None
    OUT = None
    LOW = None
    HIGH = None
    is_mock = True

    def setmode(self, *args, **kwargs):
        pass

    def setup(self, *args, **kwargs):
        pass

    def output(self, *args, **kwargs):
        pass

    def input(self, *args, **kwargs):
        return True


try:
    import RPi.GPIO as GPIO
except ModuleNotFoundError:
    GPIO = MockGPIO()


RELAY_PIN = 18


class Electrovalve_12V:
    """Standard 12V Electrovalve driver (connected to a relay)"""

    def __init__(self) -> None:
        self._logger = logging.getLogger("drivers." + self.__class__.__name__)

        if hasattr(GPIO, "is_mock"):
            self._logger.info("'RPi.GPIO' not available to import. Using mock...")

        GPIO.setmode(GPIO.BCM)
        GPIO.setup(RELAY_PIN, GPIO.OUT)
        GPIO.output(RELAY_PIN, GPIO.LOW)  # start closed

        self._opened = False

    def open(self):
        """opens valve"""
        self._opened = True
        if not GPIO.input(RELAY_PIN):
            GPIO.output(RELAY_PIN, GPIO.HIGH)

    def close(self):
        """closes valve"""
        self._opened = False
        if GPIO.input(RELAY_PIN):
            GPIO.output(RELAY_PIN, GPIO.LOW)

    def is_opened(self) -> bool:
        return self._opened
