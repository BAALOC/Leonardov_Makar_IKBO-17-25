"""Reading of the start script."""


class ScriptError(Exception):
    """Raised when the start script cannot be read."""


def read_script(path: str) -> list[str]:
    """Return lines of the start script."""
    try:
        with open(path, encoding='utf-8') as source:
            return source.read().splitlines()
    except FileNotFoundError:
        raise ScriptError(f'{path}: file not found') from None
    except OSError as error:
        raise ScriptError(f'{path}: {error.strerror}') from None
    except UnicodeDecodeError:
        raise ScriptError(f'{path}: not UTF-8 text') from None
