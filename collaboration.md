# Human and AI collaboration log

**Status:** Initial version reviewed and approved by Jim for commit. Started November 23, 2026; updated throughout the project.

## Purpose and roles

This is Jim's solo AIPI 510 Module 3 project. Codex is an AI coding and learning assistant. This file records how we work together, what AI contributes, and the decisions and review Jim provides. We will update it on each project branch and revisit it at the end for separate reflections.

Jim described this as his first full ML production pipeline and asked for a simple project with clear teaching. He expects substantial implementation help from AI, with explanations along the way. The aim is to produce a working system that he can understand and explain.

Codex has written most of the initial implementation, drafted documentation, executed checks, and performed the approved Git commands. Jim has directed the scope, selected the dataset, decided how to handle the data, asked questions about the implementation, and reviewed the work before authorizing the first commit and push. This log should not imply that Jim independently wrote or ran work performed by Codex.

## Working agreement

- Work on one agreed project step at a time, using a feature branch.
- Explain the purpose of changes and pause for material decisions and questions.
- Review the changes and relevant checks together before committing.
- Commit and push approved work; use pull requests to review changes into `main`.
- Jim reviews and merges PRs and decides when to begin the next step.
- Record AI assistance, corrections, unresolved questions, and verification honestly.
- Update this log before completing each branch. Leave Jim's personal reflections for him to write or approve.

## Choosing the project and adjusting our process

**Period:** November 21–23, 2026, before and during the first branch.

Jim asked for a manageable project that would support the assignment's full pipeline requirements and serve as a learning exercise. Codex inspected the assignment and researched several concepts, including plasma-cutting ideas. Jim rejected those options and redirected the search toward ready-made Hugging Face datasets. After comparing options, Jim selected customer churn prediction.

Codex initially moved too quickly and drafted a larger application outside the repository Jim later created. Jim explicitly asked to work together more slowly, with separate branches, explanations, and review points. Codex stopped that work. The earlier draft remains outside this repository and was not included in the first project commit. The repository's `AGENTS.md` now records the agreed pace and scope limits.

## Branch 1: Project setup and data ingestion

- **Branch:** `feat/setup-data-ingestion`
- **Date:** November 23, 2026
- **Implementation commit:** [`3b2c396`](https://github.com/jr613d/AIPI510_Module3_project/commit/3b2c3964f0b6b2a0b0a34d29b49764949d49381c) — `feat: set up project and reproducible data ingestion`
- **Recorded status:** Implementation committed and pushed. Jim approved this collaboration log and the README evaluation plan for a follow-up documentation commit on the same branch. Jim will initiate the PR; no PR or merge has been recorded here yet.

### Jim's decisions and review

- Combined project setup and data ingestion into the first branch.
- Chose to keep raw and cleaned CSVs local and commit the script, configuration, and aggregate data summary.
- Chose to retain all customers and preserve the 11 blank `TotalCharges` entries as missing values, rather than filling them with zero or deleting customers.
- Asked where the dataset came from, how it was created, and whether it contained real customer records.
- Requested the first five rows and explanations of all 21 columns.
- Questioned the README's manual line wrapping and clarified that this is a solo project with AI assistance, rather than a two-student project.
- Confirmed that he understood the work presented and authorized the first commit and push.
- Requested this ongoing collaboration log and a chance to review its first draft before committing it.
- Asked whether an evaluation metric had been defined, reviewed the explanation, and approved ROC AUC as the primary metric with precision and recall as supporting metrics.
- Requested a persistent project map, approved the nine-step branch sequence, and authorized saving, committing, and pushing it on the current branch for inclusion in the PR.

### What Codex contributed

- Inspected the clean clone and created the agreed feature branch.
- Set up an isolated Python environment and pinned the initial pandas, requests, and PyYAML dependencies.
- Wrote the ingestion script, configuration, tests, README, and agent instructions.
- Pinned the HF dataset revision and checksum, preserved the original CSV, and generated a cleaned copy and aggregate reports.
- Checked the publisher descriptions and verified that the HF download was byte-for-byte identical to the CSV in IBM's public sample repository.
- Explained that this is IBM's fictional telecom sample and that the reviewed descriptions do not document a real-customer collection process or reproducible generation algorithm.
- Displayed the first five records in grouped tables and explained identifiers, customer attributes, subscriptions, billing fields, and the churn target.
- Updated the project documents to reflect Jim's solo-project arrangement.
- Created and pushed the approved implementation commit, leaving `main` unchanged.
- Drafted this log for Jim's review.
- Explained the evaluation metrics and the limitations of accuracy for this dataset, then documented the approved evaluation plan in the README's project overview.
- Saved the agreed project map in the README and linked it from `AGENTS.md`, including the rule to start each later branch from updated `main` after Jim merges the preceding PR.

### Verification and limits

Codex ran 11 automated ingestion tests and additional checks against the full dataset. The checks confirmed that all 7,043 customers and 21 columns were retained, IDs and target labels stayed unchanged, and the 11 missing charge values remained missing. The original file matched its expected checksum, repeated ingestion produced identical outputs, and Git excluded the CSVs and virtual environment. The committed [data summary](reports/data_summary.md) records the dataset checks.

Codex authored and ran these checks. Jim reviewed the explanations and results and approved the implementation commit. Model training, API work, and cloud deployment remain future steps.

### Learning discussion and follow-up

Topics discussed included raw versus cleaned data, numeric versus categorical fields, missing values versus valid “no service” categories, features versus the target, checksums, and the difference between a local commit and a push to GitHub. We also discussed how evaluation metrics compare predictions with known outcomes, why an always-`No` model could achieve about 73.5% accuracy while catching no churners, and how ROC AUC, precision, and recall describe different aspects of performance. The evaluation plan is documented; no model scores have been measured yet.

**Jim's notes:** To be added after reviewing this draft. What is clear, what remains confusing, and what would he like to try himself?

**Codex's process observation:** The initial pace was too fast for the requested learning experience. Limiting work to the agreed branch and pausing at the data-storage and missing-value decisions gave Jim concrete choices to assess. We should maintain that pace in later steps.

## Branch 2: Cloud storage

- **Branch:** `feat/cloud-storage`
- **Date and goal:** November 23, 2026. Store the prepared CSV in Google Cloud Storage and retrieve the same bytes programmatically.
- **Later integration update:** Jim merged PR #2 into `main` at `602baf7`. The training branch incorporated this merge before its first implementation commit; the pending-review wording below describes the earlier branch-completion state.
- **Status:** Implementation, offline checks, and a real authenticated cloud download passed. Jim reviewed the explanation and walkthrough and agreed to proceed. Codex committed and pushed the storage implementation as [`652e634`](https://github.com/jr613d/AIPI510_Module3_project/commit/652e634) and opened [PR #2](https://github.com/jr613d/AIPI510_Module3_project/pull/2) into `main`; Jim's PR review and merge remain pending. Jim created the bucket, uploaded the CSV, installed the SDK, and completed local login. Codex verified the retrieved bytes; no cloud resources were created by Codex.

### Jim's decisions and questions

- Authorized starting the storage branch while another agent finishes setup/data ingestion.
- Chose Google Cloud Storage and asked to handle bucket setup and console upload himself.
- Asked what belongs in GitHub and how code connects to a cloud dataset. We discussed bucket/object addresses, configuration versus authentication, and why a private bucket does not require committing data or credentials.
- Asked Codex to implement the repository work while he prepares the bucket.
- Supplied `gs://kangaroo_baseball_field/telco_churn.csv` and a project-picker screenshot showing project ID `project-902e069e-c3ed-49c2-a13`. Codex added these identifiers to `config.yaml`; this does not establish that the object is accessible or its bytes are correct.
- Reported project number `161834179213`, bucket location `us-east1`, Standard storage, and an uploaded `text/csv` object of approximately 971.9 KB. Codex recorded these as Jim-reported console details in the walkthrough. A local check still found no `gcloud` command on PATH, no ADC file in the default location, and no explicit credentials environment variable; no cloud request was attempted.
- Asked why local authentication is needed, how other people would reproduce training without his login, and when Weights & Biases fits. We distinguished dataset access during training from public app prediction requests, discussed future cloud service identities, and explained how another person can use their own bucket and credentials. Jim restated that the repository supplies steps to rerun training using someone else's own resources. Experiment tracking remains after a working training pipeline.
- Installed the SDK and completed the local authentication flow himself, then reported that he was done. Codex confirmed the SDK and default ADC file were present without displaying credential contents.
- Reviewed the walkthrough of configuration, authentication, download, checksum verification, and atomic saving, acknowledged the explanation, and agreed to the next step of diff review, commit, and PR.

### AI assistance and implementation

- Created an isolated Git worktree so the ingestion agent's checkout stays on its own branch. Based this branch on committed ingestion work and fast-forwarded it to the newly committed roadmap before making storage edits.
- Used `feat/cloud-storage`, the name in Jim's request, and updated the roadmap's step 2 row to match. The usual sequence remains to create later branches from updated `main` after Jim's merge; this concurrent start was explicitly requested.
- Added configurable GCS transfers with a pinned fingerprint of the reviewed cleaned CSV. Downloads verify bytes before atomically saving a separate Git-ignored cloud copy. Optional uploads check the same fingerprint and refuse to replace an existing cloud object.
- Wrote the walkthrough for bucket/object configuration, local Application Default Credentials, transfer commands, and common failures. Credentials stay outside the repository.
- Added offline tests for correct bytes, wrong-file rejection, failed authentication/access, local-file preservation, and upload replacement protection.

### Verification and limits

Codex installed the dependencies in this worktree's separate `.venv`, ran all
22 unittest checks successfully, and confirmed there are no broken package
requirements. An additional offline transfer check using the actual cleaned
CSV preserved identical bytes, all 7,043 rows and 21 columns, and 11 missing
charge values. The file matched the fingerprint committed in the ingestion
summary. CLI help works; unset project configuration fails clearly before
authentication. Git ignores the data folders and virtual environment, and
`git diff --check` passed.

The first test run exposed a test-fixture path mismatch between macOS `/var`
and `/private/var`; normalizing the temporary root fixed it. Google's SDK
emits a support warning for the existing Python 3.10 environment even though
these checks pass. A supported Python upgrade remains a decision for Jim.

Codex then ran a real authenticated download on November 23, 2026. The first
attempt encountered DNS restrictions in the execution sandbox and was stopped;
the network-enabled retry succeeded. The downloaded file contained 971,878
bytes and matched the reviewed cleaned-data SHA-256. Additional checks on the
download confirmed 7,043 rows, 21 columns, unique customer IDs, 11 missing
charge values, and target counts of 5,174 No / 1,869 Yes. Git ignores the file.
This verifies actual read access and uploaded contents; the automated test
suite still uses mocked cloud responses. Jim handled the real console upload;
the optional Python upload command has only offline coverage.

Google also emitted a warning about missing quota-project configuration in
user ADC; the live download succeeded without changing it. No cloud IAM or
bucket settings were changed by Codex.
No model, experiment tracker, API, container, or application deployment is
included in this step. Codex reviewed the diff before committing. Step 1 was
merged separately into `main`; this worktree was fast-forwarded to that merge
before preparing the storage commit. Jim will review and merge the storage PR.

**Jim's learning notes:** To be added or approved by Jim after review.

**AI process observation:** Jim clarified that he wants to manage the cloud
console himself and understand the repository connection. Keep console setup
with Jim and explain the code through a verified file transfer before moving on.

## Branch 3: Training pipeline — in progress

- **Branch:** `feat/training-pipeline`, created from `main` at merge commit `9efa21f` (PR #1).
- **Jim's decisions:** Requested that training begin while another agent develops cloud storage in a separate worktree. Selected logistic regression after discussing the proposed model.
- **Modeling eligibility decision:** Rejected the proposed median imputation after questioning whether zero-tenure records belong in the modeling population. Asked whether any zero-tenure records have nonzero total charges and chose to exclude zero-tenure records from modeling while retaining them in ingestion outputs. Codex checked the full cleaned CSV: all 11 zero-tenure records have missing totals and `Churn = No`; none have nonzero totals. The eligible population is 7,032 records with no missing totals. Prospect status and inability to churn are interpretations not established by the data. Jim then explicitly requested that the exclusion be implemented in preprocessing, separately from cleaning.
- **AI assistance:** Updated local `main`, created the training branch, inspected the existing ingestion interface, and recorded the model choice in configuration and the README. Explained the roles of training, validation, and test data and the need to fit preprocessing on training data only.
- **Preprocessing implementation:** Codex wrote `src/preprocess.py` to filter eligible rows in memory before splitting, report exclusions, and stop for review if eligible rows have missing totals. Added stratified splitting in both stages, using the proposed 70/15/15 proportions as configurable defaults and seed 42. Jim expected stratification; the precise proportions are Codex's stated defaults rather than a separately confirmed decision. Added scikit-learn 1.7.2 to the project virtual environment and requirements.
- **Feature selection discussion:** Jim questioned whether 19 predictors were too many. Codex explained availability at prediction time, relevance, redundancy, practical input burden, regularization, and validation-based comparison. Jim initially approved a smaller feature set with a comparison, then explicitly deferred the comparison and directed Codex to proceed with eight inputs: tenure, contract, monthly charges, internet service, tech support, online security, payment method, and paperless billing.
- **Recorded rationale and future exploration:** At Jim's request, explicitly documented that eight inputs keep his first production pipeline manageable, support clear explanations, and reduce the eventual API/interface input burden while retaining plausibly relevant service and billing information. This does not establish that 19 predictors would be excessive or that the selected eight are optimal. Jim wants to revisit the comparison if time permits, after prioritizing completion of the pipeline. Any comparison should hold partitions and training settings constant, use validation results for selection, and preserve an independent final evaluation rather than repeatedly selecting against test results.
- **Encoding and training:** Jim asked whether encoding had happened and which method would be used. Codex explained and implemented one-hot encoding for the six categorical fields and standard scaling for the two numeric fields. Both are fitted only on training data and saved with the L2-regularized logistic regression classifier. The eight inputs expand to 20 model columns. Codex used a stated provisional 0.5 classification cutoff; it has not been selected as the final threshold. The full-feature comparison was not run.
- **Verification and status:** Codex authored eight preprocessing tests and five training tests; all 24 ingestion/preprocessing/training tests passed. Full-data checks confirmed 11 excluded rows, 7,032 eligible customers, disjoint complete partitions of 4,922/1,055/1,055, repeatable assignments, and unchanged raw and cleaned CSV fingerprints. Training tests checked train-only fitting, unseen categories, missing inputs, forbidden predictors, convergence failure, saved-model reloading, and no test-partition access by training. Validation ROC AUC was 0.8488, precision 67.10%, and recall 55.16% at cutoff 0.5. The pipeline was saved locally and aggregate validation results recorded; no test predictions or test metrics were produced. No training-branch commit or PR has been created. Jim will review implementation and results before authorizing a commit.
- **Pending decisions and work:** Discuss the classification threshold using validation results, finalize the approach, and evaluate the held-out test partition (deferred to a follow-up after this PR; see below). Comparing all 19 predictors is optional future work if time permits.
- **Sync with merged work:** Jim requested bringing merged PRs into the training branch before committing and asked about conflicts. Codex backed up the 11 training files, stashed that scoped work, fast-forwarded the branch to `origin/main` at `602baf7` (merged PR #2), and restored the training changes. Resolved five overlapping files by preserving both branches' configuration, dependencies, ignore rules, and collaboration entries, and reconciling the README's current status. Training source files and the existing validation report were preserved. No training commit was created. The cloud-transfer implementation is now present; connecting training to the downloader remains pending.
- **Post-sync verification:** All 35 combined tests and dependency checks passed. Codex compared the restored training files and validation report with the backup, confirmed cloud implementation files match `origin/main`, checked both configuration sections, and confirmed no unresolved conflicts remain. Cloud tests were offline mocks; no new live download or test-set evaluation was performed. The previously documented Google SDK warning about Python 3.10 remains; the project interpreter was not changed.
- **Review follow-up:** Jim requested cloud-fed training, a dependency refresh, and a supported Python decision within this PR. Codex confirmed that the dependency refresh had already installed google-cloud-storage 3.17.1 in the training environment during the sync. Changed preprocessing to call `storage.download()`, verify the exact in-memory bytes passed to pandas, and record their cloud URI, path, actual checksum, and expected checksum. Training and the saved artifact now use that provenance instead of hashing the unused local processed CSV after fitting. No local-data fallback is used.
- **Python decision:** Jim approved Python 3.13. Codex installed a project-local Python 3.13.18 runtime with a temporary uv tool, preserved the old environment in ignored `.venv-py310-backup/`, and rebuilt `.venv` with Python 3.13. System Python and the other agent's worktree were not changed. Added `.python-version`, updated setup instructions, and pinned NumPy 2.2.6 and SciPy 1.15.3 to preserve the original numerical-library versions during the interpreter upgrade. uv is an installation aid, not a runtime project dependency. Fresh requirements installation and validation under 3.13 are part of this follow-up.
- **Handoff and validation under 3.13:** The Codex sessions ran out of capacity before recording this result; Jim brought in Claude Code (another AI coding assistant) to continue. Claude Code reviewed the uncommitted training work and the separate experiment-tracking worktree and reported its assessment before changing anything. It then confirmed `.venv` runs Python 3.13.18 with the pinned versions, that all 40 offline tests pass (11 ingestion, 11 storage, 12 preprocessing, 6 training) and `pip check` is clean, and reran `python -m src.train` live: the cloud download matched the expected SHA-256 and validation results were identical (ROC AUC 0.8488, 155/76/126/698 confusion counts). Google's quota-project warning for user ADC still appears and does not block the download. Claude Code corrected stale test counts in the README and added `.DS_Store` to `.gitignore`.
- **Threshold and test evaluation plan:** Jim chose to commit and merge the training pipeline with the provisional 0.5 threshold, then select the threshold on validation data and run the one-time test evaluation as a small follow-up. No test predictions or metrics have been produced.

## Template for later branches

Copy this structure when a new project step begins. Add facts as work happens and update the status when the step finishes.

### Branch: `<branch-name>`

- **Date and goal:**
- **Jim's decisions, questions, review, and hands-on work:**
- **AI assistance:** Research, code, explanations, debugging, or Git actions actually performed.
- **Verification:** Checks run, who ran them, and what they did or did not establish.
- **Corrections or disagreements:** What changed and why.
- **Evidence and status:** Relevant commits, PR, merge, and unfinished work.
- **Learning notes:** Jim's own observations and any remaining questions.
- **AI process observation:** What helped the collaboration and what should change next time.

## End-of-project reflections — not yet written

We will revisit the full log together after the project is complete. These reflections should be grounded in the branch entries and completed work.

### Jim's reflection

To be written or approved by Jim: what he learned, what he can now explain or do himself, where AI helped most, and where he still needs practice.

### Codex's reflection

To be drafted at the end: which assistance was useful, where the AI made mistakes or moved too quickly, how Jim's feedback changed the work, and what would improve a future collaboration. This should describe observed behavior and results without claiming to know Jim's internal learning experience.
