import { describe, it, expect } from 'vitest';
import { generateSlotId, generateBatchId, generateInstanceId } from '@/utils/idGenerator';

describe('idGenerator', () => {
  describe('generateSlotId', () => {
    it('matches LOCATION_POSITION format', () => {
      const id = generateSlotId('TENT01');
      expect(id).toMatch(/^[A-Z0-9]+_[A-Z0-9]{3}$/);
    });

    it('derives prefix from locationKey', () => {
      const id = generateSlotId('Rack3B');
      expect(id).toMatch(/^RACK3B_/);
    });

    it('uses fallback for empty input', () => {
      const id = generateSlotId('');
      expect(id).toMatch(/^SLOT_[A-Z0-9]{3}$/);
    });

    it('truncates long location keys to 8 chars', () => {
      const id = generateSlotId('VERYLONGLOCATIONNAME');
      const prefix = id.split('_')[0];
      expect(prefix.length).toBeLessThanOrEqual(8);
    });

    it('sanitizes special characters', () => {
      const id = generateSlotId('Zürich-1');
      expect(id).toMatch(/^ZURICH1_[A-Z0-9]{3}$/);
    });
  });

  describe('generateBatchId', () => {
    it('matches PREFIX-YYYY-NNN format', () => {
      const id = generateBatchId('COCO');
      const year = new Date().getFullYear();
      expect(id).toMatch(new RegExp(`^COCO-${year}-[A-Z0-9]{3}$`));
    });

    it('derives prefix from substrateKey', () => {
      const id = generateBatchId('Perlite');
      expect(id).toMatch(/^PERLIT-/);
    });

    it('uses fallback for empty input', () => {
      const id = generateBatchId('');
      const year = new Date().getFullYear();
      expect(id).toMatch(new RegExp(`^SUB-${year}-[A-Z0-9]{3}$`));
    });

    it('truncates long substrate keys to 6 chars', () => {
      const id = generateBatchId('SuperLongSubstrateName');
      const prefix = id.split('-')[0];
      expect(prefix.length).toBeLessThanOrEqual(6);
    });

    it('sanitizes diacritics', () => {
      const id = generateBatchId('Böden');
      expect(id).toMatch(/^BODEN-/);
    });
  });

  describe('generateInstanceId', () => {
    it('matches PREFIX-MMDD-NNN format', () => {
      const id = generateInstanceId('Cannabis');
      expect(id).toMatch(/^CANNA-\d{4}-[A-Z0-9]{3}$/);
    });

    it('derives prefix from species name', () => {
      const id = generateInstanceId('Tomato');
      expect(id).toMatch(/^TOMAT-/);
    });

    it('uses PLANT fallback for empty input', () => {
      const id = generateInstanceId('');
      expect(id).toMatch(/^PLANT-\d{4}-[A-Z0-9]{3}$/);
    });

    it('truncates long species names to 5 chars', () => {
      const id = generateInstanceId('Chrysanthemum');
      const prefix = id.split('-')[0];
      expect(prefix.length).toBeLessThanOrEqual(5);
    });

    it('sanitizes special characters', () => {
      const id = generateInstanceId('Ménthe');
      expect(id).toMatch(/^MENTH-/);
    });
  });
});
