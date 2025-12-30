import streamlit as st
import pandas as pd
import math

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
        st.error(
            "Majestic CSV is missing expected columns:\n\n" + "\n".join(missing_majestics)
        )
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

    st.success(f"Majestic: Found {len(majestic_out):,} matching topical trust flow entries.")
    st.subheader("Majestic Filter Output")
    st.dataframe(majestic_out, use_container_width=True)

    # If Ahrefs file is also uploaded, merge it
    if ahrefs_file:
        ahrefs_df = pd.read_csv(ahrefs_file)

        # Expected Ahrefs fields (by typical export headers)
        # We’ll try to match by column names, but if your export uses different naming,
        # you can rename columns in the mapping below.
        col_map = {
            "Target": "Target",
            "Domain Rating": "Domain Rating",
            "Organic Total Keywords": "Organic Total Keywords",
            "Organic Traffic": "Organic Traffic",
            "Organic Top Countries": "Organic Top Countries",
            "Ref. domains followed": "Ref. domains followed",
            "Outgoing domains Followed": "Outgoing domains Followed",
        }

        # Check required Ahrefs columns exist
        missing_ahrefs = [v for v in col_map.values() if v not in ahrefs_df.columns]
        if missing_ahrefs:
            st.error(
                "Ahrefs CSV is missing expected columns:\n\n"
                + "\n".join(missing_ahrefs)
                + "\n\nTip: Open your Ahrefs file and confirm column headers match exactly."
            )
            st.stop()

        # Keep only the necessary columns
        ahrefs_keep = list(col_map.values())
        ahrefs_small = ahrefs_df[ahrefs_keep].copy()

        # Deduplicate by Target (in case Ahrefs export has duplicates)
        ahrefs_small = ahrefs_small.drop_duplicates(subset=["Target"])

        # Merge: Majestic Item matches Ahrefs Target
        merged = majestic_out.merge(
            ahrefs_small,
            how="left",
            left_on="Item",
            right_on="Target"
        )

        # Remove Target column after merge (optional - you can keep it if you want)
        merged.drop(columns=["Target"], inplace=True)

        # Compute LD:RD ratio
        merged["LD:RD ratio"] = merged.apply(
            lambda row: round_up(
                safe_divide(row.get("Outgoing domains Followed"), row.get("Ref. domains followed"))
            ),
            axis=1
        )

        st.success("Ahrefs metrics appended successfully.")
        st.subheader("Merged Output (Majestic + Ahrefs)")
        st.dataframe(merged, use_container_width=True)

        # Download merged CSV
        merged_csv = merged.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="Download Merged CSV",
            data=merged_csv,
            file_name="majestic_winter_sports_with_ahrefs.csv",
            mime="text/csv"
        )

    else:
        st.info("Upload an Ahrefs Batch Analysis CSV to append Ahrefs metrics and calculate LD:RD ratio.")
else:
    st.info("Upload your Majestic CSV to get started.")
