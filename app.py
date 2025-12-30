import streamlit as st
import pandas as pd

st.set_page_config(page_title="Majestic Winter Sports Filter", layout="wide")

st.title("Majestic CSV Filter: Sports/Winter Sports")
st.write(
    "Upload a Majestic SEO CSV export and extract any Topical Trust Flow entries where "
    "**TopicalTrustFlow_Topic contains 'Sports/Winter Sports'**, along with its paired value."
)

uploaded_file = st.file_uploader("Upload Majestic CSV", type=["csv"])

topic_search = st.text_input("Topic contains:", value="Sports/Winter Sports")
case_sensitive = st.checkbox("Case sensitive", value=False)

if uploaded_file:
    df = pd.read_csv(uploaded_file)

    topic_cols = [f"TopicalTrustFlow_Topic_{i}" for i in range(10)]
    value_cols = [f"TopicalTrustFlow_Value_{i}" for i in range(10)]

    missing_cols = [c for c in topic_cols + value_cols if c not in df.columns]
    if missing_cols:
        st.error(
            "Your CSV is missing one or more expected Topical Trust Flow columns:\n\n"
            + "\n".join(missing_cols)
        )
        st.stop()

    matches = []

    for i, (tcol, vcol) in enumerate(zip(topic_cols, value_cols)):
        topics = df[tcol].astype(str)

        if case_sensitive:
            mask = topics.str.contains(topic_search, na=False)
        else:
            mask = topics.str.contains(topic_search, na=False, case=False)

        if mask.any():
            tmp = df.loc[mask, ["Item", tcol, vcol]].copy()
            tmp.rename(columns={tcol: "TopicalTrustFlow_Topic", vcol: "TopicalTrustFlow_Value"}, inplace=True)
            tmp["Topic_Index"] = i
            matches.append(tmp)

    if matches:
        out = pd.concat(matches, ignore_index=True)

        st.success(f"Found {len(out):,} matching topical trust flow entries.")
        st.dataframe(out, use_container_width=True)

        csv_data = out.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="Download Filtered CSV",
            data=csv_data,
            file_name="majestic_winter_sports_filtered.csv",
            mime="text/csv"
        )
    else:
        st.warning("No matches found for that topic string.")
else:
    st.info("Upload a CSV to get started.")
