/**
 * The three IPM create dialogs must carry `noValidate`.
 *
 * Their fields declare native `required` and their forms are RHF + zod. Without
 * `noValidate`, Chrome aborts submission before the `submit` event fires:
 * `handleSubmit` never runs, zod never runs, no helper text renders, and the
 * user gets only a transient native bubble in the browser's own locale
 * (#778 B1).
 *
 * It went unnoticed because the E2E page objects submitted these dialogs by
 * dispatching a raw `new Event('submit')` at the form, bypassing the button and
 * with it native validation entirely. #815 routed them through the real button
 * -- as a state-changing helper must -- and the next nightly failed on all six
 * profiles at once, which is how the product defect surfaced.
 *
 * **Why this asserts the attribute rather than the behaviour.** A behavioural
 * test was written first and then thrown away: it passed with and without
 * `noValidate`, because jsdom does not block submission on native constraints
 * the way Chrome does. Shipping it would have added a test that cannot fail --
 * precisely the defect class this whole change exists to remove. Asserting the
 * attribute is narrower but honest: it fails the moment `noValidate` is dropped.
 *
 * The authoritative check stays the E2E suite: TC-REQ-010-010, -011, -022 and
 * -033 run in a real browser, and they are what caught this.
 */
import { describe, expect, it } from 'vitest';
import { screen } from '@testing-library/react';

import PestCreateDialog from '@/pages/pflanzenschutz/PestCreateDialog';
import DiseaseCreateDialog from '@/pages/pflanzenschutz/DiseaseCreateDialog';
import TreatmentCreateDialog from '@/pages/pflanzenschutz/TreatmentCreateDialog';

import { renderWithProviders } from '../helpers';

function formOf(testId: string): HTMLFormElement {
  const dialog = screen.getByTestId(testId);
  const form = dialog.querySelector('form');
  expect(form, `${testId} renders no form`).not.toBeNull();
  return form as HTMLFormElement;
}

describe('IPM create dialogs — zod validation is reachable through the button', () => {
  it('the pest dialog suppresses native validation so zod can run', () => {
    renderWithProviders(<PestCreateDialog open onClose={() => {}} onCreated={() => {}} />);

    expect(formOf('pest-create-dialog').noValidate).toBe(true);
  });

  it('the disease dialog suppresses native validation so zod can run', () => {
    renderWithProviders(<DiseaseCreateDialog open onClose={() => {}} onCreated={() => {}} />);

    expect(formOf('disease-create-dialog').noValidate).toBe(true);
  });

  it('the treatment dialog suppresses native validation so zod can run', () => {
    renderWithProviders(<TreatmentCreateDialog open onClose={() => {}} onCreated={() => {}} />);

    expect(formOf('treatment-create-dialog').noValidate).toBe(true);
  });
});
