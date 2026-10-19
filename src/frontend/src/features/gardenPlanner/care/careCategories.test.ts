/**
 * The context-dependent category offer (REQ-053 F-03, W-007): which categories a bed shows follows its
 * growing medium and its type; an unknown context hides nothing.
 */
import { describe, expect, it } from 'vitest';
import { categoriesFor, categoryFitsContext, formKindOf, taskTarget } from './careCategories';

describe('categoryFitsContext (F-03)', () => {
  it.each(['flush', 'ec_check', 'ph_adjustment'])('%s is offered on a substrate bed and hidden on native soil', (category) => {
    expect(categoryFitsContext(category, { growingMedium: 'potting_mix' })).toBe(true);
    expect(categoryFitsContext(category, { growingMedium: 'raised_bed_mix' })).toBe(true);
    expect(categoryFitsContext(category, { growingMedium: 'native_soil' })).toBe(false);
  });

  it.each(['hilling', 'tillage', 'liming'])('%s is hidden on pot substrates and offered on soil beds', (category) => {
    expect(categoryFitsContext(category, { growingMedium: 'native_soil' })).toBe(true);
    expect(categoryFitsContext(category, { growingMedium: 'raised_bed_mix' })).toBe(true);
    expect(categoryFitsContext(category, { growingMedium: 'potting_mix' })).toBe(false);
    expect(categoryFitsContext(category, { growingMedium: 'mineral_substrate' })).toBe(false);
  });

  it.each(['greenhouse', 'greenhouse_bed', 'cold_frame', 'tent'])('ventilating is offered in a %s', (type) => {
    expect(categoryFitsContext('ventilating', { locationTypeKey: type })).toBe(true);
  });

  it('hides ventilating in an open bed', () => {
    expect(categoryFitsContext('ventilating', { locationTypeKey: 'raised_bed' })).toBe(false);
  });

  it('hides nothing when the medium and the type are unknown', () => {
    for (const category of ['flush', 'hilling', 'ventilating', 'watering']) {
      expect(categoryFitsContext(category, {})).toBe(true);
    }
  });
});

describe('categoriesFor', () => {
  it('offers a free note in the log but not as a task, and keeps treatments out of the log (E-16)', () => {
    expect(categoriesFor({}, 'log')).toContain('note');
    expect(categoriesFor({}, 'task')).not.toContain('note');
    expect(categoriesFor({}, 'task')).toContain('pest_control');
    expect(categoriesFor({}, 'log')).not.toContain('pest_control');
  });

  it('narrows a native-soil raised bed in the open', () => {
    const offered = categoriesFor({ growingMedium: 'native_soil', locationTypeKey: 'raised_bed' }, 'task');
    expect(offered).toContain('hilling');
    expect(offered).not.toContain('flush');
    expect(offered).not.toContain('ventilating');
  });
});

describe('formKindOf (GP-FR-084)', () => {
  it('maps the categories to the five short forms and a note', () => {
    expect(formKindOf('watering')).toBe('watering');
    expect(formKindOf('flush')).toBe('watering');
    expect(formKindOf('feeding')).toBe('feeding');
    expect(formKindOf('mulching')).toBe('mulching');
    expect(formKindOf('weeding')).toBe('note');
    expect(formKindOf('anything_else')).toBe('note');
  });

  it('names what a task is bound to', () => {
    expect(taskTarget({ entity_type: 'location' })).toBe('bed');
    expect(taskTarget({ entity_type: 'plant_instance' })).toBe('plant');
    expect(taskTarget({ entity_type: 'tank' })).toBe('other');
    expect(taskTarget({ entity_type: null })).toBe('other');
  });
});
