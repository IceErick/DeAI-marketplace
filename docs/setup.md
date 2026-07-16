# Setup & Run

Step-by-step for a fresh machine. Everything is driven by `make` — run `make help` to list targets.

## Prerequisites

1. **Foundry** (Solidity toolchain: `forge`, `anvil`, `cast`):
   ```sh
   curl -L https://foundry.paradigm.xyz | bash
   foundryup
   ```
2. **Python 3.11+** (for the integration layer, UI, and benchmarks).
3. **IPFS (Kubo)** — *optional*. Without it, `ipfs_client` uses a local mock store so everything still runs.
   Install from https://docs.ipfs.tech/install/ and run `ipfs daemon` for real IPFS numbers.

## First-time install

```sh
make install        # forge install (OpenZeppelin, forge-std) + python venv + pip install
```

## Compile & test (no chain needed)

```sh
make test           # forge build + run the Solidity test suite
make gas            # same, with a per-operation gas report (research angle 2)
```

## Run the full stack locally

Open two terminals:

```sh
# Terminal A — local blockchain
make chain          # starts Anvil on http://127.0.0.1:8545 with funded dev accounts

# Terminal B — deploy + drive
make deploy         # deploys the 3 contracts, writes backend/deployments.local.json
python -m examples.make_demo_model   # create a real demo model artifact
make ui             # open the Streamlit demo (upload → register → verify → license → usage)
# or:
make api            # start the FastAPI backend, then browse http://127.0.0.1:8000/docs
```

## Collect research data

```sh
make benchmark                    # writes benchmarks/results/*.csv
python -m benchmarks.plot_results # renders PNG figures from those CSVs
```

## Troubleshooting

- **`ABI ... not found`** → run `make test` (or `forge build`) so `out/` exists.
- **`No deployed addresses found`** → run `make deploy` (needs Anvil running via `make chain`).
- **IPFS shows "mock mode"** → no daemon reachable; fine for demos, but start `ipfs daemon` for real timings.
- **`forge: command not found`** → run `foundryup`, then restart your shell.
