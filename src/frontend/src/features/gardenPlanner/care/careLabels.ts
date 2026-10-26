/**
 * How a care task and a care category are named in the UI (REQ-053 §12): the bed's care tab, the care
 * log dialog and the field-mode sheet share these, so a task or a category never reads differently in two
 * places. Pure: the translator and the language are arguments.
 */
import type { TFunction } from 'i18next';
import { NOTE_CATEGORY } from './careCategories';
import type { CareTask } from './careTypes';

/** The task's name in the UI language: the German name where there is one and the UI speaks German. */
export function careTaskName(task: Pick<CareTask, 'name' | 'name_de'>, language: string): string {
  return (language.startsWith('de') && task.name_de) || task.name;
}

/** The name of a care category; the free note of the care log is not a task category (§20.10). */
export function careCategoryLabel(t: TFunction, category: string): string {
  return category === NOTE_CATEGORY ? t('pages.bed.care.log.noteCategory') : t(`enums.taskCategory.${category}`);
}
