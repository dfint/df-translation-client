import tkinter as tk
import tkinter.ttk as ttk

from typing import Any, Callable, Mapping, Union, TypeVar, Generic

TWidget = TypeVar("TWidget")


class ScrollbarFrame(tk.Frame, Generic[TWidget]):
    """
    A frame with scrollbars which can be added to any widget which supports scrolling (eg. Text, Listbox, Entry, etc.)
    """
    def __init__(self, *args,
                 widget_factory: Callable[..., TWidget],
                 widget_args: Mapping[str, Any] = None,
                 show_scrollbars=tk.BOTH,
                 scrollbar: Callable[..., Union[tk.Scrollbar, ttk.Scrollbar]] = ttk.Scrollbar,
                 **kwargs):
        
        super().__init__(*args, **kwargs)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        if widget_args is None:
            widget_args = dict()

        self.__widget = widget_factory(self, **widget_args)
        self.__widget.grid(row=0, column=0, sticky=tk.NSEW)
        
        if show_scrollbars in (tk.HORIZONTAL, tk.BOTH):
            x_scrollbar = scrollbar(self, orient=tk.HORIZONTAL, command=self.__widget.xview)
            self.__widget.config(xscrollcommand=x_scrollbar.set)
            x_scrollbar.grid(row=1, column=0, sticky=tk.EW)
        
        if show_scrollbars in (tk.VERTICAL, tk.BOTH):
            y_scrollbar = scrollbar(self, orient=tk.VERTICAL, command=self.__widget.yview)
            self.__widget.config(yscrollcommand=y_scrollbar.set)
            y_scrollbar.grid(row=0, column=1, sticky=tk.NS)
    
    @property
    def widget(self) -> TWidget:
        return self.__widget


if __name__ == '__main__':
    root = tk.Tk()
    
    scrollable_text = ScrollbarFrame(
        root,
        widget_factory=tk.Text,
        widget_args=dict(wrap=tk.NONE),
        scrollbar=ttk.Scrollbar
    )
    scrollable_text.pack()
    
    scrollable_listbox = ScrollbarFrame(
        root,
        widget_factory=tk.Listbox,
        scrollbar=ttk.Scrollbar,
        show_scrollbars=tk.VERTICAL
    )
    scrollable_listbox.pack()

    root.mainloop()
