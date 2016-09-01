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
    
    def __init__(self):
        super().__init__()
        
        self.entry_username = ttk.Entry(self)
        self.entry_username.pack()
        
        self.entry_password = ttk.Entry(self, show='\u2022')  # 'bullet' symbol
        self.entry_password.pack()
        
        self.button = ttk.Button(self, text='Check connection')
        self.button.pack()
        self.button.bind('<1>', self.bt_check_connection)

app = App()
app.mainloop()
