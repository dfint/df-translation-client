import asyncio
import multiprocessing as mp
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk
from typing import Optional

from async_tkinter_loop import async_handler
from dfrus import dfrus
from natsort import natsorted
from tk_grid_helper import grid_manager

from df_translation_client.frames.dialog_do_not_fix_spaces import DialogDoNotFixSpaces
from df_translation_client.frames.frame_debug import DebugFrame
from df_translation_client.utils.config import Config
from df_translation_client.utils.po_languages import (
    get_suitable_codepages_for_file,
    load_dictionary_with_cleanup,
    load_dictionary_raw,
)
from df_translation_client.widgets import FileEntry, TwoStateButton, ScrollbarFrame
from df_translation_client.widgets.custom_widgets import Checkbutton, Combobox, Text


class ProcessMessageWrapper:
    _chunk_size = 1024

    def __init__(self, message_receiver):
        self._message_receiver = message_receiver
        self.encoding = "utf-8"

    def write(self, s):
        for i in range(0, len(s), self._chunk_size):
            self._message_receiver.send(s[i:i + self._chunk_size])

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

    def bt_patch(self):
        if self.dfrus_process is not None and self.dfrus_process.is_alive():
            return False

        executable_file = self.file_entry_executable_file.path

        if not Path(executable_file).exists():
            messagebox.showerror("Error", "Valid path to an executable file must be specified")
        else:
            if not self.debug_frame:
                with open(self.fileentry_translation_file.path, "r", encoding="utf-8") as translation_file:
                    dictionary = dict(load_dictionary_with_cleanup(translation_file, self.exclusions))
            else:
                dictionary = dict(self.debug_frame.bisect.filtered_strings)

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
        translation_file_path = self.fileentry_translation_file.path

        if translation_file_path.exists():
            with open(translation_file_path, "r", encoding="utf-8") as translation_file:
                dictionary, language = load_dictionary_raw(translation_file)
        else:
            dictionary = None
            language = None

        exclusions = DialogDoNotFixSpaces(
            exclusions=self.config_section["fix_space_exclusions"],
            dictionary=dictionary,
            default_language=language,
        ).wait_result()

        if exclusions:
            self.exclusions = exclusions
            self.config_section["fix_space_exclusions"] = exclusions

    def setup_checkbutton(self, text, config_key, default_state):
        config = self.config_section

        def save_checkbox_state(widget, option_name):
            config[option_name] = widget.is_checked

        check = Checkbutton(text=text)
        check.config(command=lambda: save_checkbox_state(check, config_key))
        check.is_checked = config[config_key] = config.get(config_key, default_state)
        return check

    translation_file_language: Optional[str]

    def save_encoding_into_config(self, event):
        self.config_section["last_encoding"] = event.widget.text
        if self.translation_file_language:
            self.config_section["language_codepages"][self.translation_file_language] = event.widget.text

    async def update_combo_encoding_list(self, translation_file):
        try:
            codepages, language = await get_suitable_codepages_for_file(translation_file)
            self.combo_encoding.values = natsorted(codepages)
            self.translation_file_language = language
        except Exception:
            self.translation_file_language = None
            self.combo_encoding.values = tuple()

    async def config_combo_encoding(self, translation_file: Path):
        await self.update_combo_encoding_list(translation_file)

        if "last_encoding" in self.config_section:
            self.combo_encoding.text = self.config_section["last_encoding"]
        elif self.combo_encoding.values:
            self.combo_encoding.current(0)

        self.combo_encoding.bind("<<ComboboxSelected>>", func=self.save_encoding_into_config)

    async def update_combo_encoding(self, translation_file: Path):
        await self.update_combo_encoding_list(translation_file)

        if (self.translation_file_language
                and self.translation_file_language in self.config_section["language_codepages"]):

            self.combo_encoding.text = self.config_section["language_codepages"][self.translation_file_language]
        elif self.combo_encoding.values:
            self.combo_encoding.current(0)
        else:
            self.combo_encoding.text = "cp437"

    async def on_translation_file_change(self, file_path: Path):
        self.config_section.check_and_save_path("df_exe_translation_file", file_path)
        await self.update_combo_encoding(self.fileentry_translation_file.path)
        if self.debug_frame and file_path.is_file():
            with open(self.fileentry_translation_file.path, "r", encoding="utf-8") as translation_file:
                self.debug_frame.set_dictionary(load_dictionary_with_cleanup(translation_file, self.exclusions))

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

        with grid_manager(self, sticky=tk.EW, padx=2, pady=2) as grid:
            self.file_entry_executable_file = FileEntry(
                dialog_type="askopenfilename",
                filetypes=[("Executable files", "*.exe")],
                default_path=self.config_section.get("df_executable", ""),
                on_change=lambda text: self.config_section.check_and_save_path("df_executable", text),
            )
            grid.new_row() \
                .add(tk.Label(text="DF executable file:"), sticky=tk.W) \
                .add(self.file_entry_executable_file).column_span(2)

            self.fileentry_translation_file = FileEntry(
                dialog_type="askopenfilename",
                filetypes=[
                    ("Hardcoded strings' translation", "*hardcoded*.po"),
                    ("Translation files", "*.po"),
                    # ("csv file", "*.csv"), # @TODO: Currently not supported
                ],
                default_path=self.config_section.get("df_exe_translation_file", ""),
                on_change=async_handler(self.on_translation_file_change),
                change_color=True
            )
            grid.new_row() \
                .add(tk.Label(text="Translation file:"), sticky=tk.W) \
                .add(self.fileentry_translation_file).column_span(2)

            self.combo_encoding = Combobox()
            asyncio.get_event_loop().create_task(self.config_combo_encoding(self.fileentry_translation_file.path))
            grid.new_row() \
                .add(tk.Label(text="Encoding:"), sticky=tk.W) \
                .add(self.combo_encoding).column_span(2)

            # FIXME: chk_do_not_patch_charmap does nothing
            self.chk_do_not_patch_charmap = self.setup_checkbutton(
                text="Don't patch charmap table",
                config_key="do_not_patch_charmap",
                default_state=False)

            grid.new_row().skip(1).add(self.chk_do_not_patch_charmap).column_span(2)

            self.chk_add_leading_trailing_spaces = self.setup_checkbutton(
                text="Add necessary leading/trailing spaces",
                config_key="add_leading_trailing_spaces",
                default_state=True)

            button_exclusions = ttk.Button(self, text="Exclusions...", command=self.bt_exclusions)

            grid.new_row().add(self.chk_add_leading_trailing_spaces).column_span(2).add(button_exclusions)

            if debug:
                if self.fileentry_translation_file.path.is_file():
                    with open(self.fileentry_translation_file.path, "r", encoding="utf-8") as translation_file:
                        dictionary = load_dictionary_with_cleanup(translation_file, self.exclusions)
                else:
                    dictionary = None
                self.debug_frame = DebugFrame(dictionary=dictionary)

                grid.new_row().add(self.debug_frame, sticky=tk.NSEW, columnspan=3).configure(weight=1)
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

            grid.new_row().add(self.chk_debug_output).column_span(2).add(self.button_patch)

            # ------------------------------------------------------------------------------------------

            scrollbar_frame = ScrollbarFrame(widget_factory=Text,
                                             widget_args=dict(width=48, height=8, enabled=False),
                                             show_scrollbars=tk.VERTICAL)

            grid.new_row().add(scrollbar_frame, sticky=tk.NSEW).column_span(3).configure(weight=1)

            self.log_field: Text = scrollbar_frame.widget

            grid.columnconfigure(1, weight=1)

        self.bind("<Destroy>", self.kill_processes)
