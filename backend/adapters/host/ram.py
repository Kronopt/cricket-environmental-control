import psutil
import random
from ..interfaces import MachineInfo


class RAM(MachineInfo):
    """RAM usage"""

    def Get(self) -> float:
        return psutil.virtual_memory().percent


class MockRAM(MachineInfo):
    def Get(self) -> float:
        return float(random.randrange(1, 100))
