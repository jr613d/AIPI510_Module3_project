# Project collaboration instructions

- This is Jim's solo student project. Codex is his AI coding and learning assistant, not a second student or project partner. Do not impose partner-specific contribution requirements.
- Jim makes project decisions and reviews the work; Codex helps with implementation, testing, and explanations. Document AI assistance honestly.
- Work in this cloned repository, not the sibling `churn_predictor` draft.
- Jim wants to learn the project step by step. Explain what you are doing
  and why; pause for material decisions and answer questions along the way.
- Implement only the currently agreed step. Do not add future model,
  experiment tracking, API, interface, Docker, or deployment work early.
- Use a separate branch for each agreed step. The first branch combines
  project setup and data ingestion: `feat/setup-data-ingestion`.
- Before a commit, summarize the changes and validation and give Jim the
  opportunity to review. Then use focused commits and a PR into `main`.
- Jim reviews and merges PRs; wait until he is ready for the next step.
- Raw and processed CSVs stay local. Commit ingestion code, configuration,
  attribution, and an aggregate data summary. Do not commit `.venv` or secrets.
- Preserve raw data unchanged. Fit learned preprocessing only after splitting
  in a future modeling step. Customer IDs must not become model inputs.
- Jim chose to retain every customer and keep blank TotalCharges as missing
  numeric values. Do not fill with zero or drop these rows without discussion.
- The dataset is IBM's fictional telecom sample, not validated live customer
  data. Do not overstate the model's real-world predictive ability.
