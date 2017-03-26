import io
import multiprocessing as mp
import requests
import sys
import tkinter as tk
import tkinter.ttk as ttk
import string
import subprocess
import json
import os
import re

from dfrus.patchdf import get_codepages
from dfrus import dfrus
from os import path
from tkinter import messagebox
from transifex.api import TransifexAPI, TransifexAPIException
from custom_widgets import CheckbuttonVar, EntryCustom, ComboboxCustom, ListboxCustom, CustomText, FileEntry
from custom_widgets import TwoStateButton
from collections import OrderedDict
from df_gettext_toolkit import po
from multiprocessing import connection


def downloader(queue, tx, project, language, res, i, file_path):
    exception_info = 'Everything is ok! (If you see this message, contact the developer)'
    queue.put((i, 'downloading...'))
    for j in range(10):
        try:
            tx.get_translation(project, res['slug'], language, file_path)
            queue.put((i, 'ok!'))
            return
        except:
            queue.put((i, 'retry... (%d)' % (10 - j)))
            exception_info = sys.exc_info()[0]
    else:
        queue.put((i, 'failed'))
        queue.put(exception_info)


def check_and_save_path(config, key, file_path):
    if path.exists(file_path):
        config[key] = file_path


class DownloadTranslationsFrame(tk.Frame):
    @staticmethod
    def init_config(config):
        if 'download_translations' not in config:
            config['download_translations'] = dict()
        
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
            last_language = self.config.get('language', None)
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

    def download_waiter(self, resources, language, project, download_dir, i=0, queue=None,
                        initial_names=None, resource_names=None):
        if i >= len(resources):
            # Everything is downloaded
            self.config['language'] = language

            if sys.platform == 'win32':
                subprocess.Popen('explorer "%s"' % (download_dir.replace('/', '\\')))
            else:
                pass  # Todo: open the directory in a file manager on linux

            self.download_started = False
            self.button_download.reset_state()
        else:
            if queue is None:
                queue = mp.Queue()
            
            if initial_names is None:
                initial_names = [res['name'] for res in self.resources]
                resource_names = list(initial_names)

            if self.download_process is None:
                self.download_process = mp.Process(target=downloader, kwargs=dict(
                    i=i,
                    queue=queue,
                    tx=self.tx,
                    project=project,
                    language=language,
                    res=resources[i],
                    file_path=path.join(download_dir, '%s_%s.po' % (resources[i]['slug'], language))
                ))
                self.download_process.start()
            elif not self.download_process.is_alive() and queue.empty():
                queue.put((i, 'stopped'))

            while not queue.empty():
                j, message = queue.get()
                resource_names[j] = initial_names[j] + ' - ' + message
                self.listbox_resources.values = tuple(resource_names)
                self.app.update()
                
                if message == 'ok!':
                    self.progressbar.step()
                    if self.download_process is not None:
                        self.download_process.join()  # ensure process is terminated
                        self.download_process = None
                    i += 1
                elif message == 'failed':
                    error = queue.get()
                    messagebox.showerror('Downloading error', error)
                    self.download_started = False
                    self.button_download.reset_state()
                    return
                elif message == 'stopped':
                    self.download_started = False
                    self.download_process = None
                    return

            self.after(100, self.download_waiter,
                       resources, language, project, download_dir, i,
                       queue, initial_names, resource_names)
    
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
            
            self.listbox_resources.values = tuple(resource_names)
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


def cleanup_dictionary(d: iter, exclusions=None):
    if not exclusions:
        exclusions = set()
    else:
        exclusions = set(exclusions)

    for original_string, translation in d:
        if original_string and translation and original_string != translation:
            if original_string not in exclusions:
                if original_string[0] == ' ' and translation[0] not in {' ', ','}:
                    translation = ' ' + translation

                if original_string[-1] == ' ' and translation[-1] != ' ':
                    translation += ' '

            translation = translation.translate({0xfeff: None, 0x2019: "'", 0x201d: '"', 0x2014: '-'})

            yield original_string, translation


class ProcessMessageWrapper:
    _chunk_size = 1024

    def __init__(self, message_receiver):
        self._message_receiver = message_receiver
        self.encoding = 'utf-8'
    
    def write(self, s):
        for i in range(0, len(s), self._chunk_size):
            if isinstance(self._message_receiver, connection.Connection):
                self._message_receiver.send(s[i:i+self._chunk_size])
            else:  # mp.Queue or queue.Queue
                self._message_receiver.put(s[i:i+self._chunk_size])
            
    def flush(self):
        pass  # stub method


class PatchExecutableFrame(tk.Frame):
    @staticmethod
    def init_config(config):
        if 'patch_executable' not in config:
            config['patch_executable'] = dict()

        config = config['patch_executable']

        if 'fix_space_exclusions' not in config:
            config['fix_space_exclusions'] = dict(ru=['Histories of '])

        if 'language_codepages' not in config:
            config['language_codepages'] = dict()

        return config

    def update_log(self, message_queue):
        try:
            if isinstance(message_queue, connection.Connection):
                while message_queue.poll():
                    self.log_field.write(message_queue.recv())
            else:
                while not message_queue.empty():
                    self.log_field.write(message_queue.get())
            
            if not self.dfrus_process.is_alive():
                self.log_field.write('\n[PROCESS FINISHED]')
                self.button_patch.reset_state()
            else:
                self.after(100, self.update_log, message_queue)
        except (EOFError, BrokenPipeError):
            self.log_field.write('\n[MESSAGE QUEUE/PIPE BROKEN]')
            self.button_patch.reset_state()
    
    def bt_patch(self):
        if self.dfrus_process is not None and self.dfrus_process.is_alive():
            return False
        
        executable_file = self.fileentry_executable_file.text
        translation_file = self.fileentry_translation_file.text
        
        if not executable_file or not path.exists(executable_file):
            messagebox.showerror('Error', 'Valid path to an executable file must be specified')
        elif not translation_file or not path.exists(translation_file):
            messagebox.showerror('Error', 'Valid path to a translation file must be specified')
        else:
            with open(translation_file, 'r', encoding='utf-8') as fn:
                pofile = po.PoReader(fn)
                meta = pofile.meta
                dictionary = OrderedDict(
                    cleanup_dictionary(((entry['msgid'], entry['msgstr']) for entry in pofile),
                                       self.exclusions.get(meta['Language'], set()))
                )
            
            self.config['last_encoding'] = self.combo_encoding.text
            
            queue = mp.Queue()
            self.after(100, self.update_log, queue)
            self.log_field.clear()
            self.dfrus_process = mp.Process(target=dfrus.run,
                                            kwargs=dict(
                                                path=executable_file,
                                                dest='',
                                                trans_table=dictionary,
                                                codepage=self.combo_encoding.text,
                                                debug=self.chk_debug_output.is_checked,
                                                stdout=ProcessMessageWrapper(queue)
                                            ))
            self.dfrus_process.start()
            return True

        return False

    def bt_stop(self):
        r = messagebox.showwarning('Are you sure?', 'Stop the patching process?', type=messagebox.OKCANCEL)
        if r == 'cancel':
            return False
        else:
            self.dfrus_process.terminate()
            return True

    def kill_processes(self, _):
        if self.dfrus_process and self.dfrus_process.is_alive():
            self.dfrus_process.terminate()

    def bt_exclusions(self):
        translation_file = self.fileentry_translation_file.text
        language = None
        dictionary = None
        if translation_file and path.exists(translation_file):
            with open(translation_file, 'r', encoding='utf-8') as fn:
                pofile = po.PoReader(fn)
                meta = pofile.meta
                language = meta['Language']
                dictionary = {entry['msgid']: entry['msgstr'] for entry in pofile}

        dialog = DialogDontFixSpaces(self, self.config['fix_space_exclusions'], language, dictionary)
        self.config['fix_space_exclusions'] = dialog.exclusions or self.config['fix_space_exclusions']
        self.exclusions = self.config['fix_space_exclusions']

    def setup_checkbutton(self, text, config_key, default_state):
        config = self.config

        def save_checkbox_state(event, option_name):
            config[option_name] = not event.widget.is_checked  # Event occurs before the widget changes state
        
        check = CheckbuttonVar(self, text=text)
        check.bind('<1>', lambda event: save_checkbox_state(event, config_key))
        check.is_checked = config[config_key] = config.get(config_key, default_state)
        return check

    def filter_codepages(self, codepages):
        translation_file = self.fileentry_translation_file.text
        with open(translation_file, 'r', encoding='utf-8') as fn:
            pofile = po.PoReader(fn)
            self.translation_file_language = pofile.meta['Language']
            dictionary = list(cleanup_dictionary((entry['msgid'], entry['msgstr']) for entry in pofile))

        for codepage in codepages:
            try:
                for _, item in dictionary:
                    item.encode(codepage)
                yield codepage
            except UnicodeEncodeError:
                pass

    def on_translation_path_change(self, text):
        check_and_save_path(self.config, 'df_exe_translation_file', text)

        # Update codepage combobox
        # TODO: Cache supported codepages' list
        codepages = get_codepages().keys()
        if self.fileentry_translation_file.path_is_valid():
            codepages = self.filter_codepages(codepages)
        self.combo_encoding.values = tuple(sorted(codepages,
                                                  key=lambda x: int(x.strip(string.ascii_letters))))

        if self.translation_file_language not in self.config['language_codepages']:
            self.combo_encoding.current(0)
        else:
            self.combo_encoding.text = self.config['language_codepages'][self.translation_file_language]

    def __init__(self, master=None, app=None):
        super().__init__(master)
        
        self.app = app
        
        self.config = self.init_config(self.app.config)
        config = self.config
        self.exclusions = config['fix_space_exclusions']
        
        self.dfrus_process = None
        
        tk.Label(self, text='DF executable file:').grid()
        
        self.fileentry_executable_file = FileEntry(
            self,
            dialogtype='askopenfilename',
            filetypes=[('Executable files', '*.exe')],
            default_path=config.get('df_executable', ''),
            on_change=lambda text: check_and_save_path(self.config, 'df_executable', text),
        )
        self.fileentry_executable_file.grid(column=1, row=0, columnspan=2, sticky='EW')
        
        tk.Label(self, text='DF executable translation file:').grid()
        
        self.fileentry_translation_file = FileEntry(
            self,
            dialogtype='askopenfilename',
            filetypes=[
                ("Hardcoded strings' translation", '*hardcoded*.po'),
                ('Translation files', '*.po'),
                # ('csv file', '*.csv'), # @TODO: Currently not supported 
            ],
            default_path=config.get('df_exe_translation_file', ''),
            on_change=self.on_translation_path_change,
        )
        self.fileentry_translation_file.grid(column=1, row=1, columnspan=2, sticky='EW')
        if self.fileentry_translation_file.path_is_valid():
            with open(self.fileentry_translation_file.text, 'r', encoding='utf-8') as fn:
                self.translation_file_language = po.PoReader(fn).meta['Language']
        else:
            self.translation_file_language = None

        tk.Label(self, text='Encoding:').grid()
        
        self.combo_encoding = ComboboxCustom(self)
        self.combo_encoding.grid(column=1, row=2, sticky=tk.E + tk.W)

        codepages = get_codepages().keys()
        if self.fileentry_translation_file.path_is_valid():
            codepages = self.filter_codepages(codepages)
        self.combo_encoding.values = tuple(sorted(codepages,
                                                  key=lambda x: int(x.strip(string.ascii_letters))))
        
        if 'last_encoding' in config:
            self.combo_encoding.text = config['last_encoding']
        else:
            self.combo_encoding.current(0)

        def save_encoding_into_config(event):
            config['last_encoding'] = event.widget.text
            if self.translation_file_language:
                config['language_codepages'][self.translation_file_language] = event.widget.text
        
        self.combo_encoding.bind('<<ComboboxSelected>>', func=save_encoding_into_config)
        
        self.chk_dont_patch_charmap = self.setup_checkbutton(
            text="Don't patch charmap table",
            config_key='dont_patch_charmap',
            default_state=False)
        
        self.chk_dont_patch_charmap.grid(column=1, sticky=tk.W)
        
        self.chk_add_leading_trailing_spaces = self.setup_checkbutton(
            text='Add necessary leading/trailing spaces',
            config_key='add_leading_trailing_spaces',
            default_state=True)
        
        self.chk_add_leading_trailing_spaces.grid(columnspan=2, sticky=tk.W)
        
        button_exclusions = ttk.Button(self, text='Exclusions...', command=self.bt_exclusions)
        button_exclusions.grid(row=4, column=2)

        self.chk_debug_output = self.setup_checkbutton(
            text='Enable debugging output',
            config_key='debug_output',
            default_state=False)
        
        self.chk_debug_output.grid(columnspan=2, sticky=tk.W)

        self.button_patch = TwoStateButton(self, text='Patch!', command=self.bt_patch, text2='Stop!', command2=self.bt_stop)
        self.button_patch.grid(row=5, column=2)
        
        self.log_field = CustomText(self, width=48, height=16, enabled=False)
        self.log_field.grid(columnspan=3, sticky='NSWE')

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(6, weight=1)

        self.bind('<Destroy>', self.kill_processes)


class TranslateExternalFiles(tk.Frame):
    @staticmethod
    def init_config(config, section_name):
        if section_name not in config:
            config[section_name] = dict()

        config = config[section_name]

        return config

    @staticmethod
    def get_languages(directory):
        s = set()
        for filename in os.listdir(directory):
            if filename.endswith('.po'):
                with open(path.join(directory, filename), encoding='utf-8') as file:
                    s.add(po.PoReader(file).meta['Language'])

        return sorted(s)

    def on_change_translation_files_path(self, config, key, directory):
        check_and_save_path(config, key, directory)
        if path.exists(directory):
            self.combo_language.values = tuple(self.get_languages(directory))
            self.combo_language.current(0)
        else:
            self.combo_language.values = tuple()
            self.combo_language.text = ''

    def on_change_language(self, event=None, widget=None):
        def filter_files_by_language(directory, language):
            for filename in os.listdir(directory):
                if filename.endswith('.po'):
                    with open(path.join(directory, filename), encoding='utf-8') as file:
                        if po.PoReader(file).meta['Language'] == language:
                            yield filename

        if widget is None:
            widget = event.widget
        
        directory = self.fileentry_translation_files.text
        files = filter_files_by_language(directory, widget.text) if path.exists(directory) else tuple()
        self.listbox_translation_files.values = tuple(files)

    def __init__(self, master, app=None, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.app = app
        self.config = self.init_config(self.app.config, section_name='translate_external_files')
        config = self.config

        tk.Label(self, text='Dwarf Fortress root path:').grid()

        self.fileentry_df_root_path = FileEntry(
            self,
            dialogtype='askdirectory',
            default_path=config.get('df_root_path', ''),
            on_change=lambda text: check_and_save_path(self.config, 'df_root_path', text),
        )
        self.fileentry_df_root_path.grid(row=0, column=1, sticky='WE')
        
        tk.Label(self, text="Translation files' directory:").grid()
        
        self.fileentry_translation_files = FileEntry(
            self,
            dialogtype='askdirectory',
            default_path=config.get('translation_files_path', ''),
            on_change=lambda text: self.on_change_translation_files_path(self.config, 'translation_files_path', text),
        )
        self.fileentry_translation_files.grid(row=1, column=1, sticky='WE')

        tk.Label(self, text="Language:").grid()

        self.combo_language = ComboboxCustom(self)
        self.combo_language.grid(row=2, column=1, sticky='WE')
        
        directory = self.fileentry_translation_files.text
        if path.exists(directory):
            self.combo_language.values = tuple(self.get_languages(self.fileentry_translation_files.text))
            self.combo_language.current(0)
        
        self.combo_language.bind('<<ComboboxSelected>>', self.on_change_language)

        self.listbox_translation_files = ListboxCustom(self)
        self.listbox_translation_files.grid(columnspan=2, sticky='NSWE')
        self.on_change_language(widget=self.combo_language)

        self.grid_columnconfigure(1, weight=1)


class App(tk.Tk):
    def save_settings(self, _=None):
        with open(self.config_path, 'w', encoding='utf-8') as config_file:
            json.dump(self.config, config_file, indent=4, sort_keys=True)

    def save_settings_repeatedly(self, delay=500):
        nb = self.notebook
        if nb.tabs():
            self.config['last_tab_opened'] = nb.tabs().index(nb.select())
        
        self.after(delay, self.save_settings_repeatedly, delay)
        self.save_settings()

    def check_for_errors(self, delay=100):
        if self.stderr.getvalue():
            messagebox.showerror('Unhandled Exception', self.stderr.getvalue())
            self.stderr.truncate(0)
            self.stderr.seek(0)
        self.after(delay, self.check_for_errors, delay)

    def init_config(self, noconfig):
        config_name = '.df-translate.json'
        userdir = path.expanduser('~')
        self.config_path = path.join(userdir, config_name)
        default_config = dict()
        
        if noconfig:
            self.config = default_config
        else:
            try:
                with open(self.config_path, encoding='utf-8') as config_file:
                    self.config = json.load(config_file)
            except (FileNotFoundError, ValueError):
                self.config = default_config
        
        if 'last_tab_opened' not in self.config:
            self.config['last_tab_opened'] = 0
        
        if not noconfig:
            self.bind('<Destroy>', self.save_settings)  # Save settings on quit
            self.save_settings_repeatedly(delay=500)  # Save settings every 500 ms

    def __init__(self, noconfig=False):
        super().__init__()

        executable = path.split(sys.executable)[1]
        if executable.startswith('pythonw') or not executable.startswith('python'):
            self.stderr = io.StringIO()
            sys.stderr = self.stderr
            self.check_for_errors()

        self.notebook = ttk.Notebook()
        
        self.config = None
        self.config_path = None
        self.init_config(noconfig)
        
        notebook = self.notebook
        notebook.pack(fill='both', expand=1)
        
        f1 = DownloadTranslationsFrame(notebook, self)
        notebook.add(f1, text='Download translations')
        
        f1 = PatchExecutableFrame(notebook, self)
        notebook.add(f1, text='Patch executable file')
        
        f1 = TranslateExternalFiles(notebook, self)
        # notebook.add(f1, text='Translate external text files')
        
        # f1 = tk.Frame(notebook)
        # notebook.add(f1, text='Translate packed files')
        
        notebook.select(self.config['last_tab_opened'])

if __name__ == '__main__':
    mp.freeze_support()
    App(noconfig='--noconfig' in sys.argv).mainloop()
