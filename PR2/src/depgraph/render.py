"""Text output of a dependency graph."""

from depgraph.graph import Graph

NO_DEPENDENCIES = '(none)'


def format_graph(graph: Graph) -> list[str]:
    """Return the graph as lines: one per package, then the cycles."""
    lines = [f'Dependency graph of {graph.root}:']
    for name, dependencies in graph.edges.items():
        targets = ', '.join(dependencies) or NO_DEPENDENCIES
        lines.append(f'{name} -> {targets}')
    lines.append(f'Packages: {len(graph.edges)}')
    lines.append(f'Cycles: {len(graph.cycles)}')
    lines.extend('  ' + ' -> '.join(cycle) for cycle in graph.cycles)
    return lines
