import { createContext, useContext, type ReactNode } from 'react';

/**
 * REQ-045 — provides the REQ-009 aggregated payloads (fetched once for all the
 * user's active widget keys, N+1 avoidance) to individual widgets. Widgets that
 * have no aggregated slice self-fetch their own data (like WinterProtectionWidget).
 */

interface DashboardData {
  payloads: Record<string, unknown>;
  loading: boolean;
}

const DashboardDataContext = createContext<DashboardData>({ payloads: {}, loading: false });

export function DashboardDataProvider({
  value,
  children,
}: {
  value: DashboardData;
  children: ReactNode;
}) {
  return <DashboardDataContext.Provider value={value}>{children}</DashboardDataContext.Provider>;
}

export function useWidgetPayload(widgetKey: string): { payload: unknown; loading: boolean } {
  const { payloads, loading } = useContext(DashboardDataContext);
  return { payload: payloads[widgetKey], loading };
}

/**
 * "Is the dashboard still fetching?" — the aggregate signal behind the grid's
 * single loading announcement (`DashboardLoadingRegion`, issue #1337).
 *
 * It reads the *same* flag `useWidgetPayload` hands each widget, deliberately:
 * the announcement and the placeholders it speaks for can then never disagree
 * about whether the dashboard is loading. The REQ-045 aggregate endpoint fetches
 * every active widget key in a single round trip, so there is one flag for the
 * whole batch rather than one per widget (see `dashboardSlice`).
 *
 * Widgets that fetch their own data (`weather_forecast`, `winter_protection`)
 * are *not* represented here. Their placeholders carry neither a dropped name
 * nor a live region of their own today; folding them into the aggregate needs a
 * registration mechanism and is a separate decision.
 */
export function useDashboardLoading(): boolean {
  return useContext(DashboardDataContext).loading;
}
