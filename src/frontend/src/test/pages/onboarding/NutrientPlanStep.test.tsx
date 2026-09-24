import { screen } from '@testing-library/react';
import { describe, it, expect, beforeEach, afterAll, vi } from 'vitest';
import i18n from 'i18next';
import NutrientPlanStep from '@/pages/onboarding/steps/NutrientPlanStep';
import type { NutrientPlanMatch, Species } from '@/api/types';
import { renderWithProviders } from '../../helpers';

/**
 * The wizard's nutrient-plan step after #1618: the backend now returns only plans
 * linked to one of the selected species, each naming the species it matched.
 */

const TOMATO = {
  key: 'solanum-lycopersicum',
  scientific_name: 'Solanum lycopersicum',
  common_names: ['Tomate'],
} as Species;
const BASIL = { key: 'ocimum-basilicum', scientific_name: 'Ocimum basilicum', common_names: [] } as unknown as Species;

function plan(overrides: Partial<NutrientPlanMatch> = {}): NutrientPlanMatch {
  return {
    plan_key: 'plan-tomato',
    name: 'Tomate — Plagron Terra + PK 13-14',
    description: 'Saisonplan',
    substrate_type: 'soil',
    species_keys: ['solanum-lycopersicum'],
    matched_species: ['solanum-lycopersicum'],
    fertilizer_count: 0,
    fertilizers: [],
    ...overrides,
  };
}

function render(plans: NutrientPlanMatch[], allSpecies: Species[] = [TOMATO, BASIL]) {
  return renderWithProviders(
    <NutrientPlanStep
      plans={plans}
      loading={false}
      favoriteNutrientPlanKeys={[]}
      onToggleFavoritePlan={vi.fn()}
      experienceLevel="intermediate"
      allSpecies={allSpecies}
    />,
  );
}

describe('NutrientPlanStep (#1618)', () => {
  beforeEach(() => {
    i18n.changeLanguage('de');
  });
  afterAll(() => {
    i18n.changeLanguage('en');
  });

  it('names the selected species each plan was matched for', () => {
    render([plan({ matched_species: ['solanum-lycopersicum', 'ocimum-basilicum'] })]);

    expect(screen.getByTestId('plan-matched-species-plan-tomato')).toHaveTextContent(
      'Passend für: Tomate, Ocimum basilicum',
    );
  });

  it('falls back to the key for a species the wizard catalogue does not hold', () => {
    render([plan({ matched_species: ['unknown-species'] })], []);

    expect(screen.getByTestId('plan-matched-species-plan-tomato')).toHaveTextContent('unknown-species');
  });

  it('explains why no plan is offered when nothing matches', () => {
    render([]);

    expect(screen.getByText(i18n.t('pages.onboarding.nutrientPlans.noPlans'))).toBeInTheDocument();
    expect(screen.getByText(i18n.t('pages.onboarding.nutrientPlans.noPlansDetail'))).toBeInTheDocument();
    expect(i18n.t('pages.onboarding.nutrientPlans.noPlansDetail')).toMatch(/Pflanzenarten/);
  });
});
