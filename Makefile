# Makefile

ENVFILE := .env
SHELL := /bin/bash

CONTRACT_ADDRESS ?= 0xb8B2292b361931AEa8D1A9b3C062a68730Be4056

up: llama-model
	docker compose up -d
	docker compose up -d llama-server

down:
	docker compose down -v
	docker compose down -v llama-server

build: .cartesi/image/hash

.cartesi/image/hash:
	cartesi build

rebuild:
	rm -rf .cartesi
	cartesi build

.cartesi/output.cid: .cartesi/image/hash
	docker run --rm -v ${PWD}/.cartesi/image:/data -v ${PWD}/.cartesi:/output ghcr.io/zippiehq/cartesi-carize:latest \
	 bash -c "/carize.sh && chown $(id -u):$(id -g) /output/output.*"

#.cartesi/image/hash
build-contract:
	cd contracts && forge install --no-commit
	cd contracts && forge build --via-ir

deploy-contract: --load-env .cartesi/image/hash build-contract
	cd contracts && TASK_ISSUER=${TASK_ISSUER} PRIVATE_KEY=${PRIVATE_KEY} MACHINE_HASH=0x$(shell xxd -p -c32 .cartesi/image/hash) forge script script/Deploy.s.sol --rpc-url ${RPC_URL} --broadcast --via-ir

send: --load-env
	cast send --private-key=${PRIVATE_KEY} --rpc-url ${RPC_URL} ${CONTRACT_ADDRESS} "runExecution(bytes)" ${PAYLOAD}

--load-env: ${ENVFILE}
	$(eval include include $(PWD)/${ENVFILE})

${ENVFILE}:
	@test ! -f $@ && echo "$(ENVFILE) not found. Creating with default values"
	echo PRIVATE_KEY='0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80' >> $(ENVFILE)
	echo RPC_URL=http://127.0.0.1:8545 >> $(ENVFILE)
	echo TASK_ISSUER=0x95401dc811bb5740090279Ba06cfA8fcF6113778 >> $(ENVFILE)

.cartesi/presigned:
	curl -s -X POST "http://127.0.0.1:3034/upload" -d "{}" 2> /dev/null > .cartesi/presigned

# presigned = $(eval presigned := $$(shell \
# 	 cat .cartesi/presigned))$(presigned)

publish: .cartesi/output.cid .cartesi/presigned
	@curl -s -X PUT "$(shell cat .cartesi/presigned | jq -r '.presigned_url' | sed 's/solver-bucket.localstack:4566/localhost:4566\/solver-bucket/')" -H "Content-Type: application/octet-stream" --data-binary "@.cartesi/output.car"
	@curl -s -X POST "http://127.0.0.1:3034/publish/$(shell cat .cartesi/presigned | jq -r '.upload_id')" -d "{}" | jq
	@echo -e "Publishing.\nRun 'make publish-status' to check the upload status, and when it is complete run 'make ensure-publish' to register the app"

publish-status: .cartesi/output.cid .cartesi/presigned
	@curl -s -X GET "http://127.0.0.1:3034/publish_status/$(shell cat .cartesi/presigned | jq -r '.upload_id')" | jq
	@echo -e "\nRun 'make ensure-publish' to register the app when it is complete"

ensure-publish: .cartesi/output.cid .cartesi/presigned
	@curl -s -X POST "http://127.0.0.1:3034/ensure/$(shell cat .cartesi/output.cid)/$(shell xxd -p -c32 .cartesi/image/hash)/$(shell cat .cartesi/output.size)" | jq

--load-env-%: ${ENVFILE}.%
	@$(eval include include $^)

${ENVFILE}.%:
	test ! -f $@ && $(error "file $@ doesn't exist")

#.cartesi/image/hash
deploy-contract-%: ${ENVFILE}.% .cartesi/image/hash build-contract
	@$(eval include include $<)
	cd contracts && TASK_ISSUER=${TASK_ISSUER} PRIVATE_KEY=${PRIVATE_KEY} MACHINE_HASH=0x$(shell xxd -p -c32 .cartesi/image/hash) forge script script/Deploy.s.sol --rpc-url ${RPC_URL} --broadcast --via-ir

send-%: ${ENVFILE}.%
	@$(eval include include $<)
	cast send --private-key=${PRIVATE_KEY} --rpc-url ${RPC_URL} ${CONTRACT_ADDRESS} "runExecution(bytes)" ${PAYLOAD}

.cartesi/presigned-%: ${ENVFILE}.%
	@$(eval include include $<)
	curl  -X POST "${SOLVER_URL}/upload" -d "{}" 2> /dev/null > $@

publish-%: ${ENVFILE}.% .cartesi/presigned-% .cartesi/output.cid
	@$(eval include include $<)
	curl  -X PUT "$(shell cat $(word 2,$^) | jq -r '.presigned_url')" -H "Content-Type: application/octet-stream" --data-binary "@.cartesi/output.car"
	curl  -X POST "${SOLVER_URL}/publish/$(shell cat $(word 2,$^) | jq -r '.upload_id')" -d "{}" | jq
	echo -e "Publishing.\nRun 'make publish-status-%' to check the upload status, and when it is complete run 'make ensure-publish-%' to register the app"

publish-status-%: ${ENVFILE}.% .cartesi/presigned-% .cartesi/output.cid
	@$(eval include include $<)
	@curl -s -X GET "${SOLVER_URL}/publish_status/$(shell cat $(word 2,$^) | jq -r '.upload_id')" | jq
	@echo -e "\nRun 'make ensure-publish' to register the app when it is complete"

ensure-publish-%: ${ENVFILE}.% .cartesi/output.cid
	@$(eval include include $<)
	@curl -s -X POST "${SOLVER_URL}/ensure/$(shell cat .cartesi/output.cid)/$(shell xxd -p -c32 .cartesi/image/hash)/$(shell cat .cartesi/output.size)" | jq

llama-model: llama/models/Phi-3-mini-4k-instruct-q4.gguf

llama/models/Phi-3-mini-4k-instruct-q4.gguf:
	mkdir -p llama/models
	wget -q https://huggingface.co/microsoft/Phi-3-mini-4k-instruct-gguf/resolve/main/Phi-3-mini-4k-instruct-q4.gguf \
	 -O llama/models/Phi-3-mini-4k-instruct-q4.gguf
