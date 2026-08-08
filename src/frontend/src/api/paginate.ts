/**
 * Complete-catalogue loading for list endpoints (#995).
 *
 * **The defect this closes.** A list view that issues one bounded request and
 * renders the result as if it were the whole set loses every row past the page
 * size, silently. `DataTable` makes that worse rather than visible: its search,
 * sort and pagination all run **client-side**, over the rows already in the
 * store. So a user who types the name of a row that never arrived gets "no
 * results" — the UI actively denies the row exists. Nothing indicates a
 * truncated list. Three seeded fertilizers went missing this way and were
 * reported as a search defect (#956, #995).
 *
 * **Why the whole catalogue rather than pagination controls.** Server-side
 * paging would only be correct if search and sort moved to the server too —
 * otherwise the search box keeps lying, one page at a time. That is a backend
 * change plus a debounced round-trip per keystroke, replacing instant filtering,
 * for reference catalogues that hold tens to low hundreds of rows. Loading them
 * completely is one request at 31 rows and honest at any size: the cost grows
 * linearly and visibly (`ceil(n / CATALOGUE_PAGE_SIZE)` requests) instead of the
 * result being quietly wrong.
 *
 * The price, stated rather than hidden: at 5000 rows this is 25 sequential
 * requests, and at that point paging the *server* — with server-side search and
 * sort — becomes the right answer. `scripts/check_seed_catalogue_page_size.py`
 * prints the request count per catalogue on every run so the day that argument
 * flips is a number somebody reads, not a discovery.
 */

/**
 * Largest page the backend's shared pagination dependency accepts
 * (`app/common/pagination.py`: `limit: int = Query(50, ge=1, le=200)`).
 * A fixed `limit=500` was tried and 422'd (#614).
 */
export const MAX_PAGE_SIZE = 200;

/**
 * Page size used when loading a complete catalogue. The backend cap: fewer
 * round-trips is strictly better here, since every page is a sequential request.
 */
export const CATALOGUE_PAGE_SIZE = MAX_PAGE_SIZE;

/**
 * Upper bound on the paging loop. Purely a defence against an endpoint that
 * ignores `offset` and returns a full page forever — at `CATALOGUE_PAGE_SIZE`
 * it allows 200 000 rows, far past any catalogue this application holds, so it
 * cannot truncate a real result set.
 */
const MAX_PAGES = 1000;

/**
 * Loads every page of a list endpoint until a short page comes back.
 *
 * The termination rule is `batch.length < pageSize`, not a `total` from an
 * envelope: most list endpoints here return a plain array with no total, and a
 * short page is the one signal all of them share.
 *
 * @param loadPage Fetches one page. Receives `offset` and `limit`.
 * @param pageSize Rows per request; defaults to {@link CATALOGUE_PAGE_SIZE}.
 * @returns Every row, in the order the endpoint returned them.
 */
export async function fetchAllPages<T>(
  loadPage: (offset: number, limit: number) => Promise<T[]>,
  pageSize: number = CATALOGUE_PAGE_SIZE,
): Promise<T[]> {
  const all: T[] = [];
  let offset = 0;
  for (let page = 0; page < MAX_PAGES; page += 1) {
    const batch = await loadPage(offset, pageSize);
    all.push(...batch);
    if (batch.length < pageSize) break;
    offset += pageSize;
  }
  return all;
}
