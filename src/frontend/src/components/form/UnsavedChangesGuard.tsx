import { useEffect } from 'react';
import { useBlocker } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import ConfirmDialog from '@/components/common/ConfirmDialog';

interface UnsavedChangesGuardProps {
  dirty: boolean;
}

export default function UnsavedChangesGuard({ dirty }: UnsavedChangesGuardProps) {
  const { t } = useTranslation();

  const blocker = useBlocker(dirty);

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
      open={blocker.state === 'blocked'}
      title={t('common.unsavedChanges')}
      message={t('common.unsavedChanges')}
      onConfirm={() => blocker.proceed?.()}
      onCancel={() => blocker.reset?.()}
    />
  );
}
