import logging
import threading
import requests
from dataclasses import dataclass
from typing import Any
from nicegui import ui
from . import actuators_controller
from . import api
from . import api_client
from . import configurations
from . import discovery
from . import poller
from . import subscriber
from .dates import Dates
from ..adapters import interfaces


@dataclass
class TemperatureFanData:
    one_third_speed: int
    two_third_speed: int
    full_speed: int

    def set_one_third_speed(self, value: int):
        self.one_third_speed = value

    def set_two_third_speed(self, value: int):
        self.two_third_speed = value

    def set_full_speed(self, value: int):
        self.full_speed = value

    def values(self) -> list[int]:
        return [self.one_third_speed, self.two_third_speed, self.full_speed]


@dataclass
class CO2FanData:
    one_third_speed: int
    two_third_speed: int
    full_speed: int

    def set_one_third_speed(self, value: int):
        self.one_third_speed = value

    def set_two_third_speed(self, value: int):
        self.two_third_speed = value

    def set_full_speed(self, value: int):
        self.full_speed = value

    def values(self) -> list[int]:
        return [self.one_third_speed, self.two_third_speed, self.full_speed]


@dataclass
class NH3FanData:
    one_third_speed: float
    two_third_speed: float
    full_speed: float

    def set_one_third_speed(self, value: float):
        self.one_third_speed = value

    def set_two_third_speed(self, value: float):
        self.two_third_speed = value

    def set_full_speed(self, value: float):
        self.full_speed = value

    def values(self) -> list[float]:
        return [self.one_third_speed, self.two_third_speed, self.full_speed]


@dataclass
class HumiditySettings:
    target: int
    cycle: str
    cycle_targets: str

    def set_target(self, value: int):
        self.target = value

    def _set_cycle(self, value: str) -> Dates:
        dates = Dates(value)
        dates.remove_past_dates()
        return dates

    def set_cycle(self, value: str):
        self.cycle = str(self._set_cycle(value))

    def set_cycle_targets(self, value: str):
        self.cycle_targets = value

    def __setattr__(self, prop, val):
        if prop == "cycle":
            dates = self._set_cycle(val)
            val = str(dates)

        super().__setattr__(prop, val)


@dataclass
class BurstSettings:
    opened_for_secs: int
    every_secs: int

    def set_opened_for_secs(self, value: int):
        self.opened_for_secs = value

    def set_every_secs(self, value: int):
        self.every_secs = value


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


class node_knob(ui.knob):
    def __init__(
        self,
        starting_value: float,
        min: float,
        max: float,
        lower_bound: float,
        mid_lower_bound: float,
        mid_upper_bound: float,
        upper_bound: float,
        lower_color: str,
        mid_color: str,
        upper_color: str,
        mid_lower_color: None | str = None,
        mid_upper_color: None | str = None,
    ):
        super().__init__(
            starting_value, min=min, max=max, center_color="dark", show_value=True
        )
        self.props("readonly")

        self.lower_bound = lower_bound
        self.mid_lower_bound = mid_lower_bound
        self.mid_upper_bound = mid_upper_bound
        self.upper_bound = upper_bound

        self.lower_color = lower_color
        self.mid_lower_color = mid_lower_color if mid_lower_color else mid_color
        self.mid_color = mid_color
        self.mid_upper_color = mid_upper_color if mid_upper_color else mid_color
        self.upper_color = upper_color

        self.on_value_change(starting_value)

    def on_value_change(self, value: Any):
        super().on_value_change(value)

        if value < self.lower_bound:
            self.props(f"color={self.lower_color}")

        elif self.lower_bound <= value < self.mid_lower_bound:
            self.props(f"color={self.mid_lower_color}")

        elif self.mid_lower_bound <= value < self.mid_upper_bound:
            self.props(f"color={self.mid_color}")

        elif self.mid_upper_bound <= value < self.upper_bound:
            self.props(f"color={self.mid_upper_color}")

        elif value >= self.upper_bound:
            self.props(f"color={self.upper_color}")


class humidity_target_option(ui.number):
    def __init__(self, date: str, config: HumiditySettings, *args, **kwargs):
        super().__init__(
            on_change=lambda e: self.save_target_rh(e.value), *args, **kwargs
        )
        self.date = date
        self.config = config

        self.save_target_rh(0)

    def save_target_rh(self, value):
        targets_rh = eval(self.config.cycle_targets)  # dict(date: str -> target: int)
        if value < 0:
            del targets_rh[self.date]
        else:
            targets_rh[self.date] = int(value)
        self.config.set_cycle_targets(str(targets_rh))


class humidity_target_options(ui.column):
    def __init__(self, dates: Any, config: HumiditySettings, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.dates: dict[str, humidity_target_option] = dict()
        self.config = config

        self.handle(dates)

    def handle(self, dates: Any):
        if dates is None:
            self._clear()
            return

        if isinstance(dates, list):
            if len(dates) == 0:
                self._clear()
                return

            targets_rh = eval(
                self.config.cycle_targets
            )  # dict(date: str -> target: int)

            new_dates = []
            for date in dates:

                date_as_str = str(date)
                new_dates.append(date_as_str)
                if date_as_str not in self.dates:
                    targets_rh[date_as_str] = 0

                    with self:
                        self.dates[date_as_str] = humidity_target_option(
                            date=date_as_str,
                            config=self.config,
                            prefix=self._prefix(date),
                            value=targets_rh[date_as_str],
                            min=0,
                            max=100,
                            step=1,
                            suffix="%rh",
                        )

            to_del = []
            for date in self.dates:
                if date not in new_dates:
                    self.dates[date].save_target_rh(-1)
                    self.dates[date].delete()
                    to_del.append(date)

            for date in to_del:
                del self.dates[date]
                del targets_rh[date]

    def _prefix(self, date: str | dict[str, str]) -> str:
        if isinstance(date, str):
            return f"{date}:"
        if isinstance(date, dict):
            return "{} to {}:".format(date["from"], date["to"])

    def _clear(self):
        self.clear()
        self.dates.clear()
        self.config.set_cycle_targets("{}")


class Frontend(subscriber.Subscriber):
    """Pretty frontend"""

    def __init__(
        self,
        configs: configurations.Configurations,
        actuator_controller: actuators_controller.ActuatorsController,
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
        self._actuator_controller = actuator_controller
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
        self.left_drawer = ui.left_drawer(bordered=True).props("width=324")

        self.temperature_fan_speeds = TemperatureFanData(
            self._configs["fan"].getint("temperature_1_third_speed"),
            self._configs["fan"].getint("temperature_2_third_speed"),
            self._configs["fan"].getint("temperature_full_speed"),
        )
        self.co2_fan_speeds = CO2FanData(
            self._configs["fan"].getint("co2_1_third_speed"),
            self._configs["fan"].getint("co2_2_third_speed"),
            self._configs["fan"].getint("co2_full_speed"),
        )
        self.nh3_fan_speeds = NH3FanData(
            self._configs["fan"].getfloat("nh3_1_third_speed"),
            self._configs["fan"].getfloat("nh3_2_third_speed"),
            self._configs["fan"].getfloat("nh3_full_speed"),
        )
        self.humidity_settings = HumiditySettings(
            self._configs["electrovalve"].getint("humidity_target"),
            self._configs["electrovalve"].get("humidity_cycle"),
            self._configs["electrovalve"].get("humidity_cycle_targets"),
        )
        self.burst_state = BurstSettings(
            self._configs["electrovalve"].getint("burst_opened_for_secs"),
            self._configs["electrovalve"].getint("burst_every_secs"),
        )

        self._actuator_controller._humidity_settings_data = self.humidity_settings

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
            self._build_humidity_cycle_options()
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
                            "data": self.temperature_fan_speeds.values(),
                        }
                    ],
                }
            ).classes("w-full h-40 pb-4")

            ui.label("set fans to 1/3 speed at:")
            ui.slider(
                min=0,
                max=100,
                step=1,
                value=self.temperature_fan_speeds.one_third_speed,
            ).classes("pb-8").props("label-always switch-label-side").on(
                "update:model-value",
                lambda e: (
                    self.temperature_fan_speeds.set_one_third_speed(int(e.args)),
                    self._update_chart(fan_chart, self.temperature_fan_speeds.values()),
                ),
            )

            ui.label("set fans to 2/3 speed at:")
            ui.slider(
                min=0,
                max=100,
                step=1,
                value=self.temperature_fan_speeds.two_third_speed,
            ).classes("pb-8").props("label-always switch-label-side").on(
                "update:model-value",
                lambda e: (
                    self.temperature_fan_speeds.set_two_third_speed(int(e.args)),
                    self._update_chart(fan_chart, self.temperature_fan_speeds.values()),
                ),
            )

            ui.label("set fans to full speed at:")
            ui.slider(
                min=0, max=100, step=1, value=self.temperature_fan_speeds.full_speed
            ).classes("pb-8").props("label-always switch-label-side").on(
                "update:model-value",
                lambda e: (
                    self.temperature_fan_speeds.set_full_speed(int(e.args)),
                    self._update_chart(fan_chart, self.temperature_fan_speeds.values()),
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
                            "data": self.co2_fan_speeds.values(),
                        }
                    ],
                }
            ).classes("w-full h-40 pb-4")

            ui.label("set fans to 1/3 speed at:")
            ui.slider(
                min=0, max=5000, step=10, value=self.co2_fan_speeds.one_third_speed
            ).classes("pb-8").props("label-always switch-label-side").on(
                "update:model-value",
                lambda e: (
                    self.co2_fan_speeds.set_one_third_speed(int(e.args)),
                    self._update_chart(fan_chart, self.co2_fan_speeds.values()),
                ),
            )

            ui.label("set fans to 2/3 speed at:")
            ui.slider(
                min=0, max=5000, step=10, value=self.co2_fan_speeds.two_third_speed
            ).classes("pb-8").props("label-always switch-label-side").on(
                "update:model-value",
                lambda e: (
                    self.co2_fan_speeds.set_two_third_speed(int(e.args)),
                    self._update_chart(fan_chart, self.co2_fan_speeds.values()),
                ),
            )

            ui.label("set fans to full speed at:")
            ui.slider(
                min=0, max=5000, step=10, value=self.co2_fan_speeds.full_speed
            ).classes("pb-8").props("label-always switch-label-side").on(
                "update:model-value",
                lambda e: (
                    self.co2_fan_speeds.set_full_speed(int(e.args)),
                    self._update_chart(fan_chart, self.co2_fan_speeds.values()),
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
                            "data": self.nh3_fan_speeds.values(),
                        }
                    ],
                }
            ).classes("w-full h-40 pb-4")

            ui.label("set fans to 1/3 speed at:")
            ui.slider(
                min=0, max=1, step=0.01, value=self.nh3_fan_speeds.one_third_speed
            ).classes("pb-8").props("label-always switch-label-side").on(
                "update:model-value",
                lambda e: (
                    self.nh3_fan_speeds.set_one_third_speed(float(e.args)),
                    self._update_chart(fan_chart, self.nh3_fan_speeds.values()),
                ),
            )

            ui.label("set fans to 2/3 speed at:")
            ui.slider(
                min=0, max=1, step=0.01, value=self.nh3_fan_speeds.two_third_speed
            ).classes("pb-8").props("label-always switch-label-side").on(
                "update:model-value",
                lambda e: (
                    self.nh3_fan_speeds.set_two_third_speed(float(e.args)),
                    self._update_chart(fan_chart, self.nh3_fan_speeds.values()),
                ),
            )

            ui.label("set fans to full speed at:")
            ui.slider(
                min=0, max=1, step=0.01, value=self.nh3_fan_speeds.full_speed
            ).classes("pb-8").props("label-always switch-label-side").on(
                "update:model-value",
                lambda e: (
                    self.nh3_fan_speeds.set_full_speed(float(e.args)),
                    self._update_chart(fan_chart, self.nh3_fan_speeds.values()),
                ),
            )

    def _build_humidity_options(self):
        with ui.expansion("Humidity (%RH)", icon="water_drop"):
            ui.label("target relative humidity:")
            ui.slider(
                min=0, max=100, step=1, value=self.humidity_settings.target
            ).classes("pb-8").props("label-always switch-label-side").bind_value(
                self.humidity_settings, "target", forward=lambda x: int(x)
            )

    def _build_humidity_cycle_options(self):
        with ui.expansion("Humidity Cycle", icon="calendar_month"):
            dates = eval(self.humidity_settings.cycle)
            ui.date(dates, on_change=lambda e: target_options.handle(e.value)).props(
                "multiple range"
            ).bind_value(
                self.humidity_settings,
                "cycle",
                forward=lambda e: str(e),
                backward=lambda e: Dates(e).date_intervals(),
            )

            target_options = humidity_target_options(
                dates=dates, config=self.humidity_settings
            )

    def _build_pump_burst_options(self):
        with ui.expansion("Bursts", icon="shower"):

            ui.number(
                prefix="opened for",
                value=self.burst_state.opened_for_secs,
                min=1,
                step=1,
                suffix="secs",
                on_change=lambda e: self.burst_state.set_opened_for_secs(int(e.value)),
            ).classes("pr-32")

            ui.number(
                prefix="every",
                value=self.burst_state.every_secs,
                min=1,
                step=1,
                suffix="secs",
                on_change=lambda e: self.burst_state.set_every_secs(int(e.value)),
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
                    node_knob(
                        float(f"{self._host_cpu.get():.2f}"),
                        min=0,
                        max=100,
                        lower_bound=70,
                        mid_lower_bound=70,
                        mid_upper_bound=90,
                        upper_bound=90,
                        lower_color="green",
                        mid_color="orange",
                        upper_color="red",
                    ).bind_value_from(
                        self._host_cpu,
                        "value",
                        backward=lambda x: float(f"{x:.2f}"),
                    )

                with ui.card():
                    ui.label("ram %").classes("self-center")
                    node_knob(
                        float(f"{self._host_ram.get():.2f}"),
                        min=0,
                        max=100,
                        lower_bound=70,
                        mid_lower_bound=70,
                        mid_upper_bound=90,
                        upper_bound=90,
                        lower_color="green",
                        mid_color="orange",
                        upper_color="red",
                    ).bind_value_from(
                        self._host_ram,
                        "value",
                        backward=lambda x: float(f"{x:.2f}"),
                    )

                with ui.card():
                    ui.label("disk %").classes("self-center")
                    node_knob(
                        float(f"{self._host_disk.get():.2f}"),
                        min=0,
                        max=100,
                        lower_bound=70,
                        mid_lower_bound=70,
                        mid_upper_bound=90,
                        upper_bound=90,
                        lower_color="green",
                        mid_color="orange",
                        upper_color="red",
                    ).bind_value_from(
                        self._host_disk,
                        "value",
                        backward=lambda x: float(f"{x:.2f}"),
                    )

                with ui.card():
                    ui.label("temp ℃").classes("self-center")
                    node_knob(
                        float(f"{self._host_temperature.get():.2f}"),
                        min=0,
                        max=100,
                        lower_bound=60,
                        mid_lower_bound=60,
                        mid_upper_bound=70,
                        upper_bound=70,
                        lower_color="green",
                        mid_color="orange",
                        upper_color="red",
                    ).bind_value_from(
                        self._host_temperature,
                        "value",
                        backward=lambda x: float(f"{x:.2f}"),
                    )

            ui.label("crickets info").classes("self-center")
            with ui.row():
                with ui.card():
                    ui.label("temp ℃").classes("self-center")
                    node_knob(
                        float(f"{self._sensor_temperature.read():.2f}"),
                        min=0,
                        max=100,
                        lower_bound=24,
                        mid_lower_bound=28,
                        mid_upper_bound=32,
                        upper_bound=35,
                        lower_color="red",
                        mid_lower_color="orange",
                        mid_color="green",
                        mid_upper_color="orange",
                        upper_color="red",
                    ).bind_value_from(
                        self._sensor_temperature,
                        "value",
                        backward=lambda x: float(f"{x:.2f}"),
                    )

                with ui.card():
                    ui.label("co2 ㏙").classes("self-center")
                    node_knob(
                        float(f"{self._sensor_co2.read():.2f}"),
                        min=0,
                        max=10000,
                        lower_bound=1000,
                        mid_lower_bound=1500,
                        mid_upper_bound=5000,
                        upper_bound=6000,
                        lower_color="red",
                        mid_lower_color="orange",
                        mid_color="green",
                        mid_upper_color="orange",
                        upper_color="red",
                    ).bind_value_from(
                        self._sensor_co2,
                        "value",
                        backward=lambda x: float(f"{x:.2f}"),
                    )

                with ui.card():
                    ui.label("nh3 ㏙").classes("self-center")
                    node_knob(
                        float(f"{self._sensor_nh3.read():.2f}"),
                        min=0,
                        max=1,
                        lower_bound=0.05,
                        mid_lower_bound=0.1,
                        mid_upper_bound=0.8,
                        upper_bound=0.85,
                        lower_color="red",
                        mid_lower_color="orange",
                        mid_color="green",
                        mid_upper_color="orange",
                        upper_color="red",
                    ).bind_value_from(
                        self._sensor_nh3,
                        "value",
                        backward=lambda x: float(f"{x:.2f}"),
                    )

                with ui.card():
                    ui.label("%rh").classes("self-center")
                    node_knob(
                        float(f"{self._sensor_humidity.read():.2f}"),
                        min=0,
                        max=100,
                        lower_bound=25,
                        mid_lower_bound=30,
                        mid_upper_bound=100,
                        upper_bound=100,
                        lower_color="red",
                        mid_lower_color="orange",
                        mid_color="green",
                        upper_color="green",
                    ).bind_value_from(
                        self._sensor_humidity,
                        "value",
                        backward=lambda x: float(f"{x:.2f}"),
                    )

            with ui.row().classes("self-center"):
                with ui.card():
                    ui.label("fans %").classes("self-center")
                    node_knob(
                        float(f"{self._sensor_humidity.read():.2f}"),
                        min=0,
                        max=100,
                        lower_bound=100,
                        mid_lower_bound=100,
                        mid_upper_bound=100,
                        upper_bound=100,
                        lower_color="green",
                        mid_color="green",
                        upper_color="green",
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
                    electrovalve_knob.props("readonly").bind_value_from(
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
                    node_knob(
                        float(f"{poller.readings.host_cpu:.2f}"),
                        min=0,
                        max=100,
                        lower_bound=70,
                        mid_lower_bound=70,
                        mid_upper_bound=90,
                        upper_bound=90,
                        lower_color="green",
                        mid_color="orange",
                        upper_color="red",
                    ).bind_value_from(
                        poller.readings,
                        "host_cpu",
                        backward=lambda x: float(f"{x:.2f}"),
                    )

                with ui.card():
                    ui.label("ram %").classes("self-center")
                    node_knob(
                        float(f"{poller.readings.host_ram:.2f}"),
                        min=0,
                        max=100,
                        lower_bound=70,
                        mid_lower_bound=70,
                        mid_upper_bound=90,
                        upper_bound=90,
                        lower_color="green",
                        mid_color="orange",
                        upper_color="red",
                    ).bind_value_from(
                        poller.readings,
                        "host_ram",
                        backward=lambda x: float(f"{x:.2f}"),
                    )

                with ui.card():
                    ui.label("disk %").classes("self-center")
                    node_knob(
                        float(f"{poller.readings.host_disk:.2f}"),
                        min=0,
                        max=100,
                        lower_bound=70,
                        mid_lower_bound=70,
                        mid_upper_bound=90,
                        upper_bound=90,
                        lower_color="green",
                        mid_color="orange",
                        upper_color="red",
                    ).bind_value_from(
                        poller.readings,
                        "host_disk",
                        backward=lambda x: float(f"{x:.2f}"),
                    )

                with ui.card():
                    ui.label("temp ℃").classes("self-center")
                    node_knob(
                        float(f"{poller.readings.host_temperature:.2f}"),
                        min=0,
                        max=100,
                        lower_bound=60,
                        mid_lower_bound=60,
                        mid_upper_bound=70,
                        upper_bound=70,
                        lower_color="green",
                        mid_color="orange",
                        upper_color="red",
                    ).bind_value_from(
                        poller.readings,
                        "host_temperature",
                        backward=lambda x: float(f"{x:.2f}"),
                    )

            ui.label("crickets info").classes("self-center")
            with ui.row():
                with ui.card():
                    ui.label("temp ℃").classes("self-center")
                    node_knob(
                        float(f"{poller.readings.sensor_temperature:.2f}"),
                        min=0,
                        max=100,
                        lower_bound=24,
                        mid_lower_bound=28,
                        mid_upper_bound=32,
                        upper_bound=35,
                        lower_color="red",
                        mid_lower_color="orange",
                        mid_color="green",
                        mid_upper_color="orange",
                        upper_color="red",
                    ).bind_value_from(
                        poller.readings,
                        "sensor_temperature",
                        backward=lambda x: float(f"{x:.2f}"),
                    )

                with ui.card():
                    ui.label("co2 ㏙").classes("self-center")
                    node_knob(
                        float(f"{poller.readings.co2:.2f}"),
                        min=0,
                        max=10000,
                        lower_bound=1000,
                        mid_lower_bound=1500,
                        mid_upper_bound=5000,
                        upper_bound=6000,
                        lower_color="red",
                        mid_lower_color="orange",
                        mid_color="green",
                        mid_upper_color="orange",
                        upper_color="red",
                    ).bind_value_from(
                        poller.readings,
                        "co2",
                        backward=lambda x: float(f"{x:.2f}"),
                    )

                with ui.card():
                    ui.label("nh3 ㏙").classes("self-center")
                    node_knob(
                        float(f"{poller.readings.nh3:.2f}"),
                        min=0,
                        max=1,
                        lower_bound=0.05,
                        mid_lower_bound=0.1,
                        mid_upper_bound=0.8,
                        upper_bound=0.85,
                        lower_color="red",
                        mid_lower_color="orange",
                        mid_color="green",
                        mid_upper_color="orange",
                        upper_color="red",
                    ).bind_value_from(
                        poller.readings,
                        "nh3",
                        backward=lambda x: float(f"{x:.2f}"),
                    )

                with ui.card():
                    ui.label("%rh").classes("self-center")
                    node_knob(
                        float(f"{poller.readings.humidity:.2f}"),
                        min=0,
                        max=100,
                        lower_bound=25,
                        mid_lower_bound=30,
                        mid_upper_bound=100,
                        upper_bound=100,
                        lower_color="red",
                        mid_lower_color="orange",
                        mid_color="green",
                        upper_color="green",
                    ).bind_value_from(
                        poller.readings,
                        "humidity",
                        backward=lambda x: float(f"{x:.2f}"),
                    )

            with ui.row().classes("self-center"):
                with ui.card():
                    ui.label("fans %").classes("self-center")
                    node_knob(
                        float(f"{poller.readings.fans:.2f}"),
                        min=0,
                        max=100,
                        lower_bound=100,
                        mid_lower_bound=100,
                        mid_upper_bound=100,
                        upper_bound=100,
                        lower_color="green",
                        mid_color="green",
                        upper_color="green",
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
                    electrovalve_knob.props("readonly").bind_value_from(
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
                        str(self.humidity_settings.target),
                    ),
                    (
                        "electrovalve",
                        "humidity_cycle",
                        str(self.humidity_settings.cycle),
                    ),
                    (
                        "electrovalve",
                        "humidity_cycle_targets",
                        str(self.humidity_settings.cycle_targets),
                    ),
                    # electrovalve, burst
                    (
                        "electrovalve",
                        "burst_opened_for_secs",
                        str(self.burst_state.opened_for_secs),
                    ),
                    (
                        "electrovalve",
                        "burst_every_secs",
                        str(self.burst_state.every_secs),
                    ),
                    # fan, temperature
                    (
                        "fan",
                        "temperature_1_third_speed",
                        str(self.temperature_fan_speeds.one_third_speed),
                    ),
                    (
                        "fan",
                        "temperature_2_third_speed",
                        str(self.temperature_fan_speeds.two_third_speed),
                    ),
                    (
                        "fan",
                        "temperature_full_speed",
                        str(self.temperature_fan_speeds.full_speed),
                    ),
                    # fan, co2
                    (
                        "fan",
                        "co2_1_third_speed",
                        str(self.co2_fan_speeds.one_third_speed),
                    ),
                    (
                        "fan",
                        "co2_2_third_speed",
                        str(self.co2_fan_speeds.two_third_speed),
                    ),
                    ("fan", "co2_full_speed", str(self.co2_fan_speeds.full_speed)),
                    # fan, nh3
                    (
                        "fan",
                        "nh3_1_third_speed",
                        str(self.nh3_fan_speeds.one_third_speed),
                    ),
                    (
                        "fan",
                        "nh3_2_third_speed",
                        str(self.nh3_fan_speeds.two_third_speed),
                    ),
                    ("fan", "nh3_full_speed", str(self.nh3_fan_speeds.full_speed)),
                )
            )

    def _update_all_configs(self):
        self._update_local_configs()

        with self._update_remote_configs_lock:
            configs_for_nodes = api.Configs(
                electrovalve=api.ElectrovalveConfigs(
                    humidity_target=str(self.humidity_settings.target),
                    humidity_cycle=self.humidity_settings.cycle,
                    humidity_cycle_targets=self.humidity_settings.cycle_targets,
                    burst_opened_for_secs=self.burst_state.opened_for_secs,
                    burst_every_secs=self.burst_state.every_secs,
                ),
                fan=api.FanConfigs(
                    temperature_1_third_speed=str(
                        self.temperature_fan_speeds.one_third_speed
                    ),
                    temperature_2_third_speed=str(
                        self.temperature_fan_speeds.two_third_speed
                    ),
                    temperature_full_speed=str(self.temperature_fan_speeds.full_speed),
                    co2_1_third_speed=str(self.co2_fan_speeds.one_third_speed),
                    co2_2_third_speed=str(self.co2_fan_speeds.two_third_speed),
                    co2_full_speed=str(self.co2_fan_speeds.full_speed),
                    nh3_1_third_speed=str(self.nh3_fan_speeds.one_third_speed),
                    nh3_2_third_speed=str(self.nh3_fan_speeds.two_third_speed),
                    nh3_full_speed=str(self.nh3_fan_speeds.full_speed),
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

    def _update_chart(self, chart: ui.chart, values: list[int] | list[float]):
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
