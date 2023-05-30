import random
import psutil
from ..interfaces import HostInfo


class RAM(HostInfo):
    """RAM usage"""

    def get(self) -> float:
        "RAM usage percentage"
        return psutil.virtual_memory().percent


class MockRAM(HostInfo):
    def get(self) -> float:
        return float(random.randrange(1, 100))