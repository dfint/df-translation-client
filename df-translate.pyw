import io
import multiprocessing as mp
import sys
import tkinter as tk
import tkinter.ttk as ttk

from config import save_settings, load_settings
from os import path
from tkinter import messagebox
from frame_patch import PatchExecutableFrame
from frame_download import DownloadTranslationsFrame
from frame_translate_external_files import TranslateExternalFiles


class App(tk.Tk):
    def save_settings_repeatedly(self, config, config_path, delay=500):
        if hasattr(self, 'notebook'):
            nb = self.notebook
            if nb.tabs():
                self.config['last_tab_opened'] = nb.tabs().index(nb.select())
        
        self.after(delay, self.save_settings_repeatedly, config, config_path, delay)
        save_settings(config, config_path)

    def check_for_errors(self, delay=100):
        if self.stderr.getvalue():
            messagebox.showerror('Unhandled Exception', self.stderr.getvalue())
            self.stderr.truncate(0)
            self.stderr.seek(0)
        self.after(delay, self.check_for_errors, delay)

    def init_config(self, noconfig):
        config_name = '.df-translate.json'
        userdir = path.expanduser('~')
        config_path = path.join(userdir, config_name)
        config = dict(last_tab_opened=0)

        if not noconfig:
            config = load_settings(config_path, defaults=config)
            self.bind('<Destroy>', lambda _: save_settings(config, config_path))  # Save settings on quit
            self.save_settings_repeatedly(config, config_path, delay=500)  # Save settings every 500 ms

        return config, config_path

    def __init__(self, noconfig=False, debug=False):
        super().__init__()

        executable = path.split(sys.executable)[1]
        if executable.startswith('pythonw') or not executable.startswith('python'):  # if no console attached
            self.stderr = io.StringIO()
            sys.stderr = self.stderr
            self.check_for_errors()

        self.config, self.config_path = self.init_config(noconfig)

        self.notebook = ttk.Notebook()
        notebook = self.notebook
        notebook.pack(fill='both', expand=1)

        notebook.add(DownloadTranslationsFrame(notebook, self.config),
                     text='Download translations')

        notebook.add(PatchExecutableFrame(notebook, self.config, debug=debug),
                     text='Patch executable file')

        notebook.add(TranslateExternalFiles(notebook, self.config),
                     text='Translate external text files')

        tab = self.config['last_tab_opened']
        if 0 <= tab < len(notebook.tabs()):
            notebook.select(tab)


if __name__ == '__main__':
    mp.freeze_support()
    App(noconfig='--noconfig' in sys.argv, debug='--debug' in sys.argv).mainloop()
