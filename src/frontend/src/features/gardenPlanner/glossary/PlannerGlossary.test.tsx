/**
 * The glossary of the garden planner (REQ-053 GP-UX-011, UI-NFR-011): every term is named, reachable by
 * keyboard and opens its explanation; every term has an explanation in German and English.
 */
import { cleanup, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, describe, expect, it } from 'vitest';
import i18n from '@/i18n/i18n';
import { expectNoA11yViolations } from '@/test/a11y/expectNoA11yViolations';
import { renderWithProviders } from '@/test/helpers';
import PlannerGlossary, { PLANNER_GLOSSARY_TERMS, PlannerTermField } from './PlannerGlossary';

afterEach(() => cleanup());

describe('PlannerGlossary', () => {
  it('names each term and explains it once the trigger gets the keyboard focus', async () => {
    const user = userEvent.setup();
    renderWithProviders(<PlannerGlossary id="test" terms={['fruchtfolge', 'zehrerklassen']} />);

    const glossary = screen.getByRole('group', { name: 'Terms explained' });
    expect(glossary).toHaveTextContent('Crop rotation');
    expect(glossary).toHaveTextContent('Heavy, medium, light feeders');

    await user.tab();
    const rotation = screen.getByRole('button', { name: /^Crop rotation — a different plant family/ });
    expect(rotation).toHaveFocus();
    const tooltip = await screen.findByRole('tooltip');
    expect(tooltip).toHaveTextContent('Crop rotation — a different plant family in the bed each year');
    // The default experience level is beginner: the tooltip carries the beginner tip.
    expect(tooltip).toHaveTextContent('A crop rotation hint is advice, not a ban.');

    await user.tab();
    expect(screen.getByRole('button', { name: /^Heavy, medium and light feeders/ })).toHaveFocus();
  });

  it('puts the term trigger next to a field without taking the field label', () => {
    renderWithProviders(
      <PlannerTermField term="pflanzabstand">
        <label>
          Plant spacing
          <input />
        </label>
      </PlannerTermField>,
    );
    expect(screen.getByRole('textbox', { name: 'Plant spacing' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /^Plant spacing — distance from plant to plant/ })).toBeInTheDocument();
  });

  it('has no accessibility violations', async () => {
    renderWithProviders(<PlannerGlossary id="a11y" terms={PLANNER_GLOSSARY_TERMS} />);
    await expectNoA11yViolations(screen.getByTestId('planner-glossary-a11y'));
  });

  it.each(['de', 'en'] as const)('explains every planner term in %s (short, long, beginner tip, label)', (lng) => {
    const t = i18n.getFixedT(lng);
    for (const term of PLANNER_GLOSSARY_TERMS) {
      for (const field of ['short', 'long', 'beginnerTip'] as const) {
        const key = `glossary.${term}.${field}`;
        expect(i18n.exists(key, { lng }), `${lng}: ${key}`).toBe(true);
        expect(t(key).trim().length, `${lng}: ${key}`).toBeGreaterThan(0);
      }
      expect(i18n.exists(`pages.gardenPlan.glossary.terms.${term}`, { lng }), `${lng}: label of ${term}`).toBe(true);
    }
  });
});
