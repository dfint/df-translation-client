import tkinter as tk
import traceback
from tkinter import ttk as ttk, messagebox

from config import Config
from frames.frame_download import DownloadTranslationsFrame
from frames.frame_patch import PatchExecutableFrame
from frames.frame_translate_external_files import TranslateExternalFiles
from tkinter_helpers import pack_expand


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
        pack_expand(notebook)

        notebook.add(DownloadTranslationsFrame(notebook, config), text='Download translations')
        notebook.add(PatchExecutableFrame(notebook, config, debug=self.app.debug), text='Patch executable file')
        notebook.add(TranslateExternalFiles(notebook, config), text='Translate external text files')

        tab = self.config_section.get('last_tab_opened', 0)
        if 0 <= tab < len(notebook.tabs()):
            notebook.select(tab)

        notebook.bind('<<NotebookTabChanged>>', lambda _event: notebook.nametowidget(notebook.select()).update())

        return notebook

    def report_callback_exception(self, exc_type, exc_value, exc_traceback):
        if issubclass(exc_type, KeyboardInterrupt):
            self.quit()
            return

        super().report_callback_exception(exc_type, exc_value, exc_traceback)

        filename, line, *_ = traceback.extract_tb(exc_traceback).pop()
        message = '{}: {}\n{}, Line: {}\n'.format(exc_type.__name__, exc_value, filename, line)
        messagebox.showerror('Unhandled Exception', message)

    def __init__(self, app):
        super().__init__()
        self.app = app
        config = self.app.config
        self.config_section = config.init_section('application', dict(last_tab_opened=0))
        self.notebook = self.init_notebook(config)
