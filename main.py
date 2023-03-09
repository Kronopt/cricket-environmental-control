import configparser
import backend.adapters.actuators.electrovalve as electrovalve_actuator
import backend.adapters.actuators.fan as fan_actuator
import backend.adapters.sensors.co2 as co2_sensor
import backend.adapters.sensors.humidity as humidity_sensor
import backend.adapters.sensors.nh3 as nh3_sensor
import backend.adapters.sensors.temperature as temperature_sensor

# get configs
configs = configparser.ConfigParser()
configs.read("configs.ini")

# init actuators and sensors
electrovalves = electrovalve_actuator.Electrovalve(configs)
fans = fan_actuator.Fan(configs)
co2 = co2_sensor.CO2()
humidity = humidity_sensor.Humidity()
nh3 = nh3_sensor.NH3()
temperature = temperature_sensor.Temperature()

# TODO init frontend
# TODO run frontend and backend in threads/multiprocessing
