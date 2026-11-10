/**
 * The tent rules of a location (REQ-053 WP 10.11, W-016): the light-schedule hints in words, the location's own
 * neighbourhood factor and its lighting, written through `PATCH /locations/{key}`.
 */
import { cleanup, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { http, HttpResponse } from 'msw';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { expectNoA11yViolations } from '@/test/a11y/expectNoA11yViolations';
import { renderWithProviders } from '@/test/helpers';
import { server } from '@/test/mocks/server';
import TentRulesSection from './TentRulesSection';
import type { TentHint } from './types';

const BASE = '/api/v1/t/:tenant';

function usePatch() {
  const bodies: unknown[] = [];
  server.use(
    http.patch(`${BASE}/locations/:key`, async ({ request }) => {
      bodies.push(await request.json());
      return HttpResponse.json({ key: 'loc_tent', bed_status: 'active', plan_revision: 3 });
    }),
  );
  return bodies;
}

function renderSection(props: Partial<Parameters<typeof TentRulesSection>[0]> = {}) {
  const onSaved = vi.fn();
  const view = renderWithProviders(
    <TentRulesSection
      locationKey="loc_tent"
      supportsLayout
      adjacencyFactor={null}
      lighting={null}
      hints={[]}
      canEdit
      onSaved={onSaved}
      {...props}
    />,
  );
  return { onSaved, ...view };
}

const CONFLICT: TentHint = {
  code: 'tent.photoperiod_conflict',
  severity: 'warning',
  groups: [
    { photoperiod_hours: 18, plant_count: 2, phase_names: ['Vegetative'] },
    { photoperiod_hours: 12, plant_count: 1, phase_names: [] },
  ],
  unknown_plant_count: 1,
};

afterEach(() => cleanup());

describe('TentRulesSection', () => {
  it('describes a photoperiod conflict in words, without its code', () => {
    renderSection({ hints: [CONFLICT] });

    const alert = screen.getByTestId('tent-hint-photoperiod-conflict');
    expect(alert).toHaveTextContent('Different light needs under one lamp');
    expect(alert).toHaveTextContent('18 hours of light for 2 plants (Vegetative); 12 hours of light for 1 plant');
    expect(alert).toHaveTextContent('For 1 more plant no light duration is recorded');
    expect(alert).not.toHaveTextContent('tent.photoperiod_conflict');
  });

  it('says when the light needs of some plants are unknown', () => {
    renderSection({
      hints: [{ code: 'tent.photoperiod_unknown', severity: 'info', groups: [], unknown_plant_count: 2 }],
    });

    expect(screen.getByTestId('tent-hint-photoperiod-unknown')).toHaveTextContent(
      'For 2 plants no light duration is recorded for their current phase.',
    );
  });

  it('writes the factor and the lighting in one PATCH and keeps a stored fixture footprint', async () => {
    const bodies = usePatch();
    const user = userEvent.setup();
    const fixture = { kind: 'rect', origin: [0.1, 0.1], width_m: 0.6, length_m: 0.6 };
    const { onSaved } = renderSection({ lighting: { fixture_geometry: fixture } });

    await user.type(screen.getByRole('spinbutton', { name: 'Neighbourhood factor' }), '2.5');
    await user.type(screen.getByRole('spinbutton', { name: 'Lamp height' }), '180');
    await user.type(screen.getByRole('spinbutton', { name: 'Distance to the plants' }), '40');
    await user.click(screen.getByRole('button', { name: /save/i }));

    await waitFor(() => expect(onSaved).toHaveBeenCalledTimes(1));
    expect(bodies).toEqual([
      {
        adjacency_factor: 2.5,
        lighting: { lamp_height_cm: 180, canopy_distance_cm: 40, fixture_geometry: fixture },
      },
    ]);
  });

  it('refuses a canopy farther from the lamp than the lamp is high, before any request', async () => {
    const bodies = usePatch();
    const user = userEvent.setup();
    renderSection();

    await user.type(screen.getByRole('spinbutton', { name: 'Lamp height' }), '50');
    await user.type(screen.getByRole('spinbutton', { name: 'Distance to the plants' }), '80');
    await user.click(screen.getByRole('button', { name: /save/i }));

    expect(await screen.findByText('The distance to the plants cannot be larger than the lamp height.')).toBeVisible();
    expect(bodies).toEqual([]);
  });

  it('is read-only for a viewer', () => {
    renderSection({ canEdit: false, adjacencyFactor: 2 });

    expect(screen.getByRole('spinbutton', { name: 'Neighbourhood factor' })).toBeDisabled();
    expect(screen.queryByRole('button', { name: /save/i })).not.toBeInTheDocument();
  });

  it('shows nothing for a location without a layout and without hints', () => {
    renderSection({ supportsLayout: false });

    expect(screen.queryByTestId('tent-rules-section')).not.toBeInTheDocument();
  });

  it('has no critical accessibility violation', async () => {
    const { container } = renderSection({ hints: [CONFLICT] });
    await expectNoA11yViolations(container);
  });
});
