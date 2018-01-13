import tkinter as tk
import tkinter.ttk as ttk

from tkinter import filedialog
from os import path
from collections import namedtuple


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
    def values(self, values):
        self['values'] = tuple(values)


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


class CustomText(tk.Frame):
    @staticmethod
    def scrollbar_switcher(scrollbar, first, last):
        scrollbar.set(first, last)
        if first == '0.0' and last == '1.0':
            scrollbar.grid_remove()
        elif not scrollbar.grid_info():
            scrollbar.grid()
    
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
        # Use self.default_path only if self.entry.text is empty (Captain Obvious)
        self.default_path = self.entry.text or self.default_path
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

        if file_path:  # if not cancelled
            self.entry.text = file_path

            if self.on_change is not None and file_path != self._prev_value:
                self.on_change(file_path)

            self._prev_value = file_path

    def on_entry_keyup(self, event):
        if event.widget.text != self._prev_value:
            self.on_change(event.widget.text)
            self._prev_value = event.widget.text

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
        self._prev_value = self.default_path
        self.entry.pack(fill='x', expand=1)
        if self.on_change is not None:
            self.entry.bind('<KeyRelease>', func=self.on_entry_keyup)
    
    @property
    def text(self):
        return self.entry.text

    def path_is_valid(self):
        return self.text and path.exists(self.text)


class TwoStateButton(ttk.Button):
    def _action(self):
        command = self._state[0].command
        if command():
            self.swap_state()

    def swap_state(self):
        self._state.reverse()
        self['text'] = self._state[0].text

    def reset_state(self):
        self._state = list(self._initial_state)
        self['text'] = self._state[0].text

    def __init__(self, parent, text, command, text2, command2, **kwargs):
        TextCommand = namedtuple('TextCommand', 'text,command')
        self._initial_state = (TextCommand(text, command), TextCommand(text2, command2))
        self._state = list(self._initial_state)
        super().__init__(parent, text=text, command=self._action, **kwargs)
