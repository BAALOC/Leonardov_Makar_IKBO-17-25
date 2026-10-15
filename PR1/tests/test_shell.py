"""Tests of the command interpreter."""

import os
import unittest
from unittest import mock

from emulator.shell import Shell
from emulator.vfs import Node


class ShellTest(unittest.TestCase):
    """Behaviour of the stub commands and of error reporting."""

    def setUp(self) -> None:
        """Create a shell."""
        self.shell = Shell('demo')

    def test_prompt_contains_vfs_name(self) -> None:
        """The prompt shows the VFS name."""
        self.assertEqual(self.shell.prompt, 'demo$ ')

    def test_empty_line_does_nothing(self) -> None:
        """A blank line produces neither output nor errors."""
        result = self.shell.execute('')
        self.assertEqual((result.output, result.error), ('', ''))

    def test_ls_stub(self) -> None:
        """The ls stub prints its name and arguments."""
        result = self.shell.execute('ls -l /tmp')
        self.assertEqual(result.output, "ls: args=['-l', '/tmp']")

    def test_cd_stub(self) -> None:
        """The cd stub prints its name and arguments."""
        result = self.shell.execute('cd')
        self.assertEqual(result.output, 'cd: args=[]')

    def test_unknown_command(self) -> None:
        """An unknown command is reported."""
        result = self.shell.execute('foo bar')
        self.assertEqual(result.error, 'foo: command not found')

    def test_exit(self) -> None:
        """The exit command requests closing of the emulator."""
        self.assertTrue(self.shell.execute('exit').exit_requested)

    def test_exit_with_arguments(self) -> None:
        """The exit command rejects arguments and does not close."""
        result = self.shell.execute('exit now')
        self.assertEqual(result.error, 'exit: too many arguments')
        self.assertFalse(result.exit_requested)

    def test_environment_in_arguments(self) -> None:
        """Variables are expanded before the command runs."""
        with mock.patch.dict(os.environ, {'HOME': '/home/user'}):
            result = self.shell.execute('ls $HOME')
        self.assertEqual(result.output, "ls: args=['/home/user']")

    def test_vfs_tree_of_empty_vfs(self) -> None:
        """The service command shows only the root of an empty VFS."""
        self.assertEqual(self.shell.execute('vfs-tree').output, '/')

    def test_vfs_tree(self) -> None:
        """The service command draws the loaded VFS."""
        root = Node(is_dir=True)
        root.children['f'] = Node(is_dir=False, data=b'12')
        result = Shell('demo', root).execute('vfs-tree')
        self.assertEqual(result.output, '/\n`-- f (2 B)')

    def test_vfs_tree_with_arguments(self) -> None:
        """The service command rejects arguments."""
        result = self.shell.execute('vfs-tree /')
        self.assertEqual(result.error, 'vfs-tree: too many arguments')
