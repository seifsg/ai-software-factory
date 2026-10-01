import assert from 'node:assert/strict';
import {normalizeTitle, readTasks} from '../model.mjs';

assert.equal(normalizeTitle('   '), '', 'Whitespace-only titles must be rejected');
assert.equal(normalizeTitle('  Ship the feature  '), 'Ship the feature');
assert.equal(normalizeTitle('Write notes'), 'Write notes');
assert.deepEqual(readTasks({getItem: () => '{broken'}), []);
assert.deepEqual(readTasks({getItem: () => '["Task",2]'}), ['Task']);
console.log('PASS: title validation and existing storage behavior');
