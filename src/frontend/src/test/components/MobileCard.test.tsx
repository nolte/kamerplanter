import { render, screen, cleanup } from '@testing-library/react';
import { describe, it, expect, afterEach } from 'vitest';
import Chip from '@mui/material/Chip';
import MobileCard from '@/components/common/MobileCard';

describe('MobileCard — test hooks', () => {
  afterEach(() => {
    cleanup();
  });

  it('emits a hook for the title and the subtitle', () => {
    render(<MobileCard title="Tomate" subtitle="TOM-001" />);

    // Before these hooks existed the only anchors were the MUI class names
    // (`.MuiTypography-subtitle2` plus a following-sibling caption), which the
    // E2E page objects had to hard-code.
    expect(screen.getByTestId('card-title').textContent).toBe('Tomate');
    expect(screen.getByTestId('card-subtitle').textContent).toBe('TOM-001');
  });

  it('omits the subtitle hook when there is no subtitle', () => {
    render(<MobileCard title="Tomate" />);

    expect(screen.queryByTestId('card-subtitle')).toBeNull();
  });

  it('additionally keys the title and subtitle by the column id they mirror', () => {
    render(
      <MobileCard title="25.07.2026, 10:00" titleId="loggedAt" subtitle="TOM-001" subtitleId="plants" />,
    );

    // Most cards render their identifying values as title/subtitle, where they
    // used to be reachable only through `card-title`/`card-subtitle` — i.e. not
    // by the column id that addresses the same value on the desktop table.
    expect(screen.getByTestId('card-field-loggedAt').textContent).toBe('25.07.2026, 10:00');
    expect(screen.getByTestId('card-field-plants').textContent).toBe('TOM-001');
    // The pre-existing hooks stay intact and keep carrying the full value.
    expect(screen.getByTestId('card-title').textContent).toBe('25.07.2026, 10:00');
    expect(screen.getByTestId('card-subtitle').textContent).toBe('TOM-001');
  });

  it('omits the column hook when the caller keys no title/subtitle id', () => {
    render(<MobileCard title="Tomate" subtitle="TOM-001" />);

    expect(document.querySelector('[data-testid^="card-field-"]')).toBeNull();
    expect(screen.getByTestId('card-title').textContent).toBe('Tomate');
  });

  it('keys each field by the column id it mirrors', () => {
    render(
      <MobileCard
        title="Tomate"
        fields={[
          { id: 'location', label: 'Standort', value: 'Beet 1' },
          { id: 'currentPhase', label: 'Phase', value: 'Vegetativ' },
        ]}
      />,
    );

    // Reading "the phase field" by position read the location field instead —
    // the defect this hook removes.
    expect(screen.getByTestId('card-field-currentPhase').textContent).toBe('Vegetativ');
    expect(screen.getByTestId('card-field-location').textContent).toBe('Beet 1');
  });

  it('renders an unkeyed field without a hook and without dropping its value', () => {
    render(
      <MobileCard title="Tomate" fields={[{ label: 'Standort', value: 'Beet 1' }]} />,
    );

    expect(screen.getByText('Beet 1')).toBeInTheDocument();
    expect(document.querySelector('[data-testid^="card-field-"]')).toBeNull();
  });

  it('keys each chip by the column id it mirrors', () => {
    render(
      <MobileCard
        title="Tomate"
        chips={[
          { id: 'currentPhase', content: <Chip size="small" label="Vegetativ" /> },
          { id: 'plantingRun', content: <Chip size="small" label="Durchlauf A" /> },
        ]}
      />,
    );

    expect(screen.getByTestId('card-chip-currentPhase').textContent).toBe('Vegetativ');
    expect(screen.getByTestId('card-chip-plantingRun').textContent).toBe('Durchlauf A');
  });

  it('keeps the chip hook stable when a preceding chip is absent', () => {
    render(
      <MobileCard
        title="Tomate"
        chips={[{ id: 'plantingRun', content: <Chip size="small" label="Durchlauf A" /> }]}
      />,
    );

    // Index 0 would now be the planting-run chip; the keyed hook still says
    // there is no phase chip instead of returning the wrong one.
    expect(screen.queryByTestId('card-chip-currentPhase')).toBeNull();
    expect(screen.getByTestId('card-chip-plantingRun').textContent).toBe('Durchlauf A');
  });

  it('does not overwrite a caller-provided chip testid', () => {
    render(
      <MobileCard
        title="Tomate"
        chips={[
          {
            id: 'recognition',
            content: <Chip size="small" label="Erkennung" data-testid="recognition-chip" />,
          },
        ]}
      />,
    );

    // Existing testids are a contract; the keyed hook must not shadow them.
    expect(screen.getByTestId('recognition-chip').textContent).toBe('Erkennung');
    expect(screen.queryByTestId('card-chip-recognition')).toBeNull();
  });

  it('carries the hook on a span when the chip content is not an element', () => {
    render(<MobileCard title="Tomate" chips={[{ id: 'status', content: 'aktiv' }]} />);

    expect(screen.getByTestId('card-chip-status').textContent).toBe('aktiv');
  });

  it('still accepts a plain node as chips (legacy callers)', () => {
    render(
      <MobileCard
        title="Tomate"
        chips={
          <>
            <Chip size="small" label="Vegetativ" />
            <Chip size="small" label="Durchlauf A" />
          </>
        }
      />,
    );

    expect(screen.getByText('Vegetativ')).toBeInTheDocument();
    expect(document.querySelector('[data-testid^="card-chip-"]')).toBeNull();
  });

  it('renders no chip row for an empty keyed chip list', () => {
    const { container } = render(<MobileCard title="Tomate" chips={[]} />);

    // A conditional chip list can collapse to []; that must not leave an empty
    // spacer row above the fields.
    expect(container.querySelectorAll('.MuiChip-root').length).toBe(0);
    expect(document.querySelector('[data-testid^="card-chip-"]')).toBeNull();
  });
});
