/**
 * Colour of a plant marker by growth phase (REQ-053 GP-FR-067, GP-UX-060 in WP 3.7): the phase's name
 * decides, so the same phase has the same colour in every bed. The marker also carries a ring, so the
 * fill is never the only cue.
 */
import { useEffect, useMemo, useState } from 'react';
import { getGrowthPhase } from '@/api/endpoints/phases';

const PHASE_COLORS: Readonly<Record<string, string>> = {
  germination: '#81C784',
  seedling: '#66BB6A',
  vegetative: '#43A047',
  flowering: '#AB47BC',
  harvest: '#EF5350',
  drying: '#FF7043',
  curing: '#FFA726',
  flushing: '#42A5F5',
  ripening: '#FF8A65',
  cloning: '#26A69A',
};

const FALLBACK_PALETTE = [
  '#7E57C2',
  '#5C6BC0',
  '#29B6F6',
  '#26C6DA',
  '#66BB6A',
  '#D4E157',
  '#FFCA28',
  '#FFA726',
  '#EC407A',
  '#78909C',
] as const;

export function phaseColor(phaseName: string): string {
  const key = phaseName.toLowerCase().replace(/[^a-z]/g, '');
  const known = PHASE_COLORS[key];
  if (known) return known;
  let hash = 0;
  for (let index = 0; index < phaseName.length; index += 1) {
    hash = (hash * 31 + phaseName.charCodeAt(index)) | 0;
  }
  return FALLBACK_PALETTE[Math.abs(hash) % FALLBACK_PALETTE.length];
}

/** `phase key → phase name` for the phases the plants are in; empty until the names arrive. */
export function usePhaseNames(phaseKeys: readonly (string | null | undefined)[]): Readonly<Record<string, string>> {
  const wanted = useMemo(
    () => [...new Set(phaseKeys.filter((key): key is string => Boolean(key)))].sort(),
    [phaseKeys],
  );
  const signature = wanted.join('|');
  const [loaded, setLoaded] = useState<{ signature: string; names: Record<string, string> }>({
    signature: '',
    names: {},
  });
  useEffect(() => {
    if (wanted.length === 0) return undefined;
    let cancelled = false;
    Promise.all(
      wanted.map((key) =>
        getGrowthPhase(key)
          .then((phase): [string, string] => [key, phase.name])
          // A phase that cannot be read keeps the default plant colour.
          .catch((): [string, string] | null => null),
      ),
    ).then((entries) => {
      if (cancelled) return;
      setLoaded({
        signature,
        names: Object.fromEntries(entries.filter((entry): entry is [string, string] => entry !== null)),
      });
    });
    return () => {
      cancelled = true;
    };
    // `signature` is the content of `wanted`.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [signature]);
  return loaded.signature === signature ? loaded.names : NO_ENTRIES;
}

/** `phase key → colour` for the phases the plants of a bed are in; empty until the names arrive. */
export function usePhaseColors(phaseKeys: readonly (string | null | undefined)[]): Readonly<Record<string, string>> {
  const names = usePhaseNames(phaseKeys);
  return useMemo(() => colorsOf(names), [names]);
}

/** `phase key → colour` from `phase key → name`. */
export function colorsOf(names: Readonly<Record<string, string>>): Readonly<Record<string, string>> {
  const keys = Object.keys(names);
  if (keys.length === 0) return NO_ENTRIES;
  return Object.fromEntries(keys.map((key) => [key, phaseColor(names[key])]));
}

const NO_ENTRIES: Readonly<Record<string, string>> = {};
