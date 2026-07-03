# Ryan_Q5 — Bolting prediction (grouped-Shapley project)

Working directory for the modeling track against the Redmond et al. (2024)
single-plant-omics data (GEO GSE242681). Task: predict **bolting status** (binary)
from gene expression — 68 plants, 45 not-bolted / 23 bolted.

## Layout

| Path | What's in it |
|---|---|
| `code/` | Live code: `loo_harness.py` (LOO eval harness), `mad_feature_selection.py` (the `mad5000` gene set), `bootstrap.py` (variance bands). Its `README.md` has per-script explanations and command-line examples. |
| `data/tpm_tables/` | Model inputs — the TPM matrices and `phenos_to_predict.csv`. |
| `results/` | Generated outputs (per-fold predictions + run manifests). |
| `docs/` | `HANDOFFS/`, `STATUS_DOCS/`, reference PDFs. |
| `archive/` | Superseded / one-off scripts, kept for provenance. Not used by the harness. |
| `other_data/` | Raw upstream expression data (salmon quants). |
| `SinglePlantOmics/` | Read-only clone of the upstream repo — source of truth, not edited. |
| `ryan-env/` | Python 3.10.4 venv (see `requirements.txt`). |

## Environment

Python **3.10.4** / **scikit-learn 1.1.3** (matches the paper's pinned env), built with `uv`:

```bash
uv venv --python 3.10.4 ryan-env
uv pip install --python ryan-env/bin/python -r requirements.txt
```

## Quick start

See [`code/README.md`](code/README.md) for full usage. Minimal run:

```bash
PY=ryan-env/bin/python
$PY code/loo_harness.py --model ridge --feature-set regs \
    --tpm-filtered data/tpm_tables/TPM_filtered.csv \
    --regs-zscored data/tpm_tables/TPM_z_scored_only_regs.csv \
    --pheno data/tpm_tables/phenos_to_predict.csv \
    --out-dir results
```

The two project decisions are **explicit, no-default switches**: `--feature-set`
(`full` / `regs` / `mad5000`) and `--model` (`ridge` / `enet` / `rf` / `mlp` / `xgb`).

---

## Project status

The **evaluation scaffold is built and committed**; the two scientific decisions it's
built around are deliberately left open.

**Built and working:**
- Pinned, reproducible environment (Python 3.10.4 / scikit-learn 1.1.3 / xgboost 3.2.0)
  matching the paper's `flowering_variability_env.yml`, via `requirements.txt` + `uv`.
- Confirmed the upstream committed models load, the labels (45/23 split), and the TPM
  matrices — all as described in the handoff.
- `mad_feature_selection.py`: the MAD5000 gene set (mean/median switch, `log1p`,
  force-add by locus ID).
- `loo_harness.py`: leave-one-out evaluation with balanced accuracy, leak-free per-fold
  standardization, and both project decisions as switches across five models.
- `bootstrap.py`: plant-bootstrap variance bands (out-of-bag refit; prediction-bootstrap
  for the slow enet).

**Decisions still open (Gerald / assumptions track):**
- **Fork 1** — which feature set (`full` / `regs` / `mad5000`).
- **Fork 2** — which model, and whether to reuse the committed elastic-net or retrain.
- **Class-imbalance policy** is currently inconsistent across models (`rf` balanced,
  others unweighted) — pick one before final runs.
- **`rf` / `mlp` / `xgb` hyperparameters are DRAFT** — reconcile with "Artifact B".

**Not yet done:**
- The full model × feature-set **grid** of bootstrap runs (the complete error-bar table).
- Anything **WGCNA / SHAP / attribution** downstream — a later, separate track.

**Methodology notes to keep in view:** standardization here is per-fold (leak-free),
which diverges from the committed models' *global* z-scoring — so fresh results aren't
directly comparable to reused committed models without matching preprocessing. And the
bootstrap's `oob` and `pred` bands measure different things, so don't compare enet's
band directly against the others.
