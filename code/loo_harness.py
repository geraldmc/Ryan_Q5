"""Leave-one-out evaluation harness for bolting prediction.

Feature set is an EXPLICIT SWITCH with no default (brief: "never a baked-in default").
Model here is the C=0.01 L2 (ridge) logistic baseline; structured so other models
(RF, MLP, elastic-net) can be registered later without touching the eval loop.

Protocol (forced by the data / brief):
  - Leave-one-out CV        (n = 68)
  - Balanced accuracy        (23/45 class imbalance -> raw accuracy misleads)
  - Fixed, recorded seed     (SEED, matches the paper's random_state = 123)
  - Per-fold predictions saved + a JSON manifest with package versions

Standardization: done PER FOLD inside a Pipeline (StandardScaler fit on the 67
training plants only), so the held-out plant never leaks into the scaling. All
three feature sets are therefore sourced from RAW TPM_filtered, not the committed
z-scored matrices. This is leak-free but diverges from the paper's global z-scoring;
relevant only if you later compare directly against the committed (reused) models.
"""
import argparse, json, platform, sys, warnings
from pathlib import Path

import numpy as np
import pandas as pd
import sklearn
from sklearn.linear_model import LogisticRegression, LogisticRegressionCV
from sklearn.ensemble import RandomForestClassifier
from sklearn.neural_network import MLPClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.model_selection import LeaveOneOut, cross_val_predict
from sklearn.metrics import balanced_accuracy_score, accuracy_score, confusion_matrix

sys.path.insert(0, str(Path(__file__).resolve().parent))
from mad_feature_selection import select_mad_features, FLOWERING_LOCI

SEED = 123  # matches the paper's random_state; recorded in the manifest


# --------------------------------------------------------------------------- #
# Feature-set switch: returns RAW (samples x genes). Standardization is per-fold.
# --------------------------------------------------------------------------- #
def build_feature_matrix(feature_set, tpm_filtered_path, regs_zscored_path, mad_stat):
    tpm = pd.read_csv(tpm_filtered_path, index_col=0)          # genes x samples, raw TPM

    if feature_set == "full":
        genes = tpm.index
    elif feature_set == "regs":
        regs = pd.read_csv(regs_zscored_path, index_col=0)     # only for its gene list
        genes = tpm.index.intersection(regs.index)
        if len(genes) != len(regs.index):
            print(f"[warn] {len(regs.index) - len(genes)} regulator genes missing "
                  f"from TPM_filtered; using the {len(genes)} present.")
    elif feature_set == "mad5000":
        genes = select_mad_features(tpm, n_top=5000, mad_stat=mad_stat, log=True)
    else:
        raise ValueError(f"unknown feature_set {feature_set!r}")

    X = tpm.loc[genes].T                                        # samples x genes, raw
    return X


# --------------------------------------------------------------------------- #
# Model registry: the Fork-2 switch. Each returns a bare estimator; make_model()
# wraps it in the per-fold StandardScaler pipeline. Add new models here only.
#
# NOTE ON HYPERPARAMETERS: rf/mlp/xgb settings below are DRAFT placeholders (student
# plan / brief's "Artifact B"), not authoritative. Reconcile min_samples_leaf,
# n_estimators, MLP layer sizes, and the xgb tree/learning-rate settings with the
# assumptions track before any result is treated as final.
# --------------------------------------------------------------------------- #
MODELS = ("ridge", "enet", "rf", "mlp", "xgb")


def make_clf(name, seed):
    if name == "ridge":
        # L2 (ridge) logistic baseline, fixed C=0.01 -- no hyperparameter search
        return LogisticRegression(penalty="l2", C=0.01, solver="lbfgs",
                                  max_iter=1000, class_weight=None, random_state=seed)
    if name == "enet":
        # the paper's elastic-net logistic recipe (LogisticRegressionCV, saga),
        # inner 5-fold picks C and l1_ratio per training set
        return LogisticRegressionCV(Cs=10, l1_ratios=[.1, .5, .7, .9, .95, .99, 1],
                                    penalty="elasticnet", solver="saga", cv=5,
                                    max_iter=1000, class_weight=None,
                                    random_state=seed, n_jobs=1)
    if name == "rf":
        # ~500-tree random forest, balanced classes; min_samples_leaf pinned (DRAFT)
        return RandomForestClassifier(n_estimators=500, class_weight="balanced",
                                      min_samples_leaf=3, random_state=seed, n_jobs=-1)
    if name == "mlp":
        # two hidden layers (DRAFT sizes); scaling (in the pipeline) matters here
        return MLPClassifier(hidden_layer_sizes=(32, 16), max_iter=1000,
                             random_state=seed)
    if name == "xgb":
        # gradient-boosted trees (DRAFT settings). Imported lazily so the other
        # models still run if xgboost isn't installed. Class imbalance is left
        # UNWEIGHTED here (scale_pos_weight=1) -- a documented knob, unlike rf's
        # class_weight="balanced"; reconcile the weighting policy across models.
        from xgboost import XGBClassifier
        return XGBClassifier(n_estimators=500, max_depth=3, learning_rate=0.1,
                             subsample=0.8, colsample_bytree=0.8, reg_lambda=1.0,
                             scale_pos_weight=1.0, random_state=seed,
                             n_jobs=-1, eval_metric="logloss")
    raise ValueError(f"unknown model {name!r}; choose from {MODELS}")


def make_model(name, seed):
    """Bare estimator wrapped in the per-fold standardization pipeline.

    StandardScaler is monotonic per feature, so it leaves the tree-based models
    (rf, xgb) unchanged while helping the linear/saga and MLP models -- one uniform
    pipeline is therefore safe across all five.
    """
    return Pipeline([("scale", StandardScaler()), ("clf", make_clf(name, seed))])


def main():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--feature-set", required=True, choices=["full", "regs", "mad5000"],
                   help="EXPLICIT, no default (Fork 1).")
    p.add_argument("--model", required=True, choices=list(MODELS),
                   help="EXPLICIT, no default (Fork 2).")
    p.add_argument("--mad-stat", default="mean", choices=["mean", "median"],
                   help="only used when --feature-set mad5000")
    p.add_argument("--tpm-filtered", required=True, help="path to TPM_filtered.csv (raw)")
    p.add_argument("--regs-zscored", required=True,
                   help="path to TPM_z_scored_only_regs.csv (used only for its gene list)")
    p.add_argument("--pheno", required=True, help="path to phenos_to_predict.csv")
    p.add_argument("--out-dir", required=True, help="where to write predictions + manifest")
    p.add_argument("--seed", type=int, default=SEED)
    args = p.parse_args()

    out_dir = Path(args.out_dir); out_dir.mkdir(parents=True, exist_ok=True)

    # ---- labels ----
    ph = pd.read_csv(args.pheno, index_col=0)
    y = (ph["bolting"].values == "Y").astype(int)   # 1 = bolted (23), 0 = not (45)
    sample_ids = list(ph.index)                     # int (not bool) so XGBoost accepts it

    # ---- features (raw) ----
    X = build_feature_matrix(args.feature_set, args.tpm_filtered,
                             args.regs_zscored, args.mad_stat)

    # ---- alignment guard: X rows must match label order exactly ----
    if list(X.index) != sample_ids:
        # reindex X to the label order; fail loudly if any sample is absent
        missing = set(sample_ids) - set(X.index)
        if missing:
            raise ValueError(f"samples in labels but not in features: {sorted(missing)}")
        X = X.loc[sample_ids]
    assert list(X.index) == sample_ids, "alignment failed"

    fs_tag = args.feature_set + (f"_{args.mad_stat}" if args.feature_set == "mad5000" else "")
    tag = f"{args.model}_{fs_tag}"
    print(f"model={args.model}  feature_set={fs_tag}  X shape={X.shape} (samples x genes)  "
          f"y: bolted={int((y==1).sum())} not={int((y==0).sum())}")

    # ---- leave-one-out predictions ----
    model = make_model(args.model, args.seed)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")  # silence per-fold convergence chatter; report below
        y_pred = cross_val_predict(model, X.values, y, cv=LeaveOneOut())

    bal = balanced_accuracy_score(y, y_pred)
    raw = accuracy_score(y, y_pred)
    cm = confusion_matrix(y, y_pred, labels=[0, 1])  # rows=true, cols=pred; 0=not, 1=bolted

    print(f"  balanced accuracy = {bal:.4f}   (raw accuracy = {raw:.4f})")
    print(f"  confusion [true x pred], order [not, bolted]:\n"
          f"    not:    {cm[0].tolist()}\n    bolted: {cm[1].tolist()}")

    # ---- save per-fold predictions ----
    preds = pd.DataFrame({"sample": sample_ids,
                          "y_true": y.astype(int),
                          "y_pred": y_pred.astype(int)})
    preds_path = out_dir / f"preds_{tag}.csv"
    preds.to_csv(preds_path, index=False)

    # ---- save manifest (reproducibility) ----
    manifest = {
        "feature_set": args.feature_set, "mad_stat": args.mad_stat if args.feature_set=="mad5000" else None,
        "n_genes": int(X.shape[1]), "n_samples": int(X.shape[0]),
        "model": args.model, "model_spec": str(make_clf(args.model, args.seed)),
        "standardization": "per-fold StandardScaler (leak-free)",
        "cv": "LeaveOneOut", "metric_balanced_accuracy": bal, "metric_raw_accuracy": raw,
        "confusion_true_by_pred_not_bolted": cm.tolist(),
        "seed": args.seed,
        "versions": {"python": platform.python_version(), "scikit_learn": sklearn.__version__,
                     "numpy": np.__version__, "pandas": pd.__version__},
        "inputs": {"tpm_filtered": str(args.tpm_filtered), "pheno": str(args.pheno)},
    }
    manifest_path = out_dir / f"manifest_{tag}.json"
    manifest_path.write_text(json.dumps(manifest, indent=2))
    print(f"  wrote {preds_path.name} and {manifest_path.name} to {out_dir}")


if __name__ == "__main__":
    main()
