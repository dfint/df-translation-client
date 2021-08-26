import importlib
import tkinter as tk
import tkinter.ttk as ttk

from widgets import FileEntry, BisectTool, TwoStateButton, ScrollbarFrame
from widgets.custom_widgets import Text


class App(tk.Tk):
    def __init__(self):
        super().__init__()

        self.file_entry = FileEntry(self)
        self.file_entry.pack()

        def reload():
            if self.dfrus:
                try:
                    importlib.reload(self.dfrus)
                except:
                    raise
                print('dfrus reloaded', file=self.log_field)
                print(self.dfrus.__file__, file=self.log_field)
            else:
                pass

        ttk.Button(self, text='Reload dfrus', command=reload).pack()

        self.bisect = BisectTool()
        self.bisect.pack()

        ttk.Button(self, text='Patch DF').pack()
        TwoStateButton(self, 'Run DF', None, 'Kill DF process', None).pack()

        scrollbar_frame = ScrollbarFrame(self, Text, widget_args=dict(enabled=False, height=8))
        scrollbar_frame.pack()
        self.log_field: Text = scrollbar_frame.widget

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
