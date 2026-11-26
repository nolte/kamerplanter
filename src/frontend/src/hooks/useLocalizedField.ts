import { useCallback } from 'react';
import { useTranslation } from 'react-i18next';
import { localizedText } from '@/utils/localizedText';

/**
 * Returns a function that picks the localized variant of a field, by the rule of
 * `localizedText` (UI language -> other language -> '').
 * Usage: const l = useLocalizedField();
 *        l(task, 'name')       → task.name_de in German (else task.name), task.name in English
 *        l(task, 'instruction') → task.instruction_de / task.instruction alike
 */
export function useLocalizedField() {
  const { i18n } = useTranslation();

  return useCallback(
    <T extends object>(obj: T, field: string): string => {
      const rec = obj as Record<string, unknown>;
      const text = (value: unknown) => (typeof value === 'string' ? value : null);
      return localizedText(i18n.language, { de: text(rec[`${field}_de`]), en: text(rec[field]) });
    },
    [i18n.language],
  );
}
