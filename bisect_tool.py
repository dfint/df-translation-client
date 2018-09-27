import tkinter as tk
import tkinter.ttk as ttk


class Bisect(tk.Frame):
    def __init__(self, *args, strings=None, **kwargs):
        super().__init__(*args, **kwargs)
        self._strings = strings
        self.tree = tree = ttk.Treeview(self)
        tree.grid()
        tree["columns"] = ("start", "end", "start_string", "end_string")
        tree["displaycolumns"] = tree["columns"][-2:]

        if strings:
            self.insert_node(start=0, end=len(strings)-1)
        
        ttk.Button(self, text="Split", command=self.split_selected_node).grid()

    def insert_node(self, parent_node='', index='end', start=0, end=0):
        if start != end:
            text='[{} : {}] ({} strings)'.format(start, end, end-start+1)
            values = (start, end, repr(self._strings[start]), repr(self._strings[end]))
        else:
            text='[{} : {}] ({} string)'.format(start, end, end-start+1)
            values = (start, end, repr(self._strings[start]))

        self.tree.insert(parent_node, index, text=text, open=True, values=values)

    def split_selected_node(self):
        tree = self.tree
        item = tree.selection()
        if item:
            start, end = map(int, tree.item(item[0], option="values")[:2])
            if start != end:
                mid = (start + end) // 2
                self.insert_node(item, start=start, end=mid)
                self.insert_node(item, start=mid+1, end=end)

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
