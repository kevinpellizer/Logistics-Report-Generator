import streamlit as st
import os

st.title("Project Status: ALIVE")
st.write("If you can see this, we have defeated the syntax errors.")

key_check = os.environ.get("GEMINI_API_KEY")
if key_check:
    st.success("API Key is connected and safe!")
else:
    st.error("API Key is missing from Render settings.")
