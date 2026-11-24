# Project collaboration instructions

- This is Jim's solo student project. The AI assistant is his coding and learning assistant, not a second student or project partner. Do not impose partner-specific contribution requirements.
- Jim makes project decisions and reviews the work; the AI assistant helps with implementation, testing, and explanations. Document AI assistance honestly.
- Work in this cloned repository, not the sibling `churn_predictor` draft.
- Jim wants to learn the project step by step. Explain what you are doing
  and why; pause for material decisions and answer questions along the way.
- Implement only the currently agreed step. Do not add future model,
  experiment tracking, API, interface, Docker, or deployment work early.
- Use a separate branch for each agreed step. The first branch combines
  project setup and data ingestion: `feat/setup-data-ingestion`.
- Follow the branch sequence and scope in the [README project map](README.md#how-this-project-was-built). Keep its status current and record assistance in `collaboration.md`. Discuss changes to the plan with Jim before implementing them.
- After Jim merges a PR, update local `main` from GitHub and create the next agreed branch from that updated `main`. Create branches only when their step begins.
- Before a commit, summarize the changes and validation and give Jim the
  opportunity to review. Then use focused commits and a PR into `main`.
- Jim reviews and merges PRs; wait until he is ready for the next step.
- Raw and processed CSVs stay local. Commit ingestion code, configuration,
  attribution, and an aggregate data summary. Do not commit `.venv` or secrets.
- Preserve raw data unchanged. Fit learned preprocessing only after splitting
  in a future modeling step. Customer IDs must not become model inputs.
- Jim chose to retain every customer and keep blank TotalCharges as missing
  numeric values in the raw and cleaned ingestion outputs. For modeling, Jim subsequently chose to exclude zero-tenure rows: require `tenure >= 1` before splitting. Keep the source CSVs unchanged, report excluded counts, and do not impute these rows. Zero tenure does not establish prospect status or an inability to churn.
- The dataset is IBM's fictional telecom sample, not validated live customer
  data. Do not overstate the model's real-world predictive ability.
- Jim chose an initial eight-input logistic regression model: `tenure`, `MonthlyCharges`, `Contract`, `InternetService`, `TechSupport`, `OnlineSecurity`, `PaymentMethod`, and `PaperlessBilling`. The comparison with all 19 predictors is deferred. Fit one-hot encoding and numeric scaling only on training data; the current 0.5 threshold is provisional. Reserve test evaluation until the modeling and threshold choices are finalized with Jim.
- The eight-input choice prioritizes a manageable first pipeline, explainability, and fewer API/interface inputs; it is not an empirically optimal subset or a claim that 19 predictors are excessive. Jim wants to revisit the comparison as optional future exploration if time permits, after prioritizing completion of the production pipeline. Do not start that comparison without his direction.
- Jim approved Python 3.13 as the project target, including future Docker/deployment work. Use this checkout's `.venv`, rebuilt with Python 3.13; keep the old `.venv-py310-backup` and project-local `.python-runtime` out of Git. System Python is unchanged.
- Training/preprocessing must fetch the dataset through `storage.download()` with checksum verification and no fallback to the local processed CSV. Record provenance from the exact bytes passed to pandas, including cloud URI and actual SHA-256, rather than hashing a different file after fitting.
