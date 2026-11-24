import { describe, it, expect } from 'vitest';

/**
 * #3015 slice A (audit finding A-06) — a list read outside the API layer loads every page, or says why it does not.
 *
 * **The defect class.** A paged list endpoint (`offset`/`limit`, `limit<=200`) answers one window. A call site that
 * asks for the first window — `listPlantInstances(0, 200)`, `listPlantInstances()` (the default window of 50), or a
 * thunk argument `{ limit: 200 }` — and then treats the answer as the whole set silently drops every row past it: a
 * picker misses the plant created a moment ago, a name map labels the later rows with raw keys. 25 such sites were
 * found in one audit, the last of them failing the nightly core journey (`FeedingEventCreateDialog`).
 *
 * **The rule.** Outside `src/api/` a paged reader is called only with a variable offset (a paging loop such as
 * `fetchAllPages`); the complete set comes from its `listAll*` sibling. In `src/store/` even a variable offset is a
 * finding unless it is the page callback of `fetchAllPages`: a slice passing its thunk's window through hands every
 * `{}` dispatch the backend's default window. A literal `limit: <n>` in a call outside `src/api/` is a finding too.
 * A read that is bounded on purpose goes on {@link BOUNDED_READS} with the reason it may stop at one page.
 *
 * The paged readers are derived from `src/api/endpoints/` — every exported function whose first parameter is
 * `offset` or an inline params object with an `offset` field — so such a new endpoint is covered without editing
 * this file. Not covered: readers that take a key before the window (`getPlantFeedingHistory(plantKey, offset,
 * limit)`, `getLocationWateringLogs`, `getStates`, `getFillEvents`) or a named params type (`getNotifications`);
 * today these are per-object histories, bounded on purpose. An allowlist entry exempts its call prefix in its whole
 * file, so a second bounded call of the same reader there needs review by hand.
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

const ENDPOINT_SOURCES = import.meta.glob(['/src/api/endpoints/*.ts'], {
  query: '?raw',
  import: 'default',
  eager: true,
}) as Record<string, string>;

/** `export async function listX(offset = 0, …` or `export async function listX(params: { …offset?: number… } = {})`. */
const PAGED_SIGNATURE = /export\s+(?:async\s+)?function\s+(\w+)\s*\(\s*(?:offset\b|params\??\s*:\s*\{[^}]*\boffset\??\s*:)/g;

function pagedReaders(sources: Record<string, string>): Set<string> {
  const names = new Set<string>();
  for (const source of Object.values(sources)) {
    for (const m of source.matchAll(PAGED_SIGNATURE)) names.add(m[1]);
  }
  return names;
}

const PAGED_READERS = pagedReaders(ENDPOINT_SOURCES);

/**
 * Reads that may stop at one page, by file (path below `/src/`) and the finding's call text. Each entry carries why.
 */
const BOUNDED_READS: Record<string, Record<string, string>> = {
  'features/gardenPlanner/care/careApi.ts': {
    'listTasks(0': 'Open tasks of one garden object, capped at OBJECT_TASK_LIMIT on purpose; the queue page lists all.',
  },
  'pages/pflanzen/PlantInstanceDetailPage.tsx': {
    'listTasks(0':
      "Looks up the one pending watering reminder of one plant (at most one per reminder type); not shown as a list.",
  },
  'pages/stammdaten/SpeciesWorkflowsSection.tsx': {
    'listWorkflows(0': 'Workflow templates of one species — a handful per species; follow-up if that ever changes.',
  },
  'store/slices/tasksSlice.ts': {
    'listTasks(0':
      'Completed-task history of the queue, deliberately the latest 100 (#1484, #1503); unbounded history wants server paging, not all pages.',
  },
  'store/slices/importSlice.ts': {
    'listImportJobs(offset':
      '`fetchImportJobs` requires explicit `offset` and `limit` (no defaults), so no dispatcher gets a window it did not ask for.',
  },
  'store/slices/sitesSlice.ts': {
    'listSites(offset':
      'One-page branch kept for the offline cache, which keys a site list by its window (`siteListEntry`); every dispatcher passes `all: true`.',
  },
  'store/createListSlice.ts': {
    'limit: 50': 'Initial pagination state of the list-slice factory, not a request.',
  },
};

/** Code without its comments, so an explanation of the old form is not a finding. */
function stripComments(source: string): string {
  return source.replace(/\/\*[\s\S]*?\*\//g, '').replace(/(^|[^:'"`])\/\/.*$/gm, '$1');
}

function relative(file: string): string {
  return file.replace(/^\/src\//, '');
}

/**
 * The endpoint bindings of a file: namespace imports (`import * as plantApi from '@/api/endpoints/…'`) and named
 * imports (local name → exported name). Only a call through one of them is a reader call — a store thunk that shares
 * an endpoint's name (`fetchFertilizers`) is not.
 */
function endpointBindings(code: string): { namespaces: Set<string>; named: Map<string, string> } {
  const namespaces = new Set<string>();
  const named = new Map<string, string>();
  for (const m of code.matchAll(/import\s+\*\s+as\s+(\w+)\s+from\s+['"][^'"]*api\/endpoints\/[^'"]*['"]/g)) {
    namespaces.add(m[1]);
  }
  // The barrel `@/api` re-exports every endpoint module as a namespace (`export * as sitesApi from …`).
  for (const m of code.matchAll(/import\s+(?:type\s+)?\{([^}]*)\}\s+from\s+['"](?:@\/api|(?:\.\.?\/)+api)['"]/g)) {
    for (const part of m[1].split(',')) {
      const local = part.trim().replace(/^type\s+/, '').split(/\s+as\s+/).pop()?.trim();
      if (local) namespaces.add(local);
    }
  }
  for (const m of code.matchAll(/import\s+(?:type\s+)?\{([^}]*)\}\s+from\s+['"][^'"]*api\/endpoints\/[^'"]*['"]/g)) {
    for (const part of m[1].split(',')) {
      const [exported, local] = part.trim().replace(/^type\s+/, '').split(/\s+as\s+/);
      if (exported) named.set((local ?? exported).trim(), exported.trim());
    }
  }
  return { namespaces, named };
}

/** Every one-page read in `source`, as call strings, before the allowlist is applied. */
function oneWindowCalls(source: string, readers: Set<string>): string[] {
  const code = stripComments(source);
  const { namespaces, named } = endpointBindings(code);
  const out: string[] = [];
  // A paged reader called with no argument (its default window) or with a literal first offset.
  for (const m of code.matchAll(/\b(?:(\w+)\s*\.\s*)?(\w+)\(\s*(\)|\d+\s*[,)])/g)) {
    const [, namespace, local, rawArg] = m;
    const exported = namespace === undefined ? named.get(local) : namespaces.has(namespace) ? local : undefined;
    if (exported === undefined || !readers.has(exported)) continue;
    const firstArg = rawArg.trim();
    out.push(firstArg === ')' ? `${local}()` : `${local}(${firstArg.replace(/[,)]$/, '').trim()}`);
  }
  // A literal page size handed to a request or a thunk: `{ limit: 200 }`, `params: { …, limit: 200 }`.
  for (const m of code.matchAll(/\blimit\s*:\s*(\d+)/g)) out.push(`limit: ${m[1]}`);
  return out;
}

/**
 * A store slice that passes its thunk's paging arguments through (`list: ({ offset, limit }) => api.listX(offset,
 * limit)`): every dispatcher's `{}` then reads the backend's default window of 50 into a list view that searches and
 * sorts client-side — six list pages did (#3015). In `src/store/` any paged-reader call is one, unless it is the
 * page callback of `fetchAllPages`.
 */
function storePassThroughCalls(source: string, readers: Set<string>): string[] {
  const code = stripComments(source);
  const { namespaces, named } = endpointBindings(code);
  const out: string[] = [];
  for (const m of code.matchAll(/\b(?:(\w+)\s*\.\s*)?(\w+)\(\s*([A-Za-z_]\w*)/g)) {
    const [, namespace, local, firstArg] = m;
    const exported = namespace === undefined ? named.get(local) : namespaces.has(namespace) ? local : undefined;
    if (exported === undefined || !readers.has(exported)) continue;
    if (code.slice(Math.max(0, (m.index ?? 0) - 120), m.index).includes('fetchAllPages(')) continue;
    out.push(`${local}(${firstArg}`);
  }
  return out;
}

function allReadFindings(file: string, source: string, readers: Set<string>): string[] {
  const calls = oneWindowCalls(source, readers);
  return relative(file).startsWith('store/') ? [...calls, ...storePassThroughCalls(source, readers)] : calls;
}

function findings(file: string, source: string, readers: Set<string> = PAGED_READERS): string[] {
  const allowed = BOUNDED_READS[relative(file)] ?? {};
  return allReadFindings(file, source, readers)
    .filter((call) => !(call in allowed))
    .map((call) => `${relative(file)}: ${call}`);
}

describe('list reads load every page (#3015 slice A)', () => {
  it('scans the production sources and derives the paged readers from the endpoints', () => {
    expect(Object.keys(PRODUCTION_SOURCES).length).toBeGreaterThan(300);
    for (const name of ['listPlantInstances', 'listSites', 'listPlantingRuns', 'listTanks', 'listTasks']) {
      expect(PAGED_READERS.has(name)).toBe(true);
    }
    expect(PAGED_READERS.has('listPropagationEvents')).toBe(true);
    // An unpaged reader is not one: its no-argument call is the complete set.
    expect(PAGED_READERS.has('listLocations')).toBe(false);
  });

  it('no call site outside src/api/ reads one page as the whole set', () => {
    expect(Object.entries(PRODUCTION_SOURCES).flatMap(([file, source]) => findings(file, source))).toEqual([]);
  });

  it('every bounded read on the allowlist still exists — a fixed one leaves the list', () => {
    const stale: string[] = [];
    for (const [file, calls] of Object.entries(BOUNDED_READS)) {
      const source = PRODUCTION_SOURCES[`/src/${file}`];
      if (source === undefined) {
        stale.push(`${file}: file gone`);
        continue;
      }
      const raw = allReadFindings(`/src/${file}`, source, PAGED_READERS);
      for (const call of Object.keys(calls)) {
        if (!raw.includes(call)) stale.push(`${file}: ${call}`);
      }
    }
    expect(stale).toEqual([]);
  });

  it('detects the defect — fixtures', () => {
    const readers = new Set(['listPlantInstances', 'listSites', 'listPropagationEvents', 'fetchFertilizers']);
    const ns = "import * as plantApi from '@/api/endpoints/plantInstances';\n" +
      "import * as sitesApi from '@/api/endpoints/sites';\nimport * as api from '@/api/endpoints/propagation';\n";
    const named = "import { listPlantInstances, listSites as loadSites } from '@/api/endpoints/plantInstances';\n";
    // The nightly defect: the default window.
    expect(findings('/src/x.tsx', `${ns}plantApi.listPlantInstances().then(setPlants)`, readers)).toEqual([
      'x.tsx: listPlantInstances()',
    ]);
    // The same call chained across lines, as `FeedingEventCreateDialog` wrote it.
    expect(findings('/src/x.tsx', `${ns}plantApi\n        .listPlantInstances()\n        .then(setPlants)`, readers)).toEqual([
      'x.tsx: listPlantInstances()',
    ]);
    expect(findings('/src/x.tsx', `${named}await listPlantInstances(0, 200)`, readers)).toEqual([
      'x.tsx: listPlantInstances(0',
    ]);
    expect(findings('/src/x.tsx', `${named}await loadSites(0, 200)`, readers)).toHaveLength(1);
    expect(findings('/src/x.tsx', `${ns}sitesApi.listSites(0, 200)`, readers)).toHaveLength(1);
    expect(findings('/src/x.tsx', 'dispatch(fetchSites({ limit: 200 }))', readers)).toEqual(['x.tsx: limit: 200']);
    expect(findings('/src/x.tsx', "get('/x', { params: { state: 'active', limit: 200 } })", readers)).toHaveLength(1);
    expect(findings('/src/x.tsx', `${ns}api.listPropagationEvents({ limit: 200 })`, readers)).toHaveLength(1);
    // Through the barrel `@/api`, whose namespaces re-export the endpoint modules.
    expect(findings('/src/x.tsx', "import { sitesApi } from '@/api';\nsitesApi.listSites(0, 200)", readers)).toHaveLength(1);
    // Not findings: the all-pages reader, a paging loop, an unpaged reader, a comment, a same-named store thunk.
    expect(findings('/src/x.tsx', `${ns}plantApi.listAllPlantInstances().then(setPlants)`, readers)).toEqual([]);
    expect(
      findings('/src/x.tsx', `${named}fetchAllPages((offset, limit) => listPlantInstances(offset, limit))`, readers),
    ).toEqual([]);
    expect(findings('/src/x.tsx', `${ns}sitesApi.listSites(offset, limit)`, readers)).toEqual([]);
    expect(findings('/src/x.tsx', `${ns}sitesApi.listLocations(site.key)`, readers)).toEqual([]);
    expect(findings('/src/x.tsx', `${named}// one page: listPlantInstances(0, 200)`, readers)).toEqual([]);
    expect(
      findings('/src/x.tsx', "import { fetchFertilizers } from '@/store/slices/fertilizersSlice';\nfetchFertilizers()", readers),
    ).toEqual([]);
    // A store slice passing its thunk's paging through: the default window for every `{}` dispatch.
    const slice = "import * as api from '@/api/endpoints/plantInstances';\n";
    expect(
      findings('/src/store/slices/x.ts', `${slice}list: ({ offset, limit } = {}) => api.listPlantInstances(offset, limit)`, readers),
    ).toEqual(['store/slices/x.ts: listPlantInstances(offset']);
    expect(findings('/src/store/slices/x.ts', `${slice}list: () => api.listAllPlantInstances()`, readers)).toEqual([]);
    expect(
      findings('/src/store/slices/x.ts', `${slice}fetchAllPages((offset, limit) => api.listPlantInstances(offset, limit))`, readers),
    ).toEqual([]);
    // Outside the store the same pass-through is a paging loop's business, not a finding.
    expect(findings('/src/x.tsx', `${slice}api.listPlantInstances(offset, limit)`, readers)).toEqual([]);
    // An allowlisted bounded read is not a finding in its file, and is one anywhere else.
    const tasks = "import * as api from '@/api/endpoints/tasks';\napi.listTasks(0, 100, {})";
    expect(findings('/src/store/slices/tasksSlice.ts', tasks, new Set(['listTasks']))).toEqual([]);
    expect(findings('/src/store/slices/other.ts', tasks, new Set(['listTasks']))).toHaveLength(1);
  });
});
