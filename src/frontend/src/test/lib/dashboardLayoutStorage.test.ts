import { describe, it, expect, beforeEach, vi } from 'vitest';
import {
  readLocalDashboardLayout,
  writeLocalDashboardLayout,
  clearLocalDashboardLayout,
  isPersonalizationHintDismissed,
  dismissPersonalizationHint,
} from '@/lib/dashboardLayoutStorage';
import type { DashboardLayout } from '@/api/types';

const KEY = 'kp-dashboard-layout';
const HINT_KEY = 'dashboard_personalization_hint_dismissed';

// jsdom in this environment ships no native localStorage; mirror the map-backed
// mock the other storage tests use (see useLocalFavorites.test.ts).
const storageMap = new Map<string, string>();
const mockLocalStorage = {
  getItem: vi.fn((key: string) => storageMap.get(key) ?? null),
  setItem: vi.fn((key: string, value: string) => storageMap.set(key, value)),
  removeItem: vi.fn((key: string) => storageMap.delete(key)),
  clear: vi.fn(() => storageMap.clear()),
};
Object.defineProperty(globalThis, 'localStorage', { value: mockLocalStorage, writable: true });

const layout = { widgets: [{ id: 'w1', type: 'metric' }] } as unknown as DashboardLayout;

describe('dashboardLayoutStorage', () => {
  beforeEach(() => {
    storageMap.clear();
    vi.clearAllMocks();
    mockLocalStorage.getItem.mockImplementation((key: string) => storageMap.get(key) ?? null);
    mockLocalStorage.setItem.mockImplementation((key: string, value: string) => storageMap.set(key, value));
    mockLocalStorage.removeItem.mockImplementation((key: string) => storageMap.delete(key));
  });

  describe('readLocalDashboardLayout', () => {
    it('returns null when nothing is stored', () => {
      expect(readLocalDashboardLayout()).toBeNull();
    });

    it('round-trips a written layout', () => {
      writeLocalDashboardLayout(layout);
      expect(readLocalDashboardLayout()).toEqual(layout);
    });

    it('returns null for a non-object JSON value', () => {
      storageMap.set(KEY, '123');
      expect(readLocalDashboardLayout()).toBeNull();
    });

    it('returns null for malformed JSON instead of throwing', () => {
      storageMap.set(KEY, '{not valid json');
      expect(readLocalDashboardLayout()).toBeNull();
    });

    it('returns null (not a throw) when storage access fails', () => {
      mockLocalStorage.getItem.mockImplementation(() => {
        throw new Error('SecurityError');
      });
      expect(readLocalDashboardLayout()).toBeNull();
    });
  });

  describe('writeLocalDashboardLayout', () => {
    it('removes the key when given null', () => {
      writeLocalDashboardLayout(layout);
      writeLocalDashboardLayout(null);
      expect(storageMap.has(KEY)).toBe(false);
    });

    it('swallows storage errors silently', () => {
      mockLocalStorage.setItem.mockImplementation(() => {
        throw new Error('QuotaExceeded');
      });
      expect(() => writeLocalDashboardLayout(layout)).not.toThrow();
    });
  });

  describe('clearLocalDashboardLayout', () => {
    it('removes any stored layout', () => {
      writeLocalDashboardLayout(layout);
      clearLocalDashboardLayout();
      expect(storageMap.has(KEY)).toBe(false);
    });

    it('swallows storage errors silently', () => {
      mockLocalStorage.removeItem.mockImplementation(() => {
        throw new Error('SecurityError');
      });
      expect(() => clearLocalDashboardLayout()).not.toThrow();
    });
  });

  describe('personalization hint (U-005)', () => {
    it('is not dismissed by default', () => {
      expect(isPersonalizationHintDismissed()).toBe(false);
    });

    it('reports dismissed after dismissPersonalizationHint', () => {
      dismissPersonalizationHint();
      expect(storageMap.get(HINT_KEY)).toBe('true');
      expect(isPersonalizationHintDismissed()).toBe(true);
    });

    it('treats storage failure as dismissed (do not nag)', () => {
      mockLocalStorage.getItem.mockImplementation(() => {
        throw new Error('SecurityError');
      });
      expect(isPersonalizationHintDismissed()).toBe(true);
    });

    it('swallows storage errors when dismissing', () => {
      mockLocalStorage.setItem.mockImplementation(() => {
        throw new Error('QuotaExceeded');
      });
      expect(() => dismissPersonalizationHint()).not.toThrow();
    });
  });
});
