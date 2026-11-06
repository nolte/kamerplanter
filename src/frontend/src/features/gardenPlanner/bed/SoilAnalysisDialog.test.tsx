/**
 * "Record soil analysis" (REQ-053 GP-FR-122, WP 8.8): the dialog posts one `soil_analysis` care event with the values
 * as typed - each with unit and method - asks for the method a pH or EC cannot be read without, and passes axe.
 */
import { cleanup, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { http, HttpResponse } from 'msw';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { expectNoA11yViolations } from '@/test/a11y/expectNoA11yViolations';
import { authState, createTestStore, renderWithProviders, tenantState } from '@/test/helpers';
import { server } from '@/test/mocks/server';
import SoilAnalysisDialog from './SoilAnalysisDialog';

const BASE = '/api/v1/t/:tenant';

function renderDialog(onSaved = vi.fn()) {
  renderWithProviders(<SoilAnalysisDialog bedKey="loc_b03" bedName="Raised bed 3" onClose={vi.fn()} onSaved={onSaved} />, {
    store: createTestStore({ ...tenantState('grower'), ...authState() }),
  });
  return onSaved;
}

async function choose(user: ReturnType<typeof userEvent.setup>, testId: string, option: RegExp) {
  const field = screen.getByTestId(testId).closest('.MuiFormControl-root') as HTMLElement;
  await user.click(within(field).getByRole('combobox'));
  await user.click(await screen.findByRole('option', { name: option }));
}

afterEach(() => cleanup());

describe('SoilAnalysisDialog', () => {
  it('has no accessibility violations', async () => {
    renderDialog();
    await screen.findByTestId('soil-analysis-dialog');
    await expectNoA11yViolations(document.body, { minImpact: 'serious', minElements: 40 });
  });

  it('asks for the pH method instead of sending a value nobody can read', async () => {
    let posted = false;
    server.use(
      http.post(`${BASE}/care-events`, () => {
        posted = true;
        return HttpResponse.json({ key: 'ce_1' }, { status: 201 });
      }),
    );
    const user = userEvent.setup();
    renderDialog();
    await user.type(await screen.findByTestId('soil-analysis-value-1'), '6.4');
    await user.click(screen.getByTestId('soil-analysis-submit'));
    expect(await screen.findByText('Choose the measuring method - without it the value cannot be read.')).toBeInTheDocument();
    expect(posted).toBe(false);
  });

  it('posts one soil_analysis event with every value, its unit, method, source and depth', async () => {
    let body: Record<string, unknown> | null = null;
    server.use(
      http.post(`${BASE}/care-events`, async ({ request }) => {
        body = (await request.json()) as Record<string, unknown>;
        return HttpResponse.json({ key: 'ce_1', category: 'soil_analysis' }, { status: 201 });
      }),
    );
    const user = userEvent.setup();
    const onSaved = renderDialog();

    await user.type(await screen.findByTestId('soil-analysis-depth'), '30');
    await user.type(screen.getByTestId('soil-analysis-value-1'), '6,1');
    await choose(user, 'soil-analysis-method-1', /CaCl/);

    await user.click(screen.getByTestId('soil-analysis-add-row'));
    // The new row starts with the next parameter not yet in the analysis: EC.
    await user.type(screen.getByTestId('soil-analysis-value-2'), '0.4');
    await choose(user, 'soil-analysis-method-2', /1:5 extract/);

    await user.click(screen.getByTestId('soil-analysis-submit'));

    await waitFor(() => expect(onSaved).toHaveBeenCalledTimes(1));
    expect(body).toMatchObject({
      location_key: 'loc_b03',
      category: 'soil_analysis',
      measurements: [
        { parameter: 'ph', value: 6.1, unit: 'pH', ph_method: 'cacl2', source: 'lab', sample_depth_cm: 30 },
        { parameter: 'ec', value: 0.4, unit: 'mS/cm', ec_method: 'ratio_1_5', source: 'lab', sample_depth_cm: 30 },
      ],
    });
    expect(String(body!.summary)).toContain('Soil analysis (Lab)');
  });

  it('removes a value row again', async () => {
    const user = userEvent.setup();
    renderDialog();
    await user.click(await screen.findByTestId('soil-analysis-add-row'));
    expect(screen.getByTestId('soil-analysis-row-2')).toBeInTheDocument();
    await user.click(screen.getByRole('button', { name: 'Remove value 2' }));
    expect(screen.queryByTestId('soil-analysis-row-2')).toBeNull();
    // the last row cannot be removed
    expect(screen.queryByRole('button', { name: 'Remove value 1' })).toBeNull();
  });
});
