import { describe, it, expect } from 'vitest';
import { screen } from '@testing-library/react';
import type { ModuleVisibilityState } from '@/api/types';

import Sidebar from '@/layouts/Sidebar';
import { findModuleByPath, moduleCatalog, type ModuleKey } from '@/config/moduleCatalog';
import { fetchAiStatus } from '@/store/slices/aiStatusSlice';
import {
  createStoreWithExpertise,
  createStoreWithModuleOverrides,
  renderWithProviders,
  type TestStore,
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

describe('Sidebar — KI-Assistent gated on the AI feature flag (issue #685)', () => {
  /** Store with every module enabled plus a resolved AI availability status. */
  function storeWithAiStatus(available: boolean | null): TestStore {
    const store = createStoreWithModuleOverrides('expert', ALL_MODULES_ENABLED, true);
    if (available !== null) {
      store.dispatch(fetchAiStatus.fulfilled({ available }, 'req', undefined));
    }
    return store;
  }

  it('shows the KI-Assistent entry when AI features are available', () => {
    renderWithProviders(<Sidebar open />, { store: storeWithAiStatus(true) });
    expect(screen.getByTestId('nav-/ki-assistent')).toBeInTheDocument();
    // Glossar is decoupled from the AI flag (issue #684) and stays visible.
    expect(screen.getByTestId('nav-/glossar')).toBeInTheDocument();
  });

  it('hides the KI-Assistent entry when AI features are disabled', () => {
    renderWithProviders(<Sidebar open />, { store: storeWithAiStatus(false) });
    expect(screen.queryByTestId('nav-/ki-assistent')).toBeNull();
    // Glossar must remain visible even when the AI flag is off (issue #684).
    expect(screen.getByTestId('nav-/glossar')).toBeInTheDocument();
  });

  it('keeps the KI-Assistent entry visible while the AI probe is pending', () => {
    // available === null (unknown) must not hide a potentially-working feature.
    renderWithProviders(<Sidebar open />, { store: storeWithAiStatus(null) });
    expect(screen.getByTestId('nav-/ki-assistent')).toBeInTheDocument();
    expect(screen.getByTestId('nav-/glossar')).toBeInTheDocument();
  });

  it('keeps the KI-Assistent entry visible after a failed AI probe (fail-open)', () => {
    // A rejected probe (network/timeout/5xx) leaves availability unknown (null),
    // so the nav entry must stay visible — a transient fault must never hide a
    // working feature. Only a definitive available=false gates the entry.
    const store = createStoreWithModuleOverrides('expert', ALL_MODULES_ENABLED, true);
    store.dispatch(fetchAiStatus.rejected(new Error('network'), 'req', undefined));
    expect(store.getState().aiStatus.available).toBeNull();

    renderWithProviders(<Sidebar open />, { store });
    expect(screen.getByTestId('nav-/ki-assistent')).toBeInTheDocument();
    expect(screen.getByTestId('nav-/glossar')).toBeInTheDocument();
  });
});

/**
 * Issue #1291. axe reported `list` and `listitem` (serious) on every page that
 * renders the drawer: the nav <ul> held bare <a> and <div> children, and each
 * section's ListSubheader — an <li> — sat inside a <div>, so it had no list
 * parent at all. Both halves are asserted here, in the same terms the two axe
 * rules use, so a refactor that reintroduces either fails in the unit suite
 * rather than four hours later in the nightly.
 */
describe('Sidebar — the navigation is a valid list (#1291)', () => {
  function renderFullSidebar(route = '/'): void {
    renderWithProviders(<Sidebar open />, {
      store: createStoreWithModuleOverrides('expert', ALL_MODULES_ENABLED, true),
      route,
    });
  }

  /** Guards the guard: an empty query would satisfy every `every()` below. */
  function sidebarLists(): HTMLUListElement[] {
    const lists = Array.from(document.querySelectorAll('ul'));
    expect(lists.length).toBeGreaterThan(1);
    return lists as HTMLUListElement[];
  }

  it('lets a <ul> contain only <li> children (axe rule: list)', () => {
    renderFullSidebar();
    const offenders = sidebarLists().flatMap((ul) =>
      Array.from(ul.children)
        .filter((child) => !['LI', 'SCRIPT', 'TEMPLATE'].includes(child.tagName))
        .map((child) => `${child.tagName.toLowerCase()} in ul.${ul.className.split(' ')[0]}`),
    );
    expect(offenders).toEqual([]);
  });

  it('gives every <li> a list parent (axe rule: listitem)', () => {
    renderFullSidebar();
    const items = Array.from(document.querySelectorAll('li'));
    expect(items.length).toBeGreaterThan(0);
    const orphans = items
      .filter((li) => !['UL', 'OL'].includes(li.parentElement?.tagName ?? ''))
      .map((li) => `${li.textContent} in ${li.parentElement?.tagName.toLowerCase()}`);
    expect(orphans).toEqual([]);
  });

  it('associates each section heading with the sub-list it heads', () => {
    renderFullSidebar();
    const headings = Array.from(document.querySelectorAll('.MuiListSubheader-root'));
    expect(headings.length).toBeGreaterThan(0);
    for (const heading of headings) {
      const id = heading.getAttribute('id');
      expect(id, `section heading "${heading.textContent}" has no id to be referenced by`).toBeTruthy();
      // The heading lives inside the very list it names, and that list points
      // back at it — an unattached label is what the old markup produced.
      const list = heading.closest('ul');
      expect(list?.getAttribute('aria-labelledby')).toBe(id);
    }
  });

  it('keeps aria-current and the selected highlight on the active entry', () => {
    // A section entry, not a top-level one: sections are what the nesting
    // changed, so marking the current page there is the property at risk.
    renderFullSidebar('/stammdaten/species');
    const current = Array.from(
      document.querySelectorAll('[data-testid^="nav-"][aria-current="page"]'),
    );
    expect(current.map((el) => el.getAttribute('data-testid'))).toEqual([
      'nav-/stammdaten/species',
    ]);
    // Still on the anchor itself rather than on the new <li> wrapper, and still
    // carrying MUI's selected state that draws the highlight.
    expect(current[0].tagName).toBe('A');
    expect(current[0].classList.contains('Mui-selected')).toBe(true);
  });
});
