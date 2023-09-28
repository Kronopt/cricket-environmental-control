import configparser
import logging
import os
import shutil
import threading
import typing


class Configurations(configparser.ConfigParser):
    def __init__(self):
        super().__init__()
        self._logger = logging.getLogger("services." + self.__class__.__name__)
        self._lock = threading.Lock()

        # path in relation to main.py
        self._default_config_file = "default_configs.ini"
        self.config_file = "configs.ini"

        self._logger.info("reading configs...")
        self._generate_config_file()
        self.read(self.config_file)

    def set(self, section: str, option: str, value: str):
        threading.Thread(target=self._set, args=(section, option, value)).start()

    def set_multiple(self, options: typing.Sequence[typing.Tuple[str, str, str]]):
        threading.Thread(target=self._set_multiple, args=(options,)).start()

    def _set(self, section: str, option: str, value: str):
        with self._lock:
            super().set(section, option, value)

            with open(self.config_file, "w") as configfile:
                self.write(configfile)

    def _set_multiple(self, options: typing.Sequence[typing.Tuple[str, str, str]]):
        with self._lock:
            for option in options:
                super().set(option[0], option[1], option[2])

                with open(self.config_file, "w") as configfile:
                    self.write(configfile)

    def _generate_config_file(self):
        """looks for configs.ini. copies config from default_configs.ini if not found"""
        if not os.path.isfile(self.config_file):
            self._logger.debug("generating config file from default configs...")
            shutil.copyfile(self._default_config_file, self.config_file)
