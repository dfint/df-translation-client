import os
import string
import tkinter as tk
from os import path
from tkinter import ttk as ttk
from df_gettext_toolkit import po
from df_gettext_toolkit.translate_plain_text import translate_plain_text
from df_gettext_toolkit.translate_raws import translate_raws
from dfrus.patch_charmap import get_codepages
from config import check_and_save_path, init_section
from custom_widgets import FileEntry, ComboboxCustom, ListboxCustom
from frame_patch import filter_codepages
from cleanup import cleanup_special_symbols


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

    def update_listbox_translation_files(self, _=None, language=None):
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
                    strings = [cleanup_special_symbols(entry['msgstr']) for entry in pofile]
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
            # Swithched off for now
            # r'data_src': dict(
            #     po_filename='uncompressed',
            #     func=lambda *args: translate_plain_text(*args, join_paragraphs=True),
            # ),
            r'data\speech': dict(
                po_filename='speech',
                func=lambda *args: translate_plain_text(*args, join_paragraphs=False),
            ),
            r'raw\objects\text': dict(
                po_filename='text',
                func=lambda *args: translate_plain_text(*args, join_paragraphs=False),
            ),
        }

        # TODO: add progressbar
        self.listbox_found_directories.clear()
        for cur_dir, _, files in os.walk(self.fileentry_df_root_path.text):
            for pattern in patterns:
                if cur_dir.endswith(pattern):
                    self.listbox_found_directories.append(cur_dir + ' (%s files)' % len(files))
                    postfix = '_{}.po'.format(self.combo_language.text)
                    po_filename = os.path.join(self.fileentry_translation_files.text,
                                               patterns[pattern]['po_filename'] + postfix)

                    if translate:
                        func = patterns[pattern]['func']
                        for filename in func(po_filename, cur_dir, self.combo_encoding.get()):
                            # print(filename, file=sys.stderr)
                            self.listbox_found_directories.append(filename)

        if translate:
            self.listbox_found_directories.append("Completed.")

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
