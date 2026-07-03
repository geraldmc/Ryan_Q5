# Virtual Lab — 2026-07-01 — Modeling Track: Claude Code Kickoff Brief

## What this is

A kickoff brief for a **separate Claude Code session** that will build and verify the
prediction models for the grouped-Shapley project, working against the Redmond et al.
(2024) single-plant-omics repository. A parallel "assumptions track" (in the Notion/chat
Project) is still deciding the conceptual shape of the project. **This session does the
mechanical build; it must not silently resolve the two open decisions listed below.**

Repo: `https://github.com/stressedplants/SinglePlantOmics` — public.
Dataset: GEO GSE242681. Task: predict bolting status (binary) from gene expression.
68 plants after filtering — **45 not bolted (0), 23 bolted (1).**

---

## Ground rules for this session

- **The committed code is the source of truth.** Everything in the "recorded layout"
  below came from a clone in a previous session and is written from memory of that
  clone. On your own clone, confirm the real file tree and read the actual scripts
  before trusting any path, filename, or behavior stated here. If reality disagrees
  with this brief, reality wins — and flag the difference.
- **Do not pick a gene set. Do not decide reuse-vs-retrain.** Those are the two forks
  below; they belong to Gerald and to the assumptions track. Leave the feature set as an
  explicit switch, never a baked-in default.
- **Reproducibility is a first-class requirement**, not a nice-to-have. Pin the
  environment, record package versions (scikit-learn especially — see the pickle note),
  set and record seeds, and save per-fold outputs.

---

## Recorded repository layout (verify on clone)

- **Committed trained models** live under the `pheno_prediction` outputs directory —
  real fitted scikit-learn objects (roughly 0.7–10.8 MB), not stubs. Filenames carry a
  `_smaller_save`-style suffix, which suggests trimmed objects. **These are `.sav`
  pickles and are scikit-learn-version sensitive**, so confirming they load without
  error in this environment is step one, before anything leans on them.
- **The paper's training recipe** is in `pheno_prediction/train_elastic_nets.py`:
  scikit-learn `ElasticNetCV` / `LogisticRegressionCV` inside a hand-rolled
  leave-one-out loop. Binary bolting uses the logistic path. So **the committed
  classifier is an elastic-net logistic model** — good to know for the reuse fork below.
- **Labels:** `pheno_prediction/data/phenos_to_predict.csv`, 68 rows, with `bolting` as
  a Y/N column (alongside leaf number, leaf area, biomass). Confirm the Y/N encoding maps
  to 1 = bolted (23) and 0 = not bolted (45), and watch the direction.
- **Two committed gene-set matrices** (genes in rows, 68 sample columns, TPM z-scored
  per gene):
  - `data/TPM_z_scored.csv` — **19,283 genes** (full transcriptome).
  - `data/TPM_z_scored_only_regs.csv` — **1,159 genes** (regulator set).
  - Note: the regulator set is **1,159 genes, not ~180** — an earlier number that turned
    out to be a phantom. The committed matrix is 1,159.

---

## Environment and reproducibility notes

- **Clone shallow, and clone on Linux.** Use `git clone --depth 1`. Avoid macOS here:
  case-insensitive filesystems silently drop files whose names differ only by case
  during clone. Colab (Linux) or any Linux environment is safe.
- **Record the scikit-learn version** you load the pickles under, and pin it. Because
  the committed models are version-sensitive pickles, a silent version mismatch is the
  most likely first failure.
- Set a fixed seed as the only source of model randomness; vary it deliberately, never
  incidentally.

---

## The two open forks — DO NOT resolve these here

**Fork 1 — which gene set the models sit on.** Three universes are in play:
- `TPM_z_scored.csv` — 19,283 genes (full transcriptome). Committed.
- `TPM_z_scored_only_regs.csv` — 1,159 genes (regulators). Committed.
- The student's proposal builds its own set: **top 5,000 by mean absolute deviation,
  with CO/SVP/FT/SOC1/FLC force-added.** This matches neither committed matrix, so
  choosing it means **retraining from scratch.**

Until Gerald settles this, wire the feature set as a switch (e.g. a `FEATURE_SET`
variable selecting among the matrices), so the same harness runs on any of them.

**Fork 2 — reuse the committed models, or train fresh.** Sharpened by the recipe above:
- The committed models are the paper's **elastic-net logistic** classifier. "Reuse"
  only covers a logistic baseline.
- The student's plan calls for **ridge logistic (C=0.01), a random forest (~500 trees),
  and a two-layer MLP.** The random forest and MLP **do not exist in the repo and must
  be trained fresh regardless of how Fork 2 is decided.**
- This choice also feeds the "model-agnostic" claim on the assumptions track, so it is a
  deliberate decision, not a coding default.

---

## Safe to build now (independent of both forks)

1. **Clone and inventory** the repo; confirm the real layout against this brief.
2. **Load the committed models** and confirm they deserialize without error in this
   environment (the pickle-version check). This is diagnostic only — it does not commit
   you to reusing them.
3. **Load and check the labels:** 68 rows, confirm the 45/23 split and the encoding
   direction.
4. **Load both committed matrices;** confirm shape (genes × 68), orientation, and that
   values look z-scored.
5. **Stand up the evaluation harness**, feature set left as a switch:
   - leave-one-out cross-validation (forced by n = 68; matches the paper);
   - **balanced accuracy, not raw accuracy** (forced by the 23/45 imbalance);
   - fixed, recorded seed; per-fold predictions saved.
6. **Build the plant-bootstrap loop:** resample the 68 plants with replacement, refit,
   hold the model seed fixed so the only thing varying is which plants were drawn. This
   is the variance check the agnosticism claim depends on.
7. **Reproducibility scaffolding:** pinned environment, recorded versions, saved outputs.

A drafted random-forest configuration already exists in the prior handoff
(`Virtual_Lab-...-Assumptions-Handoff`, "Artifact B"), including the feature-set switch,
`class_weight="balanced"`, a pinned `min_samples_leaf`, and the bootstrap loop. Gerald
can hand that over as the starting point for step 5–6 if wanted.

---

## Waits on the forks (do not start until Gerald decides)

- The **final training run** and which models become "the" testbed — waits on both forks.
- Anything **WGCNA / SHAP / attribution** downstream — that is later, and lives on the
  other track anyway.

---

## First concrete step

Clone shallow on Linux, inventory the tree against the recorded layout, and load one
committed model plus both matrices to confirm they open cleanly in this environment.
Report what actually loaded, with the scikit-learn version used. Stop there and check in
before building the harness, so the layout is confirmed before anything is built on it.
