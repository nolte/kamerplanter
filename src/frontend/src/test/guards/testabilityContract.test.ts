/**
 * UI-NFR-022 testability contract, enforced instead of remembered (#3024).
 *
 * The 2026-11 frontend audit (bundle M12) found that what was fixed per file
 * came back in new code: dialogs without `data-testid`/`aria-labelledby`
 * (D-001/D-002 regressed since April), pages without a `-page` marker (T-02),
 * shared form wrappers that leave their controls without a testid (T-03), and
 * production code that finds elements by `data-testid` (T-05) — so renaming a
 * testid for a page object silently broke focus management. What was fixed in
 * a **shared component** stayed fixed. This guard is the shared component for
 * the rest.
 *
 * Rules (each a `describe` below):
 *
 * 1. **Dialogs** (R-011, UI-NFR-002). Every MUI `<Dialog>` — and every call of a
 *    registered pass-through wrapper ({@link DIALOG_WRAPPERS}) — carries a
 *    `data-testid` and an `aria-labelledby` whose target `id` is defined in the
 *    same file. The last half is what hand-paired id strings get wrong without
 *    anyone noticing: a typo in either half leaves the dialog unnamed.
 *    `ConfirmDialog` generates its ids with `useId`, so its many call sites need
 *    nothing.
 * 2. **Page markers** (R-005). Every `*Page.tsx` component's root element (the
 *    first element of its last top-level `return`) carries a literal
 *    `data-testid="<name>-page"`, unique across pages.
 * 3. **Form wrappers** (R-009/R-010). Every `components/form` field taking a
 *    `name: Path<T>` renders `data-testid={`form-field-${name}`}`, and every
 *    interactive element inside `components/form` carries a testid — a wrapper
 *    without one propagates the gap to every form that uses it.
 * 4. **No logic on testids** (R-004). Production code does not select by
 *    `data-testid` (`querySelector('[data-testid…')`, `closest`, `dataset.testid`,
 *    `getAttribute('data-testid')`, `getElementsBy…testid`, `sx` selectors).
 *    Focus management uses element ids or refs.
 * 5. **Naming of new ids** (R-014/R-017/R-018). No index-based testids
 *    (`-${index}`), the `-button` suffix rather than `-btn`, kebab-case. The
 *    existing violations are E2E contract (R-021: no rename without the page
 *    objects), so they are registered below — shrink-only: an entry that no
 *    longer occurs fails the test until it is deleted.
 *
 * The scan is textual (`jsxScan.ts`), like the other guards here; the detector
 * itself is pinned by fixtures in both directions at the end of this file.
 */

import { describe, expect, it } from 'vitest';
import {
  attributeValue,
  blankComments,
  hasTestId,
  labelledByResolves,
  matchLines,
  openingTags,
} from './jsxScan';

/** Every production module, as text. Tests and test helpers are not production. */
const PRODUCTION_SOURCES = import.meta.glob(
  ['/src/**/*.ts', '/src/**/*.tsx', '!/src/test/**', '!/src/**/*.test.ts', '!/src/**/*.test.tsx'],
  { query: '?raw', import: 'default', eager: true },
) as Record<string, string>;

const PAGE_SOURCES = import.meta.glob(['/src/pages/**/*Page.tsx', '/src/features/**/*Page.tsx'], {
  query: '?raw',
  import: 'default',
  eager: true,
}) as Record<string, string>;

/** `/src/pages/x/Y.tsx` → `pages/x/Y.tsx`, the form the registers are keyed on. */
function rel(path: string): string {
  return path.replace(/^\/src\//, '');
}

function productionEntries(): Array<[string, string]> {
  return Object.entries(PRODUCTION_SOURCES).map(([path, source]) => [rel(path), source]);
}

// ── 1. Dialogs ─────────────────────────────────────────────────────────────

/**
 * Components that render a raw `<Dialog {...props}>` and pass the caller's
 * `data-testid`/`aria-labelledby` through. Their own raw `<Dialog` is exempt;
 * their **call sites** are checked like a `<Dialog>`.
 *
 * `FormDialog` (#3019) is the wrapper every create/edit form dialog renders in.
 * It is listed even where it does not exist yet in a branch, so the rule holds
 * on both sides of that merge; an entry whose file is absent is simply unused.
 */
const DIALOG_WRAPPERS: ReadonlyArray<{ file: string; component: string }> = [
  { file: 'components/form/FormDialog.tsx', component: 'FormDialog' },
];

const DIALOG_TAGS = ['Dialog', ...DIALOG_WRAPPERS.map((w) => w.component)];

/** Findings of rule 1 for one file. */
export function dialogFindings(file: string, source: string): string[] {
  const wrapper = DIALOG_WRAPPERS.find((w) => w.file === file);
  const findings: string[] = [];
  for (const tag of openingTags(source, DIALOG_TAGS)) {
    if (wrapper && tag.name === 'Dialog') {
      // A pass-through wrapper must actually pass the props through.
      if (!/\{\s*\.\.\.\w+\s*\}/.test(tag.text)) {
        findings.push(`${file}:${tag.line} wrapper <Dialog> does not spread the caller's props`);
      }
      continue;
    }
    if (!hasTestId(tag.text)) findings.push(`${file}:${tag.line} <${tag.name}> without data-testid`);
    if (attributeValue(tag.text, 'aria-labelledby') === null) {
      findings.push(`${file}:${tag.line} <${tag.name}> without aria-labelledby`);
    } else if (!labelledByResolves(tag.text, source)) {
      findings.push(`${file}:${tag.line} <${tag.name}> aria-labelledby names no id defined in this file`);
    }
  }
  return findings;
}

describe('UI-NFR-022 R-011: dialogs are addressable and named', () => {
  it('every <Dialog> (and wrapper call) has data-testid and a resolving aria-labelledby', () => {
    const findings = productionEntries().flatMap(([file, source]) => dialogFindings(file, source));
    expect(findings).toEqual([]);
  });

  it('actually sees the dialogs it claims to check', () => {
    // A tokenizer bug that finds nothing would pass the rule above vacuously.
    const count = productionEntries().reduce(
      (sum, [, source]) => sum + openingTags(source, DIALOG_TAGS).length,
      0,
    );
    expect(count).toBeGreaterThan(100);
  });
});

// ── 2. Page markers ────────────────────────────────────────────────────────

/** Body of the module's `export default function`, comments blanked, or null. */
function defaultExportBody(source: string): string | null {
  const code = blankComments(source);
  const start = /export default function \w+/.exec(code);
  if (!start) return null;
  const rest = code.slice(start.index);
  const end = rest.search(/\n\}/);
  return end < 0 ? rest : rest.slice(0, end);
}

/** The `-page` marker on the root element of the default export, or why there is none. */
export function pageRootMarker(source: string): { marker: string } | { problem: string } {
  const body = defaultExportBody(source);
  if (body === null) return { problem: 'no `export default function`' };
  const returns = [...body.matchAll(/\n {2}return\s*\(?\s*(?=<)/g)];
  if (returns.length === 0) return { problem: 'no top-level JSX return' };
  const last = returns[returns.length - 1];
  const after = body.slice((last.index ?? 0) + last[0].length);
  if (after.startsWith('<>')) return { problem: 'root is a fragment' };
  const [root] = openingTags(after, ['[A-Za-z][A-Za-z0-9.]*']);
  if (!root) return { problem: 'no root element found' };
  const value = attributeValue(root.text, 'data-testid');
  if (value === null || !/data-testid="/.test(root.text)) {
    return { problem: `root <${root.name}> has no literal data-testid` };
  }
  if (!/^[a-z0-9]+(-[a-z0-9]+)*-page$/.test(value)) {
    return { problem: `root marker "${value}" is not "<kebab-name>-page"` };
  }
  return { marker: value };
}

/**
 * Pages whose marker deliberately sits below the root, with the reason. The
 * rule's point is that a test can tell the page is mounted; these satisfy it,
 * only not on the outermost element. Shrink-only.
 */
const PAGE_MARKER_BELOW_ROOT: Readonly<Record<string, string>> = {
  'pages/auth/RegisterPage.tsx':
    'root is the full-height centring Box; the marker is on the card, the element a test waits for',
  'features/gardenPlanner/history/RotationMatrixPage.tsx':
    'the route component only resolves params and renders RotationMatrixView, whose root carries the marker',
};

describe('UI-NFR-022 R-005: every page has a root -page marker', () => {
  const pages = Object.entries(PAGE_SOURCES).map(([path, source]) => [rel(path), source] as const);

  it('finds the pages', () => {
    expect(pages.length).toBeGreaterThan(80);
  });

  it('every *Page.tsx root carries a unique `<name>-page` testid', () => {
    const problems: string[] = [];
    const seen = new Map<string, string>();
    for (const [file, source] of pages) {
      const result = pageRootMarker(source);
      if ('problem' in result) {
        if (!(file in PAGE_MARKER_BELOW_ROOT)) problems.push(`${file}: ${result.problem}`);
        continue;
      }
      const other = seen.get(result.marker);
      if (other) problems.push(`${file}: marker "${result.marker}" already used by ${other}`);
      seen.set(result.marker, file);
    }
    expect(problems).toEqual([]);
  });

  it('the below-root register only lists pages that still need it, and that have a marker', () => {
    const stale = Object.keys(PAGE_MARKER_BELOW_ROOT).filter((file) => {
      const source = PAGE_SOURCES[`/src/${file}`];
      if (source === undefined) return true;
      const hasMarker = /data-testid="[a-z0-9-]+-page"/.test(blankComments(source));
      return !hasMarker || 'marker' in pageRootMarker(source);
    });
    expect(stale).toEqual([]);
  });
});

// ── 3. Form wrappers ───────────────────────────────────────────────────────

/** MUI controls a user operates. A wrapper rendering one without a testid propagates the gap. */
const INTERACTIVE = [
  'Button',
  'IconButton',
  'MenuItem',
  'Switch',
  'Checkbox',
  'Radio',
  'Tab',
  'ToggleButton',
  'TextField',
  'Select',
  'ListItemButton',
];

/** Findings of rule 3 for one `components/form` file. */
export function formWrapperFindings(file: string, source: string): string[] {
  const findings: string[] = [];
  const code = blankComments(source);
  if (/\bname:\s*Path</.test(code) && !code.includes('data-testid={`form-field-${name}`}')) {
    findings.push(`${file}: field wrapper does not render data-testid={\`form-field-\${name}\`}`);
  }
  for (const tag of openingTags(source, INTERACTIVE)) {
    if (!hasTestId(tag.text)) findings.push(`${file}:${tag.line} <${tag.name}> without data-testid`);
  }
  return findings;
}

describe('UI-NFR-022 R-009/R-010: shared form wrappers forward a testid', () => {
  const wrappers = productionEntries().filter(([file]) => /^components\/form\/[^/]+\.tsx$/.test(file));

  it('finds the wrappers', () => {
    expect(wrappers.length).toBeGreaterThan(15);
  });

  it('every field wrapper renders form-field-<name>, every control in it has a testid', () => {
    expect(wrappers.flatMap(([file, source]) => formWrapperFindings(file, source))).toEqual([]);
  });
});

// ── 4. No application logic on testids ─────────────────────────────────────

/**
 * Ways production code can find, read or style an element by its testid.
 * Comments are blanked first, so documentation may still *mention* a selector.
 */
const TESTID_LOOKUPS: ReadonlyArray<[string, RegExp]> = [
  ['attribute selector', /\[data-testid/],
  ['dataset read', /\bdataset\.testid\b/],
  ['getAttribute', /getAttribute\(\s*['"`]data-testid/],
  ['getElementsBy…', /getElementsBy\w*\([^)]*testid/i],
];

/** Findings of rule 4 for one production file. */
export function testIdLookupFindings(file: string, source: string): string[] {
  return TESTID_LOOKUPS.flatMap(([what, pattern]) =>
    matchLines(source, pattern).map((line) => `${file}:${line} selects by data-testid (${what})`),
  );
}

describe('UI-NFR-022 R-004: data-testid is a test contract, not a lookup key', () => {
  it('no production code selects, reads or styles by data-testid', () => {
    expect(productionEntries().flatMap(([file, source]) => testIdLookupFindings(file, source))).toEqual([]);
  });
});

// ── 5. Naming of new ids ───────────────────────────────────────────────────

/** Bare loop counters: a testid built from one addresses a position, not an entity (R-014). */
const INDEX_INTERPOLATION = /\$\{\s*(?:i|idx|index|j|k|n|pos|position|rowIndex)\s*(?:\+\s*1\s*)?\}/;

type NamingRule = 'index' | 'btn' | 'kebab';

/** Every `data-testid` value written as a literal or a template in `source`. */
function testIdValues(source: string): Array<{ value: string; template: boolean }> {
  const code = blankComments(source);
  const values: Array<{ value: string; template: boolean }> = [];
  for (const m of code.matchAll(/data-testid="([^"]*)"/g)) values.push({ value: m[1], template: false });
  for (const m of code.matchAll(/data-testid=\{`([^`]*)`\}/g)) values.push({ value: m[1], template: true });
  return values;
}

/** Which naming rules a single testid value breaks. */
export function namingViolations(value: string, template: boolean): NamingRule[] {
  const rules: NamingRule[] = [];
  if (template && INDEX_INTERPOLATION.test(value)) rules.push('index');
  // Interpolations are data, not naming: judge only the static skeleton.
  const skeleton = template ? value.replace(/\$\{[^}]*\}/g, 'x') : value;
  if (/-btn(?:-|$)/.test(skeleton)) rules.push('btn');
  // `form-field-<name>` / `form-option-<name>-<value>` embed the field name as is (R-010).
  const judged = /^form-(?:field|option)-/.test(skeleton) ? 'form-field-x' : skeleton;
  if (!/^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(judged)) rules.push('kebab');
  return rules;
}

/**
 * Existing ids that break a naming rule, keyed `<file>::<value>`. All of them
 * are E2E contract or registered patterns, so they stay until renamed together
 * with their page objects (R-021). Shrink-only.
 */
const NAMING_REGISTER: Readonly<Record<NamingRule, ReadonlySet<string>>> = {
  /** Index-based, no stable key available today (R-014). */
  index: new Set([
    // Photos are staged refs without a stable id until upload; the unit suite addresses them by position.
    'components/common/PhotoUpload.tsx::photo-preview-${i}',
    'components/common/PhotoUpload.tsx::photo-remove-${i}',
    'features/gardenPlanner/bed/SoilAnalysisDialog.tsx::soil-analysis-row-${position}',
    'features/gardenPlanner/bed/SoilAnalysisDialog.tsx::soil-analysis-remove-${position}',
    'features/gardenPlanner/planting/LayoutCanvas.tsx::${testId}-point-${index}',
    'pages/admin/AdminTenantImportsPage.tsx::member-mapping-remove-${index}',
    'pages/aufgaben/TaskDetailPage.tsx::task-photo-${i}',
    'pages/durchlaeufe/PlantingRunCreateDialog.tsx::remove-entry-${index}',
    'pages/giessprotokoll/WateringLogCreateDialog.tsx::remove-fertilizer-${index}',
    'pages/stammdaten/GrowingPeriodsSection.tsx::propagation-config-${idx}',
    'pages/stammdaten/SpeciesOverviewSection.tsx::overview-propagation-${idx}',
    'pages/stammdaten/species-detail/SpeciesGrowthPanel.tsx::propagation-config-${index}',
    'pages/stammdaten/species-detail/SpeciesGrowthPanel.tsx::remove-propagation-config-${index}',
    'pages/stammdaten/species-detail/SpeciesGrowthPanel.tsx::propagation-months-${index}',
    'pages/stammdaten/species-detail/SpeciesGrowthPanel.tsx::propagation-month-${index}-${m}',
    // Weather source entries carry no key of their own (source_name repeats); order is the data.
    'pages/standorte/WeatherSourceSection.tsx::weather-entry-${index}',
    'pages/standorte/WeatherSourceSection.tsx::weather-move-up-${index}',
    'pages/standorte/WeatherSourceSection.tsx::weather-move-down-${index}',
    'pages/standorte/WeatherSourceSection.tsx::weather-enable-${index}',
    'pages/standorte/WeatherSourceSection.tsx::weather-test-${index}',
    'pages/standorte/WeatherSourceSection.tsx::weather-edit-${index}',
    'pages/standorte/WeatherSourceSection.tsx::weather-remove-${index}',
    'pages/standorte/WeatherSourceSection.tsx::weather-test-result-${index}',
    'pages/standorte/WeatherSourceSection.tsx::weather-test-error-${index}',
  ]),
  /** `-btn` instead of `-button` (R-017). Page objects address them literally. */
  btn: new Set([
    'components/layout/NotificationDrawer.tsx::mark-all-read-btn',
    'components/tenants/TenantExportCard.tsx::request-tenant-export-btn',
    'pages/admin/AdminEditTenantPage.tsx::add-member-submit-btn',
    'pages/admin/AdminEditTenantPage.tsx::back-btn',
    'pages/admin/AdminEditTenantPage.tsx::cancel-tenant-erasure-btn',
    'pages/admin/AdminEditTenantPage.tsx::delete-tenant-btn',
    'pages/admin/AdminEditTenantPage.tsx::show-add-member-btn',
    'pages/admin/AdminEditUserPage.tsx::add-membership-submit-btn',
    'pages/admin/AdminEditUserPage.tsx::back-btn',
    'pages/admin/AdminEditUserPage.tsx::delete-user-btn',
    'pages/admin/AdminEditUserPage.tsx::show-add-tenant-btn',
    'pages/auth/settings/AccountSettingsGroup.tsx::delete-account-btn',
    'pages/auth/settings/AccountSettingsGroup.tsx::profile-save-btn',
    'pages/auth/settings/DisplaySettingsGroup.tsx::rerun-onboarding-btn',
    'pages/auth/settings/InstallationSettingsGroup.tsx::plantnet-reset-btn',
    'pages/auth/settings/InstallationSettingsGroup.tsx::plantnet-reset-cancel-btn',
    'pages/auth/settings/InstallationSettingsGroup.tsx::plantnet-reset-confirm-btn',
    'pages/auth/settings/InstallationSettingsGroup.tsx::plantnet-save-btn',
    'pages/auth/settings/InstallationSettingsGroup.tsx::plantnet-test-btn',
    'pages/auth/settings/InstallationSettingsGroup.tsx::reset-settings-btn',
    'pages/auth/settings/InstallationSettingsGroup.tsx::save-settings-btn',
    'pages/auth/settings/InstallationSettingsGroup.tsx::test-connection-btn',
    'pages/auth/settings/SecuritySettingsGroup.tsx::change-password-btn',
    'pages/auth/EmailChangeConfirmPage.tsx::email-change-confirm-btn',
    'pages/auth/EmailChangeConfirmPage.tsx::email-change-login-btn',
    'pages/auth/EmailChangeRevertPage.tsx::email-change-login-btn',
    'pages/auth/EmailChangeRevertPage.tsx::email-change-revert-btn',
    'pages/auth/EmailChangeRevertPage.tsx::email-change-revert-reset-btn',
    'pages/auth/PrivacySettingsPage.tsx::privacy-erasure-request-btn',
    'pages/auth/PrivacySettingsPage.tsx::privacy-export-download-btn',
    'pages/auth/PrivacySettingsPage.tsx::privacy-export-refresh-btn',
    'pages/auth/PrivacySettingsPage.tsx::privacy-export-request-btn',
    'pages/auth/PrivacySettingsPage.tsx::privacy-restrict-submit-btn',
    'pages/duengung/WaterMixRecommendationBox.tsx::water-mix-apply-btn',
    'pages/duengung/WaterMixRecommendationBox.tsx::water-mix-recommendation-btn',
    'pages/kalender/CalendarFeedUrlDialog.tsx::feed-url-close-btn',
    'pages/kalender/CalendarFeedUrlDialog.tsx::feed-url-copy-btn',
    'pages/kalender/CalendarPage.tsx::calendar-today-btn',
    'pages/kalender/CalendarPage.tsx::confirm-watering-btn',
    'pages/kalender/CalendarPage.tsx::create-feed-btn',
    'pages/kalender/CalendarPage.tsx::feed-cancel-btn',
    'pages/kalender/CalendarPage.tsx::feed-save-btn',
    'pages/pflanzen/ProfilesSection.tsx::edit-profiles-btn',
    'pages/tenants/InvitationAcceptPage.tsx::invitation-accept-btn',
    'pages/tenants/TenantSettingsPage.tsx::copy-invitation-link-btn',
    'pages/tenants/TenantSettingsPage.tsx::create-link-btn',
    'pages/tenants/TenantSettingsPage.tsx::send-invitation-btn',
  ]),
  /** Not kebab-case (R-018): the suffix is a domain key written as the data has it. */
  kebab: new Set([
    'components/dashboard/widgets/QuickActionsWidget.tsx::widget-quick_actions',
    'components/dashboard/widgets/WeatherForecastWidget.tsx::widget-weather_forecast',
    'features/gardenPlanner/zones/ZoneLegend.tsx::garden-plan-legend-plantState',
  ]),
};

describe('UI-NFR-022 R-014/R-017/R-018: naming of testids', () => {
  const found: Record<NamingRule, Set<string>> = { index: new Set(), btn: new Set(), kebab: new Set() };
  for (const [file, source] of productionEntries()) {
    for (const { value, template } of testIdValues(source)) {
      for (const rule of namingViolations(value, template)) found[rule].add(`${file}::${value}`);
    }
  }

  for (const rule of ['index', 'btn', 'kebab'] as const) {
    it(`no new ${rule} violation outside the register`, () => {
      expect([...found[rule]].filter((entry) => !NAMING_REGISTER[rule].has(entry)).sort()).toEqual([]);
    });

    it(`the ${rule} register only lists ids that still exist (shrink-only)`, () => {
      expect([...NAMING_REGISTER[rule]].filter((entry) => !found[rule].has(entry)).sort()).toEqual([]);
    });
  }
});

// ── Detector fixtures, both directions ─────────────────────────────────────

describe('detector fixtures', () => {
  describe('dialogs', () => {
    it('accepts a literal pair and an expression pair', () => {
      const literal = `
        <Dialog open data-testid="x-dialog" aria-labelledby="x-title">
          <DialogTitle id="x-title">T</DialogTitle>
        </Dialog>`;
      const expression = `
        const titleId = useId();
        return <Dialog open onClose={() => setOpen(x > 1)} data-testid="x-dialog" aria-labelledby={titleId}>
          <DialogTitle id={titleId}>T</DialogTitle></Dialog>;`;
      expect(dialogFindings('a.tsx', literal)).toEqual([]);
      expect(dialogFindings('a.tsx', expression)).toEqual([]);
    });

    it('rejects a missing testid, a missing label and a label pointing nowhere', () => {
      expect(dialogFindings('a.tsx', '<Dialog open aria-labelledby="t"><p id="t" /></Dialog>')).toEqual([
        'a.tsx:1 <Dialog> without data-testid',
      ]);
      expect(dialogFindings('a.tsx', '<Dialog open data-testid="d">')).toEqual([
        'a.tsx:1 <Dialog> without aria-labelledby',
      ]);
      expect(
        dialogFindings('a.tsx', '<Dialog open data-testid="d" aria-labelledby="x-titel"><h2 id="x-title" /></Dialog>'),
      ).toEqual(['a.tsx:1 <Dialog> aria-labelledby names no id defined in this file']);
    });

    it('ignores commented-out tags and a `>` inside an attribute expression or a comment', () => {
      const source = `
        // <Dialog open>
        {/* <Dialog open> */}
        <Dialog
          // see <Controller disabled> for why
          open={count > 0}
          data-testid="d"
          aria-labelledby="t"
        ><h2 id="t" /></Dialog>`;
      expect(dialogFindings('a.tsx', source)).toEqual([]);
      expect(openingTags(source, ['Dialog'])).toHaveLength(1);
    });

    it('does not take DialogTitle for a Dialog, and checks wrapper call sites', () => {
      expect(openingTags('<DialogTitle id="t">', ['Dialog'])).toEqual([]);
      expect(dialogFindings('a.tsx', '<FormDialog control={control} open>')).toEqual([
        'a.tsx:1 <FormDialog> without data-testid',
        'a.tsx:1 <FormDialog> without aria-labelledby',
      ]);
    });

    it('exempts the registered wrapper only while it spreads the caller props', () => {
      const wrapper = 'components/form/FormDialog.tsx';
      expect(dialogFindings(wrapper, '<Dialog {...dialogProps} onClose={x}>')).toEqual([]);
      expect(dialogFindings(wrapper, '<Dialog open={open} onClose={x}>')).toEqual([
        `${wrapper}:1 wrapper <Dialog> does not spread the caller's props`,
      ]);
    });
  });

  describe('page markers', () => {
    it('accepts a marker on the root of the last top-level return', () => {
      const source = `export default function FooPage() {
  if (loading) return <LoadingSkeleton />;
  return (
    <Box data-testid="foo-page" sx={{ p: 2 }}>
      <Inner />
    </Box>
  );
}

function Helper() {
  return <Box />;
}`;
      expect(pageRootMarker(source)).toEqual({ marker: 'foo-page' });
    });

    it('rejects a fragment root, an unmarked root and a marker deeper down', () => {
      const wrap = (jsx: string) => `export default function FooPage() {\n  return (\n    ${jsx}\n  );\n}`;
      expect(pageRootMarker(wrap('<><Box data-testid="foo-page" /></>'))).toEqual({ problem: 'root is a fragment' });
      expect(pageRootMarker(wrap('<Box sx={{ p: 2 }}><Card data-testid="foo-page" /></Box>'))).toEqual({
        problem: 'root <Box> has no literal data-testid',
      });
      expect(pageRootMarker(wrap('<Box data-testid="foo-view" />'))).toEqual({
        problem: 'root marker "foo-view" is not "<kebab-name>-page"',
      });
    });
  });

  describe('form wrappers', () => {
    it('accepts a wrapper that forwards form-field-<name> and keys its controls', () => {
      const source =
        'interface P { name: Path<T> }\n<Switch data-testid={`form-field-${name}-switch`} />\n' +
        '<TextField data-testid={`form-field-${name}`} slotProps={{ htmlInput: { "data-testid": "x" } }} />';
      expect(formWrapperFindings('components/form/X.tsx', source)).toEqual([]);
    });

    it('rejects an unkeyed control and a wrapper without form-field-<name>', () => {
      const source = 'interface P { name: Path<T> }\n<TextField label={label}\n  onChange={(e) => e.target.value > 1} />';
      expect(formWrapperFindings('components/form/X.tsx', source)).toEqual([
        'components/form/X.tsx: field wrapper does not render data-testid={`form-field-${name}`}',
        'components/form/X.tsx:2 <TextField> without data-testid',
      ]);
    });
  });

  describe('testid lookups', () => {
    it('rejects every way of selecting by testid in code', () => {
      const source = [
        `document.querySelector('[data-testid="x"]')?.focus();`,
        'el.closest(`[data-testid="${id}"]`);',
        'if (el.dataset.testid === "x") {}',
        `el.getAttribute('data-testid');`,
        `root.getElementsByClassName(testid);`,
        `sx={{ '& [data-testid="page-title"]': { mb: 0 } }}`,
      ].join('\n');
      expect(testIdLookupFindings('a.ts', source).map((f) => f.split(' ')[0])).toEqual([
        'a.ts:1',
        'a.ts:2',
        'a.ts:6',
        'a.ts:3',
        'a.ts:4',
        'a.ts:5',
      ]);
    });

    it('accepts ids, refs, a testid prop passthrough and a selector named in a comment', () => {
      const source = [
        '// resolved via [data-testid="x"] in the page object',
        '/** `[data-testid=\'y\']` is the stable trigger */',
        'document.getElementById(EDITOR_ANCHORS.panelName)?.focus();',
        "if (element.props['data-testid'] === undefined) props['data-testid'] = testId;",
        '<Box data-testid={testId} />',
      ].join('\n');
      expect(testIdLookupFindings('a.ts', source)).toEqual([]);
    });
  });

  describe('naming', () => {
    it('flags index interpolation, -btn and non-kebab', () => {
      expect(namingViolations('photo-remove-${i}', true)).toEqual(['index']);
      expect(namingViolations('row-${index + 1}', true)).toEqual(['index']);
      expect(namingViolations('save-btn', false)).toEqual(['btn']);
      expect(namingViolations('save-btn-${key}', true)).toEqual(['btn']);
      expect(namingViolations('widget-quick_actions', false)).toEqual(['kebab']);
      expect(namingViolations('legendPlantState', false)).toEqual(['kebab']);
    });

    it('accepts keyed, -button, kebab and form-field-<name> ids', () => {
      expect(namingViolations('photo-remove-${photo.key}', true)).toEqual([]);
      expect(namingViolations('save-button', false)).toEqual([]);
      expect(namingViolations('form-field-species_key', false)).toEqual([]);
      expect(namingViolations('form-option-${name}-${opt.value}', true)).toEqual([]);
      expect(namingViolations('subtitle-row', false)).toEqual([]);
    });
  });
});
