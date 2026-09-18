import { describe, expect, it } from 'vitest';
import { MACHINE_TASK_ORIGINS } from '@/api/types';

/**
 * #1503 / #1484 — a filter over a capped list must be a **query**, not a
 * narrowing of the answer.
 *
 * `GET /tasks/queue` answers at most `TaskService.QUEUE_LIMIT` (200) rows and the
 * completed list at most the 100 the page asks for. Every narrowing applied
 * *after* that cut can only ever see what the cap already let through, so a
 * matching row sorting past the cut is invisible and the page reports "nothing
 * here" for a filter that has matches. #1484 closed it for the plant filter,
 * #1503 for category and origin.
 *
 * Two halves, because a filter in the scope has two ends:
 *
 * 1. **Completeness** — every field of `QueueScope` is read by *both* thunks
 *    that build a query from it. A filter parked in the scope but never sent is
 *    the same blindness with an extra step. The field list is read out of the
 *    interface, so a fourth field extends the guard by existing.
 * 2. **Absence** — no line of the queue page both reads a queue row and mentions
 *    one of the selectors the page destructures out of `queueScope`. That is the
 *    exact shape of the three lines #1484/#1503 deleted, including
 *    `originFilter === 'machine' && task.origin === 'user'`, where the row is
 *    compared against a *literal* and only the other operand names the selection.
 *
 * **What this does not cover, deliberately.** It is scoped to the scope: a
 * *new* filter introduced as component state and never added to `QueueScope`
 * would be invisible to both halves. Detecting that needs to tell
 * `actionLoading === task.key` (per-row UI state, legitimate) from
 * `myNewFilter === task.field` (a narrowing), which the same-line read here
 * cannot do — `renderTaskCard`'s parameter is also called `task`. What the guard
 * does guarantee is that a filter which *is* in the scope is asked of the server
 * and not applied to its answer, and the completeness half is what makes adding
 * a filter to the scope the path of least resistance.
 *
 * The detector is exercised against fixtures in both directions at the end of
 * this file, including the three deleted lines as positive fixtures: a guard
 * nobody has seen fail is a guard nobody has measured.
 */

const SLICE = import.meta.glob('/src/store/slices/tasksSlice.ts', {
  query: '?raw',
  import: 'default',
  eager: true,
}) as Record<string, string>;

const TYPES = import.meta.glob('/src/api/types.ts', {
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
const typesSource = Object.values(TYPES)[0];
const pageSource = Object.values(QUEUE_PAGE)[0];

/** The members of a string-literal union declared in `types.ts`. */
export function unionMembers(source: string, name: string): string[] {
  const declaration = source.match(new RegExp(`export type ${name} =([^;]+);`))?.[1];
  if (!declaration) throw new Error(`union ${name} not found — the guard is reading the wrong file.`);
  return [...declaration.matchAll(/'([^']+)'/g)].map((m) => m[1]);
}

/**
 * The names the page uses for the scope's fields, read out of its destructuring
 * of `queueScope` — `const { plantKey: filterPlantKey, … } = queueScope;`.
 *
 * Read rather than hard-coded because these are what a narrowing would be
 * written against, and a rename that this guard did not follow would silently
 * switch it off.
 */
export function scopeSelectors(source: string): string[] {
  const destructuring = source.match(/const \{([^}]*)\}\s*=\s*queueScope\s*;/)?.[1];
  if (!destructuring) {
    throw new Error('the page no longer destructures queueScope — the guard is reading the wrong thing.');
  }
  return [...destructuring.matchAll(/(?:\w+\s*:\s*)?(\w+)\s*(?:,|$)/g)].map((m) => m[1]);
}

/** The fields of the `QueueScope` interface, read out of the source. */
export function queueScopeFields(source: string): string[] {
  const body = source.match(/export interface QueueScope \{([\s\S]*?)\n\}/)?.[1];
  if (!body) throw new Error('QueueScope interface not found — the guard is reading the wrong file.');
  return [...body.matchAll(/^\s*(\w+)\s*[?:]/gm)].map((m) => m[1]);
}

/** Source with `//` and block comments removed. */
function stripComments(source: string): string {
  return source.replace(/\/\*[\s\S]*?\*\//g, '').replace(/\/\/[^\n]*/g, '');
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
 * The argument text of the API call inside a thunk body — everything between
 * `api.<something>(` and its matching `)`.
 *
 * Mentioning `scope.category` *somewhere* in the thunk is not the property that
 * matters; reading it and then not passing it on is precisely the "parked but
 * never sent" state the completeness half exists to rule out. So the check is
 * made against what the request actually carries.
 */
export function apiCallArguments(body: string): string {
  const open = body.search(/\bapi\.\w+\s*\(/);
  if (open < 0) throw new Error('no api.* call in this thunk — the guard is reading the wrong body.');
  const from = body.indexOf('(', open);
  let depth = 0;
  for (let i = from; i < body.length; i += 1) {
    if (body[i] === '(') depth += 1;
    if (body[i] === ')') {
      depth -= 1;
      // Comments are stripped, because they are the one place a scope field can
      // appear inside the argument list while not being sent. Measured: parking
      // `scope.category` in a comment there left this check green.
      if (depth === 0) return stripComments(body.slice(from + 1, i));
    }
  }
  throw new Error('unbalanced api.* call — the guard cannot read its arguments.');
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
 * Lines that both read a **queue row** and mention a **scope selector**.
 *
 * That conjunction is the narrowing shape, and it is what an operand-based rule
 * misses. The three lines #1484/#1503 deleted were
 *
 *     if (filterCategory && task.category !== filterCategory) continue;
 *     if (originFilter === 'machine' && task.origin === 'user') continue;
 *     if (filterPlantKey && entry.plant_key !== filterPlantKey) continue;
 *
 * — the middle one compares the row against a *literal*, so "row field compared
 * to an identifier" does not see it, while "row field and a selector on one
 * line" does.
 *
 * What stays out: `task.category === 'care_reminder'` (the care de-duplication
 * rule) and `TaskOriginBadge`'s `origin === 'user'` mention no selector, and
 * `filterCategory !== 'care_reminder'` in the care loop reads no queue row.
 */
export function narrowingLines(
  source: string,
  rows: string[],
  rowExpressions: string[],
  selectors: string[],
): string[] {
  if (!rows.length || !rowExpressions.length || !selectors.length) return [];
  const escape = (v: string) => v.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  const rowAlternatives = rows.map(escape).join('|');
  const fieldAlternatives = rowExpressions.map(escape).join('|');
  const member = new RegExp(`(?:${rowAlternatives})\\s*(?:\\?\\.|\\.)\\s*(?:${fieldAlternatives})\\b`);
  const selector = new RegExp(`\\b(?:${selectors.map(escape).join('|')})\\b`);
  // Comments out, whole and trailing: a description of the deleted narrowing is
  // not the narrowing, and a trailing comment naming a selector would otherwise
  // make an innocent line look like one.
  return stripComments(source)
    .split('\n')
    .filter((line) => !line.trim().startsWith('*'))
    .filter((line) => member.test(line) && selector.test(line))
    .map((line) => line.trim());
}

/**
 * Which **row** expressions carry each scope field.
 *
 * Explicit rather than derived: a scope field and the row attribute it selects
 * on are not the same name and a mechanical transform gets it wrong — `plantKey`
 * would become `plant_key`, which no `TaskItem` has, so the plant half of the
 * guard would test nothing at all while looking complete. A field with no entry
 * here throws, so adding one to `QueueScope` forces the decision rather than
 * silently shrinking the check.
 */
const ROW_EXPRESSIONS: Record<string, string[]> = {
  // `entity_key` under `entity_type === 'plant_instance'` is how a task names its
  // plant; `plant_key` is how a *care dashboard* entry does (that source is not
  // capped and is narrowed on purpose — see the page).
  plantKey: ['entity_key', 'plant_key'],
  category: ['category'],
  origin: ['origin'],
};

function rowExpressionsFor(field: string): string[] {
  const expressions = ROW_EXPRESSIONS[field];
  if (!expressions) {
    throw new Error(
      `QueueScope grew the field "${field}" and nobody said which row attribute it selects on — ` +
        'add it to ROW_EXPRESSIONS so the absence check covers it.',
    );
  }
  return expressions;
}

describe('#1503 — the queue scope is asked of the server, not applied to its answer', () => {
  describe('every scope field reaches both queries', () => {
    const fields = queueScopeFields(sliceSource);

    it('the interface is non-empty, so an empty field list cannot pass vacuously', () => {
      expect(fields.length).toBeGreaterThanOrEqual(3);
      expect(fields).toContain('category');
      expect(fields).toContain('origin');
    });

    it.each(['tasks/fetchQueue', 'tasks/fetchCompleted'])(
      '%s passes every scope field into the request it issues',
      (actionType) => {
        const args = apiCallArguments(thunkBody(sliceSource, actionType));
        const missing = fields.filter((f) => !new RegExp(`\\bscope\\.${f}\\b`).test(args));
        expect(
          missing,
          `${actionType} does not put scope.${missing.join(', scope.')} into its request`,
        ).toEqual([]);
      },
    );

    it('the argument text was found, so the check cannot pass on an empty string', () => {
      for (const actionType of ['tasks/fetchQueue', 'tasks/fetchCompleted']) {
        expect(apiCallArguments(thunkBody(sliceSource, actionType)).length).toBeGreaterThan(10);
      }
    });
  });

  describe('the machine partition covers every non-user origin', () => {
    // `satisfies readonly Exclude<TaskOrigin,'user'>[]` proves every listed value
    // is a machine origin; it cannot prove the list is *complete*. Completeness
    // is the direction that hurts: a fourth origin added to the union and not to
    // the constant makes "machine-generated" quietly stop returning the new kind,
    // and nothing else in the tree would notice.
    const origins = unionMembers(typesSource, 'TaskOrigin');

    it('the union was parsed, so the comparison cannot pass vacuously', () => {
      expect(origins).toContain('user');
      expect(origins.length).toBeGreaterThan(1);
    });

    it('lists exactly the union minus "user"', () => {
      expect([...MACHINE_TASK_ORIGINS].sort()).toEqual(origins.filter((o) => o !== 'user').sort());
    });
  });

  describe('the page narrows neither list on a field the query already carries', () => {
    const fields = queueScopeFields(sliceSource);
    const rows = rowVariables(pageSource, ['taskQueue', 'completedTasks']);
    const selectors = scopeSelectors(pageSource);

    it('the detector found the row variables and selectors it is meant to check', () => {
      // Without this the absence assertions below would be green on an empty row
      // set or an empty selector set — a guard that measures nothing (#1155).
      expect(rows.length).toBeGreaterThan(0);
      expect(selectors.length).toBe(fields.length);
    });

    it.each(fields)('no line reads a queue row and the %s selector at once', (field) => {
      expect(narrowingLines(pageSource, rows, rowExpressionsFor(field), selectors)).toEqual([]);
    });
  });

  describe('the detector itself', () => {
    const LIST = ['taskQueue'];
    const SELECTORS = ['filterCategory', 'originFilter', 'filterPlantKey'];
    const FIELDS = ['category', 'origin', 'entity_key'];

    /** Run the detector the way the checks above run it. */
    function flagged(fixture: string): string[] {
      const rows = rowVariables(fixture, LIST);
      return narrowingLines(fixture, rows, FIELDS, SELECTORS);
    }

    describe('the three lines #1484 and #1503 deleted', () => {
      // The regression cases proper: each of these stood in `TaskQueuePage` and
      // is exactly what must never come back.
      it.each([
        [
          'the category narrowing',
          'for (const task of taskQueue) {\n  if (filterCategory && task.category !== filterCategory) continue;\n}',
        ],
        [
          'the origin narrowing, whose row operand is a literal',
          "for (const task of taskQueue) {\n  if (originFilter === 'machine' && task.origin === 'user') continue;\n}",
        ],
        [
          'the completed-list narrowing',
          'const done = completedTasks.filter((task) => {\n  if (filterCategory && task.category !== filterCategory) return false;\n});',
        ],
      ])('flags %s', (_name, fixture) => {
        const rows = rowVariables(fixture, ['taskQueue', 'completedTasks']);
        expect(rows.length).toBeGreaterThan(0);
        expect(narrowingLines(fixture, rows, FIELDS, SELECTORS)).not.toEqual([]);
      });
    });

    it.each([
      ['for-of + continue', 'for (const task of taskQueue) {\n if (task.category !== filterCategory) continue;\n}'],
      ['filter arrow', 'const x = taskQueue.filter((t) => t.category === filterCategory);'],
      ['typed filter arrow', 'const x = taskQueue.filter((t: TaskItem) => t.category !== filterCategory);'],
      ['via an alias', 'const rows = taskQueue;\nconst x = rows.filter((t) => t.category === filterCategory);'],
      ['includes', 'for (const task of taskQueue) {\n if (!filterCategory.includes(task.category)) continue;\n}'],
      ['optional chain', 'const x = taskQueue.filter((t) => t?.category === filterCategory);'],
      ['reversed operands', 'const x = taskQueue.filter((t) => filterCategory === t.category);'],
      [
        'the plant selector against the row attribute that actually carries it',
        'for (const task of taskQueue) {\n if (filterPlantKey && task.entity_key !== filterPlantKey) continue;\n}',
      ],
    ])('flags a narrowing written as %s', (_name, fixture) => {
      expect(flagged(fixture)).not.toEqual([]);
    });

    describe('what it leaves alone', () => {
      // Every fixture here iterates the list for real, so `rowVariables` is
      // non-empty and the assertion cannot pass through the early return — three
      // of these used to be vacuous for exactly that reason.
      const negatives: [string, string][] = [
        [
          'a domain constant rather than a selection',
          "for (const task of taskQueue) {\n if (task.category !== 'care_reminder') continue;\n}",
        ],
        [
          'a domain constant with the operands the other way round',
          "for (const task of taskQueue) {\n if ('care_reminder' === task.category) continue;\n}",
        ],
        [
          'a selector tested on its own, with no row in sight',
          "for (const task of taskQueue) {\n items.push(task.key);\n}\nif (filterCategory && filterCategory !== 'care_reminder') continue;",
        ],
        [
          'a commented-out narrowing',
          'for (const task of taskQueue) {\n items.push(task.key);\n // if (task.category !== filterCategory) continue;\n}',
        ],
        [
          'a narrowing of a list that is not capped',
          'for (const task of taskQueue) {\n items.push(task.key);\n}\nconst x = careDashboard.filter((c) => c.category === filterCategory);',
        ],
      ];

      it.each(negatives)('does not flag %s', (_name, fixture) => {
        expect(rowVariables(fixture, LIST).length).toBeGreaterThan(0);
        expect(flagged(fixture)).toEqual([]);
      });

      it('and none of them is green merely because nothing is ever flagged', () => {
        // The control #1155 asks for: a detector that flags everything must turn
        // every negative fixture red. If one stays green under it, that fixture
        // was proving nothing.
        const flagsEverything = (fixture: string) =>
          narrowingLines(fixture, rowVariables(fixture, LIST), ['category', 'key', 'entity_key'], [
            'filterCategory',
            'keep',
            'careDashboard',
            'task',
          ]);
        for (const [name, fixture] of negatives) {
          expect(flagsEverything(fixture), name).not.toEqual([]);
        }
      });
    });
  });
});
