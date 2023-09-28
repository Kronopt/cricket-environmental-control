import logging
import time
from . import configurations
from ..adapters import interfaces


class ActuatorsController:
    """Handles fans and electrovalve based on sensors inputs"""

    def __init__(
        self,
        configs: configurations.Configurations,
        electrovalves: interfaces.ActuatorOnOff,
        fans: interfaces.ActuatorPercentage,
        sensor_co2: interfaces.Sensor,
        sensor_humidity: interfaces.Sensor,
        sensor_nh3: interfaces.Sensor,
        sensor_temperature: interfaces.Sensor,
    ):
        self._logger = logging.getLogger("services." + self.__class__.__name__)
        self._configs = configs
        self._electrovalves = electrovalves
        self._fans = fans
        self._sensor_co2 = sensor_co2
        self._sensor_humidity = sensor_humidity
        self._sensor_nh3 = sensor_nh3
        self._sensor_temperature = sensor_temperature

        self.fan_turned_off = 0.0
        self.fan_1_third_speed = 33.33
        self.fan_2_third_speed = 66.66
        self.fan_full_speed = 100.0

    def handle_fans(self):
        """calculates fan speed for all sensors and target speed, always keeping the fastest speed"""
        fan_speed = 0.0

        if (speed := self._fans_temperature_speed()) > fan_speed:
            fan_speed = speed

        if (speed := self._fans_co2_speed()) > fan_speed:
            fan_speed = speed

        if (speed := self._fans_nh3_speed()) > fan_speed:
            fan_speed = speed

        self._fans.set(fan_speed)

    def handle_electrovalves(self):
        """basic on/off if humidity is above/below target humidity"""
        current_humidity = self._sensor_humidity.read()
        target_humidity = self._configs["electrovalve"].getint("humidity_target")

        if current_humidity < target_humidity:
            self._electrovalves.on()
        else:
            self._electrovalves.off()

    def start(self):
        """
        starts all actuators controllers.
        analyses sensor data every 5 seconds and determines what to do to the actuators
        """
        self._logger.info("starting actuators controllers...")

        while True:
            time.sleep(5)

            self.handle_fans()
            self.handle_electrovalves()

    def _fans_temperature_speed(self) -> float:
        target_temperature_1_third_speed = self._configs["fan"].getint(
            "temperature_1_third_speed"
        )
        target_temperature_2_third_speed = self._configs["fan"].getint(
            "temperature_2_third_speed"
        )
        target_temperature_full_speed = self._configs["fan"].getint(
            "temperature_full_speed"
        )
        current_temperature = self._sensor_temperature.read()

        if current_temperature >= target_temperature_full_speed:
            return self.fan_full_speed

        if current_temperature >= target_temperature_2_third_speed:
            return self.fan_2_third_speed

        if current_temperature >= target_temperature_1_third_speed:
            return self.fan_1_third_speed

        return self.fan_turned_off

    def _fans_co2_speed(self) -> float:
        target_co2_1_third_speed = self._configs["fan"].getint("co2_1_third_speed")
        target_co2_2_third_speed = self._configs["fan"].getint("co2_2_third_speed")
        target_co2_full_speed = self._configs["fan"].getint("co2_full_speed")
        current_co2 = self._sensor_co2.read()

        if current_co2 >= target_co2_full_speed:
            return self.fan_full_speed

        if current_co2 >= target_co2_2_third_speed:
            return self.fan_2_third_speed

        if current_co2 >= target_co2_1_third_speed:
            return self.fan_1_third_speed

        return self.fan_turned_off

    def _fans_nh3_speed(self) -> float:
        target_nh3_1_third_speed = self._configs["fan"].getint("nh3_1_third_speed")
        target_nh3_2_third_speed = self._configs["fan"].getint("nh3_2_third_speed")
        target_nh3_full_speed = self._configs["fan"].getint("nh3_full_speed")
        current_nh3 = self._sensor_nh3.read()

        if current_nh3 >= target_nh3_full_speed:
            return self.fan_full_speed

        if current_nh3 >= target_nh3_2_third_speed:
            return self.fan_2_third_speed

        if current_nh3 >= target_nh3_1_third_speed:
            return self.fan_1_third_speed

        return self.fan_turned_off
