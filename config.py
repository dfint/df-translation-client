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
