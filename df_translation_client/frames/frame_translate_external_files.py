import tkinter as tk
import traceback
from pathlib import Path
from tkinter import ttk

from df_gettext_toolkit.translate.batch import translate_files
from natsort import natsorted
from tkinter_layout_helpers import grid_manager, pack_manager

from df_translation_client.utils.config import Config
from df_translation_client.utils.po_languages import (
    filter_files_by_language,
    get_languages,
    get_suitable_codepages_for_directory,
)
from df_translation_client.widgets import FileEntry, ScrollbarFrame
from df_translation_client.widgets.custom_widgets import Combobox, Listbox


class TranslateExternalFiles(tk.Frame):
    def update_combo_languages(self, directory: Path):
        try:
            languages = get_languages(directory)
            self.combo_language.values = languages

            if languages:
                self.combo_language.current(0)
            else:
                self.combo_language.text = ""

            self.update_listbox_translation_files()
            self.update_combo_encoding()
        except Exception as ex:
            self.combo_language.values = tuple()
            self.combo_language.text = ""
            traceback.print_exception(ex)

    def update_listbox_translation_files(self):
        language = self.combo_language.text
        directory = self.file_entry_translation_files.path
        files = sorted(filter_files_by_language(directory, language)) if directory.exists() else tuple()
        self.listbox_translation_files.values = files

    def update_combo_encoding(self):
        if self.file_entry_translation_files.path_is_valid():
            directory = self.file_entry_translation_files.path
            language = self.combo_language.text
            self.combo_encoding.values = natsorted(get_suitable_codepages_for_directory(directory, language))

            if self.combo_encoding.values:
                self.combo_encoding.current(0)
            else:
                self.combo_encoding.text = "cp437"

    def update(self):
        super().update()
        self.update_listbox_translation_files()
        self.update_combo_encoding()
        self.update_combo_languages(self.file_entry_translation_files.path)

    def bt_search(self, translate=False):
        # TODO: add progressbar
        self.listbox_found_directories.clear()
        for message in translate_files(
            base_path=Path(self.file_entry_df_root_path.path),
            po_directory=Path(self.file_entry_translation_files.path),
            encoding=self.combo_encoding.get(),
            po_name_postfix=self.combo_language.text,
            translate=translate,
        ):
            self.listbox_found_directories.append(message)

        if translate:
            self.listbox_found_directories.append("Completed.")

    def on_translation_files_path_change(self, key, directory):
        """Save selected path to config and update languages combo"""
        self.config_section.check_and_save_path(key, directory)
        self.update_combo_languages(directory)

    def __init__(self, *args, config: Config, **kwargs):
        super().__init__(*args, **kwargs)
        self.config_section = config.init_section(section_name="translate_external_files")
        config_section = self.config_section

        with grid_manager(self, sticky=tk.NSEW, padx=2, pady=2) as grid:
            self.file_entry_df_root_path = FileEntry(
                dialog_type="askdirectory",
                default_path=config_section.get("df_root_path", ""),
                on_change=lambda path: config_section.check_and_save_path("df_root_path", path),
            )

            grid.new_row().add(tk.Label(text="Dwarf Fortress root path:"), sticky=tk.W).add(
                self.file_entry_df_root_path
            )

            self.file_entry_translation_files = FileEntry(
                dialog_type="askdirectory",
                default_path=config_section.get("translation_files_path", ""),
                on_change=lambda path: self.on_translation_files_path_change("translation_files_path", path),
            )

            grid.new_row().add(tk.Label(text="Translation files' directory:"), sticky=tk.W).add(
                self.file_entry_translation_files
            )

            self.combo_language = Combobox()
            grid.new_row().add(tk.Label(text="Language:"), sticky=tk.W).add(self.combo_language)

            directory = self.file_entry_translation_files.path
            if directory.exists():
                languages = get_languages(directory)
                self.combo_language.values = languages
                if languages:
                    self.combo_language.current(0)

            def on_combo_language_change(_event):
                self.update_listbox_translation_files()
                self.update_combo_encoding()

            self.combo_language.bind("<<ComboboxSelected>>", on_combo_language_change)

            self.combo_encoding = Combobox()
            grid.new_row().add(tk.Label(text="Encoding:"), sticky=tk.W).add(self.combo_encoding)

            self.update_combo_encoding()

            scrollbar_frame = ScrollbarFrame(widget_factory=Listbox, show_scrollbars=tk.VERTICAL)
            grid.new_row().add(scrollbar_frame).column_span(2)

            self.listbox_translation_files: Listbox = scrollbar_frame.widget
            self.update_listbox_translation_files()

            with pack_manager(tk.Frame(), side=tk.LEFT, expand=True, fill=tk.X, padx=2) as buttons:
                buttons.pack_all(
                    ttk.Button(text="Search", command=self.bt_search),
                    ttk.Button(text="Translate", command=lambda: self.bt_search(translate=True)),
                )

                grid.new_row().add(buttons.parent).column_span(2)

            scrollbar_frame = ScrollbarFrame(widget_factory=Listbox, show_scrollbars=tk.VERTICAL)
            grid.new_row().add(scrollbar_frame).column_span(2).configure(weight=1)

            self.listbox_found_directories: Listbox = scrollbar_frame.widget

            grid.columnconfigure(1, weight=1)
