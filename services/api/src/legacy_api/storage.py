"""Object storage port (DATABASE_SCHEMA: Artifact.storage_ref is a
content-addressed Object Storage key; originals are preserved unmodified).

The local backend stores content-addressed files on disk; the Supabase
Storage adapter binds at platform provisioning (DEP-09) behind the same
port, per the vendor exit strategy (DEPLOYMENT 4.10).
"""

import hashlib
from pathlib import Path
from typing import Protocol


class ObjectStorage(Protocol):
    def put(self, data: bytes) -> str:
        """Store bytes; returns the content-addressed key."""
        ...

    def get(self, key: str) -> bytes: ...

    def exists(self, key: str) -> bool: ...


def content_key(data: bytes) -> str:
    digest = hashlib.sha256(data).hexdigest()
    return f"sha256/{digest[:2]}/{digest}"


class LocalObjectStorage:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)

    def _path(self, key: str) -> Path:
        path = (self.root / key).resolve()
        if not path.is_relative_to(self.root.resolve()):
            raise ValueError("invalid storage key")
        return path

    def put(self, data: bytes) -> str:
        key = content_key(data)
        path = self._path(key)
        if not path.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
        return key

    def get(self, key: str) -> bytes:
        return self._path(key).read_bytes()

    def exists(self, key: str) -> bool:
        return self._path(key).exists()
