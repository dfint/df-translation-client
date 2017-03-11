import tkinter as tk
import tkinter.ttk as ttk

from tkinter import filedialog
from os import path


class CheckbuttonVar(ttk.Checkbutton):
    def __init__(self, *args, **kwargs):
        self._var = tk.BooleanVar()
        super().__init__(*args, variable=self._var, **kwargs)

    @property
    def is_checked(self):
        return self._var.get()

    @is_checked.setter
    def is_checked(self, value):
        self._var.set(value)


class EntryCustom(ttk.Entry):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    
    def _set(self, value):
        self.delete(0, tk.END)
        self.insert(0, value)

    @property
    def text(self):
        return self.get()

    @text.setter
    def text(self, value: str):
        self._set(value)


class ComboboxCustom(ttk.Combobox):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def _set(self, value):
        self.delete(0, tk.END)
        self.insert(0, value)

    @property
    def text(self):
        return self.get()

    @text.setter
    def text(self, value: str):
        self._set(value)

    @property
    def values(self):
        return self['values']

    @values.setter
    def values(self, values: tuple):
        self['values'] = values


class ListboxCustom(tk.Frame):
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent)

        yscrollbar = ttk.Scrollbar(self)
        xscrollbar = ttk.Scrollbar(self, orient=tk.HORIZONTAL)

        self._var = tk.Variable()
        self._listbox = tk.Listbox(self, *args,
                                   listvariable=self._var,
                                   xscrollcommand=xscrollbar.set,
                                   yscrollcommand=yscrollbar.set,
                                   **kwargs)

        yscrollbar['command'] = self._listbox.yview
        xscrollbar['command'] = self._listbox.xview

        self.grid_columnconfigure(0, weight=1)  # the same effect as expand=1 for pack
        self.grid_rowconfigure(0, weight=1)  # the same effect as expand=1 for pack
        self._listbox.grid(row=0, column=0, sticky=tk.N+tk.S+tk.E+tk.W)
        yscrollbar.grid(row=0, column=1, sticky=tk.N+tk.S)
        xscrollbar.grid(row=1, column=0, sticky=tk.E+tk.W)

    @property
    def values(self):
        return self._var.get()

    @values.setter
    def values(self, values: tuple):
        self._var.set(values)

    def clear(self):
        self._listbox.delete(0, tk.END)

    def curselection(self):
        return self._listbox.curselection()


class CustomText(tk.Frame):
    @staticmethod
    def scrollbar_switcher(scrollbar, first, last):
        scrollbar.set(first, last)
        if first == '0.0' and last == '1.0':
            scrollbar.grid_remove()
            scrollbar.visible = False
        elif not scrollbar.visible:
            scrollbar.grid()
            scrollbar.visible = True
    
    def __init__(self, parent, *args, enabled=True, **kwargs):
        super().__init__(parent)

        yscrollbar = ttk.Scrollbar(self)
        xscrollbar = ttk.Scrollbar(self, orient=tk.HORIZONTAL)

        self.enabled = enabled
        self._text = tk.Text(self, *args,
                             xscrollcommand=lambda first, last: self.scrollbar_switcher(xscrollbar, first, last),
                             yscrollcommand=lambda first, last: self.scrollbar_switcher(yscrollbar, first, last),
                             state=tk.NORMAL if enabled else tk.DISABLED,
                             **kwargs)

        yscrollbar['command'] = self._text.yview
        xscrollbar['command'] = self._text.xview

        self.grid_columnconfigure(0, weight=1)  # the same effect as expand=1 for pack
        self.grid_rowconfigure(0, weight=1)  # the same effect as expand=1 for pack
        self._text.grid(row=0, column=0, sticky=tk.N+tk.S+tk.E+tk.W)
        yscrollbar.grid(row=0, column=1, sticky=tk.N+tk.S)
        xscrollbar.grid(row=1, column=0, sticky=tk.E+tk.W)
        yscrollbar.visible = True
        xscrollbar.visible = False
    
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


class FileEntry(tk.Frame):
    def bt_browse(self):
        file_path = ''

        self.default_path = self.default_path or self.entry.text

        if self.dialogtype == 'askopenfilename':
            if path.isfile(self.default_path):
                initialdir = None
                initialfile = self.default_path
            else:
                initialdir = self.default_path
                initialfile = None

            file_path = filedialog.askopenfilename(filetypes=self.filetypes,
                                                   initialdir=initialdir, initialfile=initialfile)
        elif self.dialogtype == 'askdirectory':
            file_path = filedialog.askdirectory(initialdir=self.default_path)

        if file_path:
            self.entry.text = file_path

        if self.on_change is not None:
            self.on_change(file_path)

    def __init__(self, *args, button_text=None, default_path=None, on_change=None, filetypes=None,
                 dialogtype='askopenfilename', **kwargs):
        super().__init__(*args, **kwargs)

        if button_text is None:
            button_text = 'Browse...'

        self.filetypes = filetypes or []
        self.on_change = on_change
        self.default_path = default_path or ''
        self.dialogtype = dialogtype

        self.button = ttk.Button(self, text=button_text, command=self.bt_browse)
        self.button.pack(side='right')

        self.entry = EntryCustom(self)
        self.entry.text = self.default_path
        self.entry.pack(fill='x', expand=1)
        if self.on_change is not None:
            self.entry.bind('<KeyPress>', func=lambda event: self.on_change(event.widget.text))
    
    @property
    def text(self):
        return self.entry.text
