"""Off-chain model storage via IPFS (the "warehouse" in our mental model).

The blockchain only stores a content id (CID). The bytes live in IPFS. This module wraps the two
operations we need: add a file (-> CID) and fetch a file (CID -> bytes).

If no IPFS daemon is reachable, it transparently falls back to a *local mock store* under
`examples/artifacts/_ipfs_mock/` so the rest of the project runs without installing IPFS. The mock
uses the same content-addressing idea (CID derived from the content hash), so behaviour is analogous.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

import requests

from . import config


class IPFSClient:
    def __init__(self, api_url: str | None = None):
        self.api_url = (api_url or config.IPFS_API_URL).rstrip("/")
        self._mock_dir = config.ROOT / "examples" / "artifacts" / "_ipfs_mock"
        self.online = self._probe()

    def _probe(self) -> bool:
        """Is a Kubo daemon reachable? (Kubo only accepts POST on its API.)"""
        try:
            r = requests.post(f"{self.api_url}/api/v0/version", timeout=1.5)
            return r.ok
        except requests.RequestException:
            return False

    # --- add ---------------------------------------------------------------------------------
    def add_file(self, path: str | Path) -> str:
        """Store a file and return its CID."""
        path = Path(path)
        if self.online:
            with open(path, "rb") as f:
                r = requests.post(
                    f"{self.api_url}/api/v0/add",
                    files={"file": (path.name, f)},
                    params={"cid-version": 1},
                    timeout=30,
                )
            r.raise_for_status()
            return r.json()["Hash"]
        return self._mock_add(path.read_bytes())

    def add_bytes(self, data: bytes, name: str = "model.bin") -> str:
        if self.online:
            r = requests.post(
                f"{self.api_url}/api/v0/add",
                files={"file": (name, data)},
                params={"cid-version": 1},
                timeout=30,
            )
            r.raise_for_status()
            return r.json()["Hash"]
        return self._mock_add(data)

    # --- fetch -------------------------------------------------------------------------------
    def get_bytes(self, cid: str) -> bytes:
        """Retrieve the bytes stored under a CID."""
        if self.online:
            r = requests.post(f"{self.api_url}/api/v0/cat", params={"arg": cid}, timeout=30)
            r.raise_for_status()
            return r.content
        return self._mock_get(cid)

    # --- local mock (no daemon) --------------------------------------------------------------
    def _mock_add(self, data: bytes) -> str:
        self._mock_dir.mkdir(parents=True, exist_ok=True)
        cid = "bafymock" + hashlib.sha256(data).hexdigest()[:46]
        (self._mock_dir / cid).write_bytes(data)
        return cid

    def _mock_get(self, cid: str) -> bytes:
        p = self._mock_dir / cid
        if not p.exists():
            raise FileNotFoundError(f"CID {cid} not in local mock store ({self._mock_dir}).")
        return p.read_bytes()
