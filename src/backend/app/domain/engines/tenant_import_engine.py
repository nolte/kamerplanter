"""Key remapping of a tenant import (REQ-056 §8.4, #2138).

Pure logic, no I/O. An archive carries its source installation's keys. ArangoDB
generates ``_key`` per collection and it is unique across tenants, so a document
written back with its old key would collide with — or overwrite — a row of
another tenant in a shared database. The import therefore gives **every**
document a new key and rewrites every reference through one mapping table per
collection; which fields are references is declared once, in
:class:`~app.domain.engines.tenant_export_engine.TenantExportEngine`.

Rules per reference kind (``TenantReference.kind``):

* ``tenant`` — the source tenant's key becomes the new tenant's; any other tenant
  key refuses the archive (it names a tenant the archive does not own). Which
  rows *must* carry it is the tenant-erasure inventory's: a collection selected by
  ``tenant_key`` alone needs the source key on every row — an empty or absent one
  would be written as a global catalogue row every tenant reads, so it refuses
  the archive; a collection also selected through a parent (``locations`` via
  their site) needs the source key **or** a parent of the archive, and a supplied
  key is replaced by the new tenant's (SEC-001 of the PR #2267 review).
* ``internal`` — a row of the archive → its new key. A key the archive does not
  hold: a global catalogue row of the target when a target collection is a
  (hybrid) catalogue — collected first and checked by the service
  (``IMPORT_MISSING_CATALOG_ENTRIES``); otherwise a dangling pointer of the
  source, which is **cleared**, never kept (a kept key could name a row of
  another tenant in the target database). A reference declared as
  *provenance* (``TenantReference.provenance``: a bed's template and substrate,
  #2528) is resolved the same way — against the archive and the target's
  catalogue, so an existing system row is kept — but a key found in neither is
  cleared and counted instead of refusing the archive: it is collected by
  :meth:`TenantImportEngine.optional_catalogue_requirements`, not by
  :meth:`TenantImportEngine.catalogue_requirements`.
* ``global`` — kept; collected for the catalogue check.
* ``account`` — an account the admin mapped → that account; anything else
  becomes the pseudonym ``_anonymized`` (§8.4 step 4). A pseudonym or an erasure
  tombstone stays as it is.
* ``storage`` / ``attachment`` — ``t/<source>/…`` becomes ``t/<new>/…``; any other
  object key, or one with a ``..`` segment, refuses the archive (SEC-004); an
  attachment id is mapped like an internal reference.
* ``polymorphic`` — the sibling discriminator names the collection, then as
  ``internal``; an unknown discriminator clears the reference.

Edges (SEC-002): only an edge collection of :attr:`TenantExportEngine.IMPORTABLE_EDGES`
is written, and only an edge with at least one end in the archive (or on the tenant
itself) — an edge between two global catalogue rows would change what every tenant
reads. A ``tenant_key`` on an edge becomes the new tenant's.

A ``*_key`` path no declaration covers refuses the archive
(``IMPORT_UNDECLARED_REFERENCE``): writing it unchanged is the one thing the
import must never do. :meth:`TenantImportEngine.validate_documents` applies every
rule to every row and edge **before** anything is written.
"""

from __future__ import annotations

import copy
import uuid
from collections.abc import Callable
from typing import Any

from app.domain.engines.tenant_erasure_engine import TenantErasureEngine
from app.domain.engines.tenant_export_engine import (
    ANONYMIZED_ACCOUNT,
    TenantArchiveError,
    TenantExportEngine,
    TenantReference,
    archive_document,
    is_tombstone_or_pseudonym,
)
from app.domain.models.tenant_erasure import TenantErasureEntry
from app.domain.models.tenant_export import TenantArchive

#: Sentinel for "drop this value" while rewriting.
_CLEARED = object()


def new_document_key() -> str:
    """A fresh document key: random, so it can never equal a key the source or the target already uses."""
    return uuid.uuid4().hex


class TenantImportEngine:
    """Plans and applies the key mapping of one import."""

    def __init__(
        self,
        archive: TenantArchive,
        *,
        target_tenant_key: str,
        member_accounts: dict[str, str],
        key_factory: Callable[[], str] = new_document_key,
    ) -> None:
        self._archive = archive
        self._source = archive.source_tenant_key
        self._target = target_tenant_key
        self._members: dict[str, str] = dict(member_accounts)
        self._exported = set(TenantExportEngine.exported_collections())
        self._entries: dict[str, TenantErasureEntry] = {
            entry.collection: entry for entry in TenantErasureEngine.INVENTORY
        }
        self._catalogues = TenantExportEngine.global_catalogues()
        self._hybrid = TenantExportEngine.HYBRID_CATALOGUES
        self.mapping: dict[str, dict[str, str]] = {}
        self.nulled_references = 0
        for collection, documents in archive.collections.items():
            table: dict[str, str] = {}
            for row in documents:
                document: dict[str, Any] = row
                old = document.get("_key")
                if isinstance(old, str) and old:
                    table[old] = key_factory()
            self.mapping[collection] = table

    # ── validation (before anything is written) ─────────────────────────

    @staticmethod
    def validate_structure(archive: TenantArchive) -> None:
        """Refuse an archive whose collections, keys or reference paths the import cannot place."""
        exported = set(TenantExportEngine.exported_collections())
        unknown = sorted(set(archive.collections) - exported)
        if unknown:
            raise TenantArchiveError(
                "IMPORT_FORMAT_UNSUPPORTED",
                "the archive carries collections a tenant import does not write",
                entries=unknown,
            )
        undeclared: set[str] = set()
        for collection, documents in archive.collections.items():
            seen: set[str] = set()
            for row in documents:
                document: dict[str, Any] = row
                key = document.get("_key")
                if not isinstance(key, str) or not key or key in seen:
                    raise TenantArchiveError(
                        "IMPORT_FORMAT_UNSUPPORTED", f"{collection}: a document without a unique _key"
                    )
                seen.add(key)
                undeclared.update(
                    f"{collection}.{path}"
                    for path in TenantExportEngine.undeclared_reference_paths(collection, document)
                )
        foreign_edges = sorted(set(archive.edges) - TenantExportEngine.IMPORTABLE_EDGES)
        if foreign_edges:
            raise TenantArchiveError(
                "IMPORT_FORMAT_UNSUPPORTED",
                "the archive carries edge collections a tenant import does not write",
                entries=foreign_edges,
            )
        for name, edges in archive.edges.items():
            for row in edges:
                edge: dict[str, Any] = row
                if not isinstance(edge.get("_from"), str) or not isinstance(edge.get("_to"), str):
                    raise TenantArchiveError("IMPORT_FORMAT_UNSUPPORTED", f"{name}: an edge without _from/_to")
                fields: list[str] = list(edge)
                undeclared.update(
                    f"{name}.{field}"
                    for field in fields
                    if field[:1] != "_" and TenantExportEngine.looks_like_reference(field) and field != "tenant_key"
                )
        if undeclared:
            raise TenantArchiveError(
                "IMPORT_UNDECLARED_REFERENCE",
                "the archive carries reference fields this installation does not know how to rewrite",
                entries=sorted(undeclared),
            )

    def validate_documents(self) -> None:
        """Apply every ownership and rewrite rule to every row and edge, writing nothing (SEC-001/-002/-004).

        Run before the new tenant is founded: an archive that would fail half-way is
        refused as a whole. Catalogue rows count as absent here — this pass checks what
        the archive *claims*, the catalogue check is :meth:`catalogue_requirements`.
        """
        for collection, documents in self._archive.collections.items():
            for row in documents:
                document: dict[str, Any] = row
                self._check_ownership(collection, document)
                self.remap_document(collection, document, existing_global=set())
        for edges in self._archive.edges.values():
            for row in edges:
                edge: dict[str, Any] = row
                self.remap_edge(edge, existing_global=set(), dry_run=True)
        self.nulled_references = 0

    def _check_ownership(self, collection: str, document: dict[str, Any]) -> None:
        """The row belongs to the source tenant by its own key or through a parent row of the archive."""
        entry = self._entries.get(collection)
        if entry is None:
            raise TenantArchiveError("IMPORT_FORMAT_UNSUPPORTED", f"{collection}: not a collection of a tenant")
        claimed = document.get(entry.tenant_field)
        if claimed == self._source:
            return
        if claimed not in (None, ""):
            raise TenantArchiveError("IMPORT_FORMAT_UNSUPPORTED", "the archive carries a row of another tenant")
        for parent in entry.parents:
            value = document.get(parent.field)
            where: dict[str, Any] = dict(parent.where)
            if (
                isinstance(value, str)
                and value in self._table(parent.collection)
                and all(document.get(name) == expected for name, expected in where.items())
            ):
                return
        raise TenantArchiveError(
            "IMPORT_FORMAT_UNSUPPORTED",
            f"{collection}: a row that belongs to no tenant of the archive (no tenant key, no parent row)",
            entries=[f"{collection}/{document.get('_key')}"],
        )

    def catalogue_requirements(self) -> dict[str, set[str]]:
        """Every global catalogue row the archive points at and cannot do without: ``collection -> keys``.

        The store checks these; a missing one refuses the archive (``IMPORT_MISSING_CATALOG_ENTRIES``).
        """
        return self._catalogue_needs()[0]

    def optional_catalogue_requirements(self) -> dict[str, set[str]]:
        """The catalogue rows only *provenance* references point at: resolved like the others, never refusing.

        The store must still resolve them - an existing (system) row goes into ``existing_global`` and the key is
        kept; a missing one is cleared by :meth:`remap_document` and counted in ``nulled_references`` (#2528).
        """
        return self._catalogue_needs()[1]

    def _catalogue_needs(self) -> tuple[dict[str, set[str]], dict[str, set[str]]]:
        """``(refusing, optional)`` catalogue keys of every row and edge of the archive."""
        needed: dict[str, set[str]] = {}
        optional: dict[str, set[str]] = {}
        for collection, documents in self._archive.collections.items():
            for row in documents:
                document: dict[str, Any] = row
                for reference, value in self._references_in(collection, document):
                    self._require_catalogue(optional if reference.provenance else needed, reference, value, document)
        for edges in self._archive.edges.values():
            for row in edges:
                edge: dict[str, Any] = row
                for end in ("_from", "_to"):
                    document_id: str = str(edge[end])
                    collection, _, key = document_id.partition("/")
                    if collection in self._catalogues or (
                        collection in self._hybrid and key not in self._table(collection)
                    ):
                        needed.setdefault(collection, set()).add(key)
        return needed, optional

    def _table(self, collection: str) -> dict[str, str]:
        return self.mapping.get(collection, {})

    def _require_catalogue(
        self, needed: dict[str, set[str]], reference: TenantReference, value: str, document: dict[str, Any]
    ) -> None:
        targets = self._targets_of(reference, document)
        if reference.kind == "global":
            needed.setdefault("|".join(targets), set()).add(value)
        elif reference.kind == "internal" and not any(value in self._table(t) for t in targets):
            capable = tuple(t for t in targets if t in self._hybrid or t in self._catalogues)
            if capable:
                needed.setdefault("|".join(capable), set()).add(value)

    # ── rewriting ──────────────────────────────────────────────────────

    def remap_document(self, collection: str, document: dict[str, Any], *, existing_global: set[str]) -> dict[str, Any]:
        """The document as the target stores it: new ``_key``, every declared reference rewritten.

        ``existing_global`` holds ``"<collection>/<key>"`` of every catalogue row the
        target has (the service resolved :meth:`catalogue_requirements`).
        """
        old_key = str(document["_key"])
        # A deep copy: ``archive_document`` copies the top level only, and the rewrite below assigns into nested
        # objects (``plan.underlay.attachment_key``, ``fertilizers_used.*``). The validation pass runs on the same
        # archive rows as the write pass, so a nested key rewritten in place was a *new* key the second pass could
        # no longer map - and cleared (found with the site plan's underlay, REQ-053 WP 7.14).
        rewritten = copy.deepcopy(archive_document(document, collection=collection))
        rewritten["_key"] = self.mapping[collection][old_key]
        references = TenantExportEngine.references_of(collection)
        for path, reference in references.items():
            dotted: str = path
            segments: list[str] = dotted.split(".")
            self._rewrite_path(rewritten, segments, reference, rewritten, existing_global)
        if collection == "sites":
            _drop_unresolved_underlay(rewritten)
        entry = self._entries.get(collection)
        if entry is not None and entry.tenant_field in rewritten:
            # SEC-001 — whatever the archive said, a row the import writes is the new tenant's.
            rewritten[entry.tenant_field] = self._target
        elif entry is not None and not entry.parents:
            rewritten[entry.tenant_field] = self._target
        return rewritten

    def remap_edge(
        self, edge: dict[str, Any], *, existing_global: set[str], dry_run: bool = False
    ) -> dict[str, Any] | None:
        """The edge with both ends rewritten, or ``None`` when an end has no place in the target.

        Refuses (SEC-002) an edge none of whose ends is a row of the archive or the tenant itself:
        such an edge relates rows the tenant does not own.
        """
        if not any(self._owned_end(str(edge.get(end, ""))) for end in ("_from", "_to")):
            raise TenantArchiveError(
                "IMPORT_FORMAT_UNSUPPORTED",
                "the archive carries an edge between rows that are not the tenant's",
                entries=[f"{edge.get('_from')} -> {edge.get('_to')}"],
            )
        if dry_run:
            if "tenant_key" in edge:
                self._rewrite_tenant(edge["tenant_key"])
            return None
        ends: dict[str, str] = {}
        for end in ("_from", "_to"):
            resolved = self._resolve_id(str(edge[end]), existing_global)
            if resolved is None:
                return None
            ends[end] = resolved
        rewritten = {name: value for name, value in edge.items() if name not in ("_id", "_rev", "_key", "_from", "_to")}
        rewritten.update(ends)
        if "tenant_key" in rewritten:
            self._rewrite_tenant(rewritten["tenant_key"])
            rewritten["tenant_key"] = self._target
        return rewritten

    def _owned_end(self, document_id: str) -> bool:
        collection, _, key = document_id.partition("/")
        if collection == "tenants":
            return key == self._source
        return key in self._table(collection)

    def rewrite_storage_key(self, value: str) -> str:
        """``t/<source>/…`` → ``t/<new>/…``; anything else (or a ``..`` / empty segment) refuses (SEC-004)."""
        prefix = f"t/{self._source}/"
        tail = value[len(prefix) :] if value.startswith(prefix) else ""
        if not tail or any(segment in ("", ".", "..") for segment in tail.split("/")):
            raise TenantArchiveError("IMPORT_FORMAT_UNSUPPORTED", "an object key outside the source tenant's namespace")
        return f"t/{self._target}/{tail}"

    # ── internals ──────────────────────────────────────────────────────

    def _targets_of(self, reference: TenantReference, document: dict[str, Any]) -> tuple[str, ...]:
        if reference.kind == "polymorphic":
            target = reference.by_value.get(str(document.get(reference.discriminator or "")))
            return (target,) if target else ()
        return reference.targets

    def _references_in(self, collection: str, document: dict[str, Any]) -> list[tuple[TenantReference, str]]:
        """Every non-empty string value at a declared reference path of *document*."""
        found: list[tuple[TenantReference, str]] = []
        for path, reference in TenantExportEngine.references_of(collection).items():
            dotted: str = path
            for value in _values_at(document, dotted.split(".")):
                if isinstance(value, str) and value:
                    found += [(reference, value)]
        return found

    def _rewrite_path(
        self,
        node: Any,
        segments: list[str],
        reference: TenantReference,
        document: dict[str, Any],
        existing_global: set[str],
    ) -> None:
        if isinstance(node, list):
            for item in node:
                self._rewrite_path(item, segments, reference, document, existing_global)
            return
        if not isinstance(node, dict) or segments[0] not in node:
            return
        head, rest = segments[0], segments[1:]
        if rest:
            self._rewrite_path(node[head], rest, reference, document, existing_global)
            return
        value = node[head]
        if isinstance(value, list):
            kept = [self._rewrite_value(item, reference, document, existing_global) for item in value]
            node[head] = [item for item in kept if item is not _CLEARED]
        else:
            result = self._rewrite_value(value, reference, document, existing_global)
            node[head] = None if result is _CLEARED else result

    def _rewrite_value(
        self, value: Any, reference: TenantReference, document: dict[str, Any], existing_global: set[str]
    ) -> Any:
        if not isinstance(value, str) or not value:
            return value
        kind = reference.kind
        if kind == "opaque":
            return value
        if kind == "tenant":
            return self._rewrite_tenant(value)
        if kind == "account":
            if is_tombstone_or_pseudonym(value):
                return value
            return self._members.get(value, ANONYMIZED_ACCOUNT)
        text: str = value
        if kind == "storage":
            return self.rewrite_storage_key(text)
        if kind == "attachment":
            if "/" in text:
                return self.rewrite_storage_key(value)
            return self._internal(value, ("attachments",), existing_global)
        if kind == "global":
            return value
        targets = self._targets_of(reference, document)
        if not targets:
            self.nulled_references += 1
            return _CLEARED
        return self._internal(value, targets, existing_global)

    def _internal(self, value: str, targets: tuple[str, ...], existing_global: set[str]) -> Any:
        for target in targets:
            mapped = self.mapping.get(target, {}).get(value)
            if mapped is not None:
                return mapped
        if any(f"{target}/{value}" in existing_global for target in targets):
            return value
        self.nulled_references += 1
        return _CLEARED

    def _rewrite_tenant(self, value: Any) -> Any:
        if value in (None, ""):
            return value
        if value == self._source:
            return self._target
        raise TenantArchiveError("IMPORT_FORMAT_UNSUPPORTED", "the archive carries a row of another tenant")

    def _resolve_id(self, document_id: str, existing_global: set[str]) -> str | None:
        collection, _, key = document_id.partition("/")
        if collection == "tenants":
            return f"tenants/{self._target}" if key == self._source else None
        mapped = self.mapping.get(collection, {}).get(key)
        if mapped is not None:
            return f"{collection}/{mapped}"
        if document_id in existing_global:
            return document_id
        return None


def _drop_unresolved_underlay(site: dict[str, Any]) -> None:
    """A site plan whose underlay attachment is not in the archive keeps no underlay (REQ-053 GP-FR-033).

    The reference rewrite clears an attachment key it cannot resolve to ``None``, but the underlay's other fields
    (the calibration, the placement) would stay: ``SiteUnderlay.attachment_key`` is a required string, so such a
    plan could not be read and every read of the tenant's sites would fail. The picture is presentation, so the
    honest import is a plan without one.
    """
    plan = site.get("plan")
    if not isinstance(plan, dict):
        return
    underlay = plan.get("underlay")
    if isinstance(underlay, dict) and not underlay.get("attachment_key"):
        del plan["underlay"]


def _values_at(node: Any, segments: list[str]) -> list[Any]:
    """Every value at *segments* in *node*, walking lists transparently (lists at the leaf are flattened)."""
    if isinstance(node, list):
        return [value for item in node for value in _values_at(item, segments)]
    if not isinstance(node, dict) or segments[0] not in node:
        return []
    value = node[segments[0]]
    if len(segments) > 1:
        return _values_at(value, segments[1:])
    return list(value) if isinstance(value, list) else [value]
