import { screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { http, HttpResponse } from 'msw';
import i18n from 'i18next';
import SiteCreateDialog from '@/pages/standorte/SiteCreateDialog';
import { renderWithProviders, createStoreWithExpertise } from '../helpers';
import { server } from '../mocks/server';

describe('SiteCreateDialog', () => {
  beforeEach(() => {
    i18n.changeLanguage('de');
  });

  it('renders the dialog with its title when open', async () => {
    renderWithProviders(<SiteCreateDialog open onClose={() => {}} onCreated={() => {}} />, {
      store: createStoreWithExpertise('expert'),
    });
    expect(await screen.findByTestId('site-create-dialog')).toBeTruthy();
    expect(screen.getByRole('dialog')).toBeTruthy();
  });

  it('shows only the name field for a beginner', async () => {
    renderWithProviders(<SiteCreateDialog open onClose={() => {}} onCreated={() => {}} />, {
      store: createStoreWithExpertise('beginner'),
    });
    await screen.findByTestId('site-create-dialog');
    expect(screen.getByTestId('form-field-name')).toBeTruthy();
    expect(screen.queryByTestId('form-field-timezone')).toBeNull();
    expect(screen.queryByTestId('form-field-climate_zone')).toBeNull();
  });

  it('exposes intermediate and expert fields for an expert', async () => {
    renderWithProviders(<SiteCreateDialog open onClose={() => {}} onCreated={() => {}} />, {
      store: createStoreWithExpertise('expert'),
    });
    expect(await screen.findByTestId('form-field-climate_zone')).toBeTruthy();
    expect(screen.getByTestId('form-field-total_area_m2')).toBeTruthy();
    expect(screen.getByTestId('form-field-timezone')).toBeTruthy();
  });

  it('submits a valid site and calls onCreated', async () => {
    const user = userEvent.setup();
    const onCreated = vi.fn();
    renderWithProviders(<SiteCreateDialog open onClose={() => {}} onCreated={onCreated} />, {
      store: createStoreWithExpertise('expert'),
    });

    const nameField = within(await screen.findByTestId('form-field-name')).getByRole('textbox');
    await user.type(nameField, 'North Field');
    await user.click(screen.getByTestId('form-submit-button'));

    await waitFor(() => {
      expect(onCreated).toHaveBeenCalledOnce();
    });
  });

  it('does not submit when the required name is empty', async () => {
    const user = userEvent.setup();
    const onCreated = vi.fn();
    renderWithProviders(<SiteCreateDialog open onClose={() => {}} onCreated={onCreated} />, {
      store: createStoreWithExpertise('expert'),
    });

    await screen.findByTestId('site-create-dialog');
    await user.click(screen.getByTestId('form-submit-button'));

    await waitFor(() => {
      expect(screen.getByTestId('site-create-dialog')).toBeTruthy();
    });
    expect(onCreated).not.toHaveBeenCalled();
  });

  it('surfaces a server error without calling onCreated', async () => {
    server.use(
      http.post('/api/v1/sites', () =>
        HttpResponse.json(
          { error_id: 'e', error_code: 'CONFLICT', message: 'dup', details: [], timestamp: '', path: '', method: '' },
          { status: 409 },
        ),
      ),
      http.post('/api/v1/t/:tenant/sites', () =>
        HttpResponse.json(
          { error_id: 'e', error_code: 'CONFLICT', message: 'dup', details: [], timestamp: '', path: '', method: '' },
          { status: 409 },
        ),
      ),
    );
    const user = userEvent.setup();
    const onCreated = vi.fn();
    renderWithProviders(<SiteCreateDialog open onClose={() => {}} onCreated={onCreated} />, {
      store: createStoreWithExpertise('expert'),
    });

    const nameField = within(await screen.findByTestId('form-field-name')).getByRole('textbox');
    await user.type(nameField, 'North Field');
    await user.click(screen.getByTestId('form-submit-button'));

    await waitFor(() => {
      expect(screen.getByTestId('form-submit-button')).not.toBeDisabled();
    });
    expect(onCreated).not.toHaveBeenCalled();
  });

  it('calls onClose when cancelled', async () => {
    const user = userEvent.setup();
    const onClose = vi.fn();
    renderWithProviders(<SiteCreateDialog open onClose={onClose} onCreated={() => {}} />, {
      store: createStoreWithExpertise('expert'),
    });
    await user.click(await screen.findByTestId('form-cancel-button'));
    expect(onClose).toHaveBeenCalledOnce();
  });

  it('exposes the site type select and GPS coordinate fields for an expert', async () => {
    renderWithProviders(<SiteCreateDialog open onClose={() => {}} onCreated={() => {}} />, {
      store: createStoreWithExpertise('expert'),
    });
    expect(await screen.findByTestId('form-field-type')).toBeTruthy();
    expect(screen.getByTestId('form-field-gps_lat')).toBeTruthy();
    expect(screen.getByTestId('form-field-gps_lon')).toBeTruthy();
  });

  it('submits the chosen type and GPS coordinates', async () => {
    let captured: Record<string, unknown> | null = null;
    const capture = async ({ request }: { request: Request }) => {
      captured = (await request.json()) as Record<string, unknown>;
      return HttpResponse.json({ key: 'site-new', ...captured }, { status: 201 });
    };
    server.use(
      http.post('/api/v1/sites', capture),
      http.post('/api/v1/t/:tenant/sites', capture),
    );

    const user = userEvent.setup();
    const onCreated = vi.fn();
    renderWithProviders(<SiteCreateDialog open onClose={() => {}} onCreated={onCreated} />, {
      store: createStoreWithExpertise('expert'),
    });

    const nameField = within(await screen.findByTestId('form-field-name')).getByRole('textbox');
    await user.type(nameField, 'North Field');

    await user.click(within(screen.getByTestId('form-field-type')).getByRole('combobox'));
    await user.click(await screen.findByRole('option', { name: 'Außenbereich' }));

    await user.type(within(screen.getByTestId('form-field-gps_lat')).getByRole('spinbutton'), '52.5');
    await user.type(within(screen.getByTestId('form-field-gps_lon')).getByRole('spinbutton'), '13.4');

    await user.click(screen.getByTestId('form-submit-button'));

    await waitFor(() => {
      expect(onCreated).toHaveBeenCalledOnce();
    });
    expect(captured).not.toBeNull();
    expect(captured!.type).toBe('outdoor');
    expect(captured!.gps_coordinates).toEqual([52.5, 13.4]);
  });

  it('sends null GPS coordinates when both fields are empty', async () => {
    let captured: Record<string, unknown> | null = null;
    const capture = async ({ request }: { request: Request }) => {
      captured = (await request.json()) as Record<string, unknown>;
      return HttpResponse.json({ key: 'site-new', ...captured }, { status: 201 });
    };
    server.use(
      http.post('/api/v1/sites', capture),
      http.post('/api/v1/t/:tenant/sites', capture),
    );

    const user = userEvent.setup();
    const onCreated = vi.fn();
    renderWithProviders(<SiteCreateDialog open onClose={() => {}} onCreated={onCreated} />, {
      store: createStoreWithExpertise('expert'),
    });

    const nameField = within(await screen.findByTestId('form-field-name')).getByRole('textbox');
    await user.type(nameField, 'Indoor Tent');
    await user.click(screen.getByTestId('form-submit-button'));

    await waitFor(() => {
      expect(onCreated).toHaveBeenCalledOnce();
    });
    expect(captured!.gps_coordinates).toBeNull();
  });

  it('treats balcony as weather-relevant when selected: swaps the disabled hint for the balcony hint', async () => {
    const user = userEvent.setup();
    renderWithProviders(<SiteCreateDialog open onClose={() => {}} onCreated={() => {}} />, {
      store: createStoreWithExpertise('expert'),
    });

    await screen.findByTestId('site-create-dialog');
    // Default type is indoor => the disabled hint is visible, no balcony hint.
    expect(screen.getByTestId('site-weather-type-hint')).toBeTruthy();
    expect(screen.queryByTestId('site-balcony-weather-hint')).toBeNull();

    await user.click(within(screen.getByTestId('form-field-type')).getByRole('combobox'));
    await user.click(await screen.findByRole('option', { name: 'Balkon' }));

    // Balcony is weather-relevant => disabled hint gone, positive hint shown.
    await waitFor(() =>
      expect(screen.queryByTestId('site-weather-type-hint')).toBeNull(),
    );
    expect(screen.getByTestId('site-balcony-weather-hint')).toBeTruthy();
  });

  it('persists GPS coordinates for a balcony site', async () => {
    let captured: Record<string, unknown> | null = null;
    const capture = async ({ request }: { request: Request }) => {
      captured = (await request.json()) as Record<string, unknown>;
      return HttpResponse.json({ key: 'site-new', ...captured }, { status: 201 });
    };
    server.use(
      http.post('/api/v1/sites', capture),
      http.post('/api/v1/t/:tenant/sites', capture),
    );

    const user = userEvent.setup();
    const onCreated = vi.fn();
    renderWithProviders(<SiteCreateDialog open onClose={() => {}} onCreated={onCreated} />, {
      store: createStoreWithExpertise('expert'),
    });

    const nameField = within(await screen.findByTestId('form-field-name')).getByRole('textbox');
    await user.type(nameField, 'South Balcony');

    await user.click(within(screen.getByTestId('form-field-type')).getByRole('combobox'));
    await user.click(await screen.findByRole('option', { name: 'Balkon' }));

    await user.type(within(screen.getByTestId('form-field-gps_lat')).getByRole('spinbutton'), '48.1');
    await user.type(within(screen.getByTestId('form-field-gps_lon')).getByRole('spinbutton'), '11.6');

    await user.click(screen.getByTestId('form-submit-button'));

    await waitFor(() => {
      expect(onCreated).toHaveBeenCalledOnce();
    });
    expect(captured!.type).toBe('balcony');
    expect(captured!.gps_coordinates).toEqual([48.1, 11.6]);
  });

  it('keeps the disabled hint for a windowsill (indoor) type', async () => {
    const user = userEvent.setup();
    renderWithProviders(<SiteCreateDialog open onClose={() => {}} onCreated={() => {}} />, {
      store: createStoreWithExpertise('expert'),
    });

    await screen.findByTestId('site-create-dialog');
    await user.click(within(screen.getByTestId('form-field-type')).getByRole('combobox'));
    await user.click(await screen.findByRole('option', { name: 'Fensterbrett' }));

    expect(screen.getByTestId('site-weather-type-hint')).toBeTruthy();
    expect(screen.queryByTestId('site-balcony-weather-hint')).toBeNull();
  });

  it('blocks submission when a coordinate is out of range', async () => {
    const user = userEvent.setup();
    const onCreated = vi.fn();
    renderWithProviders(<SiteCreateDialog open onClose={() => {}} onCreated={onCreated} />, {
      store: createStoreWithExpertise('expert'),
    });

    const nameField = within(await screen.findByTestId('form-field-name')).getByRole('textbox');
    await user.type(nameField, 'Bad Coords');
    await user.type(within(screen.getByTestId('form-field-gps_lat')).getByRole('spinbutton'), '999');
    await user.type(within(screen.getByTestId('form-field-gps_lon')).getByRole('spinbutton'), '10');
    await user.click(screen.getByTestId('form-submit-button'));

    await waitFor(() => {
      expect(screen.getByTestId('site-create-dialog')).toBeTruthy();
    });
    expect(onCreated).not.toHaveBeenCalled();
  });
});
