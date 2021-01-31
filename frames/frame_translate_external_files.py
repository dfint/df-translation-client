from operator import pos
import tkinter as tk
from tkinter import messagebox, ttk
from df_gettext_toolkit import po
from df_gettext_toolkit.translate_compressed import translate_compressed
from df_gettext_toolkit.translate_plain_text import translate_plain_text
from df_gettext_toolkit.translate_raws import translate_raws
from dfrus.patch_charmap import get_codepages
from natsort import natsorted
from pathlib import Path

from config import Config
from widgets import FileEntry, ScrollableListbox
from widgets.custom_widgets import Combobox
from cleanup import cleanup_special_symbols

from .frame_patch import filter_codepages


class TranslateExternalFiles(tk.Frame):
    @staticmethod
    def get_languages(directory):
        languages = set()
        directory = Path(directory)
        for filename in directory.glob('*.po'):
            with open(directory / filename, encoding='utf-8') as file:
                languages.add(po.PoReader(file).meta['Language'])

        return sorted(languages)

    def update_combo_languages(self, directory):
        if Path(directory).exists():
            languages = self.get_languages(directory)
            self.combo_language.values = languages

            if languages:
                self.combo_language.current(0)
            else:
                self.combo_language.text = ''

            self.update_listbox_translation_files(language=self.combo_language.text)
            self.update_combo_encoding()
        else:
            self.combo_language.values = tuple()
            self.combo_language.text = ''

    def save_path_to_config(self, key, directory):
        self.config_section.check_and_save_path(key, directory)
        self.update_combo_languages(directory)

    @staticmethod
    def filter_files_by_language(directory: Path, language):
        for filename in directory.glob("*.po"):
            with open(filename, encoding='utf-8') as file:
                if po.PoReader(file).meta['Language'] == language:
                    yield filename.name

    def update_listbox_translation_files(self, language=None):
        language = self.combo_language.text if not language else language
        directory = Path(self.file_entry_translation_files.text)
        files = self.filter_files_by_language(directory, language) if directory.exists() else tuple()
        self.listbox_translation_files.values = files

    def update_combo_encoding(self, _=None):
        language = self.combo_language.text
        directory = Path(self.file_entry_translation_files.text)
        # TODO: Unify with PatchExecutableFrame.update_combo_encoding()
        if directory.exists():
            files = self.filter_files_by_language(directory, language)
            codepages = get_codepages().keys()
            for file in files:
                with open(directory / file, 'r', encoding='utf-8') as fn:
                    pofile = po.PoReader(fn)
                    strings = [cleanup_special_symbols(entry['msgstr']) for entry in pofile]
                codepages = filter_codepages(codepages, strings)
            self.combo_encoding.values = natsorted(codepages)

            if self.combo_encoding.values:
                self.combo_encoding.current(0)
            else:
                self.combo_encoding.text = 'cp437'

    def bt_search(self, translate=False):
        patterns = {
            'raw/objects': dict(
                po_filename='raw-objects',
                func=translate_raws,
            ),
            'data': dict(
                po_filename='uncompressed',
                func=lambda *args: translate_compressed(*args),
            ),
            'data/speech': dict(
                po_filename='speech',
                func=lambda *args: translate_plain_text(*args, join_paragraphs=False),
            ),
            'raw/objects/text': dict(
                po_filename='text',
                func=lambda *args: translate_plain_text(*args, join_paragraphs=False),
            ),
        }

        # TODO: add progressbar
        self.listbox_found_directories.clear()
        base_path = self.file_entry_df_root_path.text
        po_directory = Path(self.file_entry_translation_files.text)
        for cur_dir in Path(base_path).rglob("*"):
            if cur_dir.is_dir():
                for pattern in patterns:
                    if cur_dir.match('*/' + pattern):
                        self.listbox_found_directories.append(f"Matched {pattern} pattern")
                        base_name = patterns[pattern]['po_filename']
                        postfix = self.combo_language.text
                        po_filename = f"{base_name}_{postfix}.po"

                        po_file_path = po_directory / po_filename

                        if not po_file_path.exists():
                            messagebox.showerror(title="error",
                                                 message=f"File {po_filename} doesn't exist or it is a directory")
                            return

                        if po_file_path.is_dir():
                            messagebox.showerror(title="error",
                                                 message=f"{po_filename} is a directory")
                            return

                        if translate:
                            func = patterns[pattern]['func']
                            for filename in func(po_file_path, cur_dir, self.combo_encoding.get()):
                                # print(filename, file=sys.stderr)
                                self.listbox_found_directories.append(filename)

        if translate:
            self.listbox_found_directories.append("Completed.")

    def __init__(self, master, config: Config, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.config_section = config.init_section(section_name='translate_external_files')
        config_section = self.config_section

        tk.Label(self, text='Dwarf Fortress root path:').grid()

        self.file_entry_df_root_path = FileEntry(
            self,
            dialog_type='askdirectory',
            default_path=config_section.get('df_root_path', ''),
            on_change=lambda text: self.save_path_to_config('df_root_path', text),
        )
        self.file_entry_df_root_path.grid(row=0, column=1, sticky='WE')

        tk.Label(self, text="Translation files' directory:").grid()

        self.file_entry_translation_files = FileEntry(
            self,
            dialog_type='askdirectory',
            default_path=config_section.get('translation_files_path', ''),
            on_change=lambda path: self.save_path_to_config('translation_files_path', path),
        )
        self.file_entry_translation_files.grid(row=1, column=1, sticky='WE')

        tk.Label(self, text="Language:").grid()
        self.combo_language = Combobox(self)
        self.combo_language.grid(row=2, column=1, sticky='WE')

        directory = Path(self.file_entry_translation_files.text)
        if directory.exists():
            languages = self.get_languages(directory)
            self.combo_language.values = languages
            if languages:
                self.combo_language.current(0)

        def on_combo_language_change(_event):
            self.update_listbox_translation_files()
            self.update_combo_encoding()

        self.combo_language.bind('<<ComboboxSelected>>', on_combo_language_change)

        tk.Label(self, text="Encoding:").grid()
        self.combo_encoding = Combobox(self)
        self.combo_encoding.grid(row=3, column=1, sticky='WE')

        self.update_combo_encoding()

        self.listbox_translation_files = ScrollableListbox(self)
        self.listbox_translation_files.grid(columnspan=2, sticky='NSWE')
        self.update_listbox_translation_files(language=self.combo_language.text)

        ttk.Button(self, text='Search', command=self.bt_search).grid()
        ttk.Button(self, text='Translate', command=lambda: self.bt_search(translate=True)).grid(row=5, column=1)

        self.listbox_found_directories = ScrollableListbox(self)
        self.listbox_found_directories.grid(columnspan=2, sticky='NSWE')

        self.grid_columnconfigure(1, weight=1)

    def update(self):
        super().update()
        self.update_listbox_translation_files()
        self.update_combo_encoding()
        self.update_combo_languages(self.file_entry_translation_files.text)
