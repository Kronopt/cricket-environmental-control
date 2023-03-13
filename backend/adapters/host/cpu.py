import psutil
import random
from ..interfaces import MachineInfo


class CPU(MachineInfo):
    """CPU usage"""

    def __init__(self):
        super().__init__()
        self.Get()  # the response of the first call to psutil.cpu_percent is supposed to be ignored

    def Get(self) -> float:
        return psutil.cpu_percent()


class MockCPU(MachineInfo):
    def Get(self) -> float:
        return float(random.randrange(1, 100))
