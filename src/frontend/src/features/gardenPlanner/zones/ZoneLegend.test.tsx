/**
 * The layer legend (REQ-053 GP-FR-031, GP-FR-169, #2487): one section per visible site-condition layer, each value
 * with its pattern swatch, its glyph and its words, so the legend works without seeing colour (WCAG 1.4.1).
 */
import { cleanup, screen, within } from '@testing-library/react';
import { afterEach, describe, expect, it } from 'vitest';
import { expectNoA11yViolations } from '@/test/a11y/expectNoA11yViolations';
import { renderWithProviders } from '@/test/helpers';
import { ZoneLegend } from './ZoneLegend';

afterEach(() => cleanup());

const SECTIONS = ['zones', 'watered', 'sun', 'moisture', 'frost', 'plantState'] as const;

function shownSections(): string[] {
  return SECTIONS.filter((id) => screen.queryByTestId(`garden-plan-legend-${id}`) !== null);
}

describe('ZoneLegend site-condition sections', () => {
  it('renders nothing while no layer is on', () => {
    renderWithProviders(<ZoneLegend zones={[]} showZones={false} showLastWatered={false} />);
    expect(screen.queryByTestId('garden-plan-layer-legend')).toBeNull();
  });

  it.each([
    [{ showSun: true }, ['sun']],
    [{ showMoisture: true }, ['moisture']],
    [{ showFrost: true }, ['frost']],
    [{ showSun: true, showFrost: true }, ['sun', 'frost']],
  ] as const)('shows only the sections of the visible layers (%o)', async (flags, expected) => {
    renderWithProviders(<ZoneLegend zones={[]} showZones={false} showLastWatered={false} {...flags} />);
    await screen.findByTestId('garden-plan-layer-legend');
    expect(shownSections()).toEqual(expected);
  });

  it('words every value with its enum label next to a pattern and a glyph', async () => {
    renderWithProviders(
      <ZoneLegend zones={[]} showZones={false} showLastWatered={false} showSun showMoisture showFrost />,
    );
    const legend = await screen.findByTestId('garden-plan-layer-legend');
    const expected: Record<string, string[]> = {
      sun: ['Morning', 'Midday', 'Afternoon', 'All day', 'Changing'],
      moisture: ['Poor', 'Moderate', 'Good'],
      frost: ['Low', 'Normal', 'High'],
    };
    for (const [id, labels] of Object.entries(expected)) {
      const section = within(legend).getByTestId(`garden-plan-legend-${id}`);
      const items = within(section).getAllByRole('listitem');
      expect(items.map((item) => item.textContent)).toEqual(labels);
      for (const item of items) {
        const value = item.getAttribute('data-legend-value');
        expect(item.querySelector(`pattern#gp-legend-${id}-${value}`)).not.toBeNull();
        expect(item.querySelector(`[data-condition-glyph="${value}"]`)).not.toBeNull();
      }
      expect(section).toHaveTextContent('No pattern: not recorded.');
    }
    expect(within(legend).getByTestId('garden-plan-legend-sun')).toHaveTextContent('Sun window');
    expect(within(legend).getByTestId('garden-plan-legend-moisture')).toHaveTextContent('Drainage');
    expect(within(legend).getByTestId('garden-plan-legend-frost')).toHaveTextContent('Frost risk');
    await expectNoA11yViolations(legend);
  });

  it('keeps the irrigation sections next to the condition sections', async () => {
    renderWithProviders(<ZoneLegend zones={[]} showZones showLastWatered showMoisture />);
    await screen.findByTestId('garden-plan-layer-legend');
    expect(shownSections()).toEqual(['zones', 'watered', 'moisture']);
  });
});

describe('ZoneLegend plant-state section (GP-UX-061, #2488)', () => {
  it('shows no plant-state section while the layer is off', () => {
    renderWithProviders(
      <ZoneLegend zones={[]} showZones={false} showLastWatered={false} showFrost phases={['flowering']} />,
    );
    expect(screen.queryByTestId('garden-plan-legend-plantState')).toBeNull();
  });

  it('explains rings, badges and the colours of the phases on the plan, in words', async () => {
    renderWithProviders(
      <ZoneLegend
        zones={[]}
        showZones={false}
        showLastWatered={false}
        showPlantState
        phases={['Flowering', 'vegetative', 'Mulching']}
      />,
    );
    const section = await screen.findByTestId('garden-plan-legend-plantState');
    expect(shownSections()).toEqual(['plantState']);
    expect(section).toHaveTextContent('Plant state');
    const rings = await within(section).findAllByText(/./, { selector: '[data-legend-ring] p' });
    expect(rings).toHaveLength(5);
    expect(section.querySelectorAll('[data-legend-badge] [data-plan-badge-reason]')).toHaveLength(5);
    const phases = [...section.querySelectorAll('[data-legend-phase]')];
    // known phase names are worded by their enum label, an unknown one keeps its own name
    expect(phases.map((item) => item.textContent)).toEqual(['Flowering', 'Vegetative', 'Mulching']);
    expect(phases[0].querySelector('circle')?.getAttribute('fill')).toBe('#AB47BC');
    expect(section.querySelector('pattern')).toBeNull();
    await expectNoA11yViolations(screen.getByTestId('garden-plan-layer-legend'));
  });

  it('says so when no plant with a known phase is on the plan', async () => {
    renderWithProviders(<ZoneLegend zones={[]} showZones={false} showLastWatered={false} showPlantState />);
    const section = await screen.findByTestId('garden-plan-legend-plantState');
    expect(await within(section).findByText('No plant with a known phase is on the plan yet.')).toBeInTheDocument();
  });
});
