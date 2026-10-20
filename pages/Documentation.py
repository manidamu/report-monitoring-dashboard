import streamlit as st
import os

st.set_page_config(page_title="Documentation", page_icon="📖", layout="wide")

st.title("📖 System Documentation")

doc_choice = st.selectbox("Select Document:", ["Solution Design", "README"])

if doc_choice == "Solution Design":
    file_path = "SOLUTION_DESIGN.md"
else:
    file_path = "README.md"

if os.path.exists(file_path):
    with open(file_path, "r",encoding="utf-8") as f:
        content = f.read()
    st.markdown(content)
else:
    st.error(f"Could not find {file_path} in the repository root.")