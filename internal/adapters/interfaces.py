import abc


class Sensor(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def read(self) -> float:
        raise NotImplementedError


class Actuator(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def get(self) -> float:
        raise NotImplementedError

    @abc.abstractmethod
    def set(self, percent: float):
        raise NotImplementedError


class HostInfo(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def get(self) -> float:
        raise NotImplementedError
