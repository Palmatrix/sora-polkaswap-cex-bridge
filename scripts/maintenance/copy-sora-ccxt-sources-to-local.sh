#!/usr/bin/env bash

echo "Copying the Sora CCXT sources to the local repository..."

cp /ccxt/ts/ccxt.ts /pmx-dev/src/ccxt-sora-polkaswap/ccxt.ts
cp /ccxt/ts/src/sora.ts /pmx-dev/src/ccxt-sora-polkaswap/ts/sora.ts
cp /ccxt/ts/src/pro/sora.ts /pmx-dev/src/ccxt-sora-polkaswap/ts/pro/sora.ts
cp /ccxt/ts/src/abstract/sora.ts /pmx-dev/src/ccxt-sora-polkaswap/ts/abstract/sora.ts

echo ...done!