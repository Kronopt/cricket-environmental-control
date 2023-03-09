from ..interfaces import Actuator


class Fan(Actuator):
    def Set(self, percent: float):
        pass  # TODO driver


class MockFan(Actuator):
    def Set(self, percent: float):
        pass
