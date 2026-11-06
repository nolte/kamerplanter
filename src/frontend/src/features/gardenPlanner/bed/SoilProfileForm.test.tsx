/** The soil form keeps the user's edits when the summary behind it reloads (REQ-053 GP-FR-120). */
import { useState } from 'react';
import { cleanup, screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { http, HttpResponse } from 'msw';
import { afterEach, describe, expect, it } from 'vitest';
import { server } from '@/test/mocks/server';
import { renderWithProviders } from '@/test/helpers';
import SoilProfileForm from './SoilProfileForm';
import { bedSummary } from './bedTestKit';
import type { SoilProfile } from './types';

function Harness({ next }: { next: SoilProfile }) {
  const [profile, setProfile] = useState<SoilProfile>(bedSummary().soil_profile!);
  return (
    <>
      {/* A reload hands in a new object; `same` has the same content, `changed` a new one. */}
      <button type="button" onClick={() => setProfile({ ...profile })}>
        same
      </button>
      <button type="button" onClick={() => setProfile(next)}>
        changed
      </button>
      <SoilProfileForm bedKey="loc_b03" profile={profile} canEdit onSaved={() => undefined} />
    </>
  );
}

afterEach(() => cleanup());

describe('SoilProfileForm reload handling', () => {
  const changed: SoilProfile = { ...bedSummary().soil_profile!, soil_texture: 'clay' };

  it('keeps what the user typed when the same profile arrives again', async () => {
    const user = userEvent.setup();
    renderWithProviders(<Harness next={changed} />);
    const notes = await screen.findByRole('textbox', { name: /Notes/ });
    await user.type(notes, 'compost in autumn');
    await user.click(screen.getByRole('button', { name: 'same' }));
    expect(screen.getByRole('textbox', { name: /Notes/ })).toHaveValue('compost in autumn');
  });

  it('keeps unsaved edits even when the stored profile changed meanwhile', async () => {
    const user = userEvent.setup();
    renderWithProviders(<Harness next={changed} />);
    await user.type(await screen.findByRole('textbox', { name: /Notes/ }), 'x');
    await user.click(screen.getByRole('button', { name: 'changed' }));
    expect(screen.getByRole('textbox', { name: /Notes/ })).toHaveValue('x');
  });

  it('takes the stored profile when there is nothing to lose', async () => {
    const user = userEvent.setup();
    renderWithProviders(<Harness next={changed} />);
    const texture = await screen.findByTestId('form-field-soil_texture');
    expect(within(texture).getByRole('combobox')).toHaveTextContent('Loam');
    await user.click(screen.getByRole('button', { name: 'changed' }));
    expect(within(screen.getByTestId('form-field-soil_texture')).getByRole('combobox')).toHaveTextContent('Clay');
  });
});

describe('SoilProfileForm EC method (U-002, WP 8.8)', () => {
  it('asks for the EC method instead of sending a value the server refuses', async () => {
    let patched = false;
    server.use(
      http.patch('/api/v1/t/:tenant/locations/:key', () => {
        patched = true;
        return HttpResponse.json({ key: 'loc_b03', bed_status: 'active', plan_revision: 1 });
      }),
    );
    const user = userEvent.setup();
    renderWithProviders(
      <SoilProfileForm bedKey="loc_b03" profile={bedSummary().soil_profile!} canEdit onSaved={() => undefined} />,
    );
    const ec = within(await screen.findByTestId('form-field-ec_ms_cm')).getByRole('spinbutton');
    await user.type(ec, '0.8');
    await user.click(screen.getByTestId('form-submit-button'));
    expect(await screen.findByText(/Choose how the EC was measured/)).toBeInTheDocument();
    expect(patched).toBe(false);
  });
});
