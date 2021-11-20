import tkinter as tk
from functools import partial
from itertools import islice
from operator import itemgetter
from tkinter import ttk
from typing import List, Optional, Tuple, Iterable, Hashable

from bidict import bidict, MutableBidict

from .scrollbar_frame import ScrollbarFrame
from ..tkinter_helpers import Grid, Packer


class Node:
    def __init__(self, strings: List, start=0, end=-1):
        self._strings = strings
        self.start = start
        self.end = end if end >= 0 else len(strings) - 1

    def split(self) -> Tuple["Node", "Node"]:
        assert self.start != self.end
        mid = (self.start + self.end) // 2
        return Node(self._strings, self.start, mid), Node(self._strings, mid + 1, self.end)

    @property
    def size(self):
        return self.end - self.start + 1

    @property
    def tree_text(self):
        if self.size == 1:
            return f"[{self.start} : {self.end}] (1 string)"
        else:
            return f"[{self.start} : {self.end}] ({self.size} strings)"

    @property
    def items(self) -> Iterable[Tuple[str, str]]:
        return islice(self._strings, self.start, self.end + 1)

    @property
    def column_text(self) -> str:
        if self.start == self.end:
            return repr(self._strings[self.start])
        else:
            if self.end - self.start + 1 <= 2:  # One or two strings in the slice: show all strings
                return ",".join(map(repr, self.items))
            else:  # More strings: show the first and the last
                return f"{self._strings[self.start]!r} ... {self._strings[self.end]!r}"

    def __hash__(self):
        return hash((self.start, self.end))

    def __eq__(self, other: "Node"):
        return self.start == other.start and self.end == other.end

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(..., {self.start}, {self.end})"


class BisectTool(tk.Frame):
    _strings: Optional[List[Tuple[str, str]]]
    _nodes_by_item_ids: MutableBidict[Hashable, Node]

    def __init__(self, *args, strings: Optional[List[Tuple[str, str]]] = None, **kwargs):
        super().__init__(*args, **kwargs)
        with Grid(self, sticky=tk.NSEW, pady=2) as grid:
            scrollbar_frame = ScrollbarFrame(
                widget_factory=ttk.Treeview,
                show_scrollbars=tk.VERTICAL
            )

            self.tree = tree = scrollbar_frame.widget
            tree["columns"] = ("strings",)
            tree.heading("#0", text="Tree")
            tree.heading("#1", text="Strings")

            self._nodes_by_item_ids = bidict()
            self.strings = strings

            grid.add_row(scrollbar_frame).configure(weight=1)

            with Packer(tk.Frame(), side=tk.LEFT, expand=True, fill=tk.X, padx=1) as toolbar:
                toolbar.pack_all(
                    ttk.Button(text="Split", command=self.split_selected_node),
                    ttk.Button(text="Mark as bad", command=partial(self.mark_selected_node, background="orange")),
                    ttk.Button(text="Mark as good", command=partial(self.mark_selected_node, background="lightgreen")),
                    ttk.Button(text="Clear mark", command=partial(self.mark_selected_node, background="white")),
                )

                grid.add_row(toolbar.parent)

            grid.columnconfigure(0, weight=1)

    @property
    def strings(self) -> Optional[List[Tuple[str, str]]]:
        return self._strings

    @strings.setter
    def strings(self, value):
        self._strings = value
        self.tree.delete(*self.tree.get_children())
        self._nodes_by_item_ids = bidict()  # Create new empty bidict to avoid ValueDuplicationError
        if value:
            self.insert_node(Node(value))

    def insert_node(self, node: Node, parent_node: Optional[Node] = None):
        if not parent_node:
            parent_item_id = ""
        else:
            parent_item_id = self._nodes_by_item_ids.inverse[parent_node]

        item_id = self.tree.insert(
            parent_item_id,
            tk.END,
            text=node.tree_text,
            values=(node.column_text,),
            open=True,
        )

        self._nodes_by_item_ids[item_id] = node

        # Add an item id as a tag to color the row by that tag
        self.tree.item(item_id, tags=(item_id,))

    def get_item_id_of_node(self, node: Node):
        return self._nodes_by_item_ids.inverse[node]

    def get_selected_node(self) -> Optional[Node]:
        tree = self.tree
        selected_ids = tree.selection()
        if selected_ids and not tree.get_children(selected_ids[0]):
            return self._nodes_by_item_ids[selected_ids[0]]

    def split_selected_node(self):
        parent = self.get_selected_node()
        if parent and parent.start != parent.end:
            new_nodes = parent.split()

            for node in new_nodes:
                self.insert_node(parent_node=parent, node=node)

            # move selection to the first child
            item_id = self._nodes_by_item_ids.inverse[new_nodes[0]]
            self.tree.selection_set(item_id)

    def mark_selected_node(self, **kwargs):
        tree = self.tree
        for item in tree.selection():
            tree.tag_configure(item, **kwargs)

    @property
    def selected_nodes(self) -> Iterable[Node]:
        return (self._nodes_by_item_ids[item_id] for item_id in self.tree.selection())

    @property
    def filtered_strings(self):
        nodes: List[Node] = list(self.selected_nodes)
        if not nodes:
            return self._strings
        else:
            if len(nodes) == 1:
                # Only one row selected (optimized case)
                return islice(self._strings, nodes[0].start, nodes[0].end + 1)
            else:
                # Merge ranges when multiple rows selected
                enumerated_strings = list(enumerate(self._strings))
                strings = set()
                for node in nodes:
                    strings |= set(islice(enumerated_strings, node.start, node.end + 1))

                # Restore original order of the strings
                strings = map(itemgetter(1), sorted(strings, key=itemgetter(0)))
                return strings
