"""Command line entry point."""

import sys
import tkinter as tk

from emulator.config import parse_args
from emulator.gui import EmulatorWindow
from emulator.script import ScriptError, read_script
from emulator.shell import Shell
from emulator.vfs import VfsError, create_root, load_vfs

EXIT_SUCCESS = 0
EXIT_FAILURE = 1


def run_gui(shell: Shell, debug: list[str], script: list[str]) -> int:
    """Show the window, print debug lines and run the start script."""
    try:
        root = tk.Tk()
    except tk.TclError as error:
        print(f'emulator: cannot open window: {error}', file=sys.stderr)
        return EXIT_FAILURE
    window = EmulatorWindow(root, shell)
    window.show_debug(debug)
    root.after(0, window.run_script, script)
    root.mainloop()
    return EXIT_SUCCESS


def fail(message: str) -> int:
    """Print an error message and return the failure exit code."""
    print(f'emulator: {message}', file=sys.stderr)
    return EXIT_FAILURE


def main(argv: list[str] | None = None) -> int:
    """Run the emulator and return the process exit code."""
    config = parse_args(argv)
    root = create_root()
    script: list[str] = []
    try:
        if config.vfs_path is not None:
            root = load_vfs(config.vfs_path)
    except VfsError as error:
        return fail(f'cannot load VFS: {error}')
    try:
        if config.script_path is not None:
            script = read_script(config.script_path)
    except ScriptError as error:
        return fail(f'cannot read script: {error}')
    return run_gui(
        Shell(config.vfs_name, root), config.debug_lines(), script)
