// Tests des briques JavaScript (lancés par autotest_fabrique.py) : node test_briques.js
const assert = require('node:assert');
const { reconnaitreVersion } = require('./entrees.js');
const { produitAvec, empreinte } = require('./tracabilite.js');
const VERSIONS = { 'Trame 2026': ['Code station', 'Date du bilan', 'Débit entrée'], 'Trame 2025': ['Code station', 'Date', 'Débit'] };
(async () => {
  assert.strictEqual(reconnaitreVersion(['code  STATION', 'Date du bilan', 'Debit entree'], VERSIONS).version, 'Trame 2026');
  assert.throws(() => reconnaitreVersion(['Code station', 'Date du bilan'], VERSIONS), /Trame 2026.*Débit entrée.*référent/s);
  const mention = produitAvec('bilan réglementaire', '1.2.0', [{ nom: 'trame.xlsx', empreinte: '1a2b3c4d' }], new Date(2026, 10, 15));
  assert.ok(mention.startsWith('Produit avec bilan réglementaire v1.2.0 le 15/11/2026 à partir de : trame.xlsx (1a2b3c4d)'), mention);
  assert.strictEqual((await empreinte('abc')).length, 8);
  console.log('briques JavaScript : tout est bon');
})().catch(e => { console.error(e); process.exit(1); });
