import random
from ..interfaces import Sensor
from ...drivers.mq_137 import MQ137


class NH3(Sensor):
    """Ammonia (NH3) Gas Sensor"""

    def __init__(self):
        super().__init__()
        self.driver = MQ137()

    def read(self) -> float:
        return 0  # TODO driver


class MockNH3(Sensor):
    def read(self) -> float:
        return float(random.randrange(10, 100))
