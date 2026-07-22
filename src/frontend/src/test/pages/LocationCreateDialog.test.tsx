import { screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { http, HttpResponse } from 'msw';
import i18n from 'i18next';
import LocationCreateDialog from '@/pages/standorte/LocationCreateDialog';
import { renderWithProviders } from '../helpers';
import { server } from '../mocks/server';

describe('LocationCreateDialog', () => {
  beforeEach(() => {
    i18n.changeLanguage('de');
  });

  it('renders the create title when no parent is given', async () => {
    renderWithProviders(
      <LocationCreateDialog siteKey="site-1" open onClose={() => {}} onCreated={() => {}} />,
    );
    expect(await screen.findByTestId('location-create-dialog')).toBeTruthy();
    expect(screen.getByText('Bereich erstellen')).toBeTruthy();
  });

  it('renders the sublocation title when a parent location is given', async () => {
    renderWithProviders(
      <LocationCreateDialog
        siteKey="site-1"
        parentLocationKey="loc-1"
        open
        onClose={() => {}}
        onCreated={() => {}}
      />,
    );
    // dialogTitle switches to addSublocation when parentLocationKey is set
    expect(await screen.findByTestId('location-create-dialog')).toBeTruthy();
    expect(screen.getByText('Unterlocation hinzufügen')).toBeTruthy();
  });

  it('reveals the lights time row only for light types that use it', async () => {
    const user = userEvent.setup();
    renderWithProviders(
      <LocationCreateDialog siteKey="site-1" open onClose={() => {}} onCreated={() => {}} />,
    );

    // Default light_type is "natural" → lights row is shown
    await screen.findByTestId('location-create-dialog');
    expect(screen.getByLabelText('Licht Ein')).toBeTruthy();
    // use_dynamic_sunrise only renders for natural/mixed
    expect(screen.getByTestId('form-field-use_dynamic_sunrise')).toBeTruthy();

    // Switch to an artificial light type that still shows the lights row but not sunrise
    const lightTypeSelect = within(screen.getByTestId('form-field-light_type')).getByRole('combobox');
    await user.click(lightTypeSelect);
    const ledOption = await screen.findByRole('option', { name: 'LED' });
    await user.click(ledOption);

    await waitFor(() => {
      expect(screen.queryByTestId('form-field-use_dynamic_sunrise')).toBeNull();
    });
    expect(screen.getByLabelText('Licht Ein')).toBeTruthy();
  });

  it('submits a valid location and calls onCreated', async () => {
    const user = userEvent.setup();
    const onCreated = vi.fn();
    renderWithProviders(
      <LocationCreateDialog siteKey="site-1" open onClose={() => {}} onCreated={onCreated} />,
    );

    const nameField = within(await screen.findByTestId('form-field-name')).getByRole('textbox');
    await user.type(nameField, 'Bed 1');
    await user.click(screen.getByTestId('form-submit-button'));

    await waitFor(() => {
      expect(onCreated).toHaveBeenCalledOnce();
    });
  });

  it('surfaces a server error without calling onCreated', async () => {
    server.use(
      http.post('/api/v1/locations', () =>
        HttpResponse.json(
          { error_id: 'e', error_code: 'CONFLICT', message: 'dup', details: [], timestamp: '', path: '', method: '' },
          { status: 409 },
        ),
      ),
      http.post('/api/v1/t/:tenant/locations', () =>
        HttpResponse.json(
          { error_id: 'e', error_code: 'CONFLICT', message: 'dup', details: [], timestamp: '', path: '', method: '' },
          { status: 409 },
        ),
      ),
    );
    const user = userEvent.setup();
    const onCreated = vi.fn();
    renderWithProviders(
      <LocationCreateDialog siteKey="site-1" open onClose={() => {}} onCreated={onCreated} />,
    );

    const nameField = within(await screen.findByTestId('form-field-name')).getByRole('textbox');
    await user.type(nameField, 'Bed 1');
    await user.click(screen.getByTestId('form-submit-button'));

    await waitFor(() => {
      expect(screen.getByTestId('form-submit-button')).not.toBeDisabled();
    });
    expect(onCreated).not.toHaveBeenCalled();
  });

  it('calls onClose when cancelled', async () => {
    const user = userEvent.setup();
    const onClose = vi.fn();
    renderWithProviders(
      <LocationCreateDialog siteKey="site-1" open onClose={onClose} onCreated={() => {}} />,
    );
    await user.click(await screen.findByTestId('form-cancel-button'));
    expect(onClose).toHaveBeenCalledOnce();
  });

  // ── Issue #706: Location frost-exposure override tests ──────────────

  it('renders the frost exposure field', async () => {
    renderWithProviders(
      <LocationCreateDialog siteKey="site-1" open onClose={() => {}} onCreated={() => {}} />,
    );
    await screen.findByTestId('location-create-dialog');

    const frostExposureField = screen.getByTestId('form-field-frost_exposure');
    expect(frostExposureField).toBeTruthy();
  });

  it('defaults to "inherit" for frost exposure', async () => {
    renderWithProviders(
      <LocationCreateDialog siteKey="site-1" open onClose={() => {}} onCreated={() => {}} />,
    );
    await screen.findByTestId('location-create-dialog');

    // The frost exposure field should be rendered
    const frostExposureField = screen.getByTestId('form-field-frost_exposure');
    expect(frostExposureField).toBeTruthy();
  });

  it('maps frost_exposure "exposed" to frost_exposed=true on submit', async () => {
    const user = userEvent.setup();
    const onCreated = vi.fn();
    let capturedPayload: Record<string, unknown> | null = null;

    server.use(
      http.post('/api/v1/locations', async ({ request }) => {
        capturedPayload = (await request.json()) as Record<string, unknown>;
        return HttpResponse.json({
          _key: 'loc-1',
          name: 'Bed 1',
          site_key: 'site-1',
          area_m2: 0,
          frost_exposed: true,
        });
      }),
      http.post('/api/v1/t/:tenant/locations', async ({ request }) => {
        capturedPayload = (await request.json()) as Record<string, unknown>;
        return HttpResponse.json({
          _key: 'loc-1',
          name: 'Bed 1',
          site_key: 'site-1',
          area_m2: 0,
          frost_exposed: true,
        });
      }),
    );

    renderWithProviders(
      <LocationCreateDialog siteKey="site-1" open onClose={() => {}} onCreated={onCreated} />,
    );

    const nameField = within(await screen.findByTestId('form-field-name')).getByRole('textbox');
    await user.type(nameField, 'Bed 1');

    // Change frost_exposure to "exposed"
    const frostExposureSelect = within(screen.getByTestId('form-field-frost_exposure')).getByRole('combobox');
    await user.click(frostExposureSelect);
    const exposedOption = await screen.findByRole('option', { name: /Außenbereich/ });
    await user.click(exposedOption);

    await user.click(screen.getByTestId('form-submit-button'));

    await waitFor(() => {
      expect(onCreated).toHaveBeenCalledOnce();
      expect(capturedPayload?.frost_exposed).toBe(true);
    });
  });

  it('maps frost_exposure "protected" to frost_exposed=false on submit', async () => {
    const user = userEvent.setup();
    const onCreated = vi.fn();
    let capturedPayload: Record<string, unknown> | null = null;

    server.use(
      http.post('/api/v1/locations', async ({ request }) => {
        capturedPayload = (await request.json()) as Record<string, unknown>;
        return HttpResponse.json({
          _key: 'loc-1',
          name: 'Bed 1',
          site_key: 'site-1',
          area_m2: 0,
          frost_exposed: false,
        });
      }),
      http.post('/api/v1/t/:tenant/locations', async ({ request }) => {
        capturedPayload = (await request.json()) as Record<string, unknown>;
        return HttpResponse.json({
          _key: 'loc-1',
          name: 'Bed 1',
          site_key: 'site-1',
          area_m2: 0,
          frost_exposed: false,
        });
      }),
    );

    renderWithProviders(
      <LocationCreateDialog siteKey="site-1" open onClose={() => {}} onCreated={onCreated} />,
    );

    const nameField = within(await screen.findByTestId('form-field-name')).getByRole('textbox');
    await user.type(nameField, 'Bed 1');

    // Change frost_exposure to "protected"
    const frostExposureSelect = within(screen.getByTestId('form-field-frost_exposure')).getByRole('combobox');
    await user.click(frostExposureSelect);
    const protectedOption = await screen.findByRole('option', { name: /geschützt/ });
    await user.click(protectedOption);

    await user.click(screen.getByTestId('form-submit-button'));

    await waitFor(() => {
      expect(onCreated).toHaveBeenCalledOnce();
      expect(capturedPayload?.frost_exposed).toBe(false);
    });
  });

  it('maps frost_exposure "inherit" to frost_exposed=null on submit', async () => {
    const user = userEvent.setup();
    const onCreated = vi.fn();
    let capturedPayload: Record<string, unknown> | null = null;

    server.use(
      http.post('/api/v1/locations', async ({ request }) => {
        capturedPayload = (await request.json()) as Record<string, unknown>;
        return HttpResponse.json({
          _key: 'loc-1',
          name: 'Bed 1',
          site_key: 'site-1',
          area_m2: 0,
          frost_exposed: null,
        });
      }),
      http.post('/api/v1/t/:tenant/locations', async ({ request }) => {
        capturedPayload = (await request.json()) as Record<string, unknown>;
        return HttpResponse.json({
          _key: 'loc-1',
          name: 'Bed 1',
          site_key: 'site-1',
          area_m2: 0,
          frost_exposed: null,
        });
      }),
    );

    renderWithProviders(
      <LocationCreateDialog siteKey="site-1" open onClose={() => {}} onCreated={onCreated} />,
    );

    const nameField = within(await screen.findByTestId('form-field-name')).getByRole('textbox');
    await user.type(nameField, 'Bed 1');

    // Keep frost_exposure as "inherit" (default)
    await user.click(screen.getByTestId('form-submit-button'));

    await waitFor(() => {
      expect(onCreated).toHaveBeenCalledOnce();
      expect(capturedPayload?.frost_exposed).toBeNull();
    });
  });
});
