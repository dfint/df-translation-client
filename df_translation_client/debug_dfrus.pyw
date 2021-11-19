import importlib
import tkinter as tk
import tkinter.ttk as ttk

from .tkinter_helpers import Packer
from .widgets import FileEntry, BisectTool, ScrollbarFrame
from .widgets.custom_widgets import Text


class App(tk.Tk):
    def reload(self):
        if self.dfrus:
            try:
                importlib.reload(self.dfrus)
            except:
                raise
            print('dfrus reloaded', file=self.log_field)
            print(self.dfrus.__file__, file=self.log_field)
        else:
            pass

    def __init__(self):
        super().__init__()

        with Packer(self) as packer:
            self.file_entry = FileEntry()
            self.bisect = BisectTool()
            scrollbar_frame = ScrollbarFrame(widget_factory=Text, widget_args=dict(enabled=False, height=8))
            self.log_field: Text = scrollbar_frame.widget

            packer.pack_all(
                self.file_entry,
                ttk.Button(text='Reload dfrus', command=self.reload),
                self.bisect,
                ttk.Button(text='Patch DF'),
                # TwoStateButton(text='Run DF', command=None, text2='Kill DF process', command2=None),
                scrollbar_frame,
            )

        self.dfrus = None
        try:
            self.dfrus = importlib.import_module('dfrus')
            print('dfrus module loaded successfully', file=self.log_field)
            print(self.dfrus.__file__, file=self.log_field)
        except ImportError:
            print('dfrus import error', file=self.log_field)


if __name__ == '__main__':
    # mp.freeze_support()
    App().mainloop()
