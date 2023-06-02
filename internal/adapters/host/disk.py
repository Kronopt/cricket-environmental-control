import random
import psutil
from ..interfaces import HostInfo


class Disk(HostInfo):
    """Disk usage"""

    def __init__(self):
        super().__init__()

    def get(self) -> float:
        """Disk usage percentage"""
        return psutil.disk_usage("/").percent


class MockDisk(HostInfo):
    def get(self) -> float:
        return float(random.randrange(1, 100))
