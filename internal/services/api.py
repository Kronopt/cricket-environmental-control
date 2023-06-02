import configparser
from http import HTTPStatus
from nicegui import app
from pydantic import BaseModel
from starlette.responses import Response
from .subscriber import Subscriber
from ..adapters.actuators.electrovalve import Electrovalve
from ..adapters.actuators.fan import Fan
from ..adapters.host.cpu import CPU
from ..adapters.host.disk import Disk
from ..adapters.host.ram import RAM
from ..adapters.host.temperature import Temperature as HostTemperature
from ..adapters.sensors.co2 import CO2
from ..adapters.sensors.humidity import Humidity
from ..adapters.sensors.nh3 import NH3
from ..adapters.sensors.temperature import Temperature as SensorTemperature


class Percentage(BaseModel):
    percent: float


class TemperatureMeasurement(BaseModel):
    degrees: float


class Co2Measurement(BaseModel):
    ppm: float


class HumidityMeasurement(BaseModel):
    percent_rh: float


class API(Subscriber):
    """API to interact with sensors, actuators, configs, etc"""

    def __init__(
        self,
        configs: configparser.ConfigParser,
        electrovalves: Electrovalve,
        fans: Fan,
        host_cpu: CPU,
        host_disk: Disk,
        host_ram: RAM,
        host_temperature: HostTemperature,
        sensor_co2: CO2,
        sensor_humidity: Humidity,
        sensor_nh3: NH3,
        sensor_temperature: SensorTemperature,
    ):
        super().__init__()
        self.base_url = configs["api"].get("base_path")
        self.electrovalves = electrovalves
        self.fans = fans
        self.host_cpu = host_cpu
        self.host_disk = host_disk
        self.host_ram = host_ram
        self.host_temperature = host_temperature
        self.sensor_co2 = sensor_co2
        self.sensor_humidity = sensor_humidity
        self.sensor_nh3 = sensor_nh3
        self.sensor_temperature = sensor_temperature

        @app.middleware("http")
        async def verify_request_origin(request, call_next):
            if (
                request.url.path.startswith(self.base_url)
                and request.client.host not in self.known_ips
            ):
                return Response(status_code=HTTPStatus.UNAUTHORIZED)

            response = await call_next(request)
            return response

        @app.get(self.base_url + "_/health", status_code=HTTPStatus.OK)
        async def health():
            pass

        # actuators

        @app.get(self.base_url + "actuators/electrovalves")
        async def get_electrovalves_state():
            return Percentage(percent=self.electrovalves.get())

        @app.post(self.base_url + "actuators/electrovalves")
        async def set_electrovalves_state(percentage: Percentage):
            self.electrovalves.set(percentage.percent)

        @app.get(self.base_url + "actuators/fans")
        async def get_fans_state():
            return Percentage(percent=self.fans.get())

        @app.post(self.base_url + "actuators/fans")
        async def set_fans_state(percentage: Percentage):
            self.fans.set(percentage.percent)

        # host

        @app.get(self.base_url + "host/cpu")
        async def get_cpu():
            return Percentage(percent=self.host_cpu.get())

        @app.get(self.base_url + "host/disk")
        async def get_disk():
            return Percentage(percent=self.host_disk.get())

        @app.get(self.base_url + "host/ram")
        async def get_ram():
            return Percentage(percent=self.host_ram.get())

        @app.get(self.base_url + "host/temperature")
        async def get_host_temperature():
            return TemperatureMeasurement(degrees=self.host_temperature.get())

        # sensors

        @app.get(self.base_url + "sensors/co2")
        async def get_co2():
            return Co2Measurement(ppm=self.sensor_co2.read())

        @app.get(self.base_url + "sensors/humidity")
        async def get_humidity():
            return HumidityMeasurement(percent_rh=self.sensor_humidity.read())

        @app.get(self.base_url + "sensors/nh3")
        async def get_nh3():
            # TODO not sure if this is a percentage yet...
            return Percentage(percent=self.sensor_nh3.read())

        @app.get(self.base_url + "sensors/temperature")
        async def get_sensor_temperature():
            return TemperatureMeasurement(degrees=self.sensor_temperature.read())
