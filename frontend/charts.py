"""Altair charts that show how the model responds to one customer's inputs.

Colors follow the reference data-viz palette: blue for the model's answers,
orange for "this customer", and a muted dashed line for the threshold.
"""

import math

import altair as alt
import pandas as pd

PALETTE = {
    "light": {"model": "#2a78d6", "customer": "#eb6834", "muted": "#898781", "surface": "#fcfcfb"},
    "dark": {"model": "#3987e5", "customer": "#d95926", "muted": "#898781", "surface": "#1a1a19"},
}
PERCENT = alt.Axis(format="%", values=[0, 0.25, 0.5, 0.75, 1])


def colors(theme_type):
    return PALETTE["dark" if theme_type == "dark" else "light"]


def _threshold_rule(threshold, c):
    return alt.Chart(pd.DataFrame({"y": [threshold]})).mark_rule(
        color=c["muted"], strokeDash=[4, 4], strokeWidth=1.5).encode(y="y:Q")


def option_labels(data, gap=0.08):
    """Label the other options under their dots, merging dots closer than `gap`.

    Close dots share one label (e.g. "Bank transfer / Credit card") so text never
    overlaps; each dot's exact value stays in its tooltip.
    """
    rows = []
    others = data[~data["current"]].sort_values("probability")
    for field, group in others.groupby("field", sort=False):
        cluster = []
        for _, row in group.iterrows():
            if cluster and row["probability"] - cluster[-1]["probability"] > gap:
                rows.append(_merge(field, cluster))
                cluster = []
            cluster.append(row)
        rows.append(_merge(field, cluster))
    return rows


def _merge(field, cluster):
    names = " / ".join(row["option"].replace(" (automatic)", "") for row in cluster)
    return field, sum(row["probability"] for row in cluster) / len(cluster), names


def lever_chart(levers, threshold, c):
    """Dot plot: one row per choice, one dot per option, this customer's dot in orange."""
    data = pd.DataFrame(levers)
    data["who"] = data["current"].map({True: "This customer", False: "Other option"})
    spread = data.groupby("field")["probability"].agg(lambda s: s.max() - s.min())
    order = spread.sort_values(ascending=False).index.tolist()  # Biggest effect on top.
    y = alt.Y("field:N", sort=order, title=None)
    x = alt.X("probability:Q", title="Churn probability", scale=alt.Scale(domain=[0, 1]),
              axis=PERCENT)
    span = alt.Chart(data).mark_rule(color=c["muted"], strokeWidth=2, opacity=0.5).encode(
        y=y, x="min(probability):Q", x2="max(probability):Q")
    dots = alt.Chart(data).mark_circle(size=140, opacity=1, stroke=c["surface"],
                                       strokeWidth=2).encode(
        y=y, x=x,
        color=alt.Color("who:N", title=None, legend=alt.Legend(orient="top"),
                        scale=alt.Scale(domain=["This customer", "Other option"],
                                        range=[c["customer"], c["model"]])),
        order=alt.Order("current:Q"),  # Draw this customer's dot on top.
        tooltip=[alt.Tooltip("field:N", title="Input"), alt.Tooltip("option:N", title="Option"),
                 alt.Tooltip("probability:Q", title="Churn probability", format=".0%")],
    )
    names = pd.DataFrame(option_labels(data), columns=["field", "probability", "option"])
    labels = alt.Chart(names).mark_text(dy=15, fontSize=10, color=c["muted"]).encode(
        y=y, x="probability:Q", text="option:N")
    cut = pd.DataFrame({"x": [threshold], "label": [f"{threshold:.0%} threshold"]})
    rule = alt.Chart(cut).mark_rule(color=c["muted"], strokeDash=[4, 4],
                                    strokeWidth=1.5).encode(x="x:Q")
    rule_label = alt.Chart(cut).mark_text(align="left", dx=6, y=-8, color=c["muted"]).encode(
        x="x:Q", text="label:N")
    return (span + rule + rule_label + dots + labels).properties(
        height=55 * data["field"].nunique() + 40)


def curve_chart(points, x_field, x_title, x_format, threshold, c):
    """Line of probability across an input's range, with this customer as a point."""
    data = pd.DataFrame(points)
    x = alt.X("value:Q", title=x_title, axis=alt.Axis(format=x_format),
              scale=alt.Scale(domain=[data["value"].min(), data["value"].max()], nice=False))
    y = alt.Y("probability:Q", title="Churn probability", scale=alt.Scale(domain=[0, 1]),
              axis=PERCENT)
    tooltip = [alt.Tooltip("value:Q", title=x_title, format=x_format),
               alt.Tooltip("probability:Q", title="Churn probability", format=".0%")]
    line = alt.Chart(data).mark_line(color=c["model"], strokeWidth=2).encode(
        x=x, y=y, tooltip=tooltip)
    hover = alt.Chart(data).mark_circle(size=200, opacity=0).encode(x=x, y=y, tooltip=tooltip)
    me = alt.Chart(data[data["current"]]).mark_circle(
        size=140, color=c["customer"], opacity=1, stroke=c["surface"], strokeWidth=2).encode(
        x=x, y=y, tooltip=tooltip)
    return (_threshold_rule(threshold, c) + line + hover + me).properties(height=260)


def logit(probability):
    p = min(max(probability, 1e-6), 1 - 1e-6)
    return math.log(p / (1 - p))


def s_curve_chart(probability, threshold, c):
    """The logistic S-curve: score on x, probability on y, this customer and the threshold."""
    span = max(6.0, abs(logit(probability)) + 1)
    xs = [-span + i * (2 * span / 120) for i in range(121)]
    curve = pd.DataFrame({"score": xs, "probability": [1 / (1 + math.exp(-x)) for x in xs]})
    x = alt.X("score:Q", title="Model score (weighted sum of the inputs)",
              scale=alt.Scale(domain=[-span, span]))
    y = alt.Y("probability:Q", title="Churn probability", scale=alt.Scale(domain=[0, 1]),
              axis=PERCENT)
    line = alt.Chart(curve).mark_line(color=c["model"], strokeWidth=2).encode(x=x, y=y)
    cut = pd.DataFrame({"score": [logit(threshold)], "probability": [threshold]})
    cut_rule = alt.Chart(cut).mark_rule(color=c["muted"], strokeDash=[4, 4],
                                        strokeWidth=1.5).encode(x="score:Q")
    me_data = pd.DataFrame({"score": [logit(probability)], "probability": [probability],
                            "label": ["This customer"]})
    me = alt.Chart(me_data).mark_circle(size=160, color=c["customer"], opacity=1,
                                        stroke=c["surface"], strokeWidth=2).encode(
        x=x, y=y, tooltip=[alt.Tooltip("probability:Q", title="Churn probability",
                                       format=".1%")])
    # Label text stays in the text color; the orange dot carries the identity.
    label = alt.Chart(me_data).mark_text(align="left", dx=10, dy=-10,
                                         fontWeight="bold").encode(x=x, y=y, text="label:N")
    cut_label = alt.Chart(cut.assign(label=f"{threshold:.0%} threshold")).mark_text(
        align="left", dx=6, y=8, color=c["muted"]).encode(x="score:Q", text="label:N")
    return (_threshold_rule(threshold, c) + cut_rule + line + me + label + cut_label
            ).properties(height=280)
