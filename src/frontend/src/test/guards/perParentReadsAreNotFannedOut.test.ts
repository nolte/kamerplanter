import { describe, it, expect } from 'vitest';

/**
 * #3015 slice B (audit findings A-05, B-06, B-18) — a per-parent list read is not called once per parent.
 *
 * **The defect class.** Some list endpoints answer the children of one parent: the plants of one run
 * (`listRunPlants`), the beds of one site (`listBeds`), the locations of one site (`listLocations`). A view that
 * needs the children of *every* parent and calls the reader in a loop over the parents sends one request per parent:
 * the plant list read the plants of every run of the tenant to label its rows, the care log read the beds of up to 50
 * site pages, three pickers read the locations of every site. Each was O(parents) requests for a set the server
 * answers in one paged read — `planting_runs` on the plant rows, `GET /locations/options`.
 *
 * **The rule.** Outside `src/api/`, a call of a per-parent reader inside an iteration — the callback of `.map(`,
 * `.forEach(` or `.flatMap(`, or the body of a `for`/`while` loop — is a finding. A loop that is bounded on purpose
 * goes on {@link BOUNDED_FAN_OUTS} with the reason.
 *
 * **What it does not see.** A loop written as recursion or through a helper that receives the reader as an argument,
 * including the point-free form `keys.map(listRunPlants)`;
 * a reader that is not named in {@link PER_PARENT_READERS}. A new per-parent endpoint belongs on that list.
 */

const PRODUCTION_SOURCES = import.meta.glob(
  [
    '/src/**/*.ts',
    '/src/**/*.tsx',
    '!/src/api/**',
    '!/src/test/**',
    '!/src/**/*.test.ts',
    '!/src/**/*.test.tsx',
    '!/src/**/*TestKit.ts',
  ],
  { query: '?raw', import: 'default', eager: true },
) as Record<string, string>;

/** Readers that answer the children of one parent, and the projection that answers all of them at once. */
const PER_PARENT_READERS: Record<string, string> = {
  listRunPlants: '`planting_runs` on the plant list rows (`GET /plant-instances`)',
  listBeds: '`listAllLocationOptions({ isBed: true })` (`GET /locations/options?is_bed=true`)',
  listLocations: '`listAllLocationOptions()` (`GET /locations/options`)',
};

/** Fan-outs that stay, by file (path below `/src/`) and reader, each with why it is bounded. */
const BOUNDED_FAN_OUTS: Record<string, Record<string, string>> = {
  'pages/standorte/LocationDetailPage.tsx': {
    listRunPlants:
      "The plant count of each run assigned to this one location (a handful). A run's plants may stand at other " +
      'locations, so the count cannot come from the location-filtered plant list.',
  },
};

/** Code without comments; string and template contents blanked so their brackets do not count. */
function codeOnly(source: string): string {
  const withoutComments = source.replace(/\/\*[\s\S]*?\*\//g, (m) => m.replace(/[^\n]/g, ' '))
    .replace(/(^|[^:'"`\\])\/\/.*$/gm, (m, lead: string) => lead + ' '.repeat(m.length - lead.length));
  return withoutComments.replace(/(['"`])(?:\\.|(?!\1)[^\\])*\1/g, (m) => m[0] + ' '.repeat(m.length - 2) + m[0]);
}

const ITERATION_CALL = /\.(?:map|forEach|flatMap)\s*$/;
const LOOP_HEAD = /\b(?:for|while)\s*\([^{};]*(?:;[^{}]*)?\)\s*$/;

/** Whether the position `at` in `code` sits inside an iteration callback or a loop body. */
function insideIteration(code: string, at: number): boolean {
  const stack: number[] = [];
  for (let i = 0; i < at; i += 1) {
    const c = code[i];
    if (c === '(' || c === '{' || c === '[') stack.push(i);
    else if (c === ')' || c === '}' || c === ']') stack.pop();
  }
  return stack.some((open) => {
    const before = code.slice(Math.max(0, open - 200), open);
    return code[open] === '(' ? ITERATION_CALL.test(before) : code[open] === '{' && LOOP_HEAD.test(before);
  });
}

function fanOutCalls(source: string): string[] {
  const code = codeOnly(source);
  const out: string[] = [];
  for (const reader of Object.keys(PER_PARENT_READERS)) {
    for (const m of code.matchAll(new RegExp(`\\b${reader}\\s*\\(`, 'g'))) {
      if (insideIteration(code, m.index ?? 0)) out.push(reader);
    }
  }
  return out;
}

function relative(file: string): string {
  return file.replace(/^\/src\//, '');
}

function findings(file: string, source: string): string[] {
  const allowed = BOUNDED_FAN_OUTS[relative(file)] ?? {};
  return fanOutCalls(source)
    .filter((reader) => !(reader in allowed))
    .map((reader) => `${relative(file)}: ${reader} per parent — use ${PER_PARENT_READERS[reader]}`);
}

describe('per-parent reads are not fanned out (#3015 slice B)', () => {
  it('recognises the fan-out shapes this issue removed, and not a single read', () => {
    const removed = [
      // PlantInstanceListPage / WorkflowInstantiateDialog: the plants of every run.
      'runs.map((r) => limiter.run(() => listRunPlants(r.key), signal))',
      'await Promise.all(activeRuns.map(async (run) => { const p = await plantingRunApi.listRunPlants(run.key); }))',
      // historyApi: the beds of every site.
      'const perSite = await Promise.all(sites.map((site) => listBeds(site.key)));',
      // a loop body
      'for (const site of sites) { all.push(...(await siteApi.listLocations(site.key))); }',
      'sites.forEach((s) => { void listLocations(s.key); });',
    ];
    for (const snippet of removed) expect(fanOutCalls(snippet)).not.toEqual([]);

    const fine = [
      'const plants = await runApi.listRunPlants(key, true);',
      "const beds = await listBeds(siteKey); const names = beds.map((b) => b.name);",
      "const s = '.map(listLocations(x))';",
      '// sites.map((s) => listLocations(s.key))',
      'readThrough(entry, () => listBeds(siteKey))',
    ];
    for (const snippet of fine) expect(fanOutCalls(snippet)).toEqual([]);
  });

  it('scans the production sources', () => {
    expect(Object.keys(PRODUCTION_SOURCES).length).toBeGreaterThan(300);
  });

  it('no call site outside src/api/ reads the children of every parent one parent at a time', () => {
    expect(Object.entries(PRODUCTION_SOURCES).flatMap(([file, source]) => findings(file, source))).toEqual([]);
  });

  it('every bounded fan-out on the allowlist still exists — a fixed one leaves the list', () => {
    const stale: string[] = [];
    for (const [file, readers] of Object.entries(BOUNDED_FAN_OUTS)) {
      const source = PRODUCTION_SOURCES[`/src/${file}`];
      const found = source === undefined ? [] : fanOutCalls(source);
      for (const reader of Object.keys(readers)) if (!found.includes(reader)) stale.push(`${file}: ${reader}`);
    }
    expect(stale).toEqual([]);
  });
});
