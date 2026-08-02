
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from itertools import combinations
from io import BytesIO

st.set_page_config(
    page_title="Google Product Intelligence",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

REQUIRED_COLUMNS = [
    "User_ID", "Age_Group", "Occupation", "Region",
    "Google_Products_Used", "Most_Used_Product",
    "Usage_Frequency", "Satisfaction_Score",
    "Non_Adoption_Reason", "Data_Source"
]

PRODUCTS = [
    "Google Search", "YouTube", "Gmail", "Google Maps", "Google Chrome",
    "Google Drive", "Google Photos", "Google Meet", "Google Docs", "Google Pay"
]

st.markdown("""
<style>
    .main-header {
        font-size: 2.25rem;
        font-weight: 700;
        margin-bottom: 0.15rem;
    }
    .sub-header {
        color: #5f6368;
        margin-bottom: 1.25rem;
    }
    .insight-card {
        padding: 1rem 1.1rem;
        border-radius: 12px;
        background: #f8f9fa;
        border: 1px solid #e8eaed;
        margin-bottom: .75rem;
    }
    .small-note {
        color: #5f6368;
        font-size: .9rem;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_data
def load_data(uploaded_file=None):
    if uploaded_file is not None:
        data = pd.read_csv(uploaded_file)
    else:
        data = pd.read_csv("google_product_usage_500_synthetic.csv")
    return data

def validate_data(data):
    missing = [c for c in REQUIRED_COLUMNS if c not in data.columns]
    return missing

def prepare_data(data):
    d = data.copy()
    d["Satisfaction_Score"] = pd.to_numeric(d["Satisfaction_Score"], errors="coerce")
    d["Product_List"] = d["Google_Products_Used"].fillna("").apply(
        lambda x: [p.strip() for p in str(x).split(";") if p.strip()]
    )
    d["Product_Count"] = d["Product_List"].apply(len)
    d["User_Segment"] = pd.cut(
        d["Product_Count"],
        bins=[-1, 3, 6, 1000],
        labels=["Basic User", "Regular User", "Power User"]
    )
    return d

def product_long(data):
    rows = []
    for _, row in data.iterrows():
        for product in row["Product_List"]:
            rows.append({
                "User_ID": row["User_ID"],
                "Age_Group": row["Age_Group"],
                "Occupation": row["Occupation"],
                "Region": row["Region"],
                "Usage_Frequency": row["Usage_Frequency"],
                "Satisfaction_Score": row["Satisfaction_Score"],
                "Product": product,
                "Data_Source": row["Data_Source"]
            })
    return pd.DataFrame(rows)

def adoption_table(data):
    total = data["User_ID"].nunique()
    long = product_long(data)
    if total == 0 or long.empty:
        return pd.DataFrame(columns=["Product", "Users", "Adoption_Rate"])
    out = (
        long.groupby("Product")["User_ID"].nunique()
        .reset_index(name="Users")
        .sort_values("Users", ascending=False)
    )
    out["Adoption_Rate"] = out["Users"] / total * 100
    return out

def co_usage(data):
    counts = {}
    for products in data["Product_List"]:
        unique_products = sorted(set(products))
        for a, b in combinations(unique_products, 2):
            key = (a, b)
            counts[key] = counts.get(key, 0) + 1
    rows = [{"Product_A": a, "Product_B": b, "Shared_Users": n}
            for (a, b), n in counts.items()]
    if not rows:
        return pd.DataFrame(columns=["Product_A", "Product_B", "Shared_Users"])
    return pd.DataFrame(rows).sort_values("Shared_Users", ascending=False)

def safe_pct(a, b):
    return (a / b * 100) if b else 0

# ---------------- Sidebar ----------------
st.sidebar.markdown("## 📊 Google Product Intelligence")
st.sidebar.caption("User Adoption & Product Analytics Platform")

uploaded = st.sidebar.file_uploader("Upload another CSV", type=["csv"])
data = load_data(uploaded)

missing_cols = validate_data(data)
if missing_cols:
    st.error("Dataset validation failed. Missing required columns: " + ", ".join(missing_cols))
    st.stop()

data = prepare_data(data)

st.sidebar.divider()
st.sidebar.caption("Filters")

def options(col):
    return sorted([x for x in data[col].dropna().unique().tolist()])

age_filter = st.sidebar.multiselect("Age Group", options("Age_Group"), default=options("Age_Group"))
occ_filter = st.sidebar.multiselect("Occupation", options("Occupation"), default=options("Occupation"))
region_filter = st.sidebar.multiselect("Region", options("Region"), default=options("Region"))
freq_filter = st.sidebar.multiselect("Usage Frequency", options("Usage_Frequency"), default=options("Usage_Frequency"))
source_filter = st.sidebar.multiselect("Data Source", options("Data_Source"), default=options("Data_Source"))

if st.sidebar.button("Reset Filters"):
    st.rerun()

filtered = data[
    data["Age_Group"].isin(age_filter) &
    data["Occupation"].isin(occ_filter) &
    data["Region"].isin(region_filter) &
    data["Usage_Frequency"].isin(freq_filter) &
    data["Data_Source"].isin(source_filter)
].copy()

# ---------------- Header ----------------
st.markdown('<div class="main-header">Google Product Intelligence</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="sub-header">Interactive user adoption, engagement, satisfaction and product ecosystem analytics</div>',
    unsafe_allow_html=True
)

st.info(
    "Data disclaimer: This portfolio application uses synthetic and/or user-provided survey data. "
    "It is not affiliated with Google and does not use Google's proprietary or internal analytics."
)

page = st.sidebar.radio(
    "Navigate",
    [
        "Executive Overview",
        "Data Quality",
        "Product Analytics",
        "User Segmentation",
        "Product Co-Usage",
        "Automated Insights",
        "Ask Your Data"
    ]
)

# ---------------- Executive Overview ----------------
if page == "Executive Overview":
    st.subheader("Executive Overview")
    total_users = filtered["User_ID"].nunique()
    adoption = adoption_table(filtered)
    products_analyzed = adoption["Product"].nunique()
    avg_sat = filtered["Satisfaction_Score"].mean()
    avg_products = filtered["Product_Count"].mean()
    top_product = adoption.iloc[0]["Product"] if not adoption.empty else "N/A"
    overall_adoption = adoption["Adoption_Rate"].mean() if not adoption.empty else 0

    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("Total Users", f"{total_users:,}")
    c2.metric("Products Analyzed", products_analyzed)
    c3.metric("Avg Satisfaction", f"{avg_sat:.2f}/5" if pd.notna(avg_sat) else "N/A")
    c4.metric("Avg Products/User", f"{avg_products:.2f}")
    c5.metric("Most Used Product", top_product)
    c6.metric("Avg Product Adoption", f"{overall_adoption:.1f}%")

    st.caption(f"Current filtered sample size: N = {total_users:,}")

    col1, col2 = st.columns(2)
    with col1:
        if not adoption.empty:
            fig = px.bar(
                adoption.sort_values("Users"),
                x="Users", y="Product", orientation="h",
                title="Product Adoption Ranking",
                text="Users"
            )
            fig.update_layout(yaxis_title="", xaxis_title="Unique Users")
            st.plotly_chart(fig, use_container_width=True)

    with col2:
        freq = filtered["Usage_Frequency"].value_counts().reset_index()
        freq.columns = ["Usage_Frequency", "Users"]
        fig = px.pie(freq, names="Usage_Frequency", values="Users",
                     title="Usage Frequency Distribution", hole=.45)
        st.plotly_chart(fig, use_container_width=True)

    col3, col4 = st.columns(2)
    with col3:
        sat = filtered["Satisfaction_Score"].value_counts().sort_index().reset_index()
        sat.columns = ["Satisfaction_Score", "Users"]
        fig = px.bar(sat, x="Satisfaction_Score", y="Users",
                     title="Satisfaction Score Distribution")
        st.plotly_chart(fig, use_container_width=True)

    with col4:
        occ = filtered["Occupation"].value_counts().reset_index()
        occ.columns = ["Occupation", "Users"]
        fig = px.bar(occ, x="Occupation", y="Users",
                     title="Users by Occupation")
        fig.update_xaxes(tickangle=-30)
        st.plotly_chart(fig, use_container_width=True)

# ---------------- Data Quality ----------------
elif page == "Data Quality":
    st.subheader("Data Quality Center")

    duplicate_rows = int(data[REQUIRED_COLUMNS].duplicated().sum())
    duplicate_ids = int(data["User_ID"].duplicated().sum())
    missing_total = int(data[REQUIRED_COLUMNS].isna().sum().sum())
    missing_pct = missing_total / (len(data) * len(REQUIRED_COLUMNS)) * 100 if len(data) else 0
    invalid_sat = int((~data["Satisfaction_Score"].between(1, 5, inclusive="both")).sum())
    invalid_freq = int((~data["Usage_Frequency"].isin(["Daily", "Weekly", "Monthly"])).sum())
    unique_users = data["User_ID"].nunique()

    completeness = max(0, 100 - missing_pct)
    uniqueness = 100 if duplicate_rows == 0 and duplicate_ids == 0 else max(0, 100 - duplicate_ids / max(len(data), 1) * 100)
    validity = 100 if invalid_sat == 0 and invalid_freq == 0 else max(0, 100 - (invalid_sat + invalid_freq) / max(len(data), 1) * 100)
    consistency = 100 if data["Data_Source"].notna().all() else 95
    score = np.mean([completeness, uniqueness, validity, consistency])

    label = "Excellent" if score >= 95 else "Good" if score >= 85 else "Needs Attention" if score >= 70 else "Poor"

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Rows", f"{len(data):,}")
    c2.metric("Columns", len(data.columns))
    c3.metric("Unique Users", f"{unique_users:,}")
    c4.metric("Duplicate Rows", duplicate_rows)
    c5.metric("Quality Score", f"{score:.1f}%")

    st.progress(min(max(score / 100, 0), 1), text=f"Data Quality: {label}")

    quality_df = pd.DataFrame({
        "Check": ["Completeness", "Uniqueness", "Validity", "Consistency"],
        "Score": [completeness, uniqueness, validity, consistency]
    })
    fig = px.bar(quality_df, x="Check", y="Score", range_y=[0, 100],
                 title="Data Quality Dimensions", text_auto=".1f")
    st.plotly_chart(fig, use_container_width=True)

    issues = pd.DataFrame({
        "Issue": [
            "Missing values",
            "Duplicate rows",
            "Duplicate User_IDs",
            "Invalid satisfaction scores",
            "Invalid usage frequency values"
        ],
        "Count": [
            missing_total, duplicate_rows, duplicate_ids, invalid_sat, invalid_freq
        ]
    })
    st.dataframe(issues, use_container_width=True, hide_index=True)

    with st.expander("Preview Raw Data"):
        st.dataframe(data[REQUIRED_COLUMNS].head(50), use_container_width=True, hide_index=True)

# ---------------- Product Analytics ----------------
elif page == "Product Analytics":
    st.subheader("Product Analytics")
    adoption = adoption_table(filtered)

    if adoption.empty:
        st.warning("No product data is available for the selected filters.")
        st.stop()

    selected_product = st.selectbox("Select a product", adoption["Product"].tolist())
    long = product_long(filtered)
    p_users = long[long["Product"] == selected_product].copy()

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Users", f"{p_users['User_ID'].nunique():,}")
    c2.metric("Adoption Rate", f"{safe_pct(p_users['User_ID'].nunique(), filtered['User_ID'].nunique()):.1f}%")
    c3.metric("Avg Satisfaction", f"{p_users['Satisfaction_Score'].mean():.2f}/5")
    top_freq = p_users["Usage_Frequency"].mode().iloc[0] if not p_users.empty else "N/A"
    c4.metric("Typical Frequency", top_freq)

    col1, col2 = st.columns(2)
    with col1:
        fig = px.bar(adoption.sort_values("Adoption_Rate"),
                     x="Adoption_Rate", y="Product", orientation="h",
                     title="Adoption Rate by Product", text="Adoption_Rate")
        fig.update_traces(texttemplate="%{text:.1f}%")
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        compare = st.multiselect(
            "Compare products (choose up to 2)",
            adoption["Product"].tolist(),
            default=adoption["Product"].head(2).tolist()
        )[:2]
        if compare:
            comp = adoption[adoption["Product"].isin(compare)]
            fig = px.bar(comp, x="Product", y="Adoption_Rate",
                         title="Product Comparison", text="Adoption_Rate")
            fig.update_traces(texttemplate="%{text:.1f}%")
            st.plotly_chart(fig, use_container_width=True)

    st.markdown("### Selected Product Profile")
    profile = pd.DataFrame({
        "Metric": [
            "Product", "Users", "Adoption Rate", "Average Satisfaction",
            "Most Common Usage Frequency"
        ],
        "Value": [
            selected_product,
            f"{p_users['User_ID'].nunique():,}",
            f"{safe_pct(p_users['User_ID'].nunique(), filtered['User_ID'].nunique()):.1f}%",
            f"{p_users['Satisfaction_Score'].mean():.2f}/5",
            top_freq
        ]
    })
    st.dataframe(profile, use_container_width=True, hide_index=True)

# ---------------- User Segmentation ----------------
elif page == "User Segmentation":
    st.subheader("User Segmentation")
    seg = filtered["User_Segment"].value_counts().reindex(
        ["Basic User", "Regular User", "Power User"], fill_value=0
    ).reset_index()
    seg.columns = ["Segment", "Users"]

    col1, col2 = st.columns(2)
    with col1:
        fig = px.pie(seg, names="Segment", values="Users",
                     title="User Segment Distribution", hole=.45)
        st.plotly_chart(fig, use_container_width=True)
    with col2:
        fig = px.bar(seg, x="Segment", y="Users",
                     title="Users by Segment", text="Users")
        st.plotly_chart(fig, use_container_width=True)

    summary = filtered.groupby("User_Segment", observed=False).agg(
        Users=("User_ID", "nunique"),
        Avg_Satisfaction=("Satisfaction_Score", "mean"),
        Avg_Products=("Product_Count", "mean")
    ).reset_index()
    summary["Share"] = summary["Users"] / max(filtered["User_ID"].nunique(), 1) * 100
    st.dataframe(summary, use_container_width=True, hide_index=True)

    col3, col4 = st.columns(2)
    with col3:
        age_seg = pd.crosstab(filtered["Age_Group"], filtered["User_Segment"])
        fig = px.imshow(age_seg, text_auto=True, aspect="auto",
                        title="Age Group × User Segment")
        st.plotly_chart(fig, use_container_width=True)
    with col4:
        occ_seg = pd.crosstab(filtered["Occupation"], filtered["User_Segment"])
        fig = px.imshow(occ_seg, text_auto=True, aspect="auto",
                        title="Occupation × User Segment")
        st.plotly_chart(fig, use_container_width=True)

# ---------------- Product Co-Usage ----------------
elif page == "Product Co-Usage":
    st.subheader("Product Co-Usage Analysis")
    pairs = co_usage(filtered)

    if pairs.empty:
        st.warning("Not enough product combinations to calculate co-usage.")
    else:
        st.markdown("Products frequently used by the same users can reveal ecosystem relationships.")
        st.dataframe(pairs.head(20), use_container_width=True, hide_index=True)

        top = pairs.head(10).copy()
        top["Pair"] = top["Product_A"] + " + " + top["Product_B"]
        fig = px.bar(top.sort_values("Shared_Users"),
                     x="Shared_Users", y="Pair", orientation="h",
                     title="Top 10 Product Pairs by Shared Users",
                     text="Shared_Users")
        st.plotly_chart(fig, use_container_width=True)

        selected = st.selectbox("Explore relationships for a product", PRODUCTS)
        related = pairs[(pairs["Product_A"] == selected) | (pairs["Product_B"] == selected)].copy()
        if not related.empty:
            related["Related_Product"] = np.where(
                related["Product_A"] == selected,
                related["Product_B"],
                related["Product_A"]
            )
            related = related[["Related_Product", "Shared_Users"]].sort_values("Shared_Users", ascending=False)
            fig = px.bar(related.head(10).sort_values("Shared_Users"),
                         x="Shared_Users", y="Related_Product", orientation="h",
                         title=f"Products Commonly Used With {selected}")
            st.plotly_chart(fig, use_container_width=True)

# ---------------- Automated Insights ----------------
elif page == "Automated Insights":
    st.subheader("Automated Data-Driven Insights")
    adoption = adoption_table(filtered)
    total_users = filtered["User_ID"].nunique()

    insights = []

    if not adoption.empty:
        top = adoption.iloc[0]
        low = adoption.iloc[-1]
        insights.append((
            "Highest adoption",
            f"{top['Product']} is the most adopted product in the current sample.",
            f"{top['Users']:,} unique users ({top['Adoption_Rate']:.1f}% adoption)."
        ))
        insights.append((
            "Lowest adoption",
            f"{low['Product']} has the lowest adoption among the analyzed products.",
            f"{low['Users']:,} unique users ({low['Adoption_Rate']:.1f}% adoption)."
        ))

    avg_sat = filtered["Satisfaction_Score"].mean()
    if pd.notna(avg_sat):
        insights.append((
            "Overall satisfaction",
            "The average satisfaction score provides a high-level view of user sentiment.",
            f"Average satisfaction is {avg_sat:.2f} out of 5 across N={total_users:,} users."
        ))

    if not filtered["Non_Adoption_Reason"].dropna().empty:
        reason = filtered["Non_Adoption_Reason"].value_counts().idxmax()
        count = filtered["Non_Adoption_Reason"].value_counts().max()
        insights.append((
            "Top non-adoption reason",
            f'"{reason}" is the most frequently reported non-adoption reason.',
            f"{count:,} records ({safe_pct(count, len(filtered)):.1f}% of records)."
        ))

    pairs = co_usage(filtered)
    if not pairs.empty:
        p = pairs.iloc[0]
        insights.append((
            "Strongest product relationship",
            f"{p['Product_A']} and {p['Product_B']} are the most frequently co-used product pair.",
            f"They are used together by {p['Shared_Users']:,} users in the current sample."
        ))

    for title, finding, evidence in insights:
        st.markdown(
            f'<div class="insight-card"><b>{title}</b><br>{finding}<br>'
            f'<span class="small-note"><b>Evidence:</b> {evidence}</span></div>',
            unsafe_allow_html=True
        )

# ---------------- Ask Your Data ----------------
elif page == "Ask Your Data":
    st.subheader("Ask Your Data")
    st.caption("Rule-based analytics assistant: answers are calculated from the currently filtered dataset.")

    question = st.text_input(
        "Ask a question",
        placeholder="Example: Which product has the highest adoption?"
    )

    if question:
        q = question.lower().strip()
        adoption = adoption_table(filtered)
        total_users = filtered["User_ID"].nunique()

        answer = None
        explanation = None
        chart_data = None

        if ("highest" in q or "most" in q) and "adoption" in q and not adoption.empty:
            r = adoption.iloc[0]
            answer = f"{r['Product']} has the highest adoption rate at {r['Adoption_Rate']:.1f}%."
            explanation = f"{r['Users']:,} of {total_users:,} unique users use {r['Product']}."

        elif ("lowest" in q or "least" in q) and "adoption" in q and not adoption.empty:
            r = adoption.iloc[-1]
            answer = f"{r['Product']} has the lowest adoption rate at {r['Adoption_Rate']:.1f}%."
            explanation = f"{r['Users']:,} of {total_users:,} unique users use {r['Product']}."

        elif "average satisfaction" in q or "satisfaction score" in q:
            value = filtered["Satisfaction_Score"].mean()
            answer = f"The average satisfaction score is {value:.2f} out of 5."
            explanation = f"Calculated as the mean Satisfaction_Score across N={total_users:,} users."

        elif "most common" in q and "frequency" in q:
            mode = filtered["Usage_Frequency"].mode().iloc[0]
            count = (filtered["Usage_Frequency"] == mode).sum()
            answer = f"{mode} is the most common usage frequency."
            explanation = f"{count:,} records ({safe_pct(count, len(filtered)):.1f}%) are marked {mode}."

        elif "occupation" in q and ("most" in q or "highest" in q):
            counts = filtered.groupby("Occupation")["Product_Count"].mean().sort_values(ascending=False)
            if not counts.empty:
                occ = counts.index[0]
                answer = f"{occ} has the highest average number of Google products used per user."
                explanation = f"The average is {counts.iloc[0]:.2f} products per user."

        elif "why" in q and ("not" in q or "don't" in q or "non" in q):
            counts = filtered["Non_Adoption_Reason"].value_counts()
            if not counts.empty:
                reason = counts.index[0]
                answer = f'The most common reported non-adoption reason is "{reason}".'
                explanation = f"It appears in {counts.iloc[0]:,} records."

        elif "compare" in q:
            mentioned = [p for p in PRODUCTS if p.lower() in q]
            if len(mentioned) >= 2:
                a, b = mentioned[:2]
                rates = adoption.set_index("Product")["Adoption_Rate"]
                answer = f"{a} adoption is {rates.get(a, 0):.1f}%, while {b} adoption is {rates.get(b, 0):.1f}%."
                explanation = f"The comparison uses unique users divided by total unique users (N={total_users:,})."
            else:
                answer = "Please mention two Google products to compare."
                explanation = "Example: Compare Gmail and Google Drive."

        elif "together" in q or "co-used" in q or "co usage" in q or "commonly used" in q:
            pairs = co_usage(filtered)
            if not pairs.empty:
                p = pairs.iloc[0]
                answer = f"The most common product pair is {p['Product_A']} + {p['Product_B']}."
                explanation = f"They are used together by {p['Shared_Users']:,} users."
            else:
                answer = "There is not enough data to calculate product co-usage."
                explanation = "The dataset needs users with multiple products."

        else:
            answer = "I don't have enough data or a supported rule to answer that question."
            explanation = "Try asking about adoption, satisfaction, usage frequency, occupation, non-adoption reasons, comparisons, or co-usage."

        st.success(answer)
        st.write(explanation)

# ---------------- Footer ----------------
st.sidebar.divider()
st.sidebar.caption("Portfolio project • Synthetic/user survey data • Not affiliated with Google")
