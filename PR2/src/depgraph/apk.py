"""Alpine Linux (apk) repository index: download and parsing."""

from __future__ import annotations

import io
import operator
import re
import tarfile
import urllib.error
import urllib.request
import zlib
from collections.abc import Iterable
from dataclasses import dataclass, field
from http.client import HTTPException

from depgraph.repository import RepositoryError

INDEX_FILE = 'APKINDEX.tar.gz'
INDEX_MEMBER = 'APKINDEX'
TIMEOUT_SECONDS = 30
VERSION_OPERATOR = re.compile(r'[<>=~]')
NEGATION = '!'
TEXT_CODEC = 'utf-8'


@dataclass
class Package:
    """A package record of APKINDEX."""

    name: str
    depends: list[str] = field(default_factory=list)
    provides: list[str] = field(default_factory=list)
    priority: int = 0


def strip_version(entry: str) -> str:
    """Remove a version constraint from a entry."""
    return VERSION_OPERATOR.split(entry, maxsplit=1)[0]


def parse_priority(value: str) -> int:
    """Convert the provider priority field to a number."""
    return int(value) if value.isdigit() else 0


def parse_record(record: str) -> Package | None:
    """Build a package from one APKINDEX record."""
    fields = {}
    for line in record.splitlines():
        key, _, value = line.partition(':')
        fields[key] = value
    name = fields.get('P')
    if not name:
        return None
    return Package(
        name=name,
        depends=fields.get('D', '').split(),
        provides=fields.get('p', '').split(),
        priority=parse_priority(fields.get('k', '')))


class ApkIndex:
    """Repository index that resolves virtual package names."""

    def __init__(self, packages: Iterable[Package]) -> None:
        """Index packages by name and by the names they provide."""
        self.packages: dict[str, Package] = {}
        self.providers: dict[str, list[Package]] = {}
        for package in packages:
            if package.name in self.packages:
                continue
            self.packages[package.name] = package
            for entry in package.provides:
                name = strip_version(entry)
                self.providers.setdefault(name, []).append(package)

    def has_package(self, name: str) -> bool:
        """Return True if the index has a package with this name."""
        return name in self.packages

    def resolve(self, name: str) -> str:
        """Return the package that satisfies a dependency name.

        A real package wins; otherwise the provider with the highest
        priority (the first one on a tie); otherwise the name itself.
        """
        if name in self.packages:
            return name
        candidates = self.providers.get(name)
        if not candidates:
            return name
        best = max(candidates, key=operator.attrgetter('priority'))
        return best.name

    def dependencies(self, name: str) -> list[str]:
        """Return direct dependencies of a package as package names."""
        package = self.packages.get(name)
        if package is None:
            return []
        resolved: list[str] = []
        for entry in package.depends:
            if entry.startswith(NEGATION):
                continue
            target = self.resolve(strip_version(entry))
            if target != name and target not in resolved:
                resolved.append(target)
        return resolved


def parse_index(text: str) -> ApkIndex:
    """Parse the text of APKINDEX."""
    records = text.replace('\r\n', '\n').split('\n\n')
    packages = (parse_record(record) for record in records)
    index = ApkIndex(package for package in packages if package)
    if not index.packages:
        raise RepositoryError('no packages found in the index')
    return index


def index_url(repo_url: str) -> str:
    """Return the URL of the index file of a repository."""
    base = repo_url.rstrip('/')
    if base.endswith(INDEX_FILE):
        return base
    return f'{base}/{INDEX_FILE}'


def download(url: str) -> bytes:
    """Download a file over HTTP(S)."""
    try:
        with urllib.request.urlopen(url, timeout=TIMEOUT_SECONDS) as reply:
            return reply.read()
    except urllib.error.HTTPError as error:
        raise RepositoryError(
            f'cannot download {url}: HTTP {error.code} {error.reason}'
        ) from None
    except (urllib.error.URLError, HTTPException, OSError) as error:
        reason = getattr(error, 'reason', error)
        raise RepositoryError(f'cannot download {url}: {reason}') from None


def read_member(tar: tarfile.TarFile) -> bytes:
    """Return the contents of the APKINDEX file of an archive."""
    try:
        member = tar.extractfile(INDEX_MEMBER)
    except KeyError:
        member = None
    if member is None:
        raise RepositoryError(f'{INDEX_MEMBER} not found in the archive')
    return member.read()


def extract_index(archive: bytes) -> str:
    """Return the text of APKINDEX stored in APKINDEX.tar.gz."""
    try:
        with tarfile.open(fileobj=io.BytesIO(archive), mode='r:gz',
                          ignore_zeros=True) as tar:
            return read_member(tar).decode(TEXT_CODEC)
    except (tarfile.TarError, OSError, EOFError, zlib.error,
            UnicodeDecodeError):
        raise RepositoryError('invalid index archive') from None


def load_apk_index(repo_url: str) -> ApkIndex:
    """Download and parse the index of an Alpine repository."""
    return parse_index(extract_index(download(index_url(repo_url))))
