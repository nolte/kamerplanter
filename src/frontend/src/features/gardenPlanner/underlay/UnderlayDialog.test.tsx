/**
 * The underlay dialog (REQ-053 GP-FR-033, WP 7.15): pick a picture, calibrate it with two points and a known
 * distance (400 px apart + 4.0 m = 100 px/m), place and fade it, save, remove. Viewers see it read-only.
 */
import { cleanup, fireEvent, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { http, HttpResponse } from 'msw';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { expectNoA11yViolations } from '@/test/a11y/expectNoA11yViolations';
import { authState, createTestStore, renderWithProviders, tenantState } from '@/test/helpers';
import { server } from '@/test/mocks/server';
import type { PlanUnderlay } from '../model/types';
import UnderlayDialog from './UnderlayDialog';

afterEach(() => cleanup());

const BASE = '/api/v1/t/:tenant';
const STORED: PlanUnderlay = {
  attachment_key: 'att_stored',
  calibration: { p1_px: [100, 200], p2_px: [500, 200], distance_m: 4 },
  origin: [1, 5],
  rotation_deg: 15,
  opacity: 0.4,
};

function renderDialog(
  underlay: PlanUnderlay | null,
  role: 'viewer' | 'grower' = 'grower',
  handlers: { onSaved?: (next: PlanUnderlay | null) => void; onClose?: () => void } = {},
) {
  const onSaved = handlers.onSaved ?? vi.fn();
  const onClose = handlers.onClose ?? vi.fn();
  const view = renderWithProviders(
    <UnderlayDialog open siteKey="site_1" underlay={underlay} onSaved={onSaved} onClose={onClose} />,
    { store: createTestStore({ ...tenantState(role, []), ...authState() }) },
  );
  return { ...view, onSaved, onClose };
}

const PNG = new File([new Uint8Array([137, 80, 78, 71])], 'plan.png', { type: 'image/png' });

/** jsdom never decodes an image: report its natural size the way a browser's `load` would. */
function loadPicture(width = 800, height = 400) {
  const image = screen.getByRole('img', { name: /Unterlage|Underlay/ });
  Object.defineProperty(image, 'naturalWidth', { value: width, configurable: true });
  Object.defineProperty(image, 'naturalHeight', { value: height, configurable: true });
  fireEvent.load(image);
  return image;
}

async function fillCalibration(user: ReturnType<typeof userEvent.setup>, values: Record<string, string>) {
  for (const [id, value] of Object.entries(values)) {
    const input = screen.getByTestId(`underlay-${id}`);
    await user.clear(input);
    await user.type(input, value);
  }
}

describe('calibration', () => {
  it('names the scale of two points 400 px apart and 4.0 m as 100 pixels per metre', async () => {
    const user = userEvent.setup();
    renderDialog(null);
    await user.upload(screen.getByTestId('underlay-file'), PNG);
    await fillCalibration(user, { p1x: '100', p1y: '200', p2x: '500', p2y: '200', distance: '4' });

    expect(screen.getByTestId('underlay-scale')).toHaveTextContent('100');
  });

  it('keeps Save off until the picture, two different points and a distance are there', async () => {
    const user = userEvent.setup();
    renderDialog(null);
    expect(screen.getByTestId('underlay-save')).toBeDisabled();
    await user.upload(screen.getByTestId('underlay-file'), PNG);
    expect(screen.getByTestId('underlay-save')).toBeDisabled();
    await fillCalibration(user, { p1x: '100', p1y: '200', p2x: '100', p2y: '200', distance: '4' });
    expect(screen.getByTestId('underlay-save')).toBeDisabled();
    await fillCalibration(user, { p2x: '500' });
    expect(screen.getByTestId('underlay-save')).toBeEnabled();
  });

  it('refuses a non-finite or negative distance', async () => {
    const user = userEvent.setup();
    renderDialog(null);
    await user.upload(screen.getByTestId('underlay-file'), PNG);
    await fillCalibration(user, { p1x: '0', p1y: '0', p2x: '400', p2y: '0', distance: '-3' });
    expect(screen.getByTestId('underlay-save')).toBeDisabled();
    await fillCalibration(user, { distance: 'Infinity' });
    expect(screen.getByTestId('underlay-save')).toBeDisabled();
  });

  it('takes the two points from two clicks on the picture', async () => {
    const user = userEvent.setup();
    renderDialog(null);
    await user.upload(screen.getByTestId('underlay-file'), PNG);
    const image = loadPicture(800, 400);
    // displayed at half size: a click at (50, 25) inside the box is pixel (100, 50) of the picture
    vi.spyOn(image, 'getBoundingClientRect').mockReturnValue({
      left: 0, top: 0, width: 400, height: 200, right: 400, bottom: 200, x: 0, y: 0, toJSON: () => ({}),
    });
    const picture = screen.getByTestId('underlay-picture');
    fireEvent.click(picture, { clientX: 50, clientY: 25 });
    fireEvent.click(picture, { clientX: 250, clientY: 25 });

    expect(screen.getByTestId('underlay-p1x')).toHaveValue('100');
    expect(screen.getByTestId('underlay-p1y')).toHaveValue('50');
    expect(screen.getByTestId('underlay-p2x')).toHaveValue('500');
    expect(screen.getByTestId('underlay-p2y')).toHaveValue('50');
  });
});

describe('save and remove', () => {
  it('uploads the picture as an underlay attachment, then stores the calibration with the returned key', async () => {
    const user = userEvent.setup();
    const form: FormDataEntryValue[] = [];
    let put: Record<string, unknown> = {};
    server.use(
      http.post(`${BASE}/attachments`, async ({ request }) => {
        const body = await request.formData();
        form.push(body.get('category') as string);
        return HttpResponse.json({ attachment_id: 'att_new' }, { status: 201 });
      }),
      http.put(`${BASE}/sites/site_1/plan/underlay`, async ({ request }) => {
        put = (await request.json()) as Record<string, unknown>;
        return HttpResponse.json(put);
      }),
    );
    const { onSaved, onClose } = renderDialog(null);
    await user.upload(screen.getByTestId('underlay-file'), PNG);
    await fillCalibration(user, { p1x: '100', p1y: '200', p2x: '500', p2y: '200', distance: '4' });
    await user.click(screen.getByTestId('underlay-save'));

    await waitFor(() => expect(onSaved).toHaveBeenCalled());
    expect(form).toEqual(['garden_plan_underlay']);
    expect(put).toMatchObject({
      attachment_key: 'att_new',
      calibration: { p1_px: [100, 200], p2_px: [500, 200], distance_m: 4 },
      origin: [0, 0],
      rotation_deg: 0,
      opacity: 0.5,
    });
    expect(onClose).toHaveBeenCalled();
  });

  it('shows the server refusal and keeps the dialog open', async () => {
    const user = userEvent.setup();
    server.use(
      http.post(`${BASE}/attachments`, () => HttpResponse.json({ attachment_id: 'att_new' }, { status: 201 })),
      http.put(`${BASE}/sites/site_1/plan/underlay`, () =>
        HttpResponse.json(
          { error_code: 'plan.required', message: 'x', details: [{ field: 'plan', code: 'plan.required' }] },
          { status: 422 },
        ),
      ),
    );
    const { onSaved, onClose } = renderDialog(null);
    await user.upload(screen.getByTestId('underlay-file'), PNG);
    await fillCalibration(user, { p1x: '100', p1y: '200', p2x: '500', p2y: '200', distance: '4' });
    await user.click(screen.getByTestId('underlay-save'));

    expect(await screen.findByTestId('underlay-error')).toBeInTheDocument();
    expect(onSaved).not.toHaveBeenCalled();
    expect(onClose).not.toHaveBeenCalled();
  });

  it('removes a stored underlay', async () => {
    const user = userEvent.setup();
    let deleted = false;
    server.use(
      http.get(`${BASE}/attachments/att_stored`, () => new HttpResponse(new Blob(['x']), { status: 200 })),
      http.delete(`${BASE}/sites/site_1/plan/underlay`, () => {
        deleted = true;
        return new HttpResponse(null, { status: 204 });
      }),
    );
    const { onSaved } = renderDialog(STORED);
    await user.click(screen.getByTestId('underlay-remove'));
    // destructive (picture and calibration): nothing is sent before the question is answered
    expect(deleted).toBe(false);
    await user.click(screen.getByTestId('confirm-dialog-confirm'));

    await waitFor(() => expect(onSaved).toHaveBeenCalledWith(null));
    expect(deleted).toBe(true);
  });

  it('keeps the underlay when the removal is not confirmed', async () => {
    const user = userEvent.setup();
    let deleted = false;
    server.use(
      http.get(`${BASE}/attachments/att_stored`, () => new HttpResponse(new Blob(['x']), { status: 200 })),
      http.delete(`${BASE}/sites/site_1/plan/underlay`, () => {
        deleted = true;
        return new HttpResponse(null, { status: 204 });
      }),
    );
    const { onSaved } = renderDialog(STORED);
    await user.click(screen.getByTestId('underlay-remove'));
    await user.click(screen.getByTestId('confirm-dialog-cancel'));

    expect(deleted).toBe(false);
    expect(onSaved).not.toHaveBeenCalled();
  });

  it('shows a stored calibration and re-saves it without uploading again', async () => {
    const user = userEvent.setup();
    let uploads = 0;
    let put: Record<string, unknown> = {};
    server.use(
      http.get(`${BASE}/attachments/att_stored`, () => new HttpResponse(new Blob(['x']), { status: 200 })),
      http.post(`${BASE}/attachments`, () => {
        uploads += 1;
        return HttpResponse.json({ attachment_id: 'x' }, { status: 201 });
      }),
      http.put(`${BASE}/sites/site_1/plan/underlay`, async ({ request }) => {
        put = (await request.json()) as Record<string, unknown>;
        return HttpResponse.json(put);
      }),
    );
    const { onSaved } = renderDialog(STORED);
    expect(screen.getByTestId('underlay-scale')).toHaveTextContent('100');
    expect(screen.getByTestId('underlay-rotation')).toHaveValue('15');
    await user.click(screen.getByTestId('underlay-save'));

    await waitFor(() => expect(onSaved).toHaveBeenCalled());
    expect(uploads).toBe(0);
    expect(put).toMatchObject({ attachment_key: 'att_stored', rotation_deg: 15, opacity: 0.4 });
  });
});

describe('a viewer', () => {
  it('sees the calibration and can neither change nor remove it', () => {
    server.use(http.get(`${BASE}/attachments/att_stored`, () => new HttpResponse(new Blob(['x']), { status: 200 })));
    renderDialog(STORED, 'viewer');
    expect(screen.getByTestId('underlay-scale')).toHaveTextContent('100');
    expect(screen.queryByTestId('underlay-save')).toBeNull();
    expect(screen.queryByTestId('underlay-remove')).toBeNull();
    expect(screen.queryByTestId('underlay-file')).toBeNull();
  });
});

describe('accessibility', () => {
  it('has no axe violations, empty or calibrated', async () => {
    server.use(http.get(`${BASE}/attachments/att_stored`, () => new HttpResponse(new Blob(['x']), { status: 200 })));
    const empty = renderDialog(null);
    await expectNoA11yViolations(document.body);
    empty.unmount();
    renderDialog(STORED);
    await waitFor(() => expect(screen.getByTestId('underlay-picture')).toBeInTheDocument());
    await expectNoA11yViolations(document.body);
  });
});
