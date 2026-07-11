import { describe, it, expect, vi, afterEach } from 'vitest';
import { screen, waitFor, cleanup } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { renderWithProviders } from '@/test/helpers';
import type { AiResponse } from '@/api/types';

vi.mock('@/api', () => ({
  aiApi: {
    explain: vi.fn(),
  },
}));

import { aiApi } from '@/api';
import WhyButton from '@/components/ai/WhyButton';
import WhyDrawer from '@/components/ai/WhyDrawer';

const explain = vi.mocked(aiApi.explain);

const ANSWER: AiResponse = {
  answer_text: 'Because the substrate has dried below the target moisture band.',
  sources: [],
  language: 'de',
  language_mismatch_warning: false,
  uses_tenant_data: true,
  uses_cloud_provider: false,
  confidence: 'high',
  model_name: 'gemma3:12b',
  provider_type: 'ollama',
};

describe('WhyButton', () => {
  // No mock-resetting beforeEach on purpose: under vitest v4 a
  // mockReset/mockClear paired with a rejecting mock surfaces the rejection as
  // unhandled even when the component catches it. Each test sets its own
  // implementation explicitly, so history carry-over is harmless here.
  afterEach(() => cleanup());

  it('renders an accessible icon button', () => {
    renderWithProviders(
      <WhyButton request={{ subject_type: 'reminder', subject_key: 'r-1', question_template_id: 'care_reminder_watering' }} />,
    );
    expect(screen.getByTestId('why-button')).toBeTruthy();
  });

  it('opens the drawer and loads the explanation on click', async () => {
    explain.mockResolvedValue(ANSWER);
    const user = userEvent.setup();
    renderWithProviders(
      <WhyButton request={{ subject_type: 'reminder', subject_key: 'r-1', question_template_id: 'care_reminder_watering' }} />,
    );

    await user.click(screen.getByTestId('why-button'));

    expect(screen.getByTestId('why-drawer')).toBeTruthy();
    await waitFor(() => expect(explain).toHaveBeenCalled());
    expect(await screen.findByText(/substrate has dried/)).toBeTruthy();
    // Rendered through the mandatory AIResponse wrapper.
    expect(screen.getByTestId('ai-badge')).toBeTruthy();
  });

  it('surfaces the error message when the explanation fails', async () => {
    // Exercised through WhyDrawer directly (already open): the error handling
    // lives there, and this avoids the drawer open-transition timing of a click.
    explain.mockRejectedValue(new Error('down'));
    renderWithProviders(
      <WhyDrawer
        open
        onClose={() => undefined}
        request={{ subject_type: 'task', subject_key: 't-1', question_template_id: 'task_explain' }}
      />,
    );

    expect(await screen.findByTestId('why-error')).toBeTruthy();
    // No AI badge on the error path (nothing was answered).
    expect(screen.queryByTestId('ai-badge')).toBeNull();
  });
});
