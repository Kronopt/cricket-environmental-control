import random
import time
from collections import namedtuple
from sensirion_i2c_driver import LinuxI2cTransceiver, I2cConnection
from sensirion_i2c_scd import Scd4xI2cDevice
from sensirion_i2c_scd.scd4x.data_types import Scd4xPowerMode


class MockDevice:
    def read_measurement(self):
        return (
            namedtuple("co2", "co2")(float(random.randrange(0, 100))),
            namedtuple("temperature", "degrees_celsius")(
                float(random.randrange(0, 100))
            ),
            namedtuple("humidity", "percent_rh")(float(random.randrange(0, 100))),
        )


class SCD40_D_R2:
    """CO2, Temperature and Humidity Sensor driver"""

    try:
        i2c_transceiver = LinuxI2cTransceiver("/dev/i2c-1")
        device = Scd4xI2cDevice(I2cConnection(i2c_transceiver))

        device.stop_periodic_measurement()
        device.start_periodic_measurement(
            power_mode=Scd4xPowerMode.HIGH
        )  # every 5 seconds

        time.sleep(5)  # I guess the sensor needs to warm up a bit...

    except FileNotFoundError:  # code probably not running on linux
        device = MockDevice()

    last_measures = device.read_measurement()  # (co2, temperature, humidity)
    last_update = time.time()

    def co2(self) -> float:
        """CO2 ppm"""
        self._take_measurement()
        return SCD40_D_R2.last_measures[0].co2

    def temperature(self) -> float:
        """Temperature in °C"""
        self._take_measurement()
        return SCD40_D_R2.last_measures[1].degrees_celsius

    def humidity(self) -> float:
        """Humidity in %RH"""
        self._take_measurement()
        return SCD40_D_R2.last_measures[2].percent_rh

    def _take_measurement(self):
        """take a new measurement only if 5 seconds have passed since last measurement"""
        if (now := time.time()) - SCD40_D_R2.last_update > 5:  # 5 seconds have passed
            SCD40_D_R2.last_measures = SCD40_D_R2.device.read_measurement()
            SCD40_D_R2.last_update = now
