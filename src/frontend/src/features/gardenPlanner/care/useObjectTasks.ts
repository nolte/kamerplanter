/**
 * The open tasks of one garden object for the editor's properties panel (REQ-053 R-7.2, W-008). Reads only while
 * `enabled` (online, the object saved): an object the server does not know yet has no tasks to read.
 */
import { useCallback, useEffect, useMemo, useState } from 'react';
import type { TaskItem } from '@/api/types';
import { parseApiError } from '@/api/errors';
import { listOpenObjectTasks } from './careApi';

export type ObjectTasksState =
  | { status: 'idle' }
  | { status: 'loading' }
  | { status: 'ready'; tasks: TaskItem[]; loadedAt: number }
  | { status: 'error'; message: string };

export interface ObjectTasks {
  state: ObjectTasksState;
  reload: () => void;
}

/** The answer to one request; `request` names it, so an answer to an older request never shows. */
type Answer =
  | { request: string; status: 'ready'; tasks: TaskItem[]; loadedAt: number }
  | { request: string; status: 'error'; message: string };

const IDLE: ObjectTasksState = { status: 'idle' };
const LOADING: ObjectTasksState = { status: 'loading' };

export function useObjectTasks(objectKey: string, enabled: boolean): ObjectTasks {
  const [generation, setGeneration] = useState(0);
  const [answer, setAnswer] = useState<Answer | null>(null);
  // "Loading" is derived (no answer to the current request yet), so the effect sets state only in its callbacks.
  const request = `${objectKey}#${generation}`;

  useEffect(() => {
    if (!enabled) return undefined;
    let cancelled = false;
    listOpenObjectTasks(objectKey)
      .then((tasks) => {
        if (!cancelled) setAnswer({ request, status: 'ready', tasks, loadedAt: Date.now() });
      })
      .catch((error: unknown) => {
        if (!cancelled) setAnswer({ request, status: 'error', message: parseApiError(error) });
      });
    return () => {
      cancelled = true;
    };
  }, [objectKey, enabled, request]);

  const reload = useCallback(() => setGeneration((value) => value + 1), []);
  const state = useMemo<ObjectTasksState>(() => {
    if (!enabled) return IDLE;
    if (answer === null || answer.request !== request) return LOADING;
    return answer.status === 'ready'
      ? { status: 'ready', tasks: answer.tasks, loadedAt: answer.loadedAt }
      : { status: 'error', message: answer.message };
  }, [enabled, answer, request]);
  return useMemo(() => ({ state, reload }), [state, reload]);
}
