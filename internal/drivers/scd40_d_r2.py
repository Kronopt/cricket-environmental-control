import logging
import random
import threading
import time
import collections
import sensirion_i2c_driver as driver
import sensirion_i2c_scd as scd
from sensirion_i2c_scd.scd4x.data_types import Scd4xPowerMode


class MockDevice:
    def read_measurement(self):
        return (
            collections.namedtuple("co2", "co2")(random.gauss(80, 3)),
            collections.namedtuple("temperature", "degrees_celsius")(
                random.gauss(20, 3)
            ),
            collections.namedtuple("humidity", "percent_rh")(random.gauss(50, 3)),
        )


class SCD40_D_R2:
    """CO2, Temperature and Humidity Sensor driver"""

    def __init__(self):
        """singleton"""
        if hasattr(SCD40_D_R2, "_initialized"):
            return

        SCD40_D_R2._initialized = True
        SCD40_D_R2._logger = logging.getLogger("drivers." + self.__class__.__name__)

        try:
            i2c_transceiver = driver.LinuxI2cTransceiver("/dev/i2c-1")
            SCD40_D_R2._device = scd.Scd4xI2cDevice(
                driver.I2cConnection(i2c_transceiver)
            )

            SCD40_D_R2._device.stop_periodic_measurement()
            SCD40_D_R2._device.start_periodic_measurement(
                power_mode=Scd4xPowerMode.HIGH
            )

            time.sleep(5)  # I guess the sensor needs to warm up a bit...

        except FileNotFoundError:  # code probably not running on linux
            SCD40_D_R2._logger.info("can't connect to SCD40 sensor. Using mock...")
            SCD40_D_R2._device = MockDevice()

        SCD40_D_R2._measure_lock = threading.Lock()
        SCD40_D_R2._last_update = 0.0
        self._take_measurement()  # (co2, temperature, humidity)

    def co2(self) -> float:
        """CO2 ㏙"""
        self._take_measurement()
        return SCD40_D_R2._last_measures[0].co2

    def temperature(self) -> float:
        """Temperature in ℃"""
        self._take_measurement()
        return SCD40_D_R2._last_measures[1].degrees_celsius

    def humidity(self) -> float:
        """Humidity in %RH"""
        self._take_measurement()
        return SCD40_D_R2._last_measures[2].percent_rh

    def _take_measurement(self):
        """take a new measurement only if 5 seconds have passed since last measurement"""
        with SCD40_D_R2._measure_lock:
            if (now := time.time()) - SCD40_D_R2._last_update > 5:
                SCD40_D_R2._last_measures = SCD40_D_R2._device.read_measurement()
                SCD40_D_R2._last_update = now
