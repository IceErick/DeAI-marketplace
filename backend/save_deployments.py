"""Extract deployed contract addresses from Foundry's broadcast log into a JSON the app reads.

`forge script ... --broadcast` records every transaction (including CREATEs) under
broadcast/Deploy.s.sol/<chainId>/run-latest.json. This reads that file and writes a simple
{name: address} map to backend/deployments.local.json, which config.load_deployments() consumes.

    python -m backend.save_deployments            # defaults to chainId 31337 (Anvil)
    python -m backend.save_deployments 11155111   # e.g. Sepolia
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from . import config


def main(chain_id: int = 31337) -> None:
    run = config.ROOT / "broadcast" / "Deploy.s.sol" / str(chain_id) / "run-latest.json"
    if not run.exists():
        raise SystemExit(f"Broadcast log not found: {run}. Did `forge script ... --broadcast` run?")

    txs = json.loads(run.read_text()).get("transactions", [])
    addresses: dict[str, str] = {}
    for tx in txs:
        if tx.get("transactionType") == "CREATE" and tx.get("contractName") in config.CONTRACT_NAMES:
            addresses[tx["contractName"]] = tx["contractAddress"]

    missing = set(config.CONTRACT_NAMES) - addresses.keys()
    if missing:
        raise SystemExit(f"Missing addresses for {missing} in {run}")

    config.write_deployments(addresses)
    print(f"Wrote {config.DEPLOYMENTS_FILE}:")
    print(json.dumps(addresses, indent=2))


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 31337)
