import multiprocessing as mp
import sys
import os

from config import Config
from pathlib import Path
from main_window import MainWindow


class App:
    def init_config(self):
        config = Config()

        if not self.ignore_config_file:
            config_name = '.df-translate.json'
            config_path = Path(__file__).parent
            
            if not os.access(config_path, os.W_OK):
                config_path = Path.home()

            config.load_settings(config_path / config_name)

        return config

    def setup_config_autosave(self):
        if not self.ignore_config_file:
            self.window.bind('<Destroy>', lambda _: self.config.save_settings())  # Save settings on quit
            self.window.save_settings_repeatedly(self.config, delay=500)  # Save settings every 500 ms

    def __init__(self, ignore_config_file=False, debug=False):
        self.ignore_config_file = ignore_config_file
        self.debug = debug
        self.config = self.init_config()
        self.window = MainWindow(self)
        self.setup_config_autosave()
        self.window.mainloop()


if __name__ == '__main__':
    mp.freeze_support()
    App(ignore_config_file='--noconfig' in sys.argv, debug='--debug' in sys.argv)
