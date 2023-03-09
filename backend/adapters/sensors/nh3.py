import random
from ..interfaces import Sensor


class NH3(Sensor):
    def Read(self) -> float:
        return 0  # TODO driver


class MockNH3(Sensor):
    def Read(self) -> float:
        return float(random.randrange(10, 100))
