import concurrent.futures
import logging
import time
from datetime import datetime
from typing import TYPE_CHECKING
from . import configurations
from .dates import Dates, DateCycleTarget
from ..adapters import interfaces

if TYPE_CHECKING:
    from .frontend import HumiditySettings


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
        self._humidity_settings_data: "HumiditySettings"  # set by frontend

        self.fan_turned_off = 0.0
        self.fan_1_third_speed = 33.33
        self.fan_2_third_speed = 66.66
        self.fan_full_speed = 100.0

    def handle_fans(self):
        """calculates fan speed for all sensors and target speed, always keeping the fastest speed"""
        while True:
            time.sleep(5)

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
        while True:
            time.sleep(5)

            current_humidity = self._sensor_humidity.read()
            target_humidity = self._configs["electrovalve"].getfloat("humidity_target")

            if current_humidity < target_humidity:
                self._electrovalves.on()
            else:
                self._electrovalves.off()

    def handle_humidity_cycles(self):
        """
        increments target humidity based on defined date intervals
        assumes all humidity cycle date intervals end in the future
        """
        while True:
            time.sleep(60 * 60 * 12)  # half a day

            now = datetime.now()
            cycles = self._configs["electrovalve"].get("humidity_cycle")
            target = self._configs["electrovalve"].getfloat("humidity_target")
            cycle_targets = self._configs["electrovalve"].get("humidity_cycle_targets")

            date_intervals = Dates(cycles)
            date_targets = DateCycleTarget(cycle_targets)
            for date_from, date_to in date_intervals:
                target_for_date_interval = date_targets.humidity_for(date_from, date_to)
                if target_for_date_interval is None:
                    target_for_date_interval = self._humidity_settings_data.target

                if date_from <= now <= date_to:
                    today = datetime(now.year, now.month, now.day)

                    halfDays = (date_to - today).days * 2
                    differenceInTargets = target_for_date_interval - target
                    if differenceInTargets == 0:
                        continue

                    step = differenceInTargets / halfDays

                    new_target = self._humidity_settings_data.target + step
                    self._humidity_settings_data.target = new_target
                    self._configs.set(
                        "electrovalve", "humidity_target", str(new_target)
                    )

    def start(self):
        """
        starts all actuators controllers.
        analyses sensor data and determines what to do to the actuators
        """
        self._logger.info("starting actuators controllers...")

        with concurrent.futures.ThreadPoolExecutor() as executor:
            executor.submit(self.handle_fans)
            executor.submit(self.handle_electrovalves)
            executor.submit(self.handle_humidity_cycles)

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
        target_nh3_1_third_speed = self._configs["fan"].getfloat("nh3_1_third_speed")
        target_nh3_2_third_speed = self._configs["fan"].getfloat("nh3_2_third_speed")
        target_nh3_full_speed = self._configs["fan"].getfloat("nh3_full_speed")
        current_nh3 = self._sensor_nh3.read()

        if current_nh3 >= target_nh3_full_speed:
            return self.fan_full_speed

        if current_nh3 >= target_nh3_2_third_speed:
            return self.fan_2_third_speed

        if current_nh3 >= target_nh3_1_third_speed:
            return self.fan_1_third_speed

        return self.fan_turned_off
