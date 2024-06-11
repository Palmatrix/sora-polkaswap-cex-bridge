const { Keyring } = require('@polkadot/keyring');
const { ApiPromise, WsProvider } = require('@polkadot/api');

async function main() {
  // Create a new Keyring instance
  const keyring = new Keyring({ type: 'sr25519' });

  // Add a new pair from the public key
  const pair = keyring.addFromAddress('5GKYWEZweDPF7G9BQBcxj9o869xCrYnCgtkVZzJ8ssPBgsx7');

  console.log(`Public Key (Wallet Address): ${pair.address}`);

  // Connect to the SORA node
  const provider = new WsProvider('wss://sora.api.onfinality.io/public-ws');
  const api = await ApiPromise.create({ provider });

  // Query the balance of the wallet
  const { data: balance } = await api.query.system.account(pair.address);

  console.log(`Balance: ${balance.free}`);
}

main().catch(console.error);
