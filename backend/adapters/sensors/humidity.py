import random
from ..interfaces import Sensor


class Humidity(Sensor):
    def Read(self) -> float:
        return 0  # TODO driver


class MockHumidity(Sensor):
    def Read(self) -> float:
        return float(random.randrange(0, 100))
