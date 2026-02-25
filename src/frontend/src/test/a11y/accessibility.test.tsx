import { waitFor } from '@testing-library/react';
import { describe, it, expect, beforeEach } from 'vitest';
import { axe } from 'vitest-axe';
import i18n from 'i18next';
import DashboardPage from '@/pages/DashboardPage';
import NotFoundPage from '@/pages/NotFoundPage';
import EmptyState from '@/components/common/EmptyState';
import ErrorDisplay from '@/components/common/ErrorDisplay';
import { renderWithProviders } from '../helpers';

describe('Accessibility (axe)', () => {
  beforeEach(() => {
    i18n.changeLanguage('de');
  });

  it('DashboardPage has no critical a11y violations', async () => {
    const { container } = renderWithProviders(<DashboardPage />);
    await waitFor(async () => {
      const results = await axe(container);
      expect(results.violations.filter((v) => v.impact === 'critical')).toEqual([]);
    });
  });

  it('NotFoundPage has no critical a11y violations', async () => {
    const { container } = renderWithProviders(<NotFoundPage />);
    await waitFor(async () => {
      const results = await axe(container);
      expect(results.violations.filter((v) => v.impact === 'critical')).toEqual([]);
    });
  });

  it('EmptyState has no critical a11y violations', async () => {
    const { container } = renderWithProviders(<EmptyState />);
    await waitFor(async () => {
      const results = await axe(container);
      expect(results.violations.filter((v) => v.impact === 'critical')).toEqual([]);
    });
  });

  it('ErrorDisplay has no critical a11y violations', async () => {
    const { container } = renderWithProviders(<ErrorDisplay error="Test error" />);
    await waitFor(async () => {
      const results = await axe(container);
      expect(results.violations.filter((v) => v.impact === 'critical')).toEqual([]);
    });
  });
});
