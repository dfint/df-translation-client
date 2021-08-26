import codecs
import importlib
import multiprocessing as mp
import tkinter as tk
from collections import OrderedDict
from pathlib import Path
from tkinter import messagebox, ttk

from df_gettext_toolkit import parse_po
from df_gettext_toolkit.fix_translated_strings import fix_spaces, cleanup_string
from dfrus import dfrus
from dfrus.patch_charmap import get_codepages, get_encoder
from natsort import natsorted

from config import Config
from widgets import FileEntry, BisectTool, TwoStateButton, ScrollbarFrame
from widgets.custom_widgets import Checkbutton, Combobox, Text
from .dialog_do_not_fix_spaces import DialogDoNotFixSpaces


def filter_codepages(encodings, strings):
    for encoding in encodings:
        try:
            encoder_function = codecs.getencoder(encoding)
        except LookupError:
            encoder_function = get_encoder(encoding)
        
        try:
            for text in strings:
                encoded_text = encoder_function(text)[0]
                # Only one-byte encodings are supported (but shorter result is allowed)
                if len(encoded_text) > len(text): 
                    raise ValueError
            yield encoding
        except (UnicodeEncodeError, ValueError, LookupError):
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
    @staticmethod
    def reload():
        importlib.reload(dfrus)

    def __init__(self, *args, dictionary=None, **kwargs):
        super().__init__(*args, **kwargs)
        ttk.Button(self, text='Reload dfrus', command=self.reload).pack()
        self.bisect = BisectTool(self, strings=list(dictionary.items()))
        self.bisect.pack(fill=tk.BOTH, expand=1)


class PatchExecutableFrame(tk.Frame):
    def update_log(self, message_queue):
        try:
            message = []
            
            while message_queue.poll():
                message.append(message_queue.recv())
            
            self.log_field.write(''.join(message))

            if not self.dfrus_process.is_alive():
                self.log_field.write('\n[PROCESS FINISHED]')
                self.button_patch.reset_state()
            else:
                self.after(100, self.update_log, message_queue)
        except (EOFError, BrokenPipeError):
            self.log_field.write('\n[MESSAGE QUEUE/PIPE BROKEN]')
            self.button_patch.reset_state()

    def load_dictionary(self, translation_file):
        with open(translation_file, 'r', encoding='utf-8') as fn:
            pofile = parse_po.PoReader(fn)
            meta = pofile.meta
            exclusions = self.exclusions.get(meta['Language'], self.exclusions)
            dictionary = OrderedDict(
                (entry['msgid'],
                 fix_spaces(entry['msgid'], cleanup_string(entry['msgstr']), exclusions, exclusions))
                for entry in pofile
            )
        return dictionary

    @property
    def dictionary(self):
        if not self._dictionary:
            translation_file = self.fileentry_translation_file.text
            if self.fileentry_translation_file.path_is_valid():
                self._dictionary = self.load_dictionary(translation_file)
        return self._dictionary

    def bt_patch(self):
        if self.dfrus_process is not None and self.dfrus_process.is_alive():
            return False

        executable_file = self.file_entry_executable_file.text

        if not executable_file or not Path(executable_file).exists():
            messagebox.showerror('Error', 'Valid path to an executable file must be specified')
        elif not self.dictionary:
            messagebox.showerror('Error', "Dictionary wasn't loaded")
        else:
            if not self.debug_frame:
                dictionary = self.dictionary
            else:
                dictionary = OrderedDict(self.debug_frame.bisect.filtered_strings)

            self.config_section['last_encoding'] = self.combo_encoding.text

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
                    stdout=ProcessMessageWrapper(child_conn),
                    stderr=ProcessMessageWrapper(child_conn)
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
        if translation_file and Path(translation_file).exists():
            with open(translation_file, 'r', encoding='utf-8') as fn:
                pofile = parse_po.PoReader(fn)
                meta = pofile.meta
                language = meta['Language']
                dictionary = {entry['msgid']: entry['msgstr'] for entry in pofile}

        dialog = DialogDoNotFixSpaces(self, self.config_section['fix_space_exclusions'], language, dictionary)
        self.config_section['fix_space_exclusions'] = dialog.exclusions or self.config_section['fix_space_exclusions']
        self.exclusions = self.config_section['fix_space_exclusions']

    def setup_checkbutton(self, text, config_key, default_state):
        config = self.config_section

        def save_checkbox_state(event, option_name):
            config[option_name] = not event.widget.is_checked  # Event occurs before the widget changes state

        check = Checkbutton(self, text=text)
        check.bind('<1>', lambda event: save_checkbox_state(event, config_key))
        check.is_checked = config[config_key] = config.get(config_key, default_state)
        return check

    def update_combo_encoding(self, text):
        self.config_section.check_and_save_path('df_exe_translation_file', text)

        # Update codepage combobox
        # TODO: Cache supported codepages' list
        codepages = get_codepages().keys()
        if self.fileentry_translation_file.path_is_valid():
            translation_file = self.fileentry_translation_file.text
            with open(translation_file, 'r', encoding='utf-8') as fn:
                pofile = parse_po.PoReader(fn)
                self.translation_file_language = pofile.meta['Language']
                strings = [cleanup_string(entry['msgstr']) for entry in pofile]
            codepages = filter_codepages(codepages, strings)
        self.combo_encoding.values = natsorted(codepages)

        if self.translation_file_language not in self.config_section['language_codepages']:
            if self.combo_encoding.values:
                self.combo_encoding.current(0)
            else:
                self.combo_encoding.text = 'cp437'
        else:
            self.combo_encoding.text = self.config_section['language_codepages'][self.translation_file_language]

    def __init__(self, master, config: Config, debug=False):
        super().__init__(master)

        self.config_section = config.init_section(
            section_name='patch_executable',
            defaults=dict(
                fix_space_exclusions=dict(ru=['Histories of ']),
                language_codepages=dict(),
            )
        )

        self.exclusions = self.config_section['fix_space_exclusions']

        self.dfrus_process = None

        self._dictionary = None

        tk.Label(self, text='DF executable file:').grid()

        self.file_entry_executable_file = FileEntry(
            self,
            dialog_type='askopenfilename',
            filetypes=[('Executable files', '*.exe')],
            default_path=self.config_section.get('df_executable', ''),
            on_change=lambda text: self.config_section.check_and_save_path('df_executable', text),
        )
        self.file_entry_executable_file.grid(column=1, row=0, columnspan=2, sticky='EW')

        tk.Label(self, text='DF executable translation file:').grid()

        def on_translation_file_change(text):
            self.update_combo_encoding(text)
            self._dictionary = None  # Clear cached dictionary

        self.fileentry_translation_file = FileEntry(
            self,
            dialog_type='askopenfilename',
            filetypes=[
                ("Hardcoded strings' translation", '*hardcoded*.po'),
                ('Translation files', '*.po'),
                # ('csv file', '*.csv'), # @TODO: Currently not supported
            ],
            default_path=self.config_section.get('df_exe_translation_file', ''),
            on_change=on_translation_file_change,
            change_color=True
        )
        self.fileentry_translation_file.grid(column=1, row=1, columnspan=2, sticky='EW')

        tk.Label(self, text='Encoding:').grid()

        self.combo_encoding = Combobox(self)
        self.combo_encoding.grid(column=1, row=2, sticky=tk.E + tk.W)

        codepages = get_codepages().keys()

        if not self.fileentry_translation_file.path_is_valid():
            self.translation_file_language = None
        else:
            translation_file = self.fileentry_translation_file.text
            with open(translation_file, 'r', encoding='utf-8') as fn:
                pofile = parse_po.PoReader(fn)
                self.translation_file_language = pofile.meta['Language']
                strings = [cleanup_string(entry['msgstr']) for entry in pofile]
            codepages = filter_codepages(codepages, strings)

        self.combo_encoding.values = natsorted(codepages)

        if 'last_encoding' in self.config_section:
            self.combo_encoding.text = self.config_section['last_encoding']
        elif self.combo_encoding.values:
            self.combo_encoding.current(0)

        def save_encoding_into_config(event):
            self.config_section['last_encoding'] = event.widget.text
            if self.translation_file_language:
                self.config_section['language_codepages'][self.translation_file_language] = event.widget.text

        self.combo_encoding.bind('<<ComboboxSelected>>', func=save_encoding_into_config)

        # FIXME: chk_do_not_patch_charmap does nothing
        self.chk_do_not_patch_charmap = self.setup_checkbutton(
            text="Don't patch charmap table",
            config_key='do_not_patch_charmap',
            default_state=False)

        self.chk_do_not_patch_charmap.grid(column=1, sticky=tk.W)

        self.chk_add_leading_trailing_spaces = self.setup_checkbutton(
            text='Add necessary leading/trailing spaces',
            config_key='add_leading_trailing_spaces',
            default_state=True)

        self.chk_add_leading_trailing_spaces.grid(columnspan=2, sticky=tk.W)

        button_exclusions = ttk.Button(self, text='Exclusions...', command=self.bt_exclusions)
        button_exclusions.grid(row=4, column=2)

        self.debug_frame = None if not debug else DebugFrame(self, dictionary=self.dictionary)
        if self.debug_frame:
            self.debug_frame.grid(columnspan=3, sticky='NSWE')
            self.grid_rowconfigure(5, weight=1)

        self.chk_debug_output = self.setup_checkbutton(
            text='Enable debugging output',
            config_key='debug_output',
            default_state=False)

        self.chk_debug_output.grid(columnspan=2, sticky=tk.W)

        self.button_patch = TwoStateButton(self,
                                           text='Patch!', command=self.bt_patch,
                                           text2='Stop!', command2=self.bt_stop)
        self.button_patch.grid(row=6, column=2)

        scrollbar_frame = ScrollbarFrame(self, Text,
                                         widget_args=dict(width=48, height=8, enabled=False),
                                         show_scrollbars=tk.VERTICAL)
        scrollbar_frame.grid(columnspan=3, sticky=tk.NSEW)
        self.grid_rowconfigure(scrollbar_frame.grid_info()['row'], weight=1)

        self.log_field: Text = scrollbar_frame.widget

        self.grid_columnconfigure(1, weight=1)
        
        self.bind('<Destroy>', self.kill_processes)
