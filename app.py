import streamlit as st
import pandas as pd
import google.generativeai as genai
import json
from io import BytesIO
from google.api_core import client_options
import os

# --- SETUP & CONFIG ---
st.set_page_config(page_title="Global Logistics Hub", layout="wide")
st.title("🌍 Global Logistics & Courier Report Generator")

# We will securely inject the API key via Ploomber later, but for local testing:
API_KEY = os.environ.get("GEMINI_API_KEY", "AIzaSyBk4fI_lJ6Uju2GTT5K1l1w1YEpqTwvTHk")

if API_KEY and API_KEY != "PASTE_YOUR_NEW_KEY_HERE":
    # The 'Sledgehammer' fix to force v1 API and prevent 404 errors
    c_options = client_options.ClientOptions(api_endpoint="generativelanguage.googleapis.com")
    genai.configure(api_key=API_KEY, client_options=c_options)
    model = genai.GenerativeModel('gemini-1.5-flash')
else:
    st.warning("Please paste your API Key into the code to begin.")
    st.stop()

# Memory for the "Grand Report"
if 'grand_report' not in st.session_state:
    st.session_state.grand_report = []

# --- UPLOAD SECTION ---
st.subheader("1. Upload Invoices")
uploaded_files = st.file_uploader("Drop DHL, FedEx, UPS PDFs here", type="pdf", accept_multiple_files=True)

if st.button("Process All Invoices") and uploaded_files:
    with st.spinner("Extracting and categorizing market data..."):
        for file in uploaded_files:
            try:
                pdf_data = {"mime_type": "application/pdf", "data": file.getvalue()}
                
                # Upgraded Prompt for Grand Reporting
                prompt = """
                Analyze this shipping invoice. Extract the following details into a clean JSON object.
                Format strictly like this:
                {
                    "Courier": "string (e.g., DHL, UPS, FedEx)",
                    "Tracking Number": "string",
                    "Destination Market": "string (e.g., USA, Germany, Asia)",
                    "Market Cost": number (numeric value only, no currency symbols),
                    "Weight": "string",
                    "Date": "string"
                }
                Return ONLY the JSON. No other text.
                """
                response = model.generate_content([prompt, pdf_data])
                
                # Bulletproof JSON Cleaning
                clean_json = response.text.replace("```json", "").replace("
```", "").strip()
                data = json.loads(clean_json)
                
                st.session_state.grand_report.append(data)
                st.success(f"✅ Processed: {file.name}")
                
            except Exception as e:
                st.error(f"❌ Failed to process {file.name}: {str(e)}")

# --- GRAND REPORT & EXPORT ---
st.subheader("2. Grand Report")
if st.session_state.grand_report:
    # Convert data to Pandas DataFrame
    df = pd.DataFrame(st.session_state.grand_report)
    
    # Show the table on screen
    st.dataframe(df, use_container_width=True)
    
    # Package it into an Excel File
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name="Combined Couriers")
        
    # Download Button
    st.download_button(
        label="📥 Download Master Excel Report",
        data=output.getvalue(),
        file_name="Master_Courier_Report.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    
    if st.button("Clear Report (Start Over)"):
        st.session_state.grand_report = []
        st.rerun()
else:
    st.info("Upload invoices to start building the grand report.")
