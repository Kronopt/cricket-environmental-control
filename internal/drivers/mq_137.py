import logging
import math
import random
import threading
import time
import busio
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn

try:
    import board
except NotImplementedError:
    pass


class MockReader:
    @property
    def voltage(self) -> float:
        return random.gauss(1.5, 0.3)


class MQ137:
    """
    Ammonia (NH3) Gas Sensor driver

    documentation: https://cdn.sparkfun.com/assets/7/0/2/f/8/MQ137__Ver1.4__-_Manual.pdf

    Note:
        The value of R0 varies while the sensor heats up to its stable temperature.
        Allow the sensor to pre-heat (aging) for some time before trusting its output
        (see manual: https://cdn.sparkfun.com/assets/7/0/2/f/8/MQ137__Ver1.4__-_Manual.pdf)

    variables:
        R0: sensor resistance in the clean air
        Rs: sensor resistance at various concentrations of gases
        Rl: resistance of resistor used
        Rs/R0 = 1.0 (as per the documentation)

        m = (log₁₀(y2) - log₁₀(y1)) / (log₁₀(x2) - log₁₀(x1))
        m = (log₁₀(.2) - log₁₀(.6)) / (log₁₀(50) - log₁₀(1 ))

        b = log₁₀(y ) - m*log₁₀(x)
        b = log₁₀(.6) - m*log₁₀(1)
    """

    def __init__(self) -> None:
        self._logger = logging.getLogger("drivers." + self.__class__.__name__)

        try:
            self._analog_reader = AnalogIn(
                ADS.ADS1115(busio.I2C(board.SCL, board.SDA)), ADS.P0
            )
        except NameError:
            self._logger.info("'board' not available to import. Using mock...")
            self._analog_reader = MockReader()

        self.Rl = 4.7  # value of resistor (we're using a 4.7KΩ resistor)
        self.V = 5.0  # 5V of supplied voltage
        self.Rs_over_R0 = 1.0
        self.m = -0.2808297  # calculated slope from values in documentation
        self.b = -0.2218487  # calculated intersection from values in documentation

        self._R0_lock = threading.Lock()
        self._measure_R0()

        # continuously calculate R0 in the background
        threading.Thread(target=self._measure_R0_every_5_minutes).start()

    def nh3(self) -> float:
        """NH3 ㏙"""
        VRl = self._analog_reader.voltage
        Rs = self._calculate_Rs(VRl)

        with self._R0_lock:
            ratio = Rs / self.R0

        ppm = pow(10, ((math.log10(ratio) - self.b) / self.m))

        return ppm

    def _measure_R0(self):
        measures = 200
        VRl = 0.0
        for _ in range(measures):
            VRl += self._analog_reader.voltage
        VRl /= measures

        Rs = self._calculate_Rs(VRl)
        R0 = self._calculate_R0(Rs)

        with self._R0_lock:
            self.R0 = R0

        self._logger.debug("new measured R0: %s", R0)

    def _measure_R0_every_5_minutes(self):
        while True:
            time.sleep(5 * 60)
            self._measure_R0()

    def _calculate_Rs(self, VRl: float) -> float:
        """
        Rs = (Vc/VRl-1)*RL

        Rs:  resistance of sensor
        Vc:  supply voltage
        VRl: analog voltage
        Rl:  resistance of resistor used
        """
        return ((self.V / VRl) - 1) * self.Rl

    def _calculate_R0(self, Rs: float) -> float:
        """R0 = Rs/(Rs/R0)"""
        return Rs / self.Rs_over_R0
