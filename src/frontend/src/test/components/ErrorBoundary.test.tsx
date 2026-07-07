import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { useState } from 'react';
import ErrorBoundary from '@/components/common/ErrorBoundary';

function Bomb({ explode }: { explode: boolean }): React.ReactElement {
  if (explode) throw new Error('boom');
  return <div data-testid="safe-child">alles gut</div>;
}

describe('ErrorBoundary', () => {
  let errorSpy: ReturnType<typeof vi.spyOn>;
  beforeEach(() => {
    // React logs caught render errors to console.error — silence for clean output.
    errorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
  });
  afterEach(() => {
    errorSpy.mockRestore();
  });

  it('renders children when nothing throws', () => {
    render(
      <ErrorBoundary title="Fehler" hint="Bitte erneut" retryLabel="Wiederholen">
        <Bomb explode={false} />
      </ErrorBoundary>,
    );
    expect(screen.getByTestId('safe-child')).toBeInTheDocument();
  });

  it('renders the fallback with title + hint when a child throws', () => {
    render(
      <ErrorBoundary title="Widget kaputt" hint="Erneut versuchen" retryLabel="Wiederholen">
        <Bomb explode={true} />
      </ErrorBoundary>,
    );
    expect(screen.getByTestId('widget-error')).toBeInTheDocument();
    expect(screen.getByText('Widget kaputt')).toBeInTheDocument();
    expect(screen.getByText('Erneut versuchen')).toBeInTheDocument();
  });

  it('honours a custom testId on the fallback', () => {
    render(
      <ErrorBoundary title="t" hint="h" retryLabel="r" testId="widget-error-plants">
        <Bomb explode={true} />
      </ErrorBoundary>,
    );
    expect(screen.getByTestId('widget-error-plants')).toBeInTheDocument();
  });

  it('recovers via the retry button once the child stops throwing', async () => {
    const user = userEvent.setup();

    function Harness(): React.ReactElement {
      const [explode, setExplode] = useState(true);
      return (
        <>
          <button onClick={() => setExplode(false)}>fix</button>
          <ErrorBoundary title="Fehler" hint="Hinweis" retryLabel="Wiederholen">
            <Bomb explode={explode} />
          </ErrorBoundary>
        </>
      );
    }

    render(<Harness />);
    expect(screen.getByTestId('widget-error')).toBeInTheDocument();

    // Stop the child from throwing, then hit retry to remount the subtree.
    await user.click(screen.getByText('fix'));
    await user.click(screen.getByText('Wiederholen'));

    expect(screen.getByTestId('safe-child')).toBeInTheDocument();
    expect(screen.queryByTestId('widget-error')).not.toBeInTheDocument();
  });
});
