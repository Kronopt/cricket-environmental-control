import random
from ..interfaces import Sensor
from ...drivers.scd40_d_r2 import SCD40_D_R2


class Humidity(Sensor):
    """Humidity Sensor"""

    def __init__(self):
        super().__init__()
        self.driver = SCD40_D_R2()

    def read(self) -> float:
        return 0  # TODO driver


class MockHumidity(Sensor):
    def read(self) -> float:
        return float(random.randrange(0, 100))
