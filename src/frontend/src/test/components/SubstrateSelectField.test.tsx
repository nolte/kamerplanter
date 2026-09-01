import { screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { useForm } from 'react-hook-form';
import SubstrateSelectField from '@/components/form/SubstrateSelectField';
import type { Substrate } from '@/api/types';
import { renderWithProviders } from '../helpers';
import * as favoritesApi from '@/api/endpoints/favorites';

vi.mock('@/api/endpoints/favorites');

const storageMap = new Map<string, string>();
const mockLocalStorage = {
  getItem: vi.fn((key: string) => storageMap.get(key) ?? null),
  setItem: vi.fn((key: string, value: string) => storageMap.set(key, value)),
  removeItem: vi.fn((key: string) => storageMap.delete(key)),
  clear: vi.fn(() => storageMap.clear()),
  get length() { return storageMap.size; },
  key: vi.fn(() => null),
};
Object.defineProperty(globalThis, 'localStorage', { value: mockLocalStorage, writable: true });

beforeEach(() => {
  vi.mocked(favoritesApi.listFavorites).mockResolvedValue([]);
  vi.mocked(favoritesApi.addFavorite).mockResolvedValue({} as never);
  vi.mocked(favoritesApi.removeFavorite).mockResolvedValue(undefined);
});

const substrates: Substrate[] = [
  {
    key: 'sub-coco',
    type: 'coco',
    brand: 'CocoBrand',
    name_de: 'Kokoserde',
    name_en: 'Coco soil',
    is_mix: false,
    reusable: true,
    max_reuse_cycles: 3,
  } as Substrate,
  {
    key: 'sub-mix',
    type: 'living_soil',
    brand: null,
    name_de: 'Lebende Erde',
    name_en: 'Living soil',
    is_mix: true,
    reusable: false,
    max_reuse_cycles: 0,
  } as Substrate,
];

function TestForm({
  substrates: list = substrates,
  defaultValue = '',
}: {
  substrates?: Substrate[];
  defaultValue?: string;
}) {
  const { control } = useForm({ defaultValues: { substrate_key: defaultValue } });
  return (
    <SubstrateSelectField
      name="substrate_key"
      control={control}
      label="Substrat"
      substrates={list}
    />
  );
}

describe('SubstrateSelectField', () => {
  beforeEach(() => {
    storageMap.clear();
    vi.clearAllMocks();
  });

  it('renders the labelled input', () => {
    renderWithProviders(<TestForm />);
    expect(screen.getByLabelText(/substrat/i)).toBeTruthy();
  });

  it('shows the locale display name for a preselected substrate entity', () => {
    renderWithProviders(<TestForm defaultValue="sub-coco" />);
    const input = screen.getByLabelText(/substrat/i) as HTMLInputElement;
    // i18n resolves to English in the test environment → name_en.
    expect(input.value).toBe('Coco soil');
  });

  it('lists all substrate entities when opened', async () => {
    const user = userEvent.setup();
    renderWithProviders(<TestForm />);
    await user.click(screen.getByLabelText(/substrat/i));
    const listbox = screen.getByRole('listbox');
    expect(within(listbox).getAllByRole('option').length).toBe(2);
  });

  it('selects a substrate and updates the input value', async () => {
    const user = userEvent.setup();
    renderWithProviders(<TestForm />);
    const input = screen.getByLabelText(/substrat/i);
    await user.click(input);
    await user.click(screen.getByRole('option', { name: /Coco soil/i }));
    expect((input as HTMLInputElement).value).toBe('Coco soil');
  });

  it('renders enum-based fallback options when no entities are provided', async () => {
    const user = userEvent.setup();
    renderWithProviders(<TestForm substrates={[]} />);
    await user.click(screen.getByLabelText(/substrat/i));
    const listbox = screen.getByRole('listbox');
    // 14 SubstrateType enum fallbacks.
    expect(within(listbox).getAllByRole('option').length).toBe(14);
  });

  it('persists a starred favorite to the server, not to localStorage', async () => {
    // Until #1233 this asserted `localStorage.setItem`, which certified the
    // drift instead of catching it: substrate favorites lived only in the
    // browser, so the onboarding wizard's cascade was invisible here and the
    // fertilizer cascade REQ-020 §1 specifies never ran outside the wizard.
    const user = userEvent.setup();
    renderWithProviders(<TestForm />);
    await user.click(screen.getByLabelText(/substrat/i));
    const listbox = screen.getByRole('listbox');
    const firstOption = within(listbox).getAllByRole('option')[0];
    const favButton = within(firstOption).getAllByRole('button')[0];
    await user.click(favButton);

    await waitFor(() =>
      expect(favoritesApi.addFavorite).toHaveBeenCalledWith(expect.any(String), 'manual'),
    );
    expect(mockLocalStorage.setItem).not.toHaveBeenCalledWith(
      'kamerplanter-substrate-favorites',
      expect.any(String),
    );
  });
});

describe('SubstrateSelectField — soil amendments (#1175)', () => {
  const amendment = {
    key: 'sub-premix',
    type: 'peat',
    brand: 'BioBizz',
    name_de: 'BioBizz Pre·Mix (Bodenverbesserer)',
    name_en: 'BioBizz Pre-Mix (Soil Conditioner)',
    is_mix: false,
    is_amendment: true,
    reusable: false,
    max_reuse_cycles: 1,
  } as Substrate;

  it('does not offer an amendment as a growing medium', async () => {
    // `BioBizz Pre·Mix` is a soil conditioner — 30 % peat, the rest bone meal,
    // blood meal, guano, dolomite, seaweed and leonardite. Nothing is planted in
    // it, but it is typed `peat` and so appeared in the same list as the media.
    // Both call sites of this field assign a plant's medium.
    const user = userEvent.setup();
    renderWithProviders(<TestForm substrates={[...substrates, amendment]} />);

    await user.click(screen.getByRole('combobox'));
    const list = await screen.findByRole('listbox');

    expect(within(list).queryByText(/BioBizz/)).toBeNull();
    // Control: the real media are still there, so the assertion above cannot be
    // satisfied by an empty list.
    expect(within(list).getByText('Coco soil')).toBeTruthy();
  });

  it('falls back to the enum types when the only entries are amendments', async () => {
    // The fallback keys off "no selectable entity", not "no entity at all". A
    // catalogue holding nothing but amendments has nothing to plant in, and an
    // empty picker would be a dead end rather than a degraded one.
    const user = userEvent.setup();
    renderWithProviders(<TestForm substrates={[amendment]} />);

    await user.click(screen.getByRole('combobox'));
    const list = await screen.findByRole('listbox');

    expect(within(list).queryByText(/BioBizz/)).toBeNull();
    expect(within(list).getAllByRole('option').length).toBeGreaterThan(1);
  });
});
