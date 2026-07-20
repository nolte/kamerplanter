# KAMI image render + auto-review pipeline

Turns the KAMI graphic-prompt docs under `spec/design/` (authored for issue #593)
into generated images via the **`nolte-media`** plugin, and gates every image
through an **automatic Claude-vision conformance review** against
`spec/design/KAMI-CHARACTER-REFERENCE.md`, regenerating rejected images until they
pass or a per-job attempt budget is hit.

```
manifest ──> render.py generate ──> images (.render/kami/) ──> kami-image-reviewer
   ▲                                                                   │ verdict
   └──────────────── regenerate (fresh seed) ◀── rejected ────────────┘
```

## Components

| File | Role |
|------|------|
| `spec/design/_generation-manifest.yaml` | **Machine SSOT.** Every render job (id, gap, variant, emotion, pose, size, out) + its FLUX prompt (inline, or a `doc:`+`motif_heading:` reference into a prompt-doc). |
| `scripts/kami/render.py` | Deterministic driver: resolves prompts, calls the nolte-media generator, tracks per-job state, applies reviewer verdicts, regenerates rejects with a fresh seed. Never judges conformance itself. |
| `.claude/agents/kami-image-reviewer.md` | The Claude-vision reviewer: checks ONE PNG against the KAMI reference (§3 palette, §3.2 outline, §4.2 emotion, §5 size, §6 composition, §8 avoid) and writes a verdict back via `render.py verdict`. |

## Model / provider (nolte-media check)

The generator is nolte-media `skills/image-generate/scripts/image_generate.py`. Providers:

| Provider | Model | Cost | Notes |
|----------|-------|------|-------|
| **`cloudflare`** (default) | `@cf/black-forest-labs/flux-1-schnell` (FLUX.1-schnell) | **Free** (10k neurons/day, no card) | Apache-2.0, no watermark, no feed. **Ignores width/height → always ~1024² square.** |
| `gemini` | `gemini-2.5-flash-image` | **Billing required** (free quota = 0) | Best mascot fidelity, embeds a SynthID watermark. |
| `pollinations` | FLUX | Free, auth-free | Output licence unsettled; honours width/height. |

**FLUX has no negative-prompt channel.** The prompt-docs were authored for Gemini
with a trailing `Avoid: text, numbers …` clause — under FLUX that clause makes text
*more* likely. So:
- inline manifest prompts are already FLUX-normalised (avoidance as positive phrasing);
- `doc:`+`motif_heading:` jobs are normalised on the fly by `render.py`
  (`flux_normalize`: strips the `Avoid:` clause, and for `variant: dark` swaps the
  outline line to `#c8e6c9`).

## Prerequisites

This pipeline drives the `nolte-media` plugin's `image-generate` script directly by
path — it does **not** require the plugin to be loaded into Claude Code (kamerplanter
deliberately omits `nolte-media` from `task claude`). You only need a local checkout
of `nolte/claude-shared`; `render.py` resolves the script via `$NOLTE_MEDIA_ROOT` →
`$CLAUDE_PLUGIN_ROOT` → the dogfooding default `~/repos/github/claude-shared/plugins/nolte-media`.

```bash
# Cloudflare (default provider, free) — both are required:
export CLOUDFLARE_API_TOKEN=...      # scope: Workers AI — https://dash.cloudflare.com/profile/api-tokens
export CLOUDFLARE_ACCOUNT_ID=...

# Only if you render with `--provider gemini` (best mascot fidelity, but BILLING
# required — the free-tier quota for gemini-2.5-flash-image is 0):
export GEMINI_API_KEY=...            # https://aistudio.google.com/apikey

# Point at your nolte-media plugin checkout (only if not the dogfooding default
# ~/repos/github/claude-shared/plugins/nolte-media):
export NOLTE_MEDIA_ROOT=~/repos/github/claude-shared/plugins/nolte-media
```

The `pollinations` provider needs no credentials at all (optional
`POLLINATIONS_API_TOKEN` only removes the watermark). No credentials are needed to
`--dry-run` or to exercise the review state machine.

## Run the loop

```bash
# 0. See the plan (no credentials needed)
python3 scripts/kami/render.py status
python3 scripts/kami/render.py generate --dry-run --only 'empty-state|app-icon'

# 1. Generate (a subset first is wise — FLUX is fast but quota is finite)
python3 scripts/kami/render.py generate --only 'empty-state|loading|celebration'

# 2. Review — hand each pending image to the reviewer agent. From Claude Code:
python3 scripts/kami/render.py worklist --json
#    then, per image, dispatch the `kami-image-reviewer` agent with that job's
#    id/image/variant/emotion/pose (it calls `render.py verdict` itself).

# 3. Regenerate the rejects (seed auto-bumps each attempt) and re-review
python3 scripts/kami/render.py generate --only 'empty-state|loading|celebration'

# repeat 2–3 until:
python3 scripts/kami/render.py status      # no pending/generated/rejected left
```

`render.py generate` only touches jobs in `pending`/`rejected`. It leaves
`approved` alone, leaves `generated` (awaiting review) alone so quota isn't wasted,
and moves a job to `blocked` (needs a human) once `max_attempts` rejects pile up.

### Driving the review automatically from Claude Code

The review step is a Claude-vision judgement, so it runs from a Claude Code session
(this is the "automatic Claude check" the issue asked for). The orchestration a
session performs each round:

1. `render.py generate --only <batch>`
2. `render.py worklist --json` → for each entry, dispatch the **`kami-image-reviewer`**
   agent (one per image, so each review stays in its own small context). Multiple
   images can be reviewed in parallel.
3. Each agent reads the PNG + the KAMI reference and runs
   `render.py verdict --id <id> --status approved|rejected --score N --note "..."`.
4. `render.py generate --only <batch>` again to re-roll the rejects.
5. Loop until `render.py status` is clean.

## After approval (downstream, per the prompt-docs' post-processing checklists)

`render.py` stops at an **approved PNG**. The rest stays exactly as the prompt-docs
specify and is out of this pipeline's scope:

1. Crop to the target size in each job's `out:` / the doc checklist.
2. `nolte-media:png-to-transparent-svg` for the transparent motifs (app-icons stay
   opaque PNGs); vectorise conservatively.
3. Place under the `out:` path and wire the consumer (barrel `index.ts`,
   `Sidebar.tsx`, `manifest.json`, `KAMI_PHASE_IMAGES`, …).

## Logo & app-icons come from brand/, not FLUX

The app logo and PWA icons are hand-crafted brand marks that already exist under
`brand/` (`logo@2x.png`, `icon@2x.png` — 512×512, transparent, the canonical
**face-on-pot** Kami). A text-to-image model cannot reproduce a pixel-exact brand
mark, so they are **not** FLUX render jobs. Derive them deterministically:

```bash
# PWA icons (opaque #f5f5f5 background, mascot at 80% maskable safe-zone):
#   brand/icon@2x.png -> src/frontend/public/icons/icon-{192,512}.png
# App logo SVG (when needed): vectorise brand/logo@2x.png via
#   nolte-media:png-to-transparent-svg
```

The manifest's `# G-01/G-02` section documents this; those four ids
(`app-icon-512/192`, `app-logo-light/dark`) were removed as render jobs.

## Manifest coverage

- **Batch 1 (inline FLUX prompts):** the #593 single/small-motif *illustration* docs —
  empty-state, loading, celebration, onboarding, dashboard (welcome+empty),
  post-harvest (drying+curing). Logo/app-icons are brand-sourced (see above).
- **Batch 2 (59 jobs, `doc:`+`motif_heading:` references, auto FLUX-normalised):**
  features (G-06, 10×light+dark), tank fill-levels (G-05, 6×light+dark),
  sidebar nav-icons (G-04, 27×light; per-icon dark is the same mechanic, add
  `variant: dark` entries when needed).

Add a job by appending to the manifest; no code change needed. `render.py status`
validates the manifest (unique ids, resolvable prompt source) on every run.
