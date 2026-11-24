"""Streamlit front-end for the churn prediction API.

Run locally:  streamlit run frontend/app.py
The API address comes from the API_URL environment variable or Streamlit
secret (default: http://localhost:8000). This app never loads the model itself;
every prediction is a request to the deployed API.
"""

import os

import streamlit as st

import charts
from client import (CHOICES, MONTHLY_CHARGES_RANGE, TENURE_RANGE, APIError,
                    biggest_lever, build_payload, explore, health, predict)


def api_url():
    try:
        secret = st.secrets.get("API_URL")
    except (FileNotFoundError, st.errors.StreamlitSecretNotFoundError):
        secret = None
    return (secret or os.environ.get("API_URL") or "http://localhost:8000").rstrip("/")


@st.cache_data(ttl=60, show_spinner=False)
def api_is_up(url):
    return health(url)


st.set_page_config(page_title="Customer churn predictor", page_icon=":material/trending_down:",
                   layout="centered")
URL = api_url()

with st.sidebar:
    st.header("Prediction service")
    st.caption(URL)
    if api_is_up(URL):
        st.success("Connected", icon=":material/check_circle:")
    else:
        st.warning("The first request can take a few seconds while the cloud service starts.",
                   title="Not responding yet", icon=":material/hourglass_top:")
    st.header("About this model")
    st.markdown(
        "- **Model:** logistic regression on 8 customer details\n"
        "- **Data:** IBM's *fictional* telecom sample (7,032 customers)\n"
        "- **Threshold:** customers at **35%** or higher are flagged as likely to churn\n"
        "- **Test-set results:** ROC AUC 0.82; recall 69% (caught 193 of 280 churners); "
        "precision 53% (about half of flagged customers actually left)"
    )
    st.caption("A teaching project for AIPI 510. Not validated for real business decisions.")

st.title("Customer churn predictor")
st.markdown("Enter a customer's account and service details to estimate how likely they are "
            "to leave the company (churn).")


def percent(value):
    """Avoid implying certainty: show <1% / >99% instead of 0% / 100%."""
    if value < 0.01:
        return "<1%"
    if value > 0.99:
        return ">99%"
    return f"{value:.0%}"


def choice(label, options, key, **kwargs):
    """All options visible; one must always be selected."""
    return st.segmented_control(label, options, default=options[0], required=True, key=key,
                                **kwargs)


with st.container(border=True):
    st.subheader("Account")
    left, right = st.columns(2)
    tenure = left.slider("Tenure (months as a customer)", *TENURE_RANGE, value=12, key="tenure")
    # Charges in the training data are recorded in 5-cent steps.
    monthly = right.slider("Monthly charges ($)", *MONTHLY_CHARGES_RANGE, value=70.0,
                           step=0.05, format="$%.2f", key="monthly")
    st.caption(f"Slider ranges match the training data: tenure {TENURE_RANGE[0]}–"
               f"{TENURE_RANGE[1]} months and monthly charges ${MONTHLY_CHARGES_RANGE[0]:.2f}–"
               f"${MONTHLY_CHARGES_RANGE[1]:.2f}. The model has not been tested outside "
               "these ranges, so its predictions are only validated within them.")
    contract = choice("Contract", CHOICES["Contract"], "contract")
    payment = choice("Payment method", CHOICES["PaymentMethod"], "payment")
    paperless = choice("Paperless billing", CHOICES["PaperlessBilling"], "paperless")

with st.container(border=True):
    st.subheader("Services")
    internet = choice("Internet service", CHOICES["InternetService"], "internet")
    has_internet = internet != "No"
    addon_choices = ["No", "Yes"] if has_internet else ["No internet service"]
    left, right = st.columns(2)
    with left:
        tech = choice("Tech support", addon_choices, f"tech_{has_internet}",
                      disabled=not has_internet)
    with right:
        security = choice("Online security", addon_choices, f"security_{has_internet}",
                          disabled=not has_internet)
    if not has_internet:
        st.caption("Tech support and online security require internet service.")


@st.cache_data(ttl=600, max_entries=50, show_spinner=False)
def explore_cached(url, payload_items):
    return explore(url, dict(payload_items))


try:
    payload = build_payload(tenure, monthly, contract, internet, tech, security,
                            payment, paperless)
except ValueError as error:
    payload = None
    st.error(str(error), icon=":material/error:")

if st.button("Predict churn", type="primary", width="stretch",
             icon=":material/query_stats:", key="predict", disabled=payload is None):
    try:
        with st.spinner("Asking the model…"):
            st.session_state.last = {"payload": payload, "result": predict(URL, payload)}
    except APIError as error:
        st.session_state.pop("last", None)
        st.error(str(error), icon=":material/error:")

last = st.session_state.get("last")
if last and last["payload"] != payload:
    st.info("The inputs changed. Click **Predict churn** to update the prediction.",
            icon=":material/refresh:")
elif last:
    result = last["result"]
    probability, threshold = result["churn_probability"], result["threshold"]
    likely = result["churn_prediction"] == "Yes"
    with st.container(border=True):
        left, right = st.columns(2)
        left.metric("Churn probability", percent(probability))
        right.metric("Prediction", "Likely to churn" if likely else "Likely to stay")
        st.progress(probability)
        comparison = "at or above" if likely else "below"
        message = (f"This customer's estimated churn probability is **{percent(probability)}**, "
                   f"{comparison} the model's **{threshold:.0%}** threshold.")
        if likely:
            st.warning(message, title="Likely to churn", icon=":material/warning:")
        else:
            st.success(message, title="Likely to stay", icon=":material/check_circle:")
        st.caption("The threshold is set low on purpose: it catches more customers who "
                   "leave, at the cost of more false alarms. About 27% of customers in the "
                   "sample churned. The estimate shows a pattern in fictional training data, "
                   "not a certainty about a real customer.")

    st.header("Explore how the model sees this customer")
    st.caption("Each view below asks the same API about this customer with one detail "
               "changed. Orange marks this customer; the dashed line is the "
               f"{threshold:.0%} threshold.")
    try:
        with st.spinner("Asking the model “what if?”…"):
            explored = explore_cached(URL, tuple(sorted(payload.items())))
    except APIError as error:
        st.error(f"The exploration could not be loaded. {error}", icon=":material/error:")
    else:
        palette = charts.colors(st.context.theme.type)
        levers_tab, curves_tab, curve_tab = st.tabs(
            [":material/tune: What would change the risk?",
             ":material/show_chart: Tenure and charges",
             ":material/function: The S-curve"])
        with levers_tab:
            st.markdown("Each row is one of the customer's choices. Dots show the churn "
                        "probability if only that choice were different; rows with the "
                        "widest spread matter most for this customer.")
            st.altair_chart(charts.lever_chart(explored["levers"], threshold, palette),
                            alt="Churn probability for each alternative choice, "
                                "widest effect at the top")
            lever = biggest_lever(explored["levers"])
            if lever:
                st.info(f"Changing **{lever['field'].lower()}** to **{lever['option']}** would "
                        f"lower this customer's estimated risk the most: from "
                        f"{percent(lever['from'])} to {percent(lever['probability'])}.",
                        title="Biggest single lever", icon=":material/lightbulb:")
            else:
                st.info("No single change to these choices would lower this customer's risk.",
                        icon=":material/lightbulb:")
        with curves_tab:
            st.markdown("How this customer's churn probability would change across the full "
                        "range of tenure and monthly charges, with everything else unchanged.")
            left, right = st.columns(2)
            left.altair_chart(charts.curve_chart(
                explored["curves"]["tenure"], "tenure", "Tenure (months)", "d", threshold,
                palette), alt="Churn probability across tenure for this customer")
            right.altair_chart(charts.curve_chart(
                explored["curves"]["MonthlyCharges"], "MonthlyCharges", "Monthly charges",
                "$.0f", threshold, palette),
                alt="Churn probability across monthly charges for this customer")
        with curve_tab:
            st.markdown("Logistic regression multiplies each input by a weight it learned "
                        "from the training data and adds them up into one **score**. The "
                        "S-shaped *logistic function* turns any score into a probability "
                        "between 0% and 100%. Every prediction lands somewhere on this curve; "
                        "scores right of the dashed line cross the threshold.")
            st.altair_chart(charts.s_curve_chart(probability, threshold, palette),
                            alt="Logistic S-curve showing where this customer's score lands")
            st.caption("The score shown is the one implied by the API's probability "
                       f"(log-odds). The {threshold:.0%} threshold corresponds to a score of "
                       f"{charts.logit(threshold):.2f}.")
