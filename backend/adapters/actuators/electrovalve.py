from ..interfaces import Actuator


class Electrovalve(Actuator):
    def Set(self, percent: float):
        pass  # TODO driver


class MockElectrovalve(Actuator):
    def Set(self, percent: float):
        pass
