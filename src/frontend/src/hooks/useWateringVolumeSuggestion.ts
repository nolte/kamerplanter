import { useEffect, useState, useMemo } from 'react';
import { getWateringVolumeSuggestion } from '@/api/endpoints/watering-events';
import type { VolumeSuggestion } from '@/api/types';

/**
 * Fetches a watering volume suggestion for a plant from the backend.
 * Returns volume in liters, a human-readable hint, and the raw suggestion.
 */
export function useWateringVolumeSuggestion(plantKey: string | undefined | null) {
  const [suggestion, setSuggestion] = useState<VolumeSuggestion | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!plantKey) {
      // eslint-disable-next-line react-hooks/set-state-in-effect -- reset state when key is cleared
      setSuggestion(null);
      return;
    }
    let cancelled = false;
    setLoading(true);
    getWateringVolumeSuggestion(plantKey)
      .then((data) => {
        if (!cancelled) setSuggestion(data);
      })
      .catch(() => {
        if (!cancelled) setSuggestion(null);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => { cancelled = true; };
  }, [plantKey]);

  const result = useMemo(() => {
    if (!suggestion) return null;
    const liters = Math.round(suggestion.volume_ml / 100) / 10; // ml → L, 1 decimal
    const minL = Math.round(suggestion.volume_ml_min / 100) / 10;
    const maxL = Math.round(suggestion.volume_ml_max / 100) / 10;
    const hint = `${suggestion.volume_ml_min}–${suggestion.volume_ml_max} ml (${suggestion.source.split('_').join(' ')})`;
    return { liters: Math.max(0.1, liters), minLiters: minL, maxLiters: maxL, hint, raw: suggestion };
  }, [suggestion]);

  return { suggestion: result, loading };
}
