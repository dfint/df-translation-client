from collections import namedtuple
from tkinter import ttk


class TwoStateButton(ttk.Button):
    def _action(self):
        command = self._state[0].command
        if command():
            self.swap_state()

    def swap_state(self):
        self._state.reverse()
        self['text'] = self._state[0].text

    def reset_state(self):
        self._state = list(self._initial_state)
        self['text'] = self._state[0].text

    def __init__(self, *args, text, command, text2, command2, **kwargs):
        TextCommand = namedtuple('TextCommand', 'text,command')
        self._initial_state = (TextCommand(text, command), TextCommand(text2, command2))
        self._state = list(self._initial_state)
        super().__init__(*args, text=text, command=self._action, **kwargs)
