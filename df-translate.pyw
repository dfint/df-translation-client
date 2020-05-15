import io
import multiprocessing as mp
import sys
import tkinter as tk
import tkinter.ttk as ttk

from config import Config
from os import path
from tkinter import messagebox
from frames.frame_patch import PatchExecutableFrame
from frames.frame_download import DownloadTranslationsFrame
from frames.frame_translate_external_files import TranslateExternalFiles


class MainWindow(tk.Tk):
    def save_settings_repeatedly(self, config, delay=500):
        if hasattr(self, 'notebook'):
            nb = self.notebook
            if nb.tabs():
                config['last_tab_opened'] = nb.tabs().index(nb.select())

        self.after(delay, self.save_settings_repeatedly, config, delay)
        config.save_settings()

    def init_notebook(self, config: Config):
        notebook = self.notebook
        notebook.pack(fill='both', expand=1)

        notebook.add(DownloadTranslationsFrame(notebook, config), text='Download translations')
        notebook.add(PatchExecutableFrame(notebook, config, debug=self.app.debug), text='Patch executable file')
        notebook.add(TranslateExternalFiles(notebook, config), text='Translate external text files')

        tab = config['last_tab_opened']
        if 0 <= tab < len(notebook.tabs()):
            notebook.select(tab)

    def check_for_errors(self, stderr, delay=100):
        if stderr.getvalue():
            messagebox.showerror('Unhandled Exception', stderr.getvalue())
            stderr.truncate(0)
            stderr.seek(0)
        self.after(delay, self.check_for_errors, stderr, delay)

    def init_error_handler(self):
        executable = path.split(sys.executable)[1]
        if executable.startswith('pythonw') or not executable.startswith('python'):  # if no console attached
            stderr = io.StringIO()
            sys.stderr = stderr
            self.check_for_errors(stderr)

    def __init__(self, app):
        super().__init__()

        self.app = app

        self.init_error_handler()

        self.notebook = ttk.Notebook()


class App:
    def init_config(self, ignore_config_file):
        config_name = '.df-translate.json'
        user_directory = path.expanduser('~')

        default_config = dict(last_tab_opened=0)
        config = Config(default_config)

        if not ignore_config_file:
            config_path = path.join(user_directory, config_name)
            config.load_settings(config_path)

            self.window.bind('<Destroy>', lambda _: config.save_settings())  # Save settings on quit
            self.window.save_settings_repeatedly(config, delay=500)  # Save settings every 500 ms

        return config

    def __init__(self, ignore_config_file=False, debug=False):
        self.debug = debug
        self.window = MainWindow(self)
        self.config = self.init_config(ignore_config_file)
        self.window.init_notebook(self.config)
        self.window.mainloop()


if __name__ == '__main__':
    mp.freeze_support()
    App(ignore_config_file='--noconfig' in sys.argv, debug='--debug' in sys.argv)
