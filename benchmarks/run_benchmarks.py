"""Empirical benchmark harness — collects the numbers the thesis reports.

Measures, end to end against a live Anvil node + deployed contracts:
  - gas used per on-chain operation      (cost, angle 2)
  - wall-clock latency per operation      (performance, angle 2)
  - IPFS upload/retrieval time vs file size (performance, angle 2)
  - a tamper-detection check               (integrity, angle 1)

Results are written to benchmarks/results/*.csv for plot_results.py to chart.

Prereq: `make chain` (Anvil) + `make deploy` in another terminal. Then `make benchmark`.
If those aren't up, the script prints what's missing and exits cleanly.
"""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.chain import Marketplace  # noqa: E402
from backend.ipfs_client import IPFSClient  # noqa: E402
from backend.model_hash import sha256_bytes  # noqa: E402

RESULTS = Path(__file__).resolve().parent / "results"
INFERENCE = 1 << 0  # use-type bitmask: inference only


def timed(fn):
    """Run fn, return (result, elapsed_ms)."""
    t0 = time.perf_counter()
    result = fn()
    return result, (time.perf_counter() - t0) * 1000


def bench_onchain(market: Marketplace, ipfs: IPFSClient) -> pd.DataFrame:
    """One full lifecycle, recording gas + latency for each on-chain op."""
    rows = []
    data = os.urandom(4096)  # stand-in model payload
    cid = ipfs.add_bytes(data, name="bench_model.bin")
    digest = sha256_bytes(data)

    res, ms = timed(lambda: market.register_model(cid, digest, 500))
    token_id = res.return_value
    rows.append(("registerModel", res.gas_used, ms))

    price = 10**16  # 0.01 ETH
    res, ms = timed(lambda: market.list_license(token_id, price, INFERENCE, 0))
    rows.append(("listLicense", res.gas_used, ms))

    res, ms = timed(lambda: market.purchase_license(token_id, price))
    rows.append(("purchaseLicense", res.gas_used, ms))

    res, ms = timed(lambda: market.log_usage(token_id, 0))
    rows.append(("logUsage", res.gas_used, ms))

    return pd.DataFrame(rows, columns=["operation", "gas_used", "latency_ms"])


def bench_ipfs(ipfs: IPFSClient) -> pd.DataFrame:
    """IPFS upload + retrieval time across a range of file sizes."""
    rows = []
    for kb in (1, 16, 64, 256, 1024):
        data = os.urandom(kb * 1024)
        cid, up_ms = timed(lambda d=data: ipfs.add_bytes(d, name=f"blob_{kb}k.bin"))
        _, down_ms = timed(lambda c=cid: ipfs.get_bytes(c))
        rows.append((kb, up_ms, down_ms))
    return pd.DataFrame(rows, columns=["size_kb", "upload_ms", "download_ms"])


def bench_integrity(market: Marketplace, ipfs: IPFSClient) -> pd.DataFrame:
    """Register a file, then confirm the intact hash verifies and a tampered one does not."""
    data = os.urandom(2048)
    cid = ipfs.add_bytes(data, name="integrity.bin")
    digest = sha256_bytes(data)
    res = market.register_model(cid, digest, 0)
    token_id = res.return_value

    intact_ok = market.verify(token_id, digest)
    tampered = sha256_bytes(data + b"\x00")  # one byte changed => different hash
    tampered_ok = market.verify(token_id, tampered)
    return pd.DataFrame(
        [("intact_file", intact_ok, True), ("tampered_file", tampered_ok, False)],
        columns=["case", "verify_result", "expected"],
    )


def main() -> None:
    try:
        market = Marketplace()
    except RuntimeError as e:
        print(f"[skip] {e}", file=sys.stderr)
        raise SystemExit(1)

    ipfs = IPFSClient()
    RESULTS.mkdir(parents=True, exist_ok=True)

    onchain = bench_onchain(market, ipfs)
    onchain.to_csv(RESULTS / "onchain_gas_latency.csv", index=False)
    print("\n== On-chain gas & latency ==")
    print(onchain.to_string(index=False))

    ipfs_df = bench_ipfs(ipfs)
    ipfs_df.to_csv(RESULTS / "ipfs_timing.csv", index=False)
    print("\n== IPFS timing ==")
    print(ipfs_df.to_string(index=False))

    integ = bench_integrity(market, ipfs)
    integ.to_csv(RESULTS / "integrity.csv", index=False)
    print("\n== Integrity (tamper detection) ==")
    print(integ.to_string(index=False))
    assert bool(integ.loc[integ.case == "intact_file", "verify_result"].iloc[0]) is True
    assert bool(integ.loc[integ.case == "tampered_file", "verify_result"].iloc[0]) is False
    print("\nAll results written to", RESULTS)


if __name__ == "__main__":
    main()
