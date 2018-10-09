import tkinter as tk
import tkinter.ttk as ttk
from operator import itemgetter
from itertools import islice


class Bisect(tk.Frame):
    def __init__(self, *args, strings=None, **kwargs):
        super().__init__(*args, **kwargs)
        self._strings = strings
        self.tree = tree = ttk.Treeview(self)
        tree.grid(sticky='nswe')
        tree["columns"] = ("start", "end", "strings")
        tree["displaycolumns"] = tree["columns"][-1]
        tree.heading('#0', text='Tree')
        tree.heading('#1', text='Strings')

        if strings:
            self.insert_node(start=0, end=len(strings)-1)

        vscroll = ttk.Scrollbar(self, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=vscroll.set)
        vscroll.grid(row=0, column=1, sticky='ns')
        
        toolbar = tk.Frame(self)
        ttk.Button(toolbar, text="Split", command=self.split_selected_node).pack(side='left')
        ttk.Button(toolbar, text="Mark as bad", command=lambda: self.mark_selected_node(background='orange')).pack(side='left')
        ttk.Button(toolbar, text="Mark as good", command=lambda: self.mark_selected_node(background='lightgreen')).pack(side='left')
        ttk.Button(toolbar, text="Clear mark", command=lambda: self.mark_selected_node(background='white')).pack(side='left')
        toolbar.grid()

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

    def insert_node(self, parent_node='', index='end', start=0, end=0):
        if start == end:
            text='[{} : {}] ({} string)'.format(start, end, end-start+1)
            values = (start, end, repr(self._strings[start]))
        else:
            text='[{} : {}] ({} strings)'.format(start, end, end-start+1)
            if end - start + 1 <= 2:
                strings = ','.join(map(repr, islice(self._strings, start, end+1)))
            else:
                strings = '{!r} ... {!r}'.format(self._strings[start], self._strings[end])
            values = (start, end, strings)
        
        tree = self.tree
        item_id = tree.insert(parent_node, index, text=text, open=True, values=values)
        tree.item(item_id, tags=(item_id,))
        return item_id

    def split_selected_node(self):
        tree = self.tree
        item = tree.selection()
        if item and not tree.get_children(item[0]):
            start, end = map(int, tree.item(item[0], option="values")[:2])
            if start != end:
                mid = (start + end) // 2
                new_item = self.insert_node(item, start=start, end=mid)
                tree.selection_set(new_item)  # move selection to the first child
                self.insert_node(item, start=mid+1, end=end)

    def mark_selected_node(self, **kwargs):
        tree = self.tree
        for item in tree.selection():
            tree.tag_configure(item, **kwargs)

    @property
    def selected_ranges(self):
        return (map(int, self.tree.item(item, option="values")[:2]) for item in self.tree.selection())

    @property
    def filtered_strings(self):
        ranges = list(self.selected_ranges)
        if not ranges:
            return self._strings
        else:
            if len(ranges) == 1:
                # Only one row selected (optimized case)
                start, end = ranges[0]
                return islice(self._strings, start, end+1)
            else:
                # Merge ranges when multiple rows selected
                enumerated_strings = list(enumerate(self._strings))
                strings = set()
                for start, end in ranges:
                    strings |= set(islice(enumerated_strings, start, end+1))

                strings = map(itemgetter(1), sorted(strings, key=itemgetter(0)))
                return strings


if __name__ == '__main__':
    root = tk.Tk()
    bisect = Bisect(strings='Lorem ipsum dolor sit amet'.split())
    bisect.pack(fill=tk.BOTH, expand=1)
    ttk.Button(text='Get strings', command=lambda: print(list(bisect.filtered_strings))).pack()
    root.mainloop()
