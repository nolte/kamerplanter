#!/usr/bin/env bash
# Turn a Nuclei scan's own coverage into a first-class verdict (#1308).
#
# THE PROBLEM THIS EXISTS FOR, measured rather than assumed.
#
# Nuclei exits 0 and writes a ZERO-BYTE `-o` file both when it scanned
# everything and found nothing, and when it scanned nothing at all. Measured
# against the pinned v3.11.1 on 2026-09-01 with two dead ports as targets:
#
#     [INF] Templates loaded for current scan: 5
#     [INF] Targets loaded for current scan: 2
#     [INF] Skipped 127.0.0.1:19998 from target list as found unresponsive permanently: …
#     [INF] Skipped 127.0.0.1:19999 from target list as found unresponsive permanently: …
#     [INF] Scan completed in 2.167149ms. No results found.
#     exit 0, results.jsonl = 0 bytes, no results.sarif written
#
# That is byte-for-byte the artefact set the genuine clean nightly run
# 33337784895 produced (5902 templates, 2 targets, 0 matches). Downstream
# nothing could tell them apart: `hashFiles('results.sarif')` is empty in both,
# the issue-opening script reads an empty file and reports "no findings" in
# both, and the job is green in both. A scan against a stack that never came up
# reported success.
#
# So the verdict cannot be derived from the artefacts. It has to come from what
# nuclei said about its own coverage, which is why this script parses the run
# log instead of only the results file.
#
# NOT asserted here, deliberately: that the scan found nothing. Zero findings is
# the desired outcome, and failing on it would trade one blind spot for another.
# What is asserted is that the scan HAPPENED, at the breadth it was configured
# for, against targets that answered.

set -euo pipefail

usage() {
  cat >&2 <<'USAGE'
Usage: assert-nuclei-coverage.sh --log FILE --results FILE --expect-targets N
                                 --targets "URL [URL ...]"
                                 --min-templates N [--sarif FILE]
                                 [--summary FILE] [--json-out FILE]
                                 [--write-empty-sarif FILE] [--label TEXT]

  --log               nuclei's combined stdout+stderr, as written by `| tee`.
  --results           the `-o` JSONL path. Nuclei creates it even with zero
                      matches, so its ABSENCE means the scan never ran.
  --expect-targets    how many targets the scan was configured with.
  --targets           the configured targets themselves, space separated. Load
                      bearing, not decoration: nuclei also reports ports its
                      TEMPLATES probed and found closed, and without this list
                      those are indistinguishable from a configured target that
                      went unreachable. See "WHOSE DROP IS IT" below.
  --min-templates     floor for "Templates loaded for current scan".
  --sarif             the `-sarif-export` path, if any.
  --summary           append a Markdown verdict here ($GITHUB_STEP_SUMMARY).
  --json-out          write the parsed numbers here, for the artefact.
  --write-empty-sarif write a valid zero-result SARIF at this path, but ONLY
                      when every assertion below passed and nuclei wrote none.
  --label             free text naming the lane, used in the summary heading.
USAGE
}

log_file=""
results_file=""
sarif_file=""
summary_file=""
json_out=""
empty_sarif_out=""
expect_targets=""
configured_targets=""
min_templates=""
label="Nuclei scan"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --log) log_file="$2"; shift 2 ;;
    --results) results_file="$2"; shift 2 ;;
    --sarif) sarif_file="$2"; shift 2 ;;
    --summary) summary_file="$2"; shift 2 ;;
    --json-out) json_out="$2"; shift 2 ;;
    --write-empty-sarif) empty_sarif_out="$2"; shift 2 ;;
    --expect-targets) expect_targets="$2"; shift 2 ;;
    --targets) configured_targets="$2"; shift 2 ;;
    --min-templates) min_templates="$2"; shift 2 ;;
    --label) label="$2"; shift 2 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "assert-nuclei-coverage: unknown argument '$1'" >&2; usage; exit 2 ;;
  esac
done

for required in log_file results_file expect_targets configured_targets min_templates; do
  if [[ -z "${!required}" ]]; then
    echo "assert-nuclei-coverage: --${required//_/-} is required" >&2
    usage
    exit 2
  fi
done

# Collected as text so the summary can list every reason, not just the first.
failures=()
fail() {
  failures+=("$1")
  echo "::error::$1" >&2
}

# ── Did the scan run at all? ──────────────────────────────────────────────
# Both files are produced unconditionally by a nuclei that started: the log by
# the `tee` in the workflow, `results.jsonl` by nuclei's `-o` (measured: created
# at 0 bytes even for a zero-match scan). Either one missing means the step was
# skipped or died before nuclei got going.
scan_ran=true
if [[ ! -f "$log_file" ]]; then
  fail "No run log at '$log_file' — the scan step did not execute. This is not a clean result."
  scan_ran=false
fi
if [[ ! -f "$results_file" ]]; then
  fail "No results file at '$results_file' — nuclei never wrote its output file, so no scan completed."
  scan_ran=false
fi

templates_loaded=""
targets_loaded=""
unresponsive=""
unresponsive_count=0
incidental_count=0
matches=0

if [[ "$scan_ran" == true ]]; then
  # nuclei colours its own log; `-no-color` is passed in CI but stripping here
  # too keeps the script correct against a log captured without it.
  plain=$(sed 's/\x1b\[[0-9;]*m//g' "$log_file")

  templates_loaded=$(printf '%s\n' "$plain" \
    | sed -n 's/.*Templates loaded for current scan: \([0-9]\{1,\}\).*/\1/p' \
    | tail -n 1)
  targets_loaded=$(printf '%s\n' "$plain" \
    | sed -n 's/.*Targets loaded for current scan: \([0-9]\{1,\}\).*/\1/p' \
    | tail -n 1)

  # Nuclei drops a target it cannot reach and carries on to a green exit. It
  # repeats the line once per attempted request, so reduce to distinct hosts.
  #
  # WHOSE DROP IS IT — the correction that cost the 2026-09-01 nightly.
  #
  # This originally counted EVERY `Skipped` line as a configured target going
  # unreachable, and reported "3 of 2 targets were unreachable" on run
  # 33462544851 — a ratio that cannot exist, which is the tell. The three were
  # `127.0.0.1:80`, `127.0.0.1:4040` and `127.0.0.1:43800`, none of them
  # configured. They are ports the TEMPLATES probed and found closed:
  #
  #   Skipped 127.0.0.1:80 … chain="… http://127.0.0.1:80/SMS_DP_SMSPKG$/Datalib"
  #   Skipped 127.0.0.1:4040 … chain="… https://127.0.0.1:4040/jobs/?…"
  #
  # An SCCM template and a Spark-UI template knocking on closed ports is what a
  # healthy full scan against a two-port host LOOKS like. So the check fired on
  # every healthy night — a guaranteed false positive, which recreates exactly
  # the condition #1308 exists to remove: a lane red for a reason unrelated to
  # coverage, in which a real coverage failure cannot be seen.
  #
  # The guard was built and validated against the FAILURE case (two dead ports
  # as targets, where every Skipped line WAS a configured target) and never
  # against a healthy one at full breadth. Hence the identity check below and
  # the selftest that now runs a healthy log through it.
  all_skipped=$(printf '%s\n' "$plain" \
    | sed -n 's/.*Skipped \([^ ]\{1,\}\) from target list as found unresponsive permanently.*/\1/p' \
    | sort -u)

  # Normalise both sides to host:port. Configured targets arrive as URLs, the
  # log reports bare authorities. A URL without an explicit port carries the
  # scheme's default, or nothing would ever match for a plain https target.
  normalise_authority() {
    local raw="$1" scheme="" hostport=""
    case "$raw" in
      http://*)  scheme=http;  hostport="${raw#http://}" ;;
      https://*) scheme=https; hostport="${raw#https://}" ;;
      *)         hostport="$raw" ;;
    esac
    hostport="${hostport%%/*}"
    hostport="${hostport%%\?*}"
    if [[ "$hostport" != *:* ]]; then
      case "$scheme" in
        https) hostport="$hostport:443" ;;
        http)  hostport="$hostport:80" ;;
      esac
    fi
    printf '%s' "$hostport"
  }

  configured_authorities=""
  for t in $configured_targets; do
    configured_authorities+="$(normalise_authority "$t")"$'\n'
  done

  # Only a drop of something we ASKED for is a coverage verdict. The rest is
  # ordinary template probing and is reported as a number, never as a failure.
  unresponsive=""
  incidental_count=0
  while IFS= read -r dropped; do
    [[ -z "$dropped" ]] && continue
    if printf '%s' "$configured_authorities" | grep -Fxq "$(normalise_authority "$dropped")"; then
      unresponsive+="$dropped"$'\n'
    else
      incidental_count=$((incidental_count + 1))
    fi
  done <<< "$all_skipped"
  unresponsive=$(printf '%s' "$unresponsive" | sed '/^$/d')
  # Both `|| true` below absorb `grep -c`'s exit 1 for a count of ZERO, which
  # is the ordinary case, not a failure. Neither swallows a verdict: every
  # verdict in this script is an explicit comparison on the resulting number,
  # and `exit 1` at the end is driven by the `failures` array. Spelled out
  # because `scripts/check_workflow_gate_integrity.py` scans
  # `.github/workflows/**` only — moving this logic out of an inline `run:`
  # block also moved it out of that scanner's reach.
  if [[ -n "$unresponsive" ]]; then
    unresponsive_count=$(printf '%s\n' "$unresponsive" | grep -c . || true)
  fi

  matches=$(grep -c . "$results_file" || true)

  if [[ -z "$templates_loaded" ]]; then
    fail "The run log never reported 'Templates loaded for current scan' — nuclei did not reach the scanning stage."
  elif [[ "$templates_loaded" -lt "$min_templates" ]]; then
    fail "Only $templates_loaded templates loaded, below the floor of $min_templates. The template set the scan was configured with did not reach it."
  fi

  if [[ -z "$targets_loaded" ]]; then
    fail "The run log never reported 'Targets loaded for current scan' — nuclei did not reach the scanning stage."
  elif [[ "$targets_loaded" -ne "$expect_targets" ]]; then
    fail "$targets_loaded targets loaded, but $expect_targets were configured."
  fi

  # A count above the configured total is arithmetically impossible and means
  # the identity check itself is broken, not that coverage was lost. Say which,
  # because the previous version reported "3 of 2" as a coverage verdict and a
  # reader had no way to tell a defect in this script from a defect in the scan.
  if [[ "$unresponsive_count" -gt "$expect_targets" ]]; then
    fail "assert-nuclei-coverage is broken: it matched $unresponsive_count dropped targets against $expect_targets configured ones, which cannot happen. Fix the parser; do NOT read this as a coverage failure."
  elif [[ "$unresponsive_count" -gt 0 ]]; then
    fail "$unresponsive_count of $expect_targets CONFIGURED targets were unreachable and were dropped from the scan: $(printf '%s' "$unresponsive" | tr '\n' ' '). Coverage claimed by this run is not real."
  fi
fi

verdict="PASS"
if [[ ${#failures[@]} -gt 0 ]]; then
  verdict="FAIL"
fi

# ── Publish the numbers, pass or fail ─────────────────────────────────────
# The summary is written in BOTH directions on purpose. A verdict that only
# appears on failure leaves a green run as silent as it was before, and "the
# lane is quiet" would again mean either "clean" or "not running".
if [[ -n "$summary_file" ]]; then
  {
    echo "### ${label} — coverage"
    echo
    echo "| Measure | Value |"
    echo "| --- | --- |"
    echo "| Templates loaded | ${templates_loaded:-—} (floor ${min_templates}) |"
    echo "| Targets loaded | ${targets_loaded:-—} (configured ${expect_targets}) |"
    echo "| Configured targets dropped as unreachable | ${unresponsive_count} |"
    echo "| Closed ports skipped by templates (informational) | ${incidental_count:-0} |"
    echo "| Findings written | ${matches} |"
    echo "| Verdict | **${verdict}** |"
    echo
    if [[ "$verdict" == "FAIL" ]]; then
      echo "Coverage could not be confirmed:"
      echo
      for f in "${failures[@]}"; do
        echo "- ${f}"
      done
    else
      echo "A scan of ${templates_loaded} templates against ${targets_loaded} responding target(s) completed and wrote ${matches} finding(s)."
    fi
    echo
  } >> "$summary_file"
fi

if [[ -n "$json_out" ]]; then
  jq -n \
    --arg verdict "$verdict" \
    --arg label "$label" \
    --argjson templates "${templates_loaded:-null}" \
    --argjson targets "${targets_loaded:-null}" \
    --argjson expected_targets "$expect_targets" \
    --argjson min_templates "$min_templates" \
    --argjson unreachable "$unresponsive_count" \
    --argjson incidental_ports_skipped "${incidental_count:-0}" \
    --argjson matches "$matches" \
    '{label: $label, verdict: $verdict, templates_loaded: $templates,
      targets_loaded: $targets, targets_configured: $expected_targets,
      templates_floor: $min_templates, targets_unreachable: $unreachable,
      incidental_ports_skipped: $incidental_ports_skipped,
      findings: $matches}' > "$json_out"
fi

# ── Keep the Security tab honest too ──────────────────────────────────────
# Nuclei writes NO SARIF for a zero-match scan (measured), so on a clean night
# the `Upload SARIF` step is skipped and the Code Scanning category is never
# refreshed — a clean nightly and a nightly that stopped running look identical
# there as well. A zero-result SARIF closes that: it dates the analysis and
# resolves alerts the scan no longer reproduces.
#
# Written ONLY on a passing verdict. That is the whole safety property: an
# unverified scan must never be able to tell Code Scanning "nothing is wrong".
if [[ -n "$empty_sarif_out" && "$verdict" == "PASS" ]]; then
  if [[ -n "$sarif_file" && -s "$sarif_file" ]]; then
    echo "Nuclei wrote its own SARIF at '$sarif_file'; not synthesising one."
  else
    jq -n \
      --arg templates "${templates_loaded:-0}" \
      --arg targets "${targets_loaded:-0}" \
      '{
         "$schema": "https://raw.githubusercontent.com/oasis-tcs/sarif-spec/main/sarif-2.1/schema/sarif-schema-2.1.0.json",
         version: "2.1.0",
         runs: [{
           tool: {driver: {name: "nuclei", informationUri: "https://github.com/projectdiscovery/nuclei", rules: []}},
           invocations: [{
             executionSuccessful: true,
             workingDirectory: {uri: "file:///"},
             properties: {templatesLoaded: $templates, targetsLoaded: $targets}
           }],
           results: []
         }]
       }' > "$empty_sarif_out"
    echo "Wrote a zero-result SARIF to '$empty_sarif_out' (verified coverage: ${templates_loaded:-0} templates, ${targets_loaded:-0} targets)."
  fi
fi

if [[ "$verdict" == "FAIL" ]]; then
  exit 1
fi

echo "Coverage confirmed: ${templates_loaded} templates against ${targets_loaded} responding target(s), ${matches} finding(s)."
