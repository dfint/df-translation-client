import multiprocessing as mp
import tkinter as tk
import tkinter.ttk as ttk
import traceback
import subprocess
import sys
import requests

from config import check_and_save_path, init_section
from custom_widgets import ComboboxCustom, EntryCustom, FileEntry, TwoStateButton, ListboxCustom
from os import path
from tkinter import messagebox
from transifex.api import TransifexAPI, TransifexAPIException


def downloader(conn, tx, project, language, resources, file_path_pattern):
    exception_info = 'Everything is ok! (If you see this message, contact the developer)'
    for i, res in enumerate(resources):
        conn.send((i, 'downloading...'))
        for j in range(10):
            try:
                tx.get_translation(project, res['slug'], language, file_path_pattern % res['slug'])
                break
            except:
                conn.send((i, 'retry... (%d)' % (10 - j)))
                exception_info = traceback.format_exc()
        else:
            conn.send((i, 'failed'))
            conn.send(exception_info)
            return
        conn.send((i, 'ok!'))
    conn.send((None, 'completed'))


class DownloadTranslationsFrame(tk.Frame):
    def bt_connect(self):
        username = self.entry_username.text
        password = self.entry_password.text  # DO NOT remember password (not safe)
        project = self.combo_projects.text
        try:
            # Todo: make connection in separate thread
            self.tx = TransifexAPI(username, password, 'https://www.transifex.com')
            assert self.tx.ping(), 'No connection to the server'
            assert self.tx.project_exists(project), "Project %r does not exist" % project
            self.resources = self.tx.list_resources(project)
            languages = self.tx.list_languages(project, resource_slug=self.resources[0]['slug'])
        except (TransifexAPIException, requests.exceptions.ConnectionError, AssertionError) as err:
            messagebox.showerror('Error', err)
        except:
            messagebox.showerror('Unexpected error', traceback.format_exc())
        else:
            self.combo_languages.values = sorted(languages)
            last_language = self.config.get('language', None)
            if last_language and last_language in languages:
                self.combo_languages.text = last_language
            else:
                self.combo_languages.current(0)
            
            self.listbox_resources.clear()
            self.listbox_resources.values = tuple(res['name'] for res in self.resources)
            
            self.config['username'] = username

            recent_projects = self.config['recent_projects']
            if recent_projects or project != recent_projects[0]:
                if project in recent_projects:
                    recent_projects.remove(project)
                recent_projects.insert(0, project)
            self.combo_projects.values = recent_projects

    def download_waiter(self, resources, language, project, download_dir, parent_conn=None,
                        initial_names=None, resource_names=None, i=0):
        if initial_names is None:
            initial_names = [res['name'] for res in self.resources]
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
                    file_path_pattern=path.join(download_dir, '%s_' + language + '.po')
                )
            )
            self.download_process.start()

        while parent_conn.poll() or not self.download_process.is_alive():
            if parent_conn.poll():
                i, message = parent_conn.recv()
            else:
                i, message = i, 'stopped'

            if message == 'completed':
                # Everything is downloaded
                self.download_process.join()
                self.download_process = None
                self.button_download.reset_state()
                self.download_started = False

                self.config['language'] = language

                if sys.platform == 'win32':
                    subprocess.Popen('explorer "%s"' % (download_dir.replace('/', '\\')))
                else:
                    pass  # Todo: open the directory in a file manager on linux

                return

            resource_names[i] = '{} - {}'.format(initial_names[i], message)
            self.listbox_resources.values = resource_names
            self.update()

            if message == 'ok!':
                self.progressbar.step()
                break
            elif message == 'failed':
                error = parent_conn.recv()
                self.download_process.join()
                self.download_process = None
                self.button_download.reset_state()
                self.download_started = False
                messagebox.showerror('Downloading error', error)
                return
            elif message == 'stopped':
                self.download_process = None
                self.button_download.reset_state()
                self.download_started = False
                return

        self.after(100, self.download_waiter,
                   resources, language, project, download_dir,
                   parent_conn, initial_names, resource_names, i)
    
    def bt_download(self):
        if self.tx and self.resources and not self.download_started:
            self.progressbar['maximum'] = len(self.resources) * 1.001
            self.progressbar['value'] = 0
            
            download_dir = self.fileentry_download_to.text
            if not download_dir:
                messagebox.showwarning('Directory not specified', 'Specify download directory first')
                return
            else:
                self.config['download_to'] = download_dir
            
            if not path.exists(download_dir):
                messagebox.showerror('Directory does not exist', 'Specify existing directory first')
                return
            
            project = self.combo_projects.get()
            language = self.combo_languages.get()
            
            initial_names = [res['name'] for res in self.resources]
            resource_names = list(initial_names)
            
            self.listbox_resources.values = resource_names
            self.download_started = True
            self.download_waiter(self.resources, language, project, download_dir)
            return True

    def bt_stop_downloading(self):
        r = messagebox.showwarning('Are you sure?', 'Stop downloading?', type=messagebox.OKCANCEL)
        if r == 'cancel':
            return False
        else:
            self.download_process.terminate()
            return True

    def kill_processes(self, _):
        if self.download_process and self.download_process.is_alive():
            self.download_process.terminate()

    def __init__(self, master=None, config=None):
        super().__init__(master)
        
        self.config = init_section(
            config, section_name='download_translations',
            defaults=dict(recent_projects=['dwarf-fortress'])
        )

        tk.Label(self, text='Transifex project:').grid()

        self.combo_projects = ComboboxCustom(self, values=self.config['recent_projects'])
        self.combo_projects.current(0)
        self.combo_projects.grid(column=1, row=0, sticky=tk.W + tk.E)
        
        tk.Label(self, text='Username:').grid(column=0, row=1)
        
        self.entry_username = EntryCustom(self)
        self.entry_username.text = self.config.get('username', '')
        self.entry_username.grid(column=1, row=1, sticky=tk.W + tk.E)
        
        tk.Label(self, text='Password:').grid(column=0, row=2)
        
        self.entry_password = EntryCustom(self, show='\u2022')  # 'bullet' symbol
        self.entry_password.grid(column=1, row=2, sticky=tk.W + tk.E)
        
        button_connect = ttk.Button(self, text='Connect...', command=self.bt_connect)
        button_connect.grid(row=0, column=2, rowspan=3, sticky=tk.N + tk.S + tk.W + tk.E)
        
        ttk.Separator(self, orient=tk.HORIZONTAL).grid(columnspan=3, sticky=tk.W + tk.E, pady=5)
        
        tk.Label(self, text='Choose language:').grid(column=0)
        
        self.combo_languages = ComboboxCustom(self)
        self.combo_languages.grid(column=1, row=4, sticky=tk.W + tk.E)
        
        # self.chk_all_languages = CheckbuttonVar(self, text='All languages (backup)')
        # self.chk_all_languages.grid(column=1)
        
        ttk.Separator(self, orient=tk.HORIZONTAL).grid(columnspan=3, sticky=tk.W + tk.E, pady=5)
        
        tk.Label(self, text='Download to:').grid()
        
        self.fileentry_download_to = FileEntry(
            self,
            dialogtype='askdirectory',
            default_path=self.config.get('download_to', ''),
            on_change=lambda text: check_and_save_path(self.config, 'download_to', text),
        )
        
        self.fileentry_download_to.grid(column=1, row=6, columnspan=2, sticky='WE')
        
        self.button_download = TwoStateButton(self, text='Download translations', command=self.bt_download,
                                              text2='Stop', command2=self.bt_stop_downloading)
        self.button_download.grid(sticky=tk.W + tk.E)
        
        self.progressbar = ttk.Progressbar(self)
        self.progressbar.grid(column=1, row=7, columnspan=2, sticky=tk.W + tk.E)
        
        tk.Label(self, text='Resources:').grid(columnspan=3)

        self.listbox_resources = ListboxCustom(self)
        self.listbox_resources.grid(column=0, columnspan=3, sticky=tk.E + tk.W + tk.N + tk.S)

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(9, weight=1)

        self.resources = None
        self.tx = None
        self.download_started = False
        self.download_process = None

        self.bind('<Destroy>', self.kill_processes)
