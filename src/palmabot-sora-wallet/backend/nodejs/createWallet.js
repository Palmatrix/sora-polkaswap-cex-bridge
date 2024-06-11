const { randomAsHex, mnemonicGenerate, mnemonicToMiniSecret, cryptoWaitReady } = require('@polkadot/util-crypto');
const { Keyring } = require('@polkadot/keyring');

// Wait for the promise to resolve before using the crypto libraries
cryptoWaitReady().then(async () => {
  // Generate a mnemonic for the wallet
  const mnemonic = mnemonicGenerate();

  // Create a new Keyring instance
  const keyring = new Keyring({ type: 'sr25519' });

  // Add a new pair from the mnemonic
  const pair = keyring.addFromUri(mnemonic);

  // Get the seed from the mnemonic
  const seed = mnemonicToMiniSecret(mnemonic);

  console.log(`Mnemonic: ${mnemonic}`);
  console.log(`Public Key (Wallet Address): ${pair.address}`);
  console.log(`Seed: ${Buffer.from(seed).toString('hex')}`);

});
