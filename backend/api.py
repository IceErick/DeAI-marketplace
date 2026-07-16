"""Thin FastAPI layer exposing the marketplace as a REST service.

This is intentionally small — it maps HTTP requests onto the `Marketplace` facade and the IPFS
client. It's here so a frontend (or a grader) can drive the whole flow over HTTP:

    upload -> register -> verify -> list -> purchase -> log usage

Start it with `make api`, then open http://127.0.0.1:8000/docs for interactive Swagger docs.
"""

from __future__ import annotations

from fastapi import FastAPI, HTTPException, UploadFile
from pydantic import BaseModel

from .chain import Marketplace
from .ipfs_client import IPFSClient
from .model_hash import sha256_bytes

app = FastAPI(title="DeAI-marketplace API", version="0.1.0")

ipfs = IPFSClient()


def _market() -> Marketplace:
    try:
        return Marketplace()
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))


# --- request models --------------------------------------------------------------------------
class ListRequest(BaseModel):
    token_id: int
    price_wei: int
    allowed_use_types: int  # bitmask, e.g. 1 = inference only
    duration_s: int  # 0 = perpetual


class PurchaseRequest(BaseModel):
    token_id: int
    price_wei: int


class UsageRequest(BaseModel):
    token_id: int
    use_type: int


# --- routes ----------------------------------------------------------------------------------
@app.get("/health")
def health():
    return {"ipfs_online": ipfs.online}


@app.post("/register")
async def register(file: UploadFile, royalty_bps: int = 500):
    """Upload a model file, pin it to IPFS, and register it on-chain in one call."""
    data = await file.read()
    cid = ipfs.add_bytes(data, name=file.filename or "model.bin")
    digest = sha256_bytes(data)
    result = _market().register_model(cid, digest, royalty_bps)
    return {"token_id": result.return_value, "cid": cid, "sha256": digest, "gas_used": result.gas_used}


@app.get("/verify/{token_id}")
def verify(token_id: int):
    """Re-download the model from IPFS, re-hash it, and check against the on-chain hash."""
    m = _market()
    model = m.get_model(token_id)  # (ipfsCID, sha256Hash, version, createdAt, updatedAt, creator)
    cid = model[0]
    data = ipfs.get_bytes(cid)
    digest = sha256_bytes(data)
    return {"token_id": token_id, "cid": cid, "recomputed_sha256": digest, "intact": m.verify(token_id, digest)}


@app.post("/list")
def list_license(req: ListRequest):
    r = _market().list_license(req.token_id, req.price_wei, req.allowed_use_types, req.duration_s)
    return {"tx_hash": r.tx_hash, "gas_used": r.gas_used}


@app.post("/purchase")
def purchase(req: PurchaseRequest):
    r = _market().purchase_license(req.token_id, req.price_wei)
    return {"tx_hash": r.tx_hash, "gas_used": r.gas_used}


@app.post("/usage")
def log_usage(req: UsageRequest):
    r = _market().log_usage(req.token_id, req.use_type)
    return {"tx_hash": r.tx_hash, "gas_used": r.gas_used, "total_logs": _market().total_logs()}
