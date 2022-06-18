import asyncio
import subprocess
import sys
import tkinter as tk
import traceback
from asyncio import Task
from pathlib import Path
from tkinter import ttk, messagebox
from typing import List, Optional

import requests
from async_tkinter_loop import async_handler
from transifex.api import TransifexAPI, TransifexAPIException

from df_translation_client.utils.config import Config
from df_translation_client.utils.tkinter_helpers import Grid, GridCell
from df_translation_client.widgets import FileEntry, TwoStateButton, ScrollbarFrame
from df_translation_client.widgets.custom_widgets import Combobox, Entry, Listbox


async def async_downloader(transifex_api: TransifexAPI, project: str, language: str, resources, file_path_pattern: str):
    for i, res in enumerate(resources):
        yield i, "downloading...", None
        exception_info = None
        for j in range(10, 0, -1):
            try:
                await run_in_executor(
                    transifex_api.get_translation,
                    project,
                    res["slug"],
                    language,
                    file_path_pattern.format(res["slug"])
                )
                break
            except Exception:
                yield i, f"retry... ({j})", None
                exception_info = traceback.format_exc()
        else:
            yield i, "failed", exception_info
            return
        yield i, "ok!", None

    yield None, "completed", None


async def get_transifex_connection(username, password, project):
    tx = TransifexAPI(username, password, "https://www.transifex.com")
    assert await run_in_executor(tx.ping), "No connection to the server"
    assert await run_in_executor(tx.project_exists, project), "Project %r does not exist" % project
    return tx


async def list_resources(transifex_api: TransifexAPI, project_slug: str):
    return await run_in_executor(transifex_api.list_resources, project_slug)


async def list_languages(transifex_api: TransifexAPI, project_slug: str, resource_slug: str):
    return await run_in_executor(transifex_api.list_languages, project_slug, resource_slug)


async def run_in_executor(func, *args):
    return await asyncio.get_running_loop().run_in_executor(None, func, *args)


class DownloadTranslationsFrame(tk.Frame):
    transifex_api: Optional[TransifexAPI] = None
    resources: Optional[List[dict]] = None
    downloader_task: Optional[Task] = None

    @async_handler
    async def bt_connect(self):
        username = self.entry_username.text
        password = self.entry_password.text  # DO NOT remember password (not safe)
        project = self.combo_projects.text
        if not username or not password or not project:
            messagebox.showerror("Required fields", "Fields Username, Password and Project are required")
            return

        self.button_connect.config(state=tk.DISABLED)

        try:
            self.transifex_api = await get_transifex_connection(username, password, project)
            self.resources = await list_resources(self.transifex_api, project)
            languages = await list_languages(self.transifex_api, project, self.resources[0]["slug"])
        except (TransifexAPIException, requests.exceptions.ConnectionError, AssertionError) as err:
            messagebox.showerror("Error", err)
        else:
            self.combo_languages.values = sorted(languages)
            last_language = self.config_section.get("language", None)
            if last_language and last_language in languages:
                self.combo_languages.text = last_language
            else:
                self.combo_languages.current(0)
            
            self.listbox_resources.clear()
            self.listbox_resources.values = tuple(res["name"] for res in self.resources)
            
            self.config_section["username"] = username

            recent_projects = self.config_section["recent_projects"]
            if recent_projects or project != recent_projects[0]:
                if project in recent_projects:
                    recent_projects.remove(project)
                recent_projects.insert(0, project)
            self.combo_projects.values = recent_projects
        finally:
            self.button_connect.config(state=tk.ACTIVE)

    async def downloader(self, resources, language: str, project: str, download_dir: Path,
                         initial_names=None, resource_names=None):
        if initial_names is None:
            initial_names = [res["name"] for res in self.resources]
            resource_names = initial_names.copy()

        file_path_pattern = str(download_dir / f"{{}}_{language}.po")
        async for i, message, error_text in async_downloader(self.transifex_api, project, language, resources,
                                                             file_path_pattern):
            if message == "completed":
                # Everything is downloaded
                self.button_download.reset_state()

                self.config_section["language"] = language

                if sys.platform == "win32":
                    subprocess.Popen(f'explorer "{download_dir}"')
                else:
                    pass  # Todo: open the directory in a file manager on linux
            else:
                resource_names[i] = "{} - {}".format(initial_names[i], message)
                self.listbox_resources.values = resource_names
                self.update()

                if message == "ok!":
                    self.progressbar.step()
                elif message == "failed":
                    messagebox.showerror("Downloading error", error_text)
                    break
                elif message == "stopped":
                    break
        else:
            self.button_download.reset_state()

    @property
    def download_started(self) -> bool:
        return self.downloader_task is not None and not self.downloader_task.done()

    def bt_download(self) -> bool:
        if not self.transifex_api:
            messagebox.showerror("Not connected", "Make connection first")
            return False  # Don't change the two-state button state
        elif not self.resources:
            messagebox.showerror("No resources", "No resources to download")
            return False
        elif self.download_started:
            messagebox.showerror("Downloading in process", "Downloading is already started")
            return False
        if not self.fileentry_download_to.path_is_valid():
            messagebox.showerror("Directory does not exist", "Specify existing directory first")
            return False
        else:
            self.progressbar["maximum"] = len(self.resources) * 1.001
            self.progressbar["value"] = 0
            self.update()

            download_dir = self.fileentry_download_to.path
            self.config_section.check_and_save_path("download_to", download_dir)

            project = self.combo_projects.get()
            language = self.combo_languages.get()

            initial_names = [res["name"] for res in self.resources]
            resource_names = list(initial_names)

            self.listbox_resources.values = resource_names

            self.downloader_task: Task = asyncio.get_running_loop().create_task(
                self.downloader(self.resources, language, project, download_dir)
            )
            return True

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

    def __init__(self, *args, config: Config, **kwargs):
        super().__init__(*args, **kwargs)

        self.config_section = config.init_section(
            section_name="download_translations",
            defaults=dict(recent_projects=["dwarf-fortress"])
        )

        with Grid(self, sticky=tk.EW, padx=2, pady=2) as grid:
            self.combo_projects = Combobox(values=self.config_section["recent_projects"])
            self.combo_projects.current(0)
            grid.add_row("Transifex project:", self.combo_projects)

            self.entry_username = Entry()
            self.entry_username.text = self.config_section.get("username", "")
            grid.add_row("Username:", self.entry_username)

            self.entry_password = Entry(show="•")
            grid.add_row("Password:", self.entry_password)

            self.button_connect = ttk.Button(text="Connect...", command=self.bt_connect)
            grid.add(self.button_connect, row=0, column=2, rowspan=3, sticky=tk.NSEW)

            grid.add_row(ttk.Separator(orient=tk.HORIZONTAL), ..., ...)

            self.combo_languages = Combobox()
            grid.add_row("Choose language:", self.combo_languages, ...)

            grid.add_row(ttk.Separator(orient=tk.HORIZONTAL), ..., ...)

            self.fileentry_download_to = FileEntry(
                dialog_type="askdirectory",
                default_path=self.config_section.get("download_to", ""),
                on_change=lambda text: self.config_section.check_and_save_path("download_to", text),
            )
            grid.add_row("Download to:", self.fileentry_download_to, ...)

            self.button_download = TwoStateButton(text="Download translations", command=self.bt_download,
                                                  text2="Stop", command2=self.bt_stop_downloading)

            self.progressbar = ttk.Progressbar()

            grid.add_row(self.button_download, self.progressbar, ...)

            grid.add_row(tk.Label(text="Resources:"), ..., ...)

            scrollbar_frame = ScrollbarFrame(widget_factory=Listbox, show_scrollbars=tk.VERTICAL)
            grid.add_row(GridCell(scrollbar_frame, columnspan=3, sticky=tk.NSEW)).configure(weight=1)

            self.listbox_resources: Listbox = scrollbar_frame.widget

            grid.columnconfigure(1, weight=1)

        self.bind("<Destroy>", self.kill_background_tasks)
