"""
mlflow_tracking.py
==================
Experiment tracking + model registry with MLflow.

WHY THIS MATTERS
----------------
The #1 MLOps failure is "we can't reproduce that model." Experiment tracking
records *exactly* what produced a model (params, metrics, code SHA, data
version) and the registry turns the winning run into a versioned, promotable
artifact with a Staging -> Production lifecycle.

This script:
  1) Trains a model while logging everything to MLflow.
  2) Evaluates it and applies a QUALITY GATE (never register a regression).
  3) Registers + promotes to Production only if it beats the current baseline.

Run a local tracking server first (optional):
    mlflow server --host 127.0.0.1 --port 5000
Then:
    export MLFLOW_TRACKING_URI=http://127.0.0.1:5000
    python mlflow_tracking.py
"""
from __future__ import annotations

import os
import subprocess

import mlflow
from mlflow.tracking import MlflowClient
from sklearn.datasets import make_classification
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import f1_score
from sklearn.model_selection import train_test_split

MODEL_NAME = "demo-classifier"
QUALITY_THRESHOLD = 0.80  # WHY: an explicit bar so we never ship a regression


def git_sha() -> str:
    """Tie every run to the exact code that produced it (reproducibility)."""
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"], text=True
        ).strip()
    except Exception:
        return "unknown"


def current_production_f1(client: MlflowClient) -> float:
    """Baseline = the model currently in Production.

    WHY: we promote a new model only if it BEATS the incumbent, not just if it
    clears an absolute number. This prevents silently replacing a better model.
    """
    try:
        for mv in client.search_model_versions(f"name='{MODEL_NAME}'"):
            if mv.current_stage == "Production":
                run = client.get_run(mv.run_id)
                return float(run.data.metrics.get("val_f1", 0.0))
    except Exception:
        pass
    return 0.0


def main() -> None:
    mlflow.set_experiment("demo-classifier-training")

    X, y = make_classification(n_samples=4000, n_features=20, random_state=42)
    X_tr, X_val, y_tr, y_val = train_test_split(X, y, test_size=0.25, random_state=42)

    params = {"n_estimators": 300, "max_depth": 12, "random_state": 42}

    with mlflow.start_run(run_name="rf-candidate") as run:
        # --- Log the FULL context of the run --------------------------------
        mlflow.log_params(params)              # WHY: reproducible config
        mlflow.set_tag("git_sha", git_sha())   # WHY: exact code lineage
        mlflow.set_tag("data_version", "synthetic-v1")  # WHY: exact data lineage

        model = RandomForestClassifier(**params).fit(X_tr, y_tr)
        val_f1 = f1_score(y_val, model.predict(X_val))
        mlflow.log_metric("val_f1", val_f1)    # WHY: objective run comparison

        # Log the model as a versioned artifact usable by the registry.
        mlflow.sklearn.log_model(model, artifact_path="model")
        print(f"[run {run.info.run_id[:8]}] val_f1={val_f1:.4f}")

        # --- QUALITY GATE ----------------------------------------------------
        client = MlflowClient()
        baseline = current_production_f1(client)
        print(f"Production baseline val_f1={baseline:.4f}, threshold={QUALITY_THRESHOLD}")

        if val_f1 < QUALITY_THRESHOLD:
            # WHY: an absolute floor - some tasks have a non-negotiable minimum.
            print("BLOCKED: below absolute quality threshold. Not registering.")
            return
        if val_f1 <= baseline:
            # WHY: don't replace a better incumbent (champion/challenger logic).
            print("BLOCKED: does not beat current Production model. Not promoting.")
            return

        # --- Register + promote ---------------------------------------------
        model_uri = f"runs:/{run.info.run_id}/model"
        mv = mlflow.register_model(model_uri, MODEL_NAME)
        client.transition_model_version_stage(
            name=MODEL_NAME,
            version=mv.version,
            stage="Production",
            archive_existing_versions=True,  # WHY: exactly one Production version
        )
        print(f"PROMOTED {MODEL_NAME} v{mv.version} to Production.")


if __name__ == "__main__":
    # Default to a local file store if no server configured (safe for demos).
    os.environ.setdefault("MLFLOW_TRACKING_URI", "file:./mlruns")
    main()
