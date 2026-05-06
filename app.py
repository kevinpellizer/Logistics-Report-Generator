import streamlit as st
import google.generativeai as genai
import os
import pandas as pd
import json
from io import BytesIO

# 1. Setup
st.set_page_config(page_title="Multi-Invoice Auditor", layout="wide", page_icon="📊")
api_key = os.environ.get("GEMINI_API_KEY")
genai.configure(api_key=api_key)
model = genai.GenerativeModel('gemini-3-flash-preview')

st.title("📊 Multi-Invoice Financial Auditor")

# 2. Multiple File Upload
uploaded_files = st.file_uploader("Upload DHL Invoices (Multiple allowed)", type=['pdf', 'png', 'jpg'], accept_multiple_files=True)

if uploaded_files:
    if st.button(f"Analyze {len(uploaded_files)} Invoices", type="primary"):
        all_shipments = []
        total_reported_net = 0.0
        
        progress_bar = st.progress(0)
        
        for i, uploaded_file in enumerate(uploaded_files):
            with st.spinner(f"Processing: {uploaded_file.name}..."):
                try:
                    p = "Extract every shipment. Keys: 'tracking_nr', 'country', 'cost'. "
                    p += "Also find 'invoice_net_total'. Return ONLY JSON."
                    
                    fb = uploaded_file.getvalue()
                    response = model.generate_content([p, {"mime_type": uploaded_file.type, "data": fb}])
                    
                    # Clean & Parse
                    raw = response.text.replace("```json", "").replace("```", "").strip()
                    data = json.loads(raw)
                    
                    # Store data
                    shipments = data.get('shipments', [])
                    for s in shipments:
                        s['source_file'] = uploaded_file.name # Keep track of which file it came from
                    
                    all_shipments.extend(shipments)
                    total_reported_net += float(data.get('invoice_net_total', 0))
                    
                except Exception as e:
                    st.error(f"Error in {uploaded_file.name}: {e}")
            
            progress_bar.progress((i + 1) / len(uploaded_files))

        if all_shipments:
            df = pd.DataFrame(all_shipments)
            df.columns = [c.lower() for c in df.columns]

            # Grouping
            summary = df.groupby('country')['cost'].sum().reset_index()
            
            # --- NEW: Transpose for the Excel layout you want (Row 1: Country, Row 2: Cost) ---
            transposed_summary = summary.set_index('country').T

            st.subheader("🌍 Combined Results by Country")
            st.table(summary)
            
            calc_sum = df['cost'].sum()
            st.metric("Total Calculated (All Files)", f"€{calc_sum:,.2f}")
            st.metric("Total Reported on Invoices", f"€{total_reported_net:,.2f}")

            # 3. Excel Download Logic
            out = BytesIO()
            with pd.ExcelWriter(out, engine='openpyxl') as writer:
                # Sheet 1: Raw Data
                df.to_excel(writer, index=False, sheet_name='All_Shipments')
                # Sheet 2: Your specific Row 1 (Country) / Row 2 (Cost) layout
                transposed_summary.to_excel(writer, sheet_name='Country_Summary')
            
            st.divider()
            st.download_button(
                label="📥 Download Consolidated Excel Report",
                data=out.getvalue(),
                file_name="consolidated_audit_report.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
