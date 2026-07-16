# DeAI-marketplace — developer entrypoints.
# Run `make help` to see everything. Each target is intentionally one obvious command.

RPC_URL ?= http://127.0.0.1:8545
# Anvil's first well-known dev account (test-only key; never use on a real network).
DEPLOYER_PK ?= 0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80

.PHONY: help install install-foundry install-python chain deploy test gas fmt api ui benchmark clean

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
	  awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-16s\033[0m %s\n", $$1, $$2}'

install: install-foundry install-python ## Install all dependencies (Solidity libs + Python)

install-foundry: ## Fetch Solidity libraries (OpenZeppelin, forge-std)
	forge install foundry-rs/forge-std --no-git || true
	forge install OpenZeppelin/openzeppelin-contracts --no-git || true

install-python: ## Create a venv and install Python deps
	python3 -m venv .venv
	./.venv/bin/pip install --upgrade pip
	./.venv/bin/pip install -r backend/requirements.txt

chain: ## Start a local blockchain (Anvil) in the foreground
	anvil

deploy: ## Deploy the three contracts to $(RPC_URL) and write backend/deployments.local.json
	forge script script/Deploy.s.sol:Deploy \
	  --rpc-url $(RPC_URL) --private-key $(DEPLOYER_PK) --broadcast -vvv
	./.venv/bin/python -m backend.save_deployments

test: ## Compile + run the Foundry test suite
	forge test -vv

gas: ## Run tests with a gas report (cost & performance research angle)
	forge test --gas-report

fmt: ## Format Solidity sources
	forge fmt

api: ## Start the FastAPI backend
	./.venv/bin/uvicorn backend.api:app --reload --port 8000

ui: ## Start the Streamlit demo UI
	./.venv/bin/streamlit run ui/app.py

benchmark: ## Run the empirical benchmark harness -> benchmarks/results/*.csv
	./.venv/bin/python benchmarks/run_benchmarks.py

clean: ## Remove build artifacts
	forge clean
	rm -rf benchmarks/results/*.csv benchmarks/results/*.png examples/artifacts
