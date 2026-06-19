"""NFR-013 §2.1 / §4.2 — local-filesystem object-storage adapter.

Backend key: ``local-fs``. Stores objects as files under
``STORAGE_LOCAL_FS_ROOT``. This is the default backend so that the system
runs out-of-the-box without an external S3 service.

The local filesystem has no native pre-signed URLs and no native
server-side copy, so:

- ``capabilities.supports_presigned_*`` and ``supports_server_side_copy``
  report ``False`` — the service layer must proxy uploads/downloads through
  the backend.
- ``presign_download_url`` / ``presign_upload_url`` still return a usable URL:
  a backend-internal **signed token URL** (HMAC over key + expiry +
  constraints). The API layer (Lauf 2) redeems the token via
  :func:`verify_token` before streaming/accepting bytes.

All blocking filesystem work runs in ``asyncio.to_thread`` so the adapter
satisfies the async ``IObjectStorageAdapter`` contract without blocking the
event loop.
"""

from __future__ import annotations

import asyncio
import base64
import hashlib
import hmac
import json
import shutil
import time
from collections.abc import AsyncIterator
from pathlib import Path, PurePosixPath
from typing import Any

import structlog

from app.common.exceptions import NotFoundError
from app.domain.interfaces.object_storage_adapter import IObjectStorageAdapter
from app.domain.models.storage import (
    ObjectMetadata,
    ObjectRef,
    StorageCapabilities,
    local_fs_capabilities,
)

logger = structlog.get_logger()

BACKEND_KEY = "local-fs"

# Stream chunk size for get_object (256 KiB).
_CHUNK_SIZE = 256 * 1024


def _sanitize_key(key: str) -> PurePosixPath:
    """Normalize and validate an object key into a safe relative POSIX path.

    Rejects absolute keys and any traversal (``..``) so a key can never
    resolve outside the storage root.

    Raises:
        ValueError: when the key is empty, absolute, or escapes the root.
    """
    if not key or not key.strip():
        raise ValueError("Object key must be a non-empty string.")
    # Normalize separators; treat the key as POSIX-style regardless of OS.
    normalized = key.replace("\\", "/").strip("/")
    if not normalized:
        raise ValueError("Object key must not be empty after normalization.")
    pure = PurePosixPath(normalized)
    if pure.is_absolute():
        raise ValueError(f"Object key must be relative, got absolute: {key!r}")
    parts = pure.parts
    if any(part == ".." for part in parts):
        raise ValueError(f"Object key must not contain '..' traversal: {key!r}")
    return pure


class LocalFsStorageAdapter(IObjectStorageAdapter):
    """Filesystem-backed object storage (NFR-013 §4.2)."""

    def __init__(
        self,
        root: str,
        public_base_url: str,
        signing_secret: str,
        *,
        max_object_size_bytes: int,
        attachment_repo: Any = None,
    ) -> None:
        self._root = Path(root).resolve()
        self._public_base_url = public_base_url.rstrip("/")
        if not signing_secret:
            raise ValueError(
                "local-fs storage requires a non-empty signing secret "
                "(STORAGE_LOCALFS_SIGNING_SECRET, jwt_secret_key or fernet_key)."
            )
        self._signing_secret = signing_secret.encode("utf-8")
        self._max_object_size_bytes = max_object_size_bytes
        self._attachment_repo = attachment_repo

    @property
    def capabilities(self) -> StorageCapabilities:
        return local_fs_capabilities(self._max_object_size_bytes)

    # --- Path helpers ------------------------------------------------

    def _path_for(self, key: str) -> Path:
        rel = _sanitize_key(key)
        candidate = (self._root / rel).resolve()
        # Defense in depth: ensure the resolved path stays under root.
        if self._root != candidate and self._root not in candidate.parents:
            raise ValueError(f"Resolved path escapes storage root: {key!r}")
        return candidate

    def _meta_path_for(self, path: Path) -> Path:
        return path.with_name(path.name + ".meta.json")

    # --- Sync filesystem primitives (run via to_thread) --------------

    def _write_sync(self, path: Path, data: bytes, mime_type: str, metadata: dict[str, str]) -> ObjectRef:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        etag = hashlib.md5(data, usedforsecurity=False).hexdigest()  # noqa: S324 — etag, not security
        meta = {
            "content_type": mime_type,
            "etag": etag,
            "user_metadata": metadata,
        }
        self._meta_path_for(path).write_text(json.dumps(meta), encoding="utf-8")
        return ObjectRef(key=None, etag=etag, size_bytes=len(data))  # type: ignore[arg-type]

    def _read_sync(self, path: Path) -> bytes:
        return path.read_bytes()

    def _read_meta_sync(self, path: Path) -> dict[str, Any]:
        meta_path = self._meta_path_for(path)
        if not meta_path.exists():
            return {}
        try:
            return json.loads(meta_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError, OSError:
            return {}

    def _delete_sync(self, path: Path) -> bool:
        existed = path.exists()
        path.unlink(missing_ok=True)
        self._meta_path_for(path).unlink(missing_ok=True)
        return existed

    def _delete_prefix_sync(self, prefix_path: Path, prefix_rel: PurePosixPath) -> int:
        if not prefix_path.exists():
            # Prefix may also be a virtual key-prefix (not a directory).
            return self._delete_glob_prefix_sync(prefix_rel)
        if prefix_path.is_dir():
            count = sum(1 for p in prefix_path.rglob("*") if p.is_file() and not p.name.endswith(".meta.json"))
            shutil.rmtree(prefix_path, ignore_errors=True)
            return count
        # A file exactly matching the prefix.
        self._delete_sync(prefix_path)
        return 1

    def _delete_glob_prefix_sync(self, prefix_rel: PurePosixPath) -> int:
        """Delete keys that start with ``prefix_rel`` but are not a directory."""
        parent = (self._root / prefix_rel.parent).resolve()
        if not parent.exists() or not parent.is_dir():
            return 0
        stem = prefix_rel.name
        count = 0
        for p in parent.iterdir():
            if p.is_file() and not p.name.endswith(".meta.json") and p.name.startswith(stem):
                self._delete_sync(p)
                count += 1
        return count

    def _list_sync(self, prefix: str) -> list[str]:
        prefix_rel = prefix.replace("\\", "/").strip("/")
        keys: list[str] = []
        if not self._root.exists():
            return keys
        for p in self._root.rglob("*"):
            if not p.is_file() or p.name.endswith(".meta.json"):
                continue
            rel = p.relative_to(self._root).as_posix()
            if not prefix_rel or rel.startswith(prefix_rel):
                keys.append(rel)
        keys.sort()
        return keys

    def _copy_sync(self, src: Path, dst: Path) -> None:
        if not src.exists():
            raise NotFoundError("object", str(src))
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, dst)
        src_meta = self._meta_path_for(src)
        if src_meta.exists():
            shutil.copyfile(src_meta, self._meta_path_for(dst))

    # --- IObjectStorageAdapter contract ------------------------------

    async def put_object(
        self,
        key: str,
        stream: AsyncIterator[bytes],
        mime_type: str,
        metadata: dict[str, str] | None = None,
    ) -> ObjectRef:
        path = self._path_for(key)
        chunks: list[bytes] = []
        async for chunk in stream:
            chunks.append(chunk)
        data = b"".join(chunks)
        ref = await asyncio.to_thread(self._write_sync, path, data, mime_type, metadata or {})
        logger.info("storage_put_object", backend=BACKEND_KEY, key=key, size_bytes=ref.size_bytes)
        return ObjectRef(key=key, etag=ref.etag, size_bytes=ref.size_bytes)

    async def get_object(self, key: str) -> AsyncIterator[bytes]:
        path = self._path_for(key)
        if not await asyncio.to_thread(path.exists):
            raise NotFoundError("object", key)
        data = await asyncio.to_thread(self._read_sync, path)

        async def _iter() -> AsyncIterator[bytes]:
            for i in range(0, len(data), _CHUNK_SIZE):
                yield data[i : i + _CHUNK_SIZE]

        return _iter()

    async def delete_object(self, key: str) -> None:
        path = self._path_for(key)
        await asyncio.to_thread(self._delete_sync, path)
        logger.info("storage_delete_object", backend=BACKEND_KEY, key=key)

    async def delete_prefix(self, prefix: str) -> int:
        prefix_rel = _sanitize_key(prefix)
        prefix_path = (self._root / prefix_rel).resolve()
        if self._root != prefix_path and self._root not in prefix_path.parents:
            raise ValueError(f"Resolved prefix escapes storage root: {prefix!r}")
        count = await asyncio.to_thread(self._delete_prefix_sync, prefix_path, prefix_rel)
        logger.info("storage_delete_prefix", backend=BACKEND_KEY, prefix=prefix, deleted=count)
        return count

    async def list_objects(self, prefix: str, page_token: str | None = None) -> dict[str, Any]:
        keys = await asyncio.to_thread(self._list_sync, prefix)
        # local-fs returns the full listing in one page (no native pagination).
        return {"keys": keys, "next_page_token": None}

    async def head_object(self, key: str) -> ObjectMetadata:
        path = self._path_for(key)
        if not await asyncio.to_thread(path.exists):
            raise NotFoundError("object", key)
        stat = await asyncio.to_thread(path.stat)
        meta = await asyncio.to_thread(self._read_meta_sync, path)
        return ObjectMetadata(
            key=key,
            size_bytes=stat.st_size,
            content_type=meta.get("content_type"),
            etag=meta.get("etag", ""),
            last_modified=str(stat.st_mtime),
            user_metadata=meta.get("user_metadata", {}),
        )

    def presign_download_url(
        self,
        key: str,
        ttl_seconds: int = 900,
        response_disposition: str | None = None,
    ) -> str:
        # Validate the key so we never sign an unsafe path.
        _sanitize_key(key)
        token = self._make_token(
            {
                "op": "download",
                "key": key,
                "exp": int(time.time()) + ttl_seconds,
                "disposition": response_disposition,
            }
        )
        return f"{self._public_base_url}/{token}"

    def presign_upload_url(self, key: str, mime_type: str, ttl_seconds: int = 900) -> str:
        _sanitize_key(key)
        token = self._make_token(
            {
                "op": "upload",
                "key": key,
                "mime_type": mime_type,
                "max_size": self._max_object_size_bytes,
                "exp": int(time.time()) + ttl_seconds,
            }
        )
        return f"{self._public_base_url}/{token}"

    async def copy_object(self, src_key: str, dst_key: str) -> None:
        src = self._path_for(src_key)
        dst = self._path_for(dst_key)
        await asyncio.to_thread(self._copy_sync, src, dst)
        logger.info("storage_copy_object", backend=BACKEND_KEY, src=src_key, dst=dst_key)

    async def health_check(self) -> dict[str, Any]:
        def _probe() -> tuple[bool, str | None]:
            try:
                self._root.mkdir(parents=True, exist_ok=True)
                probe = self._root / ".health_check"
                probe.write_text("ok", encoding="utf-8")
                probe.unlink(missing_ok=True)
                return True, None
            except OSError as exc:
                return False, str(exc)

        ready, reason = await asyncio.to_thread(_probe)
        result: dict[str, Any] = {
            "backend": BACKEND_KEY,
            "root": str(self._root),
            "ready": ready,
        }
        if reason is not None:
            result["reason"] = reason
        return result

    async def delete_for_user(self, tenant_key: str, user_key: str, scope: str) -> int:
        """REQ-025 erasure hook — delete every stored object owned by a user.

        Walks the attachments catalog for ``tenant_key + created_by`` and
        deletes each backing object. Returns the number of objects deleted.
        Without a wired attachment repository this returns 0 (Lauf 2 wires it
        through the DI provider).
        """
        if self._attachment_repo is None:
            return 0
        categories = _scope_to_categories(scope)
        attachments = await asyncio.to_thread(self._attachment_repo.find_by_user, tenant_key, user_key, categories)
        deleted = 0
        for att in attachments:
            await self.delete_object(att.storage_key)
            deleted += 1
        logger.info(
            "storage_delete_for_user",
            backend=BACKEND_KEY,
            tenant_key=tenant_key,
            user_key=user_key,
            scope=scope,
            deleted=deleted,
        )
        return deleted

    async def strip_exif_for_user(self, tenant_key: str, user_key: str, scope: str) -> int:
        """REQ-025 erasure hook — strip EXIF from a user's images.

        Walks the attachments catalog and rewrites each image with metadata
        removed. The actual Pillow-based EXIF strip lands in Lauf 2; for now
        the bytes are rewritten unchanged so the pipeline (lookup → read →
        write-back) is exercised end-to-end.
        """
        if self._attachment_repo is None:
            return 0
        categories = _scope_to_categories(scope)
        attachments = await asyncio.to_thread(self._attachment_repo.find_by_user, tenant_key, user_key, categories)
        rewritten = 0
        for att in attachments:
            if not (att.mime_type or "").startswith("image/"):
                continue
            path = self._path_for(att.storage_key)
            if not await asyncio.to_thread(path.exists):
                continue
            data = await asyncio.to_thread(self._read_sync, path)
            # TODO(Lauf 2): replace with Pillow EXIF/GPS strip (NFR-013 §4.2).
            stripped = data
            await asyncio.to_thread(self._write_sync, path, stripped, att.mime_type, {})
            rewritten += 1
        logger.info(
            "storage_strip_exif_for_user",
            backend=BACKEND_KEY,
            tenant_key=tenant_key,
            user_key=user_key,
            scope=scope,
            rewritten=rewritten,
        )
        return rewritten

    # --- Token signing / verification --------------------------------

    def _make_token(self, payload: dict[str, Any]) -> str:
        body = base64.urlsafe_b64encode(json.dumps(payload, sort_keys=True).encode("utf-8")).rstrip(b"=")
        sig = hmac.new(self._signing_secret, body, hashlib.sha256).digest()
        sig_b64 = base64.urlsafe_b64encode(sig).rstrip(b"=")
        return f"{body.decode('ascii')}.{sig_b64.decode('ascii')}"

    def verify_token(self, token: str) -> dict[str, Any] | None:
        """Verify an HMAC token and return its payload, or ``None`` if invalid/expired.

        Used by the API layer (Lauf 2) to redeem a ``presign_*`` URL. Checks
        the signature in constant time and enforces the embedded expiry.
        """
        return verify_token(token, self._signing_secret)


def _scope_to_categories(scope: str):  # type: ignore[no-untyped-def]
    """Map a REQ-025 erasure scope string to attachment categories.

    ``"all"`` (or empty) means every category. Otherwise the scope is treated
    as a comma-separated list of ``AttachmentCategory`` values; unknown values
    are ignored.
    """
    from app.common.enums import AttachmentCategory

    if not scope or scope == "all":
        return None
    categories = []
    for raw in scope.split(","):
        value = raw.strip()
        try:
            categories.append(AttachmentCategory(value))
        except ValueError:
            continue
    return categories or None


def verify_token(token: str, signing_secret: bytes | str) -> dict[str, Any] | None:
    """Stateless verification of a local-fs signed token (module-level helper).

    Returns the decoded payload dict when the signature is valid and the token
    has not expired; otherwise ``None``. Exposed at module level so Lauf 2 / the
    API layer can verify without instantiating the adapter.
    """
    secret = signing_secret.encode("utf-8") if isinstance(signing_secret, str) else signing_secret
    try:
        body_str, sig_str = token.split(".", 1)
    except ValueError:
        return None
    body = body_str.encode("ascii")
    expected = hmac.new(secret, body, hashlib.sha256).digest()
    try:
        provided = base64.urlsafe_b64decode(sig_str + "=" * (-len(sig_str) % 4))
    except ValueError, TypeError:
        return None
    if not hmac.compare_digest(expected, provided):
        return None
    try:
        payload_bytes = base64.urlsafe_b64decode(body_str + "=" * (-len(body_str) % 4))
        payload = json.loads(payload_bytes.decode("utf-8"))
    except ValueError, TypeError, json.JSONDecodeError:
        return None
    exp = payload.get("exp")
    if not isinstance(exp, int) or exp < int(time.time()):
        return None
    return payload
