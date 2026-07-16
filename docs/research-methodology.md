# Research Methodology

This is an **empirical research** project: the deliverable is not just a system but *measurements* that
support claims about it. This document maps each research angle to a concrete mechanism, the metric(s)
we collect, and how to reproduce them.

## Research questions

- **RQ1 (Integrity & security).** Can blockchain-anchored hashing reliably detect unauthorized
  modification of shared AI models, and establish provenance/ownership?
- **RQ2 (Cost & performance).** What are the gas costs, transaction latencies, and IPFS transfer times of
  the core operations, and how do they scale with model size?
- **RQ3 (Licensing & royalties).** Can smart contracts correctly and automatically enforce licensing terms
  and split royalty payments across realistic scenarios?
- **RQ4 (Usage tracking & ethics).** Can the system produce a complete, tamper-evident audit trail of model
  usage and enforce machine-checkable allowed-use constraints?

## Angle → mechanism → metric

| Angle | Mechanism in the code | Metric(s) | Where measured |
|---|---|---|---|
| 1. Integrity & security | `ModelRegistry.verify()` vs SHA-256 re-hash; ERC-721 ownership | tamper-detection correctness (should be 100% by construction); ownership transfer correctness | `benchmarks/run_benchmarks.py::bench_integrity`, `test/ModelRegistry.t.sol` |
| 2. Cost & performance | all on-chain ops; IPFS add/cat | gas per op; tx latency (ms); IPFS upload/download time vs size | `bench_onchain`, `bench_ipfs`; `forge test --gas-report` |
| 3. Licensing & royalties | `Licensing.purchaseLicense` payment split; expiry | payout correctness; gas per purchase; behaviour on expiry/wrong price | `test/Licensing.t.sol`, `bench_onchain` |
| 4. Usage tracking & ethics | `UsageLog.logUsage` gated by license + use-type bitmask | audit-trail completeness (events == uses); rejection of unlicensed/disallowed uses | `test/UsageLog.t.sol` |

## Use-type encoding (angle 4)

Allowed uses are a 32-bit bitmask on each license. The application-level enum:

| Bit | Use type | Meaning |
|---|---|---|
| 0 | inference | run the model to get predictions |
| 1 | fine-tuning | further-train / derive a new model |
| 2 | redistribution | share the model onward |

`logUsage(tokenId, useType)` reverts unless the caller's license has the corresponding bit set — this is how
"ethical / permitted use" is made machine-checkable rather than a paper policy.

## Experiment protocol (reproducible)

1. `make install` — install Foundry libs + Python deps.
2. `make gas` — record per-operation gas from the Foundry gas report (RQ2, deterministic).
3. `make chain` (terminal A) and `make deploy` (terminal B) — bring up a local chain with contracts.
4. `python -m examples.make_demo_model` — create a real model artifact.
5. `make benchmark` — writes `benchmarks/results/{onchain_gas_latency,ipfs_timing,integrity}.csv`.
6. `python -m benchmarks.plot_results` — render figures for the write-up.
7. Repeat step 5 N times (e.g. 30) to report mean ± std for latency/IPFS timing (latency varies; gas does not).

## Threats to validity (discuss in the thesis)

- **Latency on a local Anvil node** is near-instant and *not* representative of a public network; report
  local numbers for cost, but note real-network latency/finality differs (a later milestone deploys to a testnet).
- **IPFS timing** depends on daemon config and peer availability; the mock store bypasses the network — use a
  real Kubo daemon for reported IPFS numbers.
- **Tamper detection is correct by construction** (a hash comparison), so RQ1's quantitative result is a
  demonstration, not a statistical finding — frame it accordingly.
- **Royalty enforcement** is guaranteed only within this platform's Licensing contract, not across external
  marketplaces (ERC-2981 is advisory). This bounds the IP-theft claim.

See [related-work.md](related-work.md) for prior systems each of these builds on.
