/**
 * Link semantics for DataTable rows and cards that lead to a detail page (#3017, W-01/N-18).
 *
 * A row that navigated through `onRowClick={() => navigate(...)}` was a focusable `<tr>` / `<div>` with no
 * role and no `href`: a screen reader announced nothing actionable, and Ctrl-, Cmd-, Shift- and middle-click
 * did nothing because there was no URL to open. Everything that needs the router lives here, so a DataTable
 * without `getRowHref` keeps working outside a `<Router>` (its own unit tests render it bare).
 *
 * - Desktop: the row keeps its native `row` role (a table row must stay a row), and the first visible cell
 *   carries a real `<a href>` — the row's single tab stop, named by that cell's text, with the browser's own
 *   "open in new tab" behaviour. A click anywhere else on the row follows the same URL, and a modified or
 *   middle click there opens it in a new tab.
 * - Mobile card: the card is the link (`role="link"`, Enter follows it, a modified click opens a new tab).
 */
import type { KeyboardEvent, MouseEvent, ReactNode } from 'react';
import { Link as RouterLink, useHref, useNavigate } from 'react-router-dom';
import Box from '@mui/material/Box';
import Link from '@mui/material/Link';
import TableRow from '@mui/material/TableRow';

const focusRing = {
  outline: '2px solid',
  outlineColor: 'primary.main',
  outlineOffset: -2,
} as const;

/** A click the browser would turn into "open in a new tab / window" on a real link. */
function wantsNewTab(e: MouseEvent<HTMLElement>): boolean {
  return e.ctrlKey || e.metaKey || e.shiftKey || e.button === 1;
}

/** Anything inside a row or card that handles its own activation (links, buttons, form fields). */
const INTERACTIVE_DESCENDANT =
  'a[href],button,input,select,textarea,[role="button"],[role="link"],[data-row-link="true"]';

/**
 * True when the event started on an interactive element nested inside the row or card — the row's own
 * cell link, a chip link to another page, an action button. That element owns the click, middle click
 * and key press; the row must neither navigate nor open its own URL in a new tab on top of it.
 * The row or card element itself (a card carries `role="link"`) does not count.
 */
function startedOnNestedControl(e: MouseEvent<HTMLElement>): boolean {
  const target = e.target as HTMLElement | null;
  const interactive = target?.closest(INTERACTIVE_DESCENDANT);
  return Boolean(interactive && interactive !== e.currentTarget && e.currentTarget.contains(interactive));
}

function useRowFollow(href: string) {
  const navigate = useNavigate();
  // The URL as the browser sees it (basename applied), for `window.open`.
  const absoluteHref = useHref(href);
  const follow = (e: MouseEvent<HTMLElement>) => {
    if (startedOnNestedControl(e)) return;
    if (wantsNewTab(e)) {
      e.preventDefault();
      window.open(absoluteHref, '_blank', 'noopener');
      return;
    }
    if (e.button !== 0) return;
    navigate(href);
  };
  return { follow, navigate, absoluteHref };
}

interface RowCellLinkProps {
  href: string;
  children: ReactNode;
}

/** The real anchor inside the row's first visible cell. */
export function RowCellLink({ href, children }: RowCellLinkProps) {
  return (
    <Link
      component={RouterLink}
      to={href}
      data-row-link="true"
      data-testid="data-table-row-link"
      color="inherit"
      underline="hover"
      // The row's own click handler would navigate a second time.
      onClick={(e: MouseEvent<HTMLAnchorElement>) => e.stopPropagation()}
      sx={{ display: 'inline-block', '&:focus-visible': focusRing }}
    >
      {children}
    </Link>
  );
}

interface LinkedTableRowProps {
  href: string;
  rowKey: string;
  children: ReactNode;
}

/** A desktop row whose whole surface follows `href`; keyboard users reach it through {@link RowCellLink}. */
export function LinkedTableRow({ href, rowKey, children }: LinkedTableRowProps) {
  const { follow } = useRowFollow(href);
  return (
    <TableRow
      hover
      onClick={follow}
      onAuxClick={follow}
      sx={{ cursor: 'pointer' }}
      data-testid="data-table-row"
      data-row-key={rowKey}
    >
      {children}
    </TableRow>
  );
}

interface LinkedCardProps {
  href: string;
  rowKey: string;
  children: ReactNode;
}

/** A mobile card that is itself the link to `href`. */
export function LinkedCard({ href, rowKey, children }: LinkedCardProps) {
  const { follow, navigate, absoluteHref } = useRowFollow(href);
  const onKeyDown = (e: KeyboardEvent<HTMLElement>) => {
    // A link activates on Enter only (Space scrolls); keys on nested controls are theirs.
    // `target !== currentTarget` already leaves every key on a nested control (see startedOnNestedControl) to it.
    if (e.target !== e.currentTarget || e.repeat || e.key !== 'Enter') return;
    e.preventDefault();
    if (e.ctrlKey || e.metaKey || e.shiftKey) {
      window.open(absoluteHref, '_blank', 'noopener');
      return;
    }
    navigate(href);
  };
  return (
    <Box
      role="link"
      tabIndex={0}
      onClick={follow}
      onAuxClick={follow}
      onKeyDown={onKeyDown}
      sx={{ cursor: 'pointer', '&:focus-visible': focusRing }}
      data-testid="data-table-row"
      data-row-key={rowKey}
    >
      {children}
    </Box>
  );
}
