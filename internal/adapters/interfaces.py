import abc


class Sensor(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def read(self) -> float:
        raise NotImplementedError


class ActuatorPercentage(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def get(self) -> float:
        raise NotImplementedError

    @abc.abstractmethod
    def set(self, percent: float):
        raise NotImplementedError


class ActuatorOnOff(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def on(self):
        raise NotImplementedError

    @abc.abstractmethod
    def off(self):
        raise NotImplementedError

    @abc.abstractmethod
    def is_on(self) -> bool:
        raise NotImplementedError


class HostInfo(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def get(self) -> float:
        raise NotImplementedError
