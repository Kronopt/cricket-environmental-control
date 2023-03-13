import abc


class Sensor(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def Read(self) -> float:
        raise NotImplementedError


class Actuator(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def Set(self, percent: float):
        raise NotImplementedError


class MachineInfo(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def Get(self) -> float:
        raise NotImplementedError
