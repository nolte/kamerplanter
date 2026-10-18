/** The soil form keeps the user's edits when the summary behind it reloads (REQ-053 GP-FR-120). */
import { useState } from 'react';
import { cleanup, screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, describe, expect, it } from 'vitest';
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
