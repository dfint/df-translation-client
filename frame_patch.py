import multiprocessing as mp
import string
import tkinter as tk
import dfrus
from collections import OrderedDict
from os import path
from tkinter import messagebox, ttk as ttk
from df_gettext_toolkit import po
from config import check_and_save_path, init_section
from custom_widgets import CheckbuttonVar, FileEntry, ComboboxCustom, TwoStateButton, CustomText
from dialog_dont_fix_spaces import DialogDontFixSpaces
from dfrus.patch_charmap import get_codepages
from bisect_tool import Bisect


def cleanup_spaces(d: iter, exclusions=None):
    exclusions = set(exclusions) if exclusions else set()

    for original_string, translation in d:
        if original_string and translation and original_string != translation:
            if original_string not in exclusions:
                if original_string[0] == ' ' and translation[0] not in {' ', ','}:
                    translation = ' ' + translation

                if original_string[-1] == ' ' and translation[-1] != ' ':
                    translation += ' '

            yield original_string, translation


def cleanup_special_symbols(s):
    # TODO: Make this mapping customizable
    return s.translate({0xfeff: None, 0x2019: "'", 0x201d: '"', 0x2014: '-'})


def filter_codepages(codepages, strings):
    for codepage in codepages:
        try:
            for item in strings:
                # Only one-byte encodings are supported
                if len(item.encode(codepage)) != len(item):
                    raise ValueError
            yield codepage
        except (UnicodeEncodeError, ValueError):
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


class DebugFrame(tk.Frame):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        Bisect(self).pack(fill=tk.BOTH, expand=1)


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
                    cleanup_spaces(((entry['msgid'], cleanup_special_symbols(entry['msgstr'])) for entry in pofile),
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
                strings = [cleanup_special_symbols(entry['msgstr']) for entry in pofile]
            codepages = filter_codepages(codepages, strings)
        self.combo_encoding.values = sorted(codepages,
                                            key=lambda x: int(x.strip(string.ascii_letters)))

        if self.translation_file_language not in self.config['language_codepages']:
            self.combo_encoding.current(0)
        else:
            self.combo_encoding.text = self.config['language_codepages'][self.translation_file_language]

    def __init__(self, master, config, debug=False):
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
                strings = [cleanup_special_symbols(entry['msgstr']) for entry in pofile]
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

        self.chk_add_leading_trailing_spaces = self.setup_checkbutton(
            text='Add necessary leading/trailing spaces',
            config_key='add_leading_trailing_spaces',
            default_state=True)

        self.chk_add_leading_trailing_spaces.grid(columnspan=2, sticky=tk.W)

        button_exclusions = ttk.Button(self, text='Exclusions...', command=self.bt_exclusions)
        button_exclusions.grid(row=4, column=2)

        self.debug_frame = None if not debug else DebugFrame(self)
        if self.debug_frame:
            self.debug_frame.grid(columnspan=3, sticky='NSWE')

        self.chk_debug_output = self.setup_checkbutton(
            text='Enable debugging output',
            config_key='debug_output',
            default_state=False)

        self.chk_debug_output.grid(columnspan=2, sticky=tk.W)

        self.button_patch = TwoStateButton(self,
                                           text='Patch!', command=self.bt_patch,
                                           text2='Stop!', command2=self.bt_stop)
        self.button_patch.grid(row=6, column=2)

        self.log_field = CustomText(self, width=48, height=8, enabled=False)
        self.log_field.grid(columnspan=3, sticky='NSWE')

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(7, weight=1)

        self.bind('<Destroy>', self.kill_processes)
