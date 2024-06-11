$( document ).ready(function() {

        // const { ApiPromise, WsProvider, Keyring } = polkadotApi;
        // const { cryptoWaitReady } = polkadotUtilCrypto;

        $(document).on('click', '#my_submit', async function(event) {

            // // get mnemonic from local storage
            const mnemonic = localStorage.getItem('wallet_seed');
            const recipient = document.getElementById('address_to').value;
            const tokenId =  document.getElementById('token_id').value;
            const amount =  document.getElementById('amount').value;

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
                console.log(api);
                const transfer = await api.tx.assets.transfer(tokenId, recipient, amount);

                // Sign and send the transaction
                const hash = transfer.signAndSend(sender, ({ status }) => {
                    if (status.isInBlock) {
                        document.getElementById('status').innerText = `Transaction included at blockHash ${status.asInBlock}`;
                    } else if (status.isFinalized) {
                        document.getElementById('status').innerText = `Transaction finalized at blockHash ${status.asFinalized}`;
                    }
                });

                console.log(`Transaction hash: ${hash}`);
            } catch (error) {
                console.error('Failed to send token:', error);
                document.getElementById('status').innerText = `Error: ${error.message}`;
            }
        });
});
