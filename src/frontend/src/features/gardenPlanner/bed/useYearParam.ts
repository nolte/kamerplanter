/**
 * The season shown in the bed view (`?year=`, REQ-053 GP-FR-077). The year is validated against the
 * offered range, so a hand-edited URL falls back to the current year instead of asking for 1900.
 */
import { useCallback, useMemo } from 'react';
import { useLocation, useNavigate, useSearchParams } from 'react-router-dom';

/** Years on offer: next year (planning ahead) down to this many years back. */
const YEARS_BACK = 5;

export interface YearParam {
  year: number;
  years: readonly number[];
  setYear: (year: number) => void;
}

export function useYearParam(now: Date = new Date()): YearParam {
  const [searchParams] = useSearchParams();
  const location = useLocation();
  const navigate = useNavigate();
  const current = now.getFullYear();
  const raw = searchParams.get('year');

  const years = useMemo(
    () => Array.from({ length: YEARS_BACK + 2 }, (_, index) => current + 1 - index),
    [current],
  );
  const year = useMemo(() => {
    const requested = raw === null ? Number.NaN : Number(raw);
    return years.includes(requested) ? requested : current;
  }, [raw, years, current]);

  const setYear = useCallback(
    (next: number) => {
      const params = new URLSearchParams(location.search);
      if (next === current) params.delete('year');
      else params.set('year', String(next));
      const search = params.toString();
      navigate({ search: search ? `?${search}` : '', hash: location.hash }, { replace: true });
    },
    [current, location.search, location.hash, navigate],
  );

  return useMemo(() => ({ year, years, setYear }), [year, years, setYear]);
}
