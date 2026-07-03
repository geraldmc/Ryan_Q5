# Virtual Lab — 2026-07-01 — Student Grouped-Shapley Project: Assumptions-to-Test Handoff

## Purpose of this document

A student has proposed an original project: a **model-agnostic grouped-Shapley
attribution pipeline for transcriptomic data**, with coalitions drawn from WGCNA
co-expression modules, a "Two-Level Efficiency Axiom," and a directional regulatory
check against the ATRM map. The goal of the current line of work is **not** to build
it yet. It is to step through the assumptions the proposal makes, one at a time and
critically, to decide two things: whether the project is coherent at all, and whether
it can be finished inside the program window.

This session settled some of those assumptions and surfaced several more. The main job
of this document is to **compile the full list of assumptions still to test into a
single ordered agenda**, so the next chat can open directly on the first one rather
than rebuild the context. The early promise in the previous chat — "there's a longer
list worth going through" — is that list, written out below.

The testbed is now fixed: **Redmond, Ronald, Davis & Ezer (2024)**, *Single-plant-omics
reveals the cascade of transcriptional changes during the vegetative-to-reproductive
transition*, The Plant Cell 36:4594–4606 (GEO GSE242681; repo
`stressedplants/SinglePlantOmics`). Full paper has been read.

---

## What the testbed gives us (settled facts from the paper)

- **Task:** predict bolting status (binary). 68 plants after filtering — **23 bolted,
  45 not bolted.**
- **The paper's own model:** elastic-net **logistic regression**, leave-one-out
  cross-validation, ~85% accuracy on regulator genes (85.3% headline; 80.8% full
  transcriptome; 76.5% variant-only).
- **Trained models are committed** to the repo, so nothing needs retraining to be
  reachable.
- **Feature sets in play:** ~19,283 filtered genes (full transcriptome) or ~180
  regulator genes (the paper's curated transcription-factor / signalling set, used to
  keep coefficients interpretable). TPM, z-scored per gene.
- **A directed regulatory network already exists in the paper:** DynGENIE3 filtered
  against DAP-seq. ATRM adds curated, signed transcription-factor-to-target edges on
  top. Together these give a ready ground truth for "did attribution land on the
  upstream regulator or its downstream targets."

---

## What this session resolved

**The two gates pass.** Data is reachable by one clone; compute is trivial on free
Colab. All three proposed models (random forest, ridge, two-layer neural network)
train in seconds; exact Shapley on a linear model is closed-form. Running the pipeline
is not where the risk lives. This confirms the June 29 altitude read.

**Model-agnosticism is claimable only in the mechanical sense, not the evidentiary
sense.** The central finding: at n=68, cross-model agreement cannot tell you the
attributions are correct, so "model-agnostic" holds only in the trivial sense that the
code runs on any model. Two reasons: (a) bootstrap-resampling the 68 plants reshuffles
each model's top-attributed genes substantially, and that within-model wobble is wider
than the between-model differences the comparison depends on; (b) ~55% of the
transcriptome moves on the single bolted-vs-unbolted axis, so any adequate model
recovers the same dominant signal and agreement is near-guaranteed by the data. The
locked wording is saved as an artifact (see below). **Action carried forward:** the
student must actually *run* the plant-bootstrap to turn "there is noise" from an
assertion into a shown figure. This is modest and doable.

**The neural net is the weak leg.** A two-layer network on 68 samples is
over-parameterized; SHAP on it attributes to the overfitting, not the biology, and its
top genes will swing with the seed. Recommendation on the table (not yet Gerald's
decision): cut it, or demote it to a deliberate teaching moment — *here is why 68
plants can't support a network, and here is what its unreliable attributions look
like.* That framing is on-theme for the program's shortcut-learning through-line.
A random forest already carries the one genuine nonlinear test; ridge on a 0/1 label
is a linear model and so is a validation anchor, not a third independent test.

**The random-forest configuration is drafted** (artifact below): leave-one-out
(forced by n=68, matches the paper), `class_weight="balanced"` with balanced accuracy
reported instead of raw accuracy (forced by 23/45), `min_samples_leaf` pinned rather
than tuned (tuning on 68 samples is itself unstable — the paper's `l1_ratio` flipping
across folds is the same disease), a fixed seed, `predict_proba` as the only exposed
surface, and a plant-bootstrap loop for the variance check. The feature set is left as
an explicit switch, not a silent default.

**The three-bottleneck claims in the rationale were assessed** against the citations
provided:

- *Bottleneck 1 (credit dilution):* best-supported of the three but **overstated**.
  Fixes: say "the standard SHAP *estimators* assume independence," not "SHAP assumes
  independence" (it is a property of how KernelSHAP / interventional TreeSHAP
  marginalize, not of the Shapley value); attribute the splitting to **correlation,
  not causation**; and note that this dilution is Shapley obeying its own fairness
  axioms — a "bottleneck" only relative to the goal of naming one causal driver.
  Aas, Jullum & Løland (2021) is the correct anchor. Lundberg & Lee (2017) is fine as
  the primary source. Hooker et al. (2019) is weak here — it is the remove-and-retrain
  benchmark and belongs nearer bottleneck 3.
- *Bottleneck 2 (upstream buried under downstream):* **its citation [11] was not in
  the set provided — still outstanding.** Independent of the source, the claim as
  phrased is wrong about mechanism: SHAP does not give higher attribution because a
  gene has a bigger expression change; it attributes by contribution to the
  *prediction*. Downstream effectors correlate more tightly with the phenotype, so a
  model trained to predict the phenotype leans downstream and SHAP faithfully reports
  that. The burial is a property of the **model and the data, not of SHAP**. This is
  the conceptual crux: grouping (WGCNA) plus the ATRM directional check **detects**
  whether attribution landed upstream or downstream — it does not **move** it upstream.
  The rationale must be reframed from "our method solves this" to "our method measures
  this."
- *Bottleneck 3 (noise / variance):* substantively true but **under-anchored**. Azodi,
  Tang & Shiu (2020) is a review that gestures rather than establishes the specific
  claim. Replace its load-bearing role with the student's **own bootstrap-variance
  result** (the same plant-resampling figure) and cite the review only as context.

---

## The assumptions still to test — the agenda for the next chat

Ordered by dependency: earlier items block later ones. Recommendation is to start at
the top.

**1. What does the second efficiency clause actually mean?** *(Linchpin. Deferred
repeatedly; take it first.)* The proposal says "module credits sum to prediction offset
from ground truth." Standard Shapley efficiency sums attributions to *model output
minus baseline*, not to distance from the true label. Two readings: (a) it is a slip
for the standard clause, in which case the two-level property is just the **Owen (1977)
value the student already cites, and the axiom carries no novelty**; or (b) it is a
deliberate redefinition against the true label, in which case it is **not standard
Shapley and the whole estimator changes**. Needs the student's actual intent stated
plainly. This determines whether there is a novel axiom at all, and what the estimator
is even computing.

**2. What single gene set do the models and the WGCNA coalitions both sit on?**
*(Blocks almost everything downstream.)* The fork: full transcriptome (~19,283) makes
WGCNA modules trustworthy but makes the random forest and network overfit harder and
makes within-module fine-mapping run across thousands of genes; 180 regulators makes
the model tractable and interpretable but is too few genes for a sound co-expression
network. These pull in opposite directions and cannot both be satisfied. Must be
resolved before any model is the "right" testbed and before axiom 2 has a defined
target.

**3. Do the WGCNA coalitions actually satisfy Owen's precondition on this data?**
*(Depends on 2.)* Owen's a-priori-union construction requires **between-module
independence**. But 55% of the transcriptome moves on one binary axis, so a
co-expression network built here will have modules correlated *through* bolting. If
between-module independence fails, credit dilution is not solved — it just moves up to
the between-module level. This is testable directly (measure inter-module correlation)
and should be tested, not assumed.

**4. Does within-module fine-mapping inherit the same correlation problem one level
down?** *(Depends on 2 and 3.)* Even if grouping fixes dilution between modules, genes
*within* a module are by definition co-expressed. Within-module Shapley then faces the
identical correlated-feature issue at the finer scale. Need to state whether the method
claims trustworthy per-gene fine-mapping inside modules, and if so, on what basis.

**5. Which SHAP perturbation mode is pinned, and why?** Interventional (marginal) vs
conditional / correlation-respecting materially changes attributions on co-expressed
genes — flagged in the June 29 assessment as a fork that must be pinned deliberately.
Not yet discussed. Interacts with bottleneck 1, since that whole claim is about the
independence assumption baked into the marginal mode.

**6. Reframe the bottleneck claims and supply the missing reference.** Fold in the
three assessments above: narrow bottleneck 1, reframe bottleneck 2 from "solves" to
"detects," re-anchor bottleneck 3 to the student's own bootstrap. **Outstanding input
needed: reference [11]** for bottleneck 2.

**7. Decide the neural net's fate.** Cut, or keep as an explicit teaching moment about
over-parameterization at small n. A decision, not an analysis.

**8. Finish the model-agnosticism claim by running the bootstrap.** The honest wording
is locked; the demonstration is not built. This is the figure that supports both the
agnosticism paragraph and bottleneck 3.

**9. Timeframe and scope verdict.** Emerges once 1–2 are settled. If the project is
scoped to the paper's committed linear models, it collapses to a very doable four-week
build but the novelty shrinks to the coalition choice and the directional criterion.
If the student trains their own models to honor "agnostic," n=68 makes the evidentiary
claim shaky and adds a training burden. The program window is five weeks (June 22 –
July 31); we are already in week two, so the effective runway is roughly four weeks.

---

## Artifacts produced this session (carry into the new chat)

### A. Locked wording — model-agnosticism, tight technical version

> Model-agnosticism here is mechanical, not evidentiary. The estimator needs only a
> prediction function, so it runs unchanged on the random forest, ridge, and neural
> network — true by construction, but silent on whether the attributions are correct.
> The intended stronger claim — that cross-model agreement certifies real biological
> signal — fails at n=68. Bootstrapping the 68 plants shows within-model attribution
> variance large enough to swallow the between-model differences the comparison depends
> on. And because ~55% of transcripts move on the bolted-versus-unbolted axis, any
> adequate model recovers the same dominant signal, so agreement is near-guaranteed by
> the data and says nothing about the method. Agnosticism is therefore claimable only
> mechanically; cross-model agreement is context, not proof. The evidentiary version
> would need a sample large enough for a held-out test set and for between-model
> agreement to exceed bootstrapped within-model noise.

### B. Random-forest configuration (pseudocode)

```python
# The RF is a prediction function for the estimator, evaluated honestly — not an end in itself.

import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import LeaveOneOut, cross_val_predict
from sklearn.metrics import balanced_accuracy_score

SEED = 0   # pinned; the only source of RF randomness. Varied deliberately, never incidentally.

# --- Feature set: the UNRESOLVED FORK, surfaced rather than hidden ---
#   X_full : 68 x ~19,283  whole filtered transcriptome  -> WGCNA modules valid, RF overfits harder
#   X_reg  : 68 x ~180      regulator genes (paper's set) -> tractable model, too few genes for sound WGCNA
FEATURE_SET = "regulators"                      # {"regulators", "transcriptome"} — decide before trusting output
X = X_reg if FEATURE_SET == "regulators" else X_full   # TPM, z-scored per gene (paper convention)
y = bolting_status                              # 1 = bolted (23), 0 = not bolted (45)

def make_rf(seed):
    return RandomForestClassifier(
        n_estimators=1000,        # many trees: attribution stability matters more than speed at this size
        max_features="sqrt",      # standard, but correlated genes make this choice consequential
        min_samples_leaf=3,       # guard against single-plant leaves; main overfitting knob (see note)
        class_weight="balanced",  # 23 vs 45 — don't let the 45 negatives set the threshold
        bootstrap=True,
        random_state=seed,
        n_jobs=-1,
    )

# --- Honest evaluation: leave-one-out, because 68 samples cannot spare a test set ---
# Mirrors the paper's own scheme; this is the correct choice, not a shortcut.
oof_proba = cross_val_predict(make_rf(SEED), X, y,
                              cv=LeaveOneOut(), method="predict_proba")[:, 1]
oof_pred = (oof_proba >= 0.5).astype(int)

# Balanced accuracy, never raw accuracy — raw is inflated by the majority class.
print("balanced accuracy (LOOCV):", balanced_accuracy_score(y, oof_pred))

# --- The object the estimator actually consumes ---
final_rf = make_rf(SEED).fit(X, y)             # fit once on all 68 for attribution
predict_fn = lambda M: final_rf.predict_proba(M)[:, 1]   # inputs -> scores; nothing internal exposed

# --- The variance check that keeps the agnosticism claim honest ---
# Resample PLANTS (not genes), refit, recompute attributions downstream.
# RF seed held FIXED so the only thing varying is which plants were drawn —
# this isolates sampling-of-plants variance from the tree's internal randomness.
def bootstrap_models(n_boot=200):
    rng = np.random.default_rng(SEED)
    for _ in range(n_boot):
        idx = rng.choice(len(y), size=len(y), replace=True)
        yield make_rf(SEED).fit(X[idx], y[idx])
```

---

## Outstanding inputs before or during the next chat

- **Reference [11]** for bottleneck 2 — the one claim that is both the conceptual spine
  of the method and currently unverifiable.
- The student's **plain statement of what "prediction offset from ground truth" means**
  (agenda item 1). Without it, the axiom cannot be judged novel or coherent.
- Optional: pull the exact passages from Aas, Jullum & Løland (2021) and Azodi, Tang &
  Shiu (2020) to lock bottleneck wording for an eventual write-up.

## Recommended opening move for the new chat

Start at agenda item 1 (the efficiency clause). Everything else — novelty, estimator
design, whether the feature-set fork even has a well-defined target — hangs off what
that clause is actually asserting.
