/**
 * The display name of a growth phase as the phase definitions name it ("Seedling", "flowering"): the
 * `enums.phaseName.<key>` text of a known phase in the active language, else the stored name itself (#2764).
 */
import type { TFunction } from 'i18next';

/** `enums.phaseName.<key>` for a phase name: "Flowering" and "flowering" alike, blanks and dashes as `_`. */
export function phaseKeyOf(name: string): string {
  return name.trim().toLowerCase().replace(/[\s-]+/g, '_');
}

export function phaseLabel(t: TFunction, name: string): string {
  return t(`enums.phaseName.${phaseKeyOf(name)}`, { defaultValue: name });
}
