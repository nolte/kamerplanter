import { describe, it, expect, vi } from 'vitest';
import { screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { renderWithProviders } from '@/test/helpers';
import SymptomPicker from '@/components/diagnosis/SymptomPicker';
import type { DiagnosisSymptom } from '@/api/types';

function makeSymptom(overrides: Partial<DiagnosisSymptom> = {}): DiagnosisSymptom {
  return {
    slug: 'leaf_spots',
    category: 'leaf_shape_change',
    label: 'Spots on the leaves',
    common_causes_hint: 'Fungal disease or nutrient deficiency.',
    applicable_phases: ['vegetative'],
    ...overrides,
  };
}

describe('SymptomPicker', () => {
  it('renders symptoms grouped by category', () => {
    renderWithProviders(
      <SymptomPicker
        symptoms={[
          makeSymptom(),
          makeSymptom({ slug: 'small_flying_insects', category: 'pest_visible', label: 'Small flying insects' }),
        ]}
        selected={[]}
        onToggle={vi.fn()}
      />,
    );

    expect(screen.getByTestId('symptom-picker')).toBeTruthy();
    expect(screen.getByTestId('symptom-leaf_spots')).toBeTruthy();
    expect(screen.getByTestId('symptom-small_flying_insects')).toBeTruthy();
  });

  it('reflects the selected state', () => {
    renderWithProviders(
      <SymptomPicker symptoms={[makeSymptom()]} selected={['leaf_spots']} onToggle={vi.fn()} />,
    );
    const checkbox = screen.getByTestId('symptom-leaf_spots').querySelector('input');
    expect(checkbox?.checked).toBe(true);
  });

  it('calls onToggle when a symptom is clicked', async () => {
    const onToggle = vi.fn();
    const user = userEvent.setup();
    renderWithProviders(<SymptomPicker symptoms={[makeSymptom()]} selected={[]} onToggle={onToggle} />);

    await user.click(screen.getByLabelText('Spots on the leaves'));
    expect(onToggle).toHaveBeenCalledWith('leaf_spots');
  });
});
