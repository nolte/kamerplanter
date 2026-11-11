/**
 * The bounds of the object props, mirrored from the backend props models (`app/domain/models/garden_object.py`,
 * REQ-053 §9.5 / §9.8): a field refuses here what the server would refuse, so a typo never reaches the save. The
 * server stays the authority; these numbers only have to agree with it.
 */

/** `MIN_DIMENSION_M` of `geometry.py`: the smallest height an object can have (`_HeightM`, ge). */
export const MIN_HEIGHT_M = 0.01;
/** `MAX_DIMENSION_M` of `geometry.py`: the largest height and sill height (`_HeightM`, `_SillHeightM`, le). */
export const MAX_HEIGHT_M = 1000;
/** `_SillHeightM` (ge 0): a sill may sit at floor level (a French window). */
export const MIN_SILL_HEIGHT_M = 0;
/** `LampProps.ppfd_ref` (ge 0); the model sets no upper bound, so neither does the field. */
export const MIN_PPFD = 0;
/** `DoorProps.swing` (max_length 50): bounded free text until the spec fixes a value set. */
export const MAX_SWING_LENGTH = 50;
