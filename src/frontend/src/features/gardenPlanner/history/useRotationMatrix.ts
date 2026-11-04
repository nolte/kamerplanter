/**
 * Loads the rotation matrix of a site page by page (`GET /sites/{key}/rotation-matrix`, REQ-053 GP-FR-135).
 * The first page decides the look-back; every later page and every refresh asks for the same `years`, so the
 * columns line up. A refresh after a year was filled in fetches again as many beds as are on screen, so a bed from
 * a later page does not vanish. Every request carries a generation: an answer to an outdated request (another site,
 * a newer refresh) is dropped.
 */
import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { parseApiError } from '@/api/errors';
import { getRotationMatrix } from './historyApi';
import type { RotationMatrix } from './historyTypes';
import { type FamilyMark, familyMarks, hasMoreBeds, mergeMatrixPage } from './rotationMatrix';

export type MatrixState =
  | { status: 'loading' }
  | { status: 'error'; message: string }
  | {
      status: 'ready';
      matrix: RotationMatrix;
      /** The family marks, in the order they were first shown: a further page does not recolour what is on screen. */
      marks: ReadonlyMap<string, FamilyMark>;
      busy: boolean;
      failure: 'more' | 'refresh' | null;
    };

/**
 * Fetch the first page, then more pages until `atLeast` beds are held or the matrix has no more. A page that adds
 * no bed ends the loop (a server that ignores the offset must not make it spin).
 */
async function fetchBeds(siteKey: string, atLeast: number, years: number | undefined): Promise<RotationMatrix> {
  let matrix = await getRotationMatrix(siteKey, 0, years);
  while (matrix.beds.length < atLeast && hasMoreBeds(matrix)) {
    const merged = mergeMatrixPage(matrix, await getRotationMatrix(siteKey, matrix.beds.length, matrix.years));
    if (merged.beds.length === matrix.beds.length) break;
    matrix = merged;
  }
  return matrix;
}

export function useRotationMatrix(siteKey: string) {
  const [state, setState] = useState<MatrixState>({ status: 'loading' });
  const matrixRef = useRef<RotationMatrix | null>(null);
  const marksRef = useRef<ReadonlyMap<string, FamilyMark>>(new Map());
  const generation = useRef(0);

  const ready = useCallback((matrix: RotationMatrix, busy = false, failure: 'more' | 'refresh' | null = null) => {
    matrixRef.current = matrix;
    marksRef.current = familyMarks(matrix.beds, [...marksRef.current.keys()]);
    setState({ status: 'ready', matrix, marks: marksRef.current, busy, failure });
  }, []);

  const load = useCallback(() => {
    const mine = ++generation.current;
    matrixRef.current = null;
    fetchBeds(siteKey, 0, undefined)
      .then((matrix) => {
        if (generation.current === mine) ready(matrix);
      })
      .catch((error: unknown) => {
        if (generation.current === mine) setState({ status: 'error', message: parseApiError(error) });
      });
  }, [siteKey, ready]);

  // The caller keys the component by site, so a new site starts with a fresh hook: nothing of an old one stays on
  // screen or in a merge. The state starts as `loading`, so nothing is set synchronously here.
  useEffect(() => {
    load();
    return () => {
      generation.current += 1;
    };
  }, [load]);

  /** Refetch what is on screen (after a year was filled in or taken back); the retry of a failed first load. */
  const reload = useCallback(() => {
    const current = matrixRef.current;
    if (current === null) {
      setState({ status: 'loading' });
      load();
      return;
    }
    const mine = ++generation.current;
    setState({ status: 'ready', matrix: current, marks: marksRef.current, busy: true, failure: null });
    fetchBeds(siteKey, current.beds.length, current.years)
      .then((matrix) => {
        if (generation.current === mine) ready(matrix);
      })
      .catch(() => {
        if (generation.current === mine) ready(current, false, 'refresh');
      });
  }, [siteKey, load, ready]);

  const loadMore = useCallback(() => {
    const current = matrixRef.current;
    if (current === null || !hasMoreBeds(current)) return;
    const mine = ++generation.current;
    setState({ status: 'ready', matrix: current, marks: marksRef.current, busy: true, failure: null });
    getRotationMatrix(siteKey, current.beds.length, current.years)
      .then((next) => {
        if (generation.current === mine) ready(mergeMatrixPage(current, next));
      })
      .catch(() => {
        if (generation.current === mine) ready(current, false, 'more');
      });
  }, [siteKey, ready]);

  return useMemo(() => ({ state, reload, loadMore }), [state, reload, loadMore]);
}
