import { screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { useForm } from 'react-hook-form';
import SubstrateSelectField from '@/components/form/SubstrateSelectField';
import type { Substrate } from '@/api/types';
import { renderWithProviders } from '../helpers';

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

  it('persists a starred favorite to localStorage', async () => {
    const user = userEvent.setup();
    renderWithProviders(<TestForm />);
    await user.click(screen.getByLabelText(/substrat/i));
    const listbox = screen.getByRole('listbox');
    const firstOption = within(listbox).getAllByRole('option')[0];
    const favButton = within(firstOption).getAllByRole('button')[0];
    await user.click(favButton);
    expect(mockLocalStorage.setItem).toHaveBeenCalledWith(
      'kamerplanter-substrate-favorites',
      expect.any(String),
    );
  });
});
