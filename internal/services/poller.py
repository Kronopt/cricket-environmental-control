from dataclasses import dataclass
import logging
import threading
import time
import requests
from . import api_client
from . import configurations


@dataclass
class Readings:
    electrovalves: bool = False
    fans: float = 0.0
    host_cpu: float = 0.0
    host_disk: float = 0.0
    host_ram: float = 0.0
    host_temperature: float = 0.0
    co2: float = 0.0
    humidity: float = 0.0
    nh3: float = 0.0
    sensor_temperature: float = 0.0


class PollerManager:
    """manages pollers"""

    def __init__(
        self,
        configs: configurations.Configurations,
        api_client: api_client.APIClient,
    ):
        super().__init__()
        self._logger = logging.getLogger("services." + self.__class__.__name__)
        self._api_client = api_client
        self._update_interval = configs["poller"].getint("update_interval")
        self._pollers: dict[str, "Poller"] = dict()  # ip -> Poller for that node ip

    def new_poller(self, ip: str) -> "Poller":
        if not ip in self._pollers:
            self._pollers[ip] = Poller(self, ip)
        return self._pollers[ip]

    def remove_poller(self, ip: str):
        if ip in self._pollers:
            self._pollers[ip].stop()
            del self._pollers[ip]


class Poller:
    """polls another node for data, given a node ip"""

    def __init__(
        self,
        manager: PollerManager,
        ip: str,
    ):
        """starts polling node API at the given ip"""
        super().__init__()
        self._manager = manager
        self.ip = ip
        self.on = True
        self.readings = Readings()

        threading.Thread(target=self._poll_api).start()

    def stop(self):
        """stops polling node API at the given ip"""
        self.on = False

    def _poll_api(self):
        """polls node API at the given ip at defined intervals"""
        while True:
            time.sleep(self._manager._update_interval)

            if not self.on:
                return

            try:
                readings = self._manager._api_client.get_all_readings(self.ip)
                self.readings.electrovalves = readings.electrovalves.opened
                self.readings.fans = readings.fans.percent
                self.readings.host_cpu = readings.host_cpu.percent
                self.readings.host_disk = readings.host_disk.percent
                self.readings.host_ram = readings.host_ram.percent
                self.readings.host_temperature = readings.host_temperature.degrees
                self.readings.co2 = readings.co2.ppm
                self.readings.humidity = readings.humidity.percent
                self.readings.nh3 = readings.nh3.ppm
                self.readings.sensor_temperature = readings.sensor_temperature.degrees
            except (requests.HTTPError, requests.exceptions.ConnectionError) as e:
                status_code = None
                reason = None
                if e.response is not None:
                    status_code = e.response.status_code
                    reason = e.response.reason

                self._manager._logger.error(
                    f"error getting all readings for node {self.ip}: status code {status_code}, reason {reason}",
                )
