# Ethics and Limitations

**This model is built on fictional data.** The IBM Telco Customer Churn dataset describes 7,043 made-up customers of a made-up company, published by IBM for teaching. The pipeline is real, but the model's results say nothing about real customers.

With that in mind, I want to imagine these were real data and describe the four limitations and ethical considerations that matter for this project.

### 1. Ethics, bias, and fairness can't be fully evaluated without knowing the data's origin and how predictions are used

A real ethics review would start with two questions: **where did the data come from and how was it collected**, and **what happens to a customer after a prediction is made?** Neither can be answered here. IBM does not document how the sample was generated, and this homework project has no real business action attached to a prediction. Those are the most important questions for a real project. The same prediction could lead to a helpful retention discount or to something harmful, and the ethics depend on which.

### 2. Privacy: no re-identifiable data, and customer IDs kept out of the model

Data privacy means making sure nothing collected could re-identify a person. This dataset is synthetic, so no real person can be identified. Still, the source data includes customer IDs, which in a real setting could be joined to other, more sensitive records. I treated them with care: the IDs are used only to audit the data and are **intentionally excluded from the model's inputs**, the API, the app, and the experiment records. The API does not store the customer details it receives.

### 3. Excluding demographics does not guarantee fairness

I intentionally excluded gender, senior-citizen status, partner, and dependents from the model. (An experiment that added them, along with the remaining service and billing columns, improved validation ROC AUC by only about 0.004.) However, the model could still pick up on those factors through **confounding or proxy variables** that remain in the model. For example, payment method or internet service type may correlate with age, income, or location. I did not run a fairness audit comparing results across demographic groups, so I cannot claim the model treats those groups equally.

### 4. The dataset is small

After excluding 11 zero-tenure customers and splitting the data, the test set contains 1,055 customers and **only about 280 who churned**. With numbers this small, the test results (ROC AUC 0.819, precision 52.7%, recall 68.9%) could shift by several points with a different random split. They are honest, single-run estimates, not precise measurements.

---

**In short:** this project demonstrates a reproducible ML pipeline. Before a model like this could responsibly be used, it would need real data with a documented origin, a defined and reviewed use for its predictions, and a fairness audit.
