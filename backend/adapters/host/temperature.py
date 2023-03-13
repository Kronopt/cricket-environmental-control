import functools
import random
import psutil
from ..interfaces import HostInfo


class Temperature(HostInfo):
    """Temperature"""

    def Get(self) -> float:
        "Temperature in celsius (-274 == no temperature data)"
        if hasattr(psutil, "sensors_temperatures"):
            all_temperatures = psutil.sensors_temperatures()

            if "coretemp" in all_temperatures:
                cpu_temperatures = all_temperatures["coretemp"]
                return functools.reduce(
                    lambda x, y: x + y, cpu_temperatures.current
                ) / len(cpu_temperatures)

        return -274.0


class MockTemperature(HostInfo):
    def Get(self) -> float:
        return float(random.randrange(30, 50))
