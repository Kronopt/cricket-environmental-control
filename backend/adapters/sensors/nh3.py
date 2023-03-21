import random
from ..interfaces import Sensor
from ...drivers.sen_17053 import SEN17053


class NH3(Sensor):
    """Ammonia (NH3) Gas Sensor"""

    def __init__(self):
        super().__init__()
        self.driver = SEN17053()

    def read(self) -> float:
        return 0  # TODO driver


class MockNH3(Sensor):
    def read(self) -> float:
        return float(random.randrange(10, 100))
