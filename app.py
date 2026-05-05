import streamlit as st
import google.generativeai as genai
import os
import pandas as pd
import json
from io import BytesIO

# 1. Setup
st.set_page_config(page_title="Logistics Auditor", layout="wide", page_icon="📊")
api_key = os.environ.get("GEMINI_API_KEY")
genai.configure(api_key=api_key)
model = genai.GenerativeModel('gemini-3-flash-preview')

st.title("📊 Logistics Financial Auditor")

# 2. File Upload
uploaded_file = st.file_uploader("Upload Invoice", type=['pdf', 'png', 'jpg'])

if uploaded_file:
    if st.button("Run Full Audit", type="primary"):
        with st.spinner("Gemini 3 is extracting data..."):
            try:
                # Forceful Prompt
                p = "Extract every shipment. Use ONLY these keys: 'tracking_nr', 'country', 'cost'. "
                p += "The 'country' MUST be the 2-letter code (DE, FR, etc). "
                p += "Also find 'invoice_net_total'. Return as JSON."
                
                fb = uploaded_file.getvalue()
                response = model.generate_content([p, {"mime_type": uploaded_file.type, "data": fb}])
                
                # Cleaning
                raw = response.text.replace("```json", "").replace("```", "").strip()
                data = json.loads(raw)
                
                # Create DataFrame
                df = pd.DataFrame(data['shipments'])

                # --- NEW: SAFETY CHECK FOR COLUMNS ---
                if not df.empty:
                    # If AI used different capitalization, fix it
                    df.columns = [c.lower() for c in df.columns]
                    
                    if 'country' in df.columns and 'cost' in df.columns:
                        # Success - Do the math
                        summary = df.groupby('country').agg(
                            Total_Cost=('cost', 'sum'),
                            Count=('cost', 'count')
                        ).reset_index()

                        st.subheader("🌍 Results by Country")
                        st.table(summary)
                        
                        calc_total = df['cost'].sum()
                        rep_total = data.get('invoice_net_total', 0)
                        
                        col1, col2 = st.columns(2)
                        col1.metric("Calculated Sum", f"€{calc_total:,.2f}")
                        col2.metric("Invoice Net Total", f"€{rep_total:,.2f}")

                        # Excel Logic
                        out = BytesIO()
                        with pd.ExcelWriter(out, engine='openpyxl') as writer:
                            df.to_excel(writer, index=False, sheet_name='All_Shipments')
                            summary.to_excel(writer, index=False, sheet_name='Summary')
                        
                        st.download_button("📥 Download Excel Report", out.getvalue(), 
                                         "audit_report.xlsx", 
                                         "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
                    else:
                        st.error(f"Missing columns. AI found: {list(df.columns)}")
                        st.write("Raw data extracted:", df)
                else:
                    st.warning("AI didn't find any shipments in this document.")

            except Exception as e:
                st.error(f"Processing Error: {e}")
