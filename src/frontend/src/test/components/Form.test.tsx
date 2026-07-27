import { render, screen } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import Form from '@/components/form/Form';

/**
 * These assertions are deliberately *structural* rather than behavioural.
 *
 * The behaviour we actually care about — an empty `required` field must reach
 * zod instead of being intercepted by the browser — cannot be tested here at
 * all: jsdom does not implement native constraint validation, so submitting an
 * invalid form resolves identically with and without `noValidate`. A test
 * written in that shape passes even when the guard is removed, which is how
 * #825 stayed invisible across ~55 files (see #822, which discarded exactly
 * such a test rather than ship a check that cannot fail).
 *
 * So what is asserted here is the one thing jsdom *can* see and that a
 * regression would actually change: the attribute reaches the DOM node, and a
 * call site cannot take it away again. The behavioural half of the contract is
 * covered in a real browser by the E2E suite.
 */
describe('Form', () => {
  it('renders a form element carrying noValidate', () => {
    render(
      <Form onSubmit={vi.fn()} data-testid="subject">
        <button type="submit">Submit</button>
      </Form>,
    );

    const form = screen.getByTestId('subject');
    expect(form.tagName).toBe('FORM');
    expect(form.hasAttribute('novalidate')).toBe(true);
  });

  it('keeps noValidate even when a call site tries to unset it', () => {
    render(
      // @ts-expect-error -- `noValidate` is removed from the prop surface on
      // purpose; this reproduces a call site trying to opt out anyway, which
      // must not work at runtime either.
      <Form onSubmit={vi.fn()} noValidate={false} data-testid="subject">
        <button type="submit">Submit</button>
      </Form>,
    );

    expect(screen.getByTestId('subject').hasAttribute('novalidate')).toBe(true);
  });

  it('forwards submit handling and arbitrary form props', () => {
    const onSubmit = vi.fn((event: React.FormEvent) => event.preventDefault());
    render(
      <Form onSubmit={onSubmit} id="my-form" data-testid="subject">
        <button type="submit">Submit</button>
      </Form>,
    );

    const form = screen.getByTestId('subject');
    expect(form.getAttribute('id')).toBe('my-form');

    screen.getByRole('button', { name: 'Submit' }).click();
    expect(onSubmit).toHaveBeenCalledTimes(1);
  });
});
