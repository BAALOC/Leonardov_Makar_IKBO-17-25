"""Tests of the dependency graph and its text output."""

import unittest

from depgraph.graph import Graph, build_graph
from depgraph.render import format_graph
from depgraph.testrepo import FileRepository, parse_test_repository


def repo(text: str) -> FileRepository:
    """Parse a test repository text."""
    return parse_test_repository(text, 'repo.txt')


class BuildGraphTest(unittest.TestCase):
    """Transitive dependencies, filter and cycles."""

    def test_chain(self) -> None:
        """Transitive dependencies are included."""
        graph = build_graph(repo('A: B\nB: C\nC:\n'), 'A')
        self.assertEqual(graph.edges, {'A': ['B'], 'B': ['C'], 'C': []})
        self.assertEqual(graph.cycles, [])

    def test_dfs_order(self) -> None:
        """Packages are listed in depth-first preorder."""
        graph = build_graph(
            repo('A: B C\nB: D\nC: E\nD:\nE:\n'), 'A')
        self.assertEqual(list(graph.edges), ['A', 'B', 'D', 'C', 'E'])

    def test_shared_dependency_is_visited_once(self) -> None:
        """A diamond has one node for the shared dependency."""
        graph = build_graph(repo('A: B C\nB: D\nC: D\nD:\n'), 'A')
        self.assertEqual(sorted(graph.edges), ['A', 'B', 'C', 'D'])
        self.assertEqual(graph.edges['C'], ['D'])
        self.assertEqual(graph.cycles, [])

    def test_unreachable_packages_are_ignored(self) -> None:
        """Only reachable packages are in the graph."""
        graph = build_graph(repo('A: B\nB:\nC: D\nD:\n'), 'A')
        self.assertEqual(sorted(graph.edges), ['A', 'B'])

    def test_unknown_dependency_is_a_leaf(self) -> None:
        """A dependency without its own line has no dependencies."""
        graph = build_graph(repo('A: X\n'), 'A')
        self.assertEqual(graph.edges, {'A': ['X'], 'X': []})

    def test_simple_cycle(self) -> None:
        """A cycle is recorded and does not loop forever."""
        graph = build_graph(repo('A: B\nB: C\nC: A\n'), 'A')
        self.assertEqual(list(graph.edges), ['A', 'B', 'C'])
        self.assertEqual(graph.cycles, [['A', 'B', 'C', 'A']])

    def test_self_dependency(self) -> None:
        """A package that depends on itself is a cycle."""
        graph = build_graph(repo('A: A B\nB:\n'), 'A')
        self.assertEqual(graph.cycles, [['A', 'A']])
        self.assertEqual(graph.edges['A'], ['A', 'B'])

    def test_cycle_not_through_root(self) -> None:
        """A cycle below the root is found."""
        graph = build_graph(repo('A: B\nB: C\nC: B\n'), 'A')
        self.assertEqual(graph.cycles, [['B', 'C', 'B']])

    def test_several_cycles(self) -> None:
        """Every cycle is recorded."""
        graph = build_graph(
            repo('A: B C\nB: A\nC: D\nD: C\n'), 'A')
        self.assertEqual(graph.cycles, [['A', 'B', 'A'], ['C', 'D', 'C']])

    def test_filter_removes_packages(self) -> None:
        """Packages whose name contains the substring are skipped."""
        graph = build_graph(
            repo('A: AB BC\nAB: ABC\nBC:\nABC:\n'), 'A', 'BC')
        self.assertEqual(graph.edges, {'A': ['AB'], 'AB': []})

    def test_filter_applies_to_whole_subtree(self) -> None:
        """Dependencies of a skipped package are not reached."""
        graph = build_graph(repo('A: B\nB: C\nC:\n'), 'A', 'B')
        self.assertEqual(graph.edges, {'A': []})

    def test_filter_keeps_other_paths(self) -> None:
        """A package skipped on one path stays on another."""
        graph = build_graph(repo('A: B C\nB: D\nC: D\nD:\n'), 'A', 'B')
        self.assertEqual(list(graph.edges), ['A', 'C', 'D'])

    def test_filter_breaks_cycle(self) -> None:
        """Removing a package can remove the cycle."""
        graph = build_graph(repo('A: B\nB: C\nC: A\n'), 'A', 'C')
        self.assertEqual(graph.cycles, [])

    def test_deep_chain(self) -> None:
        """A chain of a few hundred packages is processed."""
        names = ['Q' * (index + 1) for index in range(300)]
        lines = [f'{a}: {b}' for a, b in zip(names, names[1:], strict=False)]
        graph = build_graph(repo('\n'.join(lines) + '\n'), names[0])
        self.assertEqual(len(graph.edges), len(names))


class FormatGraphTest(unittest.TestCase):
    """Text output."""

    def test_format(self) -> None:
        """The output lists packages, counts and cycles."""
        graph = build_graph(repo('A: B\nB: A C\nC:\n'), 'A')
        self.assertEqual(format_graph(graph), [
            'Dependency graph of A:',
            'A -> B',
            'B -> A, C',
            'C -> (none)',
            'Packages: 3',
            'Cycles: 1',
            '  A -> B -> A',
        ])

    def test_empty_graph(self) -> None:
        """A graph without packages has only the counters."""
        self.assertEqual(format_graph(Graph('A')), [
            'Dependency graph of A:', 'Packages: 0', 'Cycles: 0'])
