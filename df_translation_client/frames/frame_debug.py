import importlib
import tkinter as tk
from tkinter import ttk

from dfrus import dfrus

from df_translation_client.tkinter_helpers import Packer
from df_translation_client.widgets import BisectTool


class DebugFrame(tk.Frame):
    @staticmethod
    def reload():
        importlib.reload(dfrus)

    def __init__(self, *args, dictionary=None, **kwargs):
        super().__init__(*args, **kwargs)
        with Packer(self) as packer:
            if dictionary is not None:
                dictionary = list(dictionary.items())
            self.bisect = BisectTool(self, strings=dictionary)

            packer.pack(ttk.Button(text="Reload dfrus", command=self.reload)) \
                  .expand(self.bisect)

    def set_dictionary(self, dictionary):
        self.bisect.strings = list(dictionary.items())
