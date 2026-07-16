"""Integrity hashing for model files (research angle 1: integrity & security).

The SHA-256 of a model file is what we anchor on-chain. To verify a downloaded model we re-hash it
and compare — the smart contract's `verify()` returns false for any tampered byte.

Run directly to hash a file:
    python -m backend.model_hash examples/artifacts/demo_model.joblib
"""

from __future__ import annotations

import hashlib
import sys
from pathlib import Path

_CHUNK = 1 << 20  # 1 MiB, so we can hash large model files without loading them fully into memory.


def sha256_file(path: str | Path) -> str:
    """Return the hex SHA-256 digest of a file's contents."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(_CHUNK):
            h.update(chunk)
    return h.hexdigest()


def sha256_bytes(data: bytes) -> str:
    """Return the hex SHA-256 digest of raw bytes."""
    return hashlib.sha256(data).hexdigest()


def to_bytes32(hex_digest: str) -> bytes:
    """Convert a 64-char hex digest into the 32-byte value the contracts store as bytes32."""
    return bytes.fromhex(hex_digest.removeprefix("0x"))


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("usage: python -m backend.model_hash <file>", file=sys.stderr)
        raise SystemExit(2)
    digest = sha256_file(sys.argv[1])
    print(f"sha256: 0x{digest}")
