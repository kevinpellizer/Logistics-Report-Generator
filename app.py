import streamlit as st
import google.generativeai as genai
import json
import os

# 1. Page Configuration
st.set_page_config(page_title="Logistics Hub", layout="wide")

# 2. Setup API Key from Render Environment Variables
api_key = os.environ.get("GEMINI_API_KEY")

if not api_key:
    st.error("API Key not found. Please add GEMINI_API_KEY to Render Environment Variables.")
    st.stop()

genai.configure(api_key=api_key)
model = genai.GenerativeModel('gemini-pro')

# 3. App Interface
st.title("📦 Global Logistics & Courier Hub")
st.write("Enter a tracking ID or logistics data to generate a smart report.")

tracking_id = st.text_input("Logistics Data / Tracking ID", placeholder="e.g. 1Z999AA10123456784")

if st.button("Generate Intelligence Report"):
    if tracking_id:
        with st.spinner("Gemini AI is analyzing logistics patterns..."):
            try:
                # Simple prompt for stability
                prompt = f"Analyze this logistics data: {tracking_id}. Provide a detailed status, estimated delivery, and potential risks in a clean format."
                response = model.generate_content(prompt)
                
                # Display the result clearly
                st.subheader("Analysis Results")
                st.markdown(response.text)
                
            except Exception as e:
                st.error(f"An error occurred: {e}")
    else:
        st.warning("Please enter some data first.")
