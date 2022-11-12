import tkinter as tk
from contextlib import AbstractContextManager, contextmanager
from typing import Union, Generic, TypeVar


class DefaultRootWrapper:  # pragma: no cover
    @property
    def default_root(self):
        return tk._default_root  # pylint: disable=protected-access

    @default_root.setter
    def default_root(self, value):
        tk._default_root = value  # pylint: disable=protected-access


default_root_wrapper = DefaultRootWrapper()


@contextmanager
def set_parent(new_parent):
    old_root = default_root_wrapper.default_root
    default_root_wrapper.default_root = new_parent
    try:
        yield new_parent
    finally:
        default_root_wrapper.default_root = old_root


T = TypeVar("T")


class ParentSetter(AbstractContextManager, Generic[T]):
    parent: tk.Widget
    _old_root: tk.Widget

    def __init__(self, parent: Union[tk.Tk, tk.Frame, tk.Toplevel]):
        self.parent = parent

    def __enter__(self) -> T:
        self._old_root = default_root_wrapper.default_root
        default_root_wrapper.default_root = self.parent
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        default_root_wrapper.default_root = self._old_root


def pack_expand(widget: tk.Widget, **kwargs):
    widget.pack(fill=tk.BOTH, expand=True, **kwargs)


class Packer(ParentSetter["Packer"]):
    def __init__(self, parent, **kwargs):
        super().__init__(parent)
        self.parent = parent
        self.row = 0
        self.column = 0
        self.options = kwargs

    def pack_all(self, *args: tk.Widget):
        for item in args:
            item.pack(**self.options)

    def pack(self, widget: tk.Widget, **kwargs):
        widget.pack(**kwargs)
        return self

    def pack_left(self, widget: tk.Widget, **kwargs):
        widget.pack(side=tk.LEFT, **kwargs)
        return self

    def pack_right(self, widget: tk.Widget, **kwargs):
        widget.pack(side=tk.RIGHT, **kwargs)
        return self

    def pack_expanded(self, widget: tk.Widget, **kwargs):
        widget.pack(fill=tk.BOTH, expand=True, **kwargs)
        return self
