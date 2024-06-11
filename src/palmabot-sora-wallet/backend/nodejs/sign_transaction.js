// Import the necessary classes from the Polkadot API
const { ApiPromise, WsProvider, Keyring } = require('@polkadot/api');
const { cryptoWaitReady } = require ('@polkadot/util-crypto');

async function signTransaction(mnemonic, recipient, tokenId, amount) {

            try {
                // Ensure crypto libraries are initialized
                await cryptoWaitReady();

                // Initialize the provider to connect to the node
                const wsProvider = new WsProvider('wss://sora.api.onfinality.io/public-ws'); // Replace with your node's WS endpoint

                // Create the API instance
                const api = await ApiPromise.create({ provider: wsProvider });

                // Create a keyring instance
                const keyring = new Keyring({ type: 'sr25519' });

                // Add an account to the keyring (using a mnemonic phrase)
                const sender = keyring.addFromUri(mnemonic);

                // Create the token transfer transaction
                const transfer = await api.tx.assets.transfer(tokenId, recipient, amount);

                // Sign and send the transaction
                const hash = await transfer.signAndSend(sender, ({ status }) => {
                    if (status.isInBlock) {
                        document.getElementById('status').innerText = `Transaction included at blockHash ${status.asInBlock}`;
                    } else if (status.isFinalized) {
                        document.getElementById('status').innerText = `Transaction finalized at blockHash ${status.asFinalized}`;
                    }
                });

                console.log(`Transaction hash: ${hash}`);
            } catch (error) {
                console.error('Failed to send token:', error);
                alert(`Failed to send token: ${error.message}`);
            }
}
window.signTransaction = signTransaction;
