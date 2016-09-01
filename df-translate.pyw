import tkinter as tk
import tkinter.ttk as ttk
import tkinter.messagebox as messagebox

from transifex.api import TransifexAPI


class App(tk.Tk):
    def bt_check_connection(self, event):
        username = self.entry_username.get()
        password = self.entry_password.get()
        t = TransifexAPI(username, password, 'http://transifex.com')
        messagebox.showinfo('Warning', 'Connected' if t.ping() else 'Failed to connect')
    
    def init_connection_page(self, parent):
        self.entry_username = ttk.Entry(parent)
        self.entry_username.pack()
        
        self.entry_password = ttk.Entry(parent, show='\u2022')  # 'bullet' symbol
        self.entry_password.pack()
        
        self.button = ttk.Button(parent, text='Check connection')
        self.button.pack()
        self.button.bind('<1>', self.bt_check_connection)
    
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
