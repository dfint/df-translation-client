import io
import multiprocessing as mp
import sys
import tkinter as tk
import tkinter.ttk as ttk
import string
import os

from dialog_dont_fix_spaces import DialogDontFixSpaces

try:
    from dfrus.patchdf import get_codepages
except ImportError:
    from dfrus.patch_charmap import get_codepages

from config import check_and_save_path, init_section, save_settings, load_settings
from dfrus import dfrus
from os import path
from tkinter import messagebox
from custom_widgets import CheckbuttonVar, ComboboxCustom, ListboxCustom, CustomText, FileEntry
from custom_widgets import TwoStateButton
from collections import OrderedDict
from df_gettext_toolkit import po
from df_gettext_toolkit.translate_plain_text import translate_plain_text
from df_gettext_toolkit.translate_raws import translate_raws
from tab_download import DownloadTranslationsFrame


def cleanup_dictionary(d: iter, exclusions=None):
    exclusions = set(exclusions) if exclusions else set()

    for original_string, translation in d:
        if original_string and translation and original_string != translation:
            if original_string not in exclusions:
                if original_string[0] == ' ' and translation[0] not in {' ', ','}:
                    translation = ' ' + translation

                if original_string[-1] == ' ' and translation[-1] != ' ':
                    translation += ' '

            # TODO: Make this mapping customizable
            translation = translation.translate({0xfeff: None, 0x2019: "'", 0x201d: '"', 0x2014: '-'})

            yield original_string, translation


def filter_codepages(codepages, strings):
    for codepage in codepages:
        try:
            for item in strings:
                item.encode(codepage)
            yield codepage
        except UnicodeEncodeError:
            pass


class ProcessMessageWrapper:
    _chunk_size = 1024

    def __init__(self, message_receiver):
        self._message_receiver = message_receiver
        self.encoding = 'utf-8'
    
    def write(self, s):
        for i in range(0, len(s), self._chunk_size):
            self._message_receiver.send(s[i:i+self._chunk_size])
            
    def flush(self):
        pass  # stub method


class PatchExecutableFrame(tk.Frame):
    def update_log(self, message_queue):
        try:
            while message_queue.poll():
                self.log_field.write(message_queue.recv())
            
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
                                       self.exclusions.get(meta['Language'], self.exclusions))
                )
            
            self.config['last_encoding'] = self.combo_encoding.text

            parent_conn, child_conn = mp.Pipe()

            self.after(100, self.update_log, parent_conn)
            self.log_field.clear()
            self.dfrus_process = mp.Process(
                target=dfrus.run,
                kwargs=dict(
                    path=executable_file,
                    dest='',
                    trans_table=dictionary,
                    codepage=self.combo_encoding.text,
                    debug=self.chk_debug_output.is_checked,
                    stdout=ProcessMessageWrapper(child_conn)
                )
            )
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

    def update_combo_encoding(self, text):
        check_and_save_path(self.config, 'df_exe_translation_file', text)

        # Update codepage combobox
        # TODO: Cache supported codepages' list
        codepages = get_codepages().keys()
        if self.fileentry_translation_file.path_is_valid():
            translation_file = self.fileentry_translation_file.text
            with open(translation_file, 'r', encoding='utf-8') as fn:
                pofile = po.PoReader(fn)
                self.translation_file_language = pofile.meta['Language']
                strings = [val for _, val in cleanup_dictionary((entry['msgid'], entry['msgstr']) for entry in pofile)]
            codepages = filter_codepages(codepages, strings)
        self.combo_encoding.values = sorted(codepages,
                                            key=lambda x: int(x.strip(string.ascii_letters)))

        if self.translation_file_language not in self.config['language_codepages']:
            self.combo_encoding.current(0)
        else:
            self.combo_encoding.text = self.config['language_codepages'][self.translation_file_language]

    def __init__(self, master, config):
        super().__init__(master)
        
        self.config = init_section(
            config, section_name='patch_executable',
            defaults=dict(
                fix_space_exclusions=dict(ru=['Histories of ']),
                language_codepages=dict(),
            )
        )
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
            on_change=self.update_combo_encoding,
        )
        self.fileentry_translation_file.grid(column=1, row=1, columnspan=2, sticky='EW')

        tk.Label(self, text='Encoding:').grid()
        
        self.combo_encoding = ComboboxCustom(self)
        self.combo_encoding.grid(column=1, row=2, sticky=tk.E + tk.W)

        codepages = get_codepages().keys()
        
        if not self.fileentry_translation_file.path_is_valid():
            self.translation_file_language = None
        else:
            translation_file = self.fileentry_translation_file.text
            with open(translation_file, 'r', encoding='utf-8') as fn:
                pofile = po.PoReader(fn)
                self.translation_file_language = pofile.meta['Language']
                strings = [val for _, val in cleanup_dictionary((entry['msgid'], entry['msgstr']) for entry in pofile)]
            codepages = filter_codepages(codepages, strings)

        self.combo_encoding.values = sorted(codepages,
                                            key=lambda x: int(x.strip(string.ascii_letters)))
        
        if 'last_encoding' in config:
            self.combo_encoding.text = config['last_encoding']
        else:
            self.combo_encoding.current(0)

        def save_encoding_into_config(event):
            config['last_encoding'] = event.widget.text
            if self.translation_file_language:
                config['language_codepages'][self.translation_file_language] = event.widget.text
        
        self.combo_encoding.bind('<<ComboboxSelected>>', func=save_encoding_into_config)

        # FIXME: chk_dont_patch_charmap does nothing
        self.chk_dont_patch_charmap = self.setup_checkbutton(
            text="Don't patch charmap table",
            config_key='dont_patch_charmap',
            default_state=False)
        
        self.chk_dont_patch_charmap.grid(column=1, sticky=tk.W)

        # FIXME: chk_add_leading_trailing_spaces does nothing
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

        self.button_patch = TwoStateButton(self,
                                           text='Patch!', command=self.bt_patch,
                                           text2='Stop!', command2=self.bt_stop)
        self.button_patch.grid(row=5, column=2)
        
        self.log_field = CustomText(self, width=48, height=16, enabled=False)
        self.log_field.grid(columnspan=3, sticky='NSWE')

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(6, weight=1)

        self.bind('<Destroy>', self.kill_processes)


class TranslateExternalFiles(tk.Frame):
    @staticmethod
    def get_languages(directory):
        languages = set()
        for filename in os.listdir(directory):
            if filename.endswith('.po'):
                with open(path.join(directory, filename), encoding='utf-8') as file:
                    languages.add(po.PoReader(file).meta['Language'])

        return sorted(languages)

    def on_change_translation_files_path(self, config, key, directory):
        check_and_save_path(config, key, directory)
        if path.exists(directory):
            languages = self.get_languages(directory)
            self.combo_language.values = languages

            if languages:
                self.combo_language.current(0)
            else:
                self.combo_language.text = ''

            self.update_listbox_translation_files(language=self.combo_language.text)
        else:
            self.combo_language.values = tuple()
            self.combo_language.text = ''

    @staticmethod
    def filter_files_by_language(directory, language):
        for filename in os.listdir(directory):
            if filename.endswith('.po'):
                with open(path.join(directory, filename), encoding='utf-8') as file:
                    if po.PoReader(file).meta['Language'] == language:
                        yield filename

    def update_listbox_translation_files(self, event=None, language=None):
        language = self.combo_language.text if not language else language
        directory = self.fileentry_translation_files.text
        files = self.filter_files_by_language(directory, language) if path.exists(directory) else tuple()
        self.listbox_translation_files.values = files

    def update_combo_encoding(self, _=None):
        language = self.combo_language.text
        directory = self.fileentry_translation_files.text
        # TODO: Unify with PatchExecutableFrame.update_combo_encoding()
        if path.exists(directory):
            files = self.filter_files_by_language(directory, language)
            codepages = get_codepages().keys()
            for file in files:
                with open(path.join(directory, file), 'r', encoding='utf-8') as fn:
                    pofile = po.PoReader(fn)
                    strings = [val for _, val in cleanup_dictionary((entry['msgid'], entry['msgstr']) for entry in pofile)]
                codepages = filter_codepages(codepages, strings)
            self.combo_encoding.values = sorted(codepages,
                                                key=lambda x: int(x.strip(string.ascii_letters)))

            self.combo_encoding.current(0)

    def bt_search(self, translate=False):
        patterns = {
            r'raw\objects': dict(
                po_filename='raw-objects',
                func=translate_raws,
            ),
            r'data_src': dict(
                po_filename='uncompressed',
                func=lambda *args: translate_plain_text(*args, join_paragraphs=True),
            ),
            r'data\speech': dict(
                po_filename='speech',
                func=lambda *args: translate_plain_text(*args, join_paragraphs=False),
            ),
            r'raw\objects\text': dict(
                po_filename='text',
                func=lambda *args: translate_plain_text(*args, join_paragraphs=False),
            ),
        }

        self.listbox_found_directories.clear()
        for cur_dir, _, files in os.walk(self.fileentry_df_root_path.text):
            for pattern in patterns:
                if cur_dir.endswith(pattern):
                    self.listbox_found_directories.insert(tk.END, cur_dir + ' (%s files)' % len(files))
                    postfix = '_{}.po'.format(self.combo_language.text)
                    po_filename = os.path.join(self.fileentry_translation_files.text,
                                               patterns[pattern]['po_filename'] + postfix)

                    if translate:
                        func = patterns[pattern]['func']
                        # func(po_filename, cur_dir, encoding)

    def __init__(self, master, config, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.config = init_section(config, section_name='translate_external_files')
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
            languages = self.get_languages(directory)
            self.combo_language.values = languages
            if languages:
                self.combo_language.current(0)

        self.combo_language.bind('<<ComboboxSelected>>', self.update_listbox_translation_files)

        tk.Label(self, text="Encoding:").grid()
        self.combo_encoding = ComboboxCustom(self)
        self.combo_encoding.grid(row=3, column=1, sticky='WE')
        
        self.update_combo_encoding()

        self.listbox_translation_files = ListboxCustom(self)
        self.listbox_translation_files.grid(columnspan=2, sticky='NSWE')
        self.update_listbox_translation_files(language=self.combo_language.text)

        ttk.Button(self, text='Search', command=self.bt_search).grid()
        ttk.Button(self, text='Translate', command=lambda: self.bt_search(translate=True)).grid(row=5, column=1)

        self.listbox_found_directories = ListboxCustom(self)
        self.listbox_found_directories.grid(columnspan=2, sticky='NSWE')

        self.grid_columnconfigure(1, weight=1)


class App(tk.Tk):
    def save_settings_repeatedly(self, config, config_path, delay=500):
        if hasattr(self, 'notebook'):
            nb = self.notebook
            if nb.tabs():
                self.config['last_tab_opened'] = nb.tabs().index(nb.select())
        
        self.after(delay, self.save_settings_repeatedly, config, config_path, delay)
        save_settings(config, config_path)

    def check_for_errors(self, delay=100):
        if self.stderr.getvalue():
            messagebox.showerror('Unhandled Exception', self.stderr.getvalue())
            self.stderr.truncate(0)
            self.stderr.seek(0)
        self.after(delay, self.check_for_errors, delay)

    def init_config(self, noconfig):
        config_name = '.df-translate.json'
        userdir = path.expanduser('~')
        config_path = path.join(userdir, config_name)
        config = dict(last_tab_opened=0)

        if not noconfig:
            config = load_settings(config_path, defaults=config)
            self.bind('<Destroy>', lambda _ : save_settings(config, config_path))  # Save settings on quit
            self.save_settings_repeatedly(config, config_path, delay=500)  # Save settings every 500 ms

        return config, config_path

    def __init__(self, noconfig=False):
        super().__init__()

        executable = path.split(sys.executable)[1]
        if executable.startswith('pythonw') or not executable.startswith('python'):  # if no console attached
            self.stderr = io.StringIO()
            sys.stderr = self.stderr
            self.check_for_errors()

        self.config, self.config_path = self.init_config(noconfig)

        self.notebook = ttk.Notebook()
        notebook = self.notebook
        notebook.pack(fill='both', expand=1)

        notebook.add(DownloadTranslationsFrame(notebook, self.config),
                     text='Download translations')

        notebook.add(PatchExecutableFrame(notebook, self.config),
                     text='Patch executable file')

        notebook.add(TranslateExternalFiles(notebook, self.config),
                     text='Translate external text files')

        tab = self.config['last_tab_opened']
        if 0 <= tab < len(notebook.tabs()):
            notebook.select(tab)

if __name__ == '__main__':
    mp.freeze_support()
    App(noconfig='--noconfig' in sys.argv).mainloop()
