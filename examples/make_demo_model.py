"""Produce a small *real* model artifact to demo and benchmark with.

Trains a tiny scikit-learn classifier on the classic Iris dataset and serialises it to a file.
It's deliberately small and dependency-light — the point is to have a genuine model file (bytes on
disk) to upload, hash, and register, not to do ML research.

    python -m examples.make_demo_model            # writes examples/artifacts/demo_model.joblib
"""

from __future__ import annotations

from pathlib import Path

import joblib
from sklearn.datasets import load_iris
from sklearn.linear_model import LogisticRegression

OUT = Path(__file__).resolve().parent / "artifacts" / "demo_model.joblib"


def main() -> Path:
    X, y = load_iris(return_X_y=True)
    model = LogisticRegression(max_iter=500).fit(X, y)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, OUT)
    print(f"Wrote demo model -> {OUT} ({OUT.stat().st_size} bytes)")
    return OUT


if __name__ == "__main__":
    main()
