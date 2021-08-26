import re
import tkinter as tk
from tkinter import ttk as ttk

from widgets import ScrollbarFrame
from widgets.custom_widgets import Listbox, Combobox, Entry


def show_spaces(s):
    parts = re.search(r'^(\s*)(.*?)(\s*)$', s)
    return '\u2022' * len(parts.group(1)) + parts.group(2) + '\u2022' * len(parts.group(3))


class DialogDoNotFixSpaces(tk.Toplevel):
    def update_listbox_exclusions(self):
        exclusions = self.exclusions.get(self.combo_language.text, list())
        self.listbox_exclusions.values = sorted(show_spaces(item) for item in exclusions)
        self.restore_strings.update({show_spaces(s): s for s in exclusions})

    def combo_language_change_selection(self, _):
        self.update_listbox_exclusions()
        self.update_listbox_exclusions_hints()

    def update_listbox_exclusions_hints(self):
        text = self.entry_search.text
        values = ((show_spaces(key) for key in self.strings if text.lower() in key.lower())
                  if self.language == self.combo_language.text else tuple())
        self.listbox_exclusions_hints.values = values

    def entry_search_key_release(self, _):
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
            language_list.insert(0, language)
        self.language = language

        self.dictionary = dictionary or dict()
        self.strings = sorted((key for key in dictionary.keys() if key.startswith(' ') or key.endswith(' ')),
                              key=lambda x: x.lower().strip())
        self.restore_strings = {show_spaces(s): s for s in self.strings}

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

        self.listbox_exclusions: Listbox = scrollable_listbox.widget

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

        self.listbox_exclusions_hints: Listbox = scrollbar_frame.widget
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
