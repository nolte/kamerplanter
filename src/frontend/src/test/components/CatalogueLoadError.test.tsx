/**
 * The ready-made failure element for `useCatalogue` (#1628).
 *
 * The call-site suites assert that each picker renders this element on a failed
 * load. What only this file asks is the element's own contract: it is silent in
 * every state but `failed`, it names the catalogue that failed rather than
 * saying "no entries", it is announced (`role="alert"`) and has a real,
 * keyboard-reachable retry with a touch-sized hit area, and the retry reaches
 * the network through the real hook rather than through a stub.
 */
import type { ReactNode } from 'react';
import { cleanup, render, renderHook, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { Provider } from 'react-redux';
import { combineReducers, configureStore } from '@reduxjs/toolkit';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { http, HttpResponse } from 'msw';
import i18n from 'i18next';
import { ThemeContextProvider } from '@/theme';
import CatalogueLoadError from '@/components/common/CatalogueLoadError';
import { CATALOGUE_NAMES, useCatalogue, type CatalogueStatus } from '@/hooks/useCatalogue';
import botanicalFamiliesReducer from '@/store/slices/botanicalFamiliesSlice';
import { deFull, enFull } from '../i18nTestResources';
import { server } from '../mocks/server';
import { WAIT_BUDGET } from '../waitBudget';

const FAMILIES_URL = '/api/v1/botanical-families';

function renderElement(ui: ReactNode) {
  return render(<ThemeContextProvider>{ui}</ThemeContextProvider>);
}

function staticReader(status: CatalogueStatus, reload = vi.fn()) {
  return { name: 'species' as const, status, reload };
}

describe('CatalogueLoadError', () => {
  beforeEach(() => {
    i18n.changeLanguage('de');
  });

  afterEach(() => {
    cleanup();
    i18n.changeLanguage('en');
  });

  it.each<CatalogueStatus>(['loading', 'ready'])('renders nothing while %s', (status) => {
    renderElement(<CatalogueLoadError reader={staticReader(status)} />);
    expect(screen.queryByTestId('catalogue-load-error-species')).toBeNull();
    expect(screen.queryByRole('alert')).toBeNull();
  });

  it('names the failed catalogue in an announced alert, not as an empty list', () => {
    renderElement(<CatalogueLoadError reader={staticReader('failed')} />);

    const alert = screen.getByRole('alert');
    expect(alert.textContent).toContain(
      i18n.t('common.catalogue.loadFailedTitle', {
        catalogue: i18n.t('common.catalogue.names.species'),
      }),
    );
    expect(alert.textContent).toContain(i18n.t('common.catalogue.loadFailedPicker'));
  });

  it('uses the lookup wording when the catalogue only resolves names', () => {
    renderElement(<CatalogueLoadError reader={staticReader('failed')} impact="lookup" />);
    const alert = screen.getByRole('alert');
    expect(alert.textContent).toContain(i18n.t('common.catalogue.loadFailedLookup'));
    expect(alert.textContent).not.toContain(i18n.t('common.catalogue.loadFailedPicker'));
  });

  it('retries from the keyboard, with a 48 px hit area', async () => {
    const reload = vi.fn();
    const onRetry = vi.fn();
    const user = userEvent.setup();
    renderElement(<CatalogueLoadError reader={staticReader('failed', reload)} onRetry={onRetry} />);

    const retry = screen.getByTestId('catalogue-load-error-species-retry');
    expect(retry.tagName).toBe('BUTTON');
    expect(retry.textContent).toBe(i18n.t('common.retry'));
    // UI-NFR-001 R-011; jsdom has no layout, so the rule is read off the style.
    const style = getComputedStyle(retry);
    expect(style.minHeight).toBe('48px');
    expect(style.minWidth).toBe('48px');

    await user.tab();
    expect(document.activeElement).toBe(retry);
    await user.keyboard('{Enter}');
    expect(onRetry).toHaveBeenCalledOnce();
    expect(reload).toHaveBeenCalledOnce();
  });

  it('has a DE and EN label for every catalogue the hook can read', () => {
    const pick = (full: Record<string, unknown>) =>
      (full.common as { catalogue: { names: Record<string, string> } }).catalogue.names;
    for (const name of CATALOGUE_NAMES) {
      expect(pick(deFull)[name], `de ${name}`).toBeTruthy();
      expect(pick(enFull)[name], `en ${name}`).toBeTruthy();
    }
    const keysOf = (full: Record<string, unknown>) =>
      Object.keys((full.common as { catalogue: Record<string, unknown> }).catalogue).sort();
    expect(keysOf(deFull)).toEqual(keysOf(enFull));
  });
});

describe('CatalogueLoadError with the real useCatalogue', () => {
  beforeEach(() => {
    i18n.changeLanguage('de');
  });

  afterEach(() => {
    cleanup();
    i18n.changeLanguage('en');
  });

  function Harness() {
    const families = useCatalogue('botanicalFamilies');
    return (
      <>
        <span data-testid="status">{families.status}</span>
        <CatalogueLoadError reader={families} />
      </>
    );
  }

  function renderHarness() {
    const store = configureStore({
      reducer: combineReducers({ botanicalFamilies: botanicalFamiliesReducer }),
    });
    return render(
      <Provider store={store}>
        <ThemeContextProvider>
          <Harness />
        </ThemeContextProvider>
      </Provider>,
    );
  }

  it('exposes the catalogue name on the reader', () => {
    const store = configureStore({
      reducer: combineReducers({ botanicalFamilies: botanicalFamiliesReducer }),
    });
    const { result } = renderHook(() => useCatalogue('botanicalFamilies', { enabled: false }), {
      wrapper: ({ children }: { children: ReactNode }) => (
        <Provider store={store}>{children}</Provider>
      ),
    });
    expect(result.current.name).toBe('botanicalFamilies');
  });

  it('shows on a failed load and disappears after a successful retry', async () => {
    let attempts = 0;
    server.use(
      http.get(FAMILIES_URL, () => {
        attempts += 1;
        if (attempts === 1) return new HttpResponse(null, { status: 500 });
        return HttpResponse.json([]);
      }),
    );
    const user = userEvent.setup();
    renderHarness();

    const retry = await screen.findByTestId(
      'catalogue-load-error-botanicalFamilies-retry',
      {},
      { timeout: WAIT_BUDGET },
    );
    await user.click(retry);

    await waitFor(
      () => {
        expect(screen.getByTestId('status').textContent).toBe('ready');
      },
      { timeout: WAIT_BUDGET },
    );
    expect(screen.queryByTestId('catalogue-load-error-botanicalFamilies')).toBeNull();
    expect(attempts).toBeGreaterThan(1);
  });
});
