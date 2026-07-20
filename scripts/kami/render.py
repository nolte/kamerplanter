#!/usr/bin/env python3
"""KAMI image render + review driver.

Drives the nolte-media ``image-generate`` script (FLUX.1-schnell via Cloudflare
by default) over the job manifest ``spec/design/_generation-manifest.yaml`` and
tracks per-job state so a Claude-vision reviewer can gate every generated PNG
against ``spec/design/KAMI-CHARACTER-REFERENCE.md`` and rejected jobs are
regenerated with a fresh seed.

This script is deterministic and stdlib-only apart from PyYAML: it never judges
conformance itself — that is the reviewer agent's job (``kami-image-reviewer``).
It only *generates*, records *attempts*, and applies the reviewer's *verdicts*.

Pipeline (one round):

    render.py generate            # generate every pending/rejected job
    render.py worklist            # emit the review worklist (status=generated)
    # -> Claude vision reviews each image, then per image:
    render.py verdict --id <ID> --status approved|rejected --note "..."
    render.py generate            # regenerate the rejected ones (seed bumped)
    # repeat until `render.py status` shows no pending/generated/rejected

Prompt source per job (manifest): either an inline ``prompt:`` (a self-contained
FLUX prompt) or ``from_doc:`` + ``motif_heading:`` (the first fenced block after
that heading in the prompt document is extracted). Inline wins if both are set.

Provider/model: the default provider is ``cloudflare`` (FLUX.1-schnell,
``@cf/black-forest-labs/flux-1-schnell`` — free tier, no watermark). Override
per-run with ``--provider`` or per-job with ``provider:`` in the manifest.

The nolte-media ``image_generate.py`` path is resolved from, in order:
``$NOLTE_MEDIA_ROOT``, ``$CLAUDE_PLUGIN_ROOT``, then the dogfooding default
``~/repos/github/claude-shared/plugins/nolte-media``.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MANIFEST = REPO_ROOT / "spec" / "design" / "_generation-manifest.yaml"
DEFAULT_RENDER_DIR = REPO_ROOT / ".render" / "kami"
STATE_FILENAME = "render-state.json"

DOGFOOD_MEDIA_ROOT = Path.home() / "repos" / "github" / "claude-shared" / "plugins" / "nolte-media"

# Statuses a job moves through.
PENDING = "pending"      # never generated
GENERATED = "generated"  # image on disk, awaiting review
APPROVED = "approved"    # reviewer confirmed KAMI-conformant — terminal
REJECTED = "rejected"    # reviewer rejected — regenerate with a fresh seed
BLOCKED = "blocked"      # max attempts hit without approval — terminal, needs a human

REGEN_STATUSES = {PENDING, REJECTED}


class RenderError(Exception):
    pass


# --------------------------------------------------------------------------- #
# nolte-media image_generate.py resolution
# --------------------------------------------------------------------------- #
def resolve_image_generate() -> Path:
    for env in ("NOLTE_MEDIA_ROOT", "CLAUDE_PLUGIN_ROOT"):
        root = os.environ.get(env)
        if root:
            cand = Path(root) / "skills" / "image-generate" / "scripts" / "image_generate.py"
            if cand.is_file():
                return cand
    cand = DOGFOOD_MEDIA_ROOT / "skills" / "image-generate" / "scripts" / "image_generate.py"
    if cand.is_file():
        return cand
    raise RenderError(
        "cannot find nolte-media image_generate.py. Set $NOLTE_MEDIA_ROOT to your "
        "nolte-media plugin checkout (default tried: "
        f"{DOGFOOD_MEDIA_ROOT})."
    )


# --------------------------------------------------------------------------- #
# Manifest + state
# --------------------------------------------------------------------------- #
def load_manifest(path: Path) -> dict:
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise RenderError(f"cannot read manifest {path}: {exc}") from exc
    if not isinstance(data, dict) or "jobs" not in data:
        raise RenderError(f"manifest {path} must be a mapping with a top-level 'jobs:' list")
    jobs = data.get("jobs") or []
    seen: set[str] = set()
    for job in jobs:
        jid = job.get("id")
        if not jid:
            raise RenderError(f"every job needs an 'id': offending entry {job!r}")
        if jid in seen:
            raise RenderError(f"duplicate job id: {jid}")
        seen.add(jid)
        if not job.get("prompt") and not (job_doc(job) and job.get("motif_heading")):
            raise RenderError(
                f"job {jid} needs either an inline 'prompt:' or both "
                "a doc ('doc:'/'from_doc:') and 'motif_heading:'"
            )
    return data


def state_path(render_dir: Path) -> Path:
    return render_dir / STATE_FILENAME


def load_state(render_dir: Path) -> dict:
    p = state_path(render_dir)
    if not p.is_file():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise RenderError(f"cannot read state file {p}: {exc}") from exc


def save_state(render_dir: Path, state: dict) -> None:
    render_dir.mkdir(parents=True, exist_ok=True)
    state_path(render_dir).write_text(
        json.dumps(state, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def job_state(state: dict, jid: str) -> dict:
    return state.setdefault(jid, {"status": PENDING, "attempts": 0})


# --------------------------------------------------------------------------- #
# Prompt resolution (inline, or fenced block after a heading in a doc)
# --------------------------------------------------------------------------- #
def extract_block_after_heading(doc_path: Path, heading: str) -> str:
    try:
        text = doc_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise RenderError(f"cannot read from_doc {doc_path}: {exc}") from exc
    pat = re.compile(rf"^#+[ \t].*{re.escape(heading)}.*$", re.MULTILINE)
    m = pat.search(text)
    if not m:
        raise RenderError(f"no heading matching {heading!r} found in {doc_path}")
    rest = text[m.end():]
    fence = re.search(r"```[^\n]*\n(.*?)\n```", rest, re.DOTALL)
    if not fence:
        raise RenderError(f"no fenced prompt block after heading {heading!r} in {doc_path}")
    block = fence.group(1).strip()
    if not block:
        raise RenderError(f"empty fenced block after heading {heading!r} in {doc_path}")
    return block


# The prompt-docs were authored for Gemini: narrative scene + a trailing
# "Avoid: text, numbers, ..." negative clause + a Light-mode dark-green outline.
# FLUX has no negative-prompt channel, so we strip the negative clause (a literal
# "Avoid: text" makes FLUX MORE likely to render text) and swap the outline line
# for the Dark palette when a Dark variant is requested. Inline `prompt:` blocks
# are already FLUX-normalised and skip this.
_AVOID_RE = re.compile(r"\n[ \t]*Avoid:.*\Z", re.IGNORECASE | re.DOTALL)
_OUTLINE_LIGHT_RE = re.compile(r"Outlines:\s*dark green\s*#1b5e20[^\n]*", re.IGNORECASE)
_DARK_OUTLINE = "Outlines: light green #c8e6c9, 2.5px outer, 1.5px inner, rounded line caps."

# Cloudflare Workers-AI FLUX rejects prompts longer than ~2048 chars with HTTP 400.
MAX_PROMPT_CHARS = 2040


def flux_normalize(block: str, variant: str | None) -> str:
    block = _AVOID_RE.sub("", block).strip()
    if variant == "dark":
        block = _OUTLINE_LIGHT_RE.sub(_DARK_OUTLINE, block)
    return block


def job_doc(job: dict) -> str | None:
    """The prompt-doc path, from either 'from_doc:' or 'doc:' (unified key)."""
    return job.get("from_doc") or job.get("doc")


def resolve_prompt(job: dict, anchor: str = "") -> str:
    if job.get("prompt"):
        body = str(job["prompt"]).strip()  # inline blocks are already FLUX-clean
    else:
        rel = job_doc(job)
        doc = REPO_ROOT / rel if not os.path.isabs(rel) else Path(rel)
        block = extract_block_after_heading(doc, job["motif_heading"])
        body = flux_normalize(block, job.get("variant"))
    # Prepend the shared anatomy anchor (defaults.anatomy_anchor) so EVERY job —
    # inline or doc-referenced — states the load-bearing invariant that FLUX most
    # often gets wrong: the face + arms are on the pot, the leaves are plain.
    anchor = (anchor or "").strip()
    if not anchor:
        return body
    combined = f"{anchor}\n\n{body}"
    # Cloudflare FLUX rejects prompts over ~2048 chars with HTTP 400. The anchor is
    # load-bearing, so when the anchor + scene body overflow, trim the scene body
    # (at a sentence/word boundary) rather than dropping the invariant.
    if len(combined) > MAX_PROMPT_CHARS:
        budget = MAX_PROMPT_CHARS - len(anchor) - 2
        trimmed = body[: max(0, budget)]
        cut = max(trimmed.rfind(". "), trimmed.rfind("\n"), trimmed.rfind(" "))
        if cut > budget * 0.6:
            trimmed = trimmed[: cut + 1]
        sys.stderr.write(
            f"warning: prompt for {job['id']} exceeded {MAX_PROMPT_CHARS} chars; "
            "scene body trimmed to fit (anatomy anchor kept).\n"
        )
        combined = f"{anchor}\n\n{trimmed.rstrip()}"
    return combined


# --------------------------------------------------------------------------- #
# Generation
# --------------------------------------------------------------------------- #
def image_out_path(render_dir: Path, jid: str, ext: str = "png") -> Path:
    safe = jid.replace("/", "_")
    return render_dir / f"{safe}.{ext}"


def generate_one(
    engine: Path, job: dict, prompt: str, out: Path, provider: str, seed: int,
    width: int, height: int, dry_run: bool,
) -> None:
    cmd = [
        sys.executable, str(engine),
        "--provider", provider,
        "--prompt", prompt,
        "--out", str(out),
        "--seed", str(seed),
        "--width", str(width),
        "--height", str(height),
        "--force",  # our state machine owns overwrite semantics per attempt
    ]
    if dry_run:
        preview = prompt.replace("\n", " ")
        preview = preview[:97] + "..." if len(preview) > 100 else preview
        print(f"  DRY-RUN {job['id']}: provider={provider} seed={seed} -> {out}")
        print(f"          prompt: {preview}")
        return
    proc = subprocess.run(cmd, capture_output=True, text=True)
    sys.stderr.write(proc.stderr)
    if proc.returncode != 0:
        raise RenderError(
            f"image_generate failed for {job['id']} (exit {proc.returncode}). "
            "See the provider message above."
        )


def cmd_generate(args: argparse.Namespace) -> int:
    manifest = load_manifest(args.manifest)
    defaults = manifest.get("defaults", {}) or {}
    render_dir = Path(args.render_dir or defaults.get("render_dir") or DEFAULT_RENDER_DIR)
    provider_default = args.provider or defaults.get("provider") or "cloudflare"
    base_seed = int(defaults.get("base_seed", 1000))
    max_attempts = int(args.max_attempts or defaults.get("max_attempts", 3))
    engine = resolve_image_generate()
    state = load_state(render_dir)

    only = re.compile(args.only) if args.only else None
    to_run = []
    for job in manifest["jobs"]:
        jid = job["id"]
        if only and not only.search(jid):
            continue
        js = job_state(state, jid)
        if js["status"] == APPROVED and not args.force:
            continue
        if js["status"] == GENERATED and not args.force:
            continue  # awaiting review; don't burn quota re-rolling it
        if js["status"] == BLOCKED and not args.force:
            continue
        if js["attempts"] >= max_attempts and not args.force:
            js["status"] = BLOCKED
            continue
        to_run.append(job)

    if not to_run:
        print("Nothing to generate. (Run `render.py status` for the current state.)")
        save_state(render_dir, state)
        return 0

    print(f"Generating {len(to_run)} job(s) via provider '{provider_default}' -> {render_dir}")
    failures = 0
    for job in to_run:
        jid = job["id"]
        js = job_state(state, jid)
        provider = job.get("provider") or provider_default
        ext = "jpg" if provider == "pollinations" else "png"
        out = image_out_path(render_dir, jid, ext)
        seed = base_seed + js["attempts"]  # fresh seed each attempt -> real variety on regen
        try:
            prompt = resolve_prompt(job, defaults.get("anatomy_anchor", ""))
            generate_one(
                engine, job, prompt, out, provider, seed,
                int(job.get("width", 1024)), int(job.get("height", 1024)), args.dry_run,
            )
        except RenderError as exc:
            print(f"  ERROR {jid}: {exc}", file=sys.stderr)
            failures += 1
            continue
        if not args.dry_run:
            js["attempts"] += 1
            js["status"] = GENERATED
            js["last_image"] = str(out)
            js["seed"] = seed
            js.pop("review", None)
    save_state(render_dir, state)
    if failures:
        print(f"\n{failures} job(s) failed to generate.", file=sys.stderr)
        return 1
    if not args.dry_run:
        print("\nDone. Review the images: `render.py worklist`")
    return 0


# --------------------------------------------------------------------------- #
# Review worklist + verdict application
# --------------------------------------------------------------------------- #
def cmd_worklist(args: argparse.Namespace) -> int:
    manifest = load_manifest(args.manifest)
    defaults = manifest.get("defaults", {}) or {}
    render_dir = Path(args.render_dir or defaults.get("render_dir") or DEFAULT_RENDER_DIR)
    state = load_state(render_dir)
    jobs_by_id = {j["id"]: j for j in manifest["jobs"]}

    items = []
    for jid, js in state.items():
        if js.get("status") != GENERATED:
            continue
        job = jobs_by_id.get(jid, {})
        items.append({
            "id": jid,
            "image": js.get("last_image"),
            "attempt": js.get("attempts"),
            "gap": job.get("gap"),
            "variant": job.get("variant"),
            "emotion": job.get("emotion"),
            "pose": job.get("pose"),
            "size": job.get("size"),
            "from_doc": job_doc(job),
        })
    items.sort(key=lambda x: x["id"])
    if args.json:
        print(json.dumps(items, indent=2, ensure_ascii=False))
        return 0
    if not items:
        print("No images awaiting review.")
        return 0
    print(f"{len(items)} image(s) awaiting KAMI-conformance review:\n")
    for it in items:
        print(f"- id={it['id']}  variant={it['variant']}  gap={it['gap']}  attempt={it['attempt']}")
        print(f"    image:   {it['image']}")
        print(f"    emotion: {it['emotion']}")
        print(f"    pose:    {it['pose']}")
    return 0


def cmd_verdict(args: argparse.Namespace) -> int:
    manifest = load_manifest(args.manifest)
    defaults = manifest.get("defaults", {}) or {}
    render_dir = Path(args.render_dir or defaults.get("render_dir") or DEFAULT_RENDER_DIR)
    max_attempts = int(defaults.get("max_attempts", 3))
    state = load_state(render_dir)
    if args.id not in state:
        raise RenderError(f"unknown job id (never generated): {args.id}")
    js = state[args.id]
    if args.status == "approved":
        js["status"] = APPROVED
    else:
        js["status"] = BLOCKED if js.get("attempts", 0) >= max_attempts else REJECTED
    js["review"] = {"verdict": args.status, "note": args.note or "", "score": args.score}
    save_state(render_dir, state)
    tail = " (max attempts reached -> BLOCKED, needs a human)" if js["status"] == BLOCKED else ""
    print(f"Recorded {args.status} for {args.id} -> status={js['status']}{tail}")
    return 0


def cmd_status(args: argparse.Namespace) -> int:
    manifest = load_manifest(args.manifest)
    defaults = manifest.get("defaults", {}) or {}
    render_dir = Path(args.render_dir or defaults.get("render_dir") or DEFAULT_RENDER_DIR)
    state = load_state(render_dir)
    counts: dict[str, int] = {}
    rows = []
    for job in manifest["jobs"]:
        jid = job["id"]
        js = state.get(jid, {"status": PENDING, "attempts": 0})
        counts[js["status"]] = counts.get(js["status"], 0) + 1
        rows.append((jid, js["status"], js.get("attempts", 0), (js.get("review") or {}).get("note", "")))
    total = len(manifest["jobs"])
    print(f"Manifest: {args.manifest}  ({total} jobs)")
    print(f"Render dir: {render_dir}\n")
    for status in (APPROVED, GENERATED, REJECTED, BLOCKED, PENDING):
        if counts.get(status):
            print(f"  {status:10s} {counts[status]}")
    if args.verbose:
        print()
        for jid, status, attempts, note in sorted(rows):
            note_s = f"  — {note}" if note else ""
            print(f"  {jid:36s} {status:10s} a{attempts}{note_s}")
    return 0


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #
def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="render", description=__doc__.splitlines()[0])
    p.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST, help="job manifest (YAML)")
    p.add_argument("--render-dir", type=Path, help="override render output directory")
    sub = p.add_subparsers(dest="command", required=True)

    g = sub.add_parser("generate", help="generate every pending/rejected job")
    g.add_argument("--only", help="regex; only jobs whose id matches are generated")
    g.add_argument("--provider", choices=["cloudflare", "pollinations", "gemini"], help="override provider")
    g.add_argument("--max-attempts", type=int, help="override max regen attempts")
    g.add_argument("--dry-run", action="store_true", help="print what would be generated, call nothing")
    g.add_argument("--force", action="store_true", help="regenerate even approved/generated/blocked jobs")
    g.set_defaults(func=cmd_generate)

    w = sub.add_parser("worklist", help="list images awaiting review")
    w.add_argument("--json", action="store_true", help="emit JSON for the reviewer agent")
    w.set_defaults(func=cmd_worklist)

    v = sub.add_parser("verdict", help="record a reviewer verdict for one job")
    v.add_argument("--id", required=True)
    v.add_argument("--status", required=True, choices=["approved", "rejected"])
    v.add_argument("--note", help="reviewer rationale (kept in state)")
    v.add_argument("--score", type=int, help="optional 0-100 conformance score")
    v.set_defaults(func=cmd_verdict)

    s = sub.add_parser("status", help="show the per-job state summary")
    s.add_argument("--verbose", "-v", action="store_true")
    s.set_defaults(func=cmd_status)
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return args.func(args)
    except RenderError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
