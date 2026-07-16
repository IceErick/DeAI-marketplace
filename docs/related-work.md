# Related Work / Prior Investigation

This is the literature seed for the thesis. It shows the design **builds on** prior art rather than
reinventing it, and positions the contribution.

> **Positioning.** Existing systems each solve *one* piece: marketplace fairness (Golden Grain),
> NFT-based ownership/exchange (marketplace-with-NFTs), or provenance/integrity via off-chain storage.
> **Our contribution is integrating all four angles — integrity, cost, licensing/royalties, and usage
> ethics — into one comprehensible, benchmarkable open prototype**, with an empirical evaluation of each.

BibTeX for every entry below is in [`../refs.bib`](../refs.bib). Citation keys are in `[brackets]`.

## Marketplaces for AI/ML models — angles 3 (licensing) & 2 (cost)

- **A Marketplace for Trading AI Models based on Blockchain and NFTs** `[nftmarketplace2021]` — arXiv:2112.02870.
  Represents AI models as ERC-721 NFTs stored/served via IPFS to make ownership transparent, traceable, and
  auditable. *This is the closest precedent to our `ModelRegistry` (NFT + IPFS + on-chain metadata).* We extend
  it with automated licensing, royalty splitting, and a usage audit trail.
- **Golden Grain: Building a Secure and Decentralized Model Marketplace for MLaaS** `[goldengrain2021]` —
  Weng et al., IEEE TDSC 2021 (arXiv:2011.06458). Enforces a fair "model-money swap" on Ethereum with a
  TEE-based benchmarking oracle. *Motivates our payment-fairness design and our gas/latency measurements;* we
  favour simplicity (no TEE) and instead measure cost directly.
- **Survey of Artificial Intelligence Model Marketplace** `[aimarketplacesurvey2025]` — Future Internet 2025,
  17(1):35. A taxonomy of AI model marketplaces — use it to situate our design and identify the integration gap.
- **Learning Markets: An AI Collaboration Framework Based on Blockchain and Smart Contracts** `[learningmarkets2020]` —
  smart-contract-automated model trading with game-theoretic incentives; relevant to future incentive design.

## Provenance & integrity with blockchain + off-chain storage — angles 1 & 4

- **Tamper-Evident Data and Model Provenance for IoT-Based ML Using Blockchain and Off-Chain Storage**
  `[tamperevident2026]` — MDPI Information 2026, 17(5):499. Merkle-tree hashing + compact on-chain metadata +
  off-chain store. *Directly validates our "hash on-chain, file off-chain (IPFS)" integrity approach.*
- **Cloud Data Provenance using IPFS and Blockchain Technology** `[ipfsprovenance2019]` — ACM SCC 2019. A
  foundational IPFS+blockchain provenance pattern we reuse for model files.

## Standards we implement — angles 1, 3, 4

- **EIP-721: Non-Fungible Token Standard** `[eip721]` — the ownership primitive; each model = one NFT.
- **EIP-2981: NFT Royalty Standard** `[eip2981]` — the royalty-signalling primitive our `Licensing` acts on.
  Note: ERC-2981 only *signals* royalties; enforcement is our contract's job (discuss as a limitation).

## Background survey — framing

- **On the Convergence of AI and Distributed Ledger Technology: A Scoping Review and Future Research Agenda**
  `[aidltscoping2020]` — arXiv:2001.11017. Broad AI × blockchain landscape for the introduction.

---

### ⚠️ Verification note

Titles, venues, and URLs above were confirmed via literature search. **Author lists and exact years for a few
entries (`aimarketplacesurvey2025`, `tamperevident2026`, `ipfsprovenance2019`, `learningmarkets2020`,
`aidltscoping2020`) were not fully resolved and are marked `TODO` in `refs.bib` — verify them against the
source PDF before submitting.** Do not cite an author list you have not checked.
