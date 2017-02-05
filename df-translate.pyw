import requests
import sys
import tkinter as tk
import tkinter.ttk as ttk
import string
import subprocess
import json

from dfrus.patchdf import codepages
from os import path
from tkinter import filedialog, messagebox
from transifex.api import TransifexAPI, TransifexAPIException
from custom_widgets import CheckbuttonVar, EntryCustom, ComboboxCustom


class DownloadTranslationsFrame(tk.Frame):
    def init_config(self):
        config = self.app.config
        
        if 'download_translations' not in config:
            config['download_translations'] = dict()
        
        config = config['download_translations']
        if 'recent_projects' not in config:
            config['recent_projects'] = ['dwarf-fortress']
        
        if 'download_to' not in config:
            config['download_to'] = None

        config['language'] = config.get('language', None)

        return config
    
    def bt_connect(self, _):
        username = self.entry_username.text
        password = self.entry_password.text  # DO NOT remember password (not safe)
        project = self.combo_projects.text
        try:
            # Todo: make connection in separate thread
            self.tx = TransifexAPI(username, password, 'http://transifex.com')
            assert self.tx.project_exists(project), "Project %r does not exist" % project
            self.resources = self.tx.list_resources(project)
            languages = self.tx.list_languages(project, resource_slug=self.resources[0]['slug'])
        except (TransifexAPIException, requests.exceptions.ConnectionError, AssertionError) as err:
            messagebox.showerror('Error', err)
        except:
            messagebox.showerror('Unexpected error', repr(sys.exc_info()[0]))
        else:
            self.combo_languages.values = tuple(languages)
            last_language = self.config['language']
            self.combo_languages.current(languages.index(last_language) if last_language in languages else 0)
            
            self.listbox_resources.delete(0, tk.END)
            self.listbox_resources_var.set(tuple(res['name'] for res in self.resources))
            
            self.config['username'] = username

            recent_projects = self.config['recent_projects']
            if recent_projects or project != recent_projects[0]:
                if project in recent_projects:
                    recent_projects.remove(project)
                recent_projects.insert(0, project)
            self.combo_projects.values = tuple(recent_projects)
    
    def bt_download(self, _):
        if self.tx and self.resources:
            self.progressbar['maximum'] = len(self.resources) * 1.001
            self.progressbar['value'] = 0
            
            download_dir = self.entry_download_to.get()
            if not download_dir:
                messagebox.showwarning('Directory not specified', 'Specify download directory first')
                return
            else:
                self.config['download_to'] = download_dir
            
            project = self.combo_projects.get()
            language = self.combo_languages.get()
            
            initial_names = [res['name'] for res in self.resources]
            resource_names = list(initial_names)
            
            self.listbox_resources_var.set(tuple(resource_names))
            for i, res in enumerate(self.resources):
                resource_names[i] = initial_names[i] + ' - downloading...'
                self.listbox_resources_var.set(tuple(resource_names))
                self.app.update()
                
                file_path = path.join(download_dir, '%s_%s.po' % (res['slug'], language))
                
                error = None
                for j in range(10):
                    try:
                        self.tx.get_translation(project, res['slug'], language, file_path)
                        break
                    except:
                        resource_names[i] = initial_names[i] + ' - retry... (%d)' % (10 - j)
                        self.listbox_resources_var.set(tuple(resource_names))
                        self.app.update()
                        error = sys.exc_info()[0]
                else:
                    resource_names[i] = initial_names[i] + ' - failed'
                    self.listbox_resources_var.set(tuple(resource_names))
                    self.app.update()
                    messagebox.showerror('Downloading error', error)
                    break
                
                resource_names[i] = initial_names[i] + ' - ok!'
                self.listbox_resources_var.set(tuple(resource_names))
                self.progressbar.step()
                self.app.update()

            self.config['language'] = language

            if sys.platform == 'win32':
                subprocess.Popen('explorer "%s"' % (download_dir.replace('/', '\\')))
            else:
                pass  # Todo: open the directory in a file manager on linux
    
    def bt_choose_directory(self, _):
        download_path = filedialog.askdirectory()
        if download_path:
            self.entry_download_to.text = download_path
            self.config['download_to'] = download_path
    
    def __init__(self, master=None, app=None):
        super().__init__(master)
        
        self.app = app
        
        self.config = self.init_config()
        
        tk.Label(self, text='Transifex project:').grid()

        self.combo_projects = ComboboxCustom(self, values=self.config['recent_projects'])
        self.combo_projects.current(0)
        self.combo_projects.grid(column=1, row=0)
        
        tk.Label(self, text='Username:').grid(column=0, row=1)
        
        self.entry_username = EntryCustom(self)
        self.entry_username.text = self.config.get('username', '')
        self.entry_username.grid(column=1, row=1, sticky=tk.W + tk.E)
        
        tk.Label(self, text='Password:').grid(column=0, row=2)
        
        self.entry_password = EntryCustom(self, show='\u2022')  # 'bullet' symbol
        self.entry_password.grid(column=1, row=2, sticky=tk.W + tk.E)
        
        button_connect = ttk.Button(self, text='Connect...')
        button_connect.grid(row=0, column=2, rowspan=3, sticky=tk.N + tk.S + tk.W + tk.E)
        button_connect.bind('<1>', self.bt_connect)
        
        ttk.Separator(self, orient=tk.HORIZONTAL).grid(columnspan=3, sticky=tk.W + tk.E, pady=5)
        
        tk.Label(self, text='Choose language:').grid(column=0)
        
        self.combo_languages = ComboboxCustom(self)
        self.combo_languages.grid(column=1, row=4, sticky=tk.W + tk.E)
        
        # self.chk_all_languages = CheckbuttonVar(self, text='All languages (backup)')
        # self.chk_all_languages.grid(column=1)
        
        ttk.Separator(self, orient=tk.HORIZONTAL).grid(columnspan=3, sticky=tk.W + tk.E, pady=5)
        
        tk.Label(self, text='Download to:').grid()
        
        self.entry_download_to = EntryCustom(self)
        self.entry_download_to.grid(column=1, row=6, sticky=tk.W + tk.E)
        self.entry_download_to.text = self.config['download_to'] or ''
        
        button_choose_directory = ttk.Button(self, text='Choose directory...')
        button_choose_directory.grid(column=2, row=6)
        button_choose_directory.bind('<1>', self.bt_choose_directory)
        
        self.button_download = ttk.Button(self, text='Download translations')
        self.button_download.bind('<1>', self.bt_download)
        self.button_download.grid(sticky=tk.W + tk.E)
        
        self.progressbar = ttk.Progressbar(self)
        self.progressbar.grid(column=1, row=7, columnspan=2, sticky=tk.W + tk.E)
        
        tk.Label(self, text='Resources:').grid(columnspan=3)
        
        self.listbox_resources_var = tk.Variable()
        self.listbox_resources = tk.Listbox(self, listvariable=self.listbox_resources_var)
        self.listbox_resources.grid(column=0, columnspan=3, sticky=tk.E + tk.W)
        
        self.resources = None
        self.tx = None


class DialogDontFixSpaces(tk.Toplevel):
    def combo_language_change_selection(self, _):
        self.listbox_exclusions_var.set(tuple(self.exclusions.get(self.combo_language.text, tuple())))

    def __init__(self, parent, exclusions, languages: list, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.grab_set()

        self.exclusions = exclusions

        self.title("Choose exclusions")

        language_list = list(self.exclusions)
        if any(x in language_list for x in languages):
            for item in languages:
                language_list.remove(item)
        language_list = languages + language_list

        self.combo_language = ComboboxCustom(self, values=language_list)
        self.combo_language.grid()
        self.combo_language.current(0)
        self.combo_language.bind('<<ComboboxSelected>>', self.combo_language_change_selection)

        bt = ttk.Button(self, text='-- Remove selected --')
        bt.grid(column=0, row=1, sticky=tk.N)

        self.listbox_exclusions_var = tk.Variable()
        self.listbox_exclusions = tk.Listbox(self, listvariable=self.listbox_exclusions_var)
        self.listbox_exclusions.grid(sticky='NSWE')
        self.listbox_exclusions_var.set(tuple(self.exclusions.get(self.combo_language.text, tuple())))

        self.entry_search = ttk.Entry(self)
        self.entry_search.grid(column=1, row=0)

        bt = ttk.Button(self, text='<< Add selected <<')
        bt.grid(column=1, row=1, sticky=tk.N)

        self.listbox_exclusions_hints_var = tk.Variable()
        self.listbox_exclusions_hints = tk.Listbox(self, listvariable=self.listbox_exclusions_hints_var)
        self.listbox_exclusions_hints.grid(column=1, row=2, sticky=tk.N + tk.S)

        button = ttk.Button(self, text="OK", command=self.destroy)
        button.grid(row=3, column=0)

        def cancel(_):
            self.exclusions = None
            self.destroy()

        button = ttk.Button(self, text="Cancel", command=cancel)
        button.grid(row=3, column=1)


class PatchExecutableFrame(tk.Frame):
    def init_config(self):
        config = self.app.config

        if 'patch_executable' not in config:
            config['patch_executable'] = dict()

        config = config['patch_executable']

        if 'fix_space_exclusions' not in config:
            config['fix_space_exclusions'] = dict(ru=['Histories of '])

        config['df_executable'] = config.get('df_executable', None)

        config['df_exe_translation_file'] = config.get('df_exe_translation_file', None)

        return config

    def bt_browse_executable(self, _):
        file_path = filedialog.askopenfilename(filetypes=[('Executable files', '*.exe')])
        if file_path:
            self.entry_executable_file.text = file_path
            self.config['df_executable'] = file_path
    
    def bt_browse_translation(self, _):
        file_path = filedialog.askopenfilename(filetypes=[
            ("Hardcoded strings' translation", '*hardcoded*.po'),
            ('Translation files', '*.po'),
            ('csv file', '*.csv'),
        ])
        if file_path:
            self.entry_translation_file.text = file_path
            self.config['df_exe_translation_file'] = file_path

    def check_and_save_path(self, key, file_path):
        if path.exists(file_path):
            self.config[key] = file_path

    def bt_patch(self, _):
        executable_file = self.entry_executable_file.get()
        translation_file = self.entry_translation_file.get()
        
        if not executable_file:
            messagebox.showerror('Error', 'Executable file path must be specified')
        elif not translation_file:
            messagebox.showerror('Error', 'Translation file path must be specified')
        else:
            pass
    
    def bt_exclusions(self, _):
        dialog = DialogDontFixSpaces(self, self.config['fix_space_exclusions'], [])
        self.config['fix_space_exclusions'] = dialog.exclusions or self.config['fix_space_exclusions']

    def __init__(self, master=None, app=None):
        super().__init__(master)
        
        self.app = app

        self.config = self.init_config()
        
        tk.Label(self, text='DF executable file:').grid()
        
        self.entry_executable_file = EntryCustom(self)
        self.entry_executable_file.grid(column=1, row=0, sticky=tk.E + tk.W)
        self.entry_executable_file.text = self.config['df_executable'] or ''
        self.entry_executable_file.bind('<KeyPress>',
                                        func=lambda event:
                                            self.check_and_save_path('df_executable', event.widget.text))

        button_browse_executable = ttk.Button(self, text='Browse...')
        button_browse_executable.grid(column=2, row=0)
        button_browse_executable.bind('<1>', self.bt_browse_executable)
        
        tk.Label(self, text='DF executable translation file:').grid()
        
        self.entry_translation_file = EntryCustom(self)
        self.entry_translation_file.grid(column=1, row=1, sticky=tk.E + tk.W)
        self.entry_translation_file.text = self.config['df_exe_translation_file'] or ''
        self.entry_translation_file.bind('<KeyPress>',
                                         func=lambda event:
                                            self.check_and_save_path('df_exe_translation_file', event.widget.text))
        
        button_browse_translation = ttk.Button(self, text='Browse...')
        button_browse_translation.grid(column=2, row=1)
        button_browse_translation.bind('<1>', self.bt_browse_translation)
        
        tk.Label(self, text='Encoding:').grid()
        
        self.combo_encoding = ComboboxCustom(self)
        self.combo_encoding.grid(column=1, row=2, sticky=tk.E + tk.W)
        
        self.combo_encoding.values = tuple(sorted(codepages.keys(),
                                                     key=lambda x: int(x.strip(string.ascii_letters))))
        self.combo_encoding.current(0)
        
        self.chk_dont_patch_charmap = CheckbuttonVar(self, text="Don't patch charmap table")
        self.chk_dont_patch_charmap.grid(column=1, sticky=tk.W)
        
        self.chk_add_leading_trailing_spaces = CheckbuttonVar(self, text='Add necessary leading/trailing spaces')
        self.chk_add_leading_trailing_spaces.grid(columnspan=2, sticky=tk.W)
        self.chk_add_leading_trailing_spaces.is_checked = True
        
        button_exclusions = ttk.Button(self, text='Exclusions...')
        button_exclusions.grid(row=4, column=2)
        button_exclusions.bind('<1>', self.bt_exclusions)

        self.chk_debug_output = CheckbuttonVar(self, text='Enable debugging output')
        self.chk_debug_output.grid(columnspan=2, sticky=tk.W)
        
        button_patch = ttk.Button(self, text='Patch!')
        button_patch.grid(row=5, column=2)
        button_patch.bind('<1>', self.bt_patch)
        
        log_field = tk.Text(self, width=48, height=16)
        log_field.grid(columnspan=3, sticky=tk.W + tk.E)


class App(tk.Tk):
    def save_settings(self, _=None):
        with open(self.config_path, 'w', encoding='utf-8') as config_file:
            json.dump(self.config, config_file, indent=4, sort_keys=True)

    def save_settings_repeatedly(self, delay=500):
        self.after(ms=delay, func=self.save_settings_repeatedly)
        self.save_settings()

    def init_config(self):
        config_name = '.df-translate.json'
        userdir = path.expanduser('~')
        self.config_path = path.join(userdir, config_name)
        default_config = dict()
        try:
            with open(self.config_path, encoding='utf-8') as config_file:
                self.config = json.load(config_file)
        except (FileNotFoundError, ValueError):
            self.config = default_config

        self.bind('<Destroy>', self.save_settings)  # Save settings on quit
        self.save_settings_repeatedly(delay=500)  # Save settings every 500 ms

    def __init__(self):
        super().__init__()

        self.config = None
        self.config_path = None
        self.init_config()

        notebook = ttk.Notebook()
        notebook.pack(fill='both', expand=1)
        
        f1 = DownloadTranslationsFrame(notebook, self)
        notebook.add(f1, text='Download translations')
        
        f1 = PatchExecutableFrame(notebook, self)
        notebook.add(f1, text='Patch executable file')
        
        # f1 = tk.Frame(notebook)
        # notebook.add(f1, text='Translate external text files')
        
        # f1 = tk.Frame(notebook)
        # notebook.add(f1, text='Translate packed files')

App().mainloop()
