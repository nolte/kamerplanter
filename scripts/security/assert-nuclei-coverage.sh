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
                                 --min-templates N [--sarif FILE]
                                 [--summary FILE] [--json-out FILE]
                                 [--write-empty-sarif FILE] [--label TEXT]

  --log               nuclei's combined stdout+stderr, as written by `| tee`.
  --results           the `-o` JSONL path. Nuclei creates it even with zero
                      matches, so its ABSENCE means the scan never ran.
  --expect-targets    how many targets the scan was configured with.
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
    --min-templates) min_templates="$2"; shift 2 ;;
    --label) label="$2"; shift 2 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "assert-nuclei-coverage: unknown argument '$1'" >&2; usage; exit 2 ;;
  esac
done

for required in log_file results_file expect_targets min_templates; do
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
  unresponsive=$(printf '%s\n' "$plain" \
    | sed -n 's/.*Skipped \([^ ]\{1,\}\) from target list as found unresponsive permanently.*/\1/p' \
    | sort -u)
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

  if [[ "$unresponsive_count" -gt 0 ]]; then
    fail "$unresponsive_count of $expect_targets targets were unreachable and were dropped from the scan: $(printf '%s' "$unresponsive" | tr '\n' ' '). Coverage claimed by this run is not real."
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
    echo "| Targets dropped as unreachable | ${unresponsive_count} |"
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
    --argjson matches "$matches" \
    '{label: $label, verdict: $verdict, templates_loaded: $templates,
      targets_loaded: $targets, targets_configured: $expected_targets,
      templates_floor: $min_templates, targets_unreachable: $unreachable,
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
