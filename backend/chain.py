"""web3.py wrappers around the three contracts (the "clerk" that talks to the chain).

One small class, `Marketplace`, exposes readable methods that mirror the contract functions:
register a model, list/purchase a license, verify integrity, log usage. Every transaction returns
its receipt so callers (API, benchmarks) can read gas used.

Nothing here signs with a real key — it uses a local dev account by default (see config).
"""

from __future__ import annotations

from dataclasses import dataclass

from web3 import Web3
from web3.types import TxReceipt

from . import config


@dataclass
class TxResult:
    tx_hash: str
    gas_used: int
    block_number: int
    return_value: object | None = None  # e.g. new tokenId, decoded from an event


class Marketplace:
    """Thin, typed facade over ModelRegistry + Licensing + UsageLog."""

    def __init__(self, private_key: str | None = None):
        self.w3 = Web3(Web3.HTTPProvider(config.RPC_URL))
        self.account = self.w3.eth.account.from_key(private_key or config.DEFAULT_PRIVATE_KEY)

        addrs = config.load_deployments()
        if not addrs:
            raise RuntimeError(
                "No deployed addresses found. Run `make deploy` first (writes backend/deployments.local.json)."
            )
        self.registry = self._contract("ModelRegistry", addrs["ModelRegistry"])
        self.licensing = self._contract("Licensing", addrs["Licensing"])
        self.usage = self._contract("UsageLog", addrs["UsageLog"])

    def _contract(self, name: str, address: str):
        return self.w3.eth.contract(address=Web3.to_checksum_address(address), abi=config.load_abi(name))

    # --- helpers -----------------------------------------------------------------------------
    def _send(self, fn, value: int = 0) -> TxReceipt:
        """Build, sign, send a transaction and wait for its receipt."""
        tx = fn.build_transaction(
            {
                "from": self.account.address,
                "nonce": self.w3.eth.get_transaction_count(self.account.address),
                "value": value,
            }
        )
        signed = self.account.sign_transaction(tx)
        tx_hash = self.w3.eth.send_raw_transaction(signed.raw_transaction)
        return self.w3.eth.wait_for_transaction_receipt(tx_hash)

    # --- ModelRegistry -----------------------------------------------------------------------
    def register_model(self, ipfs_cid: str, sha256_hex: str, royalty_bps: int) -> TxResult:
        sha_bytes = bytes.fromhex(sha256_hex.removeprefix("0x"))
        fn = self.registry.functions.registerModel(ipfs_cid, sha_bytes, royalty_bps)
        rcpt = self._send(fn)
        # Decode the tokenId from the ModelRegistered event.
        logs = self.registry.events.ModelRegistered().process_receipt(rcpt)
        token_id = logs[0]["args"]["tokenId"] if logs else None
        return self._result(rcpt, token_id)

    def verify(self, token_id: int, sha256_hex: str) -> bool:
        sha_bytes = bytes.fromhex(sha256_hex.removeprefix("0x"))
        return self.registry.functions.verify(token_id, sha_bytes).call()

    def get_model(self, token_id: int):
        return self.registry.functions.getModel(token_id).call()

    # --- Licensing ---------------------------------------------------------------------------
    def list_license(self, token_id: int, price_wei: int, allowed_use_types: int, duration_s: int) -> TxResult:
        fn = self.licensing.functions.listLicense(token_id, price_wei, allowed_use_types, duration_s)
        return self._result(self._send(fn))

    def purchase_license(self, token_id: int, price_wei: int) -> TxResult:
        fn = self.licensing.functions.purchaseLicense(token_id)
        return self._result(self._send(fn, value=price_wei))

    def has_valid_license(self, token_id: int, user: str) -> bool:
        return self.licensing.functions.hasValidLicense(token_id, Web3.to_checksum_address(user)).call()

    # --- UsageLog ----------------------------------------------------------------------------
    def log_usage(self, token_id: int, use_type: int) -> TxResult:
        fn = self.usage.functions.logUsage(token_id, use_type)
        return self._result(self._send(fn))

    def total_logs(self) -> int:
        return self.usage.functions.totalLogs().call()

    @staticmethod
    def _result(rcpt: TxReceipt, return_value: object | None = None) -> TxResult:
        return TxResult(
            tx_hash=rcpt["transactionHash"].hex(),
            gas_used=rcpt["gasUsed"],
            block_number=rcpt["blockNumber"],
            return_value=return_value,
        )
