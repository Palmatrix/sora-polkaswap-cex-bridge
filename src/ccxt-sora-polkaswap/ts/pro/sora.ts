
//  ---------------------------------------------------------------------------

import soraRest from '../sora.js';
import { NotSupported, ExchangeError } from '../base/errors.js';
import { sha256 } from '../static_dependencies/noble-hashes/sha256.js';
import type { Str, Balances, Dict } from '../base/types.js';
import Client from '../base/ws/Client.js';

//  ---------------------------------------------------------------------------

export default class sora extends soraRest {
    describe () {
        return this.deepExtend (super.describe (), {
            'has': {
                'ws': true,
                'watchStatus': true,
                'watchOrderBook': false,
                'watchTicker': false,
                'watchTickers': false,
                'watchOHLCV': false,
                'watchTrades': false,
                'watchBalance': false,
                'watchOrders': false,
                'watchMyTrades': false,
                'watchPositions': false,
                'watchLiquidations': false,
                'watchFundingRates': false,
                'createOrderWs': false,
                'editOrderWs': false,
                'fetchOpenOrdersWs': false,
                'fetchOrderWs': false,
                'cancelOrderWs': false,
                'cancelOrdersWs': false,
                'cancelAllOrdersWs': false,
                'fetchTradesWs': false,
                'fetchBalanceWs': true,
                'fetchMarketsWs': true,
                'fetchCurrenciesWs': true,
                'fetchOrderBookWs': false,
                'fetchTimeWs': true,
                'fetchStatusWs': true,
            },
            'urls': {
                'api': {
                    'ws': 'wss://sora.api.onfinality.io/public-ws',
                },
            },
            'options': {
                'createMarketBuyOrderRequiresPrice': true,
                'tradesLimit': 1000,
                'ordersLimit': 1000,
                'OHLCVLimit': 1000,
                'watchOrderBook': {
                    'name': 'book_lv2', // can also be 'book'
                },
                'connectionsLimit': 2000, // 2000 public, 2000 private, 4000 total, only for subscribe events, unsubscribe not restricted
                'requestsLimit': 500, // per second, only for subscribe events, unsubscribe not restricted
                'timeframes': {
                    '1m': 'candles_minute_1',
                    '5m': 'candles_minute_5',
                    '10m': 'candles_minute_10',
                    '15m': 'candles_minute_15',
                    '30m': 'candles_minute_30',
                    '1h': 'candles_hour_1',
                    '2h': 'candles_hour_2',
                    '4h': 'candles_hour_4',
                    '6h': 'candles_hour_6',
                    '12h': 'candles_hour_12',
                    '1d': 'candles_day_1',
                    '3d': 'candles_day_3',
                    '1w': 'candles_week_1',
                    '1M': 'candles_month_1',
                },
            },
            'version': '1.21',
            'streaming': {
                'keepAlive': 30000, // integer keep-alive rate in milliseconds
                'maxPingPongMisses': 2.0, // how many ping pong misses to drop and reconnect
                'ping': this.ping,
            },
        });
        // incremental data structures
        // 'orderbooks':   {}, // incremental order books indexed by symbol
        // 'ohlcvs':       {}, // standard CCXT OHLCVs indexed by symbol by timeframe
        // 'balance':      {}, // a standard CCXT balance structure, accounts indexed by currency code
        // 'orders':       {}, // standard CCXT order structures indexed by order id
        // 'trades':       {}, // arrays of CCXT trades indexed by symbol
        // 'tickers':      {}, // standard CCXT tickers indexed by symbol
        // 'transactions': {}, // standard CCXT deposits and withdrawals indexed by id or txid
    }

    async watchRequest (route, request) {
        // request['method'] = route;
        const messageHash = this.buildMessageHash (route, request);
        this.checkMessageHashDoesNotExist (messageHash);
        const url = this.urls['api']['ws'];
        return await this.watch (url, messageHash, request, messageHash);
    }

    buildRpcRequestAsJson (method, params = {}) {
        if (method === undefined) {
            throw new NotSupported (this.id + ' buildRpcRequestAsJson: no method defined');
        }
        const safeParams = this.safeValue (params, 'params', []);
        // if (safeParams === undefined) {
        //     throw new NotSupported (this.id + ' buildRpcRequestAsJson: no params defined');
        // }
        const rpcRequestAsJson = {
            'id': 1,
            'jsonrpc': '2.0',
            'method': method,
        };
        rpcRequestAsJson['params'] = safeParams;
        return JSON.stringify (rpcRequestAsJson);
    }

    buildMessageHash (method, params = {}) {
        const methods: Dict = {
            'privateCreateOrder': this.actionAndMarketMessageHash,
            'privateUpdateOrder': this.actionAndOrderIdMessageHash,
            'privateCancelOrder': this.actionAndOrderIdMessageHash,
            'privateGetOrder': this.actionAndOrderIdMessageHash,
            'privateGetTrades': this.actionAndMarketMessageHash,
        };
        const matchedMethod = this.safeValue (methods, method); // is defined for the above methods
        let messageHash = method;
        if (matchedMethod !== undefined) {
            messageHash = matchedMethod.call (this, matchedMethod, params);
        }
        return messageHash;
    }

    checkMessageHashDoesNotExist (messageHash) {
        const supressMultipleWsRequestsError = this.safeBool (this.options, 'supressMultipleWsRequestsError', false);
        if (!supressMultipleWsRequestsError) {
            const client = this.safeValue (this.clients, this.urls['api']['ws']) as Client;
            if (client !== undefined) {
                const future = this.safeValue (client.futures, messageHash);
                if (future !== undefined) {
                    throw new ExchangeError (this.id + ' a similar request with messageHash ' + messageHash + ' is already pending, you must wait for a response, or turn off this error by setting supressMultipleWsRequestsError in the options to true');
                }
            }
        }
    }

    async watchStatus (params = {}): Promise<Str> {
        const url = this.urls['api']['ws'];
        const messageHash = 'state_getRuntimeVersion';
        const abc = await this.watch (url, messageHash);
        this.log (abc);
        return abc.toString ();
    }

    async fetchBalanceWs (params = {}): Promise<Balances> {
        /**
         * @method
         * @name sora#fetchBalanceWs
         * @see ...
         * @description query for balance and get the amount of funds available for trading or funds locked in orders
         * @param {object} [params] extra parameters specific to the sora api endpoint
         * @returns {object} a [balance structure]{@link https://docs.ccxt.com/en/latest/manual.html?#balance-structure}
         */
        // await this.loadMarkets ();
        // await this.authenticate ();
        const commandRoute = 'assets_freeBalance';
        const command = this.buildRpcRequestAsJson (commandRoute, params);
        return await this.watchRequest (commandRoute, command);
    }

    parseWSBalance (message) {
        //
        //     {
        //         "channel": "balance",
        //         "reset": false,
        //         "data": {
        //             "USDT": {
        //                 "available": "15",
        //                 "total": "15"
        //             }
        //         }
        //     }
        //
        const reset = this.safeBool (message, 'reset', false);
        const data = this.safeValue (message, 'data', {});
        const currencyIds = Object.keys (data);
        if (reset) {
            this.balance = {};
        }
        for (let i = 0; i < currencyIds.length; i++) {
            const currencyId = currencyIds[i];
            const entry = data[currencyId];
            const code = this.safeCurrencyCode (currencyId);
            const account = this.account ();
            account['free'] = this.safeString (entry, 'available');
            account['total'] = this.safeString (entry, 'total');
            this.balance[code] = account;
        }
        this.balance = this.safeBalance (this.balance);
    }

    async fetchCurrenciesWs (params = {}) {
        /**
         * @method
         * @name sora#fetchCurrenciesWs
         * @see https://docs.sora.com/#tag/General/paths/~1assets/get
         * @description fetches all available currencies on an exchange
         * @param {object} [params] extra parameters specific to the sora api endpoint
         * @returns {object} an associative dictionary of currencies
         */
        await this.loadMarkets ();
        return await this.watchRequest ('getAssets', params);
    }

    actionAndMarketMessageHash (action, params = {}) {
        const symbol = this.safeString (params, 'market', '');
        return action + symbol;
    }

    actionAndOrderIdMessageHash (action, params = {}) {
        const orderId = this.safeString (params, 'orderId');
        if (orderId === undefined) {
            throw new ExchangeError (this.id + ' privateUpdateOrderMessageHash requires a orderId parameter');
        }
        return action + orderId;
    }

    handleMessage (client: Client, message) {
        // {
        //      "jsonrpc": "2.0",
        //      "method": "route_action",
        //      "params": [],
        //      "id": 1
        // }
        // {
        //      "jsonrpc": "2.0",
        //      "error":
        //          {
        //              "code": -32700,
        //              "message": "Parse error"
        //          },
        //      "id": null
        // }
        const errorValue = this.safeValue (message, 'error');
        if (errorValue !== undefined) {
            const errorCode = this.safeString (errorValue, 'code');
            const errorMessage = this.safeString (errorValue, 'message');
            const error = new ExchangeError (this.id + ' ' + errorCode + ' ' + errorMessage);
            client.reject (error);
            return;
        }
        const safeResult = this.safeValue (message, 'result', {});
        if (safeResult !== undefined) {
            const parsedBalance = this.parseBalance (safeResult);
            if (parsedBalance !== undefined) {
                // console.log ('parsedBalance', parsedBalance);
                client.resolve (parsedBalance, 'assets_freeBalance');
            }
            const safeBalanceAsFloat = this.safeFloat (safeResult, 'balance');
            if (safeBalanceAsFloat !== undefined) {
                const safeBalanceFormatted = safeBalanceAsFloat * 0.000000000000000001; // 1e-18
                client.resolve (safeBalanceFormatted, 'assets_freeBalance');
                // this.handleFetchBalance (client, message);
                // return;
            }
        }
        const errorUnknown = new NotSupported (this.id + ' handleMessage: unknown message: ' + this.json (message));
        client.reject (errorUnknown);
    }

    requestId () {
        const requestId = this.sum (this.safeInteger (this.options, 'requestId', 0), 1);
        this.options['requestId'] = requestId;
        return requestId;
    }

    handlePong (client: Client, message) {
        console.log ('handlePong', message);
        client.lastPong = this.milliseconds ();
        return message;
    }

    async authenticate (params = {}) {
        const url = this.urls['api']['ws'];
        const client = this.client (url);
        const time = this.milliseconds ();
        const timeString = this.numberToString (time);
        const nonce = timeString;
        const messageHash = 'authenticated';
        let future = this.safeValue (client.subscriptions, messageHash);
        if (future === undefined) {
            this.checkRequiredCredentials ();
            const requestId = this.requestId ();
            const signature = this.hmac (this.encode (timeString + '\n' + nonce + '\n'), this.encode (this.secret), sha256);
            const request: Dict = {
                'jsonrpc': '2.0',
                'id': requestId,
                'method': 'public/auth',
                'params': {
                    'grant_type': 'client_signature',
                    'client_id': this.apiKey,
                    'timestamp': time,
                    'signature': signature,
                    'nonce': nonce,
                    'data': '',
                },
            };
            future = await this.watch (url, messageHash, this.extend (request, params), messageHash);
            client.subscriptions[messageHash] = future;
        }
        return future;
    }
}
