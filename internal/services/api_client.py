import configparser
import requests
from . import api


class APIClient:
    """API client to interact with other nodes"""

    def __init__(self, configs: configparser.ConfigParser):
        self.base_api_url = configs["api"].get("base_path")
        self.port = configs["api"].getint("port")

    # TODO test methods

    def get_electrovalves_state(self, node_ip: str) -> api.Percentage:
        r = requests.get(
            f"{node_ip}:{self.port}{self.base_api_url}actuators/electrovalves"
        )
        json = r.json()
        return api.Percentage(percent=json["percent"])

    # TODO implement remaining methods
