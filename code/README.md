# Bolting-prediction harness

Leave-one-out evaluation harness for predicting **bolting status** (binary) from
gene expression in the Redmond et al. (2024) single-plant-omics data (GEO GSE242681,
68 plants: 45 not-bolted, 23 bolted).

Two files, which must live in the same directory:

| File | Role |
|---|---|
| `loo_harness.py` | The runnable script: feature-set × model switches, LOO CV, balanced accuracy, saved outputs. |
| `mad_feature_selection.py` | Builds the `mad5000` custom gene set (imported by the harness). |

---

## The two switches

The harness deliberately exposes the two open project decisions as **required,
no-default** command-line switches. Nothing is silently chosen for you.

**`--feature-set` (Fork 1) — which gene universe:**

| Value | Genes | Source |
|---|---|---|
| `full` | 19,283 | full transcriptome (`TPM_filtered.csv`) |
| `regs` | 1,159 | regulator subset (gene list from `TPM_z_scored_only_regs.csv`) |
| `mad5000` | ~5,004 | top-5,000 most-variable + 5 force-added flowering genes |

**`--model` (Fork 2) — which classifier:**

| Value | Model |
|---|---|
| `ridge` | L2 logistic, fixed `C=0.01` (no hyperparameter search) |
| `enet` | paper's elastic-net logistic (`LogisticRegressionCV`, saga) — **slow** |
| `rf` | random forest, 500 trees, `class_weight="balanced"` |
| `mlp` | two-layer MLP `(32, 16)` |
| `xgb` | gradient-boosted trees (xgboost), 500 trees, `max_depth=3` |

**`--mad-stat mean|median`** — only used with `--feature-set mad5000`; picks
mean- vs median-absolute-deviation for ranking. Defaults to `mean`.

---

## Environment

Python **3.10.4** with **scikit-learn 1.1.3** (see the project `requirements.txt`).
Built with `uv`:

```bash
uv venv --python 3.10.4 /path/to/ryan-env
uv pip install --python /path/to/ryan-env/bin/python -r requirements.txt
```

All commands below assume `PY=/path/to/ryan-env/bin/python`.

---

## Inputs

Point these at **your own copies** of the data (the harness never needs to write
into the source repo). Set them once as shell variables to keep commands short:

```bash
PY=/path/to/ryan-env/bin/python
DATA=/path/to/your/data          # holds the CSVs below
OUT=/path/to/your/harness_out    # results go here

TPM=$DATA/TPM_filtered.csv                 # raw TPM, 19283 x 68 (feature source)
REGS=$DATA/TPM_z_scored_only_regs.csv      # used ONLY for the regulator gene list
PHENO=$DATA/phenos_to_predict.csv          # labels (bolting Y/N)
```

---

## Command-line examples

**Ridge baseline on each feature set:**

```bash
$PY loo_harness.py --model ridge --feature-set full \
    --tpm-filtered $TPM --regs-zscored $REGS --pheno $PHENO --out-dir $OUT

$PY loo_harness.py --model ridge --feature-set regs \
    --tpm-filtered $TPM --regs-zscored $REGS --pheno $PHENO --out-dir $OUT

$PY loo_harness.py --model ridge --feature-set mad5000 --mad-stat mean \
    --tpm-filtered $TPM --regs-zscored $REGS --pheno $PHENO --out-dir $OUT
```

**Swap the model (same feature set):**

```bash
$PY loo_harness.py --model rf   --feature-set regs --tpm-filtered $TPM --regs-zscored $REGS --pheno $PHENO --out-dir $OUT
$PY loo_harness.py --model mlp  --feature-set regs --tpm-filtered $TPM --regs-zscored $REGS --pheno $PHENO --out-dir $OUT
$PY loo_harness.py --model enet --feature-set regs --tpm-filtered $TPM --regs-zscored $REGS --pheno $PHENO --out-dir $OUT
$PY loo_harness.py --model xgb  --feature-set regs --tpm-filtered $TPM --regs-zscored $REGS --pheno $PHENO --out-dir $OUT
```

**`mad5000` with the median ranking variant:**

```bash
$PY loo_harness.py --model ridge --feature-set mad5000 --mad-stat median \
    --tpm-filtered $TPM --regs-zscored $REGS --pheno $PHENO --out-dir $OUT
```

**Sweep the full model × feature-set grid (bash loop):**

```bash
for model in ridge enet rf mlp xgb; do
  for fs in full regs mad5000; do
    $PY loo_harness.py --model $model --feature-set $fs \
        --tpm-filtered $TPM --regs-zscored $REGS --pheno $PHENO --out-dir $OUT
  done
done
```

**Change the seed** (default 123, matching the paper's `random_state`):

```bash
$PY loo_harness.py --model rf --feature-set full --seed 7 \
    --tpm-filtered $TPM --regs-zscored $REGS --pheno $PHENO --out-dir $OUT
```

---

## Outputs

Each run writes two files to `--out-dir`, tagged `<model>_<featureset>[_<madstat>]`:

- **`preds_<tag>.csv`** — per-fold predictions: `sample, y_true, y_pred` (1 = bolted).
- **`manifest_<tag>.json`** — balanced/raw accuracy, confusion matrix, the exact
  model spec (all hyperparameters), seed, and package versions (Python, scikit-learn,
  numpy, pandas) for reproducibility.

Console output shows balanced accuracy, raw accuracy, and the confusion matrix.

---

## Methodology notes (read before trusting numbers)

- **Balanced accuracy is the headline metric**, not raw accuracy — the 23/45 class
  imbalance makes raw accuracy flatter a model that leans "not bolted."
- **Leave-one-out CV** (n = 68 forces it; matches the paper's protocol).
- **Standardization is per-fold and leak-free**: `StandardScaler` is fit on the 67
  training plants inside each fold, never on the held-out one. This is more correct
  than the committed models' *global* z-scoring — so these numbers are **not directly
  comparable** to reused committed models without matching the preprocessing.
- **`rf`, `mlp`, and `xgb` hyperparameters are DRAFT placeholders** (`min_samples_leaf`,
  layer sizes, tree depth / learning rate, etc.), not authoritative. Reconcile with
  the assumptions track / "Artifact B" before treating any result as final.
- **Class-imbalance handling is inconsistent across models** (a documented gap):
  `rf` uses `class_weight="balanced"`, `xgb` is left unweighted (`scale_pos_weight=1`),
  and `ridge`/`enet`/`mlp` are unweighted. Pick one policy before final runs.
- **`enet` is slow** — it re-runs the paper's inner 5-fold × 10 Cs × 7 l1-ratios
  search on every LOO fold. Expect minutes on `regs`, much longer on `full`.
- **Single-run point estimates only.** Variance (the plant-bootstrap loop) is a
  separate, not-yet-built step.
