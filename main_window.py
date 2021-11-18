import tkinter as tk
import traceback
from tkinter import ttk as ttk, messagebox

from config import Config
from frames.frame_download import DownloadTranslationsFrame
from frames.frame_patch import PatchExecutableFrame
from frames.frame_translate_external_files import TranslateExternalFiles
from tkinter_helpers import pack_expand, set_parent


class MainWindow(tk.Tk):
    def save_settings_repeatedly(self, config, delay=500):
        if hasattr(self, "notebook"):
            nb = self.notebook
            if nb.tabs():
                self.config_section["last_tab_opened"] = nb.tabs().index(nb.select())

        self.after(delay, self.save_settings_repeatedly, config, delay)
        config.save_settings()

    def update_selected_tab(self):
        selected_tab_name = self.notebook.select()
        selected_tab = self.notebook.nametowidget(selected_tab_name)
        selected_tab.update()

    def init_notebook(self, config: Config) -> ttk.Notebook:
        with set_parent(ttk.Notebook(self)) as notebook:
            notebook.add(DownloadTranslationsFrame(config=config, borderwidth=3),
                         text="Download translations")
            notebook.add(PatchExecutableFrame(config=config, debug=self.app.debug, borderwidth=3),
                         text="Patch executable file")
            notebook.add(TranslateExternalFiles(config=config, borderwidth=3),
                         text="Translate external text files")

            tab = self.config_section.get("last_tab_opened", 0)
            if 0 <= tab < len(notebook.tabs()):
                notebook.select(tab)

            notebook.bind("<<NotebookTabChanged>>", lambda _event: self.update_selected_tab())

            return notebook

    def report_callback_exception(self, exc_type, exc_value, exc_traceback):
        if issubclass(exc_type, KeyboardInterrupt):
            self.quit()
            return

        super().report_callback_exception(exc_type, exc_value, exc_traceback)

        filename, line, *_ = traceback.extract_tb(exc_traceback).pop()
        messagebox.showerror(
            "Unhandled Exception",
            f"{exc_type.__name__}: {exc_value}\n"
            f"{filename}, Line: {line}"
        )

    def __init__(self, app):
        super().__init__()
        self.app = app
        config = self.app.config
        self.config_section = config.init_section("application", dict(last_tab_opened=0))
        self.notebook = self.init_notebook(config)
        pack_expand(self.notebook)
