import { describe, expect, it } from 'vitest';

/**
 * #1503 / #1484 — a filter over a capped list must be a **query**, not a
 * narrowing of the answer.
 *
 * `GET /tasks/queue` answers at most `TaskService.QUEUE_LIMIT` (200) rows and the
 * completed list at most the 100 the page asks for. Every narrowing applied
 * *after* that cut can only ever see what the cap already let through, so a
 * matching row sorting past the cut is invisible and the page reports "nothing
 * here" for a filter that has matches. #1484 closed it for the plant filter,
 * #1503 for category and origin. Nothing structural stopped the next filter from
 * arriving as a client narrowing again — this guard does.
 *
 * Two halves, because the defect has two ends:
 *
 * 1. **Completeness** — every field of `QueueScope` is read by *both* thunks
 *    that build a query from it. A filter parked in the scope but never sent is
 *    the same blindness with an extra step. The field list is read out of the
 *    interface, so a fourth filter extends the guard by existing.
 * 2. **Absence** — the queue page performs no narrowing of `taskQueue` /
 *    `completedTasks` on a field the scope already asks the server for.
 *
 * The detector below is exercised against fixtures in both directions at the end
 * of this file: a guard nobody has seen fail is a guard nobody has measured.
 */

const SLICE = import.meta.glob('/src/store/slices/tasksSlice.ts', {
  query: '?raw',
  import: 'default',
  eager: true,
}) as Record<string, string>;

const QUEUE_PAGE = import.meta.glob('/src/pages/aufgaben/TaskQueuePage.tsx', {
  query: '?raw',
  import: 'default',
  eager: true,
}) as Record<string, string>;

const sliceSource = Object.values(SLICE)[0];
const pageSource = Object.values(QUEUE_PAGE)[0];

/** `plantKey` → `plant_key`: the scope's field name in its wire spelling. */
function wireName(field: string): string {
  return field.replace(/[A-Z]/g, (c) => `_${c.toLowerCase()}`);
}

/** The fields of the `QueueScope` interface, read out of the source. */
export function queueScopeFields(source: string): string[] {
  const body = source.match(/export interface QueueScope \{([\s\S]*?)\n\}/)?.[1];
  if (!body) throw new Error('QueueScope interface not found — the guard is reading the wrong file.');
  return [...body.matchAll(/^\s*(\w+)\s*[?:]/gm)].map((m) => m[1]);
}

/** The body of one `createAsyncThunk` call, found by the action type it declares. */
export function thunkBody(source: string, actionType: string): string {
  const start = source.indexOf(`'${actionType}'`);
  if (start < 0) throw new Error(`thunk ${actionType} not found — the guard is reading the wrong file.`);
  const rest = source.slice(start);
  const end = rest.indexOf('\n});');
  return rest.slice(0, end < 0 ? rest.length : end);
}

/**
 * Row variables a narrowing could be written on: anything iterated out of, or
 * mapped over, one of `listNames`.
 *
 * Covered spellings — the point being that the *instrument* must not have the
 * gap the guard is about:
 *
 *  * `for (const task of taskQueue)`
 *  * `taskQueue.filter((task) => …)`, `.filter((task: TaskItem) => …)`
 *  * `.some(`, `.every(`, `.find(`, `.map(`, `.reduce(` over the same list
 *  * a local alias — `const rows = taskQueue;` then `rows.filter((task) => …)`
 */
export function rowVariables(source: string, listNames: string[]): string[] {
  const names = new Set(listNames);
  // Aliases first, so `const rows = completedTasks` is followed through.
  for (const m of source.matchAll(/const\s+(\w+)\s*(?::[^=\n]+)?=\s*(\w+)\s*;/g)) {
    if (names.has(m[2])) names.add(m[1]);
  }
  const rows = new Set<string>();
  for (const list of names) {
    for (const m of source.matchAll(new RegExp(`for\\s*\\(\\s*const\\s+(\\w+)\\s+of\\s+${list}\\b`, 'g'))) {
      rows.add(m[1]);
    }
    const iterator = `${list}\\s*\\.\\s*(?:filter|some|every|find|findIndex|map|flatMap|reduce)\\s*\\(\\s*\\(?\\s*(\\w+)`;
    for (const m of source.matchAll(new RegExp(iterator, 'g'))) {
      rows.add(m[1]);
    }
  }
  return [...rows];
}

/**
 * Lines on which a row variable is tested against `field` **by a value the code
 * does not spell out** — i.e. by a selection rather than by a domain constant.
 *
 * The distinction is the one that matters and it is not cosmetic: the page
 * legitimately asks `task.category === 'care_reminder'` to de-duplicate care
 * rows against the care dashboard, and `TaskOriginBadge` asks
 * `origin === 'user'` to decide a badge. Neither is a *filter*: the value is
 * fixed in the source, not picked by a user, so no cap can hide a row from it.
 * A comparison against an identifier is the narrowing shape (#1503).
 *
 * Spellings covered: `===`, `!==`, `==`, `!=` in either operand order,
 * `.includes(row.field)`, `.has(row.field)`, a `switch` discriminant, and a bare
 * truthiness test in a guard.
 */
export function narrowingLines(source: string, rows: string[], field: string): string[] {
  if (!rows.length) return [];
  const rowAlternatives = rows.map((r) => r.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')).join('|');
  const member = `(?:${rowAlternatives})\\s*(?:\\?\\.|\\.)\\s*${field}\\b`;
  // Not a quote and not a number: the operand is a variable, so the value is a
  // selection rather than a constant of the domain.
  const variable = `[A-Za-z_$][\\w$.?\\[\\]']*`;
  const patterns = [
    new RegExp(`${member}\\s*(?:===|!==|==|!=)\\s*${variable}`),
    new RegExp(`(?<!['"])\\b${variable}\\s*(?:===|!==|==|!=)\\s*${member}`),
    new RegExp(`\\.\\s*(?:includes|has)\\s*\\(\\s*${member}`),
    new RegExp(`switch\\s*\\(\\s*${member}`),
    new RegExp(`(?:if|&&|\\|\\|)\\s*\\(?\\s*!?${member}\\s*\\)?\\s*(?:\\)|&&|\\|\\||\\?)`),
  ];
  return source
    .split('\n')
    .filter((line) => !line.trim().startsWith('//') && !line.trim().startsWith('*'))
    .filter((line) => patterns.some((p) => p.test(line)))
    .map((line) => line.trim());
}

describe('#1503 — the queue scope is asked of the server, not applied to its answer', () => {
  describe('every scope field reaches both queries', () => {
    const fields = queueScopeFields(sliceSource);

    it('the interface is non-empty, so an empty field list cannot pass vacuously', () => {
      expect(fields.length).toBeGreaterThanOrEqual(3);
      expect(fields).toContain('category');
      expect(fields).toContain('origin');
    });

    it.each(['tasks/fetchQueue', 'tasks/fetchCompleted'])('%s reads every scope field', (actionType) => {
      const body = thunkBody(sliceSource, actionType);
      const missing = fields.filter((f) => !new RegExp(`\\bscope\\.${f}\\b`).test(body));
      expect(missing, `${actionType} never reads scope.${missing.join(', scope.')}`).toEqual([]);
    });
  });

  describe('the page narrows neither list on a field the query already carries', () => {
    const fields = queueScopeFields(sliceSource).map(wireName);
    const rows = rowVariables(pageSource, ['taskQueue', 'completedTasks']);

    it('the detector found the row variables it is meant to check', () => {
      // Without this the absence assertions below would be green on an empty
      // row set — a guard that measures nothing (#1155 class).
      expect(rows.length).toBeGreaterThan(0);
    });

    it.each(fields)('no narrowing of a queue row on %s', (field) => {
      expect(narrowingLines(pageSource, rows, field)).toEqual([]);
    });
  });

  describe('the detector itself', () => {
    const LIST = ['taskQueue'];

    it.each([
      ['for-of + continue', 'for (const task of taskQueue) {\n if (task.category !== picked) continue;\n}'],
      ['filter arrow', 'const x = taskQueue.filter((t) => t.category === picked);'],
      ['typed filter arrow', 'const x = taskQueue.filter((t: TaskItem) => t.category !== picked);'],
      ['via an alias', 'const rows = taskQueue;\nconst x = rows.filter((t) => t.category === picked);'],
      ['includes', 'for (const task of taskQueue) {\n if (!picked.includes(task.category)) continue;\n}'],
      ['switch', 'for (const task of taskQueue) {\n switch (task.category) { default: }\n}'],
      ['optional chain', 'const x = taskQueue.filter((t) => t?.category === picked);'],
      ['reversed operands', 'const x = taskQueue.filter((t) => picked === t.category);'],
    ])('flags a narrowing written as %s', (_name, fixture) => {
      expect(narrowingLines(fixture, rowVariables(fixture, LIST), 'category')).not.toEqual([]);
    });

    it.each([
      ['a badge reading the field off a single task', 'const label = task.origin === "user" ? a : b;'],
      [
        'a domain constant rather than a selection',
        "for (const task of taskQueue) {\n if (task.category !== 'care_reminder') continue;\n}",
      ],
      [
        'a domain constant with the operands the other way round',
        "for (const task of taskQueue) {\n if ('care_reminder' === task.category) continue;\n}",
      ],
      ['a comment describing the old narrowing', '// if (t.category !== picked) continue;'],
      ['a narrowing on a list that is not capped', 'const x = careDashboard.filter((c) => c.category === picked);'],
    ])('does not flag %s', (_name, fixture) => {
      expect(narrowingLines(fixture, rowVariables(fixture, LIST), 'category')).toEqual([]);
    });
  });
});
