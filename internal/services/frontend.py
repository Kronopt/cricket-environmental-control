import configparser
from nicegui import ui
from .subscriber import Subscriber


class Frontend(Subscriber):
    """Pretty frontend"""

    def __init__(self, configs: configparser.ConfigParser):
        super().__init__()
        self.port = configs["api"].getint("port")
        self.page_name = "🦗 Crickets 🦗"

        with ui.header():
            ui.label(self.page_name).style(
                "margin: auto; font-size: 30px; font-weight: bold"
            )

        with ui.left_drawer(fixed=False):
            ui.label("drawer")
            # TODO
            #   Home
            #   Nodes
            #       node-1
            #       node-2
            #       ...

        # TODO
        #   CPU
        #   RAM
        #   DISK
        #   status of sensors/actuators

        # TODO more

        # TODO cards

    def run(self):
        ui.run(port=self.port, title=self.page_name, reload=False, dark=True)
