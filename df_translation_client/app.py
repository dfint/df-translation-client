import multiprocessing as mp
import os
import sys
from pathlib import Path

from async_tkinter_loop import async_mainloop

from df_translation_client.utils.config import Config
from .main_window import MainWindow


class App:
    @staticmethod
    def get_config_path():
        config_name = '.df-translate.json'
        config_path = Path(__file__).parent.parent

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

        self.main_window = MainWindow(self)

        if not ignore_config_file:
            self.setup_config_autosave(self.main_window, self.config)

    def run(self):
        async_mainloop(self.main_window)
        # self.main_window.mainloop()


def main():
    mp.freeze_support()
    App(ignore_config_file='--noconfig' in sys.argv, debug='--debug' in sys.argv).run()
