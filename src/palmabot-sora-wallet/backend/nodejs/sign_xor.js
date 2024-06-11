// Import required libraries
const { ApiPromise, WsProvider, Keyring } = require('@polkadot/api');
const { cryptoWaitReady } = require('@polkadot/util-crypto');

async function main() {
    // Initialize the provider to connect to the node
    const wsProvider = new WsProvider('wss://sora.api.onfinality.io/public-ws'); // Replace with your node's WS endpoint

    // Create the API instance
    const api = await ApiPromise.create({ provider: wsProvider });

    // Ensure crypto libraries are initialized
    await cryptoWaitReady();

    // Create a keyring instance
    const keyring = new Keyring({ type: 'sr25519' });

    // Add an account to the keyring (using a mnemonic phrase)
    const mnemonic = 'benefit morning pool cabbage open mixture stick essence today region chair ten';
    const sender = keyring.addFromUri(mnemonic);

    // Define the recipient address, token ID, and the amount to send
    const recipient = 'cnTkZUJ6pea12szis2uHu1LU7LtqP2PRZq2PYALsCCQxg73VP';
    const tokenId = '0x0200000000000000000000000000000000000000000000000000000000000000'; // XOR
    const amount = 15; // Amount in the smallest unit of the token

    // Create the token transfer transaction
    const transfer = api.tx.assets.transfer(tokenId, recipient, amount);

    // Sign and send the transaction
    const hash = await transfer.signAndSend(sender, ({ status }) => {
        if (status.isInBlock) {
            console.log(`Transaction included at blockHash ${status.asInBlock}`);
        } else if (status.isFinalized) {
            console.log(`Transaction finalized at blockHash ${status.asFinalized}`);
        }
    });

    console.log(`Transaction hash: ${hash}`);
}

main().catch(console.error).finally(() => process.exit());
