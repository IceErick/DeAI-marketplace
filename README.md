# DeAI-marketplace

A **decentralized AI model sharing platform with blockchain security**. Blockchain stores immutable
metadata (ownership, provenance, licensing, usage); smart contracts automate licensing and royalty
payments; the actual model files live on IPFS. Built as an **empirical research** prototype evaluating
four angles: **integrity & security, cost & performance, licensing & royalties, and usage tracking & ethics**.

> **Stack (intentionally comprehensible):** Solidity + OpenZeppelin contracts, tested & gas-benchmarked
> with **Foundry**; **IPFS** for model files; **Python** (web3.py + FastAPI + Streamlit) as the glue and UI;
> pandas/matplotlib for the research metrics. No JavaScript/TypeScript.

## Mental model

- **Blockchain = notary + cashier** — immutable records, ownership (NFTs), licensing, royalties, usage log.
- **IPFS = warehouse** — the actual model bytes (chain stores only the content id + a SHA-256 hash).
- **Python = clerk** — moves data between user, IPFS, and chain; hashes files; runs benchmarks.

## Contracts

| Contract | Purpose | Research angle |
|---|---|---|
| [`ModelRegistry.sol`](contracts/ModelRegistry.sol) | Model = ERC-721 NFT; stores CID + SHA-256 hash + version; ERC-2981 royalties; `verify()` | integrity, provenance |
| [`Licensing.sol`](contracts/Licensing.sol) | List & purchase licenses; auto-split payment (creator/platform/owner); allowed-use bitmask | licensing & royalties |
| [`UsageLog.sol`](contracts/UsageLog.sol) | License-gated, append-only usage audit trail | usage tracking & ethics |

## Quickstart

```sh
make install        # Solidity libs + Python venv
make gas            # compile + test + per-operation gas report
make chain          # (terminal A) local Anvil blockchain
make deploy         # (terminal B) deploy contracts
make ui             # Streamlit demo: upload → register → verify → license → usage
make benchmark      # collect research CSVs -> benchmarks/results/
```

Full instructions: [docs/setup.md](docs/setup.md).

## Documentation

- [docs/architecture.md](docs/architecture.md) — system design + diagrams
- [docs/research-methodology.md](docs/research-methodology.md) — what each angle measures & how to reproduce
- [docs/related-work.md](docs/related-work.md) — literature review (BibTeX in [refs.bib](refs.bib))
- [docs/setup.md](docs/setup.md) — setup & run

## Status

Milestone 1 (this repo): **architecture + runnable scaffold + docs**. Contracts compile with a passing
sanity test suite; Python helpers, a thin API/UI, and a benchmark harness are in place. Next milestones:
full contract logic + coverage, end-to-end UI, and a public-testnet deployment with full benchmark runs.
See the roadmap in [docs/research-methodology.md](docs/research-methodology.md).
