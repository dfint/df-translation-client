import importlib
import tkinter as tk
from tkinter import ttk
from typing import Iterable, Optional, Tuple

from dfrus import dfrus
from tkinter_layout_helpers import pack_manager

from df_translation_client.widgets import BisectTool


class DebugFrame(tk.Frame):
    @staticmethod
    def reload():
        importlib.reload(dfrus)

    def __init__(self, *args, dictionary: Optional[Iterable[Tuple[str, str]]] = None, **kwargs):
        super().__init__(*args, **kwargs)
        with pack_manager(self) as packer:
            if dictionary is not None:
                dictionary = list(dictionary)
            self.bisect = BisectTool(self, strings=dictionary)

            packer.pack(ttk.Button(text="Reload dfrus", command=self.reload)).pack_expanded(self.bisect)

    def set_dictionary(self, dictionary: Iterable[Tuple[str, str]]):
        self.bisect.strings = list(dictionary)
