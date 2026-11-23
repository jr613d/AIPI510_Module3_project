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
