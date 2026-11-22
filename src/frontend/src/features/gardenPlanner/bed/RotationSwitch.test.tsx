/**
 * "Crop rotation for this bed" (REQ-053 GP-FR-137, WP 8.14): the bed's switch and the permanent-crop flag in the soil
 * tab, written through `PATCH /locations/{key}`, and the 422 for both at once shown in words.
 */
import { cleanup, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { http, HttpResponse, type JsonBodyType } from 'msw';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { expectNoA11yViolations } from '@/test/a11y/expectNoA11yViolations';
import { renderWithProviders } from '@/test/helpers';
import { server } from '@/test/mocks/server';
import RotationSwitch from './RotationSwitch';

const BASE = '/api/v1/t/:tenant';

function usePatch(response: { status: number; body: JsonBodyType } = { status: 200, body: { key: 'loc_b03' } }) {
  const bodies: unknown[] = [];
  server.use(
    http.patch(`${BASE}/locations/:key`, async ({ request }) => {
      bodies.push(await request.json());
      return HttpResponse.json(response.body, { status: response.status });
    }),
  );
  return bodies;
}

function renderSwitch(props: Partial<Parameters<typeof RotationSwitch>[0]> = {}) {
  const onSaved = vi.fn();
  const view = renderWithProviders(
    <RotationSwitch
      bedKey="loc_b03"
      rotationEnabled={null}
      rotationExempt={false}
      canEdit
      onSaved={onSaved}
      {...props}
    />,
  );
  return { onSaved, ...view };
}

afterEach(() => cleanup());

describe('RotationSwitch', () => {
  it('shows the stored state: default of the type, on, off - and the permanent-crop flag', () => {
    const { unmount } = renderSwitch({ rotationEnabled: null });
    expect(screen.getByRole('radio', { name: 'Default of the bed type' })).toBeChecked();
    unmount();
    const second = renderSwitch({ rotationEnabled: true });
    expect(screen.getByRole('radio', { name: 'Switched on' })).toBeChecked();
    second.unmount();
    renderSwitch({ rotationEnabled: false, rotationExempt: true });
    expect(screen.getByRole('radio', { name: 'Switched off' })).toBeChecked();
    expect(screen.getByRole('switch', { name: /Permanent crop/ })).toBeChecked();
  });

  it('switches the check on with a PATCH of exactly that key and reloads the summary', async () => {
    const bodies = usePatch();
    const user = userEvent.setup();
    const { onSaved } = renderSwitch();

    await user.click(screen.getByRole('radio', { name: 'Switched on' }));

    await waitFor(() => expect(onSaved).toHaveBeenCalledTimes(1));
    expect(bodies).toEqual([{ rotation_enabled: true }]);
  });

  it('sends null to return a bed to the default of its type', async () => {
    const bodies = usePatch();
    const user = userEvent.setup();
    renderSwitch({ rotationEnabled: false });

    await user.click(screen.getByRole('radio', { name: 'Default of the bed type' }));

    await waitFor(() => expect(bodies).toEqual([{ rotation_enabled: null }]));
  });

  it('marks a permanent crop with its own key only', async () => {
    const bodies = usePatch();
    const user = userEvent.setup();
    renderSwitch();

    await user.click(screen.getByRole('switch', { name: /Permanent crop/ }));

    await waitFor(() => expect(bodies).toEqual([{ rotation_exempt: true }]));
  });

  it('shows the refusal in words when the bed is exempt and switched on (422 patch.rotation_exempt_and_enabled)', async () => {
    const bodies = usePatch({
      status: 422,
      body: {
        error_id: 'err_1',
        error_code: 'patch.rotation_exempt_and_enabled',
        message: 'A bed exempt from crop rotation cannot have the rotation check switched on.',
        details: [
          {
            field: 'rotation_enabled',
            reason: 'A bed exempt from crop rotation cannot have the rotation check switched on.',
            code: 'patch.rotation_exempt_and_enabled',
          },
        ],
        timestamp: '',
        path: '',
        method: 'PATCH',
      },
    });
    const user = userEvent.setup();
    const { onSaved } = renderSwitch({ rotationEnabled: true, rotationExempt: false });

    await user.click(screen.getByRole('switch', { name: /Permanent crop/ }));

    expect(await screen.findByTestId('rotation-switch-refusal')).toHaveTextContent(
      'A permanent crop cannot have the rotation check switched on.',
    );
    expect(bodies).toEqual([{ rotation_exempt: true }]);
    expect(onSaved).not.toHaveBeenCalled();
    // nothing changed on screen: the stored state still stands
    expect(screen.getByRole('radio', { name: 'Switched on' })).toBeChecked();
    expect(screen.getByRole('switch', { name: /Permanent crop/ })).not.toBeChecked();
  });

  it('is read-only for a viewer', () => {
    renderSwitch({ canEdit: false, rotationEnabled: true });

    expect(screen.getByRole('radio', { name: 'Switched off' })).toBeDisabled();
    expect(screen.getByRole('switch', { name: /Permanent crop/ })).toBeDisabled();
    expect(screen.getByTestId('rotation-switch')).toHaveTextContent('You can look at it but not change it.');
  });

  it('has no critical accessibility violation', async () => {
    const { container } = renderSwitch();
    await expectNoA11yViolations(container);
  });
});
