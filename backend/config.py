"""Central configuration + deployed-address loading.

Everything the Python layer needs to know about *where* things live is here, so no other
module hard-codes a URL or an address. Values come from environment variables (with sensible
local-dev defaults) and, for contract addresses, from the JSON that `forge script` writes on deploy.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

# --- Endpoints -------------------------------------------------------------------------------
# Local Anvil node by default.
RPC_URL: str = os.environ.get("DEAI_RPC_URL", "http://127.0.0.1:8545")

# Kubo (go-ipfs) HTTP API. If no daemon is running, ipfs_client falls back to a local mock store.
IPFS_API_URL: str = os.environ.get("DEAI_IPFS_API", "http://127.0.0.1:5001")

# Anvil's first well-known dev account. TEST ONLY — never use this key on a real network.
DEFAULT_PRIVATE_KEY: str = os.environ.get(
    "DEAI_PRIVATE_KEY",
    "0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80",
)

# --- Paths -----------------------------------------------------------------------------------
ROOT: Path = Path(__file__).resolve().parent.parent
OUT_DIR: Path = ROOT / "out"  # Foundry compilation artifacts (ABIs live here)
DEPLOYMENTS_FILE: Path = ROOT / "backend" / "deployments.local.json"

CONTRACT_NAMES = ("ModelRegistry", "Licensing", "UsageLog")


def load_deployments() -> dict[str, str]:
    """Return {contract_name: address}. Written by the deploy step (see write_deployments)."""
    if DEPLOYMENTS_FILE.exists():
        return json.loads(DEPLOYMENTS_FILE.read_text())
    return {}


def write_deployments(addresses: dict[str, str]) -> None:
    """Persist deployed addresses so the API/UI/benchmarks can find the contracts."""
    DEPLOYMENTS_FILE.write_text(json.dumps(addresses, indent=2))


def load_abi(contract_name: str) -> list:
    """Load a contract ABI from Foundry's build output (out/<Name>.sol/<Name>.json)."""
    artifact = OUT_DIR / f"{contract_name}.sol" / f"{contract_name}.json"
    if not artifact.exists():
        raise FileNotFoundError(
            f"ABI for {contract_name} not found at {artifact}. Run `make test` or `forge build` first."
        )
    return json.loads(artifact.read_text())["abi"]
