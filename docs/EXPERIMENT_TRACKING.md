# Experiment tracking with Weights & Biases

## What W&B contributes

Cloud storage supplies the data used for training. W&B records the result of
each experiment so we can compare configurations and identify the model they
produced. A run is one record of a completed training result:

```text
Verified cloud data → training and validation → model file + validation report
                                                          ↓
                                                  src/tracking.py
                                                          ↓
                                W&B run: settings, metrics, model artifact
```

The tracking helper does not split data, train a model, choose a threshold,
or evaluate the test partition. It labels metrics as validation metrics and
refuses a report marked as test evaluation. Final test reporting will require
an explicit integration decision rather than silently relabeling results.

## What is recorded

- The selected training settings: features, split fractions, seed, eligibility
  rule, model parameters, and classification threshold.
- Validation ROC AUC, precision, recall, threshold, and confusion-matrix counts.
- The threshold status supplied by training, rather than a claim it was tuned.
- The input data's SHA-256 and cloud URI.
- Package versions from the report, plus the current Git commit and dirty flag.
  A dirty working tree means the commit alone does not identify all run code.
- A versioned `churn-model` artifact (`v0`, `v1`, …) containing a snapshot of
  the `.joblib` model and a selected aggregate JSON report. Its metadata
  includes the SHA-256 fingerprints of the model and input data.

The helper uses explicit report/settings fields instead of uploading the whole
application configuration. It does not add source CSVs, customer rows, API
keys, or Google credentials as artifacts. Code/diff capture and console capture
are disabled. Model snapshots are taken before logging so an original file
changing during upload cannot change the bytes recorded for that run. Treat
saved model files as trusted application artifacts; the helper copies their
bytes and never deserializes them.

## Setup

`wandb==0.31.2` is part of `requirements.txt`, so the normal project install
includes it. Authenticate once per computer, in your own terminal:

```bash
source .venv/bin/activate
wandb login
```

Paste the API key from your W&B settings page when prompted. The key is saved
in your home directory (`~/.netrc`), outside the repository; never put it in
`config.yaml`, source files, or chat. Anyone else reproducing the project uses
their own W&B account, just as they would use their own Google Cloud bucket.

The W&B workspace is separate from your Google Cloud project. Google login
authorizes reading the dataset; W&B login authorizes writing experiment
records. People using the eventual prediction app will not need either login.

## Configuration and usage

`config.yaml` controls tracking:

```yaml
tracking:
  project: aipi510-churn
  entity: null  # null = the default workspace of your W&B login
  mode: online  # online | offline | disabled
```

Training records a run automatically after it succeeds:

```bash
python -m src.train                          # uses tracking.mode (online)
python -m src.train --tracking-mode offline  # save locally; upload later with `wandb sync`
python -m src.train --tracking-mode disabled # no W&B at all
```

The tracking settings are checked before training starts, so a typo in the
mode does not waste a training run. Logging starts after successful training.
If logging fails (for example, no network or no login), the model and report
are still saved, but the command exits with an error rather than claiming the
run was tracked.

Offline runs are written under `wandb/` in the repository; `wandb/.gitignore`
keeps them out of Git. Offline artifact files are staged in W&B's data
directory until synced.

## Model-selection runs

Three more commands record runs in the same W&B project:

| Command | W&B run(s) | Data scored |
| --- | --- | --- |
| `python -m src.experiments` | One run per C value × feature set, group `model-selection` | Validation |
| `python -m src.thresholds` | `threshold-selection`: a table and a precision/recall chart | Validation |
| `python -m src.evaluate` | `final-test`, with metrics under `test/` | Test, once |

`log_training_run()` still refuses test results; the final test uses the
separate `log_test_run()`, so test metrics are never labelled as validation
metrics. `src/evaluate.py` refuses to run again once `reports/test_evaluation.json`
exists.

## Checks

```bash
python -m unittest discover -s tests -v       # all offline tests, mocked W&B
python tests/check_tracking_offline.py        # real SDK, offline, synthetic files
```

The unit tests use an injected SDK and synthetic fixtures, with no training or
account access. They check validation metric names, artifact/model
fingerprints, matching cloud provenance, rejection of test results and invalid
metrics, exclusion of extra report fields, propagation of logging errors, and
the training command's wiring: config mode, command-line override, disabled
mode, failure exit, and early rejection of an invalid mode.

The smoke check runs the real W&B SDK in offline mode inside a temporary
folder and confirms the run record and both artifact files were written.

## Verification record

On November 23, 2026, under Python 3.13.18 and wandb 0.31.2:

- All 55 offline tests passed and `pip check` was clean.
- The offline smoke check passed after correcting where it looks for staged
  artifact files (wandb 0.31 stages them in the data directory, not the cache).
- `python -m src.train --tracking-mode offline` downloaded and verified the
  cloud CSV, reproduced the validation results (ROC AUC 0.8488), and wrote an
  offline run.
- `python -m src.train` (online) uploaded run `qki8atue` to project
  `aipi510-churn` in workspace `jr613-d`, with validation metrics and the
  `churn-model` artifact. The code was uncommitted at the time, so that run
  records `git_dirty: true`.

References: [W&B SDK and version](https://pypi.org/project/wandb/0.31.2/),
[SDK initialization](https://github.com/wandb/wandb/blob/main/wandb/sdk/wandb_init.py),
[SDK settings](https://github.com/wandb/wandb/blob/main/wandb/sdk/wandb_settings.py).
