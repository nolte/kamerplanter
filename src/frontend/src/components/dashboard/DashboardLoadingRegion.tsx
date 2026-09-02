import Box from '@mui/material/Box';
import { visuallyHidden } from '@mui/utils';
import { useTranslation } from 'react-i18next';
import { useDashboardLoading } from '@/components/dashboard/DashboardDataContext';

/**
 * Issue #1337 item 1 — the dashboard's single loading announcement.
 *
 * Every other loading placeholder in this frontend pairs its `aria-busy`
 * wrapper with a `LoadingStatus` live region (#1324/#1329). The dashboard was
 * deliberately left out of that sweep, because the shape does not scale here:
 * mid-load the grid stands with **five** aggregated placeholders at once
 * (`tasks_today`, `care_reminders`, `active_plants_summary`, `daily_tip`,
 * `onboarding_progress`), so a region per placeholder would be five concurrent
 * polite live regions all saying "loading" — worse than the silence it
 * replaces. `LoadingSkeleton` never hits this: at most two skeletons stand at
 * once across the ten routes measured in #1337.
 *
 * The decision taken instead, and what this component implements:
 *
 * - **One region for the whole grid**, mounted by the grid component rather
 *   than by a widget or by the page. The page root already owns an unrelated
 *   status region (the edit-mode move/resize announcements in `DashboardPage`);
 *   a second one there would have two owners writing to neighbouring regions.
 *   Both grids (read-only and edit) mount this one component — exactly one is
 *   ever mounted, so the dashboard has exactly one loading region, and the two
 *   siblings cannot drift apart on the shape.
 * - **It says one translated sentence while at least one widget is loading**,
 *   and goes **empty** — not unmounted — once everything has settled. The node
 *   stays in the DOM because a live region must exist *before* its content
 *   changes for the change to be announced reliably; a region inserted together
 *   with its text is not.
 * - **An early-finished widget does not touch it.** The text is one constant
 *   string for the whole load, so React writes the DOM once when loading starts
 *   and once when it ends. Widgets settling in between change nothing, which is
 *   what keeps a five-widget load down to one announcement.
 * - **A refresh announces again**: empty → message is a content change on a
 *   live region, so a second load is not swallowed.
 *
 * The busy state itself stays on the individual placeholders (`aria-busy` on an
 * *unnamed* container — naming a role-less `<div>` is what got the name dropped
 * in the first place). Per `LoadingStatus`'s measurement, `aria-busy` must not
 * be set on this node: Chrome reports `busy=1` on a live region that carries
 * both, which invites assistive technology to defer the very announcement this
 * element exists to make.
 */
export default function DashboardLoadingRegion() {
  const { t } = useTranslation();
  const loading = useDashboardLoading();
  const message = t('dashboard.loading.announcement');
  return (
    <Box
      component="span"
      role="status"
      aria-live="polite"
      // Named only while it has something to say. `status` takes its name from
      // the author, never from its content, so the label is what a user who
      // navigates onto the region hears; leaving it in place once the dashboard
      // has settled would name an empty region after a load that is over.
      aria-label={loading ? message : undefined}
      sx={visuallyHidden}
      data-testid="dashboard-loading-status"
    >
      {loading ? message : ''}
    </Box>
  );
}
