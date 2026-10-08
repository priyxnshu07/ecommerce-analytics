"""Interactive dashboard for the Olist e-commerce analysis.

    streamlit run app.py

Every chart runs the same sql/*.sql files as the analysis (src/analysis.py),
on whatever slice the filters select, so the two can never disagree.
"""
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src.analysis import SQL_DIR, connect, run_query

# Validated palette (colorblind-safe pairs; see README > Methods).
BLUE, ORANGE, RED = "#2a78d6", "#eb6834", "#d03b3b"
INK, MUTED, GRID = "#0b0b0b", "#52514e", "#e8e7e3"

st.set_page_config(page_title="Olist E-commerce Analytics", page_icon="📊", layout="wide")


@st.cache_data(show_spinner=False)
def months_and_states():
    con = connect()
    months = [str(m) for (m,) in con.execute(
        "SELECT DISTINCT purchase_month FROM revenue_orders ORDER BY 1").fetchall()]
    states = [s for (s,) in con.execute(
        "SELECT DISTINCT customer_state FROM revenue_orders ORDER BY 1").fetchall()]
    return months, states


@st.cache_data(show_spinner=False)
def results(start: str, end: str, states: tuple[str, ...]) -> dict[str, pd.DataFrame]:
    con = connect(start, end, list(states) or None)
    out = {p.stem: run_query(con, p) for p in sorted(SQL_DIR.glob("*.sql"))}
    out["kpis"] = con.execute("""
        SELECT
            (SELECT SUM(gmv) FROM revenue_orders)                                  AS gmv,
            (SELECT COUNT(*) FROM revenue_orders)                                  AS orders,
            (SELECT AVG(gmv) FROM revenue_orders)                                  AS aov,
            (SELECT AVG(CASE WHEN is_late THEN 1.0 ELSE 0 END) FROM orders WHERE in_window AND has_delivery) AS late_rate,
            (SELECT AVG(review_score) FROM orders WHERE in_window AND review_score IS NOT NULL) AS avg_review
    """).df()
    out["late_by_month"] = con.execute("""
        SELECT purchase_month, AVG(CASE WHEN is_late THEN 1.0 ELSE 0 END) * 100 AS late_rate_pct, COUNT(*) AS delivered
        FROM orders WHERE in_window AND has_delivery GROUP BY 1 ORDER BY 1
    """).df()
    return out


def style(fig: go.Figure, height: int = 360, legend: bool = False) -> go.Figure:
    fig.update_layout(
        height=height, margin=dict(l=8, r=8, t=8, b=8),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, system-ui, sans-serif", size=13, color=INK),
        showlegend=legend, legend=dict(orientation="h", y=1.08, x=0, font=dict(color=MUTED)),
        hoverlabel=dict(bgcolor="white", font_color=INK, bordercolor=GRID),
        bargap=0.35,
    )
    fig.update_xaxes(showgrid=False, linecolor=GRID, tickfont=dict(color=MUTED), title_font=dict(color=MUTED))
    fig.update_yaxes(gridcolor=GRID, zeroline=False, tickfont=dict(color=MUTED), title_font=dict(color=MUTED))
    return fig


def brl(x: float) -> str:
    return f"R${x / 1e6:.2f}M" if x >= 1e6 else f"R${x:,.0f}"


# ---------------------------------------------------------------- filters
months, all_states = months_and_states()
st.title("Olist E-commerce Analytics")
st.caption(
    "~100,000 orders from a Brazilian online marketplace, Jan 2017 – Aug 2018. "
    "Revenue = item value excluding freight (R$, Brazilian real)."
)

f1, f2 = st.columns([2, 3])
with f1:
    start, end = st.select_slider(
        "Months", options=months, value=(months[0], months[-1]),
        format_func=lambda m: pd.Timestamp(m).strftime("%b %Y"),
    )
with f2:
    states = st.multiselect("Customer state (all if empty)", all_states, placeholder="All states")

data = results(start, end, tuple(states))
k = data["kpis"].iloc[0]
if pd.isna(k["orders"]) or k["orders"] == 0:
    st.warning("No orders match these filters.")
    st.stop()

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Revenue", brl(k["gmv"]))
c2.metric("Orders", f"{int(k['orders']):,}")
c3.metric("Avg order value", f"R${k['aov']:.0f}")
c4.metric("Late deliveries", f"{k['late_rate'] * 100:.1f}%")
c5.metric("Avg review", f"{k['avg_review']:.2f} / 5")

growth, delivery, customers, catalogue = st.tabs(
    ["📈 Growth", "🚚 Delivery & reviews", "👥 Customers", "🏷️ Categories & sellers"])

# ---------------------------------------------------------------- growth
with growth:
    m = data["01_monthly_revenue"]
    peak = m.loc[m["gmv"].idxmax()]
    st.subheader(f"Monthly revenue peaked in {pd.Timestamp(peak['purchase_month']):%b %Y} at {brl(peak['gmv'])}")
    fig = go.Figure(go.Scatter(
        x=m["purchase_month"], y=m["gmv"], mode="lines+markers",
        line=dict(color=BLUE, width=2), marker=dict(size=8, color=BLUE),
        customdata=m[["orders", "avg_order_value"]],
        hovertemplate="%{x|%b %Y}<br>Revenue R$%{y:,.0f}<br>Orders %{customdata[0]:,}<br>AOV R$%{customdata[1]:.0f}<extra></extra>",
    ))
    fig.add_annotation(x=peak["purchase_month"], y=peak["gmv"], text=f"Peak: {pd.Timestamp(peak['purchase_month']):%b %Y}",
                       showarrow=True, arrowhead=0, ay=-30, font=dict(color=MUTED, size=12))
    fig.update_yaxes(title="Revenue (R$)", tickprefix="R$", tickformat="~s")
    st.plotly_chart(style(fig), use_container_width=True)
    with st.expander("Show data"):
        st.dataframe(m, hide_index=True, use_container_width=True)

# ---------------------------------------------------------------- delivery
with delivery:
    d = data["02_delivery_vs_reviews"]
    late = d[d["is_late"]]
    on_time = d[~d["is_late"]]
    late_avg = (late["avg_review"] * late["orders"]).sum() / max(late["orders"].sum(), 1)
    ok_avg = (on_time["avg_review"] * on_time["orders"]).sum() / max(on_time["orders"].sum(), 1)
    st.subheader(f"Late orders average {late_avg:.2f} stars vs {ok_avg:.2f} when on time")
    fig = go.Figure()
    for subset, name, color in ((on_time, "On time or early", BLUE), (late, "Late", RED)):
        fig.add_bar(
            x=subset["delivery_bucket"].str[3:], y=subset["avg_review"], name=name,
            marker=dict(color=color, cornerradius=4),
            text=subset["avg_review"].map("{:.2f}".format), textposition="outside", textfont=dict(color=INK),
            customdata=subset[["orders", "pct_1_or_2_stars"]],
            hovertemplate="%{x}<br>Avg review %{y:.2f}<br>Orders %{customdata[0]:,}<br>1–2 stars %{customdata[1]:.1f}%<extra></extra>",
        )
    fig.update_yaxes(title="Average review (1–5)", range=[0, 5.3])
    fig.update_xaxes(title="Delivery vs the date promised at checkout")
    st.plotly_chart(style(fig, legend=True), use_container_width=True)

    lm = data["late_by_month"]
    st.markdown("**Late-delivery rate by month** — spikes follow demand peaks")
    fig = go.Figure(go.Scatter(
        x=lm["purchase_month"], y=lm["late_rate_pct"], mode="lines+markers",
        line=dict(color=RED, width=2), marker=dict(size=8, color=RED),
        customdata=lm[["delivered"]],
        hovertemplate="%{x|%b %Y}<br>Late %{y:.1f}%<br>Delivered %{customdata[0]:,}<extra></extra>",
    ))
    fig.add_hline(y=k["late_rate"] * 100, line=dict(color=MUTED, width=1, dash="dot"),
                  annotation_text=f"average {k['late_rate'] * 100:.1f}%", annotation_font_color=MUTED)
    fig.update_yaxes(title="Late deliveries (%)", ticksuffix="%", rangemode="tozero")
    st.plotly_chart(style(fig, height=300), use_container_width=True)
    with st.expander("Show data"):
        st.dataframe(d, hide_index=True, use_container_width=True)

# ---------------------------------------------------------------- customers
with customers:
    r = data["03_repeat_customers"].iloc[0]
    st.subheader(f"Only {r['repeat_rate_pct']:.1f}% of customers ever order again")
    a, b, c = st.columns(3)
    a.metric("Customers", f"{int(r['customers']):,}")
    b.metric("Repeat customers", f"{int(r['repeat_customers']):,}")
    c.metric("Median days to 2nd order", "–" if pd.isna(r["median_days_to_second_order"]) else f"{r['median_days_to_second_order']:.0f}")

    seg = data["05_rfm_segments"].sort_values("pct_gmv")
    st.markdown("**RFM segments — share of customers vs share of revenue**")
    fig = go.Figure()
    for col, name, color in (("pct_customers", "% of customers", BLUE), ("pct_gmv", "% of revenue", ORANGE)):
        fig.add_bar(y=seg["segment"], x=seg[col], name=name, orientation="h",
                    marker=dict(color=color, cornerradius=4),
                    hovertemplate="%{y}<br>" + name + " %{x:.1f}%<extra></extra>")
    fig.update_xaxes(title="Share (%)", ticksuffix="%", showgrid=True, gridcolor=GRID)
    fig.update_yaxes(showgrid=False)
    st.plotly_chart(style(fig, height=380, legend=True).update_layout(
        barmode="group", bargap=0.25, bargroupgap=0.08, legend_traceorder="reversed"),
                    use_container_width=True)
    st.caption("Recency and spend are scored in quintiles; frequency by order count, since ~97% of customers order once.")
    with st.expander("Show data"):
        st.dataframe(data["05_rfm_segments"], hide_index=True, use_container_width=True)

# ---------------------------------------------------------------- catalogue
with catalogue:
    cat = data["04_category_pareto"]
    sellers = data["04b_seller_concentration"]
    top_decile = sellers.iloc[0]["gmv_share_pct"]
    st.subheader(f"The top 10% of sellers generate {top_decile:.0f}% of revenue")
    left, right = st.columns(2)
    with left:
        top = cat.head(12).iloc[::-1]
        st.markdown("**Top 12 categories by revenue**")
        fig = go.Figure(go.Bar(
            y=top["category"].str.replace("_", " "), x=top["gmv"], orientation="h",
            marker=dict(color=BLUE, cornerradius=4),
            customdata=top[["gmv_share_pct", "avg_review", "late_rate_pct"]],
            hovertemplate="%{y}<br>Revenue R$%{x:,.0f} (%{customdata[0]:.1f}%)<br>Avg review %{customdata[1]:.2f}<br>Late %{customdata[2]:.1f}%<extra></extra>",
        ))
        fig.update_xaxes(title="Revenue (R$)", tickprefix="R$", tickformat="~s", showgrid=True, gridcolor=GRID)
        fig.update_yaxes(showgrid=False)
        st.plotly_chart(style(fig, height=420), use_container_width=True)
    with right:
        st.markdown("**Revenue share by seller decile** (1 = top 10% of sellers)")
        fig = go.Figure(go.Bar(
            x=sellers["seller_decile"].astype(str), y=sellers["gmv_share_pct"],
            marker=dict(color=BLUE, cornerradius=4),
            text=sellers["gmv_share_pct"].map(lambda v: f"{v:.0f}%" if v >= 1 else f"{v:.1f}%"),
            textposition="outside", textfont=dict(color=INK),
            customdata=sellers[["sellers", "cumulative_share_pct"]],
            hovertemplate="Decile %{x}<br>%{y:.1f}% of revenue<br>%{customdata[0]:,} sellers<br>Cumulative %{customdata[1]:.1f}%<extra></extra>",
        ))
        fig.update_yaxes(title="Share of revenue (%)", ticksuffix="%", range=[0, max(sellers["gmv_share_pct"]) * 1.15])
        fig.update_xaxes(title="Seller decile", type="category")
        st.plotly_chart(style(fig, height=420), use_container_width=True)
    with st.expander("Show data"):
        st.dataframe(cat, hide_index=True, use_container_width=True)

st.caption(
    "Data: [Olist Brazilian E-Commerce Public Dataset](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce) "
    "(CC BY-NC-SA 4.0). Code: [github.com/priyxnshu07/ecommerce-analytics](https://github.com/priyxnshu07/ecommerce-analytics)."
)
