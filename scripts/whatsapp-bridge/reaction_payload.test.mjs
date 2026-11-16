import test from 'node:test';
import assert from 'node:assert/strict';

import { buildReactionPayload } from './bridge_helpers.js';

test('DM reaction targets the inbound message without a participant', () => {
  const key = { remoteJid: '1@lid', id: 'ABC', participant: '1@lid', fromMe: false };
  assert.deepEqual(buildReactionPayload({ chatId: '1@lid', key, emoji: '👀' }),
    { react: { text: '👀', key: { remoteJid: '1@lid', id: 'ABC', fromMe: false } } });
});

test('group reaction keeps the sender participant', () => {
  const key = { remoteJid: '9-1@g.us', id: 'X', participant: '5@lid', fromMe: false };
  assert.equal(buildReactionPayload({ chatId: '9-1@g.us', key, emoji: '✅' }).react.key.participant, '5@lid');
});

test('empty emoji removes; own or keyless messages are refused', () => {
  assert.equal(buildReactionPayload({ chatId: '1@lid', key: { id: 'A' }, emoji: '' }).react.text, '');
  assert.equal(buildReactionPayload({ chatId: '1@lid', key: { id: 'A', fromMe: true }, emoji: '👀' }), null);
  assert.equal(buildReactionPayload({ chatId: '1@lid', key: {}, emoji: '👀' }), null);
});
