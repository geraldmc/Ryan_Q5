import pandas as pd
import numpy as np

FLOWERING = ["AT5G15840", "AT2G22540", "AT1G65480", "AT2G45660", "AT5G10140"]  # CO, SVP, FT, SOC1(AGL20), FLC

tpm  = pd.read_csv("./data/tpm_tables/TPM_filtered.csv", index_col=0)          # 19,283 × 68, raw TPM
lv   = np.log1p(tpm.values.astype(float))                        # (b) log transform
mad  = pd.Series(np.abs(lv - lv.mean(axis=1, keepdims=True)).mean(axis=1),  # (a) MEAN abs dev
                 index=tpm.index)
top5000     = mad.sort_values(ascending=False).head(5000).index
final_genes = top5000.union(pd.Index(FLOWERING))                 # ~5,000–5,005 genes
# then subset TPM_filtered to final_genes, z-score per gene, hand to the model
