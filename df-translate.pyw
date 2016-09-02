import tkinter as tk
import tkinter.ttk as ttk
import tkinter.messagebox as messagebox

from transifex.api import TransifexAPI


class App(tk.Tk):
    def bt_check_connection(self, event):
        username = self.entry_username.get()
        password = self.entry_password.get()
        t = TransifexAPI(username, password, 'http://transifex.com')
        # messagebox.showinfo('Warning', 'Connected' if t.ping() else 'Failed to connect')
        project = 'dwarf-fortress'
        assert t.project_exists(project)
        resources = t.list_resources(project)
        self.combo_languages['values'] = tuple(t.list_languages(project, resource_slug=resources[0]['slug']))
        self.combo_languages.current(0)
        # messagebox.showinfo('List of languages loaded', 'A list of available languages is loaded.')
    
    def init_connection_page(self, parent):
        label = tk.Label(parent, text='Username')
        label.grid(column=0, row=0)
        
        label = tk.Label(parent, text='Password')
        label.grid(column=0, row=1)
        
        self.entry_username = ttk.Entry(parent)
        self.entry_username.grid(column=1, row=0)
        
        self.entry_password = ttk.Entry(parent, show='\u2022')  # 'bullet' symbol
        self.entry_password.grid(column=1, row=1)
        
        self.button = ttk.Button(parent, text='Check connection')
        self.button.grid(column=2, row=0, rowspan=2, sticky=tk.N + tk.S)
        self.button.bind('<1>', self.bt_check_connection)
        
        label = tk.Label(parent, text='Available languages:')
        label.grid(column=0, row=3)
        
        self.combo_languages = ttk.Combobox(parent)
        self.combo_languages.grid(column=1, row=3, columnspan=2)
    
    def __init__(self):
        super().__init__()
        
        notebook = ttk.Notebook()
        notebook.pack(fill='both', expand=1)
        f1 = tk.Frame(notebook)
        notebook.add(f1, text='Download tranlation')
        
        self.init_connection_page(f1)
        
        f1 = tk.Frame(notebook)
        notebook.add(f1, text='Patch executable file')



app = App()
app.mainloop()
