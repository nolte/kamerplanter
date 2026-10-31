import { describe, expect, it } from 'vitest';
import { isTempKey, newTempKey } from './planModel';

describe('isTempKey', () => {
  it('recognises every key newTempKey makes', () => {
    for (let index = 0; index < 50; index += 1) expect(isTempKey(newTempKey())).toBe(true);
  });

  it.each(['loc_a', '12345', 'tmp_unsaved', 'tmpl-1', 'tmp', 'Tmp1abc'])('does not take the server key %s for a temp key', (key) => {
    expect(isTempKey(key)).toBe(false);
  });
});
