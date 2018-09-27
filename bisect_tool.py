import tkinter as tk
import tkinter.ttk as ttk


class Bisect(tk.Frame):
    def __init__(self, *args, strings=None, **kwargs):
        super().__init__(*args, **kwargs)
        self._strings = strings
        self.tree = tree = ttk.Treeview(self)
        tree.grid(columnspan=4)
        tree["columns"] = ("start", "end", "strings")
        tree["displaycolumns"] = tree["columns"][-1]
        tree.heading('#0', text='Tree')
        tree.heading('#1', text='Strings')

        if strings:
            self.insert_node(start=0, end=len(strings)-1)
        
        ttk.Button(self, text="Split", command=self.split_selected_node).grid(row=3, column=0)
        ttk.Button(self, text="Mark as bad", command=lambda: self.mark_selected_node(foreground='red')).grid(row=3, column=1)
        ttk.Button(self, text="Mark as good", command=lambda: self.mark_selected_node(foreground='green')).grid(row=3, column=2)
        ttk.Button(self, text="Clear mark", command=lambda: self.mark_selected_node(foreground='black')).grid(row=3, column=3)

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
    Bisect(root, strings='Lorem ipsum dolor sit amet'.split()).pack()
    root.mainloop()
