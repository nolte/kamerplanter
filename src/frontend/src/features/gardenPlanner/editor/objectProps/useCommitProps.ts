/**
 * The commit of a props patch of one object (REQ-053 GP-FR-180, WP 10.6): the whole props object with the patch
 * applied, as ONE `update_fields` (one undo step); an unchanged object sends nothing.
 */
import { useCallback } from 'react';
import type { GardenObjectProps } from '../../model/types';
import { propsOperation } from './propsOperation';
import type { ObjectFieldsProps } from './shared';

export function useCommitProps<P extends GardenObjectProps>({
  objectKey,
  props,
  onCommit,
}: Pick<ObjectFieldsProps<P>, 'objectKey' | 'props' | 'onCommit'>) {
  return useCallback(
    (patch: Partial<Omit<P, 'object_type'>>) => {
      const op = propsOperation(objectKey, props, { ...props, ...patch } as P);
      if (op) onCommit([op], 'edit');
    },
    [objectKey, props, onCommit],
  );
}
