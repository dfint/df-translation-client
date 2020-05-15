import json
import os.path

from collections import defaultdict


def check_and_save_path(config, key, file_path):
    if os.path.exists(file_path):
        config[key] = file_path


def init_section(config: "Config", section_name, defaults=None):
    if not defaults:
        defaults = dict()
    section = defaults
    section.update(config[section_name])
    config[section_name] = section
    return section


class Config:
    def __init__(self, defaults=None, config_path=None):
        self.config = defaultdict(dict)
        if defaults is not None:
            self.config.update(defaults)

        self.config_path = config_path

    def save_settings(self):
        with open(self.config_path, 'w', encoding='utf-8') as config_file:
            json.dump(self.config, config_file, indent=4, sort_keys=True)

    def load_settings(self, config_path=None):
        if config_path is None:
            config_path = self.config_path
        else:
            self.config_path = config_path

        try:
            with open(config_path, encoding='utf-8') as config_file:
                self.config.update(json.load(config_file))
        except (FileNotFoundError, ValueError):
            pass

    def __getitem__(self, key):
        return self.config[key]

    def __setitem__(self, key, value):
        self.config[key] = value
