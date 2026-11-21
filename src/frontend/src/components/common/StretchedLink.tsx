/**
 * A card title that links the whole card while the card keeps its own buttons (#3047).
 *
 * A card that holds other controls (duplicate, delete, a chip link) cannot be wrapped in an `<a>` or a
 * `CardActionArea`: interactive content inside a link or button is invalid, and a screen reader then
 * announces neither correctly. The usual answer is a *stretched link*: the title is the one real
 * `<a href>` (named by the title, opens in a new tab), and its `::after` covers the card so a click
 * anywhere on the card follows it. Controls that must stay clickable sit above that layer with
 * {@link aboveStretchedLink}.
 *
 * The card must be the containing block: give it `position: 'relative'` (see {@link stretchedLinkHost}).
 */
import type { ReactNode } from 'react';
import { Link as RouterLink } from 'react-router-dom';
import Link from '@mui/material/Link';

/** `sx` for the card that hosts a {@link StretchedLink}. */
export const stretchedLinkHost = { position: 'relative' } as const;

/** `sx` for a control inside the card that must stay clickable above the stretched link. */
export const aboveStretchedLink = { position: 'relative', zIndex: 1 } as const;

interface StretchedLinkProps {
  to: string;
  children: ReactNode;
  'data-testid'?: string;
}

export default function StretchedLink({ to, children, 'data-testid': testId }: StretchedLinkProps) {
  return (
    <Link
      component={RouterLink}
      to={to}
      color="inherit"
      underline="hover"
      data-testid={testId}
      sx={{
        '&::after': {
          content: '""',
          position: 'absolute',
          inset: 0,
        },
        // The focus ring belongs to the whole card the link stands for.
        '&:focus-visible': { outline: 'none' },
        '&:focus-visible::after': {
          outline: '2px solid',
          outlineColor: 'primary.main',
          outlineOffset: -2,
        },
      }}
    >
      {children}
    </Link>
  );
}
