import streamlit as st
import pandas as pd
import math
import re

st.set_page_config(page_title="Majestic + Ahrefs Winter Sports Filter", layout="wide")

st.title("Majestic + Ahrefs CSV Merge: Sports/Winter Sports")

st.write(
    "Step 1: Upload a **Majestic** CSV and extract any Topical Trust Flow entries where "
    "**TopicalTrustFlow_Topic contains 'Sports/Winter Sports'**.\n\n"
    "Step 2: Upload an **Ahrefs Batch Analysis** CSV and append Ahrefs metrics for matching domains."
)

# -----------------------------
# Upload inputs
# -----------------------------
majestic_file = st.file_uploader("1) Upload Majestic CSV", type=["csv"], key="majestic")
ahrefs_file = st.file_uploader("2) Upload Ahrefs Batch Analysis CSV", type=["csv"], key="ahrefs")

topic_search = st.text_input("Topic contains:", value="Sports/Winter Sports")
case_sensitive = st.checkbox("Case sensitive topic match", value=False)

# -----------------------------
# Helpers
# -----------------------------
def normalize_domain(x):
    """Convert URLs/domains to clean root domains for matching."""
    if pd.isna(x):
        return None
    x = str(x).strip().lower()

    # remove protocol
    x = re.sub(r"^https?://", "", x)

    # remove www
    x = re.sub(r"^www\.", "", x)

    # remove everything after first /
    x = x.split("/")[0]

    # remove trailing dots/spaces
    x = x.strip(" .")

    return x if x else None


def safe_divide(n, d):
    try:
        n = float(n)
        d = float(d)
        if d == 0:
            return None
        return n / d
    except:
        return None


def round_up(x):
    if x is None:
        return None
    try:
        return int(math.ceil(x))
    except:
        return None


# -----------------------------
# Main logic
# -----------------------------
if majestic_file:
    majestic_df = pd.read_csv(majestic_file)

    # Validate Majestic columns
    topic_cols = [f"TopicalTrustFlow_Topic_{i}" for i in range(10)]
    value_cols = [f"TopicalTrustFlow_Value_{i}" for i in range(10)]

    missing_majestics = [c for c in ["Item"] + topic_cols + value_cols if c not in majestic_df.columns]
    if missing_majestics:
        st.error("Majestic CSV is missing expected columns:\n\n" + "\n".join(missing_majestics))
        st.stop()

    # Extract matching topical trust flow rows
    matches = []

    for i, (tcol, vcol) in enumerate(zip(topic_cols, value_cols)):
        topics = majestic_df[tcol].astype(str)

        if case_sensitive:
            mask = topics.str.contains(topic_search, na=False)
        else:
            mask = topics.str.contains(topic_search, na=False, case=False)

        if mask.any():
            tmp = majestic_df.loc[mask, ["Item", tcol, vcol]].copy()
            tmp.rename(columns={tcol: "TopicalTrustFlow_Topic", vcol: "TopicalTrustFlow_Value"}, inplace=True)
            tmp["Topic_Index"] = i
            matches.append(tmp)

    if not matches:
        st.warning("No matches found for that topic string in Majestic.")
        st.stop()

    majestic_out = pd.concat(matches, ignore_index=True)

    # Add cleaned domain for merging
    majestic_out["Item_clean"] = majestic_out["Item"].apply(normalize_domain)

    st.success(f"Majestic: Found {len(majestic_out):,} matching topical trust flow entries.")
    st.subheader("Majestic Filter Output")
    st.dataframe(majestic_out.drop(columns=["Item_clean"]), use_container_width=True)

    # If Ahrefs file uploaded, merge it
    if ahrefs_file:
        ahrefs_df = pd.read_csv(ahrefs_file)

        # Exact Ahrefs column names from your export
        required_cols = [
            "Target",
            "Domain Rating",
            "Organic / Total Keywords",
            "Organic / Traffic",
            "Organic / Top Countries",
            "Ref. domains / Followed",
            "Outgoing domains / Followed",
        ]

        missing_ahrefs = [c for c in required_cols if c not in ahrefs_df.columns]
        if missing_ahrefs:
            st.error(
                "Ahrefs CSV is missing expected columns:\n\n"
                + "\n".join(missing_ahrefs)
                + "\n\nTip: Make sure you're uploading the correct Ahrefs Batch Analysis export."
            )
            st.stop()

        # Keep only needed columns
        ahrefs_small = ahrefs_df[required_cols].copy()

        # Add cleaned domain for merging
        ahrefs_small["Target_clean"] = ahrefs_small["Target"].apply(normalize_domain)

        # Deduplicate by cleaned domain
        ahrefs_small = ahrefs_small.drop_duplicates(subset=["Target_clean"])

        # Merge on cleaned domain
        merged = majestic_out.merge(
            ahrefs_small,
            how="left",
            left_on="Item_clean",
            right_on="Target_clean"
        )

        # Rename to your preferred output names
        merged.rename(columns={
            "Organic / Total Keywords": "Organic Total Keywords",
            "Orga
