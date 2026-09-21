/**
 * #1568 acceptance: the "Familie" dropdown reports a failed family load instead
 * of swallowing it.
 *
 * **The defect.** The dialog loaded its catalogue with
 * `listAllBotanicalFamilies().then(setFamilies).catch(() => {})`. On a failure
 * the field rendered its placeholder and nothing else — no message, no spinner,
 * no retry — so the user's only reading was "this species has no family to
 * choose", and the species was created without one.
 *
 * "Field", not "mandatory field": `family_key` is `z.string().nullable()` with a
 * `null` default, and submit is not coupled to the catalogue's status. An earlier
 * version of this header said "mandatory" and contradicted both the schema and
 * the component's own comment — the cheapest kind of wrong note to leave lying
 * around, and the class this repository pays for most (#1393). There was no
 * in-flight state and no ignore guard either, so closing and reopening the
 * dialog started a second sequence whose late answer could land on top of the
 * live one.
 *
 * **What makes this a falsification and not a neighbouring claim.** The rule is
 * "a failed catalogue load is visible and retryable at this field". The
 * assertions below read that field's own region, which against the old code was
 * an enabled select with one placeholder option and no sibling — the exact state
 * the repair changes.
 */
import { cleanup, render, screen, waitFor, within } from '@testing-library/react';
import { createMemoryRouter, RouterProvider } from 'react-router-dom';
import { Provider } from 'react-redux';
import { SnackbarProvider } from 'notistack';
import { ThemeContextProvider } from '@/theme';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import { http, HttpResponse } from 'msw';
import i18n from 'i18next';
import SpeciesCreateDialog from '@/pages/stammdaten/SpeciesCreateDialog';
import { renderWithProviders, createStoreWithExpertise } from '../helpers';
import { server } from '../mocks/server';
import { WAIT_BUDGET } from '../waitBudget';

const FAMILIES_URL = '/api/v1/botanical-families';

function makeFamily(index: number) {
  return {
    key: `fam-${index}`,
    name: `Familie ${String(index).padStart(2, '0')}`,
    typical_nutrient_demand: 'medium',
    common_pests: [],
    rotation_category: 'fruit',
    created_at: '2024-01-01T00:00:00Z',
    updated_at: null,
  };
}

function renderDialog() {
  return renderWithProviders(
    <SpeciesCreateDialog open onClose={() => {}} onCreated={() => {}} />,
    { store: createStoreWithExpertise('expert') },
  );
}

describe('SpeciesCreateDialog — the family catalogue has three states (#1568)', () => {
  beforeEach(() => {
    i18n.changeLanguage('de');
  });

  afterEach(() => {
    cleanup();
    i18n.changeLanguage('en');
  });

  it('shows a retryable failure at the family field instead of an empty dropdown', async () => {
    server.use(http.get(FAMILIES_URL, () => new HttpResponse(null, { status: 500 })));
    renderDialog();

    await waitFor(
      () => {
        expect(screen.getByTestId('family-catalogue-error')).toBeTruthy();
      },
      { timeout: WAIT_BUDGET },
    );
    expect(screen.getByTestId('error-retry-button')).toBeTruthy();

    // Against the old code the field was enabled and silently offered only the
    // "—" placeholder, which reads as a deliberate "no family". It must not.
    expect(screen.queryByTestId('family-catalogue-empty')).toBeNull();
  });

  it('recovers through the retry control', async () => {
    let attempts = 0;
    server.use(
      http.get(FAMILIES_URL, () => {
        attempts += 1;
        if (attempts === 1) return new HttpResponse(null, { status: 500 });
        return HttpResponse.json([makeFamily(0)]);
      }),
    );
    const user = userEvent.setup();
    renderDialog();

    await waitFor(
      () => {
        expect(screen.getByTestId('error-retry-button')).toBeTruthy();
      },
      { timeout: WAIT_BUDGET },
    );
    await user.click(screen.getByTestId('error-retry-button'));

    await waitFor(
      () => {
        expect(screen.queryByTestId('family-catalogue-error')).toBeNull();
      },
      { timeout: WAIT_BUDGET },
    );

    // The recovered catalogue, read the way a user reaches it: MUI renders the
    // options into a popover only once the select is open, so asserting the
    // option without opening would assert nothing.
    const combobox = within(screen.getByTestId('form-field-family_key')).getByRole('combobox');
    await user.click(combobox);
    const listbox = await screen.findByRole('listbox');
    expect(within(listbox).getByText(makeFamily(0).name)).toBeTruthy();
    // Pins the recovery to a second request rather than to a re-render.
    expect(attempts).toBeGreaterThan(1);
  });

  it('says the catalogue is empty only when it arrived empty', async () => {
    server.use(http.get(FAMILIES_URL, () => HttpResponse.json([])));
    renderDialog();

    await waitFor(
      () => {
        expect(screen.getByTestId('family-catalogue-empty')).toBeTruthy();
      },
      { timeout: WAIT_BUDGET },
    );
    expect(screen.queryByTestId('family-catalogue-error')).toBeNull();
    expect(
      screen.getByText(i18n.t('pages.species.familyCatalogueEmpty')),
    ).toBeTruthy();
  });
});

/**
 * The accessibility half of the three states (#1568 UI review, B1 + B2).
 *
 * **What these add over the cases above.** Those assert which *element* is on
 * screen. None of them asked how the change reaches a user who cannot see it, and
 * a grep for `aria-live` / `role="status"` / focus over both new test files
 * returned nothing. Of the three transitions exactly one announced itself for
 * free — `→ failed`, through the native `role="alert"` in MUI's `Alert`. The
 * other two were silent, and the retry additionally dropped focus to `<body>`.
 *
 * **Which code makes each of these red** — recorded because a case that passes
 * against the unrepaired version certifies nothing, which already happened once
 * in this pull request:
 *
 * | case | red against |
 * |---|---|
 * | announces while loading | removing `<LoadingStatus>` |
 * | visible indicator | removing `<LinearProgress>` |
 * | focus after a successful retry | removing `useRetryFocus` |
 * | focus after a second failure | removing `useRetryFocus` |
 */
describe('SpeciesCreateDialog — the family catalogue is perceivable (#1568 UI review)', () => {
  beforeEach(() => {
    i18n.changeLanguage('de');
  });

  afterEach(() => {
    cleanup();
    i18n.changeLanguage('en');
  });

  it('announces the load in a live region and shows a visible indicator', async () => {
    // Gated so the loading state is still on screen when this asserts. Without
    // the gate the catalogue arrives inside the first flush and the window the
    // case is about never exists — the failure mode of the SCR-002 case.
    //
    // Released in `finally`, which is not defensive noise: a failing assertion
    // here used to leave the request hanging, and a request that never settles
    // keeps its entry in `useCatalogue`'s module-level in-flight map forever, so
    // every later case in this file joined a dead promise and failed too.
    // Measured while falsifying this case — three red where one was expected.
    let release!: () => void;
    const arrives = new Promise<void>((resolve) => {
      release = resolve;
    });
    server.use(
      http.get(FAMILIES_URL, async () => {
        await arrives;
        return HttpResponse.json([makeFamily(0)]);
      }),
    );
    renderDialog();

    try {
      await assertLoadingIsPerceivable();
    } finally {
      release();
    }

    await waitFor(
      () => {
        expect(screen.getByTestId('family-catalogue-loading-status').textContent).toBe('');
      },
      { timeout: WAIT_BUDGET },
    );
    // Emptied *and* unnamed, so a user landing on it later is not told about a
    // load that is over (`LoadingStatus` property 4).
    expect(
      screen.getByTestId('family-catalogue-loading-status').getAttribute('aria-label'),
    ).toBeNull();
    expect(screen.queryByTestId('family-catalogue-loading')).toBeNull();
  });

  /** The assertions the gate exists for, so the gate can be released around them. */
  async function assertLoadingIsPerceivable(): Promise<void> {
    const status = await screen.findByTestId('family-catalogue-loading-status');
    // R-011 / WCAG 4.1.3: a region, polite, and carrying text — a named region
    // with no content announces nothing (`LoadingStatus` property 2).
    expect(status.getAttribute('role')).toBe('status');
    expect(status.getAttribute('aria-live')).toBe('polite');
    expect(status.textContent).toBe(i18n.t('pages.species.familyLoading'));

    // R-020 asks for a spinner, progress bar or skeleton; a helper text is none
    // of the three, and a greyed-out field reads as broken rather than busy.
    expect(screen.getByTestId('family-catalogue-loading')).toBeTruthy();
  }

  it('puts focus on the family field after a retry succeeds', async () => {
    let attempts = 0;
    server.use(
      http.get(FAMILIES_URL, () => {
        attempts += 1;
        if (attempts === 1) return new HttpResponse(null, { status: 500 });
        return HttpResponse.json([makeFamily(0)]);
      }),
    );
    const user = userEvent.setup();
    renderDialog();

    const retry = await screen.findByTestId('error-retry-button');
    await user.click(retry);

    await waitFor(
      () => {
        expect(screen.queryByTestId('family-catalogue-error')).toBeNull();
      },
      { timeout: WAIT_BUDGET },
    );

    // The assertion that carries B2. Against the unrepaired version the whole
    // `failed` branch unmounted under the focused button and the browser fell
    // back to `<body>`, so the user lost their place in the dialog entirely.
    const combobox = within(screen.getByTestId('form-field-family_key')).getByRole('combobox');
    await waitFor(
      () => {
        expect(document.activeElement).toBe(combobox);
      },
      { timeout: WAIT_BUDGET },
    );
    expect(document.activeElement).not.toBe(document.body);
  });

  it('puts focus back on the retry control when the retry fails again', async () => {
    server.use(http.get(FAMILIES_URL, () => new HttpResponse(null, { status: 500 })));
    const user = userEvent.setup();
    renderDialog();

    await user.click(await screen.findByTestId('error-retry-button'));

    // A *new* button is rendered for the second failure, which is why the hook
    // resolves the target at settle time instead of holding a ref to the old one.
    await waitFor(
      () => {
        expect(document.activeElement).toBe(screen.getByTestId('error-retry-button'));
      },
      { timeout: WAIT_BUDGET },
    );
  });
});

/**
 * The empty state carries a way out, and the way out is guarded (#1568 UI
 * review, B3).
 *
 * **The decision this encodes.** R-012 asks an empty state to explain itself and
 * R-014 to offer an action; the dialog had only the explanation. The operator
 * chose a call to action that **navigates**, over the reviewer's advice — the
 * reviewer's objection was that navigating pulls the user out of the task they
 * are in the middle of, which for a create dialog means losing what they typed.
 *
 * So the objection is what these cases are about. The CTA is only acceptable
 * while the warning behind it actually fires, and only fires when there is
 * something to lose: a loss warning over an untouched form is noise, and a
 * warning users have learned to click through is absent exactly when it matters.
 * Hence one case per side — dirty and not dirty.
 *
 * The mechanism is the project's existing `UnsavedChangesGuard` (30+ call sites),
 * not a second one beside it, so what is tested here is the *wiring*: the guard's
 * own behaviour has its own file.
 */
describe('SpeciesCreateDialog — the empty family catalogue offers a guarded way out', () => {
  beforeEach(() => {
    i18n.changeLanguage('de');
    server.use(http.get(FAMILIES_URL, () => HttpResponse.json([])));
  });

  afterEach(() => {
    cleanup();
    i18n.changeLanguage('en');
  });

  /** The dialog on a real two-route data router, so `useBlocker` is live. */
  function renderRouted() {
    const router = createMemoryRouter(
      [
        {
          path: '/',
          element: <SpeciesCreateDialog open onClose={() => {}} onCreated={() => {}} />,
        },
        { path: '/stammdaten/botanical-families', element: <div>family list</div> },
      ],
      { initialEntries: ['/'] },
    );
    return render(
      <Provider store={createStoreWithExpertise('expert')}>
        <ThemeContextProvider>
          <SnackbarProvider>
            <RouterProvider router={router} />
          </SnackbarProvider>
        </ThemeContextProvider>
      </Provider>,
    );
  }

  it('offers the call to action and takes an untouched form straight there', async () => {
    const user = userEvent.setup();
    renderRouted();

    const cta = await screen.findByTestId('family-catalogue-empty-cta');
    // R-014: the label names the destination rather than saying "OK".
    expect(cta.textContent).toBe(i18n.t('pages.species.familyCatalogueEmptyCta'));

    await user.click(cta);

    // Nothing typed, nothing to lose: no warning, because a warning here is the
    // noise that trains users to ignore the one that matters.
    expect(screen.queryByTestId('confirm-dialog')).toBeNull();
    expect(await screen.findByText('family list')).toBeTruthy();
  });

  it('warns before leaving once the form actually holds input, and staying is the default', async () => {
    const user = userEvent.setup();
    renderRouted();

    const name = within(await screen.findByTestId('form-field-scientific_name')).getByRole(
      'textbox',
    );
    await user.type(name, 'Ocimum basilicum');

    await user.click(screen.getByTestId('family-catalogue-empty-cta'));

    // The assertion that makes the operator's choice defensible: the navigation
    // is blocked, not merely annotated.
    await screen.findByTestId('confirm-dialog');
    // The role sits on MUI's paper, not on the testid'd root (which is
    // `presentation`) — asserted through the role query so this cannot pass on
    // a dialog that merely exists.
    expect(screen.getByRole('alertdialog')).toBeTruthy();
    expect(screen.queryByText('family list')).toBeNull();

    // "Stay" is the lighter path: `ConfirmDialog` autofocuses cancel, so Enter
    // or Escape keeps the user — leaving takes a deliberate second act.
    expect(document.activeElement).toBe(screen.getByTestId('confirm-dialog-cancel'));

    await user.click(screen.getByTestId('confirm-dialog-cancel'));
    expect(screen.queryByText('family list')).toBeNull();
    // …and the typed value survived, which is the whole point of blocking.
    expect((name as HTMLInputElement).value).toBe('Ocimum basilicum');
  });
});
