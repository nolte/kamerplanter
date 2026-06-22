import { useCallback } from 'react';
import { useTranslation } from 'react-i18next';

/**
 * Returns a function that picks the localized variant of a field.
 * Usage: const l = useLocalizedField();
 *        l(task, 'name')       → task.name_de (if DE) or task.name
 *        l(task, 'instruction') → task.instruction_de (if DE) or task.instruction
 */
export function useLocalizedField() {
  const { i18n } = useTranslation();

  return useCallback(
    <T extends object>(obj: T, field: string): string => {
      const rec = obj as Record<string, unknown>;
      if (i18n.language === 'de') {
        const deValue = rec[`${field}_de`];
        if (typeof deValue === 'string' && deValue) return deValue;
      }
      const value = rec[field];
      return typeof value === 'string' ? value : '';
    },
    [i18n.language],
  );
}
