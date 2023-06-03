import configparser
import logging
import internal.adapters.actuators.electrovalve as electrovalve_actuator
import internal.adapters.actuators.fan as fan_actuator
import internal.adapters.host.cpu as cpu_host
import internal.adapters.host.disk as disk_host
import internal.adapters.host.ram as ram_host
import internal.adapters.host.temperature as temperature_host
import internal.adapters.sensors.co2 as co2_sensor
import internal.adapters.sensors.humidity as humidity_sensor
import internal.adapters.sensors.nh3 as nh3_sensor
import internal.adapters.sensors.temperature as temperature_sensor
import internal.services.discovery as service_discovery
import internal.services.api as service_api
import internal.services.api_client as service_api_client
import internal.services.frontend as service_frontend

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("main")

logger.info("reading configs...")
configs = configparser.ConfigParser()
configs.read("configs.ini")

logger.info("init host statistics...")
host_cpu = cpu_host.CPU()
host_ram = ram_host.RAM()
host_disk = disk_host.Disk()
host_temperature = temperature_host.Temperature()

logger.info("init actuators and sensors...")
electrovalves = electrovalve_actuator.Electrovalve(configs)
fans = fan_actuator.Fan(configs)
co2 = co2_sensor.CO2()
humidity = humidity_sensor.Humidity()
nh3 = nh3_sensor.NH3()
temperature = temperature_sensor.Temperature()

logger.info("init services...")
api = service_api.API(
    configs,
    electrovalves,
    fans,
    host_cpu,
    host_disk,
    host_ram,
    host_temperature,
    co2,
    humidity,
    nh3,
    temperature,
)
api_client = service_api_client.APIClient(configs)
discovery = service_discovery.Discovery(configs)
frontend = service_frontend.Frontend(configs)

discovery.subscribe(api, frontend)

# run
frontend.run()


# TODO start listening for broadcasts
# TODO when frontend opens send broadcast
# TODO run frontend/backend/API in threads/multiprocessing
# TODO logs everywhere!
