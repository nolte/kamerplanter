import { useEffect, useRef, useState, type CSSProperties } from 'react';
import { useLocation } from 'react-router-dom';
import { visuallyHidden } from '@mui/utils';

/** How long a lazily loaded page may take to render its heading before focus falls back to `main`. */
const HEADING_WAIT_MS = 3000;

interface RouteAnnouncerProps {
  /** Id of the `<main>` landmark the page renders into. */
  mainId: string;
}

/**
 * Focus and announcement on a client-side route change (#3017, W-02/L-08; WCAG 2.4.3, 4.1.3,
 * UI-NFR-002 R-011).
 *
 * A single-page app swaps the content without a page load, so a screen reader hears nothing and the
 * keyboard focus stays on the sidebar link that was activated. After every path change this moves
 * focus to the new page's `h1` (or to `main` when the page has none) and announces the heading through
 * a polite live region.
 *
 * Focus is only moved when it is not already inside `main`: a form page that autofocuses its first
 * field (UI-NFR-008 R-010) keeps that focus, and only the announcement is made. The first render is
 * left alone — on a fresh page load the browser's own focus handling and title announcement apply.
 */
export default function RouteAnnouncer({ mainId }: RouteAnnouncerProps) {
  const { pathname } = useLocation();
  const [message, setMessage] = useState('');
  const previousPath = useRef(pathname);

  useEffect(() => {
    if (previousPath.current === pathname) return;
    previousPath.current = pathname;
    const main = document.getElementById(mainId);
    if (!main) return;

    let done = false;
    const settle = (heading: HTMLElement | null) => {
      if (done) return;
      done = true;
      observer.disconnect();
      window.clearTimeout(timer);

      const active = document.activeElement;
      const focusInsideMain = active !== null && active !== document.body && main.contains(active);
      if (!focusInsideMain) {
        const target = heading ?? main;
        if (!target.hasAttribute('tabindex')) target.setAttribute('tabindex', '-1');
        target.focus({ preventScroll: true });
      }
      setMessage(heading?.textContent?.trim() || document.title);
    };

    const findHeading = () => main.querySelector<HTMLElement>('h1');
    const observer = new MutationObserver(() => {
      const heading = findHeading();
      if (heading) settle(heading);
    });
    const timer = window.setTimeout(() => settle(findHeading()), HEADING_WAIT_MS);

    const ready = findHeading();
    if (ready) {
      settle(ready);
    } else {
      observer.observe(main, { childList: true, subtree: true });
    }

    return () => {
      done = true;
      observer.disconnect();
      window.clearTimeout(timer);
    };
  }, [pathname, mainId]);

  return (
    <div role="status" aria-live="polite" aria-atomic="true" style={visuallyHidden as CSSProperties} data-testid="route-announcer">
      {message}
    </div>
  );
}
