import tkinter as tk
from contextlib import AbstractContextManager, contextmanager
from typing import List, Union


@contextmanager
def set_parent(new_parent):
    old_root = tk._default_root
    tk._default_root = new_parent
    yield new_parent
    tk._default_root = old_root


class Cell:
    def __init__(self, widget=None, columnspan=1, **grid_options):
        self.widget = widget
        self.grid_options = grid_options
        self.grid_options["columnspan"] = columnspan

    @property
    def columnspan(self):
        return self.grid_options["columnspan"]

    @columnspan.setter
    def columnspan(self, value):
        self.grid_options["columnspan"] = value


class Row:
    def __init__(self, parent, index, grid_options):
        self.parent = parent
        self.index = index
        self.grid_options = grid_options

    def add_cells(self, *args: Union[str, type(...), Cell, tk.Widget]):
        cells: List[Cell] = list()

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
                cell = Cell(tk.Label(self.parent, text=item), column=column, columnspan=1, sticky=tk.W)
            elif isinstance(item, Cell):
                item.grid_options["column"] = column
                cell = item
                column_span = item.columnspan
            else:
                cell = Cell(item, column=column, columnspan=1)

            column += column_span
            if cell:
                cells.append(cell)

        for cell in cells:
            grid_options = dict(self.grid_options)
            grid_options.update(cell.grid_options)
            cell.widget.grid(row=self.index, **grid_options)

        return cells

    def configure(self, **kwargs):
        self.parent.grid_rowconfigure(self.index, **kwargs)


class Grid(AbstractContextManager):
    def __init__(self, parent=None, **kwargs):
        self.parent = parent
        self.row = 0
        self.column = 0
        self.grid_options = kwargs

    def add(self, widget, columnspan=1, **kwargs):
        grid_options = dict(self.grid_options)
        grid_options.update(dict(row=self.row, column=self.column))
        grid_options.update(kwargs)

        widget.grid(columnspan=columnspan,
                    **grid_options)

        self.column += columnspan

    def add_row(self, *args: Union[str, type(...), Cell, tk.Widget]) -> Row:
        row = Row(self.parent, self.row, self.grid_options)
        cells = row.add_cells(*args)

        if cells:
            self.column = 0
            self.row += 1

        return row

    def __enter__(self) -> "Grid":
        self._old_root = tk._default_root
        tk._default_root = self.parent
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        tk._default_root = self._old_root

    def columnconfigure(self, i, *args, **kwargs):
        self.parent.grid_columnconfigure(i, *args, **kwargs)

    def rowconfigure(self, i, *args, **kwargs):
        self.parent.grid_rowconfigure(i, *args, **kwargs)


class Packer(AbstractContextManager):
    def __init__(self, parent=None, **kwargs):
        self.parent = parent
        self.row = 0
        self.column = 0
        self.options = kwargs

    def pack_all(self, *args: tk.Widget):
        for item in args:
            item.pack(**self.options)

    def __enter__(self) -> "Packer":
        self._old_root = tk._default_root
        tk._default_root = self.parent
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        tk._default_root = self._old_root
