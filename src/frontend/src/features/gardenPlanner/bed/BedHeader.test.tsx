/**
 * The head of the bed view (REQ-053 GP-FR-047, #2487): the drainage of the soil profile is shown with its
 * label, and left out while it is unknown.
 */
import { cleanup, screen, within } from '@testing-library/react';
import { afterEach, describe, expect, it } from 'vitest';
import { expectNoA11yViolations } from '@/test/a11y/expectNoA11yViolations';
import { renderWithProviders } from '@/test/helpers';
import BedHeader from './BedHeader';
import { bedSummary } from './bedTestKit';
import type { BedSummary } from './types';

afterEach(() => cleanup());

function renderHeader(summary: BedSummary) {
  return renderWithProviders(
    <BedHeader
      summary={summary}
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
