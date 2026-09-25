#!/usr/bin/env python3
"""Two members upload the same photo into a shared tenant; one of them is the subject (#1770).

Runs **inside the backend container** of the reach stack (``stack.py
seed-shared-file`` ships it there) and prints one JSON record to stdout — which
records and objects exist, so the host-side observation knows where to look. It
is an environment step, not an observation: it asserts nothing about reach.

Until #1770 the upload's sha256 deduplication handed the second uploader of
identical bytes the *first* uploader's record, so the subject's erasure applied
the subject's storage rule to bytes another member still held. This seed builds
exactly that situation, through the production pipeline
(``AttachmentService.upload`` from the DI providers):

* an **organisation** tenant (not the subject's personal one, whose own erasure
  is a separate matter) with the subject and a co-holder as growers;
* the subject uploads photo *S* as a ``pest_reference`` — the hard-deleted
  category, so a shared object is at the most risk — and the co-holder uploads
  the same bytes, same category, afterwards;
* the subject uploads a second photo *C* alone, the control: an erasure that
  kept *S* for the co-holder must still delete what nothing else holds.

The co-holder is only a key in the membership and the upload; no account is
created, because nothing in this probe signs in as them.
"""

from __future__ import annotations

import argparse
import asyncio
import contextlib
import io
import json
import os
import sys
from typing import Any

from PIL import Image

MIME_TYPE = "image/jpeg"


class SeedError(RuntimeError):
    """The shared file cannot be seeded as required; the environment fails."""


def seed_jpeg(shade: int) -> bytes:
    """A small JPEG, distinct per *shade* (pure)."""
    buffer = io.BytesIO()
    Image.new("RGB", (32, 32), ((shade * 53) % 256, (shade * 97 + 20) % 256, (shade * 13 + 70) % 256)).save(
        buffer, format="JPEG", quality=90
    )
    return buffer.getvalue()


def co_holder_key(subject: str) -> str:
    return f"{subject}-co-holder"


def shared_tenant_slug(subject: str) -> str:
    return f"reach-shared-{subject}"


async def seed(subject: str) -> dict[str, Any]:
    from app.common.dependencies import (
        get_attachment_repo,
        get_membership_repo,
        get_object_storage,
        get_tenant_repo,
    )
    from app.common.enums import AttachmentCategory, TenantRole, TenantType
    from app.config.settings import settings
    from app.domain.models.membership import Membership
    from app.domain.models.tenant import Tenant
    from app.domain.services.attachment_service import AttachmentService

    holder = co_holder_key(subject)
    tenant = get_tenant_repo().create(
        Tenant(
            name=f"Reach shared garden ({subject})",
            slug=shared_tenant_slug(subject),
            tenant_type=TenantType.ORGANIZATION,
            owner_user_key=holder,
            max_members=10,
        )
    )
    if tenant.key is None:
        raise SeedError("the shared tenant was created without a key")
    memberships = get_membership_repo()
    for user_key in (subject, holder):
        memberships.create(Membership(user_key=user_key, tenant_key=tenant.key, role=TenantRole.GROWER))

    service = AttachmentService(storage=get_object_storage(), attachment_repo=get_attachment_repo(), settings=settings)

    async def upload(user_key: str, data: bytes, name: str) -> Any:
        return await service.upload(
            tenant_key=tenant.key,
            user_key=user_key,
            data=data,
            mime_type=MIME_TYPE,
            original_filename=name,
            category=AttachmentCategory.PEST_REFERENCE,
        )

    shared = seed_jpeg(7)
    subject_record = await upload(subject, shared, "reach-shared-subject.jpg")
    holder_record = await upload(holder, shared, "reach-shared-holder.jpg")
    control = await upload(subject, seed_jpeg(11), "reach-control.jpg")
    for label, record in (("subject", subject_record), ("co-holder", holder_record), ("control", control)):
        if record.key is None:
            raise SeedError(f"the {label} upload returned no attachment key")
    return {
        "subject": subject,
        "co_holder": holder,
        "tenant_key": tenant.key,
        "shared": {
            "storage_key": holder_record.storage_key,
            "subject_attachment_key": subject_record.key,
            "holder_attachment_key": holder_record.key,
        },
        "control": {"storage_key": control.storage_key, "attachment_key": control.key},
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--subject", required=True)
    args = parser.parse_args(argv)
    # The backend logs to stdout, which is this script's record channel (as in
    # ``seed_stored_files.py``): route both the object and fd 1 to stderr while
    # the product code runs, and write the record afterwards.
    sys.stdout.flush()
    record_fd = os.dup(1)
    os.dup2(2, 1)
    try:
        with contextlib.redirect_stdout(sys.stderr):
            record = asyncio.run(seed(args.subject))
    except SeedError as exc:
        print(f"seed shared file: {exc}", file=sys.stderr)
        return 1
    finally:
        sys.stdout.flush()
        os.dup2(record_fd, 1)
        os.close(record_fd)
    json.dump(record, sys.stdout, sort_keys=True)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
