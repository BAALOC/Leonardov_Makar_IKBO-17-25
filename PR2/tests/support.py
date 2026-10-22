"""Helpers shared by the tests."""

import functools
import gzip
import io
import os
import shutil
import tarfile
import tempfile
import threading
import unittest
from collections.abc import Iterator
from contextlib import contextmanager
from functools import cached_property
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from unittest import mock

SAMPLE_INDEX = """\
C:Q1musl
P:musl
V:1.2.5-r0
p:so:libc.musl-x86_64.so.1=1
k:9

C:Q1busybox
P:busybox
V:1.36.1-r0
D:so:libc.musl-x86_64.so.1
p:cmd:busybox=1.36.1-r0 cmd:sh=1.36.1-r0

C:Q1zlib
P:zlib
V:1.3.1-r0
D:so:libc.musl-x86_64.so.1
p:so:libz.so.1=1.3.1

C:Q1certs
P:ca-certificates-bundle
V:20240226-r0

C:Q1libcurl
P:libcurl
V:8.5.0-r0
D:ca-certificates-bundle so:libc.musl-x86_64.so.1 so:libz.so.1
p:so:libcurl.so.4=4.8.0

C:Q1curl
P:curl
V:8.5.0-r0
D:ca-certificates-bundle so:libcurl.so.4 so:libc.musl-x86_64.so.1 cmd:sh \
musl>=1.2.0 so:libz.so.1 so:libmissing.so.9 !curl-dev
"""

CURL_DEPENDENCIES = [
    'ca-certificates-bundle', 'libcurl', 'musl', 'busybox', 'zlib',
    'so:libmissing.so.9']
INDEX_PATH = 'alpine/main/x86_64/APKINDEX.tar.gz'
TAR_BLOCK = 512


def tar_bytes(files: dict[str, bytes]) -> bytes:
    """Build an uncompressed tar archive."""
    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode='w') as tar:
        for name, data in files.items():
            info = tarfile.TarInfo(name)
            info.size = len(data)
            tar.addfile(info, io.BytesIO(data))
    return buffer.getvalue()


def make_archive(index_text: str, cut_signature: bool = True) -> bytes:
    """Build APKINDEX.tar.gz: a signature followed by the index.

    Like abuild-sign, cut the end-of-archive blocks of the signature
    so that both gzip members form one tar stream.
    """
    signature = tar_bytes({'.SIGN.RSA.test.rsa.pub': b'sig'})
    if cut_signature:
        signature = signature[:2 * TAR_BLOCK]
    body = tar_bytes({
        'APKINDEX': index_text.encode('utf-8'),
        'DESCRIPTION': b'test repository',
    })
    return gzip.compress(signature) + gzip.compress(body)


class QuietHandler(SimpleHTTPRequestHandler):
    """Static file handler that does not log requests."""

    def log_message(self, *args: object) -> None:
        """Ignore log messages."""


class ServerTestCase(unittest.TestCase):
    """Test case with a local HTTP server and no proxy for it."""

    @cached_property
    def root(self) -> Path:
        """Return an empty temporary directory served by the server."""
        path = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, path)
        return path

    @cached_property
    def server(self) -> HTTPServer:
        """Start the server over the root directory without a proxy."""
        handler = functools.partial(QuietHandler, directory=str(self.root))
        server = HTTPServer(('127.0.0.1', 0), handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        self.addCleanup(self.stop_server)
        patcher = mock.patch.dict(
            os.environ, {'no_proxy': '127.0.0.1', 'NO_PROXY': '127.0.0.1'})
        patcher.start()
        self.addCleanup(patcher.stop)
        return server

    def stop_server(self) -> None:
        """Stop the server."""
        self.server.shutdown()
        self.server.server_close()

    @property
    def base_url(self) -> str:
        """Return the address of the server."""
        return f'http://127.0.0.1:{self.server.server_address[1]}'

    def publish(self, path: str, data: bytes) -> None:
        """Make a file available on the server."""
        target = self.root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)

    def publish_index(self, text: str = SAMPLE_INDEX) -> str:
        """Publish an index and return the repository URL."""
        self.publish(INDEX_PATH, make_archive(text))
        return f'{self.base_url}/alpine/main/x86_64'


@contextmanager
def unused_port_url() -> Iterator[str]:
    """Yield a URL of a port on which nobody listens."""
    server = HTTPServer(('127.0.0.1', 0), QuietHandler)
    port = server.server_address[1]
    server.server_close()
    yield f'http://127.0.0.1:{port}/'
