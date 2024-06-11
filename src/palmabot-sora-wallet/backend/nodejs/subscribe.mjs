const { randomAsHex, mnemonicGenerate, mnemonicToMiniSecret, cryptoWaitReady } = require('@polkadot/util-crypto');
const { Keyring } = require('@polkadot/keyring');
const { ApiPromise, WsProvider } = require('@polkadot/api');

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

  // Connect to the SORA node
  const provider = new WsProvider('ws://your-sora-node:9944');
  const api = await ApiPromise.create({ provider });

  // Query the balance of the wallet
  const { data: balance } = await api.query.system.account(pair.address);

  console.log(`Balance: ${balance.free}`);
});