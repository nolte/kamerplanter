/**
 * The names of the recurring tasks a bed template brings (REQ-053 GP-FR-087, #2897): the template stores task
 * template keys only, so the panel reads each one (`GET /tasks/templates/{key}`, at most 20) to say what the
 * opt-in "create recurring tasks" will create. Loaded only for the picked template; a key that cannot be read is
 * counted in `unreadable` instead of being named - placing with the opt-in then answers 422 for it.
 */
import { useEffect, useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { getTaskTemplate } from '@/api/endpoints/tasks';
import type { TaskTemplate } from '@/api/types';
import { careTaskName } from '../care/careLabels';

export interface TemplateTaskNames {
  names: string[];
  unreadable: number;
  loading: boolean;
}

interface Loaded {
  /** The key list the answer belongs to, so an answer for a template picked earlier is never shown. */
  forKeys: string;
  templates: TaskTemplate[];
  unreadable: number;
}

export function useTemplateTaskNames(keys: readonly string[]): TemplateTaskNames {
  const { i18n } = useTranslation();
  const joined = keys.join('\n');
  const [loaded, setLoaded] = useState<Loaded | null>(null);
  useEffect(() => {
    if (joined === '') return undefined;
    let cancelled = false;
    const wanted = joined.split('\n');
    void Promise.allSettled(wanted.map((key) => getTaskTemplate(key))).then((answers) => {
      if (cancelled) return;
      const templates = answers.flatMap((answer) => (answer.status === 'fulfilled' ? [answer.value] : []));
      setLoaded({ forKeys: joined, templates, unreadable: wanted.length - templates.length });
    });
    return () => {
      cancelled = true;
    };
  }, [joined]);
  const current = loaded !== null && loaded.forKeys === joined ? loaded : null;
  const language = i18n.language;
  return useMemo(
    () => ({
      names: current ? current.templates.map((template) => careTaskName(template, language)) : [],
      unreadable: current ? current.unreadable : 0,
      loading: joined !== '' && current === null,
    }),
    [current, joined, language],
  );
}
