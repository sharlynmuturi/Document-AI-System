import streamlit as st
import pandas as pd
from pathlib import Path

from scripts.query_engine import ask_document_ai

st.set_page_config(page_title="Document AI Review Dashboard", layout="wide")
st.title("Document AI Review Dashboard")

BASE_DIR = Path(__file__).parent
PROCESSED_DIR = BASE_DIR / "data" / "processed"

LOW_CONF_THRESHOLD = 0.8


# Detect available document types
def get_doc_types():
    types = []
    for folder in PROCESSED_DIR.iterdir():
        if folder.is_dir():
            types.append(folder.name)
    return types


doc_types = get_doc_types()

if not doc_types:
    st.error("No processed document types found.")
    st.stop()


# Sidebar
st.sidebar.header("Document Type")

selected_type = st.sidebar.selectbox(
    "Select document type",
    doc_types
)

excel_path = PROCESSED_DIR / selected_type / f"processed_{selected_type}.xlsx"


# Load excel
@st.cache_data
def load_excel(path):

    if not path.exists():
        return pd.DataFrame()

    xls = pd.ExcelFile(path)

    data = pd.concat(
        [xls.parse(sheet).assign(field_name=sheet) for sheet in xls.sheet_names]
    )

    data.reset_index(drop=True, inplace=True)

    return data


df_all = load_excel(excel_path)

if df_all.empty:
    st.warning(f"No processed data found for {selected_type}")
    st.stop()


# Document selection
st.sidebar.header("Document Selection")

doc_options = df_all["filename"].unique()

selected_doc = st.sidebar.selectbox(
    "Select Document",
    ["All"] + list(doc_options)
)

if selected_doc != "All":
    df_doc = df_all[df_all["filename"] == selected_doc]
else:
    df_doc = df_all.copy()


# Confidence highlight
def highlight_confidence(row):

    color = "#FFCCCC" if row.get("confidence", 1.0) < LOW_CONF_THRESHOLD else "#FFFFFF"

    return ["background-color: {}".format(color)] * len(row)


# Confidence summary
st.subheader("Confidence Summary")

avg_conf = df_doc["confidence"].mean()
low_conf_count = (df_doc["confidence"] < LOW_CONF_THRESHOLD).sum()

st.write(f"Average confidence: {avg_conf:.2f}")
st.write(f"Fields below threshold ({LOW_CONF_THRESHOLD}): {low_conf_count}")


# Low confidence fields
st.subheader("Low Confidence Fields")

low_conf_df = df_doc[df_doc["confidence"] < LOW_CONF_THRESHOLD]

if low_conf_df.empty:
    st.success("No low-confidence fields!")
else:
    st.dataframe(
        low_conf_df[
            ["filename", "field_name", "field_value", "confidence", "source"]
        ],
        use_container_width=True
    )
    
st.markdown("---")

# Display fields
st.subheader(
    f"{selected_type.title()} Fields for: {selected_doc}"
    if selected_doc != "All"
    else f"All {selected_type.title()} Documents"
)

st.write(f"Total records: {len(df_doc)}")

st.dataframe(
    df_doc[
        ["filename", "field_name", "field_value", "confidence", "source"]
    ].style.apply(highlight_confidence, axis=1),
    use_container_width=True
)




# RAG QUESTION INTERFACE
st.header(f"Ask Questions About {selected_type.title()} Documents")

question = st.text_input(
    "Ask a question:",
    placeholder="Example: How many documents are recorded?"
)


if st.button("Ask LLM"):

    if question.strip() == "":
        st.warning("Please enter a question.")

    else:

        with st.spinner("Searching documents and generating answer..."):

            try:

                answer = ask_document_ai(
                    question,
                    doc_type=selected_type
                )

                st.success("Answer")
                st.write(answer)

            except Exception as e:

                st.error("Error running RAG pipeline")
                st.write(str(e))