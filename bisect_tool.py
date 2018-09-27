import tkinter as tk
import tkinter.ttk as ttk


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
        hscroll = ttk.Scrollbar(self, orient=tk.HORIZONTAL, command=tree.xview)
        tree.configure(xscrollcommand=hscroll.set, yscrollcommand=vscroll.set)
        vscroll.grid(row=0, column=1, sticky='ns')
        hscroll.grid(row=1, column=0, columnspan=4, sticky='we')
        
        toolbar = tk.Frame(self)
        ttk.Button(toolbar, text="Split", command=self.split_selected_node).pack(side='left')
        ttk.Button(toolbar, text="Mark as bad", command=lambda: self.mark_selected_node(foreground='red')).pack(side='left')
        ttk.Button(toolbar, text="Mark as good", command=lambda: self.mark_selected_node(foreground='green')).pack(side='left')
        ttk.Button(toolbar, text="Clear mark", command=lambda: self.mark_selected_node(foreground='black')).pack(side='left')
        toolbar.grid(row=2, column=0)

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

    def insert_node(self, parent_node='', index='end', start=0, end=0):
        if start != end:
            text='[{} : {}] ({} strings)'.format(start, end, end-start+1)
            values = (start, end, '{!r} ... {!r}'.format(self._strings[start], self._strings[end]))
        else:
            text='[{} : {}] ({} string)'.format(start, end, end-start+1)
            values = (start, end, repr(self._strings[start]))
        
        tree = self.tree
        item_id = tree.insert(parent_node, index, text=text, open=True, values=values)
        tree.item(item_id, tags=(item_id,))

    def split_selected_node(self):
        tree = self.tree
        item = tree.selection()
        if item:
            start, end = map(int, tree.item(item[0], option="values")[:2])
            if start != end:
                mid = (start + end) // 2
                self.insert_node(item, start=start, end=mid)
                self.insert_node(item, start=mid+1, end=end)

    def mark_selected_node(self, **kwargs):
        tree = self.tree
        item = tree.selection()
        if item:
            tree.tag_configure(item[0], **kwargs)

    @property
    def filtered_strings(self):
        item = self.tree.selection()
        if not item:
            return self._strings
        else:
            start, end = map(int, self.tree.item(item[0], option="values")[:2])
            return self._strings[start:end+1]


if __name__ == '__main__':
    root = tk.Tk()
    Bisect(root, strings='Lorem ipsum dolor sit amet'.split()).pack(fill=tk.BOTH, expand=1)
    root.mainloop()
