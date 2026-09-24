#!/usr/bin/env python3
"""Seed one data subject into every collection the privacy inventories declare (#1680).

Runs **inside the backend container** of the reach stack (``stack.py seed``
ships it there together with ``check_privacy_inventory.py``) and prints one JSON
record to stdout: the subject's credentials and every row it wrote, so the act
and observation helpers on the host know what exists. It is an environment
step, not an observation: it asserts nothing about reach.

What gets a row
---------------
One row of the subject per declared *(collection, user field)*, taken from the
two declared inventories the executing paths read:

* every ``document`` / ``edge`` / ``user`` step of
  ``ErasureEngine.build_erasure_plan`` (a ``via`` step references its parent's
  row, an edge points at the subject's own row on its other side when one was
  seeded, so a traversal from the subject can actually reach it);
* every ``ANONYMIZE_COLLECTIONS`` and ``PSEUDONYMIZE_AUDIT_COLLECTIONS`` rule;
* every source of ``DataExportEngine.USER_DATA_MANIFEST`` not already covered.

The inventories supply only *where* to put the subject; the **shape** of each
row comes from the collection's domain model. That split is deliberate: a seed
that wrote whatever field an inventory names would make a misspelt field exist
in the data and certify the very walk that could never find a real row (the
``assigned_to`` defect of #1645). So a declared field that is not a field of the
collection's model stops the seed with an error — the environment fails, and the
runner reports the probe not probed with that reason instead of a false reach.

Every row is a model-valid document: required fields get a type-correct value,
unconstrained plain-``str`` fields carry a marker ``reach-seed:<row key>:<field>``
(``reach-seed.<row key>.<field>@kamerplanter.example`` in an e-mail field) the
export observer recognises the row by, and a few states are pinned so the
seeded rows do not block the acts (an *open* export or erasure request of the
subject would make the API refuse a new one). A collection no repository binds
to a model gets a minimal document and is listed under ``unmodelled``.

Only the subject's key, e-mail and display name name the subject. Row keys are
random, so a row that no longer references the subject contains no trace of it.
"""

from __future__ import annotations

import argparse
import importlib
import inspect
import json
import pkgutil
import secrets
import sys
import types
import typing
from datetime import UTC, date, datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

import check_privacy_inventory as inventory_check  # noqa: E402 — shipped beside this file
from app.config.settings import settings  # noqa: E402
from app.data_access.arango import collections as col  # noqa: E402
from app.domain.engines.data_export_engine import DataExportEngine  # noqa: E402
from app.domain.engines.erasure_engine import ErasureEngine  # noqa: E402
from app.domain.engines.password_engine import PasswordEngine  # noqa: E402
from arango import ArangoClient  # noqa: E402
from pydantic import BaseModel, EmailStr, ValidationError  # noqa: E402

APP_ROOT = Path("/app/app")
MARKER_PREFIX = "reach-seed"
FIXED_TIMESTAMP = "2026-09-01T00:00:00+00:00"
FIXED_DATE = "2026-09-01"

#: States that keep the seeded rows from blocking the acts, and values a model-level
#: validator demands that a per-field default cannot supply. The API refuses a new
#: export while one is ``pending``/``processing`` and a new erasure while one is
#: ``scheduled``/``in_progress``/``partially_completed``; a model default would
#: be exactly such a state.
STATE_OVERRIDES: dict[str, dict[str, Any]] = {
    "data_export_requests": {"status": "expired"},
    "erasure_requests": {"status": "completed"},
    "email_change_requests": {"status": "expired"},
    # Model validator: an override expires after it started.
    "manual_overrides": {"expires_at": "2026-09-02T00:00:00+00:00"},
}


#: Content that makes a row recognisable when the fields the export discloses hold
#: no free text: ``NotificationPreferences`` is nested settings only (its channel
#: ``config`` is the schemaless place a marker cannot break), and a past privacy
#: request is a status plus timestamps.
def _unique_timestamp(key: str) -> str:
    """A timestamp no other row carries, derived from the random row key."""
    seconds = int(key[2:10], 16) % (365 * 24 * 3600)
    return (datetime(2001, 1, 1, tzinfo=UTC) + timedelta(seconds=seconds)).isoformat()


DISTINCT_CONTENT: dict[str, Any] = {
    "notification_preferences": lambda key: {
        "channels": {"reach": {"enabled": False, "priority": 0, "config": {"seed": f"{MARKER_PREFIX}:{key}:config"}}}
    },
    # The export discloses only status and timestamps of the subject's past
    # requests; a unique request time is what tells the seeded one apart.
    "data_export_requests": lambda key: {"requested_at": _unique_timestamp(key)},
    "erasure_requests": lambda key: {"requested_at": _unique_timestamp(key)},
}

#: Filter fields that name an edge endpoint; a manifest source filtered on one is
#: an edge collection whose rows are the data (``user_favorites``, #1719).
EDGE_ENDPOINTS = frozenset({"_from", "_to"})

#: Fields never filled with a marker: credentials and the fields the seed sets.
_NO_MARKER = ("token", "password", "hash", "secret")


def _strings(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, dict):
        return [text for item in value.values() for text in _strings(item)]
    if isinstance(value, list):
        return [text for item in value for text in _strings(item)]
    return []


class SeedError(RuntimeError):
    """The declared inventory cannot be seeded as declared; the environment fails."""


# ── Collection -> domain model ──────────────────────────────────────────────


def _model_classes() -> dict[str, list[type[BaseModel]]]:
    """Model name -> every class of that name (two modules both define ``QualityAssessment``)."""
    import app.domain.models as models_package

    classes: dict[str, list[type[BaseModel]]] = {}
    for info in pkgutil.iter_modules(models_package.__path__):
        module = importlib.import_module(f"app.domain.models.{info.name}")
        for name, obj in vars(module).items():
            if inspect.isclass(obj) and issubclass(obj, BaseModel) and obj.__module__ == module.__name__:
                classes.setdefault(name, []).append(obj)
    return classes


def collection_models() -> dict[str, list[type[BaseModel]]]:
    """Collection -> the models a repository binds to it (the R6 placement of the inventory guard)."""
    constants = inventory_check.collection_constants(APP_ROOT)
    bindings = inventory_check.repository_bindings(APP_ROOT, constants)
    for model_name, collection in inventory_check.MODEL_COLLECTIONS_BY_HAND.items():
        bindings.setdefault(model_name, set()).add(collection)
    classes = _model_classes()
    placed: dict[str, list[type[BaseModel]]] = {}
    for model_name, collections in sorted(bindings.items()):
        for model in classes.get(model_name, []):
            for collection in collections:
                placed.setdefault(collection, []).append(model)
    return placed


def _field_names(model: type[BaseModel]) -> set[str]:
    names: set[str] = set()
    for name, field in model.model_fields.items():
        names.add(name)
        if field.alias:
            names.add(field.alias)
    return names


# ── Type-correct values for required fields ─────────────────────────────────


def _unwrap(annotation: Any) -> Any:
    while isinstance(annotation, typing.TypeAliasType):
        annotation = annotation.__value__
    if typing.get_origin(annotation) is typing.Annotated:
        return _unwrap(typing.get_args(annotation)[0])
    return annotation


def _value_for(annotation: Any, marker: str) -> Any:
    annotation = _unwrap(annotation)
    origin = typing.get_origin(annotation)
    if origin in (typing.Union, types.UnionType):
        options = [arg for arg in typing.get_args(annotation) if arg is not type(None)]
        return _value_for(options[0], marker) if options else None
    if origin is typing.Literal:
        return typing.get_args(annotation)[0]
    if origin in (list, set, frozenset, tuple):
        return []
    if origin is dict:
        return {}
    if annotation is str:
        return marker
    if annotation is EmailStr:
        # An address cannot hold the colon form; the observers read both forms.
        return f"{marker.replace(':', '.')}@kamerplanter.example"
    if annotation is bool:
        return False
    if annotation in (int, float):
        return 1
    if annotation is datetime:
        return FIXED_TIMESTAMP
    if annotation is date:
        return FIXED_DATE
    if inspect.isclass(annotation) and issubclass(annotation, Enum):
        return next(iter(annotation)).value
    if inspect.isclass(annotation) and issubclass(annotation, BaseModel):
        return _required_values(annotation, marker)
    if annotation in (list, dict):
        return annotation()
    return marker


def _required_values(model: type[BaseModel], marker: str) -> dict[str, Any]:
    values: dict[str, Any] = {}
    for name, field in model.model_fields.items():
        if field.is_required():
            values[field.alias or name] = _value_for(field.annotation, f"{marker}:{name}")
    return values


def _is_plain_str(field: Any) -> bool:
    annotation = _unwrap(field.annotation)
    if typing.get_origin(annotation) in (typing.Union, types.UnionType):
        options = [_unwrap(arg) for arg in typing.get_args(annotation) if arg is not type(None)]
    else:
        options = [annotation]
    return options == [str] and not field.metadata


# ── The seed ────────────────────────────────────────────────────────────────


class Seeder:
    def __init__(self, database: Any, subject: str) -> None:
        self.db = database
        self.subject = subject
        self.email = f"{subject}@kamerplanter.example"
        self.display_name = f"Reach Subject {subject}"
        self.password = secrets.token_urlsafe(18)
        self.models = collection_models()
        self.rows: list[dict[str, Any]] = []
        self.unmodelled: set[str] = set()
        self.unique_values: set[str] = set()
        self.covered: set[tuple[str, str, str]] = set()
        self.edge_definitions = {d["edge_collection"]: d for d in col.GRAPH_EDGE_DEFINITIONS}

    # -- plumbing

    @staticmethod
    def new_key() -> str:
        return f"rs{secrets.token_hex(8)}"

    def _ensure(self, name: str, *, edge: bool = False) -> None:
        if not self.db.has_collection(name):
            self.db.create_collection(name, edge=edge)

    def _insert(
        self, collection: str, doc: dict[str, Any], *, kind: str, role: str, edge: bool = False
    ) -> dict[str, Any]:
        self._ensure(collection, edge=edge)
        meta = self.db.collection(collection).insert(doc)
        markers = sorted({v for v in _strings(doc) if v.startswith((f"{MARKER_PREFIX}:", f"{MARKER_PREFIX}."))})
        row = {
            "id": meta["_id"],
            "key": meta["_key"],
            "rev": meta["_rev"],
            "collection": collection,
            "kind": kind,
            "role": role,
            "markers": markers,
        }
        if kind == "document":
            # An export projects a few fields; when none of them carries a marker
            # (a membership is keys, a role and flags) the observer recognises the
            # row by its content: a projection of this fingerprint that holds one
            # of the row's ``distinct`` values, which only this seed wrote.
            fingerprint = {name: value for name, value in doc.items() if not name.startswith("_")}
            row["fingerprint"] = fingerprint
            row["distinct"] = sorted(
                {*markers, *(v for v in fingerprint.values() if isinstance(v, str) and self._distinct(v))}
            )
        self.rows.append(row)
        return row

    def _distinct(self, value: str) -> bool:
        """A value only this seed wrote: the subject's tenant key, a subject reference, a unique timestamp."""
        return value == getattr(self, "tenant_key", None) or self.subject in value or value in self.unique_values

    def _model_for(self, collection: str, fields: list[str]) -> type[BaseModel] | None:
        candidates = self.models.get(collection, [])
        if not candidates:
            self.unmodelled.add(collection)
            return None
        for model in candidates:
            if set(fields) <= _field_names(model):
                return model
        names = ", ".join(model.__name__ for model in candidates)
        raise SeedError(
            f"declared field(s) {fields} of '{collection}' are not fields of its model ({names}); "
            "a seed that invented them would certify a walk no real row can satisfy"
        )

    def document(
        self, collection: str, overrides: dict[str, Any], *, role: str, key: str | None = None
    ) -> dict[str, Any]:
        """Insert one model-valid document of the subject with *overrides* applied."""
        key = key or self.new_key()
        declared = [name for name in overrides if not name.startswith("_")]
        model = self._model_for(collection, [name for name in declared if name != "tenant_key"])
        overrides = {**STATE_OVERRIDES.get(collection, {}), **overrides}
        if model is None:
            doc = {"_key": key, "reach_seed": f"{MARKER_PREFIX}:{key}:reach_seed", **overrides}
            return self._insert(collection, doc, kind="document", role=role)
        names = _field_names(model)
        if "tenant_key" in overrides and "tenant_key" not in names:
            overrides = {k: v for k, v in overrides.items() if k != "tenant_key"}
        doc: dict[str, Any] = _required_values(model, f"{MARKER_PREFIX}:{key}")
        optional_markers: set[str] = set()
        for name, field in model.model_fields.items():
            wire = field.alias or name
            if wire.startswith("_") or wire in overrides or not _is_plain_str(field):
                continue
            if inventory_check.USER_REFERENCE_FIELD.match(name) or any(part in name for part in _NO_MARKER):
                continue
            doc[wire] = f"{MARKER_PREFIX}:{key}:{wire}"
            if not field.is_required():
                optional_markers.add(wire)
        distinct = DISTINCT_CONTENT.get(collection, lambda _key: {})(key)
        doc.update(distinct)
        doc.update(overrides)
        instance = self._validate(model, collection, doc, optional_markers)
        stored = instance.model_dump(mode="json", by_alias=True)
        # In the stored (serialised) form: that is what an export discloses.
        self.unique_values |= {stored[name] for name in distinct if isinstance(stored.get(name), str)}
        stored.pop("_key", None)
        stored.update({name: value for name, value in overrides.items() if name.startswith("_")})
        stored["_key"] = key
        return self._insert(collection, stored, kind="document", role=role)

    @staticmethod
    def _validate(
        model: type[BaseModel], collection: str, doc: dict[str, Any], optional_markers: set[str]
    ) -> BaseModel:
        """Validate *doc*; an optional field whose validator refuses the marker falls back to its default.

        A field validator can demand a shape a marker does not have (a site-relative
        path, a slug). Such a field keeps the model's default; the row still
        carries the markers of its other fields. Anything else invalid stops the seed.
        """
        for _attempt in range(len(optional_markers) + 1):
            try:
                return model.model_validate(doc)
            except ValidationError as exc:
                refused = {str(error["loc"][0]) for error in exc.errors() if error["loc"]} & optional_markers
                if not refused:
                    raise SeedError(f"seeded '{collection}' row is not a valid {model.__name__}: {exc}") from exc
                for wire in refused:
                    doc.pop(wire, None)
                    optional_markers.discard(wire)
        raise SeedError(f"seeded '{collection}' row could not be made a valid {model.__name__}")

    def endpoint_edge(self, source: Any, users: str) -> dict[str, Any]:
        """Insert the subject's row of a manifest source whose rows are edges (#1719).

        Such a source (``user_favorites``) filters on an edge endpoint: the edge
        row itself is the disclosed data, ``users/<subject>`` on one side and the
        marked catalogue entry on the other. A document insert cannot hold it —
        ArangoDB refuses an edge without both endpoints — so the row is built
        here: the subject on the filtered side, a seeded row (or a named
        placeholder) of the far side's collections on the other, and a marker in
        every other field the source discloses. The row is recorded as a
        *document* row: it is the data, not a link to it, and the export
        observer recognises it by those markers.
        """
        field = source.filter_field
        definition = self.edge_definitions.get(source.collection)
        if definition is None:
            raise SeedError(f"manifest source '{source.collection}' filters on {field} but is not a graph edge")
        own_side = "from_vertex_collections" if field == "_from" else "to_vertex_collections"
        far_side = "to_vertex_collections" if field == "_from" else "from_vertex_collections"
        if users not in definition[own_side]:
            raise SeedError(f"manifest source '{source.collection}' cannot hold {users} on {field}")
        far = list(definition[far_side])
        target = next(
            (self.rows_of(name)[0]["id"] for name in far if self.rows_of(name)),
            f"{far[0]}/reach-target-{secrets.token_hex(4)}",
        )
        key = self.new_key()
        opposite = "_to" if field == "_from" else "_from"
        doc: dict[str, Any] = {"_key": key, field: f"{users}/{self.subject}", opposite: target}
        for name in source.fields:
            if name not in EDGE_ENDPOINTS:
                doc[name] = f"{MARKER_PREFIX}:{key}:{name}"
        return self._insert(
            source.collection, doc, kind="document", role=f"export:{source.collection}.{field}", edge=True
        )

    def rows_of(self, collection: str) -> list[dict[str, Any]]:
        return [row for row in self.rows if row["collection"] == collection and row["kind"] != "edge"]

    # -- the subject

    def seed(self) -> dict[str, Any]:
        plan = ErasureEngine().build_erasure_plan(self.subject)
        manifest = DataExportEngine().build_export_manifest(self.subject)
        user_steps = [step for step in plan.steps if step.kind == "user"]
        if len(user_steps) != 1:
            raise SeedError(f"the erasure plan declares {len(user_steps)} user steps; expected exactly one")
        users = user_steps[0].collection

        self.document(
            users,
            {
                "email": self.email,
                "display_name": self.display_name,
                "password_hash": PasswordEngine().hash_password(self.password),
                "email_verified": True,
                "is_active": True,
                "account_type": "human",
                "locale": "de",
                "timezone": "Europe/Berlin",
                "created_at": FIXED_TIMESTAMP,
            },
            role=f"step:{users}",
            key=self.subject,
        )
        self.covered.add((users, "_key", "{}"))

        # The subject's personal tenant carries the owner reference the tenants
        # rule declares, and every tenant-scoped row points at it.
        tenant_rules = [rule for rule in plan.anonymize if rule.collection == col.TENANTS]
        tenant_field = tenant_rules[0].user_field if tenant_rules else "owner_user_key"
        tenant = self.document(
            col.TENANTS,
            {
                tenant_field: self.subject,
                "name": f"{self.display_name}'s garden",
                "slug": f"{self.subject}-garden",
                "tenant_type": "personal",
            },
            role=f"rule:{col.TENANTS}.{tenant_field}",
        )
        self.tenant_key = tenant["key"]
        self.covered.add((col.TENANTS, tenant_field, "{}"))

        # Document steps, parents before the rows reached through them.
        documents = [step for step in plan.steps if step.kind == "document"]
        pending = list(documents)
        while pending:
            ready = [s for s in pending if s.via is None or self.rows_of(s.via)]
            if not ready:
                raise SeedError(f"document steps {[s.collection for s in pending]} have an unseedable via chain")
            for step in ready:
                pending.remove(step)
                reference = self.subject if step.via is None else self.rows_of(step.via)[0]["key"]
                self.document(
                    step.collection,
                    {step.user_field: reference, "tenant_key": self.tenant_key, **step.where},
                    role=f"step:{step.collection}",
                )
                self.covered.add((step.collection, step.user_field, json.dumps(step.where, sort_keys=True)))

        for rule in plan.anonymize:
            if (rule.collection, rule.user_field, "{}") in self.covered:
                continue
            overrides = {rule.user_field: self.subject, "tenant_key": self.tenant_key}
            overrides.update(dict.fromkeys(rule.clear_fields, self.display_name))
            self.document(rule.collection, overrides, role=f"rule:{rule.collection}.{rule.user_field}")
            self.covered.add((rule.collection, rule.user_field, "{}"))

        for audit in plan.pseudonymize_audit:
            if (audit.collection, audit.user_field, "{}") in self.covered:
                continue
            self.document(
                audit.collection,
                {audit.user_field: self.subject, "tenant_key": self.tenant_key},
                role=f"audit:{audit.collection}.{audit.user_field}",
            )
            self.covered.add((audit.collection, audit.user_field, "{}"))

        edge_targets: dict[str, str] = {}
        for source in manifest:
            if source.disclosure_gap is not None:
                continue
            if source.edge_collection:
                edge_targets[source.edge_collection] = source.collection
                if not self.rows_of(source.collection):
                    self.document(
                        source.collection, {"tenant_key": self.tenant_key}, role=f"export:{source.collection}"
                    )
                continue
            field = source.filter_field or ""
            if (source.collection, field, "{}") in self.covered:
                continue
            if field in EDGE_ENDPOINTS:
                self.endpoint_edge(source, users)
                self.covered.add((source.collection, field, "{}"))
                continue
            self.document(
                source.collection,
                {field: self.subject, "tenant_key": self.tenant_key},
                role=f"export:{source.collection}.{field}",
            )
            self.covered.add((source.collection, field, "{}"))

        subject_edges: dict[str, str] = {}
        for step in plan.steps:
            if step.kind != "edge":
                continue
            definition = self.edge_definitions.get(step.collection)
            if definition is None:
                raise SeedError(f"edge step '{step.collection}' is not in the named graph; cannot seed it")
            own_side = "from_vertex_collections" if step.user_field == "_from" else "to_vertex_collections"
            far_side = "to_vertex_collections" if step.user_field == "_from" else "from_vertex_collections"
            opposite = "_to" if step.user_field == "_from" else "_from"
            anchor_collection = step.via or users
            if anchor_collection not in definition[own_side]:
                raise SeedError(f"edge step '{step.collection}' cannot hold {anchor_collection} on {step.user_field}")
            anchor = f"{users}/{self.subject}" if step.via is None else self.rows_of(step.via)[0]["id"]
            wanted = edge_targets.get(step.collection)
            far_collections = [wanted] if wanted in definition[far_side] else list(definition[far_side])
            target = next(
                (self.rows_of(name)[0]["id"] for name in far_collections if self.rows_of(name)),
                f"{definition[far_side][0]}/reach-target-{secrets.token_hex(4)}",
            )
            edge = {"_key": self.new_key(), step.user_field: anchor, opposite: target}
            self._insert(step.collection, edge, kind="edge", role=f"step:{step.collection}", edge=True)
            if step.via is None and target in {row["id"] for row in self.rows}:
                # An edge from the subject to one of its own seeded rows: the
                # export observer lists it when that row reached the archive.
                subject_edges[step.collection] = target

        return {
            "subject": self.subject,
            "email": self.email,
            "display_name": self.display_name,
            "password": self.password,
            "tenant_key": self.tenant_key,
            "rows": self.rows,
            "subject_edges": subject_edges,
            "unmodelled": sorted(self.unmodelled),
        }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--subject", required=True)
    args = parser.parse_args(argv)

    client = ArangoClient(hosts=f"http://{settings.arangodb_host}:{settings.arangodb_port}")
    database = client.db(
        settings.arangodb_database,
        username=settings.arangodb_username,
        password=settings.arangodb_password,
    )
    if database.collection("users").has(args.subject):
        print(f"seed: subject '{args.subject}' already exists; tear the stack down first", file=sys.stderr)
        return 1
    try:
        record = Seeder(database, args.subject).seed()
    except SeedError as exc:
        print(f"seed: {exc}", file=sys.stderr)
        return 1
    json.dump(record, sys.stdout, sort_keys=True)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
