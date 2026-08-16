/**
 * Every page component either has an axe pass or is registered as owing one (#1094).
 *
 * The issue asks for the axe check to happen "by default, not by memory". In a
 * suite with no test generator there is nothing to wire it *into* — so the
 * enforceable reading is the inverse: make the absence detectable. A new page
 * added tomorrow either gets an axe assertion or turns this file red, and the
 * author has to write down, here, that it is owed.
 *
 * The register below is the honest state, not an aspiration: 6 of 84 pages are
 * covered today. #1094 scopes the backfill to the top-traffic pages and says the
 * rest follows incrementally, so listing the rest is the accurate thing to do.
 * A guard that demanded all 84 at once would be turned off this week — and the
 * register is what turns "we'll get to it" into something a reader can count.
 *
 * Two assertions, and the second is the one that keeps the register truthful:
 *
 * 1. An **unregistered** page with no axe test fails. That is the new-page case.
 * 2. A **registered** page that has since gained one also fails, so the entry
 *    must be deleted with the fix. Without this the register would slowly become
 *    a list of things that used to be broken, and the next reader would trust it.
 *
 * Coverage is detected by reading which page modules the axe tests import. That
 * is deliberately shallow: it proves a page is *scanned*, not that the scan was
 * meaningful. `expectNoA11yViolations`' own `minElements` floor is what stops a
 * scan over a loading skeleton from counting — see the note on
 * `PlantInstanceDetailPage` in topPages.a11y.test.tsx for what that caught.
 */

import { describe, it, expect } from 'vitest';

/** Every page component in the app, as module paths. */
const PAGE_MODULES = import.meta.glob('/src/pages/**/*Page.tsx', {
  query: '?raw',
  import: 'default',
  eager: true,
}) as Record<string, string>;

/** Source of every a11y test, read as text so we can see what it imports. */
const A11Y_TEST_SOURCES = import.meta.glob('/src/test/a11y/*.test.tsx', {
  query: '?raw',
  import: 'default',
  eager: true,
}) as Record<string, string>;

/** `/src/pages/pflanzen/PlantInstanceListPage.tsx` → `PlantInstanceListPage`. */
function componentName(modulePath: string): string {
  return modulePath.split('/').pop()!.replace(/\.tsx$/, '');
}

/**
 * Page components imported by at least one a11y test.
 *
 * Matched on the import specifier rather than on the identifier, so a test that
 * merely *mentions* a page name in a comment or a string does not count as
 * covering it.
 */
function pagesUnderAxe(): Set<string> {
  const covered = new Set<string>();
  const importRe = /from\s+'([^']*\/([A-Za-z0-9_]*Page))'/g;

  for (const source of Object.values(A11Y_TEST_SOURCES)) {
    for (const match of source.matchAll(importRe)) {
      covered.add(match[2]);
    }
  }
  return covered;
}

/**
 * Pages that owe an axe pass, with no rationale field on purpose.
 *
 * There is no good reason for a page to be here — only the fact that the
 * backfill has not reached it. Adding a page to this list is meant to feel like
 * recording a debt, not like justifying an exemption.
 */
const PAGES_OWING_AN_AXE_PASS: ReadonlySet<string> = new Set([
  'AccountSettingsPage',
  'ActivityDetailPage',
  'ActivityListPage',
  'AdminEditTenantPage',
  'AdminEditUserPage',
  'AquaponikPage',
  'BatchDetailPage',
  'BotanicalFamilyDetailPage',
  'BotanicalFamilyListPage',
  'CalculationsPage',
  'CalendarPage',
  'CompanionPlantingPage',
  'ConnectLandingPage',
  'CropRotationPage',
  'CultivarDetailPage',
  'DiagnosePage',
  'DiaryOverviewPage',
  'DiseaseListPage',
  'EmailVerificationPage',
  'EnvironmentControlPage',
  'ErrorPage',
  'FeedingEventDetailPage',
  'FeedingEventListPage',
  'FertilizerDetailPage',
  'FertilizerListPage',
  'GlossaryPage',
  'HarvestBatchDetailPage',
  'HarvestBatchListPage',
  'ImportPage',
  'InventreePage',
  'InvitationAcceptPage',
  'KIAssistentPage',
  'KioskStartPage',
  'LocationDetailPage',
  'NutrientCalculationsPage',
  'NutrientPlanDetailPage',
  'NutrientPlanListPage',
  'OAuthCallbackPage',
  'OverwinteringListPage',
  'PasswordResetConfirmPage',
  'PasswordResetRequestPage',
  'PestDetailPage',
  'PestIdentificationPage',
  'PestListPage',
  'PhaseDefinitionDetailPage',
  'PhaseDefinitionListPage',
  'PhaseSequenceDetailPage',
  'PhaseSequenceListPage',
  'PlantIdentificationPage',
  'PlantingRunDetailPage',
  'PlantingRunListPage',
  'PostHarvestPage',
  'PrivacySettingsPage',
  'PropagationPage',
  'RegisterPage',
  'RouterErrorPage',
  'SiteDetailPage',
  'SiteListPage',
  'SlotDetailPage',
  'SpeciesDetailPage',
  'SpeciesListPage',
  'SubstrateDetailPage',
  'SubstrateListPage',
  'SuccessionPlanListPage',
  'TankDetailPage',
  'TankListPage',
  'TaskDetailPage',
  'TenantCreatePage',
  'TenantSettingsPage',
  'TreatmentDetailPage',
  'TreatmentListPage',
  'WateringEventListPage',
  'WateringLogDetailPage',
  'WateringLogListPage',
  'WorkflowDetailPage',
  'WorkflowTemplateListPage',
]);

describe('A11y page coverage', () => {
  it('finds pages and a11y tests to compare', () => {
    // Every assertion below is a no-op over an empty glob. A moved directory or
    // a changed file-name convention would leave this file reporting green while
    // comparing nothing — the exact shape #1094 exists to remove.
    expect(Object.keys(PAGE_MODULES).length).toBeGreaterThan(50);
    expect(Object.keys(A11Y_TEST_SOURCES).length).toBeGreaterThan(0);
    expect(pagesUnderAxe().size).toBeGreaterThan(0);
  });

  it('has no page that is neither scanned nor registered as owing a scan', () => {
    const covered = pagesUnderAxe();
    const unaccounted = Object.keys(PAGE_MODULES)
      .map(componentName)
      .filter((name) => !covered.has(name) && !PAGES_OWING_AN_AXE_PASS.has(name))
      .sort();

    expect(
      unaccounted,
      `These pages have no axe assertion and are not registered as owing one:\n` +
        unaccounted.map((n) => `  - ${n}`).join('\n') +
        `\n\nAdd a case to src/test/a11y/topPages.a11y.test.tsx, or add the page to ` +
        `PAGES_OWING_AN_AXE_PASS in this file. FRONTEND.md §13.5 requires the axe pass; ` +
        `this list is what makes a new page unable to skip it silently.`,
    ).toEqual([]);
  });

  it('has no register entry for a page that is already scanned', () => {
    const covered = pagesUnderAxe();
    const stale = [...PAGES_OWING_AN_AXE_PASS].filter((name) => covered.has(name)).sort();

    expect(
      stale,
      `These pages are registered as owing an axe pass but already have one:\n` +
        stale.map((n) => `  - ${n}`).join('\n') +
        `\n\nRemove them from PAGES_OWING_AN_AXE_PASS. A register that outlives its debt ` +
        `reads as a live list of gaps and misleads the next reader.`,
    ).toEqual([]);
  });

  it('has no register entry for a page that no longer exists', () => {
    const existing = new Set(Object.keys(PAGE_MODULES).map(componentName));
    const ghosts = [...PAGES_OWING_AN_AXE_PASS].filter((name) => !existing.has(name)).sort();

    expect(
      ghosts,
      `These registered pages do not exist:\n` +
        ghosts.map((n) => `  - ${n}`).join('\n') +
        `\n\nThey were renamed or deleted; drop them from PAGES_OWING_AN_AXE_PASS.`,
    ).toEqual([]);
  });
});
