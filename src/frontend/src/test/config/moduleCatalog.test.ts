import { describe, it, expect } from 'vitest';

import {
  moduleCatalog,
  MODULE_CATEGORIES,
  findModuleByPath,
  type ModuleDefinition,
} from '@/config/moduleCatalog';

const nonCoreModules: ModuleDefinition[] = Object.values(moduleCatalog).filter(
  (m) => !m.core,
);

describe('moduleCatalog — path ownership (REQ-042)', () => {
  it('resolves the newly-controllable sidebar entries to their owning module', () => {
    expect(findModuleByPath('/ki-assistent')?.key).toBe('ai_assistant');
    expect(findModuleByPath('/glossar')?.key).toBe('glossary');
    expect(findModuleByPath('/inventree')?.key).toBe('inventory');
    // Prefix navPaths must also own the concrete list/detail routes.
    expect(findModuleByPath('/ueberwinterung/profile')?.key).toBe('overwintering');
    expect(findModuleByPath('/phasen/definitionen')?.key).toBe('phases');
    expect(findModuleByPath('/phasen/ablaeufe')?.key).toBe('phases');
  });

  it('reconciles the drifting navPaths with the real sidebar paths', () => {
    // automation used to own the phantom /umgebung; it must own the real entry.
    expect(findModuleByPath('/umgebungssteuerung')?.key).toBe('automation');
    // post_harvest used to own the phantom /post-harvest; the real sidebar path
    // is /ernte/nachernte and must resolve to post_harvest (longest-path wins),
    // while the sibling batches entry stays with the harvest module.
    expect(findModuleByPath('/ernte/nachernte')?.key).toBe('post_harvest');
    expect(findModuleByPath('/ernte/batches')?.key).toBe('harvest');
  });

  it('no longer contains the removed phantom modules', () => {
    const keys = Object.keys(moduleCatalog);
    expect(keys).not.toContain('care');
    expect(keys).not.toContain('sensors');
    expect(keys).not.toContain('smart_home');
  });

  it('lists every non-core module category in MODULE_CATEGORIES', () => {
    for (const m of nonCoreModules) {
      expect(MODULE_CATEGORIES).toContain(m.category);
    }
  });

  it('gives every non-core module at least one navPath', () => {
    for (const m of nonCoreModules) {
      expect(m.navPaths.length).toBeGreaterThan(0);
    }
  });

  it('returns undefined for a path owned by no module', () => {
    // Mechanism guard: the sidebar↔catalog sync test relies on this returning
    // undefined for any ungoverned path, which is what makes an unmapped future
    // sidebar entry fail the sync assertion.
    expect(findModuleByPath('/totally/unmapped')).toBeUndefined();
  });
});
