import { describe, expect, it } from 'vitest';
import ts from 'typescript';

/**
 * #3013 (A-02, B-01) — a failure must not disappear without a trace.
 *
 * About sixty load paths caught their error and rendered the failure as "empty":
 * `.catch(() => {})`, `.catch(() => undefined)` or a bare `catch {}`. A failed
 * session, member or invitation list then read as "there are none", a missing
 * phase list made a phase change silently impossible, and an unreadable site
 * turned an indoor bed into a garden.
 *
 * **The rule.** A handler that *swallows* — a `catch` clause or a `.catch(cb)`
 * callback whose body is empty, is the bare value `undefined`, or consists only
 * of log calls — must carry **both**
 *
 * 1. a comment that says why swallowing is correct here, and
 * 2. a log call (`captureHandledError(...)` or `console.*`), so the failure stays
 *    visible to error tracking.
 *
 * A handler that does anything else (sets an error state, rethrows, returns a
 * fallback the caller renders) is not swallowing and is out of scope — whether
 * it renders the failure is the three-state contract's business, not this guard's.
 *
 * **Known gap.** That out-of-scope case is also the most common "empty on error"
 * shape: `.catch(() => [])`, `.catch(() => null)` or `catch { setX([]) }` turn a
 * failure into an empty list without this guard noticing, and `.catch(noop)` with
 * an identifier is not inspected at all. Those are tracked as the follow-up of
 * #3013, not covered here.
 *
 * **The allowlist** names the files that still swallow, with a count and one
 * reason each. It may only shrink: a file whose count rises fails, and a file
 * whose count falls below its entry fails too, so the entry is lowered with the
 * fix instead of leaving headroom for a new swallow.
 *
 * The detector is exercised against fixtures in both directions at the end of
 * this file — a guard nobody has seen fail is a guard nobody has measured.
 */

const SOURCES = import.meta.glob(['/src/**/*.ts', '/src/**/*.tsx'], {
  query: '?raw',
  import: 'default',
  eager: true,
}) as Record<string, string>;

function isProductionSource(path: string): boolean {
  return (
    !/\.(test|spec)\.tsx?$/.test(path) &&
    !path.endsWith('.d.ts') &&
    !path.startsWith('/src/test/') &&
    !path.includes('/__mocks__/')
  );
}

const LOG_CALL = /\b(captureHandledError|console\.(warn|error|info|debug|log))\s*\(/;
const COMMENT = /\/\/|\/\*/;

/** Whether a statement is nothing but a log call (`captureHandledError(err)`, `console.warn(...)`). */
function isLogStatement(statement: ts.Statement, source: ts.SourceFile): boolean {
  return ts.isExpressionStatement(statement) && LOG_CALL.test(statement.getText(source)) &&
    ts.isCallExpression(statement.expression);
}

interface SwallowFinding {
  line: number;
  kind: 'catch' | '.catch';
}

/** Every swallowing handler of `code` that lacks the comment or the log call. */
function findUnloggedSwallows(code: string, fileName = 'x.tsx'): SwallowFinding[] {
  const source = ts.createSourceFile(
    fileName,
    code,
    ts.ScriptTarget.Latest,
    true,
    fileName.endsWith('x') ? ts.ScriptKind.TSX : ts.ScriptKind.TS,
  );
  const findings: SwallowFinding[] = [];

  const check = (node: ts.Node, body: ts.Node, kind: SwallowFinding['kind']) => {
    let swallows: boolean;
    if (ts.isBlock(body)) {
      swallows = body.statements.every((statement) => isLogStatement(statement, source));
    } else {
      swallows = (ts.isIdentifier(body) && body.text === 'undefined') || ts.isVoidExpression(body);
    }
    if (!swallows) return;
    // The handler's own text, comments inside the braces included (`getFullText` keeps the trivia).
    const text = ts.isBlock(body) ? body.getFullText(source) : node.getFullText(source);
    if (COMMENT.test(text) && LOG_CALL.test(text)) return;
    findings.push({ line: source.getLineAndCharacterOfPosition(node.getStart(source)).line + 1, kind });
  };

  const visit = (node: ts.Node) => {
    if (ts.isCatchClause(node)) {
      check(node, node.block, 'catch');
    } else if (
      ts.isCallExpression(node) &&
      ts.isPropertyAccessExpression(node.expression) &&
      node.expression.name.text === 'catch' &&
      node.arguments.length === 1
    ) {
      const handler = node.arguments[0];
      if (ts.isArrowFunction(handler) || ts.isFunctionExpression(handler)) {
        check(node, handler.body, '.catch');
      }
    }
    ts.forEachChild(node, visit);
  };
  visit(source);
  return findings;
}

/**
 * Files that still swallow, with how many handlers and why. Shrinks only — see the header.
 *
 * Two kinds of entries:
 * - **deliberate** — best-effort work whose failure has no user-facing consequence
 *   (storage quota, a cache, a lazy translation chunk). These still lack the log call.
 * - **open #3013 follow-up** — a load whose failure renders as an empty picker or
 *   list; each needs the three-state treatment (`useAsyncOptions` + `OptionsLoadError`).
 */
const ALLOWLIST: Readonly<Record<string, { count: number; reason: string }>> = {
  '/src/api/endpoints/ai.ts': {
    count: 1,
    reason:
      'deliberate: a non-JSON error body falls through to the status-only ChatStreamError',
  },
  '/src/auth/AuthProvider.tsx': {
    count: 2,
    reason:
      'deliberate: an unauthenticated bootstrap is the normal anonymous state, not a failure',
  },
  '/src/components/ai/AiChatDrawer.tsx': {
    count: 1,
    reason:
      'deliberate: the streamed answer stays; only its metadata could not be parsed',
  },
  '/src/components/ai/DailyTipCard.tsx': {
    count: 1,
    reason:
      'deliberate: browser storage unavailable (private mode, quota) — the in-memory state applies; logging every blocked storage access would flood error tracking',
  },
  '/src/components/dashboard/widgets/PlantGridWidget.tsx': {
    count: 1,
    reason:
      'deliberate: browser storage unavailable (private mode, quota) — the in-memory state applies; logging every blocked storage access would flood error tracking',
  },
  '/src/components/identification/PlantIdentificationDialog.tsx': {
    count: 1,
    reason:
      'deliberate: browser storage unavailable (private mode, quota) — the in-memory state applies; logging every blocked storage access would flood error tracking',
  },
  '/src/components/layout/NotificationBell.tsx': {
    count: 1,
    reason:
      'open #3013 follow-up: the bell keeps a stale unread count without saying so',
  },
  '/src/components/layout/NotificationDrawer.tsx': {
    count: 3,
    reason:
      'open #3013 follow-up: a failed notification load or mark-read reads as an empty/unchanged drawer',
  },
  '/src/features/gardenPlanner/editor/tools/useEditorTools.ts': {
    count: 2,
    reason:
      'deliberate: pointer capture of a synthetic or released pointer throws; the gesture still works inside the canvas',
  },
  '/src/features/gardenPlanner/editor/useAttentionFilter.ts': {
    count: 1,
    reason:
      'deliberate: browser storage unavailable (private mode, quota) — the in-memory state applies; logging every blocked storage access would flood error tracking',
  },
  '/src/features/gardenPlanner/editor/useAutoSave.ts': {
    count: 1,
    reason:
      'deliberate: browser storage unavailable (private mode, quota) — the in-memory state applies; logging every blocked storage access would flood error tracking',
  },
  '/src/features/gardenPlanner/editor/useLayerPrefs.ts': {
    count: 1,
    reason:
      'deliberate: browser storage unavailable (private mode, quota) — the in-memory state applies; logging every blocked storage access would flood error tracking',
  },
  '/src/features/gardenPlanner/editor/useLengthUnit.ts': {
    count: 1,
    reason:
      'deliberate: browser storage unavailable (private mode, quota) — the in-memory state applies; logging every blocked storage access would flood error tracking',
  },
  '/src/features/gardenPlanner/editor/useSingleKeyShortcuts.ts': {
    count: 1,
    reason:
      'deliberate: browser storage unavailable (private mode, quota) — the in-memory state applies; logging every blocked storage access would flood error tracking',
  },
  '/src/features/gardenPlanner/field/fieldPrefs.ts': {
    count: 1,
    reason:
      'deliberate: browser storage unavailable (private mode, quota) — the in-memory state applies; logging every blocked storage access would flood error tracking',
  },
  '/src/features/gardenPlanner/offline/planCache.ts': {
    count: 2,
    reason:
      'deliberate: the plan cache is best effort (quota, private mode); the network read already succeeded',
  },
  '/src/features/gardenPlanner/offline/queue.ts': {
    count: 2,
    reason:
      "deliberate: a listener's failure must not stop a queued write; a notice may show once more",
  },
  '/src/features/gardenPlanner/offline/sync.ts': {
    count: 1,
    reason:
      'deliberate: background sync registration without permission/worker; the other sync triggers remain',
  },
  '/src/features/gardenPlanner/planting/plantingSubmit.ts': {
    count: 1,
    reason:
      'deliberate: browser storage unavailable (private mode, quota) — the in-memory state applies; logging every blocked storage access would flood error tracking',
  },
  '/src/features/gardenPlanner/planting/usePlantStates.ts': {
    count: 1,
    reason:
      'open #3013 follow-up: the plant-state wires of a bed silently stay empty on a failed load',
  },
  '/src/features/gardenPlanner/zones/useZoneData.ts': {
    count: 1,
    reason:
      'open #3013 follow-up: zone task data silently stays empty on a failed load',
  },
  '/src/hooks/useCountdownTimer.ts': {
    count: 1,
    reason:
      'deliberate: the audio cue is optional; the timer works without it',
  },
  '/src/hooks/useServerFavorites.ts': {
    count: 1,
    reason:
      'open #3013 follow-up: server favourites fall back to the local set without telling the user',
  },
  '/src/hooks/useTableState.ts': {
    count: 2,
    reason:
      'deliberate: browser storage unavailable (private mode, quota) — the in-memory state applies; logging every blocked storage access would flood error tracking',
  },
  '/src/lib/dashboardLayoutStorage.ts': {
    count: 3,
    reason:
      'deliberate: browser storage unavailable (private mode, quota) — the in-memory state applies; logging every blocked storage access would flood error tracking',
  },
  '/src/lib/kioskPreferenceStorage.ts': {
    count: 1,
    reason:
      'deliberate: browser storage unavailable (private mode, quota) — the in-memory state applies; logging every blocked storage access would flood error tracking',
  },
  '/src/lib/moduleVisibilityStorage.ts': {
    count: 2,
    reason:
      'deliberate: browser storage unavailable (private mode, quota) — the in-memory state applies; logging every blocked storage access would flood error tracking',
  },
  '/src/lib/pushSubscription.ts': {
    count: 1,
    reason:
      'deliberate: unsubscribing push on sign-out is best effort and must never block the sign-out',
  },
  '/src/main.tsx': {
    count: 1,
    reason:
      'deliberate: the app mounts even if i18n init fails; initI18n reports its own load errors',
  },
  '/src/pages/aufgaben/TaskDetailPage.tsx': {
    count: 2,
    reason:
      'open #3013 follow-up: comments and history of a task read as empty on a failed load',
  },
  '/src/pages/aufgaben/WorkflowDetailPage.tsx': {
    count: 2,
    reason:
      'open #3013 follow-up: breadcrumb species and workflow executions read as absent on a failed load',
  },
  '/src/pages/aufgaben/WorkflowInstantiateDialog.tsx': {
    count: 2,
    reason:
      'open #3013 follow-up: a run/site whose targets fail to load is skipped from the picker without a word',
  },
  '/src/pages/auth/AccountSettingsPage.tsx': {
    count: 1,
    reason:
      'open #3013 follow-up: the admin system settings read as unset on a failed load',
  },
  '/src/pages/auth/EmailChangeCard.tsx': {
    count: 2,
    reason:
      'deliberate: browser storage unavailable (private mode, quota) — the in-memory state applies; logging every blocked storage access would flood error tracking',
  },
  '/src/pages/auth/NotificationSettingsTab.tsx': {
    count: 1,
    reason:
      'open #3013 follow-up: failed preferences load shows the defaults as if they were stored',
  },
  '/src/pages/duengung/NutrientPlanAssignDialog.tsx': {
    count: 2,
    reason:
      'open #3013 follow-up: plan list load failure reads as empty; the save path is handled by the parent',
  },
  '/src/pages/durchlaeufe/PlantingRunCreateDialog.tsx': {
    count: 1,
    reason:
      'open #3013 follow-up: a load failure renders as an empty list/picker — needs useAsyncOptions + OptionsLoadError',
  },
  '/src/pages/durchlaeufe/PlantingRunDetailPage.tsx': {
    count: 4,
    reason:
      'open #3013 follow-up: a load failure renders as an empty list/picker — needs useAsyncOptions + OptionsLoadError',
  },
  '/src/pages/durchlaeufe/SuccessionPlanDialog.tsx': {
    count: 1,
    reason:
      'open #3013 follow-up: a load failure renders as an empty list/picker — needs useAsyncOptions + OptionsLoadError',
  },
  '/src/pages/pflanzen/PlantInstanceDetailPage.tsx': {
    count: 2,
    reason:
      'open #3013 follow-up: secondary sections (site, plan) read as empty on a failed load',
  },
  '/src/pages/stammdaten/BotanicalFamilyDetailPage.tsx': {
    count: 1,
    reason:
      "open #3013 follow-up: the family's species list reads as empty on a failed load",
  },
  '/src/pages/stammdaten/CropRotationPage.tsx': {
    count: 1,
    reason:
      'open #3013 follow-up: a load failure renders as an empty list/picker — needs useAsyncOptions + OptionsLoadError',
  },
  '/src/pages/stammdaten/CultivarDetailPage.tsx': {
    count: 1,
    reason:
      "open #3013 follow-up: a failed lifecycle load reads as 'no lifecycle yet'",
  },
  '/src/pages/stammdaten/species-detail/SpeciesCropRotationTab.tsx': {
    count: 1,
    reason:
      'open #3013 follow-up: a load failure renders as an empty list/picker — needs useAsyncOptions + OptionsLoadError',
  },
  '/src/pages/standorte/SiteDetailPage.tsx': {
    count: 1,
    reason:
      'open #3013 follow-up: the sensors section reads as empty on a failed load',
  },
  '/src/pwa/offlineData.ts': {
    count: 3,
    reason:
      'deliberate: clearing offline data notifies listeners/channels/worker best effort; the database is cleared regardless',
  },
  '/src/pwa/storageWipe.ts': {
    count: 3,
    reason:
      'deliberate: wiping storage tolerates unavailable IndexedDB/Cache Storage — nothing was stored there',
  },
  '/src/store/sessionListener.ts': {
    count: 1,
    reason:
      'deliberate: browser storage unavailable (private mode, quota) — the in-memory state applies; logging every blocked storage access would flood error tracking',
  },
  '/src/store/slices/tenantSlice.ts': {
    count: 4,
    reason:
      'deliberate: browser storage unavailable (private mode, quota) — the in-memory state applies; logging every blocked storage access would flood error tracking',
  },
  '/src/sw.ts': {
    count: 4,
    reason:
      'deliberate: the service worker has no error tracking; each catch keeps the in-memory state or retries on the next navigation',
  },
  '/src/theme/ThemeContext.tsx': {
    count: 1,
    reason:
      'deliberate: browser storage unavailable (private mode, quota) — the in-memory state applies; logging every blocked storage access would flood error tracking',
  },
  '/src/utils/stepUpReauth.ts': {
    count: 2,
    reason:
      'deliberate: browser storage unavailable (private mode, quota) — the in-memory state applies; logging every blocked storage access would flood error tracking',
  },
};

function measure(): Map<string, number> {
  const counts = new Map<string, number>();
  for (const [path, code] of Object.entries(SOURCES)) {
    if (!isProductionSource(path)) continue;
    const findings = findUnloggedSwallows(code, path);
    if (findings.length > 0) counts.set(path, findings.length);
  }
  return counts;
}

describe('swallowed errors carry a reason and a log call (#3013)', () => {
  const counts = measure();

  it('no file swallows more handlers than its allowlist entry permits', () => {
    const over = [...counts]
      .filter(([path, count]) => count > (ALLOWLIST[path]?.count ?? 0))
      .map(([path, count]) => {
        const lines = findUnloggedSwallows(SOURCES[path], path).map((f) => f.line).join(', ');
        return `${path}: ${count} > ${ALLOWLIST[path]?.count ?? 0} (lines ${lines})`;
      });
    expect(over).toEqual([]);
  });

  it('the allowlist has no stale headroom — lower the entry with the fix', () => {
    const stale = Object.entries(ALLOWLIST)
      .filter(([path, entry]) => (counts.get(path) ?? 0) < entry.count)
      .map(([path, entry]) => `${path}: ${counts.get(path) ?? 0} < ${entry.count}`);
    expect(stale).toEqual([]);
  });

  it('every allowlist entry gives a reason', () => {
    const missing = Object.entries(ALLOWLIST)
      .filter(([, entry]) => entry.reason.trim().length < 10)
      .map(([path]) => path);
    expect(missing).toEqual([]);
  });

  it('scans a realistic share of the source tree', () => {
    const scanned = Object.keys(SOURCES).filter(isProductionSource);
    expect(scanned.length).toBeGreaterThan(500);
  });
});

describe('findUnloggedSwallows — fixtures', () => {
  const FLAGGED: [string, string][] = [
    ['an empty .catch arrow', 'p.then(f).catch(() => {});'],
    ['a .catch returning undefined', 'p.catch(() => undefined);'],
    ['a .catch returning void 0', 'p.catch(() => void 0);'],
    ['an empty catch clause', 'try { f(); } catch { }'],
    ['an empty catch clause with only a comment', 'try { f(); } catch { /* ignore */ }'],
    ['a log call without a reason', 'try { f(); } catch (e) { captureHandledError(e); }'],
    ['a reason without a log call', 'p.catch(() => {\n  // not needed\n});'],
    ['a function-expression handler', 'p.catch(function () {});'],
  ];
  const ACCEPTED: [string, string][] = [
    ['a reason plus captureHandledError', 'p.catch((e) => {\n  // display enrichment only\n  captureHandledError(e);\n});'],
    ['a reason plus console.warn in a catch clause', 'try { f(); } catch (e) {\n  // best effort\n  console.warn(e);\n}'],
    ['a handler that sets an error state', 'p.catch(() => setError(true));'],
    ['a handler that rethrows', 'try { f(); } catch (e) { throw e; }'],
    ['a handler that returns a rendered fallback', 'p.catch(() => null);'],
  ];

  it.each(FLAGGED)('flags %s', (_name, code) => {
    expect(findUnloggedSwallows(code)).toHaveLength(1);
  });

  it.each(ACCEPTED)('accepts %s', (_name, code) => {
    expect(findUnloggedSwallows(code)).toEqual([]);
  });
});
