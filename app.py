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
st.write("Extracting shipments, grouping by country, and exporting to Excel.")

# 2. File Upload
uploaded_file = st.file_uploader("Upload Invoice", type=['pdf', 'png', 'jpg'])

if uploaded_file:
    if st.button("Run Full Audit", type="primary"):
        with st.spinner("Auditing..."):
            try:
                # The Prompt
                p = "Extract shipments line-by-line. Include: Tracking Nr, Country Code, and Net Cost. "
                p += "Also find the 'Invoice Net Total'. Return as JSON object with keys "
                p += "'shipments' (list of dicts) and 'invoice_net_total' (number)."
                
                fb = uploaded_file.getvalue()
                response = model.generate_content([p, {"mime_type": uploaded_file.type, "data": fb}])
                
                # CLEANING DATA - Broken into tiny lines to avoid Syntax Errors
                raw = response.text
                raw = raw.replace("```json", "")
                raw = raw.replace("```", "")
                raw = raw.strip()
                
                data = json.loads(raw)
                
                # 3. Processing
                df = pd.DataFrame(data['shipments'])
                
                # Grouping by Country
                summary = df.groupby('country').agg(
                    Total_Cost=('cost', 'sum'),
                    Count=('cost', 'count')
                ).reset_index()

                # 4. Totals
                calc_total = df['cost'].sum()
                rep_total = data.get('invoice_net_total', 0)

                # 5. Display
                st.subheader("Results by Country")
                st.table(summary)
                st.metric("Total Calculated", f"€{calc_total:,.2f}")
                st.metric("Total on Invoice", f"€{rep_total:,.2f}")

                # 6. Excel Download
                out = BytesIO()
                with pd.ExcelWriter(out, engine='openpyxl') as writer:
                    df.to_excel(writer, index=False, sheet_name='All_Shipments')
                    summary.to_excel(writer, index=False, sheet_name='Summary')
                
                st.download_button(
                    label="📥 Download Excel Report",
                    data=out.getvalue(),
                    file_name="audit_results.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

            except Exception as e:
                st.error(f"Error: {e}")
