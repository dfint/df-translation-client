import re
import tkinter as tk
from copy import deepcopy
from tkinter import ttk as ttk
from typing import MutableMapping, List, Mapping, Optional

from tkinter_helpers import set_parent, Grid
from widgets import ScrollbarFrame
from widgets.custom_widgets import Listbox, Combobox, Entry


class HighlightedSpacesItem:
    @staticmethod
    def highlight_spaces(s):
        parts = re.search(r'^(\s*)(.*?)(\s*)$', s)
        return '•' * len(parts.group(1)) + parts.group(2) + '•' * len(parts.group(3))

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

    def __init__(self, parent, exclusions: Mapping[str, List[str]],
                 dictionary: Mapping[str, str],
                 *args,
                 default_language: str = None,
                 **kwargs):
        super().__init__(parent, *args, **kwargs)
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
        self.strings = sorted((key for key in dictionary.keys() if key.startswith(' ') or key.endswith(' ')),
                              key=lambda x: x.lower().strip())

        with Grid(self, sticky=tk.NSEW) as grid:
            with set_parent(tk.Frame()) as language_frame:
                tk.Label(text='Language:').pack(side=tk.LEFT)
                self.combo_language = Combobox(values=language_list)
                self.combo_language.pack(fill='both', expand=1)
                self.combo_language.current(0)
                self.combo_language.bind('<<ComboboxSelected>>', self.combo_language_change_selection)
                self.combo_language.bind('<Any-KeyRelease>', self.combo_language_change_selection)

            with set_parent(tk.Frame()) as filter_frame:
                tk.Label(text='Filter:').pack(side=tk.LEFT)
                self.entry_filter = Entry()
                self.entry_filter.bind('<Any-KeyRelease>', self.entry_search_key_release)
                self.entry_filter.pack(fill='both', expand=1)

            grid.add_row(language_frame, filter_frame)

            grid.add_row(ttk.Button(text='-- Remove selected --', command=self.bt_remove_selected),
                         ttk.Button(text='<< Add selected <<', command=self.bt_add_selected))

            scrollable_listbox_exclusions = ScrollbarFrame(widget_factory=Listbox,
                                                           widget_args=dict(width=40, height=20),
                                                           show_scrollbars=tk.VERTICAL)

            self.listbox_exclusions = scrollable_listbox_exclusions.widget
            self.update_listbox_exclusions()

            scrollable_listbox_hints = ScrollbarFrame(widget_factory=Listbox,
                                                      widget_args=dict(width=40, height=20),
                                                      show_scrollbars=tk.VERTICAL)

            self.listbox_exclusions_hints = scrollable_listbox_hints.widget
            self.update_listbox_exclusions_hints()

            grid.add_row(scrollable_listbox_exclusions,
                         scrollable_listbox_hints).configure(weight=1)

            grid.add_row(ttk.Button(text="OK", command=self.destroy),
                         ttk.Button(text="Cancel", command=self.cancel))

            grid.columnconfigure(0, weight=1)
            grid.columnconfigure(1, weight=1)

    def cancel(self):
        self.exclusions = None
        self.destroy()

    def wait_result(self):
        self.wait_window()
        return self.exclusions
