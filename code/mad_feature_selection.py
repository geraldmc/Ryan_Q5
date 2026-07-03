"""MAD5000 feature selection for the bolting-prediction task.

Produces the student's custom gene universe (Fork-1, third option):
  top-N most-variable genes by absolute deviation, force-adding the canonical
  flowering-time regulators regardless of rank.

Pinned decisions (from the assumptions track):
  - source matrix : TPM_filtered.csv (raw, pre-z-scored; 19,283 genes x 68 plants)
  - transform     : log1p  (decision (b) -- tames TPM mean-variance coupling)
  - force-add     : CO / SVP / FT / SOC1 / FLC, BY AGI LOCUS ID
                    (SOC1 is labelled AGL20 in the repo, so symbol matching fails --
                     locus IDs are the safe key)

Open switch (assumptions track has not finalised):
  - MAD_STAT : "mean"   -> mean   absolute deviation about the mean   (student's written spec)
               "median" -> median absolute deviation about the median (standard "MAD"; robust)
    Empirically the two share ~92% of the top-5000 here, and both yield the same
    final set size (5004) with the same force-add pattern, so this is a low-risk knob.
"""
import numpy as np
import pandas as pd

# Canonical flowering-time genes, keyed by AGI locus ID (NOT symbol -- see docstring).
FLOWERING_LOCI = ["AT5G15840",  # CO
                  "AT2G22540",  # SVP
                  "AT1G65480",  # FT
                  "AT2G45660",  # SOC1 (a.k.a. AGL20)
                  "AT5G10140"]  # FLC


def rank_by_abs_deviation(tpm_filtered: pd.DataFrame,
                          mad_stat: str = "mean",
                          log: bool = True) -> pd.Series:
    """Per-gene variability score across samples. Higher = more variable.

    Args:
        tpm_filtered: genes (rows) x samples (cols), raw TPM.
        mad_stat: "mean" or "median" -- the switch.
        log: apply log1p before scoring (pinned True).

    Returns:
        Series indexed by gene, sorted descending by the variability score.
    """
    if mad_stat not in ("mean", "median"):
        raise ValueError(f"mad_stat must be 'mean' or 'median', got {mad_stat!r}")

    v = tpm_filtered.values.astype(float)
    if log:
        v = np.log1p(v)

    if mad_stat == "mean":
        center = v.mean(axis=1, keepdims=True)
        score = np.abs(v - center).mean(axis=1)
    else:  # median absolute deviation about the median
        center = np.median(v, axis=1, keepdims=True)
        score = np.median(np.abs(v - center), axis=1)

    return pd.Series(score, index=tpm_filtered.index).sort_values(ascending=False)


def select_mad_features(tpm_filtered: pd.DataFrame,
                        n_top: int = 5000,
                        mad_stat: str = "mean",
                        log: bool = True,
                        force_add=FLOWERING_LOCI) -> pd.Index:
    """Return the MAD-selected gene set (top-n_top by score, union force_add).

    Force-added genes not present in the matrix are dropped with a warning
    rather than silently ignored.
    """
    ranked = rank_by_abs_deviation(tpm_filtered, mad_stat=mad_stat, log=log)
    top = ranked.head(n_top).index

    present = [g for g in force_add if g in tpm_filtered.index]
    missing = [g for g in force_add if g not in tpm_filtered.index]
    if missing:
        print(f"[warn] force-add genes not in matrix, skipped: {missing}")

    return top.union(pd.Index(present))


if __name__ == "__main__":
    import sys
    path = sys.argv[1]  # path to TPM_filtered.csv
    tpm = pd.read_csv(path, index_col=0)
    print(f"loaded {path}: {tpm.shape[0]} genes x {tpm.shape[1]} samples\n")
    for stat in ("mean", "median"):
        genes = select_mad_features(tpm, n_top=5000, mad_stat=stat, log=True)
        n_forced_in = sum(g in set(genes) for g in FLOWERING_LOCI)
        print(f"MAD_STAT={stat:6s} -> {len(genes)} genes  "
              f"(all {n_forced_in}/5 flowering loci present)")
