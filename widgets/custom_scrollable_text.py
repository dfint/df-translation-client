import tkinter as tk
from tkinter import ttk as ttk


class CustomScrollableText(tk.Frame):
    @staticmethod
    def scrollbar_switcher(scrollbar, first, last):
        scrollbar.set(first, last)
        if first == '0.0' and last == '1.0':
            scrollbar.grid_remove()
        elif not scrollbar.grid_info():
            scrollbar.grid()

    def __init__(self, parent, *args, enabled=True, **kwargs):
        super().__init__(parent)

        y_scrollbar = ttk.Scrollbar(self)
        x_scrollbar = ttk.Scrollbar(self, orient=tk.HORIZONTAL)

        self.enabled = enabled
        self._text = tk.Text(self, *args,
                             xscrollcommand=lambda first, last: self.scrollbar_switcher(x_scrollbar, first, last),
                             yscrollcommand=lambda first, last: self.scrollbar_switcher(y_scrollbar, first, last),
                             state=tk.NORMAL if enabled else tk.DISABLED,
                             **kwargs)

        y_scrollbar['command'] = self._text.yview
        x_scrollbar['command'] = self._text.xview

        self.grid_columnconfigure(0, weight=1)  # the same effect as expand=1 for pack
        self.grid_rowconfigure(0, weight=1)  # the same effect as expand=1 for pack
        self._text.grid(row=0, column=0, sticky=tk.N+tk.S+tk.E+tk.W)
        y_scrollbar.grid(row=0, column=1, sticky=tk.N+tk.S)
        x_scrollbar.grid(row=1, column=0, sticky=tk.E+tk.W)

    def write(self, s):
        self._text.configure(state=tk.NORMAL)
        self._text.insert(tk.END, s)
        if not self.enabled:
            self._text.configure(state=tk.DISABLED)
        self._text.yview_moveto('1.0')
        self.update()

    def clear(self):
        self._text.configure(state=tk.NORMAL)
        self._text.delete(0.0, tk.END)
        if not self.enabled:
            self._text.configure(state=tk.DISABLED)
        self.update()

    def flush(self):
        self.update()
