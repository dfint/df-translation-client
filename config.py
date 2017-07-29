import os.path


def check_and_save_path(config, key, file_path):
    if os.path.exists(file_path):
        config[key] = file_path
