import tkinter as tk
import tkinter.ttk as ttk
import tkinter.messagebox as messagebox

from transifex.api import TransifexAPI, TransifexAPIException


class DownloadTranslationsFrame(tk.Frame):
    def bt_connect(self, event):
        username = self.entry_username.get()  # Todo: remember username in the settings
        password = self.entry_password.get()  # DO NOT remember password (not safe)
        project = self.combo_projects.get()
        try:
            # Todo: make connection in separate thread
            t = TransifexAPI(username, password, 'http://transifex.com')
            assert t.project_exists(project), "Project %r does not exist" % project
            resources = t.list_resources(project)
        except (TransifexAPIException, AssertionError) as err:
            messagebox.showerror('Error', err)
        else:
            self.combo_languages['values'] = tuple(t.list_languages(project, resource_slug=resources[0]['slug']))
            self.combo_languages.current(0)  # Todo: remember chosen language, store it in settings
            
            self.listbox_resources.delete(0, tk.END)
            self.listbox_resources.insert(tk.END, *(res['name'] for res in resources))
    
    def bt_download(self, event):
        self.progressbar.start()
    
    def __init__(self, master=None):
        super().__init__(master)
        
        label = tk.Label(self, text='Project:')
        label.grid()
        
        # Todo: remember a list of recently used projects and the last used one
        self.combo_projects = ttk.Combobox(self, values=('dwarf-fortress'))
        self.combo_projects.current(0)
        self.combo_projects.grid(column=1, row=0)
        
        label = tk.Label(self, text='Username:')
        label.grid(column=0, row=1)
        
        self.entry_username = ttk.Entry(self)
        self.entry_username.grid(column=1, row=1, sticky=tk.W + tk.E)
        
        label = tk.Label(self, text='Password:')
        label.grid(column=0, row=2)
        
        self.entry_password = ttk.Entry(self, show='\u2022')  # 'bullet' symbol
        self.entry_password.grid(column=1, row=2, sticky=tk.W + tk.E)
        
        button_connect = ttk.Button(self, text='Connect')
        button_connect.grid(column=4, row=1, rowspan=2, sticky=tk.N + tk.S)
        button_connect.bind('<1>', self.bt_connect)
        
        label = tk.Label(self, text='Choose language:')
        label.grid(column=0, row=3)
        
        self.combo_languages = ttk.Combobox(self)
        self.combo_languages.grid(column=1, row=3, sticky=tk.W + tk.E)
        
        label = tk.Label(self, text='Available resources:')
        label.grid(column=0)
        
        self.listbox_resources = tk.Listbox(self)
        self.listbox_resources.grid(column=0, columnspan=3, sticky=tk.E + tk.W)
        
        self.button_download = ttk.Button(self, text='Download translations')
        self.button_download.bind('<1>', self.bt_download)
        self.button_download.grid()
        
        self.progressbar = ttk.Progressbar(self)
        self.progressbar.grid(columnspan=3, sticky=tk.W + tk.E)


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        
        notebook = ttk.Notebook()
        notebook.pack(fill='both', expand=1)
        f1 = DownloadTranslationsFrame(notebook)
        notebook.add(f1, text='Download tranlations')
        
        f1 = tk.Frame(notebook)
        notebook.add(f1, text='Patch executable file')
        
        f1 = tk.Frame(notebook)
        notebook.add(f1, text='Translate external text files')
        
        f1 = tk.Frame(notebook)
        notebook.add(f1, text='Translate packed files')


app = App()
app.mainloop()
