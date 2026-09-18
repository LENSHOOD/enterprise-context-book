"""Read immutable Git blobs in one batch process; fixtures require opt-in."""
from __future__ import annotations

import fnmatch
import hashlib
from pathlib import Path
import subprocess


def matches_scope(path: str, pattern: str) -> bool:
    """Path glob: '*' stays within a directory, '**' matches zero or more."""
    if pattern.startswith('/') or '..' in pattern.split('/'):
        raise ValueError('scope must be relative to the repository')
    def match(parts, glob):
        if not glob:
            return not parts
        if glob[0] == '**':
            return match(parts, glob[1:]) or bool(parts and match(parts[1:], glob))
        return bool(parts and fnmatch.fnmatchcase(parts[0], glob[0]) and match(parts[1:], glob[1:]))
    return match(path.split('/'), pattern.split('/'))


class SourceTree:
    def __init__(self, repo: Path, ref: str, fixture: bool = False, scope: list[str] | None = None):
        self.repo = repo.resolve()
        self.process = None
        self.fixture = fixture
        self.scope = scope or []
        self.blobs = {}
        if not self.repo.is_dir():
            raise FileNotFoundError(f'repository does not exist: {self.repo}')
        if fixture:
            self.paths = sorted(p.relative_to(self.repo).as_posix() for p in self.repo.rglob('*')
                                if p.is_file() and not p.is_symlink() and '.git' not in p.parts
                                and (not self.scope or any(matches_scope(
                                    p.relative_to(self.repo).as_posix(), pattern
                                ) for pattern in self.scope)))
            digest = hashlib.sha256()
            self.blobs = {p:(self.repo/p).read_bytes() for p in self.paths}
            for path, data in self.blobs.items():
                digest.update(path.encode() + b'\0' + hashlib.sha256(data).digest())
            self.commit = f'fixture:{ref}:{digest.hexdigest()}'
        else:
            try:
                # Avoid silently interpreting a directory inside some other repo.
                prefix = self._git('rev-parse', '--show-prefix').strip()
                if prefix:
                    raise ValueError('use the Git repository root or explicit --fixture')
                self.commit = self._git('rev-parse', '--verify', '--end-of-options', f'{ref}^{{commit}}').decode().strip()
                entries = self._git('ls-tree', '-rz', '--full-tree', self.commit).split(b'\0')
            except (subprocess.CalledProcessError, FileNotFoundError) as exc:
                raise ValueError(f'cannot resolve Git ref {ref!r}; use --fixture only for sample files') from exc
            self.paths = []
            for entry in filter(None, entries):
                metadata, path_bytes = entry.split(b'\t', 1)
                mode, kind, oid = metadata.split()
                path = path_bytes.decode('utf-8', errors='surrogateescape')
                if self.scope and not any(matches_scope(path, pattern) for pattern in self.scope):
                    continue
                self.paths.append(path)
                if kind == b'blob' and mode in (b'100644', b'100755'):
                    self.blobs[path] = oid
            self.paths.sort()

    def _git(self, *args):
        return subprocess.run(['git', '-C', str(self.repo), *args], check=True,
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE).stdout

    def read(self, path: str) -> str:
        if self.fixture:
            return self.blobs[path].decode('utf-8', errors='replace')
        if self.process is None:
            self.process = subprocess.Popen(['git', '-C', str(self.repo), 'cat-file', '--batch'],
                                            stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                            stderr=subprocess.DEVNULL)
        self.process.stdin.write(self.blobs[path] + b'\n')
        self.process.stdin.flush()
        header = self.process.stdout.readline().split()
        if len(header) != 3 or header[1] != b'blob':
            raise ValueError(f'cannot read pinned blob: {path}')
        size = int(header[2])
        data = self.process.stdout.read(size)
        if len(data) != size or self.process.stdout.read(1) != b'\n':
            raise ValueError(f'incomplete pinned blob: {path}')
        return data.decode('utf-8', errors='replace')

    def __enter__(self):
        return self

    def __exit__(self, *args):
        if self.process:
            self.process.stdin.close()
            self.process.stdout.close()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait()
