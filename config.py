import json
import os.path


def check_and_save_path(config, key, file_path):
    if os.path.exists(file_path):
        config[key] = file_path


def init_section(config, section_name, defaults=None):
    if not defaults:
        defaults = dict()
    section = defaults
    section.update(config.get(section_name, dict()))
    config[section_name] = section
    return section


def save_settings(config, config_path):
    with open(config_path, 'w', encoding='utf-8') as config_file:
        json.dump(config, config_file, indent=4, sort_keys=True)


def load_settings(config_path, defaults=None):
    if not defaults:
        defaults = dict()

    config = defaults

    try:
        with open(config_path, encoding='utf-8') as config_file:
            config.update(json.load(config_file))
    except (FileNotFoundError, ValueError):
        pass

    return config


class Config:
    def __init__(self, defaults=None, config_path=None):
        if not defaults:
            defaults = dict()

        self.config = defaults
        self.config_path = config_path

    @classmethod
    def load_settings(cls, config_path, defaults=None):
        if not defaults:
            defaults = dict()

        config = cls(defaults)

        try:
            with open(config_path, encoding='utf-8') as config_file:
                config.update(json.load(config_file))
        except (FileNotFoundError, ValueError):
            pass

        return config

    def save_settings(self, config_path=None):
        if not config_path:
            config_path = self.config_path
            assert config_path, 'Config path must be specified to save config'

        with open(config_path, 'w', encoding='utf-8') as config_file:
            json.dump(self.config, config_file, indent=4, sort_keys=True)

    def update(self, other):
        self.config.update(other)

    def __getitem__(self, item):
        return self.config[item]

    def __setitem__(self, key, value):
        self.config[key] = value
