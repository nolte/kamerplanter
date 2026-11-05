/**
 * The head of the bed view (REQ-053 GP-FR-047, #2487): the drainage of the soil profile is shown with its
 * label, and left out while it is unknown.
 */
import { cleanup, screen, within } from '@testing-library/react';
import { http, HttpResponse } from 'msw';
import { afterEach, describe, expect, it } from 'vitest';
import { expectNoA11yViolations } from '@/test/a11y/expectNoA11yViolations';
import { renderWithProviders } from '@/test/helpers';
import { server } from '@/test/mocks/server';
import BedHeader from './BedHeader';
import { bedSummary } from './bedTestKit';
import type { BedSummary } from './types';
import type { ReachThresholds } from '@/api/types';

afterEach(() => cleanup());

function renderHeader(summary: BedSummary, reachThresholds?: ReachThresholds) {
  return renderWithProviders(
    <BedHeader
      summary={summary}
      reachThresholds={reachThresholds}
      typeName="Raised bed"
      assignees={[]}
      year={2026}
      years={[2026]}
      onYearChange={() => undefined}
      onChangeStatus={null}
    />,
  );
}

describe('BedHeader drainage (GP-FR-047)', () => {
  it('shows the drainage with its label when it is known', async () => {
    const view = renderHeader(bedSummary());
    const drainage = await screen.findByTestId('bed-header-drainage');
    expect(drainage).toHaveTextContent('Drainage');
    expect(within(drainage).getByText('Good')).toBeInTheDocument();
    await expectNoA11yViolations(view.container);
  });

  it.each(['poor', 'moderate'] as const)('words the drainage "%s" from the enum', async (drainage) => {
    const base = bedSummary();
    renderHeader({ ...base, soil_profile: { ...base.soil_profile!, drainage } });
    expect(await screen.findByTestId('bed-header-drainage')).toHaveTextContent(
      drainage === 'poor' ? 'Poor' : 'Moderate',
    );
  });

  it('leaves the drainage out while it is unknown or there is no soil profile', async () => {
    const base = bedSummary();
    renderHeader({ ...base, soil_profile: { ...base.soil_profile!, drainage: 'unknown' } });
    await screen.findByTestId('bed-header');
    expect(screen.queryByTestId('bed-header-drainage')).toBeNull();
    cleanup();

    renderHeader({ ...base, soil_profile: null });
    await screen.findByTestId('bed-header');
    expect(screen.queryByTestId('bed-header-drainage')).toBeNull();
  });
});

describe('BedHeader reach hint (GP-FR-166)', () => {
  const rect = (width: number) => ({
    kind: 'rect' as const,
    origin: [1, 1] as [number, number],
    width_m: width,
    length_m: 4,
    rotation_deg: 0,
  });

  it('shows the badge for a 1.3 m bed without access sides, with the strict one-side value', async () => {
    const view = renderHeader({ ...bedSummary(), geometry: rect(1.3), site_conditions: { access_sides: [] } });
    const reach = await screen.findByTestId('bed-header-reach');
    expect(within(reach).getByTestId('bed-reach-badge')).toHaveTextContent('Bed too wide');
    expect(within(reach).getByTestId('bed-reach-detail')).toHaveTextContent(
      '1.3 m wide – the access sides are not recorded, so the one-side value applies (0.6 m).',
    );
    await expectNoA11yViolations(view.container);
  });

  it('shows no badge for a bed within reach from two opposite sides', async () => {
    renderHeader({ ...bedSummary(), geometry: rect(1.2), site_conditions: { access_sides: ['N', 'S'] } });
    await screen.findByTestId('bed-header');
    expect(screen.queryByTestId('bed-header-reach')).toBeNull();
  });

  it('names the two-side value when a bed with an opposite pair is still too wide', async () => {
    renderHeader({ ...bedSummary(), geometry: rect(1.3), site_conditions: { access_sides: ['E', 'W'] } });
    expect(await screen.findByTestId('bed-reach-detail')).toHaveTextContent(
      'from two opposite sides you reach up to 1.2 m',
    );
  });

  it('keeps the millimetre that makes a bed too wide visible', async () => {
    renderHeader({ ...bedSummary(), geometry: rect(0.601), site_conditions: { access_sides: ['S'] } });
    expect(await screen.findByTestId('bed-reach-detail')).toHaveTextContent('0.601 m wide');
  });

  it('reads two adjacent sides as one-side access', async () => {
    renderHeader({ ...bedSummary(), geometry: rect(1.0), site_conditions: { access_sides: ['N', 'E'] } });
    expect(await screen.findByTestId('bed-reach-detail')).toHaveTextContent('from one side you reach up to 0.6 m');
  });

  it('stays silent and renders the head when the bed has no geometry', async () => {
    renderHeader({ ...bedSummary(), geometry: null, site_conditions: null });
    expect(await screen.findByTestId('bed-header-area')).toBeInTheDocument();
    expect(screen.queryByTestId('bed-header-reach')).toBeNull();
  });
});

describe('BedHeader reach hint with the site thresholds (GP-FR-166, WP 8.24)', () => {
  const rect = (width: number) => ({
    kind: 'rect' as const,
    origin: [1, 1] as [number, number],
    width_m: width,
    length_m: 4,
    rotation_deg: 0,
  });

  it('takes the site two-side value instead of 1.2 m: a 1.3 m bed is within 1.5 m', async () => {
    renderHeader(
      { ...bedSummary(), geometry: rect(1.3), site_conditions: { access_sides: ['N', 'S'] } },
      { both_sides_m: 1.5, one_side_m: 0.6 },
    );
    await screen.findByTestId('bed-header');
    expect(screen.queryByTestId('bed-header-reach')).toBeNull();
  });

  it('names the site one-side value in the detail', async () => {
    renderHeader(
      { ...bedSummary(), geometry: rect(0.9), site_conditions: { access_sides: [] } },
      { both_sides_m: 1.2, one_side_m: 0.8 },
    );
    expect(await screen.findByTestId('bed-reach-detail')).toHaveTextContent(
      '0.9 m wide – the access sides are not recorded, so the one-side value applies (0.8 m).',
    );
  });

  it('a stricter site value raises the hint where the default would not', async () => {
    renderHeader(
      { ...bedSummary(), geometry: rect(1.0), site_conditions: { access_sides: ['E', 'W'] } },
      { both_sides_m: 0.9, one_side_m: 0.5 },
    );
    expect(await screen.findByTestId('bed-reach-detail')).toHaveTextContent(
      'from two opposite sides you reach up to 0.9 m',
    );
  });
});

describe('BedHeader cover photo (GP-FR-051)', () => {
  it('leads the head with the cover photo, fetched as the 512 px rendition of cover_photo_ref', async () => {
    const seen: string[] = [];
    server.use(
      http.get('/api/v1/t/:tenant/attachments/:id/thumbnails/:px', ({ params }) => {
        seen.push(`${String(params.id)}/${String(params.px)}`);
        return HttpResponse.arrayBuffer(new Uint8Array([1, 2, 3]).buffer, { headers: { 'Content-Type': 'image/jpeg' } });
      }),
    );
    const view = renderHeader(bedSummary({ cover_photo_ref: 'p_cover' }));
    const image = await screen.findByTestId('bed-header-cover-image');
    expect(image).toHaveAttribute('alt', 'Cover photo of Raised bed 3');
    expect(seen).toEqual(['p_cover/512']);
    await expectNoA11yViolations(view.container);
  });

  it('shows no photo frame while the bed has no cover', async () => {
    renderHeader(bedSummary({ cover_photo_ref: null }));
    await screen.findByTestId('bed-header');
    expect(screen.queryByTestId('bed-header-cover')).toBeNull();
  });
});
