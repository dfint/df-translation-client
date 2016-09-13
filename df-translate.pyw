import requests
import sys
import tempfile
import tkinter as tk
import tkinter.ttk as ttk
import tkinter.messagebox as messagebox

from dfrus.patchdf import codepages
from os import path
from transifex.api import TransifexAPI, TransifexAPIException


class DownloadTranslationsFrame(tk.Frame):
    def bt_connect(self, event):
        username = self.entry_username.get()  # Todo: remember username in the settings
        password = self.entry_password.get()  # DO NOT remember password (not safe)
        project = self.combo_projects.get()
        try:
            # Todo: make connection in separate thread
            self.tx = TransifexAPI(username, password, 'http://transifex.com')
            assert self.tx.project_exists(project), "Project %r does not exist" % project
            self.resources = self.tx.list_resources(project)
            languages = self.tx.list_languages(project, resource_slug=self.resources[0]['slug'])
        except (TransifexAPIException, requests.exceptions.ConnectionError, AssertionError) as err:
            messagebox.showerror('Error', err)
        except:
            messagebox.showerror('Unexpected error', repr(sys.exc_info()[0]))
        else:
            self.combo_languages['values'] = tuple(languages)
            self.combo_languages.current(0)  # Todo: remember chosen language, store it in settings
            
            self.listbox_resources.delete(0, tk.END)
            self.listbox_resources_var.set(tuple(res['name'] for res in self.resources))
    
    def bt_download(self, event):
        if self.tx and self.resources:
            self.progressbar['maximum'] = len(self.resources) * 1.001
            self.progressbar['value'] = 0
            
            if self.temp_dir is not None:
                self.temp_dir.cleanup()
                self.temp_dir = None
            
            if self.download_dir:
                download_dir = self.download_dir
            else:
                self.temp_dir = tempfile.TemporaryDirectory()
                download_dir = self.temp_dir.name
            
            project = self.combo_projects.get()
            language = self.combo_languages.get()
            
            initial_names = [res['name'] for res in self.resources]
            resource_names = list(initial_names)
            
            self.listbox_resources_var.set(tuple(resource_names))
            for i, res in enumerate(self.resources):
                file_path = path.join(download_dir, '%s_%s.po' % (res['slug'], language))
                for _ in range(10):
                    try:
                        self.tx.get_translation(project, res['slug'], language, file_path)
                        break
                    except:
                        resource_names[i] = initial_names[i] + ' - retry...'
                        self.listbox_resources_var.set(tuple(resource_names))
                        self.app.update()
                else:
                    resource_names[i] = initial_names[i] + ' - error'
                    messagebox.showerror('Downloading error', repr(sys.exc_info()[0]))
                    raise
                
                resource_names[i] = initial_names[i] + ' - ok!'
                self.listbox_resources_var.set(tuple(resource_names))
                self.progressbar.step()
                self.app.update()
            
            import subprocess
            subprocess.Popen('explorer "%s"' % (download_dir))
    
    def __init__(self, master=None, app=None):
        super().__init__(master)
        
        self.app = app
        
        label = tk.Label(self, text='Transifex project:')
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
        
        button_connect = ttk.Button(self, text='Connect...')
        button_connect.grid(columnspan=2, sticky=tk.W + tk.E)
        button_connect.bind('<1>', self.bt_connect)
        
        label = tk.Label(self, text='Choose language:')
        label.grid(column=0)
        
        self.combo_languages = ttk.Combobox(self)
        self.combo_languages.grid(column=1, row=4, sticky=tk.W + tk.E)
        
        # self.chk_all_languages_var = tk.IntVar()
        # chk_all_languages = tk.Checkbutton(self, text='All languages (backup)', variable=self.chk_all_languages_var)
        # chk_all_languages.grid(column=1)
        
        self.button_download = ttk.Button(self, text='Download translations')
        self.button_download.bind('<1>', self.bt_download)
        self.button_download.grid(row=6, sticky=tk.W + tk.E)
        
        self.progressbar = ttk.Progressbar(self)
        self.progressbar.grid(column=1, row=6, sticky=tk.W + tk.E)
        
        label = tk.Label(self, text='Resources:')
        label.grid(columnspan=2)
        
        self.listbox_resources_var = tk.Variable()
        self.listbox_resources = tk.Listbox(self, listvariable=self.listbox_resources_var)
        self.listbox_resources.grid(column=0, columnspan=2, sticky=tk.E + tk.W)
        
        self.resources = None
        self.tx = None
        self.temp_dir = None
        self.download_dir = None
    
    def __del__(self):
        if self.temp_dir is not None:
            self.temp_dir.cleanup()


class PatchExecutableFrame(tk.Frame):
    def bt_browse_executable(self, event):
        pass
    
    def bt_browse_translation(self, event):
        pass
    
    def bt_patch(self, event):
        pass
    
    def __init__(self, master=None, app=None):
        super().__init__(master)
        
        self.app = app
        
        label = tk.Label(self, text='DF executable file:')
        label.grid()
        
        self.entry_executable_file = ttk.Entry(self)
        self.entry_executable_file.grid(column=1, row=0, sticky=tk.E + tk.W)
        
        button_browse_executable = ttk.Button(self, text='Browse...')
        button_browse_executable.grid(column=2, row=0)
        button_browse_executable.bind('<1>', self.bt_browse_executable)
        
        label = tk.Label(self, text='DF executable tranlation file:')
        label.grid()
        
        self.entry_translation_file = ttk.Entry(self)
        self.entry_translation_file.grid(column=1, row=1, sticky=tk.E + tk.W)
        
        button_browse_translation = ttk.Button(self, text='Browse...')
        button_browse_translation.grid(column=2, row=1)
        button_browse_translation.bind('<1>', self.bt_browse_translation)
        
        label = tk.Label(self, text='Encoding:')
        label.grid()
        
        self.combo_encoding = ttk.Combobox(self)
        self.combo_encoding.grid(column=1, row=2, sticky=tk.E + tk.W)
        
        self.combo_encoding['values'] = tuple(['cp437'] + list(codepages.keys()))
        self.combo_encoding.current(0)
        
        self.chk_dont_patch_charmap_var = tk.IntVar()
        chk_dont_patch_charmap = ttk.Checkbutton(self, text="Don't patch charmap table",
                                                 variable=self.chk_dont_patch_charmap_var)
        chk_dont_patch_charmap.grid(column=1)
        
        button_patch = ttk.Button(self, text='Patch!')
        button_patch.grid(column=2)
        button_patch.bind('<1>', self.bt_patch)
        
        log_field = tk.Text(self, width=48, height=16)
        log_field.grid(columnspan=3)


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        
        notebook = ttk.Notebook()
        notebook.pack(fill='both', expand=1)
        
        f1 = DownloadTranslationsFrame(notebook, self)
        notebook.add(f1, text='Download tranlations')
        
        f1 = PatchExecutableFrame(notebook, self)
        notebook.add(f1, text='Patch executable file')
        
        f1 = tk.Frame(notebook)
        notebook.add(f1, text='Translate external text files')
        
        f1 = tk.Frame(notebook)
        notebook.add(f1, text='Translate packed files')


app = App()
app.mainloop()
