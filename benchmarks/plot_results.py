"""Render benchmark CSVs into figures for the thesis.

Reads whatever benchmarks/results/*.csv exist (from run_benchmarks.py) and writes matching PNGs.
Uses matplotlib only — no seaborn — so there are no extra dependencies.

    python -m benchmarks.plot_results
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # headless — write files, don't open windows.
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

RESULTS = Path(__file__).resolve().parent / "results"


def plot_gas():
    path = RESULTS / "onchain_gas_latency.csv"
    if not path.exists():
        return
    df = pd.read_csv(path)
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.bar(df["operation"], df["gas_used"], color="#4C78A8")
    ax.set_title("Gas cost per on-chain operation")
    ax.set_ylabel("gas used")
    ax.tick_params(axis="x", rotation=20)
    fig.tight_layout()
    fig.savefig(RESULTS / "gas_by_operation.png", dpi=150)
    plt.close(fig)


def plot_ipfs():
    path = RESULTS / "ipfs_timing.csv"
    if not path.exists():
        return
    df = pd.read_csv(path)
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.plot(df["size_kb"], df["upload_ms"], marker="o", label="upload")
    ax.plot(df["size_kb"], df["download_ms"], marker="s", label="download")
    ax.set_title("IPFS transfer time vs file size")
    ax.set_xlabel("file size (KB)")
    ax.set_ylabel("time (ms)")
    ax.set_xscale("log", base=2)
    ax.legend()
    fig.tight_layout()
    fig.savefig(RESULTS / "ipfs_timing.png", dpi=150)
    plt.close(fig)


def main():
    if not RESULTS.exists():
        print("No results yet — run `make benchmark` first.")
        return
    plot_gas()
    plot_ipfs()
    print("Figures written to", RESULTS)


if __name__ == "__main__":
    main()
