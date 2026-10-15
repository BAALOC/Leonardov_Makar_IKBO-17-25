"""Command interpreter of the emulator."""

from collections.abc import Callable
from dataclasses import dataclass

from emulator.parser import parse_line
from emulator.vfs import SEPARATOR, Node, create_root, tree_lines

DEFAULT_VFS_NAME = 'vfs'


@dataclass
class Result:
    """Outcome of one command line."""

    output: str = ''
    error: str = ''
    exit_requested: bool = False


def describe_call(name: str, args: list[str]) -> Result:
    """Build the output of a stub command: its name and arguments."""
    return Result(output=f'{name}: args={args}')


class Shell:
    """Interpreter that dispatches commands to their handlers."""

    def __init__(self, vfs_name: str = DEFAULT_VFS_NAME,
                 root: Node | None = None) -> None:
        """Create a shell attached to the VFS with the given name."""
        self.vfs_name = vfs_name
        self.root = root if root is not None else create_root()
        self.handlers: dict[str, Callable[[list[str]], Result]] = {
            'ls': self.cmd_ls,
            'cd': self.cmd_cd,
            'exit': self.cmd_exit,
            'vfs-tree': self.cmd_vfs_tree,
        }

    @property
    def prompt(self) -> str:
        """Return the input prompt."""
        return f'{self.vfs_name}$ '

    def execute(self, line: str) -> Result:
        """Parse and run one command line."""
        tokens = parse_line(line)
        if not tokens:
            return Result()
        name, args = tokens[0], tokens[1:]
        handler = self.handlers.get(name)
        if handler is None:
            return Result(error=f'{name}: command not found')
        return handler(args)

    def cmd_ls(self, args: list[str]) -> Result:
        """Stub of ls."""
        return describe_call('ls', args)

    def cmd_cd(self, args: list[str]) -> Result:
        """Stub of cd."""
        return describe_call('cd', args)

    def cmd_exit(self, args: list[str]) -> Result:
        """Ask the front end to close the emulator."""
        if args:
            return Result(error='exit: too many arguments')
        return Result(exit_requested=True)

    def cmd_vfs_tree(self, args: list[str]) -> Result:
        """Print the whole VFS as a tree (service command)."""
        if args:
            return Result(error='vfs-tree: too many arguments')
        return Result(output='\n'.join([SEPARATOR, *tree_lines(self.root)]))
