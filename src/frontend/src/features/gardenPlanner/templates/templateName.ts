/** The display name of a template: the system templates are shipped in English and translated here by key. */
import type { TFunction } from 'i18next';
import type { BedTemplate } from '../model/types';

export function templateName(t: TFunction, template: BedTemplate): string {
  return template.is_system
    ? t(`pages.gardenPlan.editor.templates.system.${template.key}`, { defaultValue: template.name })
    : template.name;
}
