"""Command line entry point."""

import sys

from depgraph.apk import load_apk_index
from depgraph.config import Config, parse_args
from depgraph.graph import build_graph
from depgraph.render import format_graph
from depgraph.repository import Repository, RepositoryError
from depgraph.testrepo import load_test_repository

EXIT_SUCCESS = 0
EXIT_FAILURE = 1


def fail(message: str) -> int:
    """Print an error message and return the failure exit code."""
    print(f'depgraph: error: {message}', file=sys.stderr)
    return EXIT_FAILURE


def open_repository(config: Config) -> Repository:
    """Load the real or the test repository."""
    if config.test_mode:
        return load_test_repository(config.repo)
    return load_apk_index(config.repo)


def main(argv: list[str] | None = None) -> int:
    """Print the transitive dependency graph of the package."""
    config = parse_args(argv)
    try:
        repository = open_repository(config)
        if not repository.has_package(config.package):
            return fail(f'package {config.package!r} not found in repository')
        graph = build_graph(
            repository, config.package, config.filter_substring)
    except RepositoryError as error:
        return fail(str(error))
    except RecursionError:
        return fail('dependency chain is too deep')
    print('\n'.join(format_graph(graph)))
    return EXIT_SUCCESS
