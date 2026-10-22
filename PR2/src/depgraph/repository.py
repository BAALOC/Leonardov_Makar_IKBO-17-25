"""Common types of package repositories."""

from typing import Protocol


class RepositoryError(Exception):
    """Raised when a repository cannot be read or is malformed."""


class Repository(Protocol):
    """Source of package dependencies."""

    def has_package(self, name: str) -> bool:
        """Return True if the repository describes the package."""

    def dependencies(self, name: str) -> list[str]:
        """Return direct dependencies of the package."""
