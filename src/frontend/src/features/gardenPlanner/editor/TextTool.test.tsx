/**
 * The tool "Text" in the editor (REQ-053 GP-UX-071, #2913): the eighth and last button of the rail. A click sets the
 * snapped anchor, a small dialog asks for one line of text, and the caption is a `text_label` garden object of the
 * plan batch - pending, one undo step, selected afterwards like a drawn object. The panel edits its text (and refits
 * its box in the same step); the keyboard path goes through the rail's "Set text here", the touch path through the
 * TouchBar's "Set point".
 */
import { act, cleanup, fireEvent, screen, within } from '@testing-library/react';
import { afterEach, describe, expect, it } from 'vitest';
import { expectNoA11yViolations } from '@/test/a11y/expectNoA11yViolations';
import type { GardenObject } from '../model/types';
import { setupEditor, stubPhone } from './editorTestKit';

const restores: (() => void)[] = [];
afterEach(() => {
  cleanup();
  while (restores.length) restores.pop()?.();
  localStorage.clear();
});

function textSetup(options: Parameters<typeof setupEditor>[0] = {}) {
  const t = setupEditor(options);
  t.after(() => fireEvent.click(screen.getByTestId('garden-plan-tool-text')));
  const captions = (): GardenObject[] =>
    Object.values(t.state().plan!.gardenObjects).filter((object) => object.object_type === 'text_label');
  const type = (text: string) =>
    t.after(() => fireEvent.change(screen.getByTestId('garden-plan-text-input'), { target: { value: text } }));
  const submit = () => t.after(() => fireEvent.click(screen.getByTestId('garden-plan-text-submit')));
  return { ...t, captions, type, submit };
}

describe('the text tool on the rail (GP-UX-071)', () => {
  it('is the eighth tool: pressed on the rail, a crosshair cursor, a status that says where a click puts the text', () => {
    const t = textSetup();
    expect(t.state().tool).toBe('text');
    const button = screen.getByTestId('garden-plan-tool-text');
    expect(button).toHaveAttribute('aria-pressed', 'true');
    expect(button).toHaveAccessibleName('Text');
    expect(button).toHaveStyle({ minHeight: '48px', minWidth: '48px' });
    const rail = within(screen.getByTestId('garden-plan-toolbar'));
    expect(rail.getAllByRole('button').filter((node) => node.getAttribute('aria-pressed') !== null)).toHaveLength(8);
    expect(t.canvas()).toHaveStyle({ cursor: 'crosshair' });
    expect(screen.getByTestId('garden-plan-text-status')).toHaveTextContent('Click the plan where the caption should start');
    expect(screen.getByTestId('garden-plan-text-status')).toHaveAttribute('aria-live', 'polite');
    // No shapes, no type choice: a caption is one click and a line of text.
    expect(screen.queryByTestId('garden-plan-shape-rect')).toBeNull();
  });

  it('is offered to a viewer like the bed and area tools - the save is where the role is checked', () => {
    setupEditor({ role: 'viewer' });
    expect(screen.getByTestId('garden-plan-tool-text')).toBeInTheDocument();
    expect(screen.getByTestId('garden-plan-tool-bed')).toBeInTheDocument();
  });
});

describe('setting a caption with the pointer', () => {
  it('opens the dialog at the snapped click and creates one text_label as a pending operation and one undo step', () => {
    const t = textSetup();
    const before = t.state().past.length;
    // Off the 10 cm grid: the anchor lands on (1, 14.1) like a drawn corner.
    t.click(1.02, 14.07);
    expect(screen.getByTestId('garden-plan-text-dialog')).toBeInTheDocument();
    expect(t.state().pending).toHaveLength(0);

    t.type('  Kräuterecke ');
    t.submit();

    // The form is unmounted at once (the dialog itself fades out).
    expect(screen.queryByTestId('garden-plan-text-input')).toBeNull();
    const [caption] = t.captions();
    expect(caption.label).toBe('Kräuterecke');
    expect(caption.parent_location_key ?? null).toBeNull();
    // 20 px high at 40 px/m = 0.5 m; 11 characters at 0.4 m × 0.6 = 2.64 m wide.
    expect(caption.geometry).toEqual({ kind: 'rect', origin: [1, 14.1], width_m: 2.64, length_m: 0.5, rotation_deg: 0 });
    expect(t.state().pending).toHaveLength(1);
    expect(t.state().pending[0].op).toMatchObject({
      op: 'create_garden_object',
      data: { object_type: 'text_label', label: 'Kräuterecke', props: {} },
    });
    expect(t.state().past).toHaveLength(before + 1);
    // Like a drawn object: the caption is selected and the tool hands over to Select.
    expect(t.selected()).toEqual([caption.key]);
    expect(t.state().tool).toBe('select');

    // One undo step takes it away again.
    t.after(() => fireEvent.keyDown(t.canvas(), { key: 'z', ctrlKey: true }));
    expect(t.captions()).toHaveLength(0);
  });

  it('refuses an empty, an overlong or a control-character text in the dialog and creates nothing', () => {
    const t = textSetup();
    t.click(5, 15);
    t.submit();
    expect(screen.getByText('Type a text.')).toBeInTheDocument();
    t.type('x'.repeat(81));
    expect(screen.getByText('A caption has at most 80 characters.')).toBeInTheDocument();
    t.submit();
    t.type('Zeile\u0007');
    expect(screen.getByText('A caption is one line without line breaks or control characters.')).toBeInTheDocument();
    t.submit();
    expect(screen.getByTestId('garden-plan-text-dialog')).toBeInTheDocument();
    expect(t.captions()).toHaveLength(0);
    expect(t.state().pending).toHaveLength(0);
    // Before any mistake the field counts its characters.
    t.type('Ost');
    expect(screen.getByText('3 of 80 characters, one line')).toBeInTheDocument();
  });

  it('keeps the dialog and the text when the caption would run past the garden boundary', () => {
    const t = textSetup();
    t.click(19, 15);
    t.type('Ein langer Hinweis am Rand');
    t.submit();
    expect(screen.getByTestId('garden-plan-text-error')).toBeInTheDocument();
    expect(screen.getByTestId('garden-plan-text-input')).toHaveValue('Ein langer Hinweis am Rand');
    expect(t.captions()).toHaveLength(0);
  });

  it('cancels without a trace and keeps the tool on', () => {
    const t = textSetup();
    t.click(5, 15);
    t.after(() => fireEvent.click(screen.getByTestId('garden-plan-text-cancel')));
    expect(screen.queryByTestId('garden-plan-text-input')).toBeNull();
    expect(t.state().pending).toHaveLength(0);
    expect(t.state().tool).toBe('text');
  });

  it('has no accessibility violations with the dialog open', async () => {
    const t = textSetup();
    t.click(5, 15);
    await expectNoA11yViolations(document.body, { minImpact: 'serious' });
  });
});

describe('editing a caption in the properties panel', () => {
  function withCaption() {
    const t = textSetup();
    t.click(1, 14);
    t.type('Ost');
    t.submit();
    return t;
  }

  it('changes the text and refits the box in one undo step', () => {
    const t = withCaption();
    const past = t.state().past.length;
    const field = screen.getByTestId('garden-plan-panel-name');
    expect(within(screen.getByTestId('garden-plan-panel-form')).getByLabelText('Text')).toBe(field);
    t.after(() => fireEvent.change(field, { target: { value: 'Ostbeete' } }));
    t.after(() => fireEvent.keyDown(field, { key: 'Enter' }));

    const [caption] = t.captions();
    expect(caption.label).toBe('Ostbeete');
    // Same height and anchor, 8 characters at 0.4 m × 0.6 = 1.92 m.
    expect(caption.geometry).toMatchObject({ origin: [1, 14], length_m: 0.5, width_m: 1.92 });
    expect(t.state().past).toHaveLength(past + 1);
    expect(t.state().pending.map((entry) => entry.op.op)).toEqual(['create_garden_object', 'update_fields', 'update_geometry']);
  });

  it('tells an empty text under the field and keeps the caption as it was', () => {
    const t = withCaption();
    const field = screen.getByTestId('garden-plan-panel-name');
    t.after(() => fireEvent.change(field, { target: { value: '  ' } }));
    t.after(() => fireEvent.blur(field));
    expect(screen.getByText('Type a text.')).toBeInTheDocument();
    expect(t.captions()[0].label).toBe('Ost');
    expect(t.state().pending).toHaveLength(1);
  });

  it('offers no thing properties (height, outside the boundary) for a caption', () => {
    withCaption();
    expect(screen.queryByTestId('garden-plan-panel-object-props')).toBeNull();
  });
});

describe('a caption without a pointer (WCAG 2.1.1)', () => {
  it('rail, arrow keys to the text tool, "Set text here" at the crosshair, type, Enter', () => {
    const t = setupEditor();
    const select = screen.getByTestId('garden-plan-tool-select');
    act(() => select.focus());
    // Past pan, area, bed, garden object, their sub-menu buttons, the plant and the measure tool: ten steps.
    for (let i = 0; i < 10; i += 1) fireEvent.keyDown(document.activeElement!, { key: 'ArrowDown' });
    expect(screen.getByTestId('garden-plan-tool-text')).toHaveFocus();
    t.after(() => fireEvent.click(document.activeElement!));
    expect(t.state().tool).toBe('text');
    expect(screen.queryByTestId('garden-plan-crosshair')).toBeNull();

    fireEvent.keyDown(document.activeElement!, { key: 'ArrowDown' });
    const place = screen.getByTestId('garden-plan-text-place');
    expect(place).toHaveFocus();
    expect(place).toHaveStyle({ minHeight: '48px', minWidth: '48px' });
    expect(screen.getByTestId('garden-plan-crosshair')).toBeInTheDocument();
    expect(screen.getByTestId('garden-plan-text-status')).toHaveTextContent('Move the plan on the canvas with the arrow keys');

    t.after(() => fireEvent.click(place));
    const input = screen.getByTestId('garden-plan-text-input');
    expect(input).toHaveFocus();
    t.after(() => fireEvent.change(input, { target: { value: 'Mitte' } }));
    t.after(() => fireEvent.submit(input.closest('form')!));

    const [caption] = Object.values(t.state().plan!.gardenObjects).filter((o) => o.object_type === 'text_label');
    // The crosshair is the canvas centre: (400, 400) px = model (10, 10).
    expect(caption.geometry).toMatchObject({ kind: 'rect', origin: [10, 10] });
    expect(caption.label).toBe('Mitte');
  });
});

describe('the touch path below md (GP-UX-036/069)', () => {
  it('sets the anchor at the crosshair through the TouchBar\'s "Set point" and asks for the text', () => {
    restores.push(stubPhone());
    const t = setupEditor();
    t.after(() => fireEvent.click(within(screen.getByTestId('garden-plan-dock')).getByTestId('garden-plan-tool-text')));
    expect(screen.getByTestId('garden-plan-crosshair')).toBeInTheDocument();
    expect(screen.getByTestId('garden-plan-text-status')).toHaveTextContent('"Set point"');
    expect(screen.queryByTestId('garden-plan-text-place')).toBeNull();
    const bar = screen.getByTestId('garden-plan-touchbar');
    expect(within(bar).queryByTestId('garden-plan-touch-undo')).toBeNull();

    t.after(() => fireEvent.click(within(bar).getByTestId('garden-plan-touch-place')));
    t.after(() =>
      fireEvent.change(screen.getByTestId('garden-plan-text-input'), { target: { value: 'Teich' } }),
    );
    t.after(() => fireEvent.click(screen.getByTestId('garden-plan-text-submit')));

    const [caption] = Object.values(t.state().plan!.gardenObjects).filter((o) => o.object_type === 'text_label');
    expect(caption.label).toBe('Teich');
    expect(t.state().pending).toHaveLength(1);
  });
});
