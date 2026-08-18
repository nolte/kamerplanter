"""Tests for the #1218 workflow linter (``scripts/check_attest_registry_credentials.py``).

**What is under test.** The detection logic, driven against *constructed*
workflow files written into ``tmp_path`` — never against the real
``.github/workflows``. A test asserting "the tree has N findings" would go red on
the next legitimate workflow edit and teach nobody anything.

**The deliberately-broken workflow.** :class:`TestItCanFail` writes an attesting
job with no Docker-store login and asserts the check goes red, names the job and
exits non-zero. A gate nobody has watched fail is a gate nobody knows works,
which is the whole subject of NFR-018 §2 — and this checker exists because a
*runtime* failure went unwatched for seventeen days.

**The incident is pinned by reconstruction.** :class:`TestTheIncident` rebuilds
the exact pre-fix shape of ``publish-helm-charts``: a ``helm registry login``
``run:`` step followed by ``actions/attest-build-provenance`` with
``push-to-registry: true``. That combination MUST be a finding, and adding
``docker/login-action`` MUST clear it. Both directions, because a checker that
only ever agrees with the repaired tree certifies nothing.

**What the real tree is NOT asserted here, and why.** The sibling
``test_workflow_gate_integrity_check.py`` ends with a ``TestTheRealTree`` class
re-asserting what its pre-commit hook already asserts. This file deliberately has
no such class: at the moment it was written the real tree was still broken (that
is the point — the guard was authored before the fix, so it could be *seen*
failing against the genuine defect), and a test pinning that state would have to
be inverted by the very commit that repairs it. The real tree is gated by the
``attest-registry-credentials`` pre-commit hook, which runs in the required
``static / Static CI Tests`` lane on every push to every branch.

**Why here.** ``pytest tests/unit/`` from ``src/backend`` is a CI check, and the
script lives outside the backend package, so it is loaded by path. It is not a
backend test in subject; it is one in placement, because this is the tier that
runs.

Traces to issue #1218 (no TC-ID: a source-tree gate is not a user-facing case).
"""

from __future__ import annotations

import json
import textwrap
from collections.abc import Callable
from pathlib import Path

import pytest

from tests.support.repo_scripts import load_repo_script

checker = load_repo_script("check_attest_registry_credentials")

#: The pinned action references the real workflow uses, so the fixtures fail for
#: the same reason the real file did rather than for a shape the tree never had.
ATTEST = "actions/attest-build-provenance@4d101475d8b20a2381f78447822ac1eab6504dd8 # v4.2.2"
LOGIN = "docker/login-action@dbcb813823bdd20940b903addbd779551569679f # v4.6.0"


@pytest.fixture
def build_workflows(tmp_path: Path) -> Callable[..., Path]:
    """Return a helper writing workflow files into a ``workflows/`` directory."""

    def _build(**files: str) -> Path:
        root = tmp_path / "workflows"
        root.mkdir(exist_ok=True)
        for name, content in files.items():
            (root / f"{name}.yml").write_text(textwrap.dedent(content).lstrip(), encoding="utf-8")
        return root

    return _build


#: The ``docker/login-action`` step P1 adds — written at the step indentation of
#: :func:`chart_job` so the two can be concatenated without re-indenting.
DOCKER_LOGIN_STEP = f"""      - name: Log in to GHCR (Docker credential store)
        uses: {LOGIN}
        with:
          registry: ${{{{ env.REGISTRY }}}}
          username: ${{{{ github.actor }}}}
          password: ${{{{ secrets.GITHUB_TOKEN }}}}

"""


def chart_job(*, docker_login: bool) -> str:
    """The ``publish-helm-charts`` job of ``docker-publish.yml``, pre- or post-fix.

    Reproduced at column zero rather than as an indented class attribute: the
    fixture writer dedents, and an interpolated block at a different indentation
    than its template silently produces YAML that parses as something else.

    Args:
        docker_login: Whether to include the ``docker/login-action`` step that
            P1 adds. ``False`` is the shape that shipped for seventeen days.
    """
    return f"""name: Build & Publish Container Images
on: [push]
env:
  REGISTRY: ghcr.io
  IMAGE_PREFIX: ghcr.io/${{{{ github.repository_owner }}}}
jobs:
  publish-helm-charts:
    runs-on: ubuntu-latest
    permissions:
      contents: write
      packages: write
      id-token: write
      attestations: write
    strategy:
      matrix:
        chart:
          - kamerplanter
    steps:
      - uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1

{DOCKER_LOGIN_STEP if docker_login else ""}\
      - name: Log in to GHCR
        run: echo "$TOKEN" | helm registry login ${{{{ env.REGISTRY }}}} -u actor --password-stdin

      - name: Package chart
        run: helm package helm/${{{{ matrix.chart }}}}

      - name: Push chart to GHCR
        id: push
        run: helm push "$CHART"-*.tgz "oci://$IMAGE_PREFIX/charts" 2>&1 | tee push.log

      - name: Attest chart provenance
        uses: {ATTEST}
        with:
          subject-name: ${{{{ env.IMAGE_PREFIX }}}}/charts/${{{{ matrix.chart }}}}
          subject-digest: ${{{{ steps.push.outputs.digest }}}}
          push-to-registry: true
"""


def _kinds(root: Path) -> list[str]:
    """The kind of every *counted* finding, sorted."""
    return sorted(finding.kind for finding in checker.collect(root) if not finding.justified)


def _details(root: Path) -> list[str]:
    """The detail text of every *counted* finding."""
    return [finding.detail for finding in checker.collect(root) if not finding.justified]


class TestItCanFail:
    """The broken shape, and the check going red on it."""

    def test_an_attesting_job_without_any_login_is_caught(self, build_workflows: Callable[..., Path]) -> None:
        """No login at all is the simplest form of the defect."""
        root = build_workflows(
            publish=f"""
            name: Publish
            on: [push]
            env:
              REGISTRY: ghcr.io
            jobs:
              publish-chart:
                runs-on: ubuntu-latest
                steps:
                  - name: Attest chart provenance
                    uses: {ATTEST}
                    with:
                      subject-name: ghcr.io/acme/charts/thing
                      subject-digest: sha256:abc
                      push-to-registry: true
            """
        )
        assert _kinds(root) == ["attest_without_docker_login"]

    def test_the_broken_workflow_makes_the_process_exit_non_zero(
        self, build_workflows: Callable[..., Path], capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Detection is worth nothing if the gate still reports success."""
        root = build_workflows(
            publish=f"""
            name: Publish
            on: [push]
            jobs:
              publish-chart:
                runs-on: ubuntu-latest
                steps:
                  - uses: {ATTEST}
                    with:
                      subject-name: ghcr.io/acme/charts/thing
                      push-to-registry: true
            """
        )
        assert checker.main(["--scan-root", str(root)]) == checker.EXIT_DEFECTS
        out = capsys.readouterr().out
        assert "#1218" in out
        assert checker.JUSTIFICATION_MARKER in out

    def test_the_finding_names_the_job_and_the_registry(self, build_workflows: Callable[..., Path]) -> None:
        """A file name alone does not tell anyone which of nine jobs to open."""
        root = build_workflows(
            publish=f"""
            name: Publish
            on: [push]
            jobs:
              build-backend:
                runs-on: ubuntu-latest
                steps:
                  - uses: {LOGIN}
                    with:
                      registry: ghcr.io
                  - uses: {ATTEST}
                    with:
                      subject-name: ghcr.io/acme/backend
                      push-to-registry: true
              publish-helm-charts:
                runs-on: ubuntu-latest
                steps:
                  - uses: {ATTEST}
                    with:
                      subject-name: ghcr.io/acme/charts/thing
                      push-to-registry: true
            """
        )
        findings = checker.collect(root)
        assert len(findings) == 1
        assert "publish-helm-charts" in findings[0].detail
        assert "ghcr.io" in findings[0].detail
        assert findings[0].line > 1

    def test_a_job_with_the_login_is_green(self, build_workflows: Callable[..., Path]) -> None:
        """The fix the message asks for actually clears the check."""
        root = build_workflows(
            publish=f"""
            name: Publish
            on: [push]
            jobs:
              publish-chart:
                runs-on: ubuntu-latest
                steps:
                  - uses: {LOGIN}
                    with:
                      registry: ghcr.io
                      username: ${{{{ github.actor }}}}
                      password: ${{{{ secrets.GITHUB_TOKEN }}}}
                  - uses: {ATTEST}
                    with:
                      subject-name: ghcr.io/acme/charts/thing
                      push-to-registry: true
            """
        )
        assert _kinds(root) == []
        assert checker.main(["--scan-root", str(root)]) == checker.EXIT_OK


class TestTheIncident:
    """The pre-fix ``publish-helm-charts`` shape, reconstructed and pinned.

    Reconstructed rather than read from the tree on purpose: the tree gets
    repaired, and a fixture that follows it stops testing anything. These two
    tests are the reason this file exists — the first says the real defect is a
    finding, the second says the real repair clears it.
    """

    def test_helm_registry_login_alone_is_a_finding(self, build_workflows: Callable[..., Path]) -> None:
        """The v0.1.0/v0.2.0 shape: two published releases lost four artifacts to it.

        ``helm registry login`` writes ``$HELM_REGISTRY_CONFIG``; the attest
        action reads ``~/.docker/config.json`` and nothing else, so the run dies
        with ``No credentials found for registry ghcr.io``.
        """
        root = build_workflows(docker_publish=chart_job(docker_login=False))
        assert _kinds(root) == ["attest_without_docker_login"]

    def test_the_finding_says_what_the_job_did_instead(self, build_workflows: Callable[..., Path]) -> None:
        """ "No login" and "the wrong kind of login" need different fixes.

        A message that only said "no credentials" would send the next reader to
        the `helm registry login` line, which is correct and must stay.
        """
        root = build_workflows(docker_publish=chart_job(docker_login=False))
        (detail,) = _details(root)
        assert "helm registry login" in detail
        assert "publish-helm-charts" in detail
        assert "ghcr.io" in detail

    def test_the_env_expression_subject_still_resolves_to_ghcr(self, build_workflows: Callable[..., Path]) -> None:
        """``${{ env.IMAGE_PREFIX }}/charts/${{ matrix.chart }}`` is mostly unresolvable.

        Only its head segment has to resolve, and it does — ``ghcr.io``. A
        checker that gave up on the whole string would have reported "the
        attested registry" and lost the one fact a reader needs.
        """
        root = build_workflows(docker_publish=chart_job(docker_login=False))
        assert "attests to ghcr.io" in _details(root)[0]

    def test_adding_the_docker_login_clears_it(self, build_workflows: Callable[..., Path]) -> None:
        """P1's repair, asserted from here so the two packages cannot drift."""
        root = build_workflows(docker_publish=chart_job(docker_login=True))
        assert _kinds(root) == []

    def test_the_helm_login_may_stay(self, build_workflows: Callable[..., Path]) -> None:
        """`helm push` reads Helm's store, so removing that login breaks the push.

        The checker must not push anyone towards deleting it — two logins to one
        registry in one job is the correct end state here, and R-1 of the plan is
        precisely the risk that somebody tidies one away.
        """
        source = chart_job(docker_login=True)
        assert "helm registry login" in source
        root = build_workflows(docker_publish=source)
        assert checker.main(["--scan-root", str(root)]) == checker.EXIT_OK


class TestPrecisionGuards:
    """What the check refuses to report, so it does not get switched off."""

    def test_an_attestation_that_does_not_push_is_not_a_finding(self, build_workflows: Callable[..., Path]) -> None:
        """Without ``push-to-registry`` the action never opens the Docker config."""
        root = build_workflows(
            publish=f"""
            name: Publish
            on: [push]
            jobs:
              attest-only:
                runs-on: ubuntu-latest
                steps:
                  - uses: {ATTEST}
                    with:
                      subject-name: ghcr.io/acme/thing
                      subject-digest: sha256:abc
            """
        )
        assert _kinds(root) == []

    def test_push_to_registry_false_is_not_a_finding(self, build_workflows: Callable[..., Path]) -> None:
        """Writing the default out loud is the opposite of the defect."""
        root = build_workflows(
            publish=f"""
            name: Publish
            on: [push]
            jobs:
              attest-only:
                runs-on: ubuntu-latest
                steps:
                  - uses: {ATTEST}
                    with:
                      subject-name: ghcr.io/acme/thing
                      push-to-registry: false
            """
        )
        assert _kinds(root) == []

    def test_an_expression_valued_flag_is_treated_as_possibly_true(self, build_workflows: Callable[..., Path]) -> None:
        """The unknown defaults to "requires a login", and the marker is the way out.

        Defaulting an unresolvable flag to *false* would let the next author
        reproduce #1218 simply by parameterising it.
        """
        root = build_workflows(
            publish=f"""
            name: Publish
            on: [push]
            jobs:
              attest-only:
                runs-on: ubuntu-latest
                steps:
                  - uses: {ATTEST}
                    with:
                      subject-name: ghcr.io/acme/thing
                      push-to-registry: ${{{{ github.ref_type == 'tag' }}}}
            """
        )
        assert _kinds(root) == ["attest_without_docker_login"]

    def test_a_shell_docker_login_counts(self, build_workflows: Callable[..., Path]) -> None:
        """``docker login`` writes the same file whoever invokes it."""
        root = build_workflows(
            publish=f"""
            name: Publish
            on: [push]
            jobs:
              publish-chart:
                runs-on: ubuntu-latest
                steps:
                  - name: Log in
                    run: echo "$TOKEN" | docker login ghcr.io -u actor --password-stdin
                  - uses: {ATTEST}
                    with:
                      subject-name: ghcr.io/acme/charts/thing
                      push-to-registry: true
            """
        )
        assert _kinds(root) == []

    def test_a_login_in_a_different_job_does_not_count(self, build_workflows: Callable[..., Path]) -> None:
        """Runners are per job; a sibling job's ``~/.docker/config.json`` is another machine.

        This is the mistake the eight-versus-one shape in ``docker-publish.yml``
        invites: the file *does* contain eight correct logins, none of them in
        the job that needed one.
        """
        root = build_workflows(
            publish=f"""
            name: Publish
            on: [push]
            jobs:
              login-somewhere-else:
                runs-on: ubuntu-latest
                steps:
                  - uses: {LOGIN}
                    with:
                      registry: ghcr.io
              publish-chart:
                needs: login-somewhere-else
                runs-on: ubuntu-latest
                steps:
                  - uses: {ATTEST}
                    with:
                      subject-name: ghcr.io/acme/charts/thing
                      push-to-registry: true
            """
        )
        assert _kinds(root) == ["attest_without_docker_login"]

    def test_a_comment_mentioning_the_action_is_not_a_finding(self, build_workflows: Callable[..., Path]) -> None:
        """Prose about attestation must not be read as an attestation.

        A checker that reported the paragraph explaining the fix would be
        switched off by the first person who read the report.
        """
        root = build_workflows(
            publish="""
            name: Publish
            on: [push]
            # Uses actions/attest-build-provenance with push-to-registry: true elsewhere.
            jobs:
              build:
                runs-on: ubuntu-latest
                steps:
                  # push-to-registry: true needs a docker login; see #1218.
                  - run: make build
            """
        )
        assert _kinds(root) == []

    def test_a_workflow_without_jobs_is_not_an_error(self, build_workflows: Callable[..., Path]) -> None:
        """``.github/workflows`` also holds action metadata and config files."""
        root = build_workflows(
            publish=f"""
            name: Publish
            on: [push]
            jobs:
              real:
                runs-on: ubuntu-latest
                steps:
                  - uses: {LOGIN}
                  - uses: {ATTEST}
                    with:
                      subject-name: acme/thing
                      push-to-registry: true
            """,
            notes="# just a note\n",
        )
        assert _kinds(root) == []


class TestRegistryMatching:
    """The second rule: the login must reach the registry being attested to."""

    def _job(self, login_registry: str, subject: str) -> str:
        return f"""
        name: Publish
        on: [push]
        env:
          REGISTRY: ghcr.io
        jobs:
          publish-chart:
            runs-on: ubuntu-latest
            steps:
              - uses: {LOGIN}
                with:
                  registry: {login_registry}
              - uses: {ATTEST}
                with:
                  subject-name: {subject}
                  push-to-registry: true
        """

    def test_a_login_to_the_wrong_registry_is_caught(self, build_workflows: Callable[..., Path]) -> None:
        """Presence alone would pass a job logged into Docker Hub attesting to GHCR."""
        root = build_workflows(publish=self._job("docker.io", "ghcr.io/acme/charts/thing"))
        assert _kinds(root) == ["attest_login_registry_mismatch"]
        assert "docker.io" in _details(root)[0]

    def test_the_env_reference_resolves(self, build_workflows: Callable[..., Path]) -> None:
        """``registry: ${{ env.REGISTRY }}`` is how every job in this repo spells it.

        Treating it as unresolvable would silently disable the comparison for the
        entire repository.
        """
        root = build_workflows(publish=self._job("${{ env.REGISTRY }}", "ghcr.io/acme/charts/thing"))
        assert _kinds(root) == []

    def test_an_unresolvable_registry_skips_the_comparison(self, build_workflows: Callable[..., Path]) -> None:
        """A guess about ``${{ inputs.registry }}`` would be a false positive.

        Presence is still enforced; only the host equality is dropped.
        """
        root = build_workflows(publish=self._job("${{ inputs.registry }}", "ghcr.io/acme/charts/thing"))
        assert _kinds(root) == []

    def test_a_docker_hub_short_name_matches_a_docker_hub_login(self, build_workflows: Callable[..., Path]) -> None:
        """``acme/thing`` has no registry segment, so it means Docker Hub."""
        root = build_workflows(publish=self._job("index.docker.io", "acme/thing"))
        assert _kinds(root) == []

    def test_a_port_bearing_host_is_a_registry(self, build_workflows: Callable[..., Path]) -> None:
        """``localhost:5000/thing`` is a registry reference, not a Hub short name."""
        root = build_workflows(publish=self._job("localhost:5000", "localhost:5000/acme/thing"))
        assert _kinds(root) == []


class TestJustification:
    """The per-site escape hatch, and why a bare marker is not one."""

    def _with_comment(self, *comment_lines: str) -> str:
        """An attesting job with no login, preceded by *comment_lines*.

        Built at column zero, and the comment lines indented here rather than by
        the caller: a multi-line block interpolated into an indented template
        moves ``textwrap.dedent``'s common prefix and silently reshapes the YAML.
        """
        block = "".join(f"      {line}\n" for line in comment_lines)
        return f"""name: Publish
on: [push]
jobs:
  publish-chart:
    runs-on: ubuntu-latest
    steps:
{block}      - name: Attest chart provenance
        uses: {ATTEST}
        with:
          subject-name: ghcr.io/acme/charts/thing
          push-to-registry: true
"""

    def test_a_reason_in_the_comment_block_above_the_step_exempts_it(
        self, build_workflows: Callable[..., Path]
    ) -> None:
        """This repository explains its steps in a paragraph above ``- name:``.

        The marker has to be reachable from anywhere in that paragraph, not only
        from its last line — otherwise it gets bolted on as a lonely trailer
        instead of sitting in the argument it belongs to.
        """
        root = build_workflows(
            publish=self._with_comment(
                "# attest-credentials-ok: bootstrap-docker-auth.sh writes ~/.docker/config.json",
                "# The runner image ships a pre-seeded credential file.",
            )
        )
        assert _kinds(root) == []

    def test_a_reason_on_the_step_line_exempts_it(self, build_workflows: Callable[..., Path]) -> None:
        root = build_workflows(
            publish=f"""
            name: Publish
            on: [push]
            jobs:
              publish-chart:
                runs-on: ubuntu-latest
                steps:
                  - name: Attest  # attest-credentials-ok: HELM_REGISTRY_CONFIG points at ~/.docker/config.json
                    uses: {ATTEST}
                    with:
                      subject-name: ghcr.io/acme/charts/thing
                      push-to-registry: true
            """
        )
        assert _kinds(root) == []

    def test_a_bare_marker_is_not_an_exemption(self, build_workflows: Callable[..., Path]) -> None:
        """The point of the hatch is the reason, not the token."""
        root = build_workflows(publish=self._with_comment("# attest-credentials-ok:"))
        assert _kinds(root) == ["attest_without_docker_login"]

    def test_a_too_short_reason_is_not_an_exemption(self, build_workflows: Callable[..., Path]) -> None:
        """``# attest-credentials-ok: ok`` explains nothing a reviewer can argue with."""
        root = build_workflows(publish=self._with_comment("# attest-credentials-ok: ok"))
        assert _kinds(root) == ["attest_without_docker_login"]

    def test_the_report_names_every_justified_site(
        self, build_workflows: Callable[..., Path], capsys: pytest.CaptureFixture[str]
    ) -> None:
        """An exemption stays visible; a silent one is indistinguishable from a fix."""
        root = build_workflows(
            publish=self._with_comment("# attest-credentials-ok: bootstrap-docker-auth.sh seeds the config")
        )
        assert checker.main(["--scan-root", str(root), "--list"]) == checker.EXIT_OK
        assert "bootstrap-docker-auth.sh seeds the config" in capsys.readouterr().out


class TestProcessContract:
    """Exit codes and the machine-readable output."""

    def test_json_reports_both_buckets(
        self, build_workflows: Callable[..., Path], capsys: pytest.CaptureFixture[str]
    ) -> None:
        root = build_workflows(
            publish=f"""
            name: Publish
            on: [push]
            jobs:
              unexplained:
                runs-on: ubuntu-latest
                steps:
                  - uses: {ATTEST}
                    with:
                      subject-name: ghcr.io/acme/a
                      push-to-registry: true
              explained:
                runs-on: ubuntu-latest
                steps:
                  # attest-credentials-ok: the runner image seeds ~/.docker/config.json
                  - uses: {ATTEST}
                    with:
                      subject-name: ghcr.io/acme/b
                      push-to-registry: true
            """
        )
        assert checker.main(["--scan-root", str(root), "--json"]) == checker.EXIT_DEFECTS
        payload = json.loads(capsys.readouterr().out)
        assert payload["sites"] == 2
        assert [entry["kind"] for entry in payload["unjustified"]] == ["attest_without_docker_login"]
        assert "unexplained" in payload["unjustified"][0]["detail"]
        assert "explained" in payload["justified"][0]["detail"]

    def test_a_clean_tree_exits_zero_in_json_mode(
        self, build_workflows: Callable[..., Path], capsys: pytest.CaptureFixture[str]
    ) -> None:
        root = build_workflows(
            publish=f"""
            name: Publish
            on: [push]
            jobs:
              publish:
                runs-on: ubuntu-latest
                steps:
                  - uses: {LOGIN}
                    with:
                      registry: ghcr.io
                  - uses: {ATTEST}
                    with:
                      subject-name: ghcr.io/acme/a
                      push-to-registry: true
            """
        )
        assert checker.main(["--scan-root", str(root), "--json"]) == checker.EXIT_OK
        assert json.loads(capsys.readouterr().out)["sites"] == 0

    def test_a_missing_root_is_a_usage_error_not_a_pass(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """A check that cannot run must not report success — the #814 failure mode."""
        assert checker.main(["--scan-root", str(tmp_path / "nowhere")]) == checker.EXIT_USAGE
        assert "does not exist" in capsys.readouterr().err

    def test_an_empty_directory_is_a_usage_error_not_a_pass(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Scanning nothing and reporting clean is the shape NFR-018 §2 forbids.

        A path typo, a renamed directory, a checkout that failed — every one of
        them ends here, and every one of them must be loud.
        """
        empty = tmp_path / "empty"
        empty.mkdir()
        assert checker.main(["--scan-root", str(empty)]) == checker.EXIT_USAGE
        assert "no workflow files" in capsys.readouterr().err

    def test_unparseable_yaml_is_a_usage_error_not_a_pass(
        self, build_workflows: Callable[..., Path], capsys: pytest.CaptureFixture[str]
    ) -> None:
        root = build_workflows(broken="jobs:\n  - [unclosed\n")
        assert checker.main(["--scan-root", str(root)]) == checker.EXIT_USAGE
        assert "cannot parse" in capsys.readouterr().err


class TestTheAnchorIsTheRightStep:
    """Which step a finding is pinned to — and therefore whose comment exempts it.

    Review finding F-1 on PR #1224. The site list held only the *pushing* attest
    steps while the line list held *every* attest step, so the two desynchronised
    as soon as a non-pushing attest step preceded a pushing one: the finding was
    anchored on the harmless step, and a justification written for that step
    silently exempted the violation on the other. The fixture below is the
    reproduction — it exited 0 with "1 justified site(s)" before the ordinal was
    carried through, on a job with no Docker login whatsoever.
    """

    #: A justified non-pushing attest step ahead of a pushing one, in a job that
    #: logs in nowhere.
    TWO_ATTEST_STEPS = f"""
    name: Publish
    on: [push]
    jobs:
      offender:
        runs-on: ubuntu-latest
        steps:
          # attest-credentials-ok: this one does not push, so no registry credential is needed
          - name: Attest without pushing
            uses: {ATTEST}
            with:
              subject-name: ghcr.io/nolte/thing
              subject-digest: sha256:aaaa
              push-to-registry: false
          - name: Attest WITH pushing and NO docker login at all
            uses: {ATTEST}
            with:
              subject-name: ghcr.io/nolte/thing
              subject-digest: sha256:bbbb
              push-to-registry: true
    """

    def test_a_justified_non_pushing_step_does_not_exempt_the_pushing_one(
        self, build_workflows: Callable[..., Path]
    ) -> None:
        """The reason belongs to the step it stands above, not to the next one along."""
        root = build_workflows(publish=self.TWO_ATTEST_STEPS)
        assert _kinds(root) == ["attest_without_docker_login"]

    def test_the_process_exits_non_zero_on_that_shape(
        self, build_workflows: Callable[..., Path], capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Detection is worth nothing if the gate still reports success."""
        root = build_workflows(publish=self.TWO_ATTEST_STEPS)
        assert checker.main(["--scan-root", str(root)]) == checker.EXIT_DEFECTS
        assert "offender" in capsys.readouterr().out

    def test_the_finding_points_at_the_pushing_step(self, build_workflows: Callable[..., Path]) -> None:
        """A line number one step too high sends the reader to the innocent step."""
        root = build_workflows(publish=self.TWO_ATTEST_STEPS)
        (finding,) = checker.collect(root)
        source = finding.path.read_text(encoding="utf-8").splitlines()
        assert "Attest WITH pushing" in source[finding.line - 1]

    def test_a_reason_on_the_pushing_step_still_exempts_it(self, build_workflows: Callable[..., Path]) -> None:
        """The hatch must keep working with a non-pushing step in front of it.

        The other direction of the same defect: an ordinal shifted the other way
        would move the exemption off the step that carries it, and a hatch that
        cannot be reached is a gate nobody can pass.
        """
        root = build_workflows(
            publish=f"""
            name: Publish
            on: [push]
            jobs:
              offender:
                runs-on: ubuntu-latest
                steps:
                  - name: Attest without pushing
                    uses: {ATTEST}
                    with:
                      subject-name: ghcr.io/nolte/thing
                      push-to-registry: false
                  # attest-credentials-ok: bootstrap-docker-auth.sh writes ~/.docker/config.json
                  - name: Attest with pushing
                    uses: {ATTEST}
                    with:
                      subject-name: ghcr.io/nolte/thing
                      push-to-registry: true
            """
        )
        assert _kinds(root) == []
        (finding,) = checker.collect(root)
        assert finding.justified


class TestTheLoginMustHaveRunAlready:
    """Step order and ``if:`` — review finding F-2 on PR #1224.

    Presence anywhere in the job was the whole test, so a login moved *below* the
    attest step, or hung off a condition that is false on the release run, kept
    the gate green while the run died with the exact error this gate exists for.

    **The decision on the conditional case**, since it is not statically
    decidable: a condition the attest step does not itself carry counts as *not*
    satisfying the requirement. The lenient reading — "there is an ``if:``,
    assume it is true when it matters" — is the assumption that produced #1218,
    and the escape hatch already exists for the author who knows better. Two
    steps under the *same* condition run or skip together, which needs no
    knowledge of what the condition means, and is accepted.
    """

    def _job(self, *, login_if: str = "", attest_if: str = "", login_first: bool = True) -> str:
        """A one-job workflow with a login and an attest step, in either order.

        Built at column zero with the two blocks pre-indented: an interpolated
        block at a different indentation than its template silently produces
        YAML that parses as something else.
        """
        login = f"""      - name: Log in to GHCR
        uses: {LOGIN}
{login_if}        with:
          registry: ghcr.io
"""
        attest = f"""      - name: Attest
        uses: {ATTEST}
{attest_if}        with:
          subject-name: ghcr.io/acme/charts/thing
          push-to-registry: true
"""
        body = login + attest if login_first else attest + login
        return f"""name: Publish
on: [push]
jobs:
  publish-chart:
    runs-on: ubuntu-latest
    steps:
{body}"""

    def test_a_login_below_the_attest_step_does_not_count(self, build_workflows: Callable[..., Path]) -> None:
        """``~/.docker/config.json`` is still unwritten when the action reads it."""
        root = build_workflows(publish=self._job(login_first=False))
        assert _kinds(root) == ["attest_login_after_attest_step"]

    def test_that_finding_says_the_order_is_the_problem(self, build_workflows: Callable[..., Path]) -> None:
        """ "Nothing writes the file" would send the author hunting for a step that is there."""
        root = build_workflows(publish=self._job(login_first=False))
        (detail,) = _details(root)
        assert "after it" in detail
        assert "file order" in detail

    def test_the_same_two_steps_in_the_right_order_are_green(self, build_workflows: Callable[..., Path]) -> None:
        """The negative twin: order is the only difference between red and green here."""
        root = build_workflows(publish=self._job(login_first=True))
        assert _kinds(root) == []

    def test_a_conditional_login_under_an_unconditional_attest_is_a_finding(
        self, build_workflows: Callable[..., Path]
    ) -> None:
        """``if: github.event_name == 'push'`` is false on the tag run that attests."""
        root = build_workflows(publish=self._job(login_if="        if: github.event_name == 'push'\n"))
        assert _kinds(root) == ["attest_login_only_conditional"]
        assert "if: github.event_name == 'push'" in _details(root)[0]

    def test_a_login_conditional_on_the_same_expression_as_the_attest_step_is_green(
        self, build_workflows: Callable[..., Path]
    ) -> None:
        """Two steps under one condition run together or skip together."""
        condition = "        if: startsWith(github.ref, 'refs/tags/v')\n"
        root = build_workflows(publish=self._job(login_if=condition, attest_if=condition))
        assert _kinds(root) == []

    def test_the_two_spellings_of_one_condition_compare_equal(self, build_workflows: Callable[..., Path]) -> None:
        """``if: ${{ x }}`` and ``if: x`` are one condition; only the syntax differs.

        Comparing them raw would turn the required lane red on a correct
        workflow, over a distinction GitHub does not make.
        """
        root = build_workflows(
            publish=self._job(
                login_if="        if: ${{ startsWith(github.ref, 'refs/tags/v') }}\n",
                attest_if="        if: startsWith(github.ref, 'refs/tags/v')\n",
            )
        )
        assert _kinds(root) == []

    def test_an_always_running_condition_is_no_condition(self, build_workflows: Callable[..., Path]) -> None:
        """``always()``, ``success()``, ``true`` and ``!cancelled()`` narrow nothing.

        ``!cancelled()`` appears in its ``${{ … }}`` form because a bare ``!`` is
        a YAML tag: writing it unquoted is not a valid workflow at all.
        """
        for spelling in ("always()", "success()", "true", "${{ !cancelled() }}"):
            root = build_workflows(publish=self._job(login_if=f"        if: {spelling}\n"))
            assert _kinds(root) == [], spelling


class TestShellLoginParsing:
    """Reading the registry off a ``run: docker login …`` — findings F-3 and F-4.

    Two directions of one defect class: the parser must not invent a registry
    that is not there (a spurious mismatch turns the *required* lane red on a
    correct workflow) and must not fall over on a legal command line (a
    traceback is not a verdict).
    """

    def _job(self, command: str) -> str:
        """An otherwise-correct job whose only Docker login is *command*."""
        return f"""name: Publish
on: [push]
env:
  REGISTRY: ghcr.io
jobs:
  publish-chart:
    runs-on: ubuntu-latest
    steps:
      - name: Log in
        run: {command}

      - name: Attest
        uses: {ATTEST}
        with:
          subject-name: ghcr.io/acme/charts/thing
          push-to-registry: true
"""

    def test_a_username_expression_is_not_read_as_the_registry(self, build_workflows: Callable[..., Path]) -> None:
        """``-u ${{ github.actor }}`` is three tokens under naive whitespace splitting.

        ``-u`` then consumes ``${{`` alone and ``github.actor`` is accepted as
        the registry — a mismatch against the ``ghcr.io`` subject that exists
        nowhere but in the parser.
        """
        root = build_workflows(
            publish=self._job('echo "$T" | docker login -u ${{ github.actor }} --password-stdin ghcr.io')
        )
        assert _kinds(root) == []

    def test_a_password_expression_is_not_read_as_the_registry(self, build_workflows: Callable[..., Path]) -> None:
        """The same tearing, one flag along."""
        root = build_workflows(
            publish=self._job("docker login --password ${{ secrets.GITHUB_TOKEN }} -u actor ghcr.io")
        )
        assert _kinds(root) == []

    def test_a_registry_spelled_as_an_expression_skips_the_comparison(
        self, build_workflows: Callable[..., Path]
    ) -> None:
        """An unresolvable host is unknown, not ``docker.io``."""
        root = build_workflows(publish=self._job('echo "$T" | docker login ${{ inputs.registry }} -u actor'))
        assert _kinds(root) == []

    def test_a_bare_docker_login_does_not_crash_the_checker(self, build_workflows: Callable[..., Path]) -> None:
        """``run: docker login`` with nothing after it raised ``IndexError``.

        A gate in the required lane that dies with a traceback returns no verdict
        at all — the failure class this whole issue is about.
        """
        root = build_workflows(publish=self._job("docker login"))
        assert _kinds(root) == ["attest_login_registry_mismatch"]

    def test_a_bare_docker_login_means_docker_hub(self, build_workflows: Callable[..., Path]) -> None:
        """Which is what the daemon does with it — so a GHCR subject really is a mismatch."""
        root = build_workflows(publish=self._job("docker login"))
        assert "docker.io" in _details(root)[0]

    def test_a_login_continued_across_lines_is_one_command(self, build_workflows: Callable[..., Path]) -> None:
        """Reading the first physical line only yields "no argument", i.e. Docker Hub.

        Against a ``ghcr.io`` subject that is a mismatch finding on a workflow
        which logs into exactly the right registry.
        """
        root = build_workflows(
            publish=f"""
            name: Publish
            on: [push]
            jobs:
              publish-chart:
                runs-on: ubuntu-latest
                steps:
                  - name: Log in
                    run: |
                      echo "$TOKEN" | docker login \\
                        ghcr.io -u actor --password-stdin
                  - uses: {ATTEST}
                    with:
                      subject-name: ghcr.io/acme/charts/thing
                      push-to-registry: true
            """
        )
        assert _kinds(root) == []

    def test_a_second_command_line_is_not_read_as_the_registry(self, build_workflows: Callable[..., Path]) -> None:
        """The command ends at its newline; what follows is a different command."""
        root = build_workflows(
            publish=f"""
            name: Publish
            on: [push]
            jobs:
              publish-chart:
                runs-on: ubuntu-latest
                steps:
                  - name: Log in
                    run: |
                      echo "$TOKEN" | docker login --password-stdin
                      docker build -t ghcr.io/acme/thing .
                  - uses: {ATTEST}
                    with:
                      subject-name: acme/thing
                      push-to-registry: true
            """
        )
        assert _kinds(root) == []
