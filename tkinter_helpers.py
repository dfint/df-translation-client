import tkinter as tk
from contextlib import AbstractContextManager, contextmanager
from typing import List, Union, Mapping, Any, Optional, Generic, TypeVar


class DefaultRootWrapper:  # pragma: no cover
    @property
    def default_root(self):
        return tk._default_root

    @default_root.setter
    def default_root(self, value):
        tk._default_root = value


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

    def __init__(self, parent: Union[tk.Tk, tk.Frame, tk.Toplevel]):
        self.parent = parent

    def __enter__(self) -> T:
        self._old_root = default_root_wrapper.default_root
        default_root_wrapper.default_root = self.parent
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        default_root_wrapper.default_root = self._old_root


class GridCell:
    widget: tk.Widget
    row: Optional[int]
    column: Optional[int]
    rowspan: int
    columnspan: int
    grid_options: Mapping[str, Any]

    def __init__(self, widget, row=None, column=None, rowspan=1, columnspan=1, **grid_options):
        self.widget = widget
        self.row = row
        self.column = column
        self.rowspan = rowspan
        self.columnspan = columnspan
        self.grid_options = grid_options

    def grid(self, **kwargs):
        options = dict(kwargs)
        options.update(self.grid_options)  # grid_options of the cell will override options passed as grid parameters
        assert self.row is not None and self.column is not None
        self.widget.grid(row=self.row, column=self.column,
                         rowspan=self.rowspan, columnspan=self.columnspan,
                         **options)


class Row:
    def __init__(self, parent, index, grid_options):
        self.parent = parent
        self.index = index
        self.grid_options = grid_options

    def add_cells(self, *args: Union[str, type(...), GridCell, tk.Widget]):
        cells: List[GridCell] = list()

        column = 0
        for item in args:
            column_span = 1
            if item is ...:
                # Ellipsis argument doesn't create a new cell, but just enlarges columnspan of the previous cell
                # or acts as a placeholder for an empty cell if there is no non-empty cells
                # to the left in the current row
                if cells:
                    cells[-1].columnspan += 1
                cell = None
            elif isinstance(item, str):
                cell = GridCell(tk.Label(self.parent, text=item),
                                row=self.index, column=column, sticky=tk.W)
            elif isinstance(item, GridCell):
                item.column = column
                item.row = self.index
                column_span = item.columnspan
                cell = item
            else:
                cell = GridCell(item, row=self.index, column=column)

            column += column_span
            if cell:
                cells.append(cell)

        for cell in cells:
            cell.grid(**self.grid_options)

        return cells

    def configure(self, **kwargs):
        self.parent.grid_rowconfigure(self.index, **kwargs)


class Grid(ParentSetter["Grid"]):
    def __init__(self, parent, **kwargs):
        super().__init__(parent)
        self.parent = parent
        self.row = 0
        self.column = 0
        self.grid_options = kwargs

    def add(self, widget, row: Optional[int] = None, column: Optional[int] = None, columnspan=1, rowspan=1, **kwargs):
        grid_options = dict(self.grid_options)
        grid_options.update(kwargs)  # Options from arguments will override global grid options
        row = row if row is not None else self.row
        column = column if column is not None else self.column
        widget.grid(row=row, column=column,
                    rowspan=rowspan, columnspan=columnspan,
                    **grid_options)

        self.column += columnspan

    def add_row(self, *args: Union[str, type(...), GridCell, tk.Widget]) -> Row:
        row = Row(self.parent, self.row, self.grid_options)
        cells = row.add_cells(*args)

        if cells:
            self.column = 0
            self.row += 1

        return row

    def columnconfigure(self, i, *args, **kwargs):
        self.parent.grid_columnconfigure(i, *args, **kwargs)

    def rowconfigure(self, i, *args, **kwargs):
        self.parent.grid_rowconfigure(i, *args, **kwargs)


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

    def left(self, widget: tk.Widget, **kwargs):
        widget.pack(side=tk.LEFT, **kwargs)
        return self

    def right(self, widget: tk.Widget, **kwargs):
        widget.pack(side=tk.RIGHT, **kwargs)
        return self

    def expand(self, widget: tk.Widget, **kwargs):
        widget.pack(fill=tk.BOTH, expand=True, **kwargs)
        return self
