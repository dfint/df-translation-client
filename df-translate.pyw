import multiprocessing as mp
import sys
import os

from config import Config
from pathlib import Path
from main_window import MainWindow


class App:
    @staticmethod
    def get_config_path():
        config_name = '.df-translate.json'
        config_path = Path(__file__).parent

        if not os.access(config_path, os.W_OK):
            config_path = Path.home()

        return config_path / config_name

    @staticmethod
    def setup_config_autosave(window: MainWindow, config: Config):
        window.bind('<Destroy>', lambda _: config.save_settings())  # Save settings on quit
        window.save_settings_repeatedly(config, delay=500)  # Save settings every 500 ms

    def __init__(self, ignore_config_file=False, debug=False):
        self.debug = debug

        self.config = Config()

        if not ignore_config_file:
            self.config.load_settings(self.get_config_path())

        main_window = MainWindow(self)

        if not ignore_config_file:
            self.setup_config_autosave(main_window, self.config)

        main_window.mainloop()


if __name__ == '__main__':
    mp.freeze_support()
    App(ignore_config_file='--noconfig' in sys.argv, debug='--debug' in sys.argv)
