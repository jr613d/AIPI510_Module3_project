# Model: Training, Selection, and Evaluation

How the model is built, how the final version and threshold were chosen, and how it was evaluated. Moved from the README during the final review; the README has a short summary.

## Encoding and training

Jim chose to start with eight understandable inputs. The rationale is to keep the first production pipeline manageable, make the model easier to explain, and reduce the number of fields required by the eventual API and interface. Tenure, contract, charges, services, and billing preferences have a plausible connection to churn. This is a deliberate scope and learning choice, not evidence that 19 predictors would be too many or that these eight are the strongest predictors. No automated feature selection or feature-set comparison informed this choice.

The comparison with all 19 eligible predictors was later run on validation data; see "Model selection and final evaluation" below.

| Treatment | Inputs |
| --- | --- |
| Numeric scaling | `tenure`, `MonthlyCharges` |
| One-hot encoding | `Contract`, `InternetService`, `TechSupport`, `OnlineSecurity`, `PaymentMethod`, `PaperlessBilling` |

One-hot encoding creates a 0/1 indicator for each category, avoiding an invented numeric order. For example, `Contract` produces indicators for `Month-to-month`, `One year`, and `Two year`. We retain all category indicators (`drop=None`) and use L2-regularized logistic regression. The current training categories produce 18 indicator columns, plus two scaled numeric columns: **20 model columns from eight original inputs**. Meaningful categories such as `No internet service` are retained. Unseen categories are encoded as all zeros for the corresponding field (`handle_unknown="ignore"`); this permits prediction but does not teach the model the meaning of that new category.

Numeric scaling subtracts each training column's mean and divides by its standard deviation. The scaler and category vocabulary are fitted only on training data, then reused without refitting for validation. The target maps `No` to 0 and `Yes` to 1. No imputation or class balancing is used. The classifier uses solver `lbfgs`, L2 regularization with `C: 1.0`, and a maximum of 1,000 iterations; the run stops if fitting does not converge.

Run training and validation from the repository:

```bash
python -m src.train
python -m unittest discover -s tests -v
```

Optional `--config <path>` arguments are supported by preprocessing and training. Inputs, split proportions, seed, regularization strength, iteration limit, threshold, and output paths are controlled by `config.yaml`.

Outputs are a local Git-ignored fitted pipeline at `artifacts/churn_pipeline.joblib` and an aggregate [validation report](../reports/training_validation.json). Both record the cloud source URI, download path, and checksum of the exact in-memory CSV bytes used for splitting and training. The report also records configuration, environment versions, partition counts, encoded column names, and validation metrics. The saved artifact contains the scaler, encoder, classifier, and settings. It can be recreated from the cloud data and configuration; the report is suitable for committing, while fitted artifacts remain local. Each successful run is also recorded in Weights & Biases (see the [experiment tracking guide](EXPERIMENT_TRACKING.md)).

| Initial validation result (before threshold selection) | Value |
| --- | ---: |
| ROC AUC | 0.8488 |
| Precision at provisional cutoff 0.5 | 67.10% |
| Recall at provisional cutoff 0.5 | 55.16% |
| Actual churners flagged | 155 |
| Customers who stayed but were flagged | 76 |
| Actual churners missed | 126 |
| Customers who stayed and were not flagged | 698 |

These were the first validation results, at the provisional 0.5 cutoff used before threshold selection. The final model uses threshold 0.35; see "Model selection and final evaluation" below. The dataset remains a fictional teaching sample and the model applies to the project's tenure-eligible population.

The tests for these steps (11 ingestion, 14 cloud-storage, 12 preprocessing, 6 training, 15 experiment tracking, 5 experiments, 5 threshold selection, 4 final evaluation) run offline under Python 3.13, along with `pip check`. The tests include train-only scales and category vocabulary, unseen categories, ID/target exclusion, missing-input rejection, saved-model reloading, convergence failure, and no test-partition access by the training routine. Cloud tests use mocked transfers. Separately, a live run of `python -m src.train` under Python 3.13 downloaded and verified the cloud CSV and reproduced the validation results above exactly.

## Model selection and final evaluation

We used W&B to compare model versions on **validation data**, chose the final model, and then scored it **once** on the held-out test data.

**1. Experiments** (`python -m src.experiments`, results in [reports/experiments.md](../reports/experiments.md)). We trained 8 versions: the 8-input model and an all-19-input model, each with regularization strength `C` = 0.01, 0.1, 1, and 10. Validation ROC AUC ranged only from 0.8487 to 0.8532. Changing `C` made no meaningful difference, and all 19 inputs scored about 0.004 higher than 8, which is within the random variation expected for about 1,000 validation customers. Jim kept the **8-input model with `C = 1.0`**. It is simpler to explain, needs a shorter input form, and leaves out gender and other demographic inputs.

**2. Threshold** (`python -m src.thresholds`, results in [reports/threshold_selection.md](../reports/threshold_selection.md)). The model outputs a churn probability, and the threshold decides when that counts as a predicted churner. We compared cutoffs from 0.20 to 0.70 on validation data. Jim chose **0.35**, which had the best balance of precision and recall (highest F1). Compared with 0.50, it catches 216 instead of 155 of the 281 validation churners, at the cost of 161 instead of 76 false alarms. This assumes that missing a customer who leaves costs more than an unnecessary retention contact; the dataset contains no real costs to confirm that.

**3. Final test** (`python -m src.evaluate`, results in [reports/test_evaluation.md](../reports/test_evaluation.md)). After the choices above were committed, the final model was retrained and scored once on 1,055 test customers that were never used for training or for any choice:

| Final test result | Value |
| --- | ---: |
| ROC AUC | **0.8192** |
| Threshold | 0.35 |
| Precision | 52.7% |
| Recall | 68.9% |
| Churners caught | 193 of 280 |
| False alarms | 173 |

Test results are a little lower than validation (ROC AUC 0.849, precision 57.3%, recall 76.9%). This is expected: the validation data was used to make choices, so its scores are slightly optimistic, and with about 280 churners per group, scores vary by a few points by chance. The model was not adjusted after seeing the test results. `src/evaluate.py` refuses to run again once the test report exists, so the test set stays a one-time check.

All runs are in the W&B project `aipi510-churn`: the 8 experiments and the threshold comparison (group `model-selection`), the final training run, and the `final-test` run.

[← Back to the README](../README.md)
