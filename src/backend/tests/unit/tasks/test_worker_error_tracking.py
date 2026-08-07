"""The worker labels *its own* process, and importing it labels nothing (#991).

The defect this pins is not a crash. ``app/tasks/__init__.py`` used to call
``init_error_tracking(component="worker")`` at **import** time, and the API
imports ``app.tasks`` — every Celery dispatch site does, that is how a task gets
enqueued. So the first time an API request dispatched anything, the API process
re-initialised the SDK as ``component="worker"``, release
``kamerplanter-worker@…``, and stayed that way for the rest of its life. Nothing
re-initialised it back, because ``app.main`` runs its own init once, at import,
long before the first request.

The rule that was supposed to prevent this — "import ``app.tasks`` lazily, inside
the function" — does not prevent it. It only moves the relabelling from startup
to the first dispatch, which is *worse*: at startup ``app.main``'s own init runs
afterwards and corrects the tag, whereas after startup nothing does. Measured on
the pre-fix tree, importing ``app.main`` and then performing the documented lazy
import gave ``component = backend`` followed by ``component = worker``.

So the fix is not a guard against eager imports; it is making the import inert
and initialising from the worker's own entry point — the Celery ``celeryd_init``
/ ``worker_process_init`` / ``beat_init`` signals, which fire in the worker and
beat processes and in no other. These tests pin both halves: the import does
nothing, and the signals do.

Traces to issue #991 (no TC-ID: process labelling is not a user-facing case).
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import textwrap
import types
from pathlib import Path

import pytest
from celery.signals import beat_init, celeryd_init, worker_process_init

import app.tasks  # noqa: F401  importing the package is what connects the receivers

_DSN = "https://key@tracker.example/1"


class _FakeSentry(types.ModuleType):
    """Stand-in for ``sentry_sdk`` recording how it was configured.

    Deliberately not the real SDK: whether ``sentry-sdk`` is installed in the
    running environment must not decide what these tests observe. Without it,
    ``init_error_tracking`` returns ``False`` on the import-not-found branch and
    every assertion below would hold for the wrong reason.
    """

    def __init__(self) -> None:
        super().__init__("sentry_sdk")
        self.init_kwargs: dict | None = None
        self.tags: dict[str, str] = {}

    def init(self, **kwargs) -> None:
        self.init_kwargs = kwargs

    def set_tag(self, key: str, value: str) -> None:
        self.tags[key] = value


@pytest.fixture
def fake_sentry(monkeypatch: pytest.MonkeyPatch) -> _FakeSentry:
    """A live, DSN-configured tracker whose configuration the test can read."""
    module = _FakeSentry()
    monkeypatch.setitem(sys.modules, "sentry_sdk", module)
    monkeypatch.setenv("SENTRY_DSN", _DSN)
    # A deployment sets this from the image tag and it would then shadow the
    # component-derived fallback the release assertions read.
    monkeypatch.delenv("SENTRY_RELEASE", raising=False)
    return module


# ── The import is inert ───────────────────────────────────────────────────


#: Imports ``app.tasks`` the way an API request's dispatch site does, with a DSN
#: configured and the SDK faked, and reports what the import configured. The
#: second half is a control: it initialises deliberately, so an empty
#: ``after_import`` means "the import initialised nothing" rather than "nothing
#: in this process could have initialised anything".
_IMPORT_PROBE = textwrap.dedent(
    """
    import json
    import sys
    import types

    class FakeSentry(types.ModuleType):
        def __init__(self):
            super().__init__("sentry_sdk")
            self.tags = {}
        def init(self, **kwargs):
            self.tags["release"] = kwargs.get("release")
        def set_tag(self, key, value):
            self.tags[key] = value

    fake = FakeSentry()
    sys.modules["sentry_sdk"] = fake

    import app.tasks  # noqa: F401  what every Celery dispatch site in the API does
    after_import = dict(fake.tags)

    from app.observability.error_tracking import init_error_tracking
    init_error_tracking(component="control", release="control@0")

    print("RESULT " + json.dumps({"after_import": after_import, "after_control": dict(fake.tags)}))
    """
)


def _run_probe(code: str) -> dict:
    """Run *code* in a fresh interpreter under the backend root and parse its RESULT."""
    backend_root = Path(__file__).resolve().parents[3]
    result = subprocess.run(
        [sys.executable, "-c", code],
        cwd=backend_root,
        capture_output=True,
        text=True,
        env={**os.environ, "SENTRY_DSN": _DSN, "SENTRY_RELEASE": ""},
        timeout=120,
    )
    assert result.returncode == 0, f"stdout={result.stdout!r}\nstderr={result.stderr!r}"
    line = next((line for line in result.stdout.splitlines() if line.startswith("RESULT ")), None)
    assert line is not None, f"probe printed no RESULT\nstdout={result.stdout!r}\nstderr={result.stderr!r}"
    return json.loads(line.removeprefix("RESULT "))


def test_importing_app_tasks_initialises_no_error_tracking():
    """Importing the worker package must not label the importing process.

    A fresh subprocess, because the test session imported ``app.tasks`` long ago
    and an in-process assertion would only observe a cached module. This is the
    whole defect in one line: the API imports this package, so an import-time
    ``init_error_tracking(component="worker")`` makes the API report as the
    worker.
    """
    observed = _run_probe(_IMPORT_PROBE)

    assert observed["after_control"]["component"] == "control", (
        "the control init did not reach the fake SDK, so this test proves nothing "
        f"about the import: {observed['after_control']}"
    )
    assert observed["after_import"] == {}, (
        "importing app.tasks configured error tracking: "
        f"{observed['after_import']} — any process that dispatches a Celery task now reports as that component"
    )


# ── The worker's own entry point does the labelling ───────────────────────


@pytest.mark.parametrize(
    "signal",
    [
        pytest.param(celeryd_init, id="celeryd_init"),
        pytest.param(worker_process_init, id="worker_process_init"),
        pytest.param(beat_init, id="beat_init"),
    ],
)
def test_worker_entry_signal_labels_the_process_as_the_worker(fake_sentry: _FakeSentry, signal) -> None:
    """Each process Celery starts from this package must label itself.

    Sent for real rather than by calling the handler, because a handler that is
    written but never connected is the failure mode that costs the most: it
    reads as done and reports nothing.
    """
    signal.send(sender="test")

    assert fake_sentry.tags.get("component") == "worker"
    assert fake_sentry.init_kwargs is not None
    assert fake_sentry.init_kwargs["release"].startswith("kamerplanter-worker@")
