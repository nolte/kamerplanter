import { describe, it, expect } from 'vitest';
import { screen } from '@testing-library/react';
import type { ModuleVisibilityState } from '@/api/types';

import Sidebar from '@/layouts/Sidebar';
import { findModuleByPath, moduleCatalog, type ModuleKey } from '@/config/moduleCatalog';
import {
  createStoreWithExpertise,
  createStoreWithModuleOverrides,
  renderWithProviders,
} from '../helpers';

/** Every non-core module explicitly enabled — surfaces the full sidebar. */
const ALL_MODULES_ENABLED: Record<string, ModuleVisibilityState> = Object.fromEntries(
  Object.values(moduleCatalog)
    .filter((m) => !m.core)
    .map((m) => [m.key, 'enabled' as ModuleVisibilityState]),
);

/** Collect the paths of every navigable sidebar entry currently rendered. */
function renderedSidebarPaths(): string[] {
  return Array.from(document.querySelectorAll('[data-testid^="nav-/"]')).map((el) =>
    (el.getAttribute('data-testid') ?? '').slice('nav-'.length),
  );
}

describe('Sidebar — REQ-042 module overrides vs. experience level', () => {
  it('hides the expert-gated Ernte section for a beginner by default', () => {
    renderWithProviders(<Sidebar open />, {
      store: createStoreWithExpertise('beginner'),
    });
    expect(screen.queryByTestId('nav-/ernte/batches')).toBeNull();
  });

  it('reveals the Ernte section when the harvest module is enabled via a personal override', () => {
    // Regression test: the section-level gate is override-blind, so enabling the
    // harvest module as a beginner must still surface its menu item.
    renderWithProviders(<Sidebar open />, {
      store: createStoreWithModuleOverrides('beginner', { harvest: 'enabled' }),
    });
    expect(screen.getByTestId('nav-/ernte/batches')).toBeInTheDocument();
  });

  it('keeps a disabled override hidden even when the level would show the item', () => {
    renderWithProviders(<Sidebar open />, {
      store: createStoreWithModuleOverrides('expert', { harvest: 'disabled' }),
    });
    expect(screen.queryByTestId('nav-/ernte/batches')).toBeNull();
  });

  it('shows the global pest-detection entry for an expert by default', () => {
    renderWithProviders(<Sidebar open />, {
      store: createStoreWithExpertise('expert'),
    });
    expect(screen.getByTestId('nav-/pflanzenschutz/erkennung')).toBeInTheDocument();
  });

  it('hides the pest-detection entry when the AI module is disabled via override', () => {
    // The entry belongs to the AI module (more specific navPath than the ipm
    // module's /pflanzenschutz prefix), so disabling AI must hide it while the
    // sibling pest-list entry (ipm module) stays visible.
    renderWithProviders(<Sidebar open />, {
      store: createStoreWithModuleOverrides('expert', { ai: 'disabled' }),
    });
    expect(screen.queryByTestId('nav-/pflanzenschutz/erkennung')).toBeNull();
    expect(screen.getByTestId('nav-/pflanzenschutz/pests')).toBeInTheDocument();
  });
});

describe('Sidebar ↔ moduleCatalog sync (REQ-042 root-cause guard)', () => {
  it('owns every navigable sidebar entry with a catalog module', () => {
    // Render the whole sidebar with every non-core module enabled so no entry is
    // filtered out — then assert each rendered nav path resolves to a module.
    // This FAILS the moment a future sidebar entry is added without an owning
    // module (the exact regression #551 was about), closing the root cause.
    renderWithProviders(<Sidebar open />, {
      // smart home on so the automation entry (issue #587) is not filtered out.
      store: createStoreWithModuleOverrides('expert', ALL_MODULES_ENABLED, true),
    });

    const paths = renderedSidebarPaths();
    expect(paths.length).toBeGreaterThan(0);

    const ungoverned = paths.filter((path) => findModuleByPath(path) === undefined);
    expect(ungoverned).toEqual([]);
  });

  it('has no settings-only phantom module (every non-core module governs a real entry)', () => {
    // Reverse direction: every controllable module must own at least one entry
    // that actually appears in the sidebar — no toggle without a visible target.
    renderWithProviders(<Sidebar open />, {
      // smart home on so the automation entry (issue #587) is not filtered out.
      store: createStoreWithModuleOverrides('expert', ALL_MODULES_ENABLED, true),
    });

    const owningKeys = new Set(
      renderedSidebarPaths()
        .map((path) => findModuleByPath(path)?.key)
        .filter((key): key is ModuleKey => key !== undefined),
    );

    const phantomModules = Object.values(moduleCatalog)
      .filter((m) => !m.core)
      .map((m) => m.key)
      .filter((key) => !owningKeys.has(key));
    expect(phantomModules).toEqual([]);
  });
});

describe('Sidebar — newly-controllable modules (REQ-042 #551)', () => {
  const cases: Array<{ key: string; testid: string }> = [
    { key: 'ai_assistant', testid: 'nav-/ki-assistent' },
    { key: 'glossary', testid: 'nav-/glossar' },
    { key: 'inventory', testid: 'nav-/inventree' },
    { key: 'overwintering', testid: 'nav-/ueberwinterung/profile' },
    { key: 'phases', testid: 'nav-/phasen/definitionen' },
    { key: 'automation', testid: 'nav-/umgebungssteuerung' },
  ];

  it.each(cases)('shows $key by default and hides it when disabled', ({ key, testid }) => {
    const { unmount } = renderWithProviders(<Sidebar open />, {
      // smart home on so the automation entry (issue #587) is shown here.
      store: createStoreWithModuleOverrides('expert', ALL_MODULES_ENABLED, true),
    });
    expect(screen.getByTestId(testid)).toBeInTheDocument();
    unmount();

    renderWithProviders(<Sidebar open />, {
      store: createStoreWithModuleOverrides('expert', {
        ...ALL_MODULES_ENABLED,
        [key]: 'disabled',
      }, true),
    });
    expect(screen.queryByTestId(testid)).toBeNull();
  });

  it('hides the automation entry when smart home is disabled despite an override (#587)', () => {
    // Even with automation explicitly enabled, the smart-home gate keeps it hidden.
    renderWithProviders(<Sidebar open />, {
      store: createStoreWithModuleOverrides('expert', ALL_MODULES_ENABLED, false),
    });
    expect(screen.queryByTestId('nav-/umgebungssteuerung')).toBeNull();
  });

  it('hides the post-harvest entry independently of the harvest module', () => {
    // post_harvest owns /ernte/nachernte via the longest-path rule, so disabling
    // it must hide only nachernte while the harvest batches entry stays visible.
    renderWithProviders(<Sidebar open />, {
      store: createStoreWithModuleOverrides('expert', {
        ...ALL_MODULES_ENABLED,
        post_harvest: 'disabled',
      }),
    });
    expect(screen.queryByTestId('nav-/ernte/nachernte')).toBeNull();
    expect(screen.getByTestId('nav-/ernte/batches')).toBeInTheDocument();
  });
});
