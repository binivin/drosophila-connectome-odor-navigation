"""Verify integrity and key metadata of the frozen final v3 checkpoint."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import joblib

EXPECTED_SHA256 = "8d6b557bb592f29100fdf8d95cb3ccd91f608516f6862e3f772491461e983acc"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--checkpoint",
        type=Path,
        default=Path("artifacts/checkpoints/final_v3_connectome_controller.joblib"),
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        default=Path("artifacts/manifests/final_runtime_manifest.json"),
    )
    args = parser.parse_args()

    observed = sha256_file(args.checkpoint)
    if observed != EXPECTED_SHA256:
        raise SystemExit(
            f"SHA256 mismatch\nexpected: {EXPECTED_SHA256}\nobserved: {observed}"
        )

    checkpoint = joblib.load(args.checkpoint)
    assert int(checkpoint["N"]) == 532
    assert checkpoint["W_recurrent_sparse"].shape == (532, 532)
    assert int(checkpoint["W_recurrent_sparse"].nnz) == 5274
    assert len(checkpoint["readout_indices"]) == 36
    assert checkpoint["motor_output_bounds"]["forward_speed"] == [0.0, 0.85]
    assert checkpoint["motor_output_bounds"]["angular_velocity"] == [-2.5, 2.5]

    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    assert manifest["checkpoint_sha256"] == EXPECTED_SHA256

    print("Checkpoint integrity verified")
    print(f"SHA256: {observed}")
    print("neurons: 532")
    print("recurrent edges: 5274")
    print("PFL readout neurons: 36")


if __name__ == "__main__":
    main()
