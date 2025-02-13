#!/bin/bash
set -e

mkdir -p /cartesi-lambada-coprocessor/env/
rm -rf /cartesi-lambada-coprocessor/env/devnet-operators-ready.flag
rm -rf /cartesi-lambada-coprocessor/contracts/logs
rm -rf /cartesi-lambada-coprocessor/contracts/out
rm -rf /cartesi-lambada-coprocessor/contracts/cache
rm -rf /cartesi-lambada-coprocessor/contracts/broadcast
mkdir -p /cartesi-lambada-coprocessor/contracts/logs
# revet to time 12
anvil --load-state /root/.anvil/state.json --host 0.0.0.0 --block-time 1 > /cartesi-lambada-coprocessor/contracts/logs/anvil.log 2>&1 &
timeout 22 bash -c 'until curl -s -X POST http://localhost:8545 -H "Content-Type: application/json" --data '"'"'{"jsonrpc":"2.0","method":"eth_blockNumber","params":[],"id":83}'"'"' >> /dev/null ; do sleep 1 && echo "wait"; done'
curl -s -X POST http://localhost:8545 -H "Content-Type: application/json" --data '{"jsonrpc":"2.0","method":"evm_mine","params":[],"id":82}' >> /dev/null

cast send \
    --rpc-url http://0.0.0.0:8545 \
    --private-key 0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80 \
    --value 30ether 0x02C9ca5313A6E826DC05Bbe098150b3215D5F821

cast send \
    --rpc-url http://0.0.0.0:8545 \
    --private-key 0xc276a0e2815b89e9a3d8b64cb5d745d5b4f6b84531306c97aad82156000a7dd7 \
    0xc5a5C42992dECbae36851359345FE25997F5C42d "mint(address,uint256)" 0x02C9ca5313A6E826DC05Bbe098150b3215D5F821 20

cast send \
    --rpc-url http://0.0.0.0:8545 \
    --private-key 0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80 \
    --value 30ether 0x71f897938C155D4569b9f8fbff8fBFC7A89069Fb

cast send \
    --rpc-url http://0.0.0.0:8545 \
    --private-key 0x850affd0f354c8b3b3176ae914dcd90cdb0f2051d1c5e31c9bbf97a732b68a07 \
    0xc5a5C42992dECbae36851359345FE25997F5C42d "mint(address,uint256)" 0x71f897938C155D4569b9f8fbff8fBFC7A89069Fb 20

cast send \
    --rpc-url http://0.0.0.0:8545 \
    --private-key 0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80 \
    --value 30ether 0xEc1dc4D2a9459758DCe2bb13096F303a8FAF4c92

cast send \
    --rpc-url http://0.0.0.0:8545 \
    --private-key 0xa38181ab9321e4bfdfe8dae9f99b05529483bdf0254bd5bcbcc51232f26b8c36 \
    0xc5a5C42992dECbae36851359345FE25997F5C42d "mint(address,uint256)" 0xEc1dc4D2a9459758DCe2bb13096F303a8FAF4c92 20

rm -f /root/.eigenlayer/operator_keys/foo.ecdsa.key.json
echo "abcd" | /usr/local/bin/eigenlayer-orig keys import -i -k ecdsa foo  0xc276a0e2815b89e9a3d8b64cb5d745d5b4f6b84531306c97aad82156000a7dd7 2>&1 | tee /import.log
echo "abcd" | /usr/local/bin/eigenlayer-orig operator register /cartesi-lambada-coprocessor/operator-devnet.yaml 2>&1 | tee /register.log

STRATEGY_MANAGER=$(jq -r .strategyManager < /cartesi-lambada-coprocessor/deployment_parameters_devnet.json)
STRATEGY_ADDRESS=$(jq -r .addresses.erc20MockStrategy < /cartesi-lambada-coprocessor/coprocessor_deployment_output_devnet.json )
STRATEGY_UNDERLYING=$(cast call --rpc-url http://0.0.0.0:8545 $STRATEGY_ADDRESS "underlyingToken()(address)")

cast send --rpc-url http://0.0.0.0:8545 --private-key 0xc276a0e2815b89e9a3d8b64cb5d745d5b4f6b84531306c97aad82156000a7dd7 $STRATEGY_UNDERLYING "approve(address,uint256)" $STRATEGY_MANAGER 10
cast send --rpc-url http://0.0.0.0:8545 --private-key 0xc276a0e2815b89e9a3d8b64cb5d745d5b4f6b84531306c97aad82156000a7dd7 $STRATEGY_MANAGER "depositIntoStrategy(address,address,uint256)" $STRATEGY_ADDRESS $STRATEGY_UNDERLYING 10

cast rpc anvil_mine 200 --rpc-url http://localhost:8545 > /dev/null

touch /cartesi-lambada-coprocessor/env/devnet-operators-ready.flag

tail -f /cartesi-lambada-coprocessor/contracts/logs/anvil.log
