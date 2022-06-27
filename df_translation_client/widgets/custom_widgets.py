import tkinter as tk
from tkinter import ttk
from typing import TypeVar, Generic, Iterable, List, Tuple, Optional


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


TComboboxValue = TypeVar("TComboboxValue")


class TypedCombobox(ttk.Combobox, Generic[TComboboxValue]):
    _values: List[TComboboxValue]

    def __init__(self, *args, values: Optional[List[TComboboxValue]] = None, **kwargs):
        super().__init__(*args, values=values, **kwargs)
        self.config(state="readonly")

        if values is None:
            values = []

        self._values = values

    def select(self, value: TComboboxValue):
        self.current(self._values.index(value))

    @property
    def values(self) -> List[TComboboxValue]:
        return self._values

    @values.setter
    def values(self, values: Optional[List[TComboboxValue]] = None):
        if values is None:
            values = []
        self["values"] = tuple(values)

    def get(self) -> Optional[TComboboxValue]:
        if self.current() == -1:  # Если ничего не выбрано
            return None
        else:
            return self._values[self.current()]


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
        return self["values"]

    @values.setter
    def values(self, values):
        self["values"] = tuple(values)


TListboxValue = TypeVar("TListboxValue")


class Listbox(tk.Listbox, Generic[TListboxValue]):
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)

        self.__var = tk.Variable()
        self.config(listvariable=self.__var)
        self.__values: Tuple[TListboxValue] = tuple()

    @property
    def values(self) -> List[TListboxValue]:
        return list(self.__values)

    @values.setter
    def values(self, values: Iterable[TListboxValue]):
        self.__values = tuple(values)
        self.__var.set(tuple(map(str, self.__values)))

    def clear(self):
        self.__values = list()
        self.delete(0, tk.END)
        self.update()

    def append(self, item: TListboxValue):
        self.insert(tk.END, str(item))
        self.yview_moveto(1.0)
        self.update()

    def selected(self) -> List[TListboxValue]:
        current_selection = self.curselection()
        return [self.__values[i] for i in current_selection]


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
        self.yview_moveto(1.0)
        self.update()

    def clear(self):
        self.configure(state=tk.NORMAL)
        self.delete(0.0, tk.END)
        if not self.enabled:
            self.configure(state=tk.DISABLED)
        self.update()

    def flush(self):
        self.update()
