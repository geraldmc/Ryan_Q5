"""First-step diagnostic: load one committed bolting model + both matrices + labels.
Read-only. Writes nothing. Reports structure/shape/versions for check-in."""
import pickle, sklearn, numpy as np, pandas as pd

REPO = "/Users/gerald2026/Desktop/iRESEARCH-2026/LIVE-06.21.2026/PYTHON-CODE/R1_Q5/SinglePlantOmics"
PHENO = f"{REPO}/desync_python_scripts/pheno_prediction"

print(f"# scikit-learn {sklearn.__version__}\n")

# ---- 1. Load one committed bolting model (regulator set, full l1 sweep) ----
model_path = f"{PHENO}/outputs/bolting_regs_enet_smaller_save.sav"
with open(model_path, "rb") as fh:
    model = pickle.load(fh)
print("=== MODEL: bolting_regs_enet_smaller_save.sav ===")
print("top-level type    :", type(model).__name__)
if isinstance(model, dict):
    keys = list(model.keys())
    print("dict len (folds)  :", len(keys))
    print("first 3 keys      :", keys[:3])
    one = model[keys[0]]
    print("per-fold value type:", type(one).__name__)
    for attr in ("C_", "l1_ratio_", "classes_"):
        if hasattr(one, attr):
            print(f"  {attr:10s}:", getattr(one, attr))
    if hasattr(one, "coef_"):
        print("  coef_ shape:", np.asarray(one.coef_).shape,
              "| nonzero:", int(np.count_nonzero(one.coef_)))

# ---- 2. Load both committed matrices ----
print("\n=== MATRICES ===")
for name in ("TPM_z_scored.csv", "TPM_z_scored_only_regs.csv"):
    df = pd.read_csv(f"{PHENO}/data/{name}", index_col=0)
    vals = df.values
    print(f"{name}: shape={df.shape} (genes x samples)")
    print(f"    per-gene(row) mean~{np.nanmean(vals.mean(axis=1)):+.3f} "
          f"std~{np.nanmean(vals.std(axis=1)):.3f}  "
          f"[global min {np.nanmin(vals):+.2f}, max {np.nanmax(vals):+.2f}]")
    print(f"    sample cols (first 3): {list(df.columns[:3])}")

# ---- 3. Load labels, check split + encoding ----
print("\n=== LABELS: phenos_to_predict.csv ===")
ph = pd.read_csv(f"{PHENO}/data/phenos_to_predict.csv", index_col=0)
print("shape:", ph.shape, "| columns:", list(ph.columns))
print("bolting value_counts:")
print(ph["bolting"].value_counts().to_string())
y = (ph["bolting"].values == "Y")
print(f"encoded (== 'Y'):  True/bolted(1)={int(y.sum())}, False/not(0)={int((~y).sum())}")
# orientation check: do label rows match matrix columns?
regs = pd.read_csv(f"{PHENO}/data/TPM_z_scored_only_regs.csv", index_col=0)
print("label index == matrix columns (order-exact):",
      list(ph.index) == list(regs.columns))
print("label index == matrix columns (as sets)   :",
      set(ph.index) == set(regs.columns))
