/**
 * The hints the dialog shows per chosen species (REQ-053 GP-FR-132): crop rotation and the
 * neighbours of the bed (`validate-planting`), and the compatibility of the species chosen together
 * (GP-FR-070). A hint has a strength and never blocks (D-09); a failed request is shown as "could
 * not be checked", not as "all clear".
 */
import { useEffect, useMemo, useRef, useState } from 'react';
import { parseApiError } from '@/api/errors';
import { getCompatibleSpecies, getIncompatibleSpecies } from '@/api/endpoints/companionPlanting';
import { validatePlanting } from './plantingApi';
import type { ValidatePlantingResponse } from './plantingTypes';

export type HintState =
  | { status: 'loading' }
  | { status: 'ready'; data: ValidatePlantingResponse }
  | { status: 'error'; message: string };

/** One request per distinct species; the history of a bed does not change while the dialog is open. */
export function useBedHints(bedKey: string, speciesKeys: readonly (string | null)[]): Record<string, HintState> {
  const [states, setStates] = useState<Record<string, HintState>>({});
  const asked = useRef(new Set<string>());
  const wanted = useMemo(
    () => [...new Set(speciesKeys.filter((key): key is string => Boolean(key)))].sort(),
    [speciesKeys],
  );

  useEffect(() => {
    for (const key of wanted) {
      if (asked.current.has(key)) continue;
      asked.current.add(key);
      setStates((current) => ({ ...current, [key]: { status: 'loading' } }));
      validatePlanting(bedKey, key)
        .then((data) => setStates((current) => ({ ...current, [key]: { status: 'ready', data } })))
        .catch((error: unknown) =>
          setStates((current) => ({
            ...current,
            [key]: { status: 'error', message: parseApiError(error) },
          })),
        );
    }
  }, [bedKey, wanted]);

  return states;
}

export interface MixPair {
  a: string;
  b: string;
  kind: 'compatible' | 'incompatible';
  /** Compatibility score of a compatible pair. */
  score: number | null;
  /** The reason the graph records for an incompatible pair. */
  reason: string | null;
}

/** Pairs among `speciesKeys` the companion graph rates (REQ-028); a pair it knows nothing about is absent. */
export function useMixedCompatibility(speciesKeys: readonly (string | null)[]): MixPair[] {
  const keys = useMemo(
    () => [...new Set(speciesKeys.filter((key): key is string => Boolean(key)))].sort(),
    [speciesKeys],
  );
  const signature = keys.join('|');
  const [pairs, setPairs] = useState<{ signature: string; pairs: MixPair[] }>({ signature: '', pairs: [] });

  useEffect(() => {
    if (keys.length < 2) return undefined;
    let cancelled = false;
    Promise.all(
      keys.map(async (key) => {
        const [good, bad] = await Promise.all([getCompatibleSpecies(key), getIncompatibleSpecies(key)]);
        return { key, good, bad };
      }),
    )
      .then((rows) => {
        if (cancelled) return;
        const found = new Map<string, MixPair>();
        for (const { key, good, bad } of rows) {
          for (const other of keys) {
            if (other === key) continue;
            const [a, b] = key < other ? [key, other] : [other, key];
            const id = `${a}|${b}`;
            const incompatible = bad.find((s) => s.species_key === other);
            const compatible = good.find((s) => s.species_key === other);
            // An incompatibility wins over a compatibility recorded on the other side.
            if (incompatible) {
              found.set(id, { a, b, kind: 'incompatible', score: null, reason: incompatible.reason || null });
            } else if (compatible && found.get(id)?.kind !== 'incompatible') {
              found.set(id, { a, b, kind: 'compatible', score: compatible.score, reason: null });
            }
          }
        }
        setPairs({ signature, pairs: [...found.values()] });
      })
      .catch(() => {
        // The graph is a convenience here; an unreadable graph shows no pair rather than a false "fine".
        if (!cancelled) setPairs({ signature, pairs: [] });
      });
    return () => {
      cancelled = true;
    };
  }, [keys, signature]);

  return keys.length >= 2 && pairs.signature === signature ? pairs.pairs : EMPTY_PAIRS;
}

const EMPTY_PAIRS: MixPair[] = [];
