"""Plant-bootstrap loop: variance bands on balanced accuracy via plant resampling.

Turns a single-point balanced-accuracy estimate into a DISTRIBUTION, so the model x
feature-set comparisons can be read with error bars (the variance check the
"model-agnostic" claim depends on). The MODEL seed is held fixed across all
iterations -- the only thing that varies is which plants were drawn -- so the spread
reflects plant-sampling variability alone, not model stochasticity.

Two scoring modes (--method):
  oob  : OUT-OF-BAG REFIT (leak-free; default for all models except enet).
         Resample 68 plants with replacement, train on the in-bag draw (with
         multiplicity), score balanced accuracy on the ~37% out-of-bag plants that
         were not drawn. Train and test never overlap.
  pred : PREDICTION-BOOTSTRAP (cheap; default for enet). Run leave-one-out ONCE to
         get out-of-fold predictions, then resample the 68 (y_true, y_pred) pairs and
         recompute balanced accuracy. Captures the metric's sampling noise but NOT
         refit variance -- a narrower, different-in-kind band. Used for enet because a
         full refit-per-resample of its inner-CV recipe is prohibitively slow.

  auto (default): enet -> pred, everything else -> oob.
"""
import argparse, json, platform, sys, warnings
from pathlib import Path

import numpy as np
import pandas as pd
import sklearn
from sklearn.model_selection import LeaveOneOut, cross_val_predict
from sklearn.metrics import balanced_accuracy_score

sys.path.insert(0, str(Path(__file__).resolve().parent))
from loo_harness import load_Xy, make_model, make_clf, MODELS, SEED


def bootstrap_oob(name, Xv, y, seed_model, n_boot, rng):
    """Out-of-bag refit. Returns (scores, n_skipped)."""
    n = len(y)
    all_idx = np.arange(n)
    scores, skipped = [], 0
    for _ in range(n_boot):
        draw = rng.integers(0, n, size=n)          # resample plants w/ replacement
        in_bag = np.unique(draw)
        oob = np.setdiff1d(all_idx, in_bag)
        # need both classes in train, and a non-empty two-class OOB set to score
        if len(oob) == 0 or np.unique(y[draw]).size < 2 or np.unique(y[oob]).size < 2:
            skipped += 1
            continue
        model = make_model(name, seed_model)        # seed pinned every iteration
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            model.fit(Xv[draw], y[draw])            # train on in-bag (with multiplicity)
            pred = model.predict(Xv[oob])
        scores.append(balanced_accuracy_score(y[oob], pred))
    return np.array(scores), skipped


def bootstrap_pred(name, Xv, y, seed_model, n_boot, rng):
    """Prediction-bootstrap. One LOO pass, then resample (y_true, y_pred) pairs.
    Returns (scores, n_skipped, point_estimate)."""
    model = make_model(name, seed_model)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        y_pred = cross_val_predict(model, Xv, y, cv=LeaveOneOut())
    point = balanced_accuracy_score(y, y_pred)
    n = len(y)
    scores, skipped = [], 0
    for _ in range(n_boot):
        idx = rng.integers(0, n, size=n)
        if np.unique(y[idx]).size < 2:              # degenerate one-class resample
            skipped += 1
            continue
        scores.append(balanced_accuracy_score(y[idx], y_pred[idx]))
    return np.array(scores), skipped, point


def summarize(scores):
    return {
        "n_scores": int(scores.size),
        "mean": float(np.mean(scores)),
        "std": float(np.std(scores, ddof=1)),
        "ci95_lo": float(np.percentile(scores, 2.5)),
        "median": float(np.percentile(scores, 50)),
        "ci95_hi": float(np.percentile(scores, 97.5)),
    }


def main():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--feature-set", required=True, choices=["full", "regs", "mad5000"])
    p.add_argument("--model", required=True, choices=list(MODELS))
    p.add_argument("--mad-stat", default="mean", choices=["mean", "median"])
    p.add_argument("--method", default="auto", choices=["auto", "oob", "pred"],
                   help="auto: enet->pred, else oob")
    p.add_argument("--n-boot", type=int, default=1000, help="number of resamples")
    p.add_argument("--seed", type=int, default=SEED,
                   help="MODEL seed, held fixed across all iterations")
    p.add_argument("--boot-seed", type=int, default=123,
                   help="RNG seed for the plant resampling (separate from model seed)")
    p.add_argument("--tpm-filtered", required=True)
    p.add_argument("--regs-zscored", required=True)
    p.add_argument("--pheno", required=True)
    p.add_argument("--out-dir", required=True)
    args = p.parse_args()

    method = ("pred" if args.model == "enet" else "oob") if args.method == "auto" else args.method
    out_dir = Path(args.out_dir); out_dir.mkdir(parents=True, exist_ok=True)

    X, y, _ = load_Xy(args.feature_set, args.tpm_filtered,
                      args.regs_zscored, args.pheno, args.mad_stat)
    Xv = X.values
    rng = np.random.default_rng(args.boot_seed)

    fs_tag = args.feature_set + (f"_{args.mad_stat}" if args.feature_set == "mad5000" else "")
    tag = f"{args.model}_{fs_tag}_{method}"
    print(f"model={args.model}  feature_set={fs_tag}  method={method}  "
          f"n_boot={args.n_boot}  X={X.shape}")

    point = None
    if method == "oob":
        scores, skipped = bootstrap_oob(args.model, Xv, y, args.seed, args.n_boot, rng)
    else:
        scores, skipped, point = bootstrap_pred(args.model, Xv, y, args.seed, args.n_boot, rng)

    if scores.size == 0:
        raise RuntimeError("all resamples skipped (degenerate) -- check the data")

    s = summarize(scores)
    print(f"  balanced accuracy: mean={s['mean']:.4f}  std={s['std']:.4f}  "
          f"95% CI [{s['ci95_lo']:.4f}, {s['ci95_hi']:.4f}]"
          + (f"  (LOO point={point:.4f})" if point is not None else ""))
    if skipped:
        print(f"  note: {skipped}/{args.n_boot} resamples skipped (one-class draw)")

    # ---- save the full score vector + a summary manifest ----
    pd.DataFrame({"boot_balanced_accuracy": scores}).to_csv(
        out_dir / f"boot_{tag}.csv", index=False)
    manifest = {
        "model": args.model, "feature_set": args.feature_set,
        "mad_stat": args.mad_stat if args.feature_set == "mad5000" else None,
        "method": method, "n_boot": args.n_boot, "n_skipped": skipped,
        "model_seed": args.seed, "boot_seed": args.boot_seed,
        "loo_point_estimate": point,
        "summary": s,
        "model_spec": str(make_clf(args.model, args.seed)),
        "versions": {"python": platform.python_version(),
                     "scikit_learn": sklearn.__version__,
                     "numpy": np.__version__, "pandas": pd.__version__},
    }
    (out_dir / f"boot_manifest_{tag}.json").write_text(json.dumps(manifest, indent=2))
    print(f"  wrote boot_{tag}.csv and boot_manifest_{tag}.json to {out_dir}")


if __name__ == "__main__":
    main()
