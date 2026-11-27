import { cleanup, render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, beforeEach, describe, it, expect, vi } from 'vitest';
import { ThemeContextProvider } from '@/theme';
import { SnackbarProvider } from 'notistack';
import i18n from '@/i18n';
import TerminationDialog from '@/pages/pflanzen/TerminationDialog';
import type { TerminationOptions } from '@/api/types';
// The two answers the API sends for a lettuce and for a nightshade that bolted early; a backend contract test
// (tests/contracts/test_termination_options_fixture.py) keeps this file equal to the real response.
import fixture from '@/test/fixtures/terminationOptions.json';

const getTerminationOptions = vi.hoisted(() => vi.fn());
vi.mock('@/api/endpoints/plantTermination', () => ({ getTerminationOptions }));

const LETTUCE = fixture.default as TerminationOptions;
const BOLTED_NIGHTSHADE = fixture.wiltProneBolting as TerminationOptions;

type User = ReturnType<typeof userEvent.setup>;

function renderDialog(props: Partial<Parameters<typeof TerminationDialog>[0]> = {}) {
  const merged = {
    open: true,
    plantKey: 'plant-1',
    plantName: 'TOMATO-1',
    onConfirm: vi.fn(),
    onCancel: vi.fn(),
    ...props,
  };
  return {
    ...merged,
    ...render(
      <ThemeContextProvider>
        <SnackbarProvider>
          <TerminationDialog {...merged} />
        </SnackbarProvider>
      </ThemeContextProvider>,
    ),
  };
}

async function selectFrom(user: User, selectTestId: string, optionTestId: string) {
  await user.click(within(screen.getByTestId(selectTestId)).getByRole('combobox'));
  await user.click(await screen.findByTestId(optionTestId));
}

async function chooseDied(user: User) {
  await selectFrom(user, 'termination-type-select', 'termination-type-died');
  await screen.findByTestId('termination-cause-select');
}

async function chooseCause(user: User, cause: string) {
  await selectFrom(user, 'termination-cause-select', `termination-cause-${cause}`);
}

describe('TerminationDialog', () => {
  beforeEach(async () => {
    await i18n.changeLanguage('de');
    getTerminationOptions.mockReset();
    getTerminationOptions.mockResolvedValue(LETTUCE);
  });
  afterEach(() => cleanup());

  it('loads the options of the plant it ends', async () => {
    renderDialog({ plantKey: 'plant-42' });
    await waitFor(() => expect(getTerminationOptions).toHaveBeenCalledWith('plant-42'));
  });

  it('shows no cause select until "died" is chosen', () => {
    renderDialog();
    expect(screen.getByTestId('termination-type-select')).toBeTruthy();
    expect(screen.queryByTestId('termination-cause-block')).toBeNull();
  });

  it('plain confirm without a type performs a backward-compatible removal', async () => {
    const user = userEvent.setup();
    const onConfirm = vi.fn();
    renderDialog({ onConfirm });
    await user.click(screen.getByTestId('termination-confirm'));
    expect(onConfirm).toHaveBeenCalledWith({});
  });

  it('a planned end submits only the termination_type', async () => {
    const user = userEvent.setup();
    const onConfirm = vi.fn();
    renderDialog({ onConfirm });
    await selectFrom(user, 'termination-type-select', 'termination-type-harvested');
    expect(screen.queryByTestId('termination-cause-block')).toBeNull();
    await user.click(screen.getByTestId('termination-confirm'));
    expect(onConfirm).toHaveBeenCalledWith({ termination_type: 'harvested' });
  });

  it('offers every cause of the server table, bolting included', async () => {
    const user = userEvent.setup();
    renderDialog();
    await chooseDied(user);
    await user.click(within(screen.getByTestId('termination-cause-select')).getByRole('combobox'));
    for (const rule of LETTUCE.rules) {
      expect(await screen.findByTestId(`termination-cause-${rule.termination_cause}`)).toBeTruthy();
    }
    expect(screen.getByTestId('termination-cause-bolting').textContent).toBe('Schossen');
  });

  it('calls onCancel when cancelled', async () => {
    const user = userEvent.setup();
    const onCancel = vi.fn();
    renderDialog({ onCancel });
    await user.click(screen.getByTestId('termination-cancel'));
    expect(onCancel).toHaveBeenCalledOnce();
  });

  describe('acceptance-1: the cause class is derived or asked', () => {
    it('pre-fills an abiotic cause and sends the class with it', async () => {
      const user = userEvent.setup();
      const onConfirm = vi.fn();
      renderDialog({ onConfirm });
      await chooseDied(user);
      expect(screen.getByTestId('termination-confirm')).toBeDisabled();
      await chooseCause(user, 'frost');

      expect(screen.getByTestId('termination-class-prefilled').textContent).toContain('Abiotisch');
      expect(screen.queryByTestId('termination-class-picker')).toBeNull();
      expect(screen.queryByTestId('termination-wilt-question')).toBeNull();
      await user.click(screen.getByTestId('termination-confirm'));
      expect(onConfirm).toHaveBeenCalledWith({
        termination_type: 'died',
        termination_cause: 'frost',
        failure_cause_class: 'abiotic',
      });
    });

    it('pre-fills mechanical with the mechanical class', async () => {
      const user = userEvent.setup();
      const onConfirm = vi.fn();
      renderDialog({ onConfirm });
      await chooseDied(user);
      await chooseCause(user, 'mechanical');
      await user.click(screen.getByTestId('termination-confirm'));
      expect(onConfirm).toHaveBeenCalledWith(expect.objectContaining({ failure_cause_class: 'mechanical' }));
    });

    it.each([
      ['pest', 'pest_foliar', 'pest_soil'],
      ['disease', 'disease_foliar', 'disease_soil'],
    ])('requires a foliar/soil choice for %s', async (cause, foliar, soil) => {
      const user = userEvent.setup();
      const onConfirm = vi.fn();
      renderDialog({ onConfirm });
      await chooseDied(user);
      await chooseCause(user, cause);

      const picker = screen.getByTestId('termination-class-picker');
      expect(within(picker).getByTestId(`termination-class-${foliar}`)).toBeTruthy();
      expect(within(picker).getByTestId(`termination-class-${soil}`)).toBeTruthy();
      expect(within(picker).getAllByRole('radio')).toHaveLength(2);
      expect(screen.getByTestId('termination-confirm')).toBeDisabled();

      await user.click(screen.getByTestId(`termination-class-${soil}`));
      await user.click(screen.getByTestId('termination-confirm'));
      expect(onConfirm).toHaveBeenCalledWith({
        termination_type: 'died',
        termination_cause: cause,
        failure_cause_class: soil,
      });
    });

    it('lets an unknown cause pick any class, pre-filled unknown', async () => {
      const user = userEvent.setup();
      const onConfirm = vi.fn();
      renderDialog({ onConfirm });
      await chooseDied(user);
      await chooseCause(user, 'unknown');
      const picker = screen.getByTestId('termination-class-picker');
      expect(within(picker).getAllByRole('radio')).toHaveLength(7);
      expect(screen.getByTestId('termination-class-unknown')).toBeChecked();
      await user.click(screen.getByTestId('termination-confirm'));
      expect(onConfirm).toHaveBeenCalledWith(expect.objectContaining({ failure_cause_class: 'unknown' }));
    });
  });

  describe('acceptance-2: the wilt follow-up', () => {
    it.each(['heat', 'drought', 'waterlogging'])('%s asks it; yes records a soil-borne disease', async (cause) => {
      const user = userEvent.setup();
      const onConfirm = vi.fn();
      renderDialog({ onConfirm });
      await chooseDied(user);
      await chooseCause(user, cause);

      expect(screen.getByTestId('termination-wilt-question')).toBeTruthy();
      await user.click(screen.getByTestId('termination-wilt-yes'));
      expect(screen.getByTestId('termination-class-prefilled').textContent).toContain('Bodenbürtige Krankheit');
      await user.click(screen.getByTestId('termination-confirm'));
      expect(onConfirm).toHaveBeenCalledWith({
        termination_type: 'died',
        termination_cause: cause,
        failure_cause_class: 'disease_soil',
      });
    });

    it('a no keeps the abiotic pre-fill', async () => {
      const user = userEvent.setup();
      const onConfirm = vi.fn();
      renderDialog({ onConfirm });
      await chooseDied(user);
      await chooseCause(user, 'heat');
      await user.click(screen.getByTestId('termination-wilt-yes'));
      await user.click(screen.getByTestId('termination-wilt-no'));
      await user.click(screen.getByTestId('termination-confirm'));
      expect(onConfirm).toHaveBeenCalledWith(expect.objectContaining({ failure_cause_class: 'abiotic' }));
    });

    it('unknown does not ask it on a family without wilt risk', async () => {
      const user = userEvent.setup();
      renderDialog();
      await chooseDied(user);
      await chooseCause(user, 'unknown');
      expect(screen.queryByTestId('termination-wilt-question')).toBeNull();
    });

    it('unknown asks it on a wilt-prone family and a yes records a soil-borne disease', async () => {
      const user = userEvent.setup();
      const onConfirm = vi.fn();
      getTerminationOptions.mockResolvedValue(BOLTED_NIGHTSHADE);
      renderDialog({ onConfirm });
      await chooseDied(user);
      await chooseCause(user, 'unknown');
      expect(screen.getByTestId('termination-wilt-question')).toBeTruthy();
      await user.click(screen.getByTestId('termination-wilt-yes'));
      expect(screen.getByTestId('termination-class-disease_soil')).toBeChecked();
      await user.click(screen.getByTestId('termination-confirm'));
      expect(onConfirm).toHaveBeenCalledWith(expect.objectContaining({ failure_cause_class: 'disease_soil' }));
    });

    it.each(['frost', 'neglect', 'mechanical', 'bolting', 'pest', 'disease'])('%s does not ask it', async (cause) => {
      const user = userEvent.setup();
      getTerminationOptions.mockResolvedValue(BOLTED_NIGHTSHADE);
      renderDialog();
      await chooseDied(user);
      await chooseCause(user, cause);
      expect(screen.queryByTestId('termination-wilt-question')).toBeNull();
    });
  });

  describe('wilt question and class picker together (unknown on a wilt-prone family)', () => {
    async function unknownOnNightshade(user: User, onConfirm = vi.fn()) {
      getTerminationOptions.mockResolvedValue(BOLTED_NIGHTSHADE);
      renderDialog({ onConfirm });
      await chooseDied(user);
      await chooseCause(user, 'unknown');
      return onConfirm;
    }

    it('a class picked after a wilt yes wins, and the helper no longer claims a soil-borne disease', async () => {
      const user = userEvent.setup();
      const onConfirm = await unknownOnNightshade(user);
      await user.click(screen.getByTestId('termination-wilt-yes'));
      expect(screen.getByTestId('termination-wilt-question').textContent).toContain('Erfasst als bodenbürtige Krankheit');

      await user.click(screen.getByTestId('termination-class-pest_foliar'));
      const question = screen.getByTestId('termination-wilt-question');
      expect(question.textContent).not.toContain('Erfasst als bodenbürtige Krankheit');
      expect(screen.getByTestId('termination-wilt-yes')).not.toBeChecked();
      await user.click(screen.getByTestId('termination-confirm'));
      expect(onConfirm).toHaveBeenCalledWith(expect.objectContaining({ failure_cause_class: 'pest_foliar' }));
    });

    it('a late no keeps a class picked on purpose', async () => {
      const user = userEvent.setup();
      const onConfirm = await unknownOnNightshade(user);
      await user.click(screen.getByTestId('termination-class-mechanical'));
      await user.click(screen.getByTestId('termination-wilt-no'));
      expect(screen.getByTestId('termination-class-mechanical')).toBeChecked();
      await user.click(screen.getByTestId('termination-confirm'));
      expect(onConfirm).toHaveBeenCalledWith(expect.objectContaining({ failure_cause_class: 'mechanical' }));
    });

    it('a no keeps a soil-borne disease picked in the picker, with its pathogen', async () => {
      const user = userEvent.setup();
      const onConfirm = await unknownOnNightshade(user);
      await user.click(screen.getByTestId('termination-class-disease_soil'));
      await selectFrom(user, 'form-field-failure-pathogen', 'termination-pathogen-verticillium');
      await user.click(screen.getByTestId('termination-pathogen-confirmed'));
      await user.click(screen.getByTestId('termination-source-lab_test'));

      await user.click(screen.getByTestId('termination-wilt-no'));

      expect(screen.getByTestId('termination-class-disease_soil')).toBeChecked();
      expect(screen.getByTestId('termination-pathogen-confirmed')).toBeChecked();
      await user.click(screen.getByTestId('termination-confirm'));
      expect(onConfirm).toHaveBeenCalledWith({
        termination_type: 'died',
        termination_cause: 'unknown',
        failure_cause_class: 'disease_soil',
        failure_pathogen: 'verticillium',
        failure_pathogen_confirmed: true,
        failure_pathogen_source: 'lab_test',
      });
    });

    it('a no after a yes takes the soil-borne disease back to the pre-fill', async () => {
      const user = userEvent.setup();
      const onConfirm = await unknownOnNightshade(user);
      await user.click(screen.getByTestId('termination-wilt-yes'));
      await user.click(screen.getByTestId('termination-wilt-no'));
      expect(screen.getByTestId('termination-class-unknown')).toBeChecked();
      await user.click(screen.getByTestId('termination-confirm'));
      expect(onConfirm).toHaveBeenCalledWith(expect.objectContaining({ failure_cause_class: 'unknown' }));
    });
  });

  it('after a wilt yes the class is not called pre-filled', async () => {
    const user = userEvent.setup();
    renderDialog();
    await chooseDied(user);
    await chooseCause(user, 'heat');
    expect(screen.getByTestId('termination-class-prefilled').textContent).toContain('vorbelegt');
    await user.click(screen.getByTestId('termination-wilt-yes'));
    const text = screen.getByTestId('termination-class-prefilled').textContent ?? '';
    expect(text).toContain('Bodenbürtige Krankheit');
    expect(text).not.toContain('vorbelegt');
  });

  it('starts empty and loads the options again when reopened', async () => {
    const user = userEvent.setup();
    const { rerender, onConfirm, onCancel } = renderDialog();
    await chooseDied(user);
    await chooseCause(user, 'frost');
    const props = { plantKey: 'plant-1', plantName: 'TOMATO-1', onConfirm, onCancel };
    const wrap = (open: boolean) => (
      <ThemeContextProvider>
        <SnackbarProvider>
          <TerminationDialog open={open} {...props} />
        </SnackbarProvider>
      </ThemeContextProvider>
    );
    rerender(wrap(false));
    await waitFor(() => expect(screen.queryByTestId('termination-type-select')).toBeNull());
    rerender(wrap(true));
    await screen.findByTestId('termination-type-select');
    expect(screen.queryByTestId('termination-cause-block')).toBeNull();
    await waitFor(() => expect(getTerminationOptions).toHaveBeenCalledTimes(2));
  });

  describe('acceptance-3: bolting', () => {
    it('is pre-filled after a premature bolt and sent as abiotic', async () => {
      const user = userEvent.setup();
      const onConfirm = vi.fn();
      getTerminationOptions.mockResolvedValue(BOLTED_NIGHTSHADE);
      renderDialog({ onConfirm });
      await chooseDied(user);

      expect(await screen.findByTestId('termination-cause-suggested')).toBeTruthy();
      expect(within(screen.getByTestId('termination-cause-select')).getByRole('combobox').textContent).toBe('Schossen');
      expect(screen.getByTestId('termination-class-prefilled').textContent).toContain('Abiotisch');
      await user.click(screen.getByTestId('termination-confirm'));
      expect(onConfirm).toHaveBeenCalledWith({
        termination_type: 'died',
        termination_cause: 'bolting',
        failure_cause_class: 'abiotic',
      });
    });

    it('is not pre-filled without a premature bolt', async () => {
      const user = userEvent.setup();
      renderDialog();
      await chooseDied(user);
      expect(screen.queryByTestId('termination-cause-suggested')).toBeNull();
      expect(screen.getByTestId('termination-confirm')).toBeDisabled();
    });
  });

  describe('acceptance-4: the pathogen of a soil-borne loss', () => {
    it('names a hazard-list pathogen, its confirmation and who confirmed it', async () => {
      const user = userEvent.setup();
      const onConfirm = vi.fn();
      renderDialog({ onConfirm });
      await chooseDied(user);
      await chooseCause(user, 'disease');
      expect(screen.queryByTestId('termination-pathogen-block')).toBeNull();
      await user.click(screen.getByTestId('termination-class-disease_soil'));

      await user.click(within(screen.getByTestId('form-field-failure-pathogen')).getByRole('combobox'));
      for (const hazard of LETTUCE.pathogens) {
        expect(await screen.findByTestId(`termination-pathogen-${hazard}`)).toBeTruthy();
      }
      await user.click(screen.getByTestId('termination-pathogen-verticillium'));
      await user.click(screen.getByTestId('termination-pathogen-confirmed'));
      // Confirmed without saying by whom is not enough.
      expect(screen.getByTestId('termination-confirm')).toBeDisabled();
      await user.click(screen.getByTestId('termination-source-lab_test'));
      await user.click(screen.getByTestId('termination-confirm'));

      expect(onConfirm).toHaveBeenCalledWith({
        termination_type: 'died',
        termination_cause: 'disease',
        failure_cause_class: 'disease_soil',
        failure_pathogen: 'verticillium',
        failure_pathogen_confirmed: true,
        failure_pathogen_source: 'lab_test',
      });
    });

    it('sends an unconfirmed pathogen as unconfirmed', async () => {
      const user = userEvent.setup();
      const onConfirm = vi.fn();
      renderDialog({ onConfirm });
      await chooseDied(user);
      await chooseCause(user, 'pest');
      await user.click(screen.getByTestId('termination-class-pest_soil'));
      await selectFrom(user, 'form-field-failure-pathogen', 'termination-pathogen-cyst_nematode');
      await user.click(screen.getByTestId('termination-confirm'));
      expect(onConfirm).toHaveBeenCalledWith({
        termination_type: 'died',
        termination_cause: 'pest',
        failure_cause_class: 'pest_soil',
        failure_pathogen: 'cyst_nematode',
        failure_pathogen_confirmed: false,
      });
    });

    it('drops the pathogen when the class moves to the leaves', async () => {
      const user = userEvent.setup();
      const onConfirm = vi.fn();
      renderDialog({ onConfirm });
      await chooseDied(user);
      await chooseCause(user, 'disease');
      await user.click(screen.getByTestId('termination-class-disease_soil'));
      await selectFrom(user, 'form-field-failure-pathogen', 'termination-pathogen-clubroot');
      await user.click(screen.getByTestId('termination-class-disease_foliar'));
      expect(screen.queryByTestId('termination-pathogen-block')).toBeNull();
      await user.click(screen.getByTestId('termination-confirm'));
      expect(onConfirm).toHaveBeenCalledWith({
        termination_type: 'died',
        termination_cause: 'disease',
        failure_cause_class: 'disease_foliar',
      });
    });
  });

  it('describes why the confirm is blocked for keyboard and screen-reader users', async () => {
    const user = userEvent.setup();
    renderDialog();
    await chooseDied(user);
    await chooseCause(user, 'pest');

    const confirm = screen.getByTestId('termination-confirm');
    expect(confirm).toBeDisabled();
    expect(confirm).toHaveAccessibleDescription('Bitte wähle aus, ob die Ursache an Blatt oder im Boden saß.');

    await user.click(screen.getByTestId('termination-class-pest_soil'));
    expect(screen.getByTestId('termination-confirm')).toBeEnabled();
    expect(screen.getByTestId('termination-confirm')).not.toHaveAttribute('aria-describedby');
  });

  it('announces the options load as a status', async () => {
    const user = userEvent.setup();
    getTerminationOptions.mockReturnValue(new Promise(() => {}));
    renderDialog();
    await selectFrom(user, 'termination-type-select', 'termination-type-died');
    expect(screen.getByTestId('loading-skeleton').getAttribute('role')).toBe('status');
  });

  it('a failed options load says so, blocks a died confirm and can be retried', async () => {
    const user = userEvent.setup();
    getTerminationOptions.mockRejectedValueOnce(new Error('network'));
    renderDialog();
    await selectFrom(user, 'termination-type-select', 'termination-type-died');
    expect(await screen.findByTestId('termination-options-error')).toBeTruthy();
    expect(screen.getByTestId('termination-confirm')).toBeDisabled();
    // The hint on the blocked button names the failure, not a load that is no longer running.
    await user.hover(screen.getByTestId('termination-confirm').parentElement as HTMLElement);
    expect((await screen.findByRole('tooltip')).textContent).toBe('Die Ursachen konnten nicht geladen werden.');

    await user.click(screen.getByTestId('termination-options-retry'));
    expect(await screen.findByTestId('termination-cause-select')).toBeTruthy();
    expect(getTerminationOptions).toHaveBeenCalledTimes(2);
  });

  it('acceptance-6: the new labels exist in English too', async () => {
    await i18n.changeLanguage('en');
    const user = userEvent.setup();
    getTerminationOptions.mockResolvedValue(BOLTED_NIGHTSHADE);
    renderDialog();
    await chooseDied(user);
    expect(within(screen.getByTestId('termination-cause-select')).getByRole('combobox').textContent).toBe('Bolting');
    expect(screen.getByTestId('termination-class-prefilled').textContent).toContain('Abiotic');
    await chooseCause(user, 'heat');
    expect(screen.getByTestId('termination-wilt-question').textContent).toContain('wilt despite moist soil');
  });
});
