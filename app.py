import streamlit as st
import google.generativeai as genai
import json
import os

# Setup
st.set_page_config(page_title="Logistics Hub", layout="wide")
genai.configure(api_key=os.environ["GEMINI_API_KEY"])
model = genai.GenerativeModel('gemini-pro')

st.title("📦 Global Logistics Hub")

# Minimal test logic to ensure it boots
tracking_id = st.text_input("Enter Tracking ID")

if st.button("Generate Report"):
    with st.spinner("Analyzing..."):
        prompt = f"Analyze logistics for ID: {tracking_id}. Return JSON format."
        response = model.generate_content(prompt)
        
        # This is the line that was breaking - written as simply as possible
        raw_text = response.text
        clean_json = raw_text.replace("```json", "").replace("
```", "").strip()
        
        try:
            data = json.loads(clean_json)
            st.json(data)
        except:
            st.write(raw_text)
