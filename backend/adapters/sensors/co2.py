import random
from ..interfaces import Sensor


class CO2(Sensor):
    def Read(self) -> float:
        return 0  # TODO driver


class MockCO2(Sensor):
    def Read(self) -> float:
        return float(random.randrange(10, 100))
