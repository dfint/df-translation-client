import tkinter as tk
from pathlib import Path
from tkinter import filedialog, ttk
from typing import Callable, Optional

from df_translation_client.utils.tkinter_helpers import Packer
from df_translation_client.widgets.custom_widgets import Entry


class FileEntry(tk.Frame):
    def _change_entry_color(self):
        if self.path_is_valid():
            self.entry.config(background="white")
        else:
            self.entry.config(background="red")

    def _askopenfilename(self):
        if self.default_path.is_file():
            initial_dir = self.default_path.parent
            initial_file = self.default_path.name
        else:
            initial_dir = self.default_path
            initial_file = ""

        return filedialog.askopenfilename(
            filetypes=self.filetypes,
            initialdir=initial_dir,
            initialfile=initial_file,
        )

    def _bt_browse(self):
        file_path = ""
        # Use self.default_path only if self.entry.text is empty (Captain Obvious)
        self.default_path = Path(self.entry.text or self.default_path)
        if self.dialog_type == "askopenfilename":
            file_path = self._askopenfilename()
        elif self.dialog_type == "askdirectory":
            file_path = filedialog.askdirectory(initialdir=self.default_path)

        if file_path:  # if not cancelled
            self.entry.text = file_path

            if self.on_change is not None and file_path != self._prev_value:
                self.on_change(self.path)

            self._prev_value = file_path

            if self._flag_change_entry_color:
                self._change_entry_color()

    def _on_entry_key_release(self, event):
        if event.widget.text != self._prev_value:
            self.on_change(self.path)
            self._prev_value = event.widget.text

            if self._flag_change_entry_color:
                self._change_entry_color()

    def __init__(
        self,
        default_path="",
        on_change: Optional[Callable[[Path], None]] = None,
        filetypes=tuple(),
        dialog_type="askopenfilename",
        change_color=False,
        **kwargs
    ):
        super().__init__(**kwargs)

        self.filetypes = filetypes
        self.on_change = on_change
        self.default_path = Path(default_path)
        self.dialog_type = dialog_type

        with Packer(self) as packer:
            self.entry = Entry()
            self.button = ttk.Button(text="Browse...", command=self._bt_browse)
            packer.right(self.button, padx=2).expand(self.entry)

        self.entry.text = self.default_path
        self._prev_value = self.default_path

        if self.on_change is not None:
            self.entry.bind("<KeyRelease>", func=self._on_entry_key_release)

        self._flag_change_entry_color = change_color
        if change_color:
            self._change_entry_color()

    @property
    def text(self) -> str:
        return self.entry.get()

    def path_is_valid(self) -> bool:
        return self.text and self.path.exists() and self.path.is_file() == (self.dialog_type == "askopenfilename")

    @property
    def path(self) -> Path:
        return Path(self.text)
