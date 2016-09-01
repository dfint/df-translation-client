import tkinter as tk
import tkinter.ttk as ttk
import tkinter.messagebox as messagebox

from transifex.api import TransifexAPI


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        
        self.entry_username = ttk.Entry(self)
        self.entry_username.pack()
        
        self.entry_password = ttk.Entry(self, show='\u2022')  # 'bullet' symbol
        self.entry_password.pack()


app = App()
app.mainloop()
