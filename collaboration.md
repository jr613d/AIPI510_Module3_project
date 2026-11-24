# Human and AI collaboration log

**Status:** Initial version reviewed and approved by Jim for commit. Started November 23, 2026; updated throughout the project.

## Purpose and roles

This is Jim's solo AIPI 510 Module 3 project. The AI assistant is an AI coding and learning assistant. This file records how we work together, what AI contributes, and the decisions and review Jim provides. We will update it on each project branch and revisit it at the end for separate reflections.

Jim described this as his first full ML production pipeline and asked for a simple project with clear teaching. He expects substantial implementation help from AI, with explanations along the way. The aim is to produce a working system that he can understand and explain.

The AI assistant has written most of the initial implementation, drafted documentation, executed checks, and performed the approved Git commands. Jim has directed the scope, selected the dataset, decided how to handle the data, asked questions about the implementation, and reviewed the work before authorizing the first commit and push. This log should not imply that Jim independently wrote or ran work performed by the AI assistant.

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

Jim asked for a manageable project that would support the assignment's full pipeline requirements and serve as a learning exercise. The AI assistant inspected the assignment and researched several concepts, including plasma-cutting ideas. Jim rejected those options and redirected the search toward ready-made Hugging Face datasets. After comparing options, Jim selected customer churn prediction.

The AI assistant initially moved too quickly and drafted a larger application outside the repository Jim later created. Jim explicitly asked to work together more slowly, with separate branches, explanations, and review points. The AI assistant stopped that work. The earlier draft remains outside this repository and was not included in the first project commit. The repository's `AGENTS.md` now records the agreed pace and scope limits.

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

### What the AI assistant contributed

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

The AI assistant ran 11 automated ingestion tests and additional checks against the full dataset. The checks confirmed that all 7,043 customers and 21 columns were retained, IDs and target labels stayed unchanged, and the 11 missing charge values remained missing. The original file matched its expected checksum, repeated ingestion produced identical outputs, and Git excluded the CSVs and virtual environment. The committed [data summary](reports/data_summary.md) records the dataset checks.

The AI assistant authored and ran these checks. Jim reviewed the explanations and results and approved the implementation commit. Model training, API work, and cloud deployment remain future steps.

### Learning discussion and follow-up

Topics discussed included raw versus cleaned data, numeric versus categorical fields, missing values versus valid “no service” categories, features versus the target, checksums, and the difference between a local commit and a push to GitHub. We also discussed how evaluation metrics compare predictions with known outcomes, why an always-`No` model could achieve about 73.5% accuracy while catching no churners, and how ROC AUC, precision, and recall describe different aspects of performance. The evaluation plan is documented; no model scores have been measured yet.

**Jim's notes:** To be added after reviewing this draft. What is clear, what remains confusing, and what would he like to try himself?

**AI assistant's process observation:** The initial pace was too fast for the requested learning experience. Limiting work to the agreed branch and pausing at the data-storage and missing-value decisions gave Jim concrete choices to assess. We should maintain that pace in later steps.

## Branch 2: Cloud storage

- **Branch:** `feat/cloud-storage`
- **Date and goal:** November 23, 2026. Store the prepared CSV in Google Cloud Storage and retrieve the same bytes programmatically.
- **Later integration update:** Jim merged PR #2 into `main` at `602baf7`. The training branch incorporated this merge before its first implementation commit; the pending-review wording below describes the earlier branch-completion state.
- **Status:** Implementation, offline checks, and a real authenticated cloud download passed. Jim reviewed the explanation and walkthrough and agreed to proceed. The AI assistant committed and pushed the storage implementation as [`652e634`](https://github.com/jr613d/AIPI510_Module3_project/commit/652e634) and opened [PR #2](https://github.com/jr613d/AIPI510_Module3_project/pull/2) into `main`; Jim's PR review and merge remain pending. Jim created the bucket, uploaded the CSV, installed the SDK, and completed local login. The AI assistant verified the retrieved bytes; no cloud resources were created by the AI assistant.

### Jim's decisions and questions

- Authorized starting the storage branch while another agent finishes setup/data ingestion.
- Chose Google Cloud Storage and asked to handle bucket setup and console upload himself.
- Asked what belongs in GitHub and how code connects to a cloud dataset. We discussed bucket/object addresses, configuration versus authentication, and why a private bucket does not require committing data or credentials.
- Asked the AI assistant to implement the repository work while he prepares the bucket.
- Supplied `gs://kangaroo_baseball_field/telco_churn.csv` and a project-picker screenshot showing project ID `project-902e069e-c3ed-49c2-a13`. The AI assistant added these identifiers to `config.yaml`; this does not establish that the object is accessible or its bytes are correct.
- Reported project number `161834179213`, bucket location `us-east1`, Standard storage, and an uploaded `text/csv` object of approximately 971.9 KB. The AI assistant recorded these as Jim-reported console details in the walkthrough. A local check still found no `gcloud` command on PATH, no ADC file in the default location, and no explicit credentials environment variable; no cloud request was attempted.
- Asked why local authentication is needed, how other people would reproduce training without his login, and when Weights & Biases fits. We distinguished dataset access during training from public app prediction requests, discussed future cloud service identities, and explained how another person can use their own bucket and credentials. Jim restated that the repository supplies steps to rerun training using someone else's own resources. Experiment tracking remains after a working training pipeline.
- Installed the SDK and completed the local authentication flow himself, then reported that he was done. The AI assistant confirmed the SDK and default ADC file were present without displaying credential contents.
- Reviewed the walkthrough of configuration, authentication, download, checksum verification, and atomic saving, acknowledged the explanation, and agreed to the next step of diff review, commit, and PR.

### AI assistance and implementation

- Created an isolated Git worktree so the ingestion agent's checkout stays on its own branch. Based this branch on committed ingestion work and fast-forwarded it to the newly committed roadmap before making storage edits.
- Used `feat/cloud-storage`, the name in Jim's request, and updated the roadmap's step 2 row to match. The usual sequence remains to create later branches from updated `main` after Jim's merge; this concurrent start was explicitly requested.
- Added configurable GCS transfers with a pinned fingerprint of the reviewed cleaned CSV. Downloads verify bytes before atomically saving a separate Git-ignored cloud copy. Optional uploads check the same fingerprint and refuse to replace an existing cloud object.
- Wrote the walkthrough for bucket/object configuration, local Application Default Credentials, transfer commands, and common failures. Credentials stay outside the repository.
- Added offline tests for correct bytes, wrong-file rejection, failed authentication/access, local-file preservation, and upload replacement protection.

### Verification and limits

The AI assistant installed the dependencies in this worktree's separate `.venv`, ran all
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

The AI assistant then ran a real authenticated download on November 23, 2026. The first
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
bucket settings were changed by the AI assistant.
No model, experiment tracker, API, container, or application deployment is
included in this step. The AI assistant reviewed the diff before committing. Step 1 was
merged separately into `main`; this worktree was fast-forwarded to that merge
before preparing the storage commit. Jim will review and merge the storage PR.

**Jim's learning notes:** To be added or approved by Jim after review.

**AI process observation:** Jim clarified that he wants to manage the cloud
console himself and understand the repository connection. Keep console setup
with Jim and explain the code through a verified file transfer before moving on.

## Branch 3: Training pipeline — merged in PR #3

- **Branch:** `feat/training-pipeline`, created from `main` at merge commit `9efa21f` (PR #1).
- **Jim's decisions:** Requested that training begin while another agent develops cloud storage in a separate worktree. Selected logistic regression after discussing the proposed model.
- **Modeling eligibility decision:** Rejected the proposed median imputation after questioning whether zero-tenure records belong in the modeling population. Asked whether any zero-tenure records have nonzero total charges and chose to exclude zero-tenure records from modeling while retaining them in ingestion outputs. The AI assistant checked the full cleaned CSV: all 11 zero-tenure records have missing totals and `Churn = No`; none have nonzero totals. The eligible population is 7,032 records with no missing totals. Prospect status and inability to churn are interpretations not established by the data. Jim then explicitly requested that the exclusion be implemented in preprocessing, separately from cleaning.
- **AI assistance:** Updated local `main`, created the training branch, inspected the existing ingestion interface, and recorded the model choice in configuration and the README. Explained the roles of training, validation, and test data and the need to fit preprocessing on training data only.
- **Preprocessing implementation:** The AI assistant wrote `src/preprocess.py` to filter eligible rows in memory before splitting, report exclusions, and stop for review if eligible rows have missing totals. Added stratified splitting in both stages, using the proposed 70/15/15 proportions as configurable defaults and seed 42. Jim expected stratification; the precise proportions are the AI assistant's stated defaults rather than a separately confirmed decision. Added scikit-learn 1.7.2 to the project virtual environment and requirements.
- **Feature selection discussion:** Jim questioned whether 19 predictors were too many. The AI assistant explained availability at prediction time, relevance, redundancy, practical input burden, regularization, and validation-based comparison. Jim initially approved a smaller feature set with a comparison, then explicitly deferred the comparison and directed the AI assistant to proceed with eight inputs: tenure, contract, monthly charges, internet service, tech support, online security, payment method, and paperless billing.
- **Recorded rationale and future exploration:** At Jim's request, explicitly documented that eight inputs keep his first production pipeline manageable, support clear explanations, and reduce the eventual API/interface input burden while retaining plausibly relevant service and billing information. This does not establish that 19 predictors would be excessive or that the selected eight are optimal. Jim wants to revisit the comparison if time permits, after prioritizing completion of the pipeline. Any comparison should hold partitions and training settings constant, use validation results for selection, and preserve an independent final evaluation rather than repeatedly selecting against test results.
- **Encoding and training:** Jim asked whether encoding had happened and which method would be used. The AI assistant explained and implemented one-hot encoding for the six categorical fields and standard scaling for the two numeric fields. Both are fitted only on training data and saved with the L2-regularized logistic regression classifier. The eight inputs expand to 20 model columns. The AI assistant used a stated provisional 0.5 classification cutoff; it has not been selected as the final threshold. The full-feature comparison was not run.
- **Verification and status:** The AI assistant authored eight preprocessing tests and five training tests; all 24 ingestion/preprocessing/training tests passed. Full-data checks confirmed 11 excluded rows, 7,032 eligible customers, disjoint complete partitions of 4,922/1,055/1,055, repeatable assignments, and unchanged raw and cleaned CSV fingerprints. Training tests checked train-only fitting, unseen categories, missing inputs, forbidden predictors, convergence failure, saved-model reloading, and no test-partition access by training. Validation ROC AUC was 0.8488, precision 67.10%, and recall 55.16% at cutoff 0.5. The pipeline was saved locally and aggregate validation results recorded; no test predictions or test metrics were produced. No training-branch commit or PR has been created. Jim will review implementation and results before authorizing a commit.
- **Pending decisions and work:** Discuss the classification threshold using validation results, finalize the approach, and evaluate the held-out test partition (deferred to a follow-up after this PR; see below). Comparing all 19 predictors is optional future work if time permits.
- **Sync with merged work:** Jim requested bringing merged PRs into the training branch before committing and asked about conflicts. The AI assistant backed up the 11 training files, stashed that scoped work, fast-forwarded the branch to `origin/main` at `602baf7` (merged PR #2), and restored the training changes. Resolved five overlapping files by preserving both branches' configuration, dependencies, ignore rules, and collaboration entries, and reconciling the README's current status. Training source files and the existing validation report were preserved. No training commit was created. The cloud-transfer implementation is now present; connecting training to the downloader remains pending.
- **Post-sync verification:** All 35 combined tests and dependency checks passed. The AI assistant compared the restored training files and validation report with the backup, confirmed cloud implementation files match `origin/main`, checked both configuration sections, and confirmed no unresolved conflicts remain. Cloud tests were offline mocks; no new live download or test-set evaluation was performed. The previously documented Google SDK warning about Python 3.10 remains; the project interpreter was not changed.
- **Review follow-up:** Jim requested cloud-fed training, a dependency refresh, and a supported Python decision within this PR. The AI assistant confirmed that the dependency refresh had already installed google-cloud-storage 3.17.1 in the training environment during the sync. Changed preprocessing to call `storage.download()`, verify the exact in-memory bytes passed to pandas, and record their cloud URI, path, actual checksum, and expected checksum. Training and the saved artifact now use that provenance instead of hashing the unused local processed CSV after fitting. No local-data fallback is used.
- **Python decision:** Jim approved Python 3.13. The AI assistant installed a project-local Python 3.13.18 runtime with a temporary uv tool, preserved the old environment in ignored `.venv-py310-backup/`, and rebuilt `.venv` with Python 3.13. System Python and the other agent's worktree were not changed. Added `.python-version`, updated setup instructions, and pinned NumPy 2.2.6 and SciPy 1.15.3 to preserve the original numerical-library versions during the interpreter upgrade. uv is an installation aid, not a runtime project dependency. Fresh requirements installation and validation under 3.13 are part of this follow-up.
- **Handoff and validation under 3.13:** The original AI assistant's sessions ran out of capacity before recording this result; Jim brought in Claude Code (another AI coding assistant) to continue. Claude Code reviewed the uncommitted training work and the separate experiment-tracking worktree and reported its assessment before changing anything. It then confirmed `.venv` runs Python 3.13.18 with the pinned versions, that all 40 offline tests pass (11 ingestion, 11 storage, 12 preprocessing, 6 training) and `pip check` is clean, and reran `python -m src.train` live: the cloud download matched the expected SHA-256 and validation results were identical (ROC AUC 0.8488, 155/76/126/698 confusion counts). Google's quota-project warning for user ADC still appears and does not block the download. Claude Code corrected stale test counts in the README and added `.DS_Store` to `.gitignore`.
- **Threshold and test evaluation plan:** Jim chose to commit and merge the training pipeline with the provisional 0.5 threshold, then select the threshold on validation data and run the one-time test evaluation as a small follow-up. No test predictions or metrics have been produced.

## Branch 4: Experiment tracking — merged in PR #4

- **Branch:** `feat/experiment-tracking`, in the separate `AIPI510_Module3_cloud_storage` worktree, based on `main` at merge commit `932160b` (PR #3).
- **Date and goal:** November 23, 2026. Record each training run's settings, validation metrics, data fingerprint, code version, and model file in Weights & Biases.
- **Preparation (original AI assistant):** While training was still in progress, the AI assistant wrote the tracking helper `src/tracking.py`, its mocked-SDK unit tests, an offline smoke check, an optional `requirements-tracking.txt`, the W&B guide, and a `wandb/.gitignore`. The helper was not yet called by training, and no W&B run had been created.
- **Handoff:** Jim assigned Claude Code to work exclusively in this worktree and branch and to finish the experiment-tracking step. Claude Code reviewed the original AI assistant's uncommitted preparation, confirmed the worktree's `.venv` runs Python 3.13.18 with wandb 0.31.2, and confirmed all 47 existing tests passed before making changes. An uncommitted wording change in `AGENTS.md` (from "Codex" to "the AI assistant") was already present. Jim approved including it and asked for the same wording throughout the project documents, so later mentions of the earlier assistant read "the AI assistant" or "the original AI assistant."
- **Jim's learning and hands-on work:** Asked for an entry-level overview of the W&B platform (projects, runs, config, metrics, artifacts, offline mode, and comparison with MLflow) and where to store the API key safely. Created his W&B account and ran `wandb login` himself in a separate terminal, so the key never passed through the chat or repository.
- **Jim's decisions:** Online tracking by default for `python -m src.train`, with a command-line override; W&B project name `aipi510-churn`; and moving `wandb` into the main `requirements.txt` (tracking is required by the assignment and will be needed in Docker), replacing the separate tracking requirements file.
- **AI assistance (Claude Code):** Added a `tracking` section to `config.yaml` (project, entity, mode) and a `tracking_settings()` validator. Moved the training command into `main()`, which checks tracking settings before training, calls `log_training_run()` after a successful fit, prints the run URL, and exits with an error (after saving outputs) if logging fails. Added `--tracking-mode online|offline|disabled`. Added 8 tests for settings validation and the command's wiring. Rewrote the tracking guide to describe the finished integration and removed stale Python 3.10 notes. Updated the README's current step, project map, dependencies, and test counts.
- **Correction:** The original AI assistant's offline smoke check failed because it searched only W&B's cache folder for the staged model file; wandb 0.31.2 stages offline artifact files in its data folder. Claude Code located the file there, confirmed the tracking code was correct, and widened the check to search both folders.
- **Verification:** Claude Code ran all 55 offline tests (passing) and `pip check` (clean); ran the offline smoke check with the real SDK (passing after the correction); ran `python -m src.train --tracking-mode offline`, which verified the cloud download and reproduced validation ROC AUC 0.8488; and ran `python -m src.train` online, which uploaded run `qki8atue` with the `churn-model` artifact to project `aipi510-churn` in workspace `jr613-d`. Because the code was uncommitted, that run records `git_dirty: true`. Jim's review of the run in the W&B dashboard is pending.
- **Status:** Jim reviewed the run in the W&B dashboard and the walkthrough, and authorized the commits. Claude Code committed `16fb720` and `d9e155a`, made a clean online run (`aj21jggr`, `git_dirty: false`), and pushed the branch. `gh` was not installed, so Jim opened PR #4 in the browser using a plain-language description Claude Code drafted at his request, and merged it.
- **Learning notes:** To be added or approved by Jim.

## Branch 4b: Model selection and final test evaluation — merged in PR #5

- **Branch:** `feat/model-selection`, in the `AIPI510_Module3_cloud_storage` worktree, created from `main` at merge commit `0f8d302` (PR #4).
- **Date and goal:** November 23, 2026. Use W&B to compare model versions on validation data, choose the model and threshold, then evaluate the test set once.
- **Jim's questions:** Asked whether the purpose of tracking is to iterate on the model before using the test set, and whether more than one W&B run should be recorded. Claude Code explained the validation loop, why the test set is scored once at the end, and proposed four experiments in plain language. Jim chose to do all four. This adds step 4b to the project map.
- **Experiments (Claude Code implemented; Jim decided):** `src/experiments.py` trained 8 versions (8 or 19 inputs × `C` 0.01, 0.1, 1, 10), each logged to W&B. Validation ROC AUC ranged from 0.8487 to 0.8532. Claude Code explained that differences of this size are within chance variation and noted that the 19-input version uses gender and other demographics and needs a longer form. Jim kept the 8-input model with `C = 1.0`. The all-19 comparison that was deferred during Branch 3 is now complete.
- **Threshold (Claude Code implemented; Jim decided):** `src/thresholds.py` compared cutoffs from 0.20 to 0.70 on validation data and logged a W&B table and chart. Jim chose 0.35 (highest F1), which caught 216 of 281 validation churners with 161 false alarms. The assumption that a missed churner costs more than a false alarm is not supported by cost data in the dataset.
- **Final test:** Claude Code wrote `src/evaluate.py`, which scores the test partition once, refuses to rerun after its report exists, and logs a separate `final-test` W&B run. Claude Code recommended committing the code first so the final runs would record a clean commit; Jim agreed (`9467b72`) and then authorized the final runs. Claude Code then retrained the final model (W&B run `ohhh014q`; validation precision 57.3%, recall 76.9%) and ran the test evaluation once (run `i2dn23t5`): **ROC AUC 0.8192, precision 52.7%, recall 68.9%**, 193 of 280 churners caught, 173 false alarms. These are lower than validation, as expected after making choices on validation data. The model was not adjusted after the test results.
- **Verification:** 69 offline tests pass (14 new: experiments, thresholds, final evaluation, and their W&B logging, all with mocked training and W&B). Dry runs with W&B disabled reproduced the baseline validation results (ROC AUC 0.8488; 155/76 at threshold 0.5) before the online runs.
- **Status:** Claude Code committed the final reports and documentation (`99cdb2f`) and pushed the branch. Jim asked for the PR description to use the proper terms (validation and test sets, precision, recall, F1) explained simply, opened PR #5, and merged it.
- **Learning notes:** To be added or approved by Jim.

## Branch 5: Prediction API — merged in PR #6

- **Date and goal:** November 23, 2026. Serve the final model through a local `/predict` endpoint that a front end can call.
- **Work split:** Jim divided the remaining work between two AI agents in separate worktrees: this one owns the back end (API, Docker, deployment), and the other builds the Streamlit front end against an API contract Jim approved (request fields, response fields, `/health`, readable 4xx errors, CORS).
- **Jim's questions and understanding:** Jim asked where everything would be hosted, where the model would live, and where requests would go. The AI assistant explained that step 5 runs only on his Mac, step 6 packages the same code in a container, and step 7 gives it a public address, with the front end calling that address. It also corrected two points in his summary: W&B records training rather than performing it, and at that moment the threshold and test evaluation were still being finished on the other branch. Jim also checked whether the assignment requires the model to come from a particular place; it only requires the API to load the trained model.
- **Jim's decisions:**
  - FastAPI with uvicorn.
  - Build the small model file into the Docker image for the deployed API (implemented in steps 6–7), because it is simplest and serves reliably.
  - The API needs elegant, or at least clear, error handling.
  - Categories must match the training data exactly; the front end will use dropdowns.
  - Tenure is documented as months and rounded to the nearest whole month.
  - Values outside the training data's range are flagged and not allowed.
  - Reject inconsistent internet-service combinations with a clear message.
  - Allow calls from any website for now.
- **Cost question:** Jim asked whether a bot could run up cloud charges and what the downside of allowing any website is. The AI assistant explained that CORS only governs browsers, so bots are unaffected either way; the real exposure is the public URL itself, which the assignment requires. Limiting the cost is a deployment setting (step 7).
- **AI assistance:** Wrote `src/api.py` and `tests/test_api.py`, and added FastAPI, uvicorn, and httpx (for tests) to `requirements.txt`. Changed training to record the training partition's numeric ranges in the model file and validation report, so the API reads the ranges instead of hard-coding them. Allowed categories come from the fitted encoder, and the threshold from `config.yaml`. Wrote this step's README section.
- **Verification:** The AI assistant retrained locally with W&B disabled, to avoid adding a run that only adds recorded ranges. Validation metrics were unchanged (ROC AUC 0.8488; 216 caught, 161 false alarms at 0.35). All 83 tests pass, including 14 new API tests that use a synthetic model, and `pip check` is clean. It also started the real server and checked `/health`, two `/predict` requests with `curl`, and the `/docs` page. The test client prints a deprecation warning about httpx; it does not affect the API.
- **Trying it in the browser:** Jim's first attempt to open the docs page failed for two reasons. The server was not running, and port 8000 was occupied by the front-end agent's mock API, which has no docs page. The AI assistant explained this, ran the real API on port 8001, and added a note on ports to the README.
- **Status:** Jim reviewed the API in the browser and authorized a commit and push. The PR is next.

## Branch 6: Docker — merged in PR #8

- **Date and goal:** November 23, 2026. Package the project in one Docker image with entry points for serving and training, built and run locally.
- **Jim's decisions:** Approved one image with `serve`, `train`, and `test` commands, and building the trained model into the image. The build fails if the model is missing or mismatched. Credentials are connected only at run time for training and are never stored in the image. Jim installed Docker Desktop himself.
- **AI assistance:** Wrote the `Dockerfile` (Python 3.13.18-slim, non-root user, a build-time model check, and a recorded model SHA-256), `docker-entrypoint.sh`, an allow-list `.dockerignore`, and the README's Docker section. Explained the Apple-silicon (ARM) versus Cloud Run (x86) difference for step 7.
- **Verification:** The AI assistant built the image (836 MB) and confirmed the following:
  - All 83 tests pass inside the container.
  - The container runs as a non-root user and contains no data CSVs or credential files.
  - `serve` answers `/health`, `/predict` (including the readable errors), and `/docs`, and honors a `PORT` setting as Cloud Run requires.
  - An unknown command exits with a usage message.
  - `train` without credentials stops with Google's "credentials not found" message.
  - Builds fail as intended when the model is missing or `config.yaml` has an invalid threshold.

  Jim then ran `train` in the container himself, connecting his Google and W&B logins read-only.
  - The run downloaded and verified the cloud data and reproduced the validation results exactly (ROC AUC 0.8488; 216 caught, 161 false alarms).
  - It was recorded as W&B run `udfqgkyz` in `jr613-d/aipi510-churn`.
  - Jim first had to reload his shell profile so the terminal could find the `docker` command.

  The AI assistant rebuilt the image with that model. The image's recorded model SHA-256 (`5c1ddc44…`) matches the file the run produced, and the rebuilt image served the same predictions.
- **Reproducibility without Jim's credentials:**
  - Jim asked what the image contains, and how his professor could retrain from it without his Google or W&B logins.
  - The AI assistant explained that the image holds addresses (bucket, file, W&B project) but no keys. Serving needs no credentials, but retraining would fail on the private bucket.
  - It offered three ways to get the data (grant the grader read access, make the file public, or let them use their own bucket), plus options for W&B.
  - **Jim's decisions:** make the data file publicly readable, with an anonymous-download fallback, and document the own-bucket route for full independence. Make the W&B project public and view-only, and link it. Document `--tracking-mode disabled` and "use your own W&B login" for retraining.
  - **AI assistance:** Added the anonymous fallback to `src/storage.py`. It is used only for downloads when no Google login exists, the checksum check still applies, and a private file produces a clear explanation. Added 4 storage tests and wrote the README section "Reproducing without author credentials".
  - **W&B result:** Jim made the W&B project public. The AI assistant confirmed with an anonymous query that it is readable without a login (14 runs).
  - **Bucket result:** Jim changed the bucket's permissions, but anonymous requests were still refused after several minutes. The AI assistant listed likely causes, including an organization policy blocking public sharing. Jim first decided to rely on the data-sourcing scripts. He then worked out the console setting himself and made the file publicly downloadable, and supplied the direct link for the documentation.
  - **Verification after the change:** The AI assistant confirmed that the public link returns the file and that its SHA-256 matches `config.yaml`. In a rebuilt container with no credentials, `train` downloaded the file anonymously, passed the checksum, and reproduced Jim's validation metrics exactly. 86 tests pass.
  - **Final state:** The data is publicly readable, and the README links the direct download. The own-bucket route is documented for full independence. The anonymous fallback still checks the checksum, and for a private file it explains what to do instead of showing Google's generic credentials error.
- **Status:** Docker merged in PR #8. The reproducibility follow-up (anonymous fallback and README section) was finished after that merge, so it goes in its own small PR.

## Branch 7: API deployment — merged in PR #11

- **Date and goal:** November 23, 2026. Deploy the API publicly and verify it with real HTTP requests.
- **Choosing the platform:** The AI assistant compared Cloud Run, Cloud Functions, AWS or Azure, and platforms outside the assignment's list (Render, Hugging Face Spaces). It recommended Cloud Run, because it runs the tested Docker image unchanged in the same Google project. Jim chose Cloud Run on the condition that everything could be done from the command line, since he does not like the web console. He decided to run every `gcloud` command himself, using his own login, while the AI assistant wrote and explained each one.
- **Cost limits:** Jim asked for a $5 **hard cap**, not just a budget email. The AI assistant explained that Google Cloud has no built-in spending cap, and that billing data lags by hours. It proposed a budget that sends messages to a small "cost guard" function.
  - Jim chose the guard's targeted shut-off: make the API and data private, rather than disabling billing for the whole project.
  - The AI assistant wrote the guard and its tests.
  - Jim then set it aside to finish the project first, judging the risk low. The deployed API's one-instance limit is the current safeguard, and the guard's code is kept for later.
- **Account setup:** The first checks showed that the `gcloud` CLI was not logged in, separately from the Python login used in earlier steps. Jim ran `gcloud auth login` and set the default project.
  - The project sits under an organization, `james-e-redden-org`, that Jim had not known about. Google creates one automatically for some accounts.
  - The effective sharing policy allows public access (`allowAll`), so a public Cloud Run service was possible. This probably explains why the earlier attempt to make the bucket public needed extra steps.
- **Deployment:** The AI assistant built an x86 image on the Mac. The build was slow because the Mac emulates x86 and the network was slow; it carries the W&B-tracked model `5c1ddc44…`.
  - Jim created the Artifact Registry repository, connected Docker to it, and pushed the image.
  - He then deployed `churn-api` by digest. The deploy used a dedicated runtime identity with no permissions; public access; 1 CPU and 1 GiB; min 0 and max 1 instances; and a 30-second timeout.
- **Verification:** The AI assistant tested the public URL with no login:
  - `/health` returned ok.
  - `/predict` returned the same probability as locally (0.6705, "Yes" at 0.35).
  - Invalid input returned the readable 422 errors.
  - `/docs` loads, and CORS allows any site.
  - Jim also tried the live API himself and confirmed that it worked.
- **Architecture diagram:** While the image built, Jim asked for a system architecture diagram. He liked it and asked for it to be front and center for his professor. The AI assistant made it a standalone image, `docs/architecture.svg`, with automatic light and dark versions, and checked how it renders.
- **Coordinating with the README rewrite:** The front-end agent was restructuring the README on `docs/readme-final`, so Jim passed along its request. To avoid a conflict, the deployment instructions went into a new `docs/DEPLOYMENT.md` instead of the README. The README was left unchanged on this branch, and the diagram is ready for the rewritten README to show at the top.
- **Status:** The API is live. Jim authorized a commit and push of `docs/DEPLOYMENT.md`, the diagram, and this entry.

## Branch 8: Front-end (Streamlit) — merged in PR #7, deployed

- **Branch:** `feat/frontend`, in the `AIPI510_Module3_cloud_storage` worktree, created from `main` at merge commit `e18cbaf` (PR #5).
- **Planning and division of work:** Jim asked Claude Code to propose how two AI agents could split the remaining work without conflicts. Claude Code proposed a back-end track (API, Docker, API deployment) for the agent in the main worktree and a front-end track (Streamlit app, then final-documentation drafts) for itself, with collision rules: separate worktrees and branches, front-end code only in `frontend/` with its own requirements, no `git stash`, only one's own README and collaboration sections, and the API PR merging first. It noticed that the other agent's `feat/prediction-api` branch predated PR #5 and needed `main` merged in to use the 0.35 threshold. Jim chose Streamlit, left the model-delivery method for the deployed API to the other agent, and approved the API contract: `POST /predict` with the eight inputs, returning `churn_probability`, `churn_prediction`, and `threshold`, plus `GET /health`. Claude Code drafted a message for Jim to pass to the other agent.
- **Jim's design decisions:** Asked that monthly charges use a slider like tenure, without $5 steps, and that a short note under both sliders explain that the model was trained and validated only within those ranges. Pointed Claude Code to the project's Streamlit skill. Asked for a creative visualization of the model below the prediction and left the design open.
- **AI assistance (Claude Code):** Wrote `client.py` (request building, the data's internet add-on rule, range checks, response validation, readable errors), `app.py` (form, prediction display, model facts, remembered results), `mock_api.py` (a stand-in API with fake predictions for local development), and `charts.py`. Followed the Streamlit skill: segmented controls instead of dropdowns and horizontal radios, sentence case, Material icons, bordered sections, widget keys, and verification in a running app through Streamlit's agent API. Followed the data-viz skill's palette, mark, labeling, and visual-review guidance for the charts. For the visualization, proposed and built an explore section that asks the API "what if?" questions within the approved contract: a dot plot of how each choice changes the risk (with the biggest lever called out), probability curves across tenure and monthly charges, and the logistic S-curve with the customer's position.
- **Corrections:** The first version used a deprecated Streamlit button option, which was replaced. A probability right at 0.5% displayed as "0%", so values below 1% now show "<1%". Rendering the charts to images led to option labels on the dots, a labeled threshold, and axes fitted to the input ranges. The stand-in API intermittently refused parallel requests because of its server's small connection queue; the queue was enlarged and the app sends four requests at a time. Claude Code's cleanup of its own test servers also stopped Jim's running stand-in API, because it matched processes by name; Claude Code explained the cause, Jim restarted it, and later cleanups stopped processes by port-owned process ID only. Jim's long-running Streamlit server kept an old copy of `client.py` in memory after new functions were added; restarting Streamlit fixed the resulting import error, and the front-end README now notes this.
- **Verification:** 19 front-end tests pass in the front-end environment (Streamlit 1.67.0); in the main environment the 6 page tests skip cleanly. The tests cover the request format and input rules, response checking and error messages, the "what if?" variations, and headless page behavior. Claude Code also drove a headless instance of the app against the stand-in API (no console warnings) and reviewed rendered images of each chart. The Node.js palette validator could not be run because Node is not installed; the colors are the data-viz skill's documented, pre-validated pair. Jim ran the app locally and confirmed it works. All predictions so far come from the stand-in API, not the trained model.
- **Integration with the merged API (PR #6):** At Jim's request, Claude Code merged updated `main` into `feat/frontend`. It resolved one project-map conflict (step 5 merged) and kept the log in branch order. It then checked the API against the contract: routes, field names, threshold, and CORS matched. Two differences needed front-end changes. The API reports errors as `{"error": ...}` rather than FastAPI's default `detail`, so the client now reads both and the stand-in API mirrors the real format. The API also accepts monthly charges of $18.40–$118.60, the training partition's range, while the slider used the full dataset's $18.25–$118.75; the slider and what-if points now use the API's range. Claude Code installed the API packages in this worktree, retrained locally with W&B disabled so the model file included the input ranges (the committed validation report was reproduced byte for byte), ran the real API, and confirmed real predictions, accepted range edges, a readable rejection of $18.25, and the full explore section. Real-model charts showed overlapping labels for close options, so options within 8 percentage points now share one label.
- **Deployment:** After the API went live, the other agent passed on its address. Claude Code verified the live API (health, the sample prediction 0.6705 matching the local model, a readable range error, and open CORS) and ran the front-end and its full "what if?" exploration against it (about one second). It then gave Jim step-by-step instructions for Streamlit Community Cloud: branch `main`, main file `frontend/app.py`, Python 3.13, and the `API_URL` secret. Jim deployed the app at https://aipi510module3project-churn.streamlit.app/. Claude Code confirmed that the app answers publicly without a sign-in and that its health check responds; the interactive behavior was checked by Jim in a browser, since it cannot be driven from the command line.
- **Status:** Merged in PR #7 and deployed publicly.
- **Learning notes:** To be added or approved by Jim.

## Branch 9: Final review — ethics (PR #9) and README (PR #12) merged

- **Branch:** `docs/final-review`, in the `AIPI510_Module3_cloud_storage` worktree, created from `main` at `890478e` (PR #6).
- **Ethics and limitations:** Jim asked for drafts written in his voice and shared a guide he wrote as a writing sample. Claude Code's first draft (about 1,600 words) did not work for Jim. He changed the approach: Claude Code gave its ranked view of the project's limitations and ethical considerations, and Jim then chose the points to highlight: the fictional data; that ethics and fairness cannot be fully evaluated without knowing the data's origin and what is done after a prediction; privacy and the handling of customer IDs; possible confounding/proxy variables despite excluding demographics; and the small test set. He asked for a concise, easy-to-grade section. Claude Code found no rubric in the assignment beyond the learning goal to reflect on ethical implications and limitations, drafted `docs/ETHICS_AND_LIMITATIONS.md` (about 450 words) from Jim's points, corrected two claims to match the code (customer IDs are excluded from model inputs, the API, the app, and experiment records, not from the dataset; the 19-input experiment added service and billing columns as well as demographics), and removed a fifth point Jim had not chosen. Jim edited the draft and approved it.
- **README restructure (`docs/readme-final`):** After a project check-in, Jim asked Claude Code to restructure the README, which had grown step by step to 448 lines. Claude Code rebuilt it (about 220 lines) around the assignment's required sections: links to the live app, API, W&B project, and dataset; overview and goals; dataset; model and evaluation, with the validation-versus-test table; a new cloud services table; setup and usage (training, tests, API, Docker, front-end, and deployment); ethics and limitations; repository structure; and a table of every step and pull request. The detailed material moved nearly word for word into `docs/DATA.md`, `docs/MODEL.md`, `docs/API.md`, and `docs/DOCKER.md`, with out-of-date phrases such as "the current step above" removed and links checked. At Jim's request, passed on by the other agent, the architecture diagram from step 7 (`docs/architecture.svg`) leads the README; Claude Code's smaller Mermaid diagram was removed as a duplicate. The deployment commands in the README match `docs/DEPLOYMENT.md`, and the live links were added after both deployments.
- **Final check and reflections (`docs/final-reflections`):** Claude Code checked the merged project against every assignment requirement. All 106 tests passed on `main`, and the live API, live app, data file, W&B project (public, 14 runs), and GitHub repository all answered without a login. Jim approved a short note under the app's "Biggest single lever" callout stating that it shows the model's associations, not causes. Jim wrote his end-of-project reflection; Claude Code removed a duplicated paragraph, corrected "Weights & Biases," and fixed punctuation, then drafted the AI assistant's reflection for Jim's review.

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

## End-of-project reflections

### Jim's reflection

It was a fantastic learning experience, because this is why I got into this course: to get hands-on experience building things in collaboration with AI and to get a depth of understanding (so that I understand how the pieces fit together and how they are all intended to function to complement a production pipeline), while not having to put hands to keyboard to write Python code or troubleshoot code.

I felt like I was able to quarterback an AI agent team of two. I kept them going at a pace that kept me in the loop and understanding what they were doing at every step, while they made a lot of recommendations that, honestly, were good and I didn't really have to deviate too much from.

There were some interesting points of communication back through the READMEs, through the documentation, and through the ethics and limitations discussions. I can tell, as soon as the agent is writing something for a human, that my view and my voice are going to be better than just letting the agent write it. In terms of Python and code and other things like that, it's so much better than me, so much better than I will ever be.

I still have a lot more to learn about Docker, Google Cloud, and production ML pipelines. I was intrigued by the full suite of resources available on Google Cloud and through the Weights & Biases platform, and I now want to go explore more about what these are and can do.

One of my big concerns is about security and understanding how the choices that are made at the setup phase for these systems have downstream implications for security and cost, particularly as I'm building APIs with connections to models in cloud storage. I have accountability for the costs incurred there.

I needed to make some things public to satisfy the project requirements, but left to my own devices, I would experiment in private. I don't think there are other collaboration reflections that I have.

### AI assistant's reflection

*Drafted by Claude Code from the branch entries above; it describes observed behavior and results, not Jim's experience.*

**What helped.** The assistance was most useful when it turned Jim's decisions into working, tested code and explained the trade-offs before he chose: the tenure eligibility rule, eight inputs versus nineteen, the 35% threshold, and the one-time test evaluation. Splitting the remaining work between two agents, with separate worktrees, clear ownership, and an approved API contract, let the back end and front end progress in parallel. Testing the pieces together caught the real integration problems early: the API's error format and its narrower monthly-charge range.

**Where the AI went wrong.** The assistants made mistakes, and the log records them. Early on, an assistant moved too fast and built a larger application outside the repository before Jim asked for a slower, branch-by-branch pace. Claude Code's cleanup of its own test servers stopped Jim's running stand-in API because it matched processes by name. Its first ethics draft ran about 1,600 words in a voice Jim did not recognize. Smaller errors (a deprecated Streamlit option, a probability shown as "0%", overlapping chart labels, a stand-in server that dropped parallel requests) were caught by testing and by looking at the output.

**How Jim's feedback changed the work.** Jim's questions changed the project more than any code did: whether zero-tenure customers belong in the model, whether to iterate before touching the test set, and how the model's ranges should be enforced. His redirection of the ethics section, choosing the points himself and asking for something concise and easy to grade, produced a better document than the assistant's draft. His insistence on reviewing each step before a commit kept him able to explain every part of the submission.

**What would improve a future collaboration.** Ask for a writing sample and the reader's needs before drafting anything meant for people. Agree on the shared contract (API fields, errors, and limits) before two agents build against it. Stop only processes the assistant started, by process ID. And keep making cost and security consequences visible at setup time, such as public access, scaling limits, and billing, since Jim is accountable for them.
