/**
 * The name of a phase in the tent rules hint, in the reader's language (REQ-053 W-016.6, #2889).
 *
 * The server sends each phase as its machine name plus both catalogue display names and words nothing itself; the
 * client picks, like the phase pages do (`display_name_de` in German, `display_name` otherwise):
 *
 * 1. the catalogue name in the UI language,
 * 2. the app's own `enums.phaseName.<code>` translation (a legacy growth phase has no German catalogue name),
 * 3. in German only: the English catalogue name,
 * 4. the machine name.
 */
import type { TFunction } from 'i18next';
import { apiLanguage } from '@/i18n/apiLanguage';
import { phaseKeyOf, phaseLabel } from '../planting/phaseLabel';
import type { PhaseLabel, PhotoperiodGroup } from './types';

/** The part of the i18next instance the label needs: the active language and whether a key is translated. */
export interface PhaseLabelI18n {
  language: string;
  exists: (key: string) => boolean;
}

export function tentPhaseLabel(t: TFunction, i18n: PhaseLabelI18n, phase: PhaseLabel): string {
  const german = apiLanguage(i18n.language) === 'de';
  const own = (german ? phase.display_name_de : phase.display_name)?.trim();
  if (own) return own;
  const key = `enums.phaseName.${phaseKeyOf(phase.code)}`;
  if (i18n.exists(key)) return t(key);
  const english = phase.display_name?.trim();
  if (german && english) return english;
  return phase.code;
}

/**
 * The phase names of one photoperiod group, each once and sorted in the UI language. A backend without `phases`
 * sends only `phase_names` (English or machine names): those are translated where the app knows the phase.
 */
export function groupPhaseLabels(t: TFunction, i18n: PhaseLabelI18n, group: PhotoperiodGroup): string[] {
  const labels =
    group.phases && group.phases.length > 0
      ? group.phases.map((phase) => tentPhaseLabel(t, i18n, phase))
      : group.phase_names.map((name) => phaseLabel(t, name));
  return [...new Set(labels)].sort((a, b) => a.localeCompare(b, i18n.language));
}
