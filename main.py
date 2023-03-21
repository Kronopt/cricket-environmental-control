import configparser
import backend.adapters.actuators.electrovalve as electrovalve_actuator
import backend.adapters.actuators.fan as fan_actuator
import backend.adapters.host.cpu as cpu_host
import backend.adapters.host.disk as disk_host
import backend.adapters.host.ram as ram_host
import backend.adapters.host.temperature as temperature_host
import backend.adapters.sensors.co2 as co2_sensor
import backend.adapters.sensors.humidity as humidity_sensor
import backend.adapters.sensors.nh3 as nh3_sensor
import backend.adapters.sensors.temperature as temperature_sensor
import backend.services.discovery as discovery

# get configs
configs = configparser.ConfigParser()
configs.read("configs.ini")

# init host statistics
host_cpu = cpu_host.CPU()
host_ram = ram_host.RAM()
host_disk = disk_host.Disk()
host_temperaturte = temperature_host.Temperature()

# init actuators and sensors
electrovalves = electrovalve_actuator.Electrovalve(configs)
fans = fan_actuator.Fan(configs)
co2 = co2_sensor.CO2()
humidity = humidity_sensor.Humidity()
nh3 = nh3_sensor.NH3()
temperature = temperature_sensor.Temperature()

# init services
node_discovery = discovery.Discovery(configs)
# TODO start listening for broadcasts
# TODO register subscribers to get notified on new IPs

# TODO init frontend
# TODO run frontend and backend in threads/multiprocessing
