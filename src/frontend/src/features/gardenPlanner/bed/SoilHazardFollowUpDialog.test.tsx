/**
 * The follow-up after a soil-borne loss (REQ-053 §11.3a Nr. 5, #2888 F-20): the offer to take a confirmed pathogen
 * into the bed - written only on "Take into the bed", and then with nothing but the plant key, so the server takes
 * pathogen, date and source from the stored loss - and the clean-system hint at hydroponics, which writes nothing.
 */
import { act, cleanup, fireEvent, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { http, HttpResponse } from 'msw';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { expectNoA11yViolations } from '@/test/a11y/expectNoA11yViolations';
import { renderWithProviders } from '@/test/helpers';
import { server } from '@/test/mocks/server';
import SoilHazardFollowUpDialog from './SoilHazardFollowUpDialog';
import type { SoilHazardFollowUp } from './soilHazardTypes';

const BASE = '/api/v1/t/:tenant';
const OFFER: SoilHazardFollowUp = {
  kind: 'offer',
  location_key: 'loc_b03',
  hazard: 'clubroot',
  confirmed_at: '2026-07-01',
  source: 'lab_test',
};

function setOnline(value: boolean) {
  Object.defineProperty(navigator, 'onLine', { configurable: true, get: () => value });
  act(() => {
    window.dispatchEvent(new Event(value ? 'online' : 'offline'));
  });
}

function useTakeOver() {
  const posts: { key: string; body: unknown }[] = [];
  server.use(
    http.post(`${BASE}/locations/:key/soil-hazards`, async ({ params, request }) => {
      posts.push({ key: String(params.key), body: await request.json() });
      return HttpResponse.json({ location_key: String(params.key), soil_hazards: [] }, { status: 201 });
    }),
  );
  return posts;
}

function renderDialog(followUp: SoilHazardFollowUp) {
  const onClose = vi.fn();
  renderWithProviders(
    <SoilHazardFollowUpDialog followUp={followUp} plantKey="pi_kohl" plantName="Cabbage 1" onClose={onClose} />,
  );
  return onClose;
}

afterEach(() => {
  setOnline(true);
  cleanup();
});

describe('SoilHazardFollowUpDialog', () => {
  it('offers the confirmed pathogen and takes it into the bed only on confirmation', async () => {
    const posts = useTakeOver();
    const user = userEvent.setup();
    const onClose = renderDialog(OFFER);

    const dialog = await screen.findByTestId('confirm-dialog');
    expect(dialog).toHaveTextContent('Take the soil hazard into the bed?');
    expect(dialog).toHaveTextContent('Cabbage 1 died of Clubroot, confirmed by Lab test');
    expect(posts).toEqual([]);

    await user.click(within(dialog).getByTestId('confirm-dialog-confirm'));

    await waitFor(() => expect(posts).toEqual([{ key: 'loc_b03', body: { plant_key: 'pi_kohl' } }]));
    await waitFor(() => expect(onClose).toHaveBeenCalledTimes(1));
  });

  it('writes nothing when the offer is declined', async () => {
    const posts = useTakeOver();
    const user = userEvent.setup();
    const onClose = renderDialog(OFFER);

    await user.click(await screen.findByTestId('confirm-dialog-cancel'));

    expect(onClose).toHaveBeenCalledTimes(1);
    expect(posts).toEqual([]);
  });

  it('keeps the offer locked offline: the server must check the loss', async () => {
    const posts = useTakeOver();
    renderDialog(OFFER);
    const dialog = await screen.findByTestId('confirm-dialog');

    setOnline(false);
    fireEvent.click(within(dialog).getByTestId('confirm-dialog-confirm'));

    expect(await within(dialog).findByTestId('confirm-dialog-offline')).toBeInTheDocument();
    expect(posts).toEqual([]);
  });

  it('shows the clean-system hint at hydroponics and writes nothing', async () => {
    const posts = useTakeOver();
    const user = userEvent.setup();
    const onClose = renderDialog({ kind: 'clean_system', location_key: 'loc_nft' });

    const dialog = await screen.findByTestId('soil-hazard-clean-system-dialog');
    expect(dialog).toHaveTextContent('Clean and disinfect the system');
    expect(dialog).toHaveTextContent('clean and disinfect the system before you replant');
    await user.click(within(dialog).getByTestId('soil-hazard-clean-system-ok'));

    expect(onClose).toHaveBeenCalledTimes(1);
    expect(posts).toEqual([]);
  });

  it('has no axe violations', async () => {
    useTakeOver();
    renderDialog(OFFER);
    await expectNoA11yViolations(await screen.findByTestId('confirm-dialog'));
  });
});
