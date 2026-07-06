import { useCallback, useEffect, useMemo, useState } from 'react';
import { listSites } from '@/api/endpoints/sites';
import { getSiteWeatherForecast } from '@/api/endpoints/weatherSources';
import type { Site, SiteWeatherForecastResponse } from '@/api/types';

interface FetchState {
  loading: boolean;
  /** True when the forecast request itself failed (endpoint / network error). */
  error: boolean;
  /** The site whose forecast is shown, or `null` when the tenant has no site. */
  site: Site | null;
  forecast: SiteWeatherForecastResponse | null;
  /** True when the tenant owns more than one site (drives the site-name header). */
  multipleSites: boolean;
}

interface State extends FetchState {
  /**
   * Re-runs the site/forecast fetch from scratch. Surfaced so the widget can
   * offer a "Retry" action on its error state (UI-NFR-004 R-015: network
   * errors MUST offer a retry option).
   */
  refetch: () => void;
}

const INITIAL: FetchState = {
  loading: true,
  error: false,
  site: null,
  forecast: null,
  multipleSites: false,
};

/**
 * Issue #392 (R7) — resolves the single site whose weather forecast the
 * dashboard `WeatherForecastWidget` renders.
 *
 * The widget is dashboard-wide but a forecast is per-site, so we keep the
 * selection deliberately simple (no multi-site aggregation): fetch the tenant's
 * sites once and pick the first site that carries `gps_coordinates` — the
 * precondition the backend fetch task requires to persist any forecast — falling
 * back to the first site otherwise. The forecast read is graceful by contract
 * (empty `forecasts` + `null` frost fields when no source is configured), so an
 * unconfigured site simply surfaces the widget's configure empty state.
 *
 * Returns an object; the return is `useMemo`-stabilised per the custom-hook
 * convention so consumers don't re-render on referentially-new snapshots.
 */
export function useSiteWeatherForecast(): State {
  const [state, setState] = useState<FetchState>(INITIAL);
  // Bumped by `refetch()` to re-run the effect below (e.g. after a Retry click).
  const [reloadToken, setReloadToken] = useState(0);

  useEffect(() => {
    let cancelled = false;
    const load = async () => {
      setState((prev) => ({ ...prev, loading: true, error: false }));
      try {
        const sites = await listSites();
        if (cancelled) return;
        const chosen = sites.find((s) => s.gps_coordinates) ?? sites[0] ?? null;
        if (!chosen) {
          setState({ loading: false, error: false, site: null, forecast: null, multipleSites: false });
          return;
        }
        const forecast = await getSiteWeatherForecast(chosen.key);
        if (cancelled) return;
        setState({
          loading: false,
          error: false,
          site: chosen,
          forecast,
          multipleSites: sites.length > 1,
        });
      } catch {
        if (!cancelled) {
          setState({ loading: false, error: true, site: null, forecast: null, multipleSites: false });
        }
      }
    };
    load();
    return () => {
      cancelled = true;
    };
  }, [reloadToken]);

  const refetch = useCallback(() => setReloadToken((t) => t + 1), []);

  return useMemo(
    () => ({
      loading: state.loading,
      error: state.error,
      site: state.site,
      forecast: state.forecast,
      multipleSites: state.multipleSites,
      refetch,
    }),
    [state.loading, state.error, state.site, state.forecast, state.multipleSites, refetch],
  );
}
