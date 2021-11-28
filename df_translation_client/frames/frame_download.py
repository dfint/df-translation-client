import multiprocessing as mp
import subprocess
import sys
import tkinter as tk
import traceback
from pathlib import Path
from tkinter import ttk, messagebox

import requests
from transifex.api import TransifexAPI, TransifexAPIException

from df_translation_client.config import Config
from df_translation_client.tkinter_helpers import Grid, GridCell
from df_translation_client.widgets import FileEntry, TwoStateButton, ScrollbarFrame
from df_translation_client.widgets.custom_widgets import Combobox, Entry, Listbox


def downloader(conn, tx: TransifexAPI, project: str, language: str, resources, file_path_pattern: str):
    exception_info = "Everything is ok! (If you see this message, contact the developer)"
    for i, res in enumerate(resources):
        conn.send((i, "downloading..."))
        for j in range(10, 0, -1):
            try:
                tx.get_translation(project, res["slug"], language, file_path_pattern.format(res["slug"]))
                break
            except Exception:
                conn.send((i, f"retry... ({j})"))
                exception_info = traceback.format_exc()
        else:
            conn.send((i, "failed"))
            conn.send(exception_info)
            return
        conn.send((i, "ok!"))
    conn.send((None, "completed"))


class DownloadTranslationsFrame(tk.Frame):
    def bt_connect(self):
        username = self.entry_username.text
        password = self.entry_password.text  # DO NOT remember password (not safe)
        project = self.combo_projects.text
        try:
            # Todo: make connection in separate thread
            self.tx = TransifexAPI(username, password, "https://www.transifex.com")
            assert self.tx.ping(), "No connection to the server"
            assert self.tx.project_exists(project), "Project %r does not exist" % project
            self.resources = self.tx.list_resources(project)
            languages = self.tx.list_languages(project, resource_slug=self.resources[0]["slug"])
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

    def download_waiter(self, resources, language: str, project: str, download_dir: Path, parent_conn=None,
                        initial_names=None, resource_names=None, i=0):
        if initial_names is None:
            initial_names = [res["name"] for res in self.resources]
            resource_names = initial_names.copy()

        if self.download_process is None:
            parent_conn, child_conn = mp.Pipe()

            self.download_process = mp.Process(
                target=downloader,
                kwargs=dict(
                    conn=child_conn,
                    tx=self.tx,
                    project=project,
                    language=language,
                    resources=resources,
                    file_path_pattern=str(download_dir / f"{{}}_{language}.po")
                )
            )
            self.download_process.start()

        while parent_conn.poll() or not self.download_process.is_alive():
            if parent_conn.poll():
                i, message = parent_conn.recv()
            else:
                i, message = i, "stopped"

            if message == "completed":
                # Everything is downloaded
                self.download_process.join()
                self.download_process = None
                self.button_download.reset_state()
                self.download_started = False

                self.config_section["language"] = language

                if sys.platform == "win32":
                    subprocess.Popen(f'explorer "{download_dir}"')
                else:
                    pass  # Todo: open the directory in a file manager on linux

                return

            resource_names[i] = "{} - {}".format(initial_names[i], message)
            self.listbox_resources.values = resource_names
            self.update()

            if message == "ok!":
                self.progressbar.step()
                break
            elif message == "failed":
                error = parent_conn.recv()
                self.download_process.join()
                self.download_process = None
                self.button_download.reset_state()
                self.download_started = False
                messagebox.showerror("Downloading error", error)
                return
            elif message == "stopped":
                self.download_process = None
                self.button_download.reset_state()
                self.download_started = False
                return

        self.after(100, self.download_waiter,
                   resources, language, project, download_dir,
                   parent_conn, initial_names, resource_names, i)
    
    def bt_download(self):
        if self.tx and self.resources and not self.download_started:
            self.progressbar["maximum"] = len(self.resources) * 1.001
            self.progressbar["value"] = 0

            if not self.fileentry_download_to.path_is_valid():
                messagebox.showerror("Directory does not exist", "Specify existing directory first")
                return

            download_dir = self.fileentry_download_to.path
            self.config_section.check_and_save_path("download_to", download_dir)

            project = self.combo_projects.get()
            language = self.combo_languages.get()
            
            initial_names = [res["name"] for res in self.resources]
            resource_names = list(initial_names)
            
            self.listbox_resources.values = resource_names
            self.download_started = True
            self.download_waiter(self.resources, language, project, download_dir)
            return True

    def bt_stop_downloading(self):
        r = messagebox.showwarning("Are you sure?", "Stop downloading?", type=messagebox.OKCANCEL)
        if r == "cancel":
            return False
        else:
            self.download_process.terminate()
            return True

    def kill_processes(self, _):
        if self.download_process and self.download_process.is_alive():
            self.download_process.terminate()

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

            button_connect = ttk.Button(text="Connect...", command=self.bt_connect)
            grid.add(button_connect, row=0, column=2, rowspan=3, sticky=tk.NSEW)

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

        self.resources = None
        self.tx = None
        self.download_started = False
        self.download_process = None

        self.bind("<Destroy>", self.kill_processes)
