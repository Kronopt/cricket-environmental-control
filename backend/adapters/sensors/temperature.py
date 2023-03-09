import random
from ..interfaces import Sensor


class Temperature(Sensor):
    def Read(self) -> float:
        return 0  # TODO driver


class MockTemperature(Sensor):
    def Read(self) -> float:
        return float(random.randrange(10, 30))
