/**
 * The shared names of care tasks and categories (REQ-053 §12): the bed's care tab, the care log and the
 * field sheet read them from one place.
 */
import type { TFunction } from 'i18next';
import { describe, expect, it } from 'vitest';
import { NOTE_CATEGORY } from './careCategories';
import { careCategoryLabel, careTaskName } from './careLabels';

const t = ((key: string) => `t:${key}`) as unknown as TFunction;

describe('care labels', () => {
  it('names a task in German only where a German name exists', () => {
    expect(careTaskName({ name: 'Water', name_de: 'Gießen' }, 'de-DE')).toBe('Gießen');
    expect(careTaskName({ name: 'Water', name_de: '' }, 'de')).toBe('Water');
    expect(careTaskName({ name: 'Water', name_de: 'Gießen' }, 'en')).toBe('Water');
  });

  it('names the free note apart from the task categories', () => {
    expect(careCategoryLabel(t, NOTE_CATEGORY)).toBe('t:pages.bed.care.log.noteCategory');
    expect(careCategoryLabel(t, 'weeding')).toBe('t:enums.taskCategory.weeding');
  });
});
