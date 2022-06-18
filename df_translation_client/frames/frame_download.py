import asyncio
import platform
import subprocess
import tkinter as tk
import traceback
from asyncio import Task
from enum import Enum
from pathlib import Path
from tkinter import ttk, messagebox
from typing import List, Optional

from async_tkinter_loop import async_handler
from tk_grid_helper import grid_manager

from df_translation_client.downloaders.abstract_downloader import AbstractDownloader
from df_translation_client.downloaders.common import StatusEnum, DownloadStage
from df_translation_client.downloaders.github import GithubDownloader
from df_translation_client.downloaders.transifex_api_2 import TransifexApiDownloader
from df_translation_client.utils.config import Config
from df_translation_client.widgets import FileEntry, TwoStateButton, ScrollbarFrame
from df_translation_client.widgets.custom_widgets import Combobox, Entry, Listbox, TypedCombobox


class DownloadFromEnum(Enum):
    GITHUB = "Github (faster, no registration, data updates at midnight GMT+00)"
    TRANSIFEX = "Transifex (slower, needs registration, up-to-date)"

    def __str__(self):
        return self.value


class DownloadTranslationsFrame(tk.Frame):
    downloader_api: Optional[AbstractDownloader] = None
    resources: Optional[List[str]] = None
    downloader_task: Optional[Task] = None

    @async_handler
    async def bt_connect(self):
        username = self.entry_username.text
        password = self.entry_password.text
        project = self.combo_projects.text

        download_from = self.combo_download_from.get()
        if download_from is DownloadFromEnum.GITHUB:
            self.downloader_api = GithubDownloader()
        else:  # DownloadFromEnum.TRANSIFEX
            if not username or not password or not project:
                messagebox.showerror("Required fields", "Fields Username, Password and Project are required")
                return

            self.downloader_api = TransifexApiDownloader(username, password, project)

        self.button_connect.config(state=tk.DISABLED)

        try:
            await self.downloader_api.connect()
            self.resources = await self.downloader_api.list_resources()
            languages = await self.downloader_api.list_languages(self.resources[0])
        except Exception as err:
            traceback.print_exc()
            messagebox.showerror("Error", str(err))
            return
        else:
            self.combo_languages.values = sorted(languages)
            last_language = self.config_section.get("language", None)

            if last_language and last_language in languages:
                self.combo_languages.text = last_language
            else:
                self.combo_languages.current(0)

            self.listbox_resources.clear()
            self.listbox_resources.values = tuple(res for res in self.resources)
        finally:
            self.button_connect.config(state=tk.ACTIVE)

        if download_from is DownloadFromEnum.TRANSIFEX:
            # Remember last successfully credentials
            self.config_section["username"] = username

            recent_projects = self.config_section["recent_projects"]
            if recent_projects or project != recent_projects[0]:
                if project in recent_projects:
                    recent_projects.remove(project)
                recent_projects.insert(0, project)
            self.combo_projects.values = recent_projects

    async def downloader(self, language: str, download_dir: Path):
        lines = {res: res for res in self.resources}  # { "resource": "resource - status" }

        file_path_pattern = str(download_dir / "{resource}_{language}.po")
        async for stage in self.downloader_api.async_downloader(
                language, self.resources, file_path_pattern
        ):
            stage: DownloadStage
            lines[stage.resource] = "{} - {}".format(stage.resource, stage.status.value)
            self.listbox_resources.values = list(lines.values())
            self.update()

            if stage.status == StatusEnum.OK:
                self.progressbar.step()
            elif stage.status == StatusEnum.FAILED:
                messagebox.showerror("Downloading error", stage.error_text)
                break
        else:
            # Everything is downloaded
            self.button_download.reset_state()

            self.config_section["language"] = language

            if platform.system() == "Windows":
                subprocess.Popen(["explorer", download_dir])
            elif platform.system() == "Darwin":
                subprocess.Popen(["open", download_dir])
            else:
                subprocess.Popen(["xdg-open", download_dir])

        self.button_download.reset_state()

    @property
    def download_started(self) -> bool:
        return self.downloader_task is not None and not self.downloader_task.done()

    def bt_download(self) -> bool:
        if not self.downloader_api:
            messagebox.showerror("Not connected", "Make connection first")
        elif self.resources is None:
            messagebox.showerror("No resources", "No resources to download")
        elif self.download_started:
            messagebox.showerror("Downloading in process", "Downloading is already started")
        if not self.fileentry_download_to.path_is_valid():
            messagebox.showerror("Directory does not exist", "Specify existing directory first")
        else:
            self.resources: List[str]
            self.progressbar["maximum"] = len(self.resources) * 1.001
            self.progressbar["value"] = 0
            self.update()

            download_dir = self.fileentry_download_to.path
            self.config_section.check_and_save_path("download_to", download_dir)

            language = self.combo_languages.get()

            self.listbox_resources.values = self.resources

            self.downloader_task: Task = asyncio.get_running_loop().create_task(
                self.downloader(language, download_dir)
            )
            return True

        return False  # Don't change state of the button

    def bt_stop_downloading(self):
        r = messagebox.showwarning("Are you sure?", "Stop downloading?", type=messagebox.OKCANCEL)
        if r == "cancel":
            return False
        else:
            if self.downloader_task is not None:
                self.downloader_task.cancel()
            return True

    def kill_background_tasks(self, _event):
        if self.downloader_task and not self.downloader_task.done():
            self.downloader_task.cancel()

    def on_combo_download_from_change(self, _event=None):
        state = tk.DISABLED if self.combo_download_from.get() is DownloadFromEnum.GITHUB else tk.NORMAL
        self.combo_projects.config(state=state)
        self.entry_username.config(state=state)
        self.entry_password.config(state=state)
        self.combo_languages.values = []
        self.listbox_resources.values = []

    def __init__(self, *args, config: Config, **kwargs):
        super().__init__(*args, **kwargs)

        self.config_section = config.init_section(
            section_name="download_translations",
            defaults=dict(recent_projects=["dwarf-fortress"])
        )

        with grid_manager(self, sticky=tk.EW, padx=2, pady=2) as grid:
            self.combo_download_from = TypedCombobox[DownloadFromEnum](values=list(DownloadFromEnum))
            self.combo_download_from.select(DownloadFromEnum.GITHUB)

            self.combo_download_from.bind("<<ComboboxSelected>>", self.on_combo_download_from_change)

            self.button_connect = ttk.Button(text="Connect...", command=self.bt_connect)
            grid.new_row() \
                .add(tk.Label(text="Download from:")) \
                .add(self.combo_download_from) \
                .add(self.button_connect, sticky=tk.NSEW).row_span(3)

            self.combo_projects = Combobox(values=self.config_section["recent_projects"])
            self.combo_projects.current(0)
            grid.new_row().add(tk.Label(text="Transifex project:")).add(self.combo_projects)

            self.entry_username = Entry()
            self.entry_username.text = self.config_section.get("username", "")
            grid.new_row().add(tk.Label(text="Username:")).add(self.entry_username)

            self.entry_password = Entry(show="•")
            grid.new_row().add(tk.Label(text="Password:")).add(self.entry_password)

            grid.new_row().add(ttk.Separator(orient=tk.HORIZONTAL)).column_span(3)

            self.combo_languages = Combobox()
            grid.new_row().add(tk.Label(text="Choose language:")).add(self.combo_languages).column_span(2)

            grid.new_row().add(ttk.Separator(orient=tk.HORIZONTAL)).column_span(3)

            self.fileentry_download_to = FileEntry(
                dialog_type="askdirectory",
                default_path=self.config_section.get("download_to", ""),
                on_change=lambda text: self.config_section.check_and_save_path("download_to", text),
            )
            grid.new_row().add(tk.Label(text="Download to:")).add(self.fileentry_download_to).column_span(2)

            self.button_download = TwoStateButton(text="Download translations", command=self.bt_download,
                                                  text2="Stop", command2=self.bt_stop_downloading)

            self.progressbar = ttk.Progressbar()

            grid.new_row().add(self.button_download).add(self.progressbar).column_span(2)

            grid.new_row().add(tk.Label(text="Resources:")).column_span(3)

            scrollbar_frame = ScrollbarFrame(widget_factory=Listbox, show_scrollbars=tk.VERTICAL)
            grid.new_row().add(scrollbar_frame, sticky=tk.NSEW).column_span(3).configure(weight=1)

            self.listbox_resources: Listbox = scrollbar_frame.widget

            grid.columnconfigure(1, weight=1)

        self.on_combo_download_from_change()
        self.bind("<Destroy>", self.kill_background_tasks)
