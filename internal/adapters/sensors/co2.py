import random
from ..interfaces import Sensor
from ...drivers.scd40_d_r2 import SCD40_D_R2


class CO2(Sensor):
    """CO2 Sensor"""

    def __init__(self):
        super().__init__()
        self.driver = SCD40_D_R2()

    def read(self) -> float:
        return self.driver.co2()


class MockCO2(Sensor):
    def read(self) -> float:
        return float(random.randrange(10, 100))
