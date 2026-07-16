"""Streamlit demo UI — the whole lifecycle in one pure-Python screen.

Walks a user through: upload a model -> register on-chain -> verify integrity -> list a license ->
purchase -> log usage. Each step shows the gas used, so the research story is visible while clicking.

Run with `make ui` (requires `make deploy` first so the contracts exist).
"""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

# Allow `import backend...` when Streamlit runs this file directly.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.chain import Marketplace  # noqa: E402
from backend.ipfs_client import IPFSClient  # noqa: E402
from backend.model_hash import sha256_bytes  # noqa: E402

st.set_page_config(page_title="DeAI-marketplace", page_icon="🔗", layout="centered")
st.title("🔗 DeAI-marketplace")
st.caption("Decentralized AI model sharing — provenance, licensing & usage on-chain; files on IPFS.")


@st.cache_resource
def get_clients():
    return Marketplace(), IPFSClient()


try:
    market, ipfs = get_clients()
except Exception as e:  # noqa: BLE001
    st.error(f"Not connected. Start Anvil and run `make deploy` first.\n\n{e}")
    st.stop()

st.success(f"Connected as {market.account.address}  ·  IPFS {'online' if ipfs.online else 'mock mode'}")

tab_register, tab_verify, tab_license, tab_usage = st.tabs(
    ["1 · Register", "2 · Verify", "3 · License", "4 · Log usage"]
)

with tab_register:
    st.subheader("Upload & register a model")
    uploaded = st.file_uploader("Model file")
    royalty = st.slider("Creator royalty (%)", 0, 20, 5)
    if uploaded and st.button("Register on-chain"):
        data = uploaded.read()
        cid = ipfs.add_bytes(data, name=uploaded.name)
        digest = sha256_bytes(data)
        res = market.register_model(cid, digest, royalty * 100)
        st.write({"token_id": res.return_value, "cid": cid, "sha256": f"0x{digest}", "gas_used": res.gas_used})

with tab_verify:
    st.subheader("Verify integrity")
    token_id = st.number_input("Token id", min_value=1, step=1, key="verify_id")
    if st.button("Fetch from IPFS & verify"):
        model = market.get_model(int(token_id))
        cid = model[0]
        data = ipfs.get_bytes(cid)
        digest = sha256_bytes(data)
        intact = market.verify(int(token_id), digest)
        st.write({"cid": cid, "recomputed_sha256": f"0x{digest}", "intact": intact})
        st.success("Integrity OK — file matches the on-chain hash.") if intact else st.error("Tampered!")

with tab_license:
    st.subheader("List & purchase a license")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**List (owner)**")
        lid = st.number_input("Token id", min_value=1, step=1, key="list_id")
        price_eth = st.number_input("Price (ETH)", min_value=0.0, value=0.01, step=0.01)
        inference = st.checkbox("Allow inference", value=True)
        finetune = st.checkbox("Allow fine-tuning", value=False)
        perpetual = st.checkbox("Perpetual", value=True)
        days = 0 if perpetual else st.number_input("Duration (days)", min_value=1, value=30)
        if st.button("List license"):
            mask = (1 if inference else 0) | ((1 << 1) if finetune else 0)
            wei = int(price_eth * 10**18)
            r = market.list_license(int(lid), wei, mask, int(days) * 86400)
            st.write({"gas_used": r.gas_used})
    with col2:
        st.markdown("**Purchase (buyer)**")
        pid = st.number_input("Token id", min_value=1, step=1, key="buy_id")
        pprice = st.number_input("Price (ETH)", min_value=0.0, value=0.01, step=0.01, key="buy_price")
        if st.button("Purchase license"):
            r = market.purchase_license(int(pid), int(pprice * 10**18))
            st.write({"gas_used": r.gas_used})

with tab_usage:
    st.subheader("Log a usage event")
    uid = st.number_input("Token id", min_value=1, step=1, key="usage_id")
    use_type = st.selectbox("Use type", options=[(0, "inference"), (1, "fine-tuning"), (2, "redistribution")], format_func=lambda o: o[1])
    if st.button("Log usage"):
        r = market.log_usage(int(uid), use_type[0])
        st.write({"gas_used": r.gas_used, "total_logs": market.total_logs()})
