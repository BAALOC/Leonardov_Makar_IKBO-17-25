"""Dependency graph built by a recursive depth-first search."""

from dataclasses import dataclass, field

from depgraph.repository import Repository


@dataclass
class Graph:
    """Dependency graph: edges in DFS order and the cycles found."""

    root: str
    edges: dict[str, list[str]] = field(default_factory=dict)
    cycles: list[list[str]] = field(default_factory=list)


class GraphBuilder:
    """Recursive DFS over the transitive dependencies of a package."""

    def __init__(self, repository: Repository, substring: str = '') -> None:
        """Create a builder that skips names with the substring."""
        self.repository = repository
        self.substring = substring
        self.graph = Graph(root='')
        self.path: list[str] = []

    def is_excluded(self, name: str) -> bool:
        """Return True if the package must not be analyzed."""
        return bool(self.substring) and self.substring in name

    def build(self, root: str) -> Graph:
        """Build the graph of everything reachable from the root."""
        self.graph = Graph(root=root)
        self.path = []
        self.visit(root)
        return self.graph

    def visit(self, name: str) -> None:
        """Record the edges of a package and visit its dependencies."""
        self.path.append(name)
        dependencies = [
            dependency for dependency in self.repository.dependencies(name)
            if not self.is_excluded(dependency)]
        self.graph.edges[name] = dependencies
        for dependency in dependencies:
            if dependency in self.path:
                self.record_cycle(dependency)
            elif dependency not in self.graph.edges:
                self.visit(dependency)
        self.path.pop()

    def record_cycle(self, dependency: str) -> None:
        """Save the cycle closed by an edge to a package on the path."""
        start = self.path.index(dependency)
        self.graph.cycles.append([*self.path[start:], dependency])


def build_graph(
        repository: Repository, root: str, substring: str = '') -> Graph:
    """Build the dependency graph of a package."""
    return GraphBuilder(repository, substring).build(root)
