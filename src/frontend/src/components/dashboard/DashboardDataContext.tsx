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
