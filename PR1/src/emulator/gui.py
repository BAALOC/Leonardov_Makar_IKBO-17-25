"""Tkinter front end of the emulator."""

import tkinter as tk
from tkinter import scrolledtext

from emulator.parser import strip_comment
from emulator.shell import Result, Shell

OUTPUT_ROWS = 24
OUTPUT_COLUMNS = 80
FONT = 'TkFixedFont'
TAG_ERROR = 'error'
TAG_DEBUG = 'debug'
ERROR_COLOR = 'red'
DEBUG_COLOR = 'gray'


class EmulatorWindow:
    """Main window: scrollable output and a command entry."""

    def __init__(self, root: tk.Tk, shell: Shell) -> None:
        """Build the widgets and bind the Enter key."""
        self.root = root
        self.shell = shell
        root.title(f'Shell Emulator - VFS: {shell.vfs_name}')
        self.output = self.create_output()
        self.entry = self.create_input_row()
        self.entry.bind('<Return>', self.on_enter)
        self.entry.focus_set()

    def create_output(self) -> scrolledtext.ScrolledText:
        """Create the read-only output area."""
        output = scrolledtext.ScrolledText(
            self.root, height=OUTPUT_ROWS, width=OUTPUT_COLUMNS,
            font=FONT, state=tk.DISABLED)
        output.tag_configure(TAG_ERROR, foreground=ERROR_COLOR)
        output.tag_configure(TAG_DEBUG, foreground=DEBUG_COLOR)
        output.pack(fill=tk.BOTH, expand=True)
        return output

    def create_input_row(self) -> tk.Entry:
        """Create the prompt label and the command entry."""
        row = tk.Frame(self.root)
        row.pack(fill=tk.X)
        tk.Label(row, text=self.shell.prompt, font=FONT).pack(side=tk.LEFT)
        entry = tk.Entry(row, font=FONT)
        entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        return entry

    def append(self, text: str, tag: str | None = None) -> None:
        """Add a line to the output area."""
        tags = (tag,) if tag else ()
        self.output.configure(state=tk.NORMAL)
        self.output.insert(tk.END, text + '\n', *tags)
        self.output.configure(state=tk.DISABLED)
        self.output.see(tk.END)

    def run_line(self, line: str) -> Result:
        """Echo a command line, execute it and show the result."""
        self.append(self.shell.prompt + line)
        result = self.shell.execute(line)
        if result.output:
            self.append(result.output)
        if result.error:
            self.append(result.error, TAG_ERROR)
        if result.exit_requested:
            self.root.destroy()
        return result

    def show_debug(self, lines: list[str]) -> None:
        """Display debug lines."""
        for line in lines:
            self.append(line, TAG_DEBUG)

    def run_script(self, lines: list[str]) -> None:
        """Run script lines, showing both the input and the output."""
        for line in lines:
            if not strip_comment(line).strip():
                continue
            if self.run_line(line).exit_requested:
                break

    def on_enter(self, _event: tk.Event) -> None:
        """Run the line typed by the user."""
        line = self.entry.get()
        self.entry.delete(0, tk.END)
        self.run_line(line)
