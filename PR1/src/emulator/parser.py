"""Command line parser with comments and variable expansion."""

import os
import re

COMMENT_MARK = '#'
VARIABLE = re.compile(r'\$(?:(\w+)|\{(\w+)\})')


def lookup_variable(match: re.Match[str]) -> str:
    """Return the value of the matched variable or an empty string."""
    return os.environ.get(match.group(1) or match.group(2), '')


def expand_variables(token: str) -> str:
    """Replace $NAME and ${NAME} with environment variable values."""
    return VARIABLE.sub(lookup_variable, token)


def strip_comment(line: str) -> str:
    """Remove a comment started by a hash sign."""
    return line.split(COMMENT_MARK, 1)[0]


def parse_line(line: str) -> list[str]:
    """Split a line into tokens and expand variables in each of them."""
    tokens = (expand_variables(token)
              for token in strip_comment(line).split())
    return [token for token in tokens if token]
