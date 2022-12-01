import re
import tkinter as tk
from copy import deepcopy
from tkinter import ttk
from typing import List, Mapping, MutableMapping, Optional

from tk_grid_helper import grid_manager

from df_translation_client.utils.tkinter_helpers import Packer
from df_translation_client.widgets import ScrollbarFrame
from df_translation_client.widgets.custom_widgets import Combobox, Entry, Listbox

SPACE_PLACEHOLDER = "•"


class HighlightedSpacesItem:
    @staticmethod
    def highlight_spaces(s):
        parts = re.search(r"^(\s*)(.*?)(\s*)$", s)
        return SPACE_PLACEHOLDER * len(parts.group(1)) + parts.group(2) + SPACE_PLACEHOLDER * len(parts.group(3))

    def __init__(self, value: str):
        self.value = value

    def __str__(self):
        return self.highlight_spaces(self.value)


class DialogDoNotFixSpaces(tk.Toplevel):
    combo_language: Combobox
    listbox_exclusions: Listbox[HighlightedSpacesItem]

    entry_filter: Entry
    listbox_exclusions_hints: Listbox[HighlightedSpacesItem]

    exclusions: Optional[MutableMapping[str, List[str]]]
    strings: List[str]

    def update_listbox_exclusions(self):
        exclusions = self.exclusions.get(self.combo_language.text, list())
        self.listbox_exclusions.values = sorted(map(HighlightedSpacesItem, exclusions), key=lambda x: x.value)

    def combo_language_change_selection(self, _):
        self.update_listbox_exclusions()
        self.update_listbox_exclusions_hints()

    def update_listbox_exclusions_hints(self):
        text: str = self.entry_filter.text.casefold()
        values = (HighlightedSpacesItem(string) for string in self.strings if text in string.casefold())
        self.listbox_exclusions_hints.values = values

    def entry_search_key_release(self, _):
        self.update_listbox_exclusions_hints()

    def bt_remove_selected(self):
        selected = self.listbox_exclusions.selected()
        if selected:
            item = selected[0].value
            self.exclusions[self.combo_language.text].remove(item)
            self.update_listbox_exclusions()

    def bt_add_selected(self):
        selected = self.listbox_exclusions_hints.selected()
        if selected:
            item = selected[0].value
            exclusions = set(self.exclusions.get(self.combo_language.text, set()))
            exclusions.add(item)
            self.exclusions[self.combo_language.text] = list(exclusions)
            self.update_listbox_exclusions()

    def __init__(
        self,
        *args,
        exclusions: Mapping[str, List[str]],
        dictionary: Optional[Mapping[str, str]],
        default_language: Optional[str] = None,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.grab_set()

        self.exclusions = dict(deepcopy(exclusions))

        self.title("Choose exclusions")

        language_list = sorted(self.exclusions.keys())

        # Move the default language to the top
        if default_language:
            if default_language in language_list:
                language_list.remove(default_language)
            language_list.insert(0, default_language)

        dictionary = dictionary or dict()
        self.strings = sorted(
            (key for key in dictionary.keys() if key.startswith(" ") or key.endswith(" ")),
            key=lambda x: x.lower().strip(),
        )

        with grid_manager(self, sticky=tk.NSEW, padx=2, pady=2) as grid:
            with Packer(tk.Frame()) as language_frame_packer:
                self.combo_language = Combobox(values=language_list)
                self.combo_language.current(0)
                self.combo_language.bind("<<ComboboxSelected>>", self.combo_language_change_selection)
                self.combo_language.bind("<Any-KeyRelease>", self.combo_language_change_selection)

                language_frame_packer.pack_left(tk.Label(text="Language:")).pack_expanded(self.combo_language)

            with Packer(tk.Frame()) as filter_frame_packer:
                self.entry_filter = Entry()
                self.entry_filter.bind("<Any-KeyRelease>", self.entry_search_key_release)

                filter_frame_packer.pack_left(tk.Label(text="Filter:")).pack_expanded(self.entry_filter)

            grid.new_row().add(language_frame_packer.parent).add(filter_frame_packer.parent)

            grid.new_row().add(ttk.Button(text="-- Remove selected --", command=self.bt_remove_selected)).add(
                ttk.Button(text="<< Add selected <<", command=self.bt_add_selected)
            )

            scrollable_listbox_exclusions = ScrollbarFrame(
                widget_factory=Listbox,
                widget_args=dict(width=40, height=20),
                show_scrollbars=tk.VERTICAL,
            )

            self.listbox_exclusions = scrollable_listbox_exclusions.widget
            self.update_listbox_exclusions()

            scrollable_listbox_hints = ScrollbarFrame(
                widget_factory=Listbox,
                widget_args=dict(width=40, height=20),
                show_scrollbars=tk.VERTICAL,
            )

            self.listbox_exclusions_hints = scrollable_listbox_hints.widget
            self.update_listbox_exclusions_hints()

            grid.new_row().add(scrollable_listbox_exclusions).add(scrollable_listbox_hints).configure(weight=1)

            grid.new_row().add(ttk.Button(text="OK", command=self.destroy)).add(
                ttk.Button(text="Cancel", command=self.cancel)
            )

            grid.columnconfigure(0, weight=1)
            grid.columnconfigure(1, weight=1)

    def cancel(self):
        self.exclusions = None
        self.destroy()

    def wait_result(self):
        self.wait_window()
        return self.exclusions
