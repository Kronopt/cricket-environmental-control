import configparser
from ..interfaces import Actuator
from ...drivers.electrovalve_12v import Electrovalve_12V


class Electrovalve(Actuator):
    """Standard 12V Electrovalve"""

    def __init__(self, configs: configparser.ConfigParser):
        super().__init__()
        self.driver = Electrovalve_12V()

        self.set(configs["electrovalve"].getfloat("start_percentage"))

    def set(self, percent: float):
        pass  # TODO driver


class MockElectrovalve(Actuator):
    def set(self, percent: float):
        pass
