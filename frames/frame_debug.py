import importlib
import tkinter as tk
from tkinter import ttk

from dfrus import dfrus

from tkinter_helpers import Packer
from widgets import BisectTool


class DebugFrame(tk.Frame):
    @staticmethod
    def reload():
        importlib.reload(dfrus)

    def __init__(self, *args, dictionary=None, **kwargs):
        super().__init__(*args, **kwargs)
        with Packer(self) as packer:
            self.bisect = BisectTool(self, strings=list(dictionary.items()))

            packer.pack(ttk.Button(text="Reload dfrus", command=self.reload)) \
                  .expand(self.bisect)

    def set_dictionary(self, dictionary):
        self.bisect.strings = list(dictionary.items())
