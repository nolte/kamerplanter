import { useEffect, useState } from 'react';
import { useBlocker } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import ConfirmDialog from '@/components/common/ConfirmDialog';

interface UnsavedChangesGuardProps {
  dirty: boolean;
}

export default function UnsavedChangesGuard({ dirty }: UnsavedChangesGuardProps) {
  const { t } = useTranslation();

  const blocker = useBlocker(dirty);

  // Every blocked navigation gets its own dialog instance, keyed by the
  // attempted location. Re-opening the previous instance while its closing
  // transition still runs leaves it where it was in the DOM: if another modal
  // opened in between (an activity picker whose call to action links away),
  // that modal has marked it aria-hidden and sits on top of it, so the prompt
  // is neither reachable nor focused. A fresh instance mounts its portal last,
  // on top, and takes focus. The key is updated during render, not in an
  // effect, so the instance that opens is already the new one; it changes
  // only on a new block, which keeps the closing animation of the current one.
  const blockedKey = blocker.state === 'blocked' ? blocker.location.key : null;
  const [promptKey, setPromptKey] = useState<string | null>(null);
  if (blockedKey !== null && blockedKey !== promptKey) {
    setPromptKey(blockedKey);
  }

  useEffect(() => {
    if (!dirty) return;

    const handler = (e: BeforeUnloadEvent) => {
      e.preventDefault();
    };
    window.addEventListener('beforeunload', handler);
    return () => window.removeEventListener('beforeunload', handler);
  }, [dirty]);

  return (
    <ConfirmDialog
      key={promptKey ?? 'none'}
      open={blocker.state === 'blocked'}
      title={t('common.unsavedChanges')}
      message={t('common.unsavedChanges')}
      onConfirm={() => blocker.proceed?.()}
      onCancel={() => blocker.reset?.()}
    />
  );
}
