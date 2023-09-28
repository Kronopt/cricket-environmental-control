import logging
import typing
import requests
from . import api
from . import configurations


class APIClient:
    """API client to interact with other nodes"""

    def __init__(self, configs: configurations.Configurations):
        self._logger = logging.getLogger("services." + self.__class__.__name__)
        self._base_api_url = configs["api"].get("base_path")
        self._port = configs["api"].getint("port")
        self._sessions_by_ip: dict[str, requests.Session] = dict()

    # all readings (actuators, host and sensors)

    def get_all_readings(self, ip: str) -> api.AllReadings:
        return self._get_all_readings(ip, api.ALL_READINGS_ENDPOINT)

    # actuators

    def get_electrovalves_state(self, ip: str) -> api.State:
        return self._get_state(ip, api.ELECTROVALVE_ENDPOINT)

    def set_electrovalves_state(self, ip: str, opened: bool):
        self._set_state(ip, api.ELECTROVALVE_ENDPOINT, opened)

    def get_fans_state(self, ip: str) -> api.Percentage:
        return self._get_percentage(ip, api.FANS_ENDPOINT)

    def set_fans_state(self, ip: str, percentage: float):
        self._set_percentage(ip, api.FANS_ENDPOINT, percentage)

    # host

    def get_cpu(self, ip: str) -> api.Percentage:
        return self._get_percentage(ip, api.CPU_ENDPOINT)

    def get_disk(self, ip: str) -> api.Percentage:
        return self._get_percentage(ip, api.DISK_ENDPOINT)

    def get_ram(self, ip: str) -> api.Percentage:
        return self._get_percentage(ip, api.RAM_ENDPOINT)

    def get_host_temperature(self, ip: str) -> api.TemperatureMeasurement:
        return self._get_temperature_measurement(ip, api.HOST_TEMPERATURE_ENDPOINT)

    # sensors

    def get_co2(self, ip: str) -> api.GasMeasurement:
        return self._get_gas_measurement(ip, api.CO2_ENDPOINT)

    def get_humidity(self, ip: str) -> api.Percentage:
        return self._get_percentage(ip, api.HUMIDITY_ENDPOINT)

    def get_nh3(self, ip: str) -> api.GasMeasurement:
        return self._get_gas_measurement(ip, api.NH3_ENDPOINT)

    def get_sensor_temperature(self, ip: str) -> api.TemperatureMeasurement:
        return self._get_temperature_measurement(ip, api.SENSOR_TEMPERATURE_ENDPOINT)

    # configs

    def get_configs(self, ip: str, section: str) -> typing.Dict[str, str]:
        session = self._get_session(ip)
        endpoint = f"{api.CONFIGS_ENDPOINT}/{section}"
        self._log_call("GET", endpoint, ip)

        response = session.get(
            f"http://{ip}:{self._port}{self._base_api_url}{endpoint}"
        )
        response.raise_for_status()
        return response.json()

    def get_config(self, ip: str, section: str, option: str) -> api.Config:
        session = self._get_session(ip)
        endpoint = f"{api.CONFIGS_ENDPOINT}/{section}/{option}"
        self._log_call("GET", endpoint, ip)

        response = session.get(
            f"http://{ip}:{self._port}{self._base_api_url}{endpoint}"
        )
        response.raise_for_status()
        return api.Config(value=response.json()["value"])

    def set_configs(self, ip: str, value: api.Configs):
        session = self._get_session(ip)
        endpoint = api.CONFIGS_ENDPOINT
        self._log_call("POST", endpoint, ip)

        response = session.post(
            f"http://{ip}:{self._port}{self._base_api_url}{endpoint}",
            data=value.json(),
        )
        response.raise_for_status()

    def set_config(self, ip: str, section: str, option: str, value: str):
        session = self._get_session(ip)
        endpoint = f"{api.CONFIGS_ENDPOINT}/{section}/{option}"
        self._log_call("POST", endpoint, ip)

        response = session.post(
            f"http://{ip}:{self._port}{self._base_api_url}{endpoint}",
            data=api.Config(value=value).json(),
        )
        response.raise_for_status()

    # helpers

    def _get_all_readings(self, ip: str, endpoint: str) -> api.AllReadings:
        session = self._get_session(ip)
        self._log_call("GET", endpoint, ip)

        response = session.get(
            f"http://{ip}:{self._port}{self._base_api_url}{endpoint}"
        )
        response.raise_for_status()

        json = response.json()
        return api.AllReadings(
            electrovalves=api.State(opened=json["electrovalves"]["opened"]),
            fans=api.Percentage(percent=json["fans"]["percent"]),
            host_cpu=api.Percentage(percent=json["host_cpu"]["percent"]),
            host_disk=api.Percentage(percent=json["host_disk"]["percent"]),
            host_ram=api.Percentage(percent=json["host_ram"]["percent"]),
            host_temperature=api.TemperatureMeasurement(
                degrees=json["host_temperature"]["degrees"]
            ),
            co2=api.GasMeasurement(ppm=json["co2"]["ppm"]),
            humidity=api.Percentage(percent=json["humidity"]["percent"]),
            nh3=api.GasMeasurement(ppm=json["nh3"]["ppm"]),
            sensor_temperature=api.TemperatureMeasurement(
                degrees=json["sensor_temperature"]["degrees"]
            ),
        )

    def _get_state(self, ip: str, endpoint: str) -> api.State:
        session = self._get_session(ip)
        self._log_call("GET", endpoint, ip)

        response = session.get(
            f"http://{ip}:{self._port}{self._base_api_url}{endpoint}"
        )
        response.raise_for_status()

        json = response.json()
        return api.State(opened=json["opened"])

    def _get_percentage(self, ip: str, endpoint: str) -> api.Percentage:
        session = self._get_session(ip)
        self._log_call("GET", endpoint, ip)

        response = session.get(
            f"http://{ip}:{self._port}{self._base_api_url}{endpoint}"
        )
        response.raise_for_status()

        json = response.json()
        return api.Percentage(percent=json["percent"])

    def _get_temperature_measurement(
        self, ip: str, endpoint: str
    ) -> api.TemperatureMeasurement:
        session = self._get_session(ip)
        self._log_call("GET", endpoint, ip)

        response = session.get(
            f"http://{ip}:{self._port}{self._base_api_url}{endpoint}"
        )
        response.raise_for_status()

        json = response.json()
        return api.TemperatureMeasurement(degrees=json["degrees"])

    def _get_gas_measurement(self, ip: str, endpoint: str) -> api.GasMeasurement:
        session = self._get_session(ip)
        self._log_call("GET", endpoint, ip)

        response = session.get(
            f"http://{ip}:{self._port}{self._base_api_url}{endpoint}"
        )
        response.raise_for_status()

        json = response.json()
        return api.GasMeasurement(ppm=json["ppm"])

    def _set_state(self, ip: str, endpoint: str, opened: bool):
        self._log_call("POST", endpoint, ip)
        session = self._get_session(ip)

        response = session.post(
            f"http://{ip}:{self._port}{self._base_api_url}{endpoint}",
            data=api.State(opened=opened).json(),
        )
        response.raise_for_status()

    def _set_percentage(self, ip: str, endpoint: str, percentage: float):
        session = self._get_session(ip)
        self._log_call("POST", endpoint, ip)

        response = session.post(
            f"http://{ip}:{self._port}{self._base_api_url}{endpoint}",
            data=api.Percentage(percent=percentage).json(),
        )
        response.raise_for_status()

    def _get_session(self, ip: str):
        if ip not in self._sessions_by_ip:
            self._sessions_by_ip[ip] = requests.Session()
        return self._sessions_by_ip[ip]

    def _log_call(self, method: str, endpoint: str, host: str):
        self._logger.info("OUTGOING REQUEST: %s %s %s", method, host, endpoint)
