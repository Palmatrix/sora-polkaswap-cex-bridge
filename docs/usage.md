# How to use this repository

## Projects

### ccxt-sora-polkaswap

tldr; creating SORA Network ccxt component, basically mapping out all sora endpoints into their (ccxt's) unified api and custom extensions

files: /src/ccxt-sora-polkaswap

state: prototype, working sample with connect,command,response PoC to sora endpoints

comment:  

usage:  
    - build Dockerfile  
    - mount/terminal to container /ccxt  

- execute in terminal.  
Compiles ccxt + sora sources.  
Sources can also be found in /src/ccxt-sora-polkaswap
```sh
npm run build
```

run sora exchange demo.
```sh
./scripts/demo-sora-bridge/run-demo.sh
```

### palmabot-sora-wallet

tldr; Palmatrix Palmabot Virtual Assistant bridging SORA Network, enabling shared business interests

files: /src/palmabot-sora-wallet

state: prototype

comment: no build scripts yet, need to create environment manually

usage: the /backend is node.js driven

### soratrix cdex bridge

tldr; A financial market intermediary backend for the next evolution in digital integration. targetting FSPAAS products for B2B and B2C.

files: /specs/openapi.spec.json

state: conceptual

comment: continues in Phase 2

usage: -