"""Command line parameters of the tool and their validation."""

import argparse
import re
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlsplit

APK_NAME = re.compile(r'[A-Za-z0-9][A-Za-z0-9+._-]*')
TEST_NAME = re.compile(r'[A-Z]+')
URL_SCHEMES = ('http', 'https')
IMAGE_SUFFIX = '.png'
DEFAULT_OUTPUT = 'graph.png'
EXIT_USAGE = 2


class ConfigError(Exception):
    """Raised when a parameter has an invalid value."""


@dataclass(frozen=True)
class Config:
    """Parameters given by the user."""

    package: str
    repo: str
    test_mode: bool = False
    output: str = DEFAULT_OUTPUT
    ascii_tree: bool = False
    filter_substring: str = ''


def check_package(config: Config) -> None:
    """Check the package name against the naming rules of the mode."""
    pattern = TEST_NAME if config.test_mode else APK_NAME
    if not pattern.fullmatch(config.package):
        kind = 'capital Latin letters' if config.test_mode else 'apk name'
        raise ConfigError(
            f'invalid package name {config.package!r}: expected {kind}')


def check_url(url: str) -> None:
    """Check that the repository location is an http(s) URL."""
    try:
        parts = urlsplit(url)
    except ValueError as error:
        raise ConfigError(
            f'invalid repository URL {url!r}: {error}') from None
    if parts.scheme not in URL_SCHEMES or not parts.netloc:
        raise ConfigError(f'invalid repository URL {url!r}: '
                          'expected http:// or https:// address')
    if any(char.isspace() for char in url):
        raise ConfigError(f'invalid repository URL {url!r}: whitespace')


def check_test_file(path: str) -> None:
    """Check that the test repository file exists and is readable."""
    file = Path(path)
    if not file.exists():
        raise ConfigError(f'test repository file not found: {path}')
    if not file.is_file():
        raise ConfigError(f'test repository is not a file: {path}')


def check_output(output: str) -> None:
    """Check the name of the image file."""
    path = Path(output)
    if path.suffix.lower() != IMAGE_SUFFIX:
        raise ConfigError(
            f'invalid output file {output!r}: expected {IMAGE_SUFFIX}')
    if path.is_dir():
        raise ConfigError(f'output file is a directory: {output}')
    if not path.resolve().parent.is_dir():
        raise ConfigError(f'output directory does not exist: {output}')


def check_filter(config: Config) -> None:
    """Check the filter substring."""
    substring = config.filter_substring
    if any(char.isspace() for char in substring):
        raise ConfigError(f'invalid filter {substring!r}: whitespace')
    if substring and substring in config.package:
        raise ConfigError(
            f'package {config.package!r} is excluded by filter '
            f'{substring!r}')


def validate(config: Config) -> None:
    """Raise ConfigError if any parameter is invalid."""
    check_package(config)
    if config.test_mode:
        check_test_file(config.repo)
    else:
        check_url(config.repo)
    check_output(config.output)
    check_filter(config)


def build_parser() -> argparse.ArgumentParser:
    """Create the command line parser."""
    parser = argparse.ArgumentParser(
        prog='depgraph', allow_abbrev=False,
        description='Dependency graph of Alpine Linux packages.')
    parser.add_argument('--package', required=True, metavar='NAME',
                        help='name of the analyzed package')
    parser.add_argument('--repo', required=True, metavar='URL_OR_FILE',
                        help='repository URL or test repository file')
    parser.add_argument('--test-mode', action='store_true',
                        help='treat --repo as a test repository file')
    parser.add_argument('--output', default=DEFAULT_OUTPUT, metavar='FILE',
                        help='image file name (default: %(default)s)')
    parser.add_argument('--ascii-tree', action='store_true',
                        help='print dependencies as an ASCII tree')
    parser.add_argument('--filter', default='', metavar='SUBSTRING',
                        help='skip packages whose name contains it')
    return parser


def parse_args(argv: list[str] | None = None) -> Config:
    """Parse and validate command line arguments."""
    parser = build_parser()
    namespace = parser.parse_args(argv)
    config = Config(
        package=namespace.package, repo=namespace.repo,
        test_mode=namespace.test_mode, output=namespace.output,
        ascii_tree=namespace.ascii_tree,
        filter_substring=namespace.filter)
    try:
        validate(config)
    except ConfigError as error:
        parser.error(str(error))
    return config
