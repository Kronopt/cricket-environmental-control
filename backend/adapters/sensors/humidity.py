import random
from ..interfaces import Sensor
from ...drivers.sht35 import SHT35


class Humidity(Sensor):
    """Humidity Sensor"""

    def __init__(self):
        super().__init__()
        self.driver = SHT35()

    def Read(self) -> float:
        return 0  # TODO driver


class MockHumidity(Sensor):
    def Read(self) -> float:
        return float(random.randrange(0, 100))
