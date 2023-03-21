import random
import psutil
from ..interfaces import HostInfo


class CPU(HostInfo):
    """CPU usage"""

    def __init__(self):
        super().__init__()
        self.get()  # the response of the first call to psutil.cpu_percent is supposed to be ignored

    def get(self) -> float:
        """CPU usage percentage"""
        return psutil.cpu_percent()


class MockCPU(HostInfo):
    def get(self) -> float:
        return float(random.randrange(1, 100))
