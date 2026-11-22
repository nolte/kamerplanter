import { act, cleanup, render, screen } from '@testing-library/react';
import i18n from 'i18next';
import { afterEach, describe, expect, it } from 'vitest';
import PlantStateLegendSection from './PlantStateLegendSection';

/** The phase list of the plant-state legend (REQ-053 GP-UX-061, #2488): translated names, sorted in the active language. */
const phaseLabels = () =>
  [...document.querySelectorAll('[data-legend-phase]')].map((node) => node.textContent?.trim() ?? '');

afterEach(async () => {
  cleanup();
  await act(() => i18n.changeLanguage('de'));
});

describe('PlantStateLegendSection', () => {
  // raw names sort "drying, seedling, vegetative"; the translated labels sort differently per language
  const phases = ['vegetative', 'drying', 'seedling', 'curing', 'cloning'];

  it('sorts the translated German labels, not the stored names', async () => {
    await act(() => i18n.changeLanguage('de'));
    render(<PlantStateLegendSection phases={phases} />);
    expect(phaseLabels()).toEqual(['Aushärtung', 'Klonen', 'Sämling', 'Trocknung', 'Vegetativ']);
  });

  it('sorts the English labels in English, and keeps an unknown name as stored', async () => {
    await act(() => i18n.changeLanguage('en'));
    render(<PlantStateLegendSection phases={[...phases, 'Ärgerphase']} />);
    expect(phaseLabels()).toEqual(['Ärgerphase', 'Cloning', 'Curing', 'Drying', 'Seedling', 'Vegetative']);
    expect(screen.getByText('Drying')).toBeInTheDocument();
  });
});
