# R1_Q5 — Bolting prediction (grouped-Shapley project)

Working directory for the modeling track against the Redmond et al. (2024)
single-plant-omics data (GEO GSE242681). Task: predict **bolting status** (binary)
from gene expression — 68 plants, 45 not-bolted / 23 bolted.

## Layout

| Path | What's in it |
|---|---|
| `code/` | Live code: `loo_harness.py` (LOO eval harness) + `mad_feature_selection.py` (the `mad5000` gene set). Its `README.md` has the command-line examples. |
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
(`full` / `regs` / `mad5000`) and `--model` (`ridge` / `enet` / `rf` / `mlp`).
