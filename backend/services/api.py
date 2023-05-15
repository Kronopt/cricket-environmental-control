import configparser
from flask import Flask


class API:
    """API to interact with sensors, actuators, configs, etc"""

    def __init__(self, configs: configparser.ConfigParser):
        super().__init__()
        self.app = Flask(self.__class__.__name__)
        self.port = configs["api"].getint("port")

        @self.app.get("/_/health")
        def health():
            return ""

    def run(self):
        self.app.run("0.0.0.0", self.port, debug=False, load_dotenv=False)
