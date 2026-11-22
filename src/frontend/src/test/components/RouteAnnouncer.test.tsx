/**
 * #3017 (W-02, L-08) — on a client-side route change the focus stayed on the sidebar link and nothing was
 * announced. The RouteAnnouncer moves focus to the new page's h1 and announces it politely.
 */
import { useEffect, useState } from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { Link, MemoryRouter, Route, Routes } from 'react-router-dom';
import { describe, expect, it } from 'vitest';
import RouteAnnouncer from '@/components/layout/RouteAnnouncer';

function LatePage() {
  // Stands in for a lazily loaded route: the heading arrives after the route change committed.
  const [ready, setReady] = useState(false);
  useEffect(() => {
    const id = window.setTimeout(() => setReady(true), 30);
    return () => window.clearTimeout(id);
  }, []);
  return ready ? <h1>Late page</h1> : <p>loading</p>;
}

function FormPage() {
  return (
    <>
      <h1>Form page</h1>
      {/* UI-NFR-008 R-010: a form focuses its first field on open. */}
      <input aria-label="first field" autoFocus />
    </>
  );
}

function Shell() {
  return (
    <>
      <nav>
        <Link to="/plants">Plants</Link>
        <Link to="/late">Late</Link>
        <Link to="/form">Form</Link>
        <Link to="/bare">Bare</Link>
      </nav>
      <RouteAnnouncer mainId="main-content" />
      <main id="main-content">
        <Routes>
          <Route path="/" element={<h1>Start</h1>} />
          <Route path="/plants" element={<h1>Plants overview</h1>} />
          <Route path="/late" element={<LatePage />} />
          <Route path="/form" element={<FormPage />} />
          <Route path="/bare" element={<p>no heading here</p>} />
        </Routes>
      </main>
    </>
  );
}

function renderShell() {
  return render(
    <MemoryRouter initialEntries={['/']}>
      <Shell />
    </MemoryRouter>,
  );
}

describe('RouteAnnouncer (#3017)', () => {
  it('leaves the first render alone', () => {
    renderShell();
    expect(document.body).toHaveFocus();
    expect(screen.getByTestId('route-announcer')).toHaveTextContent('');
  });

  it('moves focus from the activated nav link to the new page heading and announces it', async () => {
    const user = userEvent.setup();
    renderShell();
    await user.click(screen.getByRole('link', { name: 'Plants' }));

    const heading = await screen.findByRole('heading', { level: 1, name: 'Plants overview' });
    await waitFor(() => expect(heading).toHaveFocus());
    expect(heading).toHaveAttribute('tabindex', '-1');
    const region = screen.getByTestId('route-announcer');
    expect(region).toHaveAttribute('aria-live', 'polite');
    expect(region).toHaveTextContent('Plants overview');
  });

  it('waits for a heading that renders after the route change', async () => {
    const user = userEvent.setup();
    renderShell();
    await user.click(screen.getByRole('link', { name: 'Late' }));
    const heading = await screen.findByRole('heading', { level: 1, name: 'Late page' });
    await waitFor(() => expect(heading).toHaveFocus());
    expect(screen.getByTestId('route-announcer')).toHaveTextContent('Late page');
  });

  it('keeps the focus a page set itself inside main and only announces', async () => {
    const user = userEvent.setup();
    renderShell();
    await user.click(screen.getByRole('link', { name: 'Form' }));
    await waitFor(() => expect(screen.getByTestId('route-announcer')).toHaveTextContent('Form page'));
    expect(screen.getByRole('textbox', { name: 'first field' })).toHaveFocus();
  });

  it('falls back to main when the page has no h1', async () => {
    const user = userEvent.setup();
    renderShell();
    document.title = 'Bare — Kamerplanter';
    await user.click(screen.getByRole('link', { name: 'Bare' }));
    await waitFor(() => expect(screen.getByRole('main')).toHaveFocus(), { timeout: 5000 });
    expect(screen.getByTestId('route-announcer')).toHaveTextContent('Bare — Kamerplanter');
  });
});
