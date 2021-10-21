import re
import tkinter as tk
from copy import deepcopy
from tkinter import ttk as ttk
from typing import MutableMapping, List, Mapping

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
    def update_listbox_exclusions(self):
        exclusions = self.exclusions.get(self.combo_language.text, list())
        self.listbox_exclusions.values = sorted(map(HighlightedSpacesItem, exclusions), key=lambda x: x.value)

    def combo_language_change_selection(self, _):
        self.update_listbox_exclusions()
        self.update_listbox_exclusions_hints()

    def update_listbox_exclusions_hints(self):
        text: str = self.entry_search.text.casefold()
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

        self.exclusions: MutableMapping[str, List[str]] = dict(deepcopy(exclusions))

        self.title("Choose exclusions")

        language_list = sorted(self.exclusions.keys())

        # Move the default language to the top
        if default_language:
            if default_language in language_list:
                language_list.remove(default_language)
            language_list.insert(0, default_language)

        self.language = default_language

        self.dictionary = dictionary or dict()
        self.strings = sorted((key for key in self.dictionary.keys() if key.startswith(' ') or key.endswith(' ')),
                              key=lambda x: x.lower().strip())

        parent_frame = tk.Frame(self)
        tk.Label(parent_frame, text='Language:').pack(side=tk.LEFT)

        self.combo_language = Combobox(parent_frame, values=language_list)

        self.combo_language.pack(fill='both', expand=1)
        parent_frame.grid(sticky=tk.W+tk.E)

        self.combo_language.current(0)
        self.combo_language.bind('<<ComboboxSelected>>', self.combo_language_change_selection)
        self.combo_language.bind('<Any-KeyRelease>', self.combo_language_change_selection)

        bt = ttk.Button(self, text='-- Remove selected --', command=self.bt_remove_selected)
        bt.grid(column=0, row=1, sticky=tk.EW)

        scrollable_listbox = ScrollbarFrame(self, Listbox, widget_args=dict(width=40, height=20),
                                            show_scrollbars=tk.VERTICAL)
        scrollable_listbox.grid(sticky=tk.NSEW)

        self.listbox_exclusions: Listbox[HighlightedSpacesItem] = scrollable_listbox.widget

        self.update_listbox_exclusions()

        parent_frame = tk.Frame(self)
        tk.Label(parent_frame, text='Filter:').pack(side=tk.LEFT)

        self.entry_search = Entry(parent_frame)
        self.entry_search.bind('<Any-KeyRelease>', self.entry_search_key_release)
        self.entry_search.pack(fill='both', expand=1)

        parent_frame.grid(column=1, row=0, sticky=tk.W+tk.E)

        bt = ttk.Button(self, text='<< Add selected <<', command=self.bt_add_selected)
        bt.grid(column=1, row=1, sticky=tk.W+tk.E)

        scrollbar_frame = ScrollbarFrame(self, Listbox, widget_args=dict(width=40, height=20),
                                         show_scrollbars=tk.VERTICAL)
        scrollbar_frame.grid(column=1, row=2, sticky=tk.NSEW)

        self.listbox_exclusions_hints: Listbox[HighlightedSpacesItem] = scrollbar_frame.widget
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

    def wait_result(self):
        self.wait_window()
        return self.exclusions
