import configparser
from ..interfaces import Actuator
from ...drivers.fan_12v_3pin import FAN_12V_3PIN


class Fan(Actuator):
    """Standard Computer 12V 3PIN Fan"""

    def __init__(self, configs: configparser.ConfigParser):
        super().__init__()
        self.set(configs["fan"].getfloat("start_percentage"))
        self.driver = FAN_12V_3PIN()

    def set(self, percent: float):
        pass  # TODO driver


class MockFan(Actuator):
    def set(self, percent: float):
        pass
