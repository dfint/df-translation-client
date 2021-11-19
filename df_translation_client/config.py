import json
from collections import defaultdict
from pathlib import Path


class ConfigSection(dict):
    def check_and_save_path(self, key, file_path):
        if Path(file_path).exists():
            self[key] = str(file_path)


class Config:
    def __init__(self, config_path=None):
        self._sections = defaultdict(ConfigSection)
        self.config_path = config_path

    def save_settings(self):
        with open(self.config_path, 'w', encoding='utf-8') as config_file:
            json.dump({key: dict(section) for key, section in self._sections.items()
                       if isinstance(section, dict)},  # ignore non-dict values (to avoid errors with old config)
                      config_file, indent=4, sort_keys=True)

    def load_settings(self, config_path=None):
        if config_path is None:
            config_path = self.config_path
        else:
            self.config_path = config_path

        try:
            with open(config_path, encoding='utf-8') as config_file:
                self._sections.update(json.load(config_file))
        except (FileNotFoundError, ValueError):
            pass

    def init_section(self, section_name, defaults: dict = None) -> ConfigSection:
        if not defaults:
            defaults = dict()
        section = ConfigSection(defaults)
        section.update(self._sections[section_name])
        self._sections[section_name] = section
        return section
