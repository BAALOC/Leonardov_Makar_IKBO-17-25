"""Test repository described by a text file.

Every line has the form ``NAME: DEPENDENCY DEPENDENCY``. Package names
are capital Latin letters. Blank lines and ``#`` comments are skipped.
"""

import re
from pathlib import Path

from depgraph.repository import RepositoryError

NAME = re.compile(r'[A-Z]+')
COMMENT_MARK = '#'
SEPARATOR = ':'


class FileRepository:
    """Repository given as a map from a package to its dependencies."""

    def __init__(self, graph: dict[str, list[str]]) -> None:
        """Store the dependency lists."""
        self.graph = graph

    def has_package(self, name: str) -> bool:
        """Return True if the package has its own line in the file."""
        return name in self.graph

    def dependencies(self, name: str) -> list[str]:
        """Return direct dependencies; unknown packages have none."""
        return list(self.graph.get(name, []))


def parse_line(line: str) -> tuple[str, list[str]] | None:
    """Parse one line; return None for blank and comment lines."""
    text = line.split(COMMENT_MARK, 1)[0].strip()
    if not text:
        return None
    name, separator, rest = text.partition(SEPARATOR)
    if not separator:
        raise RepositoryError(f'expected "NAME: DEPENDENCIES", got {text!r}')
    name = name.strip()
    dependencies = rest.split()
    for item in [name, *dependencies]:
        if not NAME.fullmatch(item):
            raise RepositoryError(f'invalid package name {item!r}')
    return name, list(dict.fromkeys(dependencies))


def parse_test_repository(text: str, source: str) -> FileRepository:
    """Parse the text of a test repository file."""
    graph: dict[str, list[str]] = {}
    for number, line in enumerate(text.splitlines(), start=1):
        try:
            entry = parse_line(line)
        except RepositoryError as error:
            raise RepositoryError(f'{source}:{number}: {error}') from None
        if entry is None:
            continue
        name, dependencies = entry
        if name in graph:
            raise RepositoryError(
                f'{source}:{number}: duplicate package {name!r}')
        graph[name] = dependencies
    return FileRepository(graph)


def load_test_repository(path: str) -> FileRepository:
    """Read a test repository file."""
    try:
        text = Path(path).read_text(encoding='utf-8')
    except OSError as error:
        raise RepositoryError(f'{path}: {error.strerror}') from None
    except UnicodeDecodeError:
        raise RepositoryError(f'{path}: not UTF-8 text') from None
    return parse_test_repository(text, path)
