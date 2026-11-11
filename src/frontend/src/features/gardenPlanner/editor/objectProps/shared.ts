/**
 * What the object-property fields share (REQ-053 GP-FR-180, WP 10.6): the i18n prefix, the touch-target size and
 * how a bound is written in a hint ("0,01" in German, "0.01" in English).
 */
import type { GardenObjectProps, PlanOperation } from '../../model/types';
import type { ActionLabel } from '../tools/machineTypes';

export const OBJECT_PROPS_PREFIX = 'pages.gardenPlan.editor.panel.objectProps';

/** The minimum height of a control: WCAG 2.5.5 / GP-UX touch target. */
export const TARGET_PX = 48;

/** A bound as the reader writes numbers. */
export const formatBound = (value: number, language: string): string =>
  new Intl.NumberFormat(language).format(value);

/** The props of one object class with the panel's commit path; every class's fields take this. */
export interface ObjectFieldsProps<P extends GardenObjectProps> {
  objectKey: string;
  props: P;
  disabled: boolean;
  onCommit: (ops: PlanOperation[], label: ActionLabel) => void;
}
