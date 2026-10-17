import { describe, expect, it } from 'vitest';
import { bed, gardenObject, smallPlan } from '@/test/gardenPlanFixtures';
import {
  applyOperation,
  applyOperations,
  PlanOperationError,
  remapOperationKeys,
} from './applyOperation';
import { newTempKey, normalizePlan, UnsupportedPlanSchemaError } from './planModel';
import type { Geometry, PlanOperation } from './types';
import { planResponse } from '@/test/gardenPlanFixtures';

const RECT_A: Geometry = {
  kind: 'rect',
  origin: [1, 1],
  width_m: 1.2,
  length_m: 2,
  rotation_deg: 0,
};
const RECT_MOVED: Geometry = {
  kind: 'rect',
  origin: [2, 3],
  width_m: 1.2,
  length_m: 2,
  rotation_deg: 0,
};

function roundTrip(op: PlanOperation) {
  const before = smallPlan();
  const applied = applyOperation(before, op);
  expect(applied.inverse).not.toBeNull();
  const restored = applyOperations(applied.plan, applied.inverse ?? []);
  return { before, applied, restored: restored.plan };
}

describe('applyOperation', () => {
  it('does not mutate its input and shares what it does not change', () => {
    const before = smallPlan();
    const frozen = JSON.stringify(before);
    const { plan } = applyOperation(before, {
      op: 'update_geometry',
      entity: 'location',
      key: 'loc_a',
      geometry: RECT_MOVED,
    });
    expect(JSON.stringify(before)).toBe(frozen);
    expect(plan.locations.loc_b).toBe(before.locations.loc_b);
    expect(plan.slots).toBe(before.slots);
    expect(plan.gardenObjects).toBe(before.gardenObjects);
  });

  describe('update_geometry', () => {
    it('moves a bed and re-derives area and bbox (GP-FR-006/007)', () => {
      const { plan } = applyOperation(smallPlan(), {
        op: 'update_geometry',
        entity: 'location',
        key: 'loc_a',
        geometry: { ...RECT_MOVED, rotation_deg: 90 },
      });
      expect(plan.locations.loc_a.geometry).toEqual({ ...RECT_MOVED, rotation_deg: 90 });
      expect(plan.locations.loc_a.area_m2).toBe(2.4);
      expect(plan.locations.loc_a.bbox).toEqual([0, 3, 2, 4.2]);
    });

    it('is inverted by the previous geometry', () => {
      const { before, applied, restored } = roundTrip({
        op: 'update_geometry',
        entity: 'location',
        key: 'loc_a',
        geometry: RECT_MOVED,
      });
      expect(applied.inverse).toEqual([
        { op: 'update_geometry', entity: 'location', key: 'loc_a', geometry: RECT_A },
      ]);
      expect(restored).toEqual(before);
    });

    it('refuses a locked object and an unknown key', () => {
      const locked = smallPlan({ locations: [bed('loc_a', 1, 1, { locked: true })] });
      expect(() =>
        applyOperation(locked, {
          op: 'update_geometry',
          entity: 'location',
          key: 'loc_a',
          geometry: RECT_MOVED,
        }),
      ).toThrow(expect.objectContaining({ code: 'object.locked' }));
      expect(() =>
        applyOperation(smallPlan(), {
          op: 'update_geometry',
          entity: 'location',
          key: 'nope',
          geometry: RECT_MOVED,
        }),
      ).toThrow(PlanOperationError);
    });

    it('has no wire inverse for a bed that was not placed on the plan', () => {
      const plan = smallPlan({
        locations: [{ ...bed('loc_a', 1, 1), geometry: null, area_m2: 0, bbox: null }],
      });
      const applied = applyOperation(plan, {
        op: 'update_geometry',
        entity: 'location',
        key: 'loc_a',
        geometry: RECT_A,
      });
      expect(applied.plan.locations.loc_a.geometry).toEqual(RECT_A);
      expect(applied.inverse).toBeNull();
    });

    it('spans a point object with the 0.25 m symbol (§9.5)', () => {
      const plan = smallPlan({
        garden_objects: [
          gardenObject('go_w', 5, 5, {
            object_type: 'water_source',
            geometry: { kind: 'point', origin: [5, 5] },
            props: { object_type: 'water_source', water_source_kind: 'tap' },
          }),
        ],
      });
      const { plan: next } = applyOperation(plan, {
        op: 'update_geometry',
        entity: 'garden_object',
        key: 'go_w',
        geometry: { kind: 'point', origin: [6, 7] },
      });
      expect(next.gardenObjects.go_w.bbox).toEqual([5.75, 6.75, 6.25, 7.25]);
    });
  });

  describe('create', () => {
    it('creates a location under a parent and is inverted by a delete', () => {
      const { before, applied, restored } = roundTrip({
        op: 'create_location',
        temp_key: 'tmp1',
        data: {
          name: 'Bed 6',
          location_type_key: 'bed',
          parent_location_key: 'loc_a',
          geometry: RECT_MOVED,
        },
      });
      const created = applied.plan.locations.tmp1;
      expect(created).toMatchObject({
        name: 'Bed 6',
        depth: 1,
        parent_location_key: 'loc_a',
        area_m2: 2.4,
      });
      expect(created.bed_status).toBe('active');
      expect(restored).toEqual(before);
    });

    it('refuses a duplicate temp key and an unknown parent', () => {
      const base: PlanOperation = {
        op: 'create_location',
        temp_key: 'loc_a',
        data: { name: 'x', location_type_key: 'bed', geometry: RECT_A },
      };
      expect(() => applyOperation(smallPlan(), base)).toThrow(
        expect.objectContaining({ code: 'temp_key.duplicate' }),
      );
      expect(() =>
        applyOperation(smallPlan(), {
          ...base,
          temp_key: 'tmp1',
          data: { ...(base as { data: object }).data, parent_location_key: 'ghost' },
        } as PlanOperation),
      ).toThrow(expect.objectContaining({ code: 'reference.not_found' }));
    });

    it('lets a later operation of the same action refer to a temp key (batch semantics)', () => {
      const { plan } = applyOperations(smallPlan(), [
        {
          op: 'create_location',
          temp_key: 'tmp1',
          data: { name: 'A', location_type_key: 'bed', geometry: RECT_A },
        },
        {
          op: 'create_location',
          temp_key: 'tmp2',
          data: {
            name: 'B',
            location_type_key: 'bed',
            parent_location_key: 'tmp1',
            geometry: RECT_MOVED,
          },
        },
        { op: 'update_geometry', entity: 'location', key: 'tmp2', geometry: RECT_A },
      ]);
      expect(plan.locations.tmp2.depth).toBe(1);
      expect(plan.locations.tmp2.geometry).toEqual(RECT_A);
    });

    it('fills the discriminator and the crown radius of a tree from its circle (§9.5)', () => {
      const { plan, inverse } = applyOperation(smallPlan(), {
        op: 'create_garden_object',
        temp_key: 'tmp9',
        data: {
          object_type: 'tree',
          label: ' Apple ',
          geometry: { kind: 'circle', origin: [3, 3], radius_m: 2 },
          props: { foliage: 'deciduous' },
        },
      });
      expect(plan.gardenObjects.tmp9).toMatchObject({
        label: 'Apple',
        site_key: 'site_1',
        bbox: [1, 1, 5, 5],
        props: { object_type: 'tree', foliage: 'deciduous', crown_radius_m: 2 },
      });
      expect(inverse).toEqual([{ op: 'delete', entity: 'garden_object', key: 'tmp9' }]);
    });
  });

  describe('update_fields', () => {
    it('renames a bed and inverts with the old name', () => {
      const { before, applied, restored } = roundTrip({
        op: 'update_fields',
        entity: 'location',
        key: 'loc_a',
        fields: { name: 'Tomatoes', sun_exposure: 'full_sun', height_m: 0.4 },
      });
      expect(applied.plan.locations.loc_a).toMatchObject({
        name: 'Tomatoes',
        sun_exposure: 'full_sun',
        height_m: 0.4,
      });
      expect(applied.inverse).toEqual([
        {
          op: 'update_fields',
          entity: 'location',
          key: 'loc_a',
          fields: { name: 'Bed loc_a', sun_exposure: 'unknown', height_m: null },
        },
      ]);
      expect(restored).toEqual(before);
    });

    it('has no wire inverse for a field the lean read model does not carry', () => {
      const applied = applyOperation(smallPlan(), {
        op: 'update_fields',
        entity: 'location',
        key: 'loc_a',
        fields: { notes: 'north side' },
      });
      expect(applied.plan.locations.loc_a.notes).toBe('north side');
      expect(applied.inverse).toBeNull();
    });

    it('edits a garden object including its props and keeps the discriminator', () => {
      const { before, applied, restored } = roundTrip({
        op: 'update_fields',
        entity: 'garden_object',
        key: 'go_1',
        fields: {
          label: 'Old pear',
          notes: 'planted 2012',
          props: { crown_radius_m: 1, foliage: 'evergreen' },
        },
      });
      expect(applied.plan.gardenObjects.go_1.props).toEqual({
        object_type: 'tree',
        crown_radius_m: 1,
        foliage: 'evergreen',
      });
      expect(restored).toEqual(before);
    });
  });

  describe('delete', () => {
    it('removes a bed with its slots and plants and rebuilds the bed when inverted without plants', () => {
      const plan = smallPlan({ plants: [] });
      const applied = applyOperation(plan, { op: 'delete', entity: 'location', key: 'loc_a' });
      expect(applied.plan.locations.loc_a).toBeUndefined();
      expect(applied.plan.slots.slot_1).toBeUndefined();
      expect(applied.inverse).toEqual([
        expect.objectContaining({ op: 'create_location', temp_key: 'loc_a' }),
      ]);
      const restored = applyOperations(applied.plan, applied.inverse ?? []).plan;
      expect(restored.locations.loc_a).toMatchObject({ name: 'Bed loc_a', geometry: RECT_A });
    });

    it('is not undoable once saved when plants stand in the bed (GP-FR-155)', () => {
      const applied = applyOperation(smallPlan(), {
        op: 'delete',
        entity: 'location',
        key: 'loc_a',
      });
      expect(applied.plan.plants.pl_1).toBeUndefined();
      expect(applied.inverse).toBeNull();
    });

    it('cascades to descendants and the objects inside, parent first in the inverse', () => {
      const plan = smallPlan({
        locations: [bed('p', 0, 0), bed('c', 0, 0, { parent_location_key: 'p', depth: 1 })],
        garden_objects: [
          gardenObject('go_in', 1, 1, { parent_location_key: 'c' }),
          gardenObject('go_out', 9, 9),
        ],
        slots: [],
        plants: [],
      });
      const applied = applyOperation(plan, { op: 'delete', entity: 'location', key: 'p' });
      expect(Object.keys(applied.plan.locations)).toEqual([]);
      expect(Object.keys(applied.plan.gardenObjects)).toEqual(['go_out']);
      expect(applied.inverse?.map((op) => op.op)).toEqual([
        'create_location',
        'create_location',
        'create_garden_object',
      ]);
      const restored = applyOperations(applied.plan, applied.inverse ?? []).plan;
      expect(restored.locations.c.parent_location_key).toBe('p');
      expect(restored.locations.c.depth).toBe(1);
      expect(restored.gardenObjects.go_in.parent_location_key).toBe('c');
    });

    it('refuses to delete a locked bed or a bed that holds a locked one', () => {
      const plan = smallPlan({
        locations: [
          bed('p', 0, 0),
          bed('c', 0, 0, { parent_location_key: 'p', depth: 1, locked: true }),
        ],
        slots: [],
        plants: [],
      });
      expect(() => applyOperation(plan, { op: 'delete', entity: 'location', key: 'p' })).toThrow(
        expect.objectContaining({ code: 'object.locked', key: 'c' }),
      );
    });

    it('deletes an object and inverts it by a create with the same key', () => {
      const applied = applyOperation(smallPlan(), {
        op: 'delete',
        entity: 'garden_object',
        key: 'go_1',
      });
      expect(applied.plan.gardenObjects.go_1).toBeUndefined();
      const restored = applyOperations(applied.plan, applied.inverse ?? []).plan;
      expect(restored.gardenObjects.go_1).toMatchObject({
        label: 'Tree go_1',
        object_type: 'tree',
      });
    });
  });

  describe('set_boundary, set_locked, set_z_order', () => {
    it('sets the boundary and is inverted by the previous outline and settings', () => {
      const boundary: Geometry = {
        kind: 'rect',
        origin: [0, 0],
        width_m: 50,
        length_m: 50,
        rotation_deg: 0,
      };
      const { before, applied, restored } = roundTrip({
        op: 'set_boundary',
        boundary,
        north_angle_deg: 90,
      });
      expect(applied.plan.settings).toMatchObject({
        boundary,
        north_angle_deg: 90,
        default_grid_m: 0.1,
      });
      expect(restored.settings).toEqual(before.settings);
    });

    it('creates the settings of a site without a plan, with no wire inverse', () => {
      const plan = smallPlan({ plan: null });
      const boundary: Geometry = {
        kind: 'rect',
        origin: [0, 0],
        width_m: 10,
        length_m: 10,
        rotation_deg: 0,
      };
      const applied = applyOperation(plan, { op: 'set_boundary', boundary });
      expect(applied.plan.settings).toMatchObject({
        boundary,
        north_angle_deg: 0,
        default_grid_m: 0.1,
        adjacency_factor: 1.5,
      });
      expect(applied.inverse).toBeNull();
    });

    it('toggles the lock and the z-order and inverts both', () => {
      const lock = roundTrip({ op: 'set_locked', entity: 'location', key: 'loc_a', locked: true });
      expect(lock.applied.plan.locations.loc_a.locked).toBe(true);
      expect(lock.restored).toEqual(lock.before);
      const z = roundTrip({ op: 'set_z_order', entity: 'garden_object', key: 'go_1', z_order: 5 });
      expect(z.applied.plan.gardenObjects.go_1.z_order).toBe(5);
      expect(z.restored).toEqual(z.before);
    });
  });

  describe('applyOperations', () => {
    it('inverts a multi-operation action in reverse order (GP-FR-155 mehrfach-move)', () => {
      const before = smallPlan();
      const ops: PlanOperation[] = [
        { op: 'update_geometry', entity: 'location', key: 'loc_a', geometry: RECT_MOVED },
        {
          op: 'update_geometry',
          entity: 'location',
          key: 'loc_a',
          geometry: { ...RECT_MOVED, origin: [9, 9] },
        },
        { op: 'update_geometry', entity: 'location', key: 'loc_b', geometry: RECT_MOVED },
      ];
      const applied = applyOperations(before, ops);
      expect(applyOperations(applied.plan, applied.inverse ?? []).plan).toEqual(before);
    });

    it('leaves the plan untouched when one operation is refused', () => {
      const before = smallPlan();
      const frozen = JSON.stringify(before);
      expect(() =>
        applyOperations(before, [
          { op: 'update_geometry', entity: 'location', key: 'loc_a', geometry: RECT_MOVED },
          { op: 'delete', entity: 'location', key: 'ghost' },
        ]),
      ).toThrow(PlanOperationError);
      expect(JSON.stringify(before)).toBe(frozen);
    });

    it('has no inverse when one step has none', () => {
      const applied = applyOperations(smallPlan(), [
        { op: 'update_fields', entity: 'location', key: 'loc_a', fields: { notes: 'x' } },
        { op: 'set_z_order', entity: 'location', key: 'loc_a', z_order: 1 },
      ]);
      expect(applied.inverse).toBeNull();
    });
  });

  describe('remapOperationKeys', () => {
    it('renames existing keys and parents but not the temp key of a create', () => {
      const map = { tmp1: 'loc_9' };
      expect(remapOperationKeys({ op: 'delete', entity: 'location', key: 'tmp1' }, map)).toEqual({
        op: 'delete',
        entity: 'location',
        key: 'loc_9',
      });
      const create: PlanOperation = {
        op: 'create_location',
        temp_key: 'tmp1',
        data: {
          name: 'x',
          location_type_key: 'bed',
          parent_location_key: 'tmp1',
          geometry: RECT_A,
        },
      };
      expect(remapOperationKeys(create, map)).toMatchObject({
        temp_key: 'tmp1',
        data: { parent_location_key: 'loc_9' },
      });
      const other: PlanOperation = { op: 'delete', entity: 'location', key: 'loc_a' };
      expect(remapOperationKeys(other, map)).toBe(other);
    });
  });
});

describe('normalizePlan', () => {
  it('normalises the response into maps by key', () => {
    const plan = smallPlan();
    expect(Object.keys(plan.locations)).toEqual(['loc_a', 'loc_b']);
    expect(plan.slots.slot_1.location_key).toBe('loc_a');
    expect(plan.revision).toBe(42);
    expect(plan.settings?.north_angle_deg).toBe(15);
  });

  it('keeps a site without a plan and refuses another schema version', () => {
    expect(smallPlan({ plan: null }).settings).toBeNull();
    expect(() => normalizePlan(planResponse({ schema_version: '2' }))).toThrow(
      UnsupportedPlanSchemaError,
    );
  });
});

describe('newTempKey', () => {
  it('yields keys the batch accepts, unique within the session', () => {
    const keys = Array.from({ length: 50 }, () => newTempKey());
    for (const key of keys) expect(key).toMatch(/^[A-Za-z0-9_-]{1,40}$/);
    expect(new Set(keys).size).toBe(keys.length);
  });
});
