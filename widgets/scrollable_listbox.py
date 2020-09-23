import tkinter as tk
from tkinter import ttk as ttk


class ScrollableListbox(tk.Frame):
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent)

        y_scrollbar = ttk.Scrollbar(self)
        x_scrollbar = ttk.Scrollbar(self, orient=tk.HORIZONTAL)

        self._var = tk.Variable()
        self._listbox = tk.Listbox(self, *args,
                                   listvariable=self._var,
                                   xscrollcommand=x_scrollbar.set,
                                   yscrollcommand=y_scrollbar.set,
                                   **kwargs)

        y_scrollbar['command'] = self._listbox.yview
        x_scrollbar['command'] = self._listbox.xview

        self.grid_columnconfigure(0, weight=1)  # the same effect as expand=1 for pack
        self.grid_rowconfigure(0, weight=1)  # the same effect as expand=1 for pack
        self._listbox.grid(row=0, column=0, sticky=tk.N+tk.S+tk.E+tk.W)
        y_scrollbar.grid(row=0, column=1, sticky=tk.N+tk.S)
        x_scrollbar.grid(row=1, column=0, sticky=tk.E+tk.W)
        self.insert = lambda index, *items: self._listbox.insert(index, *items)

    @property
    def values(self):
        return self._var.get()

    @values.setter
    def values(self, values):
        self._var.set(tuple(values))

    def clear(self):
        self._listbox.delete(0, tk.END)
        self._listbox.update()

    def curselection(self):
        return self._listbox.curselection()

    def append(self, item):
        self._listbox.insert(tk.END, item)
        self._listbox.yview_moveto('1.0')
        self._listbox.update()
