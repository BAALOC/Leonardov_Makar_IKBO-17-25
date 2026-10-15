"""Command line parameters of the emulator."""

import argparse
from dataclasses import dataclass
from pathlib import Path

from emulator.shell import DEFAULT_VFS_NAME

NOT_SET = '(not set)'


@dataclass(frozen=True)
class Config:
    """Parameters given on the command line."""

    vfs_path: str | None = None
    script_path: str | None = None

    @property
    def vfs_name(self) -> str:
        """Return the VFS name shown in the title and in the prompt."""
        if self.vfs_path is None:
            return DEFAULT_VFS_NAME
        return Path(self.vfs_path).stem or DEFAULT_VFS_NAME

    def debug_lines(self) -> list[str]:
        """Return all parameters as key = value lines."""
        values = {'vfs': self.vfs_path, 'script': self.script_path}
        return [f'[debug] {key} = {value if value is not None else NOT_SET}'
                for key, value in values.items()]


def build_parser() -> argparse.ArgumentParser:
    """Create the command line parser."""
    parser = argparse.ArgumentParser(
        prog='emulator', description='Shell emulator with a VFS.',
        allow_abbrev=False)
    parser.add_argument(
        '--vfs', metavar='PATH', help='physical location of the VFS')
    parser.add_argument(
        '--script', metavar='PATH', help='path to the start script')
    return parser


def parse_args(argv: list[str] | None = None) -> Config:
    """Parse command line arguments into a Config."""
    namespace = build_parser().parse_args(argv)
    return Config(vfs_path=namespace.vfs, script_path=namespace.script)
