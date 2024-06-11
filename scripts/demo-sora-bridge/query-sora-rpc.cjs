// Import the necessary libraries
const ccxt = require ('ccxt').pro;
// const log = require ('ololog');

async function querySoraRpc() {
    // {
    //     "jsonrpc": "2.0",
    //     "method": "route_action",
    //     "params": [],
    //     "id": 1
    // }
    let exchange = new ccxt.sora({ 'verbose': true, 'newUpdates': false });
    if (!exchange.has['fetchBalanceWs']) {
        throw new Error('fetchBalanceWs not supported');
    }
    //console.log('URL:', exchange.urls['api']); // Print the available URLs
    let params = ["XORWalletAddressHere", "0x0200000000000000000000000000000000000000000000000000000000000000"];
    let fetchResult = await exchange.fetchBalanceWs({ params });
    let formattedResult = fetchResult.info.balance * 1e-21; // Convert to XOR 10^18 +k
    console.log('Balance:', formattedResult, 'kXOR');
    await exchange.close();
}

async function queryFeatureSupported() {
    let exchange = new ccxt.sora();
    if (exchange.has['watchBalance']) {
        while (true) {
            try {
                const balance = await exchange.watchBalance (params);
                console.log (new Date (), balance);
                exchange.delay(1000);
            } catch (e) {
                console.log (e);
                // stop the loop on exception or leave it commented to retry
                // throw e
            }
        }
    }else{
        console.log('watchBalance not supported');
    }
}

async function testSoraRpc() {
    querySoraRpc().catch(console.error);
    // queryFeatureSupported().catch(console.error);
}  

// Run the test
testSoraRpc().catch(console.error);