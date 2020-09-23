import io
import sys
import tkinter as tk
from pathlib import Path
from tkinter import ttk as ttk, messagebox

from config import Config
from frames.frame_download import DownloadTranslationsFrame
from frames.frame_patch import PatchExecutableFrame
from frames.frame_translate_external_files import TranslateExternalFiles


class MainWindow(tk.Tk):
    def save_settings_repeatedly(self, config, delay=500):
        if hasattr(self, 'notebook'):
            nb = self.notebook
            if nb.tabs():
                self.config_section['last_tab_opened'] = nb.tabs().index(nb.select())

        self.after(delay, self.save_settings_repeatedly, config, delay)
        config.save_settings()

    def init_notebook(self, config: Config):
        notebook = ttk.Notebook()
        notebook.pack(fill='both', expand=1)

        notebook.add(DownloadTranslationsFrame(notebook, config), text='Download translations')
        notebook.add(PatchExecutableFrame(notebook, config, debug=self.app.debug), text='Patch executable file')
        notebook.add(TranslateExternalFiles(notebook, config), text='Translate external text files')

        tab = self.config_section.get('last_tab_opened', 0)
        if 0 <= tab < len(notebook.tabs()):
            notebook.select(tab)

        notebook.bind('<<NotebookTabChanged>>', lambda _event: notebook.nametowidget(notebook.select()).update())

        return notebook

    def check_for_errors(self, stderr, delay=100):
        if stderr.getvalue():
            messagebox.showerror('Unhandled Exception', stderr.getvalue())
            stderr.truncate(0)
            stderr.seek(0)
        self.after(delay, self.check_for_errors, stderr, delay)

    def init_error_handler(self):
        executable = Path(sys.executable).name
        if executable.startswith('pythonw') or not executable.startswith('python'):  # if no console attached
            stderr = io.StringIO()
            sys.stderr = stderr
            self.check_for_errors(stderr)

    def __init__(self, app):
        super().__init__()
        self.app = app
        self.init_error_handler()
        config = self.app.config
        self.config_section = config.init_section('application', dict(last_tab_opened=0))
        self.notebook = self.init_notebook(config)
