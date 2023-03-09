import configparser
from ..interfaces import Actuator
from ...drivers.fan_12v_3pin import FAN_12V_3PIN


class Fan(Actuator):
    """Standard Computer 12V 3PIN Fan"""

    def __init__(self, configs: configparser.ConfigParser):
        super().__init__()
        self.driver = FAN_12V_3PIN()

        self.Set(configs["fan"].getfloat("start_percentage"))

    def Set(self, percent: float):
        pass  # TODO driver


class MockFan(Actuator):
    def Set(self, percent: float):
        pass
