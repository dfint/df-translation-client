import multiprocessing as mp
import tkinter as tk
from collections import OrderedDict
from pathlib import Path
from tkinter import messagebox, ttk
from typing import Optional

from df_gettext_toolkit import parse_po
from df_gettext_toolkit.fix_translated_strings import fix_spaces, cleanup_string
from dfrus import dfrus
from natsort import natsorted

from config import Config
from po_languages import get_suitable_codepages_for_file
from tkinter_helpers import Grid, GridCell
from widgets import FileEntry, TwoStateButton, ScrollbarFrame
from widgets.custom_widgets import Checkbutton, Combobox, Text
from .dialog_do_not_fix_spaces import DialogDoNotFixSpaces
from .frame_debug import DebugFrame


class ProcessMessageWrapper:
    _chunk_size = 1024

    def __init__(self, message_receiver):
        self._message_receiver = message_receiver
        self.encoding = "utf-8"

    def write(self, s):
        for i in range(0, len(s), self._chunk_size):
            self._message_receiver.send(s[i:i+self._chunk_size])

    def flush(self):
        pass  # stub method


class PatchExecutableFrame(tk.Frame):
    def update_log(self, message_queue):
        try:
            message = []
            
            while message_queue.poll():
                message.append(message_queue.recv())
            
            self.log_field.write("".join(message))

            if not self.dfrus_process.is_alive():
                self.log_field.write("\n[PROCESS FINISHED]")
                self.button_patch.reset_state()
            else:
                self.after(100, self.update_log, message_queue)
        except (EOFError, BrokenPipeError):
            self.log_field.write("\n[MESSAGE QUEUE/PIPE BROKEN]")
            self.button_patch.reset_state()

    def load_dictionary(self):
        translation_file = self.fileentry_translation_file.path
        with open(translation_file, "r", encoding="utf-8") as fn:
            pofile = parse_po.PoReader(fn)
            meta = pofile.meta
            exclusions = self.exclusions.get(meta["Language"], self.exclusions)
            dictionary = OrderedDict(
                (entry["msgid"],
                 fix_spaces(entry["msgid"], cleanup_string(entry["msgstr"]), exclusions, exclusions))
                for entry in pofile
            )
        return dictionary

    def bt_patch(self):
        if self.dfrus_process is not None and self.dfrus_process.is_alive():
            return False

        executable_file = self.file_entry_executable_file.path

        if not Path(executable_file).exists():
            messagebox.showerror("Error", "Valid path to an executable file must be specified")
        else:
            if not self.debug_frame:
                dictionary = self.load_dictionary()
            else:
                dictionary = OrderedDict(self.debug_frame.bisect.filtered_strings)

            self.config_section["last_encoding"] = self.combo_encoding.text

            parent_conn, child_conn = mp.Pipe()

            self.after(100, self.update_log, parent_conn)
            self.log_field.clear()
            self.dfrus_process = mp.Process(
                target=dfrus.run,
                kwargs=dict(
                    path=executable_file,
                    dest="",
                    trans_table=dictionary,
                    codepage=self.combo_encoding.text,
                    debug=self.chk_debug_output.is_checked,
                    stdout=ProcessMessageWrapper(child_conn),
                    stderr=ProcessMessageWrapper(child_conn)
                )
            )
            self.dfrus_process.start()
            return True

        return False

    def bt_stop(self):
        r = messagebox.showwarning("Are you sure?", "Stop the patching process?", type=messagebox.OKCANCEL)
        if r == "cancel":
            return False
        else:
            self.dfrus_process.terminate()
            return True

    def kill_processes(self, _):
        if self.dfrus_process and self.dfrus_process.is_alive():
            self.dfrus_process.terminate()

    def bt_exclusions(self):
        translation_file = self.fileentry_translation_file.path
        language = None
        dictionary = None
        if translation_file.exists():
            with open(translation_file, "r", encoding="utf-8") as fn:
                pofile = parse_po.PoReader(fn)
                meta = pofile.meta
                language = meta["Language"]
                dictionary = {entry["msgid"]: entry["msgstr"] for entry in pofile}

        dialog = DialogDoNotFixSpaces(self, self.config_section["fix_space_exclusions"], dictionary,
                                      default_language=language)

        exclusions = dialog.wait_result()
        self.exclusions = exclusions or self.config_section["fix_space_exclusions"]
        self.config_section["fix_space_exclusions"] = self.exclusions

    def setup_checkbutton(self, text, config_key, default_state):
        config = self.config_section

        def save_checkbox_state(event, option_name):
            config[option_name] = not event.widget.is_checked  # Event occurs before the widget changes state

        check = Checkbutton(text=text)
        check.bind("<1>", lambda event: save_checkbox_state(event, config_key))
        check.is_checked = config[config_key] = config.get(config_key, default_state)
        return check

    translation_file_language: Optional[str]

    def save_encoding_into_config(self, event):
        self.config_section["last_encoding"] = event.widget.text
        if self.translation_file_language:
            self.config_section["language_codepages"][self.translation_file_language] = event.widget.text

    def update_combo_encoding_list(self, translation_file):
        if translation_file.exists() and translation_file.is_file():
            codepages, language = get_suitable_codepages_for_file(translation_file)
            self.combo_encoding.values = natsorted(codepages)
            self.translation_file_language = language
        else:
            self.translation_file_language = None
            self.combo_encoding.values = tuple()

    def config_combo_encoding(self, translation_file: Path):
        self.update_combo_encoding_list(translation_file)

        if "last_encoding" in self.config_section:
            self.combo_encoding.text = self.config_section["last_encoding"]
        elif self.combo_encoding.values:
            self.combo_encoding.current(0)

        self.combo_encoding.bind("<<ComboboxSelected>>", func=self.save_encoding_into_config)

    def update_combo_encoding(self, translation_file: Path):
        self.update_combo_encoding_list(translation_file)

        if (self.translation_file_language
                and self.translation_file_language in self.config_section["language_codepages"]):

            self.combo_encoding.text = self.config_section["language_codepages"][self.translation_file_language]
        elif self.combo_encoding.values:
            self.combo_encoding.current(0)
        else:
            self.combo_encoding.text = "cp437"

    def __init__(self, *args, config: Config, debug=False, **kwargs):
        super().__init__(*args, **kwargs)

        self.config_section = config.init_section(
            section_name="patch_executable",
            defaults=dict(
                fix_space_exclusions=dict(ru=["Histories of "]),
                language_codepages=dict(),
            )
        )

        self.exclusions = self.config_section["fix_space_exclusions"]

        self.dfrus_process = None

        self._dictionary = None

        with Grid(self, sticky=tk.EW, padx=2, pady=2) as grid:
            self.file_entry_executable_file = FileEntry(
                dialog_type="askopenfilename",
                filetypes=[("Executable files", "*.exe")],
                default_path=self.config_section.get("df_executable", ""),
                on_change=lambda text: self.config_section.check_and_save_path("df_executable", text),
            )
            grid.add_row("DF executable file:", self.file_entry_executable_file, ...)

            def on_translation_file_change(file_path):
                self.config_section.check_and_save_path("df_exe_translation_file", file_path)
                self.update_combo_encoding(Path(file_path))
                if self.debug_frame:
                    self.debug_frame.set_dictionary(self.load_dictionary())

            self.fileentry_translation_file = FileEntry(
                dialog_type="askopenfilename",
                filetypes=[
                    ("Hardcoded strings' translation", "*hardcoded*.po"),
                    ("Translation files", "*.po"),
                    # ("csv file", "*.csv"), # @TODO: Currently not supported
                ],
                default_path=self.config_section.get("df_exe_translation_file", ""),
                on_change=on_translation_file_change,
                change_color=True
            )
            grid.add_row("DF executable translation file:", self.fileentry_translation_file, ...)

            self.combo_encoding = Combobox()
            self.config_combo_encoding(self.fileentry_translation_file.path)
            grid.add_row("Encoding:", self.combo_encoding)

            # FIXME: chk_do_not_patch_charmap does nothing
            self.chk_do_not_patch_charmap = self.setup_checkbutton(
                text="Don't patch charmap table",
                config_key="do_not_patch_charmap",
                default_state=False)

            grid.add_row(..., self.chk_do_not_patch_charmap, ...)

            self.chk_add_leading_trailing_spaces = self.setup_checkbutton(
                text="Add necessary leading/trailing spaces",
                config_key="add_leading_trailing_spaces",
                default_state=True)

            button_exclusions = ttk.Button(self, text="Exclusions...", command=self.bt_exclusions)

            grid.add_row(self.chk_add_leading_trailing_spaces, ..., button_exclusions)

            if debug:
                self.debug_frame = DebugFrame(dictionary=self.load_dictionary())
                grid.add_row(GridCell(self.debug_frame, sticky=tk.NSEW, columnspan=3)).configure(weight=1)
            else:
                self.debug_frame = None

            self.chk_debug_output = self.setup_checkbutton(
                text="Enable debugging output",
                config_key="debug_output",
                default_state=False
            )

            self.button_patch = TwoStateButton(
                text="Patch!", command=self.bt_patch,
                text2="Stop!", command2=self.bt_stop
            )

            grid.add_row(self.chk_debug_output, ..., self.button_patch)

            # ------------------------------------------------------------------------------------------

            scrollbar_frame = ScrollbarFrame(widget_factory=Text,
                                             widget_args=dict(width=48, height=8, enabled=False),
                                             show_scrollbars=tk.VERTICAL)

            grid.add_row(GridCell(scrollbar_frame, columnspan=3, sticky=tk.NSEW)).configure(weight=1)

            self.log_field: Text = scrollbar_frame.widget

            grid.columnconfigure(1, weight=1)
        
        self.bind("<Destroy>", self.kill_processes)
