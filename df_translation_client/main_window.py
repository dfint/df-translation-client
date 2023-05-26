import tkinter as tk
import traceback
from tkinter import messagebox, ttk

from tkinter_layout_helpers import set_parent, pack_expanded

from df_translation_client.frames.frame_download import DownloadTranslationsFrame
from df_translation_client.frames.frame_patch import PatchExecutableFrame
from df_translation_client.frames.frame_translate_external_files import (
    TranslateExternalFiles,
)
from df_translation_client.utils.config import Config


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
            notebook.add(
                DownloadTranslationsFrame(config=config, borderwidth=3),
                text="Download translations",
            )
            notebook.add(
                PatchExecutableFrame(config=config, debug=self.app.debug, borderwidth=3),
                text="Patch executable file",
            )
            notebook.add(
                TranslateExternalFiles(config=config, borderwidth=3),
                text="Translate external text files",
            )

            tab = self.config_section.get("last_tab_opened", 0)
            if 0 <= tab < len(notebook.tabs()):
                notebook.select(tab)

            notebook.bind("<<NotebookTabChanged>>", lambda _event: self.update_selected_tab(), add=False)

            return notebook

    def report_callback_exception(self, exc, val, tb):
        if issubclass(exc, KeyboardInterrupt):
            self.quit()
            return

        super().report_callback_exception(exc, val, tb)

        filename, line, *_ = traceback.extract_tb(tb).pop()
        messagebox.showerror("Unhandled Exception", f"{exc.__name__}: {val}\n{filename}, Line: {line}")

    def __init__(self, app):
        super().__init__()
        self.geometry("800x600")
        self.app = app
        config = self.app.config
        self.config_section = config.init_section("application", dict(last_tab_opened=0))
        self.notebook = self.init_notebook(config)
        pack_expanded(self.notebook)
