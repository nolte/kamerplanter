"""#1393 — the orphan sweep ships disabled, and that is a decision, not an accident.

`cleanup_orphaned_task_photos` **deletes** attachments. Four review rounds on #1424
each found a way it destroyed a photo something still referenced, and every one was
a ``photo_refs`` spelling the resolver did not know — most sharply
``/attachments/{ulid}/thumbnails/{size}``, which `_photo_response` builds and hands
to every client.

The resolver now protects any photo whose key is *mentioned* by any reference, which
closes the class rather than its fourth instance. The operator decision was still to
ship it off: a background job that deletes data, over a reference history spanning
every client version and a migration nobody schedules, does not go live in its first
release. Nothing else in #1393 depends on it — the delete route, the task-deletion
cleanup and the staged/persisted split all work with the sweep off.

This file is why that decision cannot be undone by a one-character edit. A default
flipped to a positive number arms a destructive nightly job across every
installation that has not set the variable, and the diff line that does it looks
like a harmless tuning change.

Asserted on the shipped default, not on the *behaviour* of a disabled sweep — that
has its own coverage. What is pinned here is which value an installation gets when
it says nothing.
"""

from __future__ import annotations

from app.config.settings import Settings


def test_the_sweep_is_off_unless_an_operator_switches_it_on():
    assert Settings().storage_task_photo_orphan_hours == 0, (
        "STORAGE_TASK_PHOTO_ORPHAN_HOURS no longer defaults to 0, which arms a nightly "
        "job that deletes attachments on every installation that has not set it. If that "
        "is intended, say so in the issue and change this test with the reasoning (#1393)."
    )


def test_a_positive_value_is_still_accepted():
    """The control: pinning the default must not turn the setting into a constant.

    An operator who has run the sweep and trusts it sets hours, and that has to keep
    working — otherwise this test would have quietly removed the feature instead of
    deferring it.
    """
    assert Settings(storage_task_photo_orphan_hours=48).storage_task_photo_orphan_hours == 48
