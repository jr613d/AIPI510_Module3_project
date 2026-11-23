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
