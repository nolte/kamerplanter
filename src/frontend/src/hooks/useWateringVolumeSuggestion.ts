import { useEffect, useState, useMemo } from 'react';
import { useTranslation } from 'react-i18next';
import { getWateringVolumeSuggestion } from '@/api/endpoints/watering-events';
import type { VolumeSuggestion } from '@/api/types';

export interface WateringVolumeSuggestion {
  liters: number;
  minLiters: number;
  maxLiters: number;
  /** Range and source in the user's language, e.g. "800–1200 ml (Phasenprofil)". */
  hint: string;
  raw: VolumeSuggestion;
}

export interface WateringVolumeSuggestionState {
  suggestion: WateringVolumeSuggestion | null;
  loading: boolean;
  /** True when the request failed — distinct from "the backend has no suggestion". */
  failed: boolean;
}

/**
 * Fetches a watering volume suggestion for a plant from the backend.
 * Returns volume in liters, a localized hint, and the raw suggestion.
 */
export function useWateringVolumeSuggestion(
  plantKey: string | undefined | null,
): WateringVolumeSuggestionState {
  const { t } = useTranslation();
  const [suggestion, setSuggestion] = useState<VolumeSuggestion | null>(null);
  const [loading, setLoading] = useState(false);
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    if (!plantKey) {
      // eslint-disable-next-line react-hooks/set-state-in-effect -- reset state when key is cleared
      setSuggestion(null);
      setFailed(false);
      return;
    }
    let cancelled = false;
    setLoading(true);
    setFailed(false);
    getWateringVolumeSuggestion(plantKey)
      .then((data) => {
        if (!cancelled) setSuggestion(data);
      })
      .catch(() => {
        if (cancelled) return;
        setSuggestion(null);
        setFailed(true);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => { cancelled = true; };
  }, [plantKey]);

  const result = useMemo((): WateringVolumeSuggestion | null => {
    if (!suggestion) return null;
    const liters = Math.round(suggestion.volume_ml / 100) / 10; // ml → L, 1 decimal
    const minL = Math.round(suggestion.volume_ml_min / 100) / 10;
    const maxL = Math.round(suggestion.volume_ml_max / 100) / 10;
    const source = t(`enums.wateringVolumeSource.${suggestion.source}`, {
      defaultValue: suggestion.source.split('_').join(' '),
    });
    const hint = `${suggestion.volume_ml_min}–${suggestion.volume_ml_max} ml (${source})`;
    return { liters: Math.max(0.1, liters), minLiters: minL, maxLiters: maxL, hint, raw: suggestion };
  }, [suggestion, t]);

  return useMemo(() => ({ suggestion: result, loading, failed }), [result, loading, failed]);
}
