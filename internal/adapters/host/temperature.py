import random
from collections import namedtuple
import gpiozero
from ..interfaces import HostInfo


class Temperature(HostInfo):
    """Temperature"""

    def __init__(self):
        super().__init__()

        try:
            self.cpu = gpiozero.CPUTemperature()

        except gpiozero.BadPinFactory:  # code probably not running on linux
            self.cpu = namedtuple("cpu", "temperature")(-274)

    def get(self) -> float:
        "Temperature in celsius (-274 == no temperature data)"
        return self.cpu.temperature


class MockTemperature(HostInfo):
    def get(self) -> float:
        return float(random.randrange(30, 50))
