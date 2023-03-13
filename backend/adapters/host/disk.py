import psutil
import random
from ..interfaces import MachineInfo


class Disk(MachineInfo):
    """Disk usage"""

    def Get(self) -> float:
        return psutil.disk_usage("/").percent


class MockDisk(MachineInfo):
    def Get(self) -> float:
        return float(random.randrange(1, 100))
