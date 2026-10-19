/**
 * Loads a history list a page at a time (REQ-053 GP-FR-102: pages of 50). `resetKey` names the query:
 * when it changes the list starts again from the first page; "load more" appends the next one. A
 * page shorter than the page size is the last. Newer answers win - a slow answer to an old filter
 * never replaces the list of the current one.
 */
import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { parseApiError } from '@/api/errors';
import { HISTORY_PAGE_SIZE } from './historyApi';

export type HistoryPagesState<T> =
  | { status: 'loading' }
  | { status: 'error'; message: string }
  | { status: 'ready'; items: T[]; hasMore: boolean; loadingMore: boolean; moreError: string | null };

export interface HistoryPages<T> {
  state: HistoryPagesState<T>;
  loadMore: () => void;
  /** Fetch the first page again without blanking the list. */
  reload: () => void;
}

export function useHistoryPages<T>(
  fetchPage: (offset: number) => Promise<T[]>,
  resetKey: string,
): HistoryPages<T> {
  const [state, setState] = useState<HistoryPagesState<T>>({ status: 'loading' });
  const [attempt, setAttempt] = useState(0);
  const fetchRef = useRef(fetchPage);
  const stateRef = useRef(state);
  const generation = useRef(0);
  const lastKey = useRef(resetKey);

  // The latest callback and state for the effects and handlers below; written after the render, never during it.
  useEffect(() => {
    fetchRef.current = fetchPage;
    stateRef.current = state;
  });

  useEffect(() => {
    const mine = (generation.current += 1);
    // A new query starts from a blank list; a reload keeps the rows while the request runs.
    if (lastKey.current !== resetKey) {
      lastKey.current = resetKey;
      setState({ status: 'loading' });
    }
    fetchRef
      .current(0)
      .then((page) => {
        if (generation.current === mine) {
          setState({
            status: 'ready',
            items: page,
            hasMore: page.length >= HISTORY_PAGE_SIZE,
            loadingMore: false,
            moreError: null,
          });
        }
      })
      .catch((error: unknown) => {
        if (generation.current === mine) setState({ status: 'error', message: parseApiError(error) });
      });
    return () => {
      generation.current += 1;
    };
  }, [resetKey, attempt]);

  const loadMore = useCallback(() => {
    const current = stateRef.current;
    if (current.status !== 'ready' || current.loadingMore || !current.hasMore) return;
    const mine = generation.current;
    setState({ ...current, loadingMore: true, moreError: null });
    fetchRef
      .current(current.items.length)
      .then((page) => {
        if (generation.current !== mine) return;
        setState((latest) =>
          latest.status === 'ready'
            ? {
                status: 'ready',
                items: [...latest.items, ...page],
                hasMore: page.length >= HISTORY_PAGE_SIZE,
                loadingMore: false,
                moreError: null,
              }
            : latest,
        );
      })
      .catch((error: unknown) => {
        if (generation.current !== mine) return;
        setState((latest) =>
          latest.status === 'ready' ? { ...latest, loadingMore: false, moreError: parseApiError(error) } : latest,
        );
      });
  }, []);

  const reload = useCallback(() => setAttempt((value) => value + 1), []);
  return useMemo(() => ({ state, loadMore, reload }), [state, loadMore, reload]);
}
