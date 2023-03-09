import configparser

# get configs
configs = configparser.ConfigParser()
configs.read("configs.ini")

# TODO run frontend and backend in threads/multiprocessing
