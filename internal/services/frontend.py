import logging
import threading
import requests
from nicegui import ui
from . import api
from . import api_client
from . import configurations
from . import discovery
from . import poller
from . import subscriber
from ..adapters import interfaces


class Data(list):
    def set(self, index: int, value: int):
        self[index] = value


class electrovalve_label(ui.label):
    def __init__(self, text: str = ""):
        super().__init__(text)
        self.default_classes = "self-center text-2xl pb-4 "
        self.classes(replace=self.default_classes)

    def on_text_change(self, text: str):
        super().on_text_change(text)
        if text == "ON":
            self.classes(replace=self.default_classes + "text-positive")
        else:
            self.classes(replace=self.default_classes)


class Frontend(subscriber.Subscriber):
    """Pretty frontend"""

    def __init__(
        self,
        configs: configurations.Configurations,
        api_client: api_client.APIClient,
        discovery: discovery.Discovery,
        poller_manager: poller.PollerManager,
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
        self._configs = configs
        self._api_client = api_client
        self._discovery = discovery
        self._poller_manager = poller_manager
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

        self.port = configs["api"].getint("port")
        self.node_cards: dict[str, ui.card] = dict()  # ip -> node card

        self._update_local_configs_lock = threading.Lock()
        self._update_remote_configs_lock = threading.Lock()

        self.header = ui.header()
        self.left_drawer = ui.left_drawer(bordered=True)

        self.temperature_fan_speeds = Data(
            (
                self._configs["fan"].getint("temperature_1_third_speed"),
                self._configs["fan"].getint("temperature_2_third_speed"),
                self._configs["fan"].getint("temperature_full_speed"),
            )
        )
        self.co2_fan_speeds = Data(
            (
                self._configs["fan"].getint("co2_1_third_speed"),
                self._configs["fan"].getint("co2_2_third_speed"),
                self._configs["fan"].getint("co2_full_speed"),
            )
        )
        self.nh3_fan_speeds = Data(
            (
                self._configs["fan"].getfloat("nh3_1_third_speed"),
                self._configs["fan"].getfloat("nh3_2_third_speed"),
                self._configs["fan"].getfloat("nh3_full_speed"),
            )
        )
        self.humidity_actuator_state = Data(
            (self._configs["electrovalve"].getint("humidity_target"),)
        )
        self.burst_state = Data(
            (
                self._configs["electrovalve"].getint("burst_opened_for_secs"),
                self._configs["electrovalve"].getint("burst_every_secs"),
            )
        )

        self.page_name = "🦗 Crickets 🦗"
        self._build_header()
        self._build_menu()
        self._build_body()

    def run(self):
        ui.run(
            port=self.port, title=self.page_name, reload=False, dark=True, show=False
        )

    def _build_header(self):
        with self.header:
            ui.button(on_click=lambda: self.left_drawer.toggle()).props(
                "flat color=white icon=menu"
            )
            ui.label(self.page_name).classes("self-center")

    def _build_menu(self):
        with self.left_drawer:
            ui.label("FANS").classes("text-center")
            self._build_temperature_options()
            self._build_co2_options()
            self._build_nh3_options()
            ui.separator().classes("mt-4 mb-4")

            ui.label("PUMPS").classes("text-center")
            self._build_humidity_options()
            self._build_pump_burst_options()
            ui.separator().classes("mt-4 mb-4")

            self._build_apply_configs()
            ui.separator().classes("mt-4 mb-4")

            ui.button(
                "search for new nodes",
                on_click=self.search_for_nodes,
            ).classes("ml-12 text-xs max-h-10")

    def _build_temperature_options(self):
        with ui.expansion("Temperature (℃)", icon="thermostat"):
            fan_chart = ui.chart(
                {
                    "title": False,
                    "xAxis": {
                        "title": {"text": "fan speed"},
                        "categories": ["1/3", "2/3", "full"],
                    },
                    "yAxis": {
                        "title": {"text": "temp (ºc)"},
                    },
                    "series": [
                        {
                            "showInLegend": False,
                            "data": self.temperature_fan_speeds,
                        }
                    ],
                }
            ).classes("w-full h-40 pb-4")

            ui.label("set fans to 1/3 speed at:")
            ui.slider(
                min=0, max=100, step=1, value=self.temperature_fan_speeds[0]
            ).classes("pb-8").props("label-always switch-label-side").on(
                "update:model-value",
                lambda e: (
                    self.temperature_fan_speeds.set(0, int(e.args)),
                    self._update_chart(fan_chart, self.temperature_fan_speeds),
                ),
            )

            ui.label("set fans to 2/3 speed at:")
            ui.slider(
                min=0, max=100, step=1, value=self.temperature_fan_speeds[1]
            ).classes("pb-8").props("label-always switch-label-side").on(
                "update:model-value",
                lambda e: (
                    self.temperature_fan_speeds.set(1, int(e.args)),
                    self._update_chart(fan_chart, self.temperature_fan_speeds),
                ),
            )

            ui.label("set fans to full speed at:")
            ui.slider(
                min=0, max=100, step=1, value=self.temperature_fan_speeds[2]
            ).classes("pb-8").props("label-always switch-label-side").on(
                "update:model-value",
                lambda e: (
                    self.temperature_fan_speeds.set(2, int(e.args)),
                    self._update_chart(fan_chart, self.temperature_fan_speeds),
                ),
            )

    def _build_co2_options(self):
        with ui.expansion("CO2 (㏙)", icon="co2"):
            fan_chart = ui.chart(
                {
                    "title": False,
                    "xAxis": {
                        "title": {"text": "fan speed"},
                        "categories": ["1/3", "2/3", "full"],
                    },
                    "yAxis": {
                        "title": {"text": "co2 ㏙"},
                    },
                    "series": [
                        {
                            "showInLegend": False,
                            "data": self.co2_fan_speeds,
                        }
                    ],
                }
            ).classes("w-full h-40 pb-4")

            ui.label("set fans to 1/3 speed at:")
            ui.slider(min=0, max=5000, step=10, value=self.co2_fan_speeds[0],).classes(
                "pb-8"
            ).props("label-always switch-label-side").on(
                "update:model-value",
                lambda e: (
                    self.co2_fan_speeds.set(0, int(e.args)),
                    self._update_chart(fan_chart, self.co2_fan_speeds),
                ),
            )

            ui.label("set fans to 2/3 speed at:")
            ui.slider(min=0, max=5000, step=10, value=self.co2_fan_speeds[1],).classes(
                "pb-8"
            ).props("label-always switch-label-side").on(
                "update:model-value",
                lambda e: (
                    self.co2_fan_speeds.set(1, int(e.args)),
                    self._update_chart(fan_chart, self.co2_fan_speeds),
                ),
            )

            ui.label("set fans to full speed at:")
            ui.slider(min=0, max=5000, step=10, value=self.co2_fan_speeds[2],).classes(
                "pb-8"
            ).props("label-always switch-label-side").on(
                "update:model-value",
                lambda e: (
                    self.co2_fan_speeds.set(2, int(e.args)),
                    self._update_chart(fan_chart, self.co2_fan_speeds),
                ),
            )

    def _build_nh3_options(self):
        with ui.expansion("NH3 (㏙)", icon="propane"):
            fan_chart = ui.chart(
                {
                    "title": False,
                    "xAxis": {
                        "title": {"text": "fan speed"},
                        "categories": ["1/3", "2/3", "full"],
                    },
                    "yAxis": {
                        "title": {"text": "nh3 ㏙"},
                    },
                    "series": [
                        {
                            "showInLegend": False,
                            "data": self.nh3_fan_speeds,
                        }
                    ],
                }
            ).classes("w-full h-40 pb-4")

            ui.label("set fans to 1/3 speed at:")
            ui.slider(min=0, max=1, step=0.01, value=self.nh3_fan_speeds[0],).classes(
                "pb-8"
            ).props("label-always switch-label-side").on(
                "update:model-value",
                lambda e: (
                    self.nh3_fan_speeds.set(0, int(e.args)),
                    self._update_chart(fan_chart, self.nh3_fan_speeds),
                ),
            )

            ui.label("set fans to 2/3 speed at:")
            ui.slider(min=0, max=1, step=0.01, value=self.nh3_fan_speeds[1],).classes(
                "pb-8"
            ).props("label-always switch-label-side").on(
                "update:model-value",
                lambda e: (
                    self.nh3_fan_speeds.set(1, int(e.args)),
                    self._update_chart(fan_chart, self.nh3_fan_speeds),
                ),
            )

            ui.label("set fans to full speed at:")
            ui.slider(min=0, max=1, step=0.01, value=self.nh3_fan_speeds[2],).classes(
                "pb-8"
            ).props("label-always switch-label-side").on(
                "update:model-value",
                lambda e: (
                    self.nh3_fan_speeds.set(2, int(e.args)),
                    self._update_chart(fan_chart, self.nh3_fan_speeds),
                ),
            )

    def _build_humidity_options(self):
        with ui.expansion("Humidity (%RH)", icon="water_drop"):
            ui.label("target relative humidity:")
            ui.slider(
                min=0,
                max=100,
                step=1,
                value=self.humidity_actuator_state[0],
            ).classes("pb-8").props("label-always switch-label-side").on(
                "update:model-value",
                lambda e: self.humidity_actuator_state.set(0, int(e.args)),
            )

    def _build_pump_burst_options(self):
        with ui.expansion("Bursts", icon="shower"):

            ui.number(
                prefix="opened for",
                value=self.burst_state[0],
                min=1,
                step=1,
                suffix="secs",
                on_change=lambda e: self.burst_state.set(0, int(e.value)),
            ).classes("pr-32")

            ui.number(
                prefix="every",
                value=self.burst_state[1],
                min=1,
                step=1,
                suffix="secs",
                on_change=lambda e: self.burst_state.set(1, int(e.value)),
            ).classes("pr-32")

    def _build_apply_configs(self):
        with ui.grid(columns=2):
            with ui.button("apply current", on_click=self.update_local_configs).classes(
                "text-xs max-h-10"
            ):
                ui.tooltip("applies configs to current connected Raspberry Pi").classes(
                    "text-center"
                )

            with ui.button(
                "apply all", on_click=self.update_all_configs, color="white"
            ).classes("text-xs max-h-10 text-zinc-600"):
                ui.tooltip(
                    "applies configs to current connected Raspberry Pi as well as to all known remote Raspberry Pis"
                ).classes("text-center")

    def _build_body(self):
        self.nodes_body = ui.grid(columns=3)
        with self.nodes_body:
            self._host_node()

    def _host_node(self):
        with ui.card().classes("no-shadow border-[2px] border-blue-400"):
            with ui.image("./assets/raspberry-pi.png").classes("object-top scale-50"):
                ui.label(self._discovery.own_ip()).classes(
                    "absolute-bottom text-center"
                )

            ui.label("node info").classes("self-center")
            with ui.row():
                with ui.card():
                    ui.label("cpu %").classes("self-center")
                    ui.knob(
                        float(f"{self._host_cpu.get():.2f}"),
                        min=0,
                        max=100,
                        center_color="dark",
                        show_value=True,
                    ).bind_value_from(
                        self._host_cpu, "value", backward=lambda x: float(f"{x:.2f}")
                    )

                with ui.card():
                    ui.label("ram %").classes("self-center")
                    ui.knob(
                        float(f"{self._host_ram.get():.2f}"),
                        min=0,
                        max=100,
                        center_color="dark",
                        show_value=True,
                    ).bind_value_from(
                        self._host_ram, "value", backward=lambda x: float(f"{x:.2f}")
                    )

                with ui.card():
                    ui.label("disk %").classes("self-center")
                    ui.knob(
                        float(f"{self._host_disk.get():.2f}"),
                        min=0,
                        max=100,
                        center_color="dark",
                        show_value=True,
                    ).bind_value_from(
                        self._host_disk, "value", backward=lambda x: float(f"{x:.2f}")
                    )

                with ui.card():
                    ui.label("temp ℃").classes("self-center")
                    ui.knob(
                        float(f"{self._host_temperature.get():.2f}"),
                        min=0,
                        max=100,
                        center_color="dark",
                        show_value=True,
                    ).bind_value_from(
                        self._host_temperature,
                        "value",
                        backward=lambda x: float(f"{x:.2f}"),
                    )

            ui.label("crickets info").classes("self-center")
            with ui.row():
                with ui.card():
                    ui.label("temp ℃").classes("self-center")
                    ui.knob(
                        float(f"{self._sensor_temperature.read():.2f}"),
                        min=0,
                        max=100,
                        center_color="dark",
                        show_value=True,
                    ).bind_value_from(
                        self._sensor_temperature,
                        "value",
                        backward=lambda x: float(f"{x:.2f}"),
                    )

                with ui.card():
                    ui.label("co2 ㏙").classes("self-center")
                    ui.knob(
                        float(f"{self._sensor_co2.read():.2f}"),
                        min=0,
                        max=10000,
                        center_color="dark",
                        show_value=True,
                    ).bind_value_from(
                        self._sensor_co2, "value", backward=lambda x: float(f"{x:.2f}")
                    )

                with ui.card():
                    ui.label("nh3 ㏙").classes("self-center")
                    ui.knob(
                        float(f"{self._sensor_nh3.read():.2f}"),
                        min=0,
                        max=1,
                        center_color="dark",
                        show_value=True,
                    ).bind_value_from(
                        self._sensor_nh3, "value", backward=lambda x: float(f"{x:.2f}")
                    )

                with ui.card():
                    ui.label("%rh").classes("self-center")
                    ui.knob(
                        float(f"{self._sensor_humidity.read():.2f}"),
                        min=0,
                        max=100,
                        center_color="dark",
                        show_value=True,
                    ).bind_value_from(
                        self._sensor_humidity,
                        "value",
                        backward=lambda x: float(f"{x:.2f}"),
                    )

            with ui.row().classes("self-center"):
                with ui.card():
                    ui.label("fans %").classes("self-center")
                    ui.knob(
                        float(f"{self._fans.get():.2f}"),
                        min=0,
                        max=100,
                        center_color="dark",
                        show_value=True,
                    ).bind_value_from(
                        self._fans,
                        "value",
                        backward=lambda x: float(f"{x:.2f}"),
                    )

                with ui.card():
                    ui.label("pumps").classes("self-center")

                    # HACK this knob is a hack
                    # I couldn't bind the value of self.electrovalve.value to the label any other way...
                    # I'm sure there's a way to do it, I just couldn't figure it out
                    electrovalve_knob = ui.knob(float(self._electrovalves.is_on()))
                    electrovalve_knob.bind_value_from(
                        self._electrovalves,
                        "value",
                        backward=lambda x: float(x),
                    ).set_visibility(False)

                    electrovalve_label("OFF").bind_text_from(
                        electrovalve_knob,
                        "value",
                        backward=lambda x: "ON" if x else "OFF",
                    )

    def _remote_node(self, poller: poller.Poller) -> ui.card:
        node_card = ui.card().classes("no-shadow border-[2px] border-white")
        with node_card:
            with ui.image("./assets/raspberry-pi.png").classes("object-top scale-50"):
                ui.label(poller.ip).classes("absolute-bottom text-center")

            ui.label("node info").classes("self-center")
            with ui.row():
                with ui.card():
                    ui.label("cpu %").classes("self-center")
                    ui.knob(
                        float(f"{poller.readings.host_cpu:.2f}"),
                        min=0,
                        max=100,
                        center_color="dark",
                        show_value=True,
                    ).bind_value_from(
                        poller.readings,
                        "host_cpu",
                        backward=lambda x: float(f"{x:.2f}"),
                    )

                with ui.card():
                    ui.label("ram %").classes("self-center")
                    ui.knob(
                        float(f"{poller.readings.host_ram:.2f}"),
                        min=0,
                        max=100,
                        center_color="dark",
                        show_value=True,
                    ).bind_value_from(
                        poller.readings,
                        "host_ram",
                        backward=lambda x: float(f"{x:.2f}"),
                    )

                with ui.card():
                    ui.label("disk %").classes("self-center")
                    ui.knob(
                        float(f"{poller.readings.host_disk:.2f}"),
                        min=0,
                        max=100,
                        center_color="dark",
                        show_value=True,
                    ).bind_value_from(
                        poller.readings,
                        "host_disk",
                        backward=lambda x: float(f"{x:.2f}"),
                    )

                with ui.card():
                    ui.label("temp ℃").classes("self-center")
                    ui.knob(
                        float(f"{poller.readings.host_temperature:.2f}"),
                        min=0,
                        max=100,
                        center_color="dark",
                        show_value=True,
                    ).bind_value_from(
                        poller.readings,
                        "host_temperature",
                        backward=lambda x: float(f"{x:.2f}"),
                    )

            ui.label("crickets info").classes("self-center")
            with ui.row():
                with ui.card():
                    ui.label("temp ℃").classes("self-center")
                    ui.knob(
                        float(f"{poller.readings.sensor_temperature:.2f}"),
                        min=0,
                        max=100,
                        center_color="dark",
                        show_value=True,
                    ).bind_value_from(
                        poller.readings,
                        "sensor_temperature",
                        backward=lambda x: float(f"{x:.2f}"),
                    )

                with ui.card():
                    ui.label("co2 ㏙").classes("self-center")
                    ui.knob(
                        float(f"{poller.readings.co2:.2f}"),
                        min=0,
                        max=10000,
                        center_color="dark",
                        show_value=True,
                    ).bind_value_from(
                        poller.readings, "co2", backward=lambda x: float(f"{x:.2f}")
                    )

                with ui.card():
                    ui.label("nh3 ㏙").classes("self-center")
                    ui.knob(
                        float(f"{poller.readings.nh3:.2f}"),
                        min=0,
                        max=1,
                        center_color="dark",
                        show_value=True,
                    ).bind_value_from(
                        poller.readings, "nh3", backward=lambda x: float(f"{x:.2f}")
                    )

                with ui.card():
                    ui.label("%rh").classes("self-center")
                    ui.knob(
                        float(f"{poller.readings.humidity:.2f}"),
                        min=0,
                        max=100,
                        center_color="dark",
                        show_value=True,
                    ).bind_value_from(
                        poller.readings,
                        "humidity",
                        backward=lambda x: float(f"{x:.2f}"),
                    )

            with ui.row().classes("self-center"):
                with ui.card():
                    ui.label("fans %").classes("self-center")
                    ui.knob(
                        float(f"{poller.readings.fans:.2f}"),
                        min=0,
                        max=100,
                        center_color="dark",
                        show_value=True,
                    ).bind_value_from(
                        poller.readings,
                        "fans",
                        backward=lambda x: float(f"{x:.2f}"),
                    )

                with ui.card():
                    ui.label("pumps").classes("self-center")

                    # HACK this knob is a hack
                    # I couldn't bind the value of self.electrovalve.value to the label any other way...
                    # I'm sure there's a way to do it, I just couldn't figure it out
                    electrovalve_knob = ui.knob(
                        float(poller.readings.electrovalves),
                    )
                    electrovalve_knob.bind_value_from(
                        poller.readings,
                        "electrovalves",
                        backward=lambda x: float(x),
                    ).set_visibility(False)

                    electrovalve_label("OFF").bind_text_from(
                        electrovalve_knob,
                        "value",
                        backward=lambda x: "ON" if x else "OFF",
                    )

        return node_card

    def search_for_nodes(self):
        ui.notify(f"searching for new nodes...")
        threading.Thread(target=self._discovery.broadcast).start()

    def update_local_configs(self):
        ui.notify(f"updating configs for current node...")
        threading.Thread(target=self._update_local_configs).start()

    def update_all_configs(self):
        ui.notify(f"updating configs for all nodes...")
        threading.Thread(target=self._update_all_configs).start()

    def _update_local_configs(self):
        with self._update_local_configs_lock:
            self._configs.set_multiple(
                (
                    # electrovalve, humidity
                    (
                        "electrovalve",
                        "humidity_target",
                        str(self.humidity_actuator_state[0]),
                    ),
                    # electrovalve, burst
                    (
                        "electrovalve",
                        "burst_opened_for_secs",
                        str(self.burst_state[0]),
                    ),
                    (
                        "electrovalve",
                        "burst_every_secs",
                        str(self.burst_state[1]),
                    ),
                    # fan, temperature
                    (
                        "fan",
                        "temperature_1_third_speed",
                        str(self.temperature_fan_speeds[0]),
                    ),
                    (
                        "fan",
                        "temperature_2_third_speed",
                        str(self.temperature_fan_speeds[1]),
                    ),
                    (
                        "fan",
                        "temperature_full_speed",
                        str(self.temperature_fan_speeds[2]),
                    ),
                    # fan, co2
                    ("fan", "co2_1_third_speed", str(self.co2_fan_speeds[0])),
                    ("fan", "co2_2_third_speed", str(self.co2_fan_speeds[1])),
                    ("fan", "co2_full_speed", str(self.co2_fan_speeds[2])),
                    # fan, nh3
                    ("fan", "nh3_1_third_speed", str(self.nh3_fan_speeds[0])),
                    ("fan", "nh3_2_third_speed", str(self.nh3_fan_speeds[1])),
                    ("fan", "nh3_full_speed", str(self.nh3_fan_speeds[2])),
                )
            )

    def _update_all_configs(self):
        self._update_local_configs()

        with self._update_remote_configs_lock:
            configs_for_nodes = api.Configs(
                electrovalve=api.ElectrovalveConfigs(
                    humidity_target=self.humidity_actuator_state[0],
                    burst_opened_for_secs=self.burst_state[0],
                    burst_every_secs=self.burst_state[1],
                ),
                fan=api.FanConfigs(
                    temperature_1_third_speed=self.temperature_fan_speeds[0],
                    temperature_2_third_speed=self.temperature_fan_speeds[1],
                    temperature_full_speed=self.temperature_fan_speeds[2],
                    co2_1_third_speed=self.co2_fan_speeds[0],
                    co2_2_third_speed=self.co2_fan_speeds[1],
                    co2_full_speed=self.co2_fan_speeds[2],
                    nh3_1_third_speed=self.nh3_fan_speeds[0],
                    nh3_2_third_speed=self.nh3_fan_speeds[1],
                    nh3_full_speed=self.nh3_fan_speeds[2],
                ),
            )
            for node_ip in self._discovery.known_nodes():
                try:
                    self._api_client.set_configs(node_ip, configs_for_nodes)
                except (requests.HTTPError, requests.exceptions.ConnectionError) as e:
                    status_code = None
                    reason = None
                    if e.response is not None:
                        status_code = e.response.status_code
                        reason = e.response.reason

                    self._logger.error(
                        f"error updating configs for node {node_ip}: status code {status_code}, reason {reason}",
                    )

    def _update_chart(self, chart: ui.chart, values: Data):
        chart.options["series"][0]["data"] = values
        chart.update()

    #
    # subscription methods
    #

    def add_ip(self, ip: str):
        super().add_ip(ip)
        with self.nodes_body:
            poller = self._poller_manager.new_poller(ip)
            node_card = self._remote_node(poller)
            self.node_cards[ip] = node_card

    def remove_ip(self, ip: str):
        super().remove_ip(ip)
        self.nodes_body.remove(self.node_cards[ip])
        self._poller_manager.remove_poller(ip)
        del self.node_cards[ip]
