import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { renderWithProviders } from './helpers';
import PrintButton from '@/components/common/PrintButton';

describe('PrintButton', () => {
  let onPrint: ReturnType<typeof vi.fn<() => Promise<Blob>>>;
  const originalCreateObjectURL = URL.createObjectURL;
  const originalRevokeObjectURL = URL.revokeObjectURL;

  beforeEach(() => {
    onPrint = vi.fn<() => Promise<Blob>>();
    URL.createObjectURL = vi.fn(() => 'blob:mock-url');
    URL.revokeObjectURL = vi.fn();
  });

  afterEach(() => {
    URL.createObjectURL = originalCreateObjectURL;
    URL.revokeObjectURL = originalRevokeObjectURL;
  });

  it('renders icon variant by default', () => {
    renderWithProviders(
      <PrintButton onPrint={onPrint} filename="test.pdf" />,
    );
    expect(screen.getByTestId('print-button')).toBeInTheDocument();
  });

  it('renders button variant with label', () => {
    renderWithProviders(
      <PrintButton
        onPrint={onPrint}
        filename="test.pdf"
        variant="button"
        label="Export PDF"
      />,
    );
    expect(screen.getByText('Export PDF')).toBeInTheDocument();
  });

  it('calls onPrint and triggers download on click', async () => {
    const user = userEvent.setup();
    const blob = new Blob(['test'], { type: 'application/pdf' });
    onPrint.mockResolvedValue(blob);

    renderWithProviders(
      <PrintButton onPrint={onPrint} filename="plan.pdf" />,
    );

    await user.click(screen.getByTestId('print-button'));

    await waitFor(() => {
      expect(onPrint).toHaveBeenCalledOnce();
      expect(URL.createObjectURL).toHaveBeenCalledWith(blob);
      expect(URL.revokeObjectURL).toHaveBeenCalledWith('blob:mock-url');
    });
  });

  it('calls onPrint on error path and re-enables button', async () => {
    const user = userEvent.setup();
    onPrint.mockRejectedValue(new Error('Network error'));

    renderWithProviders(
      <PrintButton onPrint={onPrint} filename="plan.pdf" />,
    );

    const button = screen.getByTestId('print-button');
    await user.click(button);

    await waitFor(() => {
      expect(onPrint).toHaveBeenCalledOnce();
      // Button is re-enabled after error
      expect(button).not.toBeDisabled();
    });
  });

  it('disables button when disabled prop is true', () => {
    renderWithProviders(
      <PrintButton onPrint={onPrint} filename="test.pdf" disabled />,
    );
    expect(screen.getByTestId('print-button')).toBeDisabled();
  });
});
