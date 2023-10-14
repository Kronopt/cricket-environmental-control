import logging
from http import HTTPStatus
import nicegui
import pydantic
from fastapi import HTTPException
from starlette.responses import Response
from . import configurations
from . import discovery
from ..adapters import interfaces


ALL_READINGS_ENDPOINT = "all-readings"
ELECTROVALVE_ENDPOINT = "actuators/electrovalves"
FANS_ENDPOINT = "actuators/fans"
CPU_ENDPOINT = "host/cpu"
DISK_ENDPOINT = "host/disk"
RAM_ENDPOINT = "host/ram"
HOST_TEMPERATURE_ENDPOINT = "host/temperature"
CO2_ENDPOINT = "sensors/co2"
HUMIDITY_ENDPOINT = "sensors/humidity"
NH3_ENDPOINT = "sensors/nh3"
SENSOR_TEMPERATURE_ENDPOINT = "sensors/temperature"
CONFIGS_ENDPOINT = "configs"


class Percentage(pydantic.BaseModel):
    percent: float


class State(pydantic.BaseModel):
    opened: bool


class TemperatureMeasurement(pydantic.BaseModel):
    degrees: float


class GasMeasurement(pydantic.BaseModel):
    ppm: float


class Config(pydantic.BaseModel):
    value: str


class ElectrovalveConfigs(pydantic.BaseModel):
    humidity_target: str
    humidity_cycle: str
    humidity_cycle_targets: str
    burst_opened_for_secs: int
    burst_every_secs: int


class AllReadings(pydantic.BaseModel):
    electrovalves: State
    fans: Percentage
    host_cpu: Percentage
    host_disk: Percentage
    host_ram: Percentage
    host_temperature: TemperatureMeasurement
    co2: GasMeasurement
    humidity: Percentage
    nh3: GasMeasurement
    sensor_temperature: TemperatureMeasurement


class FanConfigs(pydantic.BaseModel):
    temperature_1_third_speed: str
    temperature_2_third_speed: str
    temperature_full_speed: str
    co2_1_third_speed: str
    co2_2_third_speed: str
    co2_full_speed: str
    nh3_1_third_speed: str
    nh3_2_third_speed: str
    nh3_full_speed: str


class Configs(pydantic.BaseModel):
    electrovalve: ElectrovalveConfigs
    fan: FanConfigs


class API:
    """API to interact with sensors, actuators, configs, etc"""

    def __init__(
        self,
        configs: configurations.Configurations,
        discovery: discovery.Discovery,
        electrovalves: interfaces.ActuatorOnOff,
        fans: interfaces.ActuatorPercentage,
        host_cpu: interfaces.HostInfo,
        host_disk: interfaces.HostInfo,
        host_ram: interfaces.HostInfo,
        host_temperature: interfaces.HostInfo,
        sensor_co2: interfaces.Sensor,
        sensor_humidity: interfaces.Sensor,
        sensor_nh3: interfaces.Sensor,
        sensor_temperature: interfaces.Sensor,
    ):
        super().__init__()
        self._logger = logging.getLogger("services." + self.__class__.__name__)
        self._discovery = discovery
        self._electrovalves = electrovalves
        self._fans = fans
        self._host_cpu = host_cpu
        self._host_disk = host_disk
        self._host_ram = host_ram
        self._host_temperature = host_temperature
        self._sensor_co2 = sensor_co2
        self._sensor_humidity = sensor_humidity
        self._sensor_nh3 = sensor_nh3
        self._sensor_temperature = sensor_temperature
        self.base_url = configs["api"].get("base_path")

        @nicegui.app.middleware("http")
        async def verify_request_origin(request, call_next):
            if (
                request.url.path.startswith(self.base_url)
                and request.client.host not in self._discovery.known_nodes()
            ):
                endpoint = request.url.path.split(self.base_url, 1)[-1]
                self._logger.info(
                    "unauthorized access to %s from %s", endpoint, request.client.host
                )
                return Response(status_code=HTTPStatus.UNAUTHORIZED)

            response = await call_next(request)
            return response

        @nicegui.app.middleware("http")
        async def log_request(request, call_next):
            if request.url.path.startswith(self.base_url):
                endpoint = request.url.path.split(self.base_url, 1)[-1]
                self._logger.info(
                    "INCOMING REQUEST: %s %s %s",
                    request.method,
                    request.client.host,
                    endpoint,
                )
            response = await call_next(request)
            return response

        @nicegui.app.get(self.base_url + "_/health", status_code=HTTPStatus.OK)
        async def health():
            pass

        # all readings (actuators, host and sensors)

        @nicegui.app.get(self.base_url + ALL_READINGS_ENDPOINT)
        async def get_all_readings():
            return AllReadings(
                electrovalves=State(opened=self._electrovalves.is_on()),
                fans=Percentage(percent=self._fans.get()),
                host_cpu=Percentage(percent=self._host_cpu.get()),
                host_disk=Percentage(percent=self._host_disk.get()),
                host_ram=Percentage(percent=self._host_ram.get()),
                host_temperature=TemperatureMeasurement(
                    degrees=self._host_temperature.get()
                ),
                co2=GasMeasurement(ppm=self._sensor_co2.read()),
                humidity=Percentage(percent=self._sensor_humidity.read()),
                nh3=GasMeasurement(ppm=self._sensor_nh3.read()),
                sensor_temperature=TemperatureMeasurement(
                    degrees=self._sensor_temperature.read()
                ),
            )

        # actuators

        @nicegui.app.get(self.base_url + ELECTROVALVE_ENDPOINT)
        async def get_electrovalves_state():
            return State(opened=self._electrovalves.is_on())

        @nicegui.app.post(self.base_url + ELECTROVALVE_ENDPOINT)
        async def set_electrovalves_state(state: State):
            if state.opened:
                self._electrovalves.on()
            else:
                self._electrovalves.off()

        @nicegui.app.get(self.base_url + FANS_ENDPOINT)
        async def get_fans_state():
            return Percentage(percent=self._fans.get())

        @nicegui.app.post(self.base_url + FANS_ENDPOINT)
        async def set_fans_state(percentage: Percentage):
            self._fans.set(percentage.percent)

        # host

        @nicegui.app.get(self.base_url + CPU_ENDPOINT)
        async def get_cpu():
            return Percentage(percent=self._host_cpu.get())

        @nicegui.app.get(self.base_url + DISK_ENDPOINT)
        async def get_disk():
            return Percentage(percent=self._host_disk.get())

        @nicegui.app.get(self.base_url + RAM_ENDPOINT)
        async def get_ram():
            return Percentage(percent=self._host_ram.get())

        @nicegui.app.get(self.base_url + HOST_TEMPERATURE_ENDPOINT)
        async def get_host_temperature():
            return TemperatureMeasurement(degrees=self._host_temperature.get())

        # sensors

        @nicegui.app.get(self.base_url + CO2_ENDPOINT)
        async def get_co2():
            return GasMeasurement(ppm=self._sensor_co2.read())

        @nicegui.app.get(self.base_url + HUMIDITY_ENDPOINT)
        async def get_humidity():
            return Percentage(percent=self._sensor_humidity.read())

        @nicegui.app.get(self.base_url + NH3_ENDPOINT)
        async def get_nh3():
            return GasMeasurement(ppm=self._sensor_nh3.read())

        @nicegui.app.get(self.base_url + SENSOR_TEMPERATURE_ENDPOINT)
        async def get_sensor_temperature():
            return TemperatureMeasurement(degrees=self._sensor_temperature.read())

        # configs

        @nicegui.app.get(self.base_url + CONFIGS_ENDPOINT + "/{section}")
        async def get_configs(section: str):
            try:
                return configs[section]
            except KeyError:
                raise HTTPException(
                    status_code=404, detail="config section '{section}' not found"
                )

        @nicegui.app.get(self.base_url + CONFIGS_ENDPOINT + "/{section}/{option}")
        async def get_config(section: str, option: str):
            try:
                return Config(value=configs[section].get(option))
            except KeyError:
                raise HTTPException(
                    status_code=404, detail="config section '{section}' not found"
                )

        @nicegui.app.post(self.base_url + CONFIGS_ENDPOINT)
        async def set_configs(value: Configs):
            return configs.set_multiple(
                (
                    # electrovalve, humidity
                    (
                        "electrovalve",
                        "humidity_target",
                        value.electrovalve.humidity_target,
                    ),
                    (
                        "electrovalve",
                        "humidity_cycle",
                        value.electrovalve.humidity_cycle,
                    ),
                    (
                        "electrovalve",
                        "humidity_cycle_targets",
                        value.electrovalve.humidity_cycle_targets,
                    ),
                    # electrovalve, burst
                    (
                        "electrovalve",
                        "burst_opened_for_secs",
                        str(value.electrovalve.burst_opened_for_secs),
                    ),
                    (
                        "electrovalve",
                        "burst_every_secs",
                        str(value.electrovalve.burst_every_secs),
                    ),
                    # fan, temperature
                    (
                        "fan",
                        "temperature_1_third_speed",
                        value.fan.temperature_1_third_speed,
                    ),
                    (
                        "fan",
                        "temperature_2_third_speed",
                        value.fan.temperature_2_third_speed,
                    ),
                    (
                        "fan",
                        "temperature_full_speed",
                        value.fan.temperature_full_speed,
                    ),
                    # fan, co2
                    ("fan", "co2_1_third_speed", value.fan.co2_1_third_speed),
                    ("fan", "co2_2_third_speed", value.fan.co2_2_third_speed),
                    ("fan", "co2_full_speed", value.fan.co2_full_speed),
                    # fan, nh3
                    ("fan", "nh3_1_third_speed", value.fan.nh3_1_third_speed),
                    ("fan", "nh3_2_third_speed", value.fan.nh3_2_third_speed),
                    ("fan", "nh3_full_speed", value.fan.nh3_full_speed),
                )
            )

        @nicegui.app.post(self.base_url + CONFIGS_ENDPOINT + "/{section}/{option}")
        async def set_config(section: str, option: str, value: Config):
            return configs.set(section, option, value.value)
