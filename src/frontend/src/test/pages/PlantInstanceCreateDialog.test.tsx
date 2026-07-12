import { screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { http, HttpResponse } from 'msw';
import i18n from 'i18next';
import PlantInstanceCreateDialog, {
  type PlantInstanceDuplicateData,
} from '@/pages/pflanzen/PlantInstanceCreateDialog';
import { renderWithProviders } from '../helpers';
import { server } from '../mocks/server';
import { contributeReferenceImage } from '@/api/endpoints/identification';

// The undici multipart parser in the test env cannot re-read a File field from
// `request.formData()`, so we spy on the reference endpoint directly to assert
// the arguments instead of round-tripping the multipart body through MSW.
vi.mock('@/api/endpoints/identification', async (importOriginal) => {
  const actual = await importOriginal<typeof import('@/api/endpoints/identification')>();
  return {
    ...actual,
    contributeReferenceImage: vi
      .fn()
      .mockResolvedValue({ indexed: true, species_key: 'sp-1', dim: 768 }),
  };
});
const contributeReferenceMock = vi.mocked(contributeReferenceImage);

describe('PlantInstanceCreateDialog', () => {
  beforeEach(() => {
    i18n.changeLanguage('de');
    contributeReferenceMock.mockClear();
  });

  it('renders the create dialog with the create title when open', async () => {
    renderWithProviders(
      <PlantInstanceCreateDialog open onClose={() => {}} onCreated={() => {}} />,
    );
    expect(await screen.findByTestId('plant-instance-create-dialog')).toBeTruthy();
    expect(within(screen.getByRole('dialog')).getByText('Pflanze erstellen')).toBeTruthy();
  });

  it('does not render content when closed', () => {
    renderWithProviders(
      <PlantInstanceCreateDialog open={false} onClose={() => {}} onCreated={() => {}} />,
    );
    expect(screen.queryByTestId('plant-instance-create-dialog')).toBeNull();
  });

  it('prefills the instance id from a generated value', async () => {
    renderWithProviders(
      <PlantInstanceCreateDialog open onClose={() => {}} onCreated={() => {}} />,
    );
    const idField = within(await screen.findByTestId('form-field-instance_id')).getByRole('textbox');
    await waitFor(() => {
      expect((idField as HTMLInputElement).value.length).toBeGreaterThan(0);
    });
  });

  it('frames the current-phase field as actual-state capture via helper text', async () => {
    renderWithProviders(
      <PlantInstanceCreateDialog open onClose={() => {}} onCreated={() => {}} />,
    );
    await screen.findByTestId('plant-instance-create-dialog');
    // The descriptive helper text makes the phase an intentional actual-state
    // choice (REQ-003 #539 gap 3), not a silent auto-selection.
    expect(
      within(screen.getByRole('dialog')).getByText(/Aktueller Ist-Stand der Pflanze/),
    ).toBeTruthy();
  });

  it('shows the duplicate title and disables species when duplicating', async () => {
    const duplicateFrom: PlantInstanceDuplicateData = {
      species_key: 'sp-1',
      cultivar_key: null,
      plant_name: 'Big Red',
      substrate_key: null,
      substrate_type_override: null,
      current_phase_key: null,
      slot_key: null,
    };
    renderWithProviders(
      <PlantInstanceCreateDialog
        open
        onClose={() => {}}
        onCreated={() => {}}
        duplicateFrom={duplicateFrom}
      />,
    );
    expect(
      within(await screen.findByRole('dialog')).getByText('Pflanze duplizieren'),
    ).toBeTruthy();
  });

  it('submits a new plant instance and calls onCreated with the new key', async () => {
    const user = userEvent.setup();
    const onCreated = vi.fn();
    renderWithProviders(
      <PlantInstanceCreateDialog open onClose={() => {}} onCreated={onCreated} />,
    );

    // species + instance_id are required; pick species via the autocomplete
    const speciesInput = within(await screen.findByTestId('form-field-species_key')).getByRole('combobox');
    await user.click(speciesInput);
    await user.type(speciesInput, 'Solanum');
    const option = await screen.findByRole('option', { name: /Solanum lycopersicum/ });
    await user.click(option);

    await user.click(screen.getByTestId('form-submit-button'));

    await waitFor(() => {
      expect(onCreated).toHaveBeenCalledOnce();
    });
    expect(onCreated).toHaveBeenCalledWith('plant-new');
  });

  it('surfaces a server error without calling onCreated', async () => {
    server.use(
      http.post('/api/v1/plant-instances', () =>
        HttpResponse.json(
          { error_id: 'e', error_code: 'CONFLICT', message: 'dup', details: [], timestamp: '', path: '', method: '' },
          { status: 409 },
        ),
      ),
      http.post('/api/v1/t/:tenant/plant-instances', () =>
        HttpResponse.json(
          { error_id: 'e', error_code: 'CONFLICT', message: 'dup', details: [], timestamp: '', path: '', method: '' },
          { status: 409 },
        ),
      ),
    );
    const user = userEvent.setup();
    const onCreated = vi.fn();
    renderWithProviders(
      <PlantInstanceCreateDialog open onClose={() => {}} onCreated={onCreated} />,
    );

    const speciesInput = within(await screen.findByTestId('form-field-species_key')).getByRole('combobox');
    await user.click(speciesInput);
    await user.type(speciesInput, 'Solanum');
    await user.click(await screen.findByRole('option', { name: /Solanum lycopersicum/ }));

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
      <PlantInstanceCreateDialog open onClose={onClose} onCreated={() => {}} />,
    );
    await user.click(await screen.findByTestId('form-cancel-button'));
    expect(onClose).toHaveBeenCalledOnce();
  });

  it('resolves the location cascade from a duplicated slot', async () => {
    // Duplicating from a plant with a slot_key triggers getSlot → getLocation →
    // listSlots and pre-populates site/location/slot via the skip-reset refs.
    const duplicateFrom: PlantInstanceDuplicateData = {
      species_key: 'sp-1',
      cultivar_key: null,
      plant_name: 'Big Red',
      substrate_key: null,
      substrate_type_override: 'coco',
      current_phase_key: null,
      slot_key: 'slot-1',
    };
    renderWithProviders(
      <PlantInstanceCreateDialog open onClose={() => {}} onCreated={() => {}} duplicateFrom={duplicateFrom} />,
    );

    // The slot select becomes populated once the cascade resolves
    await waitFor(() => {
      expect(screen.getByTestId('form-field-slot_key')).toBeTruthy();
    });
    // Species is locked for duplicates
    const speciesInput = within(screen.getByTestId('form-field-species_key')).getByRole('combobox');
    expect(speciesInput).toBeDisabled();
  });

  it('selecting a site populates the location select cascade', async () => {
    const user = userEvent.setup();
    renderWithProviders(
      <PlantInstanceCreateDialog open onClose={() => {}} onCreated={() => {}} />,
    );

    const siteSelect = within(await screen.findByTestId('form-field-site_key')).getByRole('combobox');
    await user.click(siteSelect);
    await user.click(await screen.findByRole('option', { name: 'Main Greenhouse' }));

    // The location field reacts to the selected site without throwing
    await waitFor(() => {
      expect(screen.getByTestId('form-field-slot_key')).toBeTruthy();
    });
  });

  // ── Species favorite toggle (issue #546) ────────────────────────────
  describe('species favorite toggle', () => {
    async function selectTomato(user: ReturnType<typeof userEvent.setup>) {
      const speciesInput = within(
        await screen.findByTestId('form-field-species_key'),
      ).getByRole('combobox');
      await user.click(speciesInput);
      await user.type(speciesInput, 'Solanum');
      await user.click(await screen.findByRole('option', { name: /Solanum lycopersicum/ }));
    }

    it('disables the favorite toggle while no species is selected', async () => {
      renderWithProviders(
        <PlantInstanceCreateDialog open onClose={() => {}} onCreated={() => {}} />,
      );
      const toggle = await screen.findByTestId('favorite-toggle-species');
      expect(toggle).toBeDisabled();
    });

    it('enables the favorite toggle once a species is selected', async () => {
      const user = userEvent.setup();
      renderWithProviders(
        <PlantInstanceCreateDialog open onClose={() => {}} onCreated={() => {}} />,
      );
      await selectTomato(user);
      const toggle = screen.getByTestId('favorite-toggle-species');
      await waitFor(() => expect(toggle).not.toBeDisabled());
      // Not yet a favorite → aria-pressed is false.
      expect(toggle).toHaveAttribute('aria-pressed', 'false');
    });

    it('reflects an already-favorited species from the loaded favorites', async () => {
      server.use(
        http.get('/api/v1/t/:tenant/favorites', () =>
          HttpResponse.json([
            {
              key: 'fav-1',
              target_key: 'sp-1',
              target_type: 'species',
              source: 'manual',
              cascade_from_key: null,
              favorited_at: '2026-01-01T00:00:00Z',
            },
          ]),
        ),
      );
      const user = userEvent.setup();
      renderWithProviders(
        <PlantInstanceCreateDialog open onClose={() => {}} onCreated={() => {}} />,
      );
      await selectTomato(user);
      const toggle = screen.getByTestId('favorite-toggle-species');
      await waitFor(() => expect(toggle).toHaveAttribute('aria-pressed', 'true'));
    });

    it('adds the selected species to favorites on click and persists it', async () => {
      const addedKeys: string[] = [];
      server.use(
        http.get('/api/v1/t/:tenant/favorites', () => HttpResponse.json([])),
        http.post('/api/v1/t/:tenant/favorites', async ({ request }) => {
          const body = (await request.json()) as { target_key: string; source: string };
          addedKeys.push(body.target_key);
          return HttpResponse.json(
            {
              key: 'fav-new',
              target_key: body.target_key,
              target_type: 'species',
              source: body.source,
              cascade_from_key: null,
              favorited_at: '2026-01-01T00:00:00Z',
            },
            { status: 201 },
          );
        }),
      );
      const user = userEvent.setup();
      renderWithProviders(
        <PlantInstanceCreateDialog open onClose={() => {}} onCreated={() => {}} />,
      );
      await selectTomato(user);
      const toggle = screen.getByTestId('favorite-toggle-species');
      await waitFor(() => expect(toggle).not.toBeDisabled());

      await user.click(toggle);

      // Optimistic UI flips to favorited immediately …
      await waitFor(() => expect(toggle).toHaveAttribute('aria-pressed', 'true'));
      // … and the backend persists the selected species key.
      await waitFor(() => expect(addedKeys).toEqual(['sp-1']));
    });

    it('does not interfere with the create submission after favoriting', async () => {
      const createdPayloads: Array<{ species_key: string }> = [];
      server.use(
        http.get('/api/v1/t/:tenant/favorites', () => HttpResponse.json([])),
        http.post('/api/v1/t/:tenant/favorites', () =>
          HttpResponse.json(
            {
              key: 'fav-new',
              target_key: 'sp-1',
              target_type: 'species',
              source: 'manual',
              cascade_from_key: null,
              favorited_at: '2026-01-01T00:00:00Z',
            },
            { status: 201 },
          ),
        ),
        http.post('/api/v1/t/:tenant/plant-instances', async ({ request }) => {
          const body = (await request.json()) as { species_key: string };
          createdPayloads.push({ species_key: body.species_key });
          return HttpResponse.json({ key: 'plant-new', ...body }, { status: 201 });
        }),
      );
      const user = userEvent.setup();
      const onCreated = vi.fn();
      renderWithProviders(
        <PlantInstanceCreateDialog open onClose={() => {}} onCreated={onCreated} />,
      );
      await selectTomato(user);
      const toggle = screen.getByTestId('favorite-toggle-species');
      await waitFor(() => expect(toggle).not.toBeDisabled());
      await user.click(toggle);

      await user.click(screen.getByTestId('form-submit-button'));

      await waitFor(() => expect(onCreated).toHaveBeenCalledWith('plant-new'));
      // The favorite action left the form intact: species_key still submits.
      expect(createdPayloads).toEqual([{ species_key: 'sp-1' }]);
    });
  });

  // ── Identification photo carry-over (issue #447) ─────────────────────
  describe('identification photo carry-over', () => {
    function makePhoto(): File {
      return new File([new Uint8Array([1, 2, 3])], 'capture.jpg', { type: 'image/jpeg' });
    }

    it('hides the photo section when no identification photo is provided', async () => {
      renderWithProviders(
        <PlantInstanceCreateDialog open onClose={() => {}} onCreated={() => {}} />,
      );
      await screen.findByTestId('plant-instance-create-dialog');
      expect(screen.queryByTestId('identification-photo-section')).toBeNull();
    });

    it('shows the gallery toggle (default on) and hides the reference toggle without DINOv2', async () => {
      renderWithProviders(
        <PlantInstanceCreateDialog
          open
          onClose={() => {}}
          onCreated={() => {}}
          initialSpeciesKey="sp-1"
          identificationPhoto={makePhoto()}
        />,
      );
      expect(await screen.findByTestId('identification-photo-section')).toBeTruthy();
      const galleryToggle = within(screen.getByTestId('toggle-save-gallery-photo')).getByRole(
        'switch',
      );
      expect(galleryToggle).toBeChecked();
      // Reference toggle only exists in DINOv2 mode.
      expect(screen.queryByTestId('toggle-use-as-reference')).toBeNull();
    });

    it('shows the reference toggle (default off) when DINOv2 mode is available', async () => {
      renderWithProviders(
        <PlantInstanceCreateDialog
          open
          onClose={() => {}}
          onCreated={() => {}}
          initialSpeciesKey="sp-1"
          identificationPhoto={makePhoto()}
          allowReferenceContribution
        />,
      );
      const referenceToggle = within(
        await screen.findByTestId('toggle-use-as-reference'),
      ).getByRole('switch');
      expect(referenceToggle).not.toBeChecked();
    });

    it('uploads the photo to the new plant gallery when the toggle stays on', async () => {
      const uploadUrls: string[] = [];
      server.use(
        http.post('/api/v1/t/:tenant/plant-instances/:key/photos', ({ params }) => {
          uploadUrls.push(String(params.key));
          return HttpResponse.json(
            { attachment_id: 'att-1', uri: '/x', thumbnail_uris: null, is_cover: true, mime_type: 'image/jpeg', byte_size: 3, caption: null, taken_on: null, quality_assessment: null, created_at: null },
            { status: 201 },
          );
        }),
      );
      const user = userEvent.setup();
      const onCreated = vi.fn();
      renderWithProviders(
        <PlantInstanceCreateDialog
          open
          onClose={() => {}}
          onCreated={onCreated}
          initialSpeciesKey="sp-1"
          identificationPhoto={makePhoto()}
        />,
      );

      await screen.findByTestId('identification-photo-section');
      await user.click(screen.getByTestId('form-submit-button'));

      await waitFor(() => expect(onCreated).toHaveBeenCalledWith('plant-new'));
      expect(uploadUrls).toEqual(['plant-new']);
    });

    it('skips the gallery upload when the toggle is turned off', async () => {
      let uploadCalled = false;
      server.use(
        http.post('/api/v1/t/:tenant/plant-instances/:key/photos', () => {
          uploadCalled = true;
          return HttpResponse.json({}, { status: 201 });
        }),
      );
      const user = userEvent.setup();
      const onCreated = vi.fn();
      renderWithProviders(
        <PlantInstanceCreateDialog
          open
          onClose={() => {}}
          onCreated={onCreated}
          initialSpeciesKey="sp-1"
          identificationPhoto={makePhoto()}
        />,
      );

      await screen.findByTestId('identification-photo-section');
      await user.click(within(screen.getByTestId('toggle-save-gallery-photo')).getByRole('switch'));
      await user.click(screen.getByTestId('form-submit-button'));

      await waitFor(() => expect(onCreated).toHaveBeenCalledWith('plant-new'));
      expect(uploadCalled).toBe(false);
    });

    it('contributes the photo as a reference only when the DINOv2 toggle is enabled', async () => {
      server.use(
        http.post('/api/v1/t/:tenant/plant-instances/:key/photos', () =>
          HttpResponse.json({}, { status: 201 }),
        ),
      );
      const user = userEvent.setup();
      const onCreated = vi.fn();
      const photo = makePhoto();
      renderWithProviders(
        <PlantInstanceCreateDialog
          open
          onClose={() => {}}
          onCreated={onCreated}
          initialSpeciesKey="sp-1"
          identificationPhoto={photo}
          allowReferenceContribution
        />,
      );

      await screen.findByTestId('identification-photo-section');
      await user.click(within(screen.getByTestId('toggle-use-as-reference')).getByRole('switch'));
      await user.click(screen.getByTestId('form-submit-button'));

      await waitFor(() => expect(onCreated).toHaveBeenCalledWith('plant-new'));
      expect(contributeReferenceMock).toHaveBeenCalledWith('sp-1', 'Solanum lycopersicum', photo);
    });

    it('does not contribute a reference when the DINOv2 toggle stays off', async () => {
      server.use(
        http.post('/api/v1/t/:tenant/plant-instances/:key/photos', () =>
          HttpResponse.json({}, { status: 201 }),
        ),
      );
      const user = userEvent.setup();
      const onCreated = vi.fn();
      renderWithProviders(
        <PlantInstanceCreateDialog
          open
          onClose={() => {}}
          onCreated={onCreated}
          initialSpeciesKey="sp-1"
          identificationPhoto={makePhoto()}
          allowReferenceContribution
        />,
      );

      await screen.findByTestId('identification-photo-section');
      await user.click(screen.getByTestId('form-submit-button'));

      await waitFor(() => expect(onCreated).toHaveBeenCalledWith('plant-new'));
      expect(contributeReferenceMock).not.toHaveBeenCalled();
    });
  });
});
