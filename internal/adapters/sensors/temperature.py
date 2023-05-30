import random
from ..interfaces import Sensor
from ...drivers.sht35 import SHT35


class Temperature(Sensor):
    """Temperature Sensor"""

    def __init__(self):
        super().__init__()
        self.driver = SHT35()

    def read(self) -> float:
        return 0  # TODO driver


class MockTemperature(Sensor):
    def read(self) -> float:
        return float(random.randrange(10, 30))
