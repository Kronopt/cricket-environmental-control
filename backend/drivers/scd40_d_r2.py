class SCD40_D_R2:
    """CO2 Sensor driver"""

    pass  # TODO


# import time
# from sensirion_i2c_driver import LinuxI2cTransceiver, I2cConnection
# from sensirion_i2c_scd import Scd4xI2cDevice
# from sensirion_i2c_scd.scd4x.data_types import Scd4xPowerMode

# # Connect to the I²C 1 port
# with LinuxI2cTransceiver('/dev/i2c-1') as i2c_transceiver:
    # scd4x = Scd4xI2cDevice(I2cConnection(i2c_transceiver))
    
    # # Make sure measurement is stopped, else we can't get readings
    # scd4x.stop_periodic_measurement()
    # scd4x.start_periodic_measurement(power_mode=Scd4xPowerMode.HIGH)

    # while True:
        # time.sleep(5)
        # co2, temperature, humidity = scd4x.read_measurement()
        # print("CO2: {}\t\tTEMP: {}\t\tHUM: {}".format(co2, temperature, humidity))
