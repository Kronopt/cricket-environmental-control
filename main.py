import argparse
import concurrent.futures
import logging
import internal.adapters.actuators.electrovalve as actuator_electrovalve
import internal.adapters.actuators.fan as actuator_fan
import internal.adapters.host.cpu as host_cpu
import internal.adapters.host.disk as host_disk
import internal.adapters.host.ram as host_ram
import internal.adapters.host.temperature as host_temperature
import internal.adapters.sensors.co2 as sensor_co2
import internal.adapters.sensors.humidity as sensor_humidity
import internal.adapters.sensors.nh3 as sensor_nh3
import internal.adapters.sensors.temperature as sensor_temperature
import internal.services.api as service_api
import internal.services.api_client as service_api_client
import internal.services.configurations as service_configs
import internal.services.discovery as service_discovery
import internal.services.actuators_controller as service_actuators_controller
import internal.services.frontend as service_frontend
import internal.services.poller as service_poller


# cli
cli = argparse.ArgumentParser(description="cricket environmental control")
cli.add_argument(
    "-l",
    "--logger",
    choices=["DEBUG", "INFO", "WARNING", "ERROR", "FATAL"],
    default="INFO",
    help="log level (defaults to info)",
)
cli = cli.parse_args()
log_level: int = getattr(logging, cli.logger)


# logging
logging.basicConfig(
    level=log_level,
    handlers=(logging.StreamHandler(), logging.FileHandler(".log", "a")),
    format="%(asctime)s:%(levelname)s:%(name)s:%(message)s",
    datefmt="%Y-%m-%d %H-%M-%S",
)
logger = logging.getLogger("main")
logger.info(f"logging with level {cli.logger}")

# configs
configs = service_configs.Configurations()

# host statistics
logger.info("init host statistics...")
cpu = host_cpu.CPU()
disk = host_disk.Disk()
ram = host_ram.RAM()
temperature_host = host_temperature.Temperature()

# actuators/sensors
logger.info("init actuators and sensors...")
electrovalves = actuator_electrovalve.Electrovalve(configs)
fans = actuator_fan.Fan(configs)
co2 = sensor_co2.CO2()
humidity = sensor_humidity.Humidity()
nh3 = sensor_nh3.NH3()
temperature_sensor = sensor_temperature.Temperature()

# services
logger.info("init services...")
actuators_controller = service_actuators_controller.ActuatorsController(
    configs,
    electrovalves,
    fans,
    co2,
    humidity,
    nh3,
    temperature_sensor,
)
discovery = service_discovery.Discovery(configs)
api = service_api.API(
    configs,
    discovery,
    electrovalves,
    fans,
    cpu,
    disk,
    ram,
    temperature_host,
    co2,
    humidity,
    nh3,
    temperature_sensor,
)
api_client = service_api_client.APIClient(configs)
poller_manager = service_poller.PollerManager(configs, api_client)
frontend = service_frontend.Frontend(
    configs,
    api_client,
    discovery,
    poller_manager,
    electrovalves,
    fans,
    cpu,
    disk,
    ram,
    temperature_host,
    co2,
    humidity,
    nh3,
    temperature_sensor,
)

discovery.subscribe(frontend)

# run
with concurrent.futures.ThreadPoolExecutor() as executor:
    executor.submit(discovery.broadcast_listen)
    executor.submit(discovery.broadcast)
    executor.submit(discovery.ping_listen)
    executor.submit(discovery.ping)
    executor.submit(actuators_controller.start)
    executor.submit(frontend.run)
