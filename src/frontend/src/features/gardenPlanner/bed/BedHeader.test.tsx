/**
 * The head of the bed view (REQ-053 GP-FR-047, #2487): the drainage of the soil profile is shown with its
 * label, and left out while it is unknown.
 */
import { cleanup, screen, waitFor, within } from '@testing-library/react';
import { http, HttpResponse } from 'msw';
import { afterEach, describe, expect, it } from 'vitest';
import { expectNoA11yViolations } from '@/test/a11y/expectNoA11yViolations';
import { renderWithProviders } from '@/test/helpers';
import { server } from '@/test/mocks/server';
import BedHeader from './BedHeader';
import { bedSummary } from './bedTestKit';
import type { BedSummary, NutrientHint } from './types';
import type { ReachThresholds } from '@/api/types';
import { FABACEAE, SOLANACEAE, year as rotationYear } from '../history/historyTestKit';
import type { PreviousYearState } from '../history/usePreviousYear';

afterEach(() => cleanup());

const NOT_READ: PreviousYearState = { status: 'loading' };

function renderHeader(
  summary: BedSummary,
  reachThresholds?: Pick<ReachThresholds, 'both_sides_m' | 'one_side_m'>,
  previousYear = NOT_READ,
) {
  return renderWithProviders(
    <BedHeader
      summary={summary}
      reachThresholds={reachThresholds}
      previousYear={previousYear}
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
      '1.3 m wide – the access sides are not recorded and no path runs beside it, so the one-side value applies (0.6 m).',
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
    const detail = await screen.findByTestId('bed-reach-detail');
    expect(detail).toHaveTextContent('from two opposite sides you reach up to 1.2 m');
    // A number never wraps away from its unit ("(0,6" / "m)", #2764).
    expect(detail.textContent).toContain('1.3 m wide');
    expect(detail.textContent).toContain('1.2 m');
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

describe('BedHeader reach hint with access from paths (GP-FR-166, #2703)', () => {
  const rect = (width: number) => ({
    kind: 'rect' as const,
    origin: [1, 1] as [number, number],
    width_m: width,
    length_m: 4,
    rotation_deg: 0,
  });

  it('shows the hint for a 1.3 m bed with a path along one long side, from one side', async () => {
    renderHeader({
      ...bedSummary(),
      geometry: rect(1.3),
      site_conditions: { access_sides: [] },
      path_access: 'one',
    });
    expect(await screen.findByTestId('bed-reach-detail')).toHaveTextContent(
      '1.3 m wide – from one side you reach up to 0.6 m.',
    );
  });

  it('shows no hint for a 1.2 m bed with paths along both long sides', async () => {
    renderHeader({
      ...bedSummary(),
      geometry: rect(1.2),
      site_conditions: { access_sides: [] },
      path_access: 'both',
    });
    await screen.findByTestId('bed-header');
    expect(screen.queryByTestId('bed-header-reach')).toBeNull();
  });

  it('keeps the recorded opposite pair when the paths give less', async () => {
    renderHeader({
      ...bedSummary(),
      geometry: rect(1.2),
      site_conditions: { access_sides: ['N', 'S'] },
      path_access: 'none',
    });
    await screen.findByTestId('bed-header');
    expect(screen.queryByTestId('bed-header-reach')).toBeNull();
  });

  it('treats an absent path access (older backend) as no path', async () => {
    renderHeader({
      ...bedSummary(),
      geometry: rect(1.2),
      site_conditions: { access_sides: [] },
      path_access: undefined,
    });
    expect(await screen.findByTestId('bed-reach-detail')).toHaveTextContent(
      'no path runs beside it',
    );
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
      '0.9 m wide – the access sides are not recorded and no path runs beside it, so the one-side value applies (0.8 m).',
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

  it('shows no broken frame when the cover photo cannot be loaded (its attachment is gone)', async () => {
    let requested = 0;
    server.use(
      http.get('/api/v1/t/:tenant/attachments/:id/thumbnails/:px', () => {
        requested += 1;
        return new HttpResponse(null, { status: 404 });
      }),
    );
    renderHeader(bedSummary({ cover_photo_ref: 'p_gone' }));
    await screen.findByTestId('bed-header');
    await waitFor(() => expect(screen.queryByTestId('bed-header-cover')).toBeNull());
    expect(requested).toBe(1);
    expect(screen.queryByTestId('bed-header-cover-image-error')).toBeNull();
  });
});

describe('BedHeader nutrient hint (GP-FR-125)', () => {
  const hint = (state: NutrientHint['state'], reasons: NutrientHint['reasons'] = [], extra: Partial<NutrientHint> = {}) => ({
    state,
    confidence: 'medium' as const,
    reasons,
    compost_and_p_withheld: false,
    sources: ['test source'],
    ...extra,
  });

  it('shows "Fertiliser likely needed" with its reasons and no number', async () => {
    const view = renderHeader(
      bedSummary({
        nutrient_hint: hint('likely_deficit', ['feeding_overdue', 'preceding_nitrogen_fixer'], {
          compost_and_p_withheld: true,
        }),
      }),
    );
    const fact = await screen.findByTestId('bed-header-nutrient');
    expect(within(fact).getByTestId('bed-nutrient-badge')).toHaveTextContent('Fertiliser likely needed');
    expect(within(fact).getByTestId('bed-nutrient-reasons')).toHaveTextContent(
      'Your last feeding was a long time ago for the feeder level of your crop.',
    );
    expect(within(fact).getByTestId('bed-nutrient-reasons')).toHaveTextContent('beans or peas');
    expect(within(fact).getByTestId('bed-nutrient-reasons')).not.toHaveTextContent('compost');
    expect(within(fact).getByTestId('bed-nutrient-note')).toHaveTextContent(
      'An estimate from your care log. The app does not name a fertiliser amount.',
    );
    // never a measurement-like number: neither a value nor the source text reaches the head
    expect(fact.textContent).not.toMatch(/\d/);
    expect(fact).not.toHaveTextContent('test source');
    await expectNoA11yViolations(view.container);
  });

  it('words high P/K as no nutrient supply by compost, while it stays a soil improver', async () => {
    const view = renderHeader(
      bedSummary({
        nutrient_hint: hint('likely_deficit', ['k_class_low', 'p_or_k_class_high', 'standing_nitrogen_fixer'], {
          compost_and_p_withheld: true,
          withheld_source: 'R-006 source',
        }),
      }),
    );
    const reasons = await screen.findByTestId('bed-nutrient-reasons');
    expect(reasons).toHaveTextContent(
      'With high P/K contents compost serves no nutrient supply; as a soil improver it remains an option.',
    );
    expect(reasons).toHaveTextContent('are growing in this bed right now');
    expect(screen.getByTestId('bed-header-nutrient')).not.toHaveTextContent('R-006 source');
    await expectNoA11yViolations(view.container);
  });

  it('shows "Check feeding" for the check state', async () => {
    const view = renderHeader(bedSummary({ nutrient_hint: hint('check', ['bark_mulch_n_binding']) }));
    const badge = await screen.findByTestId('bed-nutrient-badge');
    expect(badge).toHaveTextContent('Check feeding');
    expect(badge).toHaveAttribute('data-state', 'check');
    expect(screen.getByTestId('bed-nutrient-reasons')).toHaveTextContent('Bark mulch can bind nitrogen while it rots.');
    await expectNoA11yViolations(view.container);
  });

  it.each(['ok', 'insufficient_data'] as const)('shows nothing for "%s"', async (state) => {
    renderHeader(bedSummary({ nutrient_hint: hint(state, ['thresholds_without_source']) }));
    await screen.findByTestId('bed-header');
    expect(screen.queryByTestId('bed-header-nutrient')).toBeNull();
  });

  it.each(['ok', 'insufficient_data'] as const)(
    'shows the salt-limit reason on its own for "%s" (E-17: it never changes the state)',
    async (state) => {
      const view = renderHeader(bedSummary({ nutrient_hint: hint(state, ['thresholds_without_source', 'check_salt_content']) }));
      const salt = await screen.findByTestId('bed-header-salt');
      expect(screen.getByTestId('bed-salt-badge')).toHaveTextContent('Check salt content');
      expect(salt).toHaveTextContent('above the stored salt limit');
      expect(salt).toHaveTextContent('derives no fertiliser amount');
      expect(salt.textContent).not.toMatch(/\d/);
      expect(screen.queryByTestId('bed-header-nutrient')).toBeNull();
      await expectNoA11yViolations(view.container);
    },
  );

  it('lists the salt-limit reason once, beside a nutrient state that is shown', async () => {
    renderHeader(bedSummary({ nutrient_hint: hint('check', ['feeding_due', 'check_salt_content']) }));
    const reasons = await screen.findByTestId('bed-nutrient-reasons');
    expect(reasons).not.toHaveTextContent('salt');
    expect(screen.getByTestId('bed-header-salt')).toHaveTextContent('above the stored salt limit');
  });

  it('shows no salt fact while the hint does not carry the reason', async () => {
    renderHeader(bedSummary({ nutrient_hint: hint('check', ['feeding_due']) }));
    await screen.findByTestId('bed-nutrient-reasons');
    expect(screen.queryByTestId('bed-header-salt')).toBeNull();
  });

  it('shows nothing without a hint (a location that is no bed, or an older server)', async () => {
    renderHeader(bedSummary({ nutrient_hint: null }));
    await screen.findByTestId('bed-header');
    expect(screen.queryByTestId('bed-header-nutrient')).toBeNull();
    cleanup();
    renderHeader(bedSummary());
    await screen.findByTestId('bed-header');
    expect(screen.queryByTestId('bed-header-nutrient')).toBeNull();
  });
});

describe('BedHeader site flags (GP-FR-165, WP 9.11)', () => {
  it('shows a chip with the reported flags under the site features', async () => {
    const view = renderHeader(
      bedSummary({ site_conditions: { flags: ['root_competition', 'allelopathy_risk'] } }),
    );
    const badge = await screen.findByTestId('bed-site-flags-badge');
    expect(badge).toHaveTextContent('Root competition/Allelopathy risk reported at this site');
    // A note, not a rating: the chip is neutral.
    expect(badge).toHaveClass('MuiChip-colorInfo');
    await expectNoA11yViolations(view.container);
  });

  it('names a single flag only, and a bed with flags only has a site line instead of nothing', async () => {
    renderHeader(bedSummary({ site_conditions: { flags: ['allelopathy_risk'] } }));
    const badge = await screen.findByTestId('bed-site-flags-badge');
    expect(badge).toHaveTextContent('Allelopathy risk reported at this site');
    expect(badge).not.toHaveTextContent('Root competition');
    const site = screen.getByTestId('bed-header-site');
    expect(site).toHaveTextContent('Competition: Allelopathy risk');
    expect(site).not.toHaveTextContent('Not set');
  });

  it('says "Not set" when nothing at all is recorded', async () => {
    renderWithProviders(
      <BedHeader
        summary={bedSummary({ site_conditions: { flags: [] } })}
        typeName="Raised bed"
        assignees={[]}
        year={2026}
        years={[2026]}
        onYearChange={() => undefined}
        onChangeStatus={null}
        onChangeSite={() => undefined}
        previousYear={NOT_READ}
      />,
    );
    expect(await screen.findByTestId('bed-header-site')).toHaveTextContent('Not set');
    expect(screen.queryByTestId('bed-site-flags')).toBeNull();
  });

  it('shows no chip while no flag is set', async () => {
    renderHeader(bedSummary({ site_conditions: { flags: [], wind_exposure: 'exposed' } }));
    await screen.findByTestId('bed-header-site');
    expect(screen.queryByTestId('bed-site-flags')).toBeNull();
  });
});

describe('BedHeader nearest water source (GP-FR-167, WP 9.12)', () => {
  it('shows the distance the server derived, from the bed edge', async () => {
    const view = renderHeader({ ...bedSummary(), nearest_water_source_m: 3.25 });
    expect(await screen.findByTestId('bed-header-water-source')).toHaveTextContent(
      'Nearest water source3.25 m in a straight line from the bed edge',
    );
    await expectNoA11yViolations(view.container);
  });

  it.each([0, 0.003, 0.0049])('says "Right at the bed" for %s m (nothing that would print as 0 m)', async (metres) => {
    renderHeader({ ...bedSummary(), nearest_water_source_m: metres });
    const fact = await screen.findByTestId('bed-header-water-source');
    expect(fact).toHaveTextContent('Right at the bed');
    expect(fact).not.toHaveTextContent('0 m');
  });

  it('shows the smallest distance that is not 0 at the display precision', async () => {
    renderHeader({ ...bedSummary(), nearest_water_source_m: 0.005 });
    expect(await screen.findByTestId('bed-header-water-source')).toHaveTextContent('0.01 m in a straight line');
  });

  it('shows nothing without a water source (null is not 0 m) or from an older server', async () => {
    renderHeader({ ...bedSummary(), nearest_water_source_m: null });
    await screen.findByTestId('bed-header');
    expect(screen.queryByTestId('bed-header-water-source')).toBeNull();
    cleanup();

    renderHeader(bedSummary());
    await screen.findByTestId('bed-header');
    expect(screen.queryByTestId('bed-header-water-source')).toBeNull();
  });
});

describe('BedHeader area (#2764 item 5)', () => {
  it('says "Not set" for a bed without an area instead of "0 m²"', async () => {
    renderHeader(bedSummary({ area_m2: 0 }));
    const area = await screen.findByTestId('bed-header-area');
    expect(area).toHaveTextContent('Not set');
    expect(area).not.toHaveTextContent('0 m²');
  });
});

describe('BedHeader previous year (GP-FR-077, #2764 item 1)', () => {
  it('names what the rotation timeline holds for the previous year, not a placeholder', async () => {
    renderHeader(
      bedSummary(),
      undefined,
      {
        status: 'ready',
        entry: rotationYear(2025, [
          { ...FABACEAE, season: 'spring', source: 'backfill', care_event_key: 'ce_1' },
          { ...SOLANACEAE, season: 'main', source: 'backfill', care_event_key: 'ce_2' },
        ]),
      },
    );
    const line = await screen.findByTestId('bed-header-previous-year');
    expect(line).toHaveTextContent(
      'Previous year (2025): Fabaceae (Light Feeder, Spring); Solanaceae (Heavy Feeder, Main season)',
    );
    expect(line).not.toHaveTextContent('once it has been recorded');
  });

  it('says "nothing recorded" for an empty year, and why it cannot say more while loading or after an error', async () => {
    renderHeader(bedSummary(), undefined, { status: 'ready', entry: rotationYear(2025) });
    expect(await screen.findByTestId('bed-header-previous-year')).toHaveTextContent('Previous year (2025): Nothing recorded');
    cleanup();

    renderHeader(bedSummary(), undefined, { status: 'error' });
    expect(await screen.findByTestId('bed-header-previous-year')).toHaveTextContent('cannot be read right now');
  });

  it('words fallow and green manure as the timeline does', async () => {
    renderHeader(bedSummary(), undefined, {
      status: 'ready',
      entry: rotationYear(2025, [
        { ...SOLANACEAE, plan_role: 'fallow', family_key: null, family_name: null, nutrient_demand: null },
        { ...FABACEAE, plan_role: 'green_manure' },
      ]),
    });
    expect(await screen.findByTestId('bed-header-previous-year')).toHaveTextContent(
      'Previous year (2025): Fallow; Fabaceae · Green manure (Light Feeder)',
    );
  });
});
