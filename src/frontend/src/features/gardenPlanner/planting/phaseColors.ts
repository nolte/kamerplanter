/**
 * Colour of a plant marker by growth phase (REQ-053 GP-FR-067, GP-UX-060 in WP 3.7): the phase's name
 * decides, so the same phase has the same colour in every bed. The marker also carries a ring, so the
 * fill is never the only cue.
 */
import { useEffect, useMemo, useRef, useState } from 'react';
import axios from 'axios';
import { getGrowthPhase } from '@/api/endpoints/phases';
import { ApiError } from '@/api/errors';

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

/**
 * Phase keys `/growth-phases/{key}` answered 404 for in this session (a phase-sequence entry key, or a phase that is
 * gone): they are not asked again until the page reloads.
 */
const missingPhaseKeys = new Set<string>();

/** Test seam: forget the phase keys that answered 404. */
export function forgetMissingPhaseKeys(): void {
  missingPhaseKeys.clear();
}

function isNotFound(error: unknown): boolean {
  if (error instanceof ApiError) return error.statusCode === 404;
  return axios.isAxiosError(error) && error.response?.status === 404;
}

/**
 * `phase key → phase name` for the phases the plants are in; a name appears as soon as it arrives. Each key is
 * read once per mounted hook; a key that answered 404 is remembered for the session and never asked again.
 */
export function usePhaseNames(phaseKeys: readonly (string | null | undefined)[]): Readonly<Record<string, string>> {
  const wanted = useMemo(
    () => [...new Set(phaseKeys.filter((key): key is string => Boolean(key)))].sort(),
    [phaseKeys],
  );
  const signature = wanted.join('|');
  const [resolved, setResolved] = useState<Readonly<Record<string, string>>>(NO_ENTRIES);
  const requested = useRef(new Set<string>());
  const mounted = useRef(true);
  useEffect(() => {
    mounted.current = true;
    return () => {
      mounted.current = false;
    };
  }, []);
  useEffect(() => {
    const open = wanted.filter((key) => !requested.current.has(key) && !missingPhaseKeys.has(key));
    if (open.length === 0) return;
    for (const key of open) requested.current.add(key);
    Promise.all(
      open.map((key) =>
        getGrowthPhase(key)
          .then((phase): [string, string] => [key, phase.name])
          // A phase that cannot be read keeps the default plant colour; a 404 is final for the session, any other
          // failure is tried again when the set of phases changes.
          .catch((error: unknown): null => {
            if (isNotFound(error)) missingPhaseKeys.add(key);
            else requested.current.delete(key);
            return null;
          }),
      ),
    ).then((entries) => {
      if (!mounted.current) return;
      const found = entries.filter((entry): entry is [string, string] => entry !== null);
      if (found.length > 0) setResolved((previous) => ({ ...previous, ...Object.fromEntries(found) }));
    });
    // `signature` is the content of `wanted`.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [signature]);
  return useMemo(() => {
    const names = wanted.filter((key) => key in resolved);
    return names.length === 0 ? NO_ENTRIES : Object.fromEntries(names.map((key) => [key, resolved[key]]));
  }, [wanted, resolved]);
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
