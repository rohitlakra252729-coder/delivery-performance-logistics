
import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path

st.set_page_config(
    page_title="Global Logistics Analytics",
    page_icon="🚚",
    layout="wide"
)

st.title("Global Supply Chain | Delivery Intelligence")
st.subheader(
    "Delivery Performance, Delay Risk & Logistics Efficiency"
)
st.caption("Unified Mentor Project | APL Logistics Analysis")

@st.cache_data
def load_csv(file):
    return pd.read_csv(file, low_memory=False)

uploaded_file = st.sidebar.file_uploader(
    "Upload your logistics dataset",
    type=["csv"]
)

data_path = Path("data/APL_Logistics.csv")

if uploaded_file is not None:
    df = load_csv(uploaded_file)
elif data_path.exists():
    df = load_csv(data_path)
else:
    st.info(
        "Please upload your APL Logistics CSV using the "
        "upload box in the left sidebar."
    )
    st.stop()

df.columns = df.columns.str.strip()

required = [
    "Days for shipping (real)",
    "Days for shipment (scheduled)",
    "Late_delivery_risk",
    "Shipping Mode",
    "Order Region",
    "Market",
    "Customer Segment"
]

missing = [c for c in required if c not in df.columns]

if missing:
    st.error("Missing columns: " + ", ".join(missing))
    st.stop()

for col in [
    "Days for shipping (real)",
    "Days for shipment (scheduled)",
    "Late_delivery_risk"
]:
    df[col] = pd.to_numeric(df[col], errors="coerce")

df = df.dropna(subset=required[:3]).copy()

df = df[
    (df["Days for shipping (real)"] >= 0)
    & (df["Days for shipment (scheduled)"] >= 0)
    & (df["Late_delivery_risk"].isin([0, 1]))
].copy()

if df.empty:
    st.error("No valid shipment records remain.")
    st.stop()

df["Delay Gap"] = (
    df["Days for shipping (real)"]
    - df["Days for shipment (scheduled)"]
)

df["Delivery Classification"] = "On-time"
df.loc[df["Delay Gap"] < 0, "Delivery Classification"] = "Early"
df.loc[df["Delay Gap"] > 0, "Delivery Classification"] = "Delayed"

st.sidebar.header("Filters")

def filter_options(column):
    options = sorted(df[column].dropna().unique().tolist())
    return st.sidebar.multiselect(
        column, options, default=options
    )

modes = filter_options("Shipping Mode")
regions = filter_options("Order Region")
markets = filter_options("Market")
segments = filter_options("Customer Segment")

filtered = df[
    df["Shipping Mode"].isin(modes)
    & df["Order Region"].isin(regions)
    & df["Market"].isin(markets)
    & df["Customer Segment"].isin(segments)
].copy()

if filtered.empty:
    st.warning("No shipments match your selected filters.")
    st.stop()

st.header("Delivery Performance Overview")

total = len(filtered)
on_time_rate = (filtered["Delay Gap"] <= 0).mean() * 100
delayed = (filtered["Delay Gap"] > 0).sum()
risk_rate = (
    filtered["Late_delivery_risk"] == 1
).mean() * 100
average_gap = filtered["Delay Gap"].mean()

c1, c2, c3, c4 = st.columns(4)
c1.metric("Total Shipments", f"{total:,}")
c2.metric("On-time / Early Rate", f"{on_time_rate:.2f}%")
c3.metric("Delayed Shipments", f"{delayed:,}")
c4.metric("Late Risk Flag Rate", f"{risk_rate:.2f}%")

st.metric("Average Delivery Gap", f"{average_gap:.2f} days")

st.subheader("Delivery Classification")

classification = (
    filtered["Delivery Classification"]
    .value_counts()
    .reindex(["Early", "On-time", "Delayed"], fill_value=0)
    .rename_axis("Classification")
    .reset_index(name="Shipments")
)

fig = px.bar(
    classification,
    x="Classification",
    y="Shipments",
    color="Classification",
    text="Shipments"
)
st.plotly_chart(fig, use_container_width=True)

st.subheader("Shipping Mode Comparison")

mode_summary = (
    filtered.groupby("Shipping Mode")
    .agg(
        Shipments=("Delay Gap", "size"),
        Average_Delay_Gap=("Delay Gap", "mean"),
        Delayed_Shipments=("Delay Gap", lambda x: (x > 0).sum()),
        Late_Risk_Rate=("Late_delivery_risk", "mean")
    )
    .reset_index()
)

mode_summary["Late_Risk_Rate"] *= 100

fig = px.bar(
    mode_summary,
    x="Shipping Mode",
    y="Average_Delay_Gap",
    color="Shipping Mode",
    title="Average Delay Gap by Shipping Mode"
)
st.plotly_chart(fig, use_container_width=True)
st.dataframe(mode_summary.round(2), use_container_width=True)

st.subheader("Regional and Market Analysis")

region_summary = (
    filtered.groupby(["Market", "Order Region"])
    .agg(
        Shipments=("Delay Gap", "size"),
        Average_Delay_Gap=("Delay Gap", "mean"),
        Late_Risk_Rate=("Late_delivery_risk", "mean")
    )
    .reset_index()
)

region_summary["Late_Risk_Rate"] *= 100

fig = px.bar(
    region_summary,
    x="Order Region",
    y="Late_Risk_Rate",
    color="Market",
    barmode="group",
    title="Late Risk Flag Rate by Region and Market"
)
st.plotly_chart(fig, use_container_width=True)
st.dataframe(region_summary.round(2), use_container_width=True)

st.subheader("Customer Segment Analysis")

segment_summary = (
    filtered.groupby("Customer Segment")
    .agg(
        Shipments=("Delay Gap", "size"),
        Average_Delay_Gap=("Delay Gap", "mean"),
        Late_Risk_Rate=("Late_delivery_risk", "mean")
    )
    .reset_index()
)

segment_summary["Late_Risk_Rate"] *= 100

fig = px.bar(
    segment_summary,
    x="Customer Segment",
    y="Late_Risk_Rate",
    color="Customer Segment",
    title="Late Risk Flag Rate by Customer Segment"
)
st.plotly_chart(fig, use_container_width=True)

st.subheader("Delay Gap Distribution")

fig = px.histogram(
    filtered,
    x="Delay Gap",
    nbins=30,
    title="Actual Shipping Days minus Scheduled Days"
)
fig.add_vline(x=0, line_dash="dash")
st.plotly_chart(fig, use_container_width=True)

st.subheader("Download Results")

st.download_button(
    "Download Filtered Data",
    data=filtered.to_csv(index=False).encode("utf-8"),
    file_name="filtered_logistics_data.csv",
    mime="text/csv"
)

st.caption(
    "A positive delay gap means actual shipping duration "
    "exceeded scheduled duration. The dataset risk flag is "
    "reported separately and is not assumed to be identical."
)
