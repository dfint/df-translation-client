import tkinter as tk
import tkinter.ttk as ttk
from custom_widgets import FileEntry, CustomText
import importlib


class App(tk.Tk):
    def __init__(self):
        super().__init__()

        self.label_dfrus_state = tk.Label(self)
        self.label_dfrus_state.pack()

        self.dfrus = None
        try:
            self.dfrus = importlib.import_module('dfrus.dfrus')
            self.label_dfrus_state['text'] = 'dfrus module loaded successfully'
        except ImportError:
            self.label_dfrus_state['text'] = 'dfrus import error'

        self.file_entry = FileEntry(self)
        self.file_entry.pack()

        def reload():
            if self.dfrus:
                try:
                    importlib.reload(self.dfrus)
                except:
                    raise
                self.label_dfrus_state['text'] = 'dfrus reloaded'
            else:
                pass

        self.button_reload = ttk.Button(self, text='Reload dfrus', command=reload)
        self.button_reload.pack()

        self.log_field = CustomText(self, enabled=False, height=16)
        self.log_field.pack()


if __name__ == '__main__':
    # mp.freeze_support()
    App().mainloop()
