import tkinter as tk
import tkinter.ttk as ttk
import tkinter.messagebox as messagebox

from transifex.api import TransifexAPI


class App(tk.Tk):
    def __init__(self):
        super().__init__()


app = App()
app.mainloop()
