/**
 * Axe pass for the highest-traffic pages (#1094).
 *
 * Before this, `vitest-axe` covered five surfaces out of dozens: a11y was
 * checked by memory, not by default. This backfills the pages the issue names —
 * dashboard (already covered, kept here so the set reads as one list), the plant
 * list and detail, and the task queue.
 *
 * **These render against an empty store on purpose.** A page is at its most
 * accessible-hostile while it has no data: that is when it shows spinners,
 * skeletons and empty states — controls with no name, regions with no label,
 * icon-only buttons. A test that seeded a full happy-path store would skip
 * exactly the markup users hit first.
 *
 * Kept in one file rather than folded into each page's existing test: those
 * files carry per-page store fixtures, and an axe scan added to each would
 * inherit whichever state that test happened to need. Here the state is the
 * subject.
 */

import i18n from 'i18next';
import { describe, it, beforeEach } from 'vitest';

import DashboardPage from '@/pages/DashboardPage';
import TaskQueuePage from '@/pages/aufgaben/TaskQueuePage';
import PlantInstanceListPage from '@/pages/pflanzen/PlantInstanceListPage';

import { renderWithProviders } from '../helpers';
import { expectNoA11yViolations } from './expectNoA11yViolations';

/**
 * A page reduced to its router wrapper by a render error, or short-circuited to
 * a not-found branch by a missing route parameter, still produces a handful of
 * nodes — and passes every axe rule. This floor is what makes each assertion
 * below say "this page is accessible" rather than "something was rendered".
 * Measured: the smallest of these four renders well over 100 elements even with
 * an empty store.
 */
const PAGE_MIN_ELEMENTS = 20;

/**
 * **`PlantInstanceDetailPage` lives in its own file**, because the route mock it
 * needs is module-scoped and would reach every page here.
 *
 * It was briefly in this file, and it never left its loading skeleton: 15
 * elements, unchanged after 15 seconds, because the default MSW handlers do not
 * answer the per-plant requests it makes. Axe passed it cleanly in that state —
 * a green a11y test over a spinner. Lowering `PAGE_MIN_ELEMENTS` to 15 would
 * have made this whole file worth less than nothing, since every page would then
 * pass while loading. See `plantInstanceDetail.a11y.test.tsx`, where it is
 * scanned against a seeded plant and the floor is what enforces that.
 */

describe('Accessibility — top-traffic pages', () => {
  beforeEach(() => {
    i18n.changeLanguage('de');
  });

  it('DashboardPage has no critical a11y violations', async () => {
    const { container } = renderWithProviders(<DashboardPage />);

    await expectNoA11yViolations(container, { minElements: PAGE_MIN_ELEMENTS });
  });

  it('PlantInstanceListPage has no critical a11y violations', async () => {
    const { container } = renderWithProviders(<PlantInstanceListPage />);

    await expectNoA11yViolations(container, { minElements: PAGE_MIN_ELEMENTS });
  });

  it('TaskQueuePage has no critical a11y violations', async () => {
    const { container } = renderWithProviders(<TaskQueuePage />);

    await expectNoA11yViolations(container, { minElements: PAGE_MIN_ELEMENTS });
  });
});
