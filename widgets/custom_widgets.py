import tkinter as tk
import tkinter.ttk as ttk


class Checkbutton(ttk.Checkbutton):
    def __init__(self, *args, **kwargs):
        self._var = tk.BooleanVar()
        super().__init__(*args, variable=self._var, **kwargs)

    @property
    def is_checked(self):
        return self._var.get()

    @is_checked.setter
    def is_checked(self, value):
        self._var.set(value)


class Entry(tk.Entry):
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


class Combobox(ttk.Combobox):
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


class Listbox(tk.Listbox):
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)

        self._var = tk.Variable()
        self.config(listvariable=self._var)

    @property
    def values(self):
        return self._var.get()

    @values.setter
    def values(self, values):
        self._var.set(tuple(values))

    def clear(self):
        self.delete(0, tk.END)
        self.update()

    def append(self, item):
        self.insert(tk.END, item)
        self.yview_moveto('1.0')
        self.update()


class Text(tk.Text):
    def __init__(self, parent, *args, enabled=True, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.enabled = enabled
        self.config(state=tk.NORMAL if enabled else tk.DISABLED)

    def write(self, s):
        self.config(state=tk.NORMAL)
        self.insert(tk.END, s)
        if not self.enabled:
            self.configure(state=tk.DISABLED)
        self.yview_moveto('1.0')
        self.update()

    def clear(self):
        self.configure(state=tk.NORMAL)
        self.delete(0.0, tk.END)
        if not self.enabled:
            self.configure(state=tk.DISABLED)
        self.update()

    def flush(self):
        self.update()
