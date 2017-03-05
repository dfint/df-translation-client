import requests
import sys
import tkinter as tk
import tkinter.ttk as ttk
import string
import subprocess
import json
import re

from dfrus.patchdf import codepages
from dfrus import dfrus
from multiprocessing import Process, Pipe
from os import path
from tkinter import filedialog, messagebox
from transifex.api import TransifexAPI, TransifexAPIException
from custom_widgets import CheckbuttonVar, EntryCustom, ComboboxCustom, ListboxCustom, CustomText
from collections import defaultdict, OrderedDict
from df_gettext_toolkit import po


class DownloadTranslationsFrame(tk.Frame):
    def init_config(self, config):
        if 'download_translations' not in config:
            config['download_translations'] = defaultdict(lambda: None)
        
        config = config['download_translations']
        if 'recent_projects' not in config:
            config['recent_projects'] = ['dwarf-fortress']

        return config
    
    def bt_connect(self):
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
            
            self.listbox_resources.clear()
            self.listbox_resources.values = tuple(res['name'] for res in self.resources)
            
            self.config['username'] = username

            recent_projects = self.config['recent_projects']
            if recent_projects or project != recent_projects[0]:
                if project in recent_projects:
                    recent_projects.remove(project)
                recent_projects.insert(0, project)
            self.combo_projects.values = tuple(recent_projects)
    
    def bt_download(self):
        if self.tx and self.resources:
            self.progressbar['maximum'] = len(self.resources) * 1.001
            self.progressbar['value'] = 0
            
            download_dir = self.entry_download_to.get()
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
            
            self.listbox_resources.values = tuple(resource_names)
            for i, res in enumerate(self.resources):
                resource_names[i] = initial_names[i] + ' - downloading...'
                self.listbox_resources.values = tuple(resource_names)
                self.app.update()
                
                file_path = path.join(download_dir, '%s_%s.po' % (res['slug'], language))
                
                error = None
                for j in range(10):
                    try:
                        self.tx.get_translation(project, res['slug'], language, file_path)
                        break
                    except:
                        resource_names[i] = initial_names[i] + ' - retry... (%d)' % (10 - j)
                        self.listbox_resources.values = tuple(resource_names)
                        self.app.update()
                        error = sys.exc_info()[0]
                else:
                    resource_names[i] = initial_names[i] + ' - failed'
                    self.listbox_resources.values = tuple(resource_names)
                    self.app.update()
                    messagebox.showerror('Downloading error', error)
                    break
                
                resource_names[i] = initial_names[i] + ' - ok!'
                self.listbox_resources.values = tuple(resource_names)
                self.progressbar.step()
                self.app.update()

            self.config['language'] = language

            if sys.platform == 'win32':
                subprocess.Popen('explorer "%s"' % (download_dir.replace('/', '\\')))
            else:
                pass  # Todo: open the directory in a file manager on linux
    
    def bt_choose_directory(self):
        download_path = filedialog.askdirectory()
        if download_path:
            self.entry_download_to.text = download_path
            self.config['download_to'] = download_path
    
    def __init__(self, master=None, app=None):
        super().__init__(master)
        
        self.app = app
        
        self.config = self.init_config(self.app.config)

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
        
        self.entry_download_to = EntryCustom(self)
        self.entry_download_to.grid(column=1, row=6, sticky=tk.W + tk.E)
        self.entry_download_to.text = self.config['download_to'] or ''
        
        button_choose_directory = ttk.Button(self, text='Choose directory...', command=self.bt_choose_directory)
        button_choose_directory.grid(column=2, row=6)
        
        self.button_download = ttk.Button(self, text='Download translations', command=self.bt_download)
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


def show_spaces(s):
    parts = re.search(r'^(\s*)(.*?)(\s*)$', s)
    return '\u2022' * len(parts.group(1)) + parts.group(2) + '\u2022' * len(parts.group(3))


class DialogDontFixSpaces(tk.Toplevel):
    def update_listbox_exclusions(self):
        exclusions = self.exclusions.get(self.combo_language.text, list())
        self.listbox_exclusions.values = tuple(sorted(show_spaces(item) for item in exclusions))
        self.restore_strings.update({show_spaces(s): s for s in exclusions})

    def combo_language_change_selection(self, _):
        self.update_listbox_exclusions()
        self.update_listbox_exclusions_hints()

    def update_listbox_exclusions_hints(self):
        text = self.entry_search.text
        values = ((show_spaces(key) for key in self.strings if text.lower() in key.lower())
                  if self.language == self.combo_language.text else tuple())
        self.listbox_exclusions_hints.values = tuple(values)

    def entry_search_key_up(self, _):
        self.update_listbox_exclusions_hints()

    def bt_remove_selected(self):
        index = self.listbox_exclusions.curselection()
        if index:
            item = self.restore_strings[self.listbox_exclusions.values[index[0]]]
            self.exclusions[self.combo_language.text].remove(item)
            self.update_listbox_exclusions()

    def bt_add_selected(self):
        index = self.listbox_exclusions_hints.curselection()
        if index:
            item = self.restore_strings[self.listbox_exclusions_hints.values[index[0]]]
            self.exclusions[self.combo_language.text].append(item)
            self.update_listbox_exclusions()

    def __init__(self, parent, exclusions: dict, language: str, dictionary: dict, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.grab_set()

        self.exclusions = exclusions

        self.title("Choose exclusions")

        language_list = list(self.exclusions)
        if language:
            if language in language_list:
                language_list.remove(language)
            language_list = [language] + language_list
        self.language = language

        self.dictionary = dictionary or dict()
        self.strings = sorted((key for key in dictionary.keys() if key.startswith(' ') or key.endswith(' ')),
                              key=lambda x: x.lower().strip())
        self.restore_strings = {show_spaces(s): s for s in self.strings}

        self.combo_language = ComboboxCustom(self, values=language_list)
        self.combo_language.grid(sticky=tk.W+tk.E)
        self.combo_language.current(0)
        self.combo_language.bind('<<ComboboxSelected>>', self.combo_language_change_selection)
        self.combo_language.bind('<Any-KeyRelease>', self.combo_language_change_selection)

        bt = ttk.Button(self, text='-- Remove selected --', command=self.bt_remove_selected)
        bt.grid(column=0, row=1, sticky=tk.W+tk.E)

        self.listbox_exclusions = ListboxCustom(self, width=40, height=20)
        self.listbox_exclusions.grid(sticky='NSWE')
        self.update_listbox_exclusions()

        self.entry_search = EntryCustom(self)
        self.entry_search.grid(column=1, row=0, sticky=tk.W+tk.E)
        self.entry_search.bind('<Any-KeyRelease>', self.entry_search_key_up)

        bt = ttk.Button(self, text='<< Add selected <<', command=self.bt_add_selected)
        bt.grid(column=1, row=1, sticky=tk.W+tk.E)

        self.listbox_exclusions_hints = ListboxCustom(self, width=40, height=20)
        self.listbox_exclusions_hints.grid(column=1, row=2, sticky='NSWE')
        self.update_listbox_exclusions_hints()

        button = ttk.Button(self, text="OK", command=self.destroy)
        button.grid(row=3, column=0)

        def cancel():
            self.exclusions = None
            self.destroy()

        button = ttk.Button(self, text="Cancel", command=cancel)
        button.grid(row=3, column=1)

        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(2, weight=1)


def cleanup_dictionary(d: iter, exclusions: iter):
    exclusions = set(exclusions)
    for original_string, translation in d:
        if original_string and translation and original_string != translation and original_string not in exclusions:
            if original_string[0] == ' ' and translation[0] not in {' ', ','}:
                translation = ' ' + translation

            if original_string[-1] == ' ' and translation[-1] != ' ':
                translation += ' '

            translation = translation.translate({0xfeff: None, 0x2019: "'", 0x201d: '"'})

            yield original_string, translation


class ConnectionWrapper:
    _chunk_size = 1024
    def __init__(self, connection):
        self._connection = connection
        self.encoding = 'utf-8'
    
    def write(self, s):
        for i in range(0, len(s), self._chunk_size):
            self._connection.send(s[i:i+self._chunk_size])
            
    def flush(self):
        pass  # stub method


class PatchExecutableFrame(tk.Frame):
    def init_config(self, config):
        if 'patch_executable' not in config:
            config['patch_executable'] = defaultdict(lambda: None)

        config = config['patch_executable']

        if 'fix_space_exclusions' not in config:
            config['fix_space_exclusions'] = dict(ru=['Histories of '])

        return config

    def bt_browse_executable(self):
        file_path = filedialog.askopenfilename(filetypes=[('Executable files', '*.exe')])
        if file_path:
            self.entry_executable_file.text = file_path
            self.config['df_executable'] = file_path
    
    def bt_browse_translation(self):
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

    def update_log(self, connection):
        try:
            while connection.poll():
                self.log_field.write(connection.recv())
            
            if not self.dfrus_process.is_alive():
                self.log_field.write('\n[PROCESS FINISHED]')
            else:
                self.after(100, self.update_log, connection)
        except (EOFError, BrokenPipeError):
            self.log_field.write('\n[PIPE BROKEN]')
    
    def bt_patch(self):
        if self.dfrus_process is not None and self.dfrus_process.is_alive():
            return
        
        executable_file = self.entry_executable_file.text
        translation_file = self.entry_translation_file.text
        
        if not executable_file or not path.exists(executable_file):
            messagebox.showerror('Error', 'Valid path to an executable file must be specified')
        elif not translation_file or not path.exists(translation_file):
            messagebox.showerror('Error', 'Valid path to a translation file must be specified')
        else:
            with open(translation_file, 'r', encoding='utf-8') as fn:
                pofile = po.load_po(fn)
                meta = po.get_metadata(next(pofile))
                dictionary = OrderedDict(
                    cleanup_dictionary(((entry['msgid'], entry['msgstr']) for entry in pofile),
                                       self.exclusions[meta['Language']])
                )
            
            parent_conn, child_conn = Pipe()
            self.after(100, self.update_log, parent_conn)
            self.log_field.clear()
            self.dfrus_process = Process(target=dfrus.run,
                                    kwargs=dict(
                                        path=executable_file,
                                        dest='',
                                        trans_table=dictionary,
                                        codepage=self.combo_encoding.text,
                                        debug=self.chk_debug_output.is_checked,
                                        stdout=ConnectionWrapper(child_conn)
                                    ))
            self.dfrus_process.start()
    
    def bt_exclusions(self):
        translation_file = self.entry_translation_file.text
        language = None
        dictionary = None
        if translation_file and path.exists(translation_file):
            with open(translation_file, 'r', encoding='utf-8') as fn:
                pofile = po.load_po(fn)
                first_entry = next(pofile)
                assert first_entry['msgid'] == ''
                meta = po.get_metadata(first_entry)
                language = meta['Language']
                dictionary = {entry['msgid']: entry['msgstr'] for entry in pofile}

        dialog = DialogDontFixSpaces(self, self.config['fix_space_exclusions'], language, dictionary)
        self.config['fix_space_exclusions'] = dialog.exclusions or self.config['fix_space_exclusions']
        self.exclusions = self.config['fix_space_exclusions']

    def __init__(self, master=None, app=None):
        super().__init__(master)
        
        self.app = app
        
        self.config = self.init_config(self.app.config)
        self.exclusions = self.config['fix_space_exclusions']
        
        self.dfrus_process = None
        
        tk.Label(self, text='DF executable file:').grid()
        
        self.entry_executable_file = EntryCustom(self)
        self.entry_executable_file.grid(column=1, row=0, sticky=tk.E + tk.W)
        self.entry_executable_file.text = self.config['df_executable'] or ''
        self.entry_executable_file.bind('<KeyPress>',
                                        func=lambda event:
                                            self.check_and_save_path('df_executable', event.widget.text))

        button_browse_executable = ttk.Button(self, text='Browse...', command=self.bt_browse_executable)
        button_browse_executable.grid(column=2, row=0)
        
        tk.Label(self, text='DF executable translation file:').grid()
        
        self.entry_translation_file = EntryCustom(self)
        self.entry_translation_file.grid(column=1, row=1, sticky=tk.E + tk.W)
        self.entry_translation_file.text = self.config['df_exe_translation_file'] or ''
        self.entry_translation_file.bind('<KeyPress>',
                                         func=lambda event:
                                             self.check_and_save_path('df_exe_translation_file', event.widget.text))
        
        button_browse_translation = ttk.Button(self, text='Browse...', command=self.bt_browse_translation)
        button_browse_translation.grid(column=2, row=1)
        
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
        
        button_exclusions = ttk.Button(self, text='Exclusions...', command=self.bt_exclusions)
        button_exclusions.grid(row=4, column=2)

        self.chk_debug_output = CheckbuttonVar(self, text='Enable debugging output')
        self.chk_debug_output.grid(columnspan=2, sticky=tk.W)
        
        button_patch = ttk.Button(self, text='Patch!', command=self.bt_patch)
        button_patch.grid(row=5, column=2)
        
        self.log_field = CustomText(self, width=48, height=16, enabled=False)
        self.log_field.grid(columnspan=3, sticky='NSWE')

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(6, weight=1)


class App(tk.Tk):
    def save_settings(self, _=None):
        with open(self.config_path, 'w', encoding='utf-8') as config_file:
            json.dump(self.config, config_file, indent=4, sort_keys=True)

    def save_settings_repeatedly(self, delay=500):
        nb = self.notebook
        if nb.tabs():
            self.config['last_tab_opened'] = nb.tabs().index(nb.select())
        
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
        
        if 'last_tab_opened' not in self.config:
            self.config['last_tab_opened'] = 0
        
        self.bind('<Destroy>', self.save_settings)  # Save settings on quit
        self.save_settings_repeatedly(delay=500)  # Save settings every 500 ms

    def __init__(self):
        super().__init__()
        
        self.notebook = ttk.Notebook()
        
        self.config = None
        self.config_path = None
        self.init_config()
        
        notebook = self.notebook
        notebook.pack(fill='both', expand=1)
        
        f1 = DownloadTranslationsFrame(notebook, self)
        notebook.add(f1, text='Download translations')
        
        f1 = PatchExecutableFrame(notebook, self)
        notebook.add(f1, text='Patch executable file')
        
        # f1 = tk.Frame(notebook)
        # notebook.add(f1, text='Translate external text files')
        
        # f1 = tk.Frame(notebook)
        # notebook.add(f1, text='Translate packed files')
        
        notebook.select(self.config['last_tab_opened'])

if __name__ == '__main__':
    App().mainloop()
