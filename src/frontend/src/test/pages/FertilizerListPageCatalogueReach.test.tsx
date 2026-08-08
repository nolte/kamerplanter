/**
 * #995 acceptance: every product in the catalogue is reachable **through the
 * page's own search box**, not merely present in some API response.
 *
 * This drives the real `FertilizerListPage`, the real slice, the real endpoint
 * layer and the real `DataTable` search, against an MSW handler that paginates
 * the way the backend does — `SORT product_name`, then `offset`/`limit` applied
 * to the sorted set. That last detail is what made the defect what it was: the
 * lost rows were not random, they were the *last ones by name*, which is why
 * three specific products (`pH Perfect Sensi Grow A/B`, `pH Perfect Sensi
 * Bloom B`) were the ones reported missing in #956.
 *
 * Why a rendered page rather than an assertion on the API layer: the complaint
 * was never "the API returns too few rows", it was "I search for a product I own
 * and the application says it does not exist". Only the composed page can be
 * asked that question. `DataTable` searches client-side over the rows already in
 * the store, so a truncated fetch produces a *confident wrong answer* — the
 * empty-state, not an error — and an endpoint-level test cannot see it.
 *
 * The catalogue is built at 53 rows deliberately: that is the count #995 reports
 * for the seed files, and it is what the seeded catalogue becomes if
 * `fertilizers_supplement.yaml` is ever wired into the seed registry. Today only
 * 31 of those rows reach a database (see
 * `scripts/check_seed_catalogue_page_size.py`), which is under the old default
 * of 50 — so a test built from *today's* seed count would pass against the
 * defect. It is built from the size the catalogue is one decision away from.
 */
import { waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, beforeEach } from 'vitest';
import { http, HttpResponse } from 'msw';
import i18n from 'i18next';
import FertilizerListPage from '@/pages/duengung/FertilizerListPage';
import { renderWithProviders } from '../helpers';
import { server } from '../mocks/server';

/**
 * A catalogue of 53 products whose last three by name are the ones #956 reported
 * as missing. The filler sorts before them for the same reason the real
 * catalogue does: ArangoDB's default collation is by code point, so every
 * upper-case initial precedes the lower-case `p` of "pH Perfect".
 */
const MISSING_IN_956 = [
  'pH Perfect Sensi Bloom B',
  'pH Perfect Sensi Grow A',
  'pH Perfect Sensi Grow B',
];

const CATALOGUE = [
  ...Array.from({ length: 50 }, (_v, index) => `Base Nutrient ${String(index).padStart(2, '0')}`),
  ...MISSING_IN_956,
];

function makeFertilizer(productName: string, index: number) {
  return {
    key: `fert-${index}`,
    product_name: productName,
    brand: 'Advanced Nutrients',
    fertilizer_type: 'base',
    npk_ratio: [1, 2, 3],
    ec_contribution_per_ml: 0.5,
    tank_safe: true,
    is_organic: false,
    mixing_priority: 10,
  };
}

/**
 * Installs a handler that behaves like the backend list endpoint: it sorts by
 * `product_name` and then slices by `offset`/`limit`, so a caller that asks for
 * one page of 50 gets the first 50 *by name* and never learns the rest exist.
 *
 * @returns A recorder of the `(offset, limit)` pairs the page requested.
 */
function serveCatalogue(): { requests: { offset: number; limit: number }[] } {
  const sorted = [...CATALOGUE].sort().map(makeFertilizer);
  const requests: { offset: number; limit: number }[] = [];

  const handler = ({ request }: { request: Request }) => {
    const url = new URL(request.url);
    // The backend applies its own default of 50 when the caller sends none —
    // the behaviour that turned "no paging argument" into a silent truncation.
    const offset = Number(url.searchParams.get('offset') ?? '0');
    const limit = Number(url.searchParams.get('limit') ?? '50');
    requests.push({ offset, limit });
    return HttpResponse.json(sorted.slice(offset, offset + limit));
  };

  server.use(
    http.get('/api/v1/t/:tenant/fertilizers', handler),
    http.get('/api/v1/fertilizers', handler),
  );
  return { requests };
}

/**
 * Renders the page and returns queries scoped to *this* render's container.
 *
 * Scoped rather than the global `screen`: these cases each mount a 53-row page,
 * and a query against `document.body` sees whatever a previous case left behind
 * if its cleanup has not settled. That produced a failure whose message —
 * "unable to find pH Perfect Sensi Grow A" — was indistinguishable from the
 * defect under test, which is the worst possible way for a regression test to
 * be flaky: it fails with the symptom it exists to detect.
 */
function renderPage() {
  const { container } = renderWithProviders(<FertilizerListPage />);
  return within(container);
}

type ScopedQueries = ReturnType<typeof renderPage>;

/**
 * Enters a query into the page's own search field.
 *
 * Pasted rather than typed: `user.type()` emits one change event per character,
 * and each one re-renders a 53-row table, so a 24-character product name costs
 * 24 full renders. That is fast enough on a bare run and blew the timeout under
 * `--coverage`, whose instrumentation roughly doubles wall-clock (see the note
 * in `vitest.config.ts`) — a test that only passes without coverage is a test
 * that fails in the coverage job. A paste exercises the same `onChange` →
 * debounce → `tableState.setSearch` path in a single event.
 *
 * The input is debounced by 300 ms, so every assertion that follows must sit
 * inside a `waitFor` with room for it; a bare assertion would read the
 * pre-debounce table and pass for the wrong reason.
 */
async function search(
  page: ScopedQueries,
  user: ReturnType<typeof userEvent.setup>,
  query: string,
): Promise<void> {
  const field = await page.findByTestId('table-search-input');
  const input = within(field).getByRole('textbox');
  await user.click(input);
  await user.paste(query);
}

describe('FertilizerListPage — the whole catalogue is reachable by search (#995)', () => {
  beforeEach(() => {
    i18n.changeLanguage('de');
  });

  it('loads every product, not just the first page', async () => {
    const { requests } = serveCatalogue();
    const page = renderPage();

    await waitFor(() => {
      expect(page.getByText('Base Nutrient 00')).toBeTruthy();
    });

    // The load must not have stopped at a page boundary. Asking for a page of 50
    // and rendering the answer is precisely the defect; the page asks for the
    // backend's maximum and keeps going until a short page comes back.
    expect(requests.length).toBeGreaterThan(0);
    expect(requests.every((request) => request.limit === 200)).toBe(true);
  });

  it.each(MISSING_IN_956)(
    'finds %s through the search box — the products reported missing in #956',
    async (productName) => {
      serveCatalogue();
      const user = userEvent.setup({ delay: null });
      const page = renderPage();

      await waitFor(() => {
        expect(page.getByText('Base Nutrient 00')).toBeTruthy();
      });

      await search(page, user, productName);

      // The assertion that carries the issue: before the fix this row was absent
      // from the store, so the client-side search rendered the "no results"
      // empty state — the UI answering that a shipped product does not exist.
      await waitFor(
        () => {
          expect(page.getByText(productName)).toBeTruthy();
        },
        { timeout: 5000 },
      );
      expect(page.queryByTestId('no-search-results')).toBeNull();
    },
    20000,
  );

  it('still reports no results for a product that really is not there', async () => {
    // The counterpart the positive cases need: a search that matched everything
    // would satisfy the cases above without the catalogue being loaded at all.
    serveCatalogue();
    const user = userEvent.setup({ delay: null });
    const page = renderPage();

    await waitFor(() => {
      expect(page.getByText('Base Nutrient 00')).toBeTruthy();
    });

    await search(page, user, 'Definitely Not A Seeded Product');

    await waitFor(
      () => {
        expect(page.getByTestId('no-search-results')).toBeTruthy();
      },
      { timeout: 5000 },
    );
  }, 20000);
});
