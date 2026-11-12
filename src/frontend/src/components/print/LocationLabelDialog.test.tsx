/**
 * "Etikett drucken" of a bed (REQ-053 GP-FR-052, GP-UX-028, #2899): the dialog asks the print route for the bed's
 * label with the chosen QR size and the UI language, downloads the PDF and closes; a refusal keeps it open.
 */
import { act, cleanup, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import i18n from 'i18next';
import { http, HttpResponse } from 'msw';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { LocationLabelDialog } from '@/components/print/LocationLabelDialog';
import { server } from '@/test/mocks/server';
import { renderWithProviders } from '@/test/helpers';

const LABEL_ROUTE = '/api/v1/t/:tenant/print/location-label/:key';

function setOnline(value: boolean) {
  Object.defineProperty(window.navigator, 'onLine', { configurable: true, get: () => value });
  act(() => {
    window.dispatchEvent(new Event(value ? 'online' : 'offline'));
  });
}

function captureLabelRequests(status = 200) {
  const requests: URL[] = [];
  server.use(
    http.get(LABEL_ROUTE, ({ request }) => {
      requests.push(new URL(request.url));
      if (status !== 200) return HttpResponse.json({ detail: 'Not found' }, { status });
      return new HttpResponse(new Blob(['%PDF-1.7'], { type: 'application/pdf' }), {
        headers: { 'Content-Type': 'application/pdf' },
      });
    }),
  );
  return requests;
}

describe('LocationLabelDialog', () => {
  const originalCreate = URL.createObjectURL;
  const originalRevoke = URL.revokeObjectURL;
  let downloads: string[];

  beforeEach(async () => {
    await i18n.changeLanguage('de');
    downloads = [];
    URL.createObjectURL = vi.fn(() => 'blob:label');
    URL.revokeObjectURL = vi.fn();
    vi.spyOn(HTMLAnchorElement.prototype, 'click').mockImplementation(function (this: HTMLAnchorElement) {
      downloads.push(this.download);
    });
  });

  afterEach(() => {
    setOnline(true);
    cleanup();
    URL.createObjectURL = originalCreate;
    URL.revokeObjectURL = originalRevoke;
    vi.restoreAllMocks();
  });

  it('downloads the bed label with the chosen QR size and the UI language, then closes', async () => {
    const requests = captureLabelRequests();
    const onClose = vi.fn();
    renderWithProviders(<LocationLabelDialog open onClose={onClose} locationKey="bed_1" locationName="Hochbeet Süd" />);

    expect(screen.getByTestId('bed-view-label-dialog')).toHaveTextContent('Beet-Etikett drucken');
    expect(screen.getByText(/„Hochbeet Süd“/)).toBeInTheDocument();
    expect(screen.getByTestId('bed-view-label-qr-size-40').querySelector('input')).toBeChecked();

    await userEvent.click(screen.getByTestId('bed-view-label-qr-size-60').querySelector('input')!);
    await userEvent.click(screen.getByTestId('bed-view-label-download'));

    await waitFor(() => expect(onClose).toHaveBeenCalledTimes(1));
    expect(requests).toHaveLength(1);
    // The tenant-scoped print route of the active tenant (the default test store's).
    expect(requests[0].pathname).toBe('/api/v1/t/test-tenant/print/location-label/bed_1');
    expect(Object.fromEntries(requests[0].searchParams)).toEqual({ locale: 'de', qr_size_mm: '60' });
    expect(downloads).toEqual(['bed-label-hochbeet-sud.pdf']);
  });

  it('keeps the dialog open and says so when the label cannot be made', async () => {
    captureLabelRequests(404);
    const onClose = vi.fn();
    renderWithProviders(<LocationLabelDialog open onClose={onClose} locationKey="gone" locationName="Weg" />);

    await userEvent.click(screen.getByTestId('bed-view-label-download'));

    expect(await screen.findByText('PDF konnte nicht erstellt werden. Bitte versuche es erneut.')).toBeInTheDocument();
    expect(onClose).not.toHaveBeenCalled();
    expect(downloads).toEqual([]);
  });

  it('locks the download without a connection and says why', () => {
    setOnline(false);
    renderWithProviders(<LocationLabelDialog open onClose={vi.fn()} locationKey="bed_1" locationName="Beet" />);

    expect(screen.getByTestId('bed-view-label-offline')).toBeInTheDocument();
    expect(screen.getByTestId('bed-view-label-download')).toBeDisabled();
  });
});
