# Virtual Lab — 2026-07-01 — Student Grouped-Shapley Project: Contributions and Research Question — Assessment Handoff

## Purpose of this document

This is the second session of the assumptions pass on the student's proposed
grouped-Shapley project. The first session (handoff
`Virtual_Lab-20260701-Shapley-Assumptions-Handoff.md`) compiled the agenda; this
session worked the top of it and tested two of the three "novel contributions" plus the
research question, all against the student's full written proposal
(`Ryan-iRes-Plan-06302026.pdf`), which was read in full this session.

The next chat will start clean with new inputs from Gerald: an **updated** research
question and rationale, a new **step-by-step methods list**, the **originating paper**
(Redmond et al. 2024) itself, and a couple of supporting papers. The paper's code
repository is confirmed public and was cloned and inspected this session (see "Verified
repository state" below). Because the research question and rationale are being revised,
the point of the research-question section below is to hand forward **the tests to
re-apply to the new wording**, not verdicts on wording that is about to change.

The testbed is unchanged: **Redmond, Ronald, Davis & Ezer (2024)**,
*Single-plant-omics reveals the cascade of transcriptional changes during the
vegetative-to-reproductive transition*, The Plant Cell 36:4594–4606 (GEO GSE242681;
repo `stressedplants/SinglePlantOmics`). 68 plants after filtering (23 bolted, 45 not),
binary bolting task, trained models committed to the repo (verified this session).

---

## The frame we are working in

The proposal claims three "novel contributions of this paper" (Rationale, final
paragraph):

1. Derive the player coalitions from co-expression structure (WGCNA) rather than from
   spatial segmentation, external pathway annotation, or genomic distance.
2. Enforce a "Two-Level Efficiency Axiom": gene attributions sum to the module credit,
   and module credits sum to prediction offset from ground truth.
3. Evaluate attribution quality against the ATRM regulatory map with a directional
   criterion, testing whether attribution concentrates on upstream transcription-factor
   regulators relative to their downstream targets.

The plan for the pass is to unpack and test each of these one at a time, then the
research question that sits on top of them. This session did contribution (2) (the
efficiency clause), contribution (1), and a first pass on the research question.
Contribution (3) is not yet unpacked.

---

## What this session resolved

### Efficiency clause — contribution (2) — RESOLVED: it is a slip, not a redefinition

Agenda item 1 asked what "module credits sum to prediction offset from ground truth"
means, with two readings on the table: (a) loose wording for the standard clause, in
which case the property is just the Owen (1977) value already cited and there is no new
axiom; or (b) a deliberate redefinition against the true label, in which case the whole
estimator changes.

The full proposal answers this itself, because it says the property two different ways.
The Rationale says "prediction offset from ground truth." But the **Methods** section,
where the computation is actually specified, says the opposite: "Owen value rescaling
... module credits sum to full prediction difference from **baseline**," followed by
"Satisfies the efficiency axiom at both levels," and a verification step that measures
how far the summed attributions deviate from that total. When a proposal's framing and
its method disagree, the method is the more reliable signal of what will actually be
built. The method is internally consistent and standard.

**Verdict: reading (a).** The clause is standard two-level Owen efficiency — gene
attributions sum to module credit, module credits sum to prediction-minus-baseline.
"Ground truth" is loose wording in the story, not a redefinition. There is no
error-anchored value and no regulatory-map anchor. Two consequences to record for the
eventual proposal revision:

- **Contribution (2) is not novel and should come off the list of novel contributions.**
  The Owen value *has* two-level efficiency by construction; you do not invent or
  "enforce" it. Citing Owen (1977) and then claiming his own efficiency property as a
  contribution is self-defeating.
- **The Rationale sentence needs its wording fixed** from "prediction offset from ground
  truth" to "prediction offset from baseline (the model's expected output over the
  background set)," so the story matches the method.

**Parked for the estimator-design item (roughly agenda item 5):** the Methods route to
two-level efficiency is "run a separate Shapley game inside each module, then rescale
proportionally so gene attributions sum to the module credit." Proportional rescaling is
not, in general, the true Owen within-union value. So "does the estimator compute the
Owen value, or a rescaled approximation of it?" is a real correctness question. It is
about whether the method *achieves* the efficiency, not what the clause *means*, so it
was not part of item 1 — but it must be tested before the estimator is trusted.

### Contribution (1) — TESTED: the design choice survives; the validity claim fails

Contribution (1) is two claims in one sentence.

**The design choice** — derive coalitions from co-expression structure rather than from
pathway databases, spatial layout, or genomic distance — **survives, and is where the
genuine novelty of (1) sits.** Using data-driven co-expression modules as the grouping,
instead of a curated pathway annotation (the "post-hoc pathway aggregation" the proposal
criticizes) or an arbitrary partition, is a defensible and reasonably original choice
for *what the a priori unions should be*. Keep it.

**The validity claim** — that WGCNA modules "satisfy the formal condition for a priori
unions: that members are cohesive but independent to other modules" — **fails on both
sides of the claimed condition.**

- *Owen side: there is no such formal condition.* In Owen's construction, an a priori
  union is a grouping supplied from outside the math, reflecting which players are more
  likely to act together (affinity, or a prior agreement). The value is then defined for
  *any* partition — the only requirement is that the groups be disjoint and exhaustive.
  There is no precondition that the groups be statistically independent of one another;
  the Owen value exists and is unique regardless. So "satisfies the formal condition ...
  independent to other modules" checks a box Owen never drew; the independence half is
  imported from elsewhere and attributed to Owen.
- *WGCNA side: modules are not built to be independent anyway.* WGCNA finds clusters of
  highly correlated genes (internally cohesive, yes), but between modules the eigengenes
  routinely correlate. WGCNA has an entire companion methodology — eigengene networks
  and "meta-modules" (Langfelder & Horvath 2007) — that exists precisely because modules
  relate to one another. The standard `mergeCloseModules` step only collapses the
  *most* correlated module pairs above a chosen cut height, leaving the survivors less
  correlated but not independent. Even read charitably, as a desideratum for a good
  grouping rather than a validity requirement, WGCNA does not deliver between-module
  independence and does not claim to.

**Consequence:** between-module independence is not a precondition the method
*satisfies* — it is an empirical property the method must *measure* on this dataset, and
it matters because the whole credit-dilution benefit of grouping depends on it. If
modules correlate through bolting, dilution is not solved; it moves up to the
between-module level. That is agenda item 3. Testing contribution (1) hands us item 3 as
the real question.

**Pattern worth carrying forward:** the same rhetorical move appears in both (2) and
(1). "Enforce two-level efficiency" dressed a free property as a contribution.
"Satisfies the formal condition for a priori unions" dresses an unmet, testable property
as a satisfied precondition. The student reaches for a mathematical-sounding guarantee
at exactly the points where the real situation is empirical and needs a test. Read the
rest of the proposal — including the incoming updated rationale — with that lens.

### Research question — ASSESSED (re-apply to the updated wording; do not treat as final)

The current wording: *"Does applying a two-level Owen value framework, using WGCNA
co-expression modules as player coalitions, concentrate attribution credit on upstream
transcription-factor regulators relative to their downstream targets more effectively
than standard KernelSHAP, across three classifiers trained on the Arabidopsis flowering
transition?"* This is being revised, so what follows are the two structural assumptions
and the tests to run against whatever the new version says.

*Background fact used below:* KernelSHAP recovers each feature's attribution by fitting a
weighted least-squares regression over coalitions (features switched on/off, absent ones
filled from a background), with the sum pinned to prediction-minus-baseline. The number
of coefficients fit equals the number of features.

- **Assumption one — that grouping "concentrates credit on upstream regulators more
  effectively."** This is the same issue as the efficiency clause and bottleneck 2,
  surfacing in the question's main verb. The total credit is pinned to
  prediction-minus-baseline for every method; grouping changes *how* the fixed total is
  split among correlated genes, and adds no information about which genes are upstream
  causes. There is no mechanism in the Owen construction that lifts a regulator over its
  targets. Whether a regulator gets credit is a fact about the model and the data — did
  the classifier lean on that gene — not about the grouping. The student's own Figure 6
  note concedes this: CO may never rank because it has little expression variance, so no
  attribution method can credit it. Grouping *measures* where credit landed; it does not
  *move* credit upstream. The verb "concentrate ... more effectively" assumes the thing
  we established grouping cannot do.
- **Assumption two — that "more effectively than standard KernelSHAP" is a fair
  contrast.** At the gene level, flat KernelSHAP is a weighted regression over roughly
  5,000 genes. The proposal budgets 1,000 coalition samples and calls that "sufficient"
  — but that justification is written for the *module-level* macro-game, where there are
  only a few dozen players. Fitting ~5,000 gene coefficients from 1,000 samples is
  underdetermined by roughly fivefold, so the recovered per-gene attributions are noisy
  and lean on whatever regularization the solver applies. "Owen beats flat KernelSHAP"
  then risks collapsing into "grouping cut the dimensionality, so its estimate is less
  noisy" — an artifact of starving the baseline, not evidence that grouping recovers
  biology. As written, the comparison varies dimensionality and grouping at the same
  time and reads the result as if only grouping changed. **To be fair, the baseline must
  match: coalition samples scaled to gene count, same background, same estimator, so any
  difference is attributable to grouping and not to sample starvation.**

Two smaller points fall out. The comparative framing presupposes that at least one
method concentrates upstream, but the rationale's own logic predicts both land
downstream (the model leans on downstream effectors because they track the phenotype), so
the likely real result is "both rank downstream higher, Owen slightly less so" — a
contrast between two failures, not a win. And the outcome metric's power depends entirely
on how many of these genes ATRM annotates as directed TF→target edges; if coverage is
thin, the rank ratio and Mann-Whitney test have little to compare no matter which method
wins. (That is the contribution-3 flag, below.)

**The answerable version is a "detect" question, not a "beat" question:** where does
attribution land — upstream or downstream — and does grouping change that landing,
measured against ATRM, with the baseline made fair. Re-apply this framing to the updated
wording.

---

## Verification status of the cited papers

- **Owen (1977) [17].** Only the preamble (printed pp. 76–77) was obtained; the formal
  definition of the value and its axioms (pp. 78–88) were not. The independence finding
  above does not hinge on the axioms — independence is simply absent from Owen's
  construction, and the value is defined for any partition, which is standard. If
  axiom-level sourcing is ever wanted for a write-up, note the practical obstacle: this
  is a 1977 Springer *Lecture Notes in Economics and Mathematical Systems* book chapter
  (Morgenstern festschrift, *Mathematical Economics and Game Theory*, Henn & Moeschlin
  eds.), and institutional journal access typically does not reach older Springer
  Lecture Notes volumes. A print holding or interlibrary request on the book title is
  usually faster than fighting the DOI.
- **Langfelder & Horvath (2008) [18] (WGCNA).** Verified by search this session; enough
  was confirmed to settle the WGCNA side of contribution (1). The full text is not
  needed. Remaining WGCNA questions are empirical (item 3, measuring inter-module
  correlation on this data) or procedural (soft-thresholding, TOM, dynamic tree cutting),
  and can be assessed without it. Fetch specific passages only if a specific question
  needs one.
- **Jin et al. (2015) [19] (ATRM).** Not yet pulled; needed for contribution (3). The
  paper will confirm the map's design (directed, signed TF→target edges) but will **not**
  settle the question that actually decides whether (3)'s metrics work: whether ATRM's
  **edge list covers the specific flowering regulators as directed edges** — CO→FT,
  CO→SOC1, SVP→FT, and so on. That is a "read the actual edge table against this gene
  set" task, not a "read the paper" task. Do not mistake "ATRM exists and is directed"
  for "ATRM covers what we need."
- **Reference [11] — now identified.** The July 1 handoff flagged bottleneck 2's citation
  [11] as missing. In the full proposal, [11] is **Simpson (2004)**, "The autonomous
  pathway: epigenetic and post-transcriptional gene regulation in the control of
  Arabidopsis flowering time." This is a plant-biology review of flowering-time
  regulation. It does not — and cannot — support the claim it is attached to (that SHAP
  gives downstream genes higher attribution because of bigger expression changes), which
  is a claim about SHAP mechanics, and which we already found wrong on its own terms
  (SHAP attributes by contribution to the prediction, not by expression magnitude). So
  [11] is resolved as identified, but the support gap under bottleneck 2 remains.

---

## Verified repository state (`stressedplants/SinglePlantOmics`)

The repo is public and was shallow-cloned and inspected this session, so "models are
committed and reachable" is no longer an assumption. What is actually there:

- **The bolting models are committed Python pickles** (scikit-learn), under
  `desync_python_scripts/pheno_prediction/outputs/` — real fitted objects (0.7–10.8 MB),
  not stubs. They load in Python directly; no R is needed to reach the paper's models.
  One caveat before anything leans on them: `.sav` pickles are scikit-learn-version
  sensitive, and the `_smaller_save` naming suggests a trimmed object, so confirming they
  load without error in the target environment is the sensible first step.
- **The training recipe is verified from source**, not from paraphrase:
  `pheno_prediction/train_elastic_nets.py` uses scikit-learn `ElasticNetCV` /
  `LogisticRegressionCV` with a hand-rolled leave-one-out loop (parallelized). Binary
  bolting uses the logistic path.
- **The labels are committed**: `pheno_prediction/data/phenos_to_predict.csv`, 68 rows,
  with `bolting` as a Y/N column (alongside leaf number, leaf area, biomass).
- **Both candidate gene-set matrices are committed and ready** (genes in rows, 68 sample
  columns, TPM z-scored):
  - `data/TPM_z_scored.csv` — **19,283 genes** (full transcriptome).
  - `data/TPM_z_scored_only_regs.csv` — **1,159 genes** (the regulator set).

**Correction to record: the regulator set is 1,159 genes, not ~180.** We had been
carrying "~180 regulators" from the proposal and the earlier notes; the committed matrix
the models were trained on has 1,159. By the source-of-truth rule the burden now flips to
explaining where "180" came from — it may be a phantom, or a further-curated
transcription-factor-only subset the student had in mind — but the artifact says 1,159.
This weakens the "regulators keep the model tractable" argument (1,159 features on 68
samples is still very wide) and it changes the target agenda item 2 has to choose among.

---

## The agenda from here

Carried from the July 1 agenda, updated with this session's results:

1. Efficiency clause — **done** (reading a; contribution 2 off the novelty list; wording
   fix recorded; rescaling correctness parked to item 5).
2. **Gene-set fork** — still open, and it blocks the most. Three concrete options now,
   two of them sitting ready in the repo. The full transcriptome (**19,283** genes,
   `TPM_z_scored.csv`) makes WGCNA trustworthy but the models overfit harder and
   within-module fine-mapping runs across thousands of genes. The committed regulator set
   (**1,159** genes, `TPM_z_scored_only_regs.csv` — corrected up from the ~180 we had
   carried) is more tractable but still wide on 68 samples and is thin for a sound
   co-expression network. And the proposal's own WGCNA plan is a **third** universe —
   **top 5,000 by mean absolute deviation, with CO/SVP/FT/SOC1/FLC force-added** — which
   matches neither committed matrix. Re-open the fork against all three, noting that the
   models were trained on the first two, so choosing the third would require retraining.
3. **Between-module independence test** — promoted; surfaced directly by contribution
   (1). Testable on the data (measure inter-module eigengene correlation). This decides
   whether grouping's credit-dilution benefit is real or just moved up a level.
4. Within-module fine-mapping — does the correlated-feature problem recur one level down,
   among genes inside a module.
5. SHAP perturbation mode (interventional vs conditional) **and** the parked
   rescaling-vs-true-Owen correctness point.
6. Bottleneck reframe — narrow bottleneck 1, reframe bottleneck 2 from "solves" to
   "detects," re-anchor bottleneck 3 to the student's own bootstrap. Reference [11] is
   now identified (Simpson 2004) but does not support the claim.
7. Neural-net fate — cut, or keep as a teaching moment about over-parameterization at
   n=68.
8. Run the plant-bootstrap to turn "there is noise" into a shown figure.
9. Timeframe and scope verdict.

**Not yet started:** contribution (3), the ATRM directional criterion — the last of the
three contributions to unpack.

---

## New inputs arriving in the next chat (from Gerald)

- **Updated research question and rationale.** Re-apply the two structural tests above to
  the new wording; do not assume this session's assessment carries over verbatim.
- **Step-by-step methods list (new).** Assess it for coherence and for whether it fits
  the program window, against everything above — especially the gene-set fork (item 2),
  which most of the steps will silently assume.
- **Redmond et al. (2024) — the originating paper, full text.** The testbed. Read for
  the committed models, the exact preprocessing (log2(TPM+1), the `_rerun` QC drop to 68
  samples), and anything that pins the gene set.
- **A couple of supporting papers.**
- **Repository — confirmed public and cloned** (`stressedplants/SinglePlantOmics`).
  Verified this session; see "Verified repository state" above for what is committed. No
  fork or access grant is needed — a shallow clone reaches it directly and the sandbox
  can talk to github.com, so it can be re-cloned in the next chat on demand.

---

## Recommended opening move for the new chat

Load the new inputs first (originating paper, updated question and rationale, step-by-step
list). Then, in order: (1) re-test the updated research question against the two
structural assumptions above; (2) finish the contribution pass by unpacking contribution
(3), the ATRM directional criterion — this is a paper-and-edge-list check that can be run
independently; (3) settle the gene-set fork (item 2), because it defines the target for
the models, for WGCNA, and for the outcome metric, and the incoming step-by-step list
will assume it. The between-module independence test (item 3) and the rescaling
correctness check (item 5) are the two data/estimator tasks that most affect whether the
project's central claim holds, and both become concrete once the gene set is fixed.
