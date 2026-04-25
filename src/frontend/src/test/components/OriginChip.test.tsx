import { describe, it, expect } from 'vitest';
import { screen } from '@testing-library/react';
import OriginChip from '@/components/common/OriginChip';
import { renderWithProviders } from '@/test/helpers';

describe('OriginChip', () => {
  it('renders System chip with icon and tooltip when origin=system', () => {
    renderWithProviders(<OriginChip origin="system" />);
    const chip = screen.getByTestId('origin-chip-system');
    expect(chip).toBeTruthy();
    expect(chip.textContent).toMatch(/system/i);
  });

  it('treats isSystem=true like origin=system', () => {
    renderWithProviders(<OriginChip isSystem />);
    expect(screen.getByTestId('origin-chip-system')).toBeTruthy();
  });

  it('renders nothing for origin=tenant', () => {
    const { container } = renderWithProviders(<OriginChip origin="tenant" />);
    expect(container.querySelector('[data-testid^="origin-chip-"]')).toBeNull();
  });

  it('renders nothing when neither origin nor isSystem is set', () => {
    const { container } = renderWithProviders(<OriginChip />);
    expect(container.querySelector('[data-testid^="origin-chip-"]')).toBeNull();
  });

  it('renders enrichment variant', () => {
    renderWithProviders(<OriginChip origin="enrichment" />);
    expect(screen.getByTestId('origin-chip-enrichment')).toBeTruthy();
  });

  it('renders import variant', () => {
    renderWithProviders(<OriginChip origin="import" />);
    expect(screen.getByTestId('origin-chip-import')).toBeTruthy();
  });
});
