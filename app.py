import streamlit as st
import google.generativeai as genai
import os
import pandas as pd
import json
import time  
from io import BytesIO

# 1. Setup
st.set_page_config(page_title="Multi-Invoice Auditor", layout="wide", page_icon="📊")
api_key = os.environ.get("GEMINI_API_KEY")
genai.configure(api_key=api_key)
model = genai.GenerativeModel('gemini-3-flash-preview')

st.title("📊 Multi-Invoice Financial Auditor")

# 2. Multiple File Upload
uploaded_files = st.file_uploader("Upload Courier Invoices (Multiple allowed)", type=['pdf', 'png', 'jpg'], accept_multiple_files=True)

if uploaded_files:
    if st.button(f"Analyze {len(uploaded_files)} Invoices", type="primary"):
        all_shipments = []
        total_reported_net = 0.0
        
        progress_bar = st.progress(0)
        
        for i, uploaded_file in enumerate(uploaded_files):
            with st.spinner(f"Processing: {uploaded_file.name}..."):
                try:
                   # --- THE NEW UNIVERSAL VAT-FREE PROMPT ---
                    p = "Extract every shipment line-by-line. Use ONLY these keys: 'tracking_nr', 'country', 'cost'. "
                    p += "The 'country' MUST be the 2-letter destination code. "
                    p += "CRITICAL FOR COST: The 'cost' MUST be the TOTAL NET AMOUNT for that specific shipment. "
                    p += "You must ADD the base shipping rate PLUS all surcharges (fuel, remote area, handling, tolls, etc.) for that row. "
                    p += "The invoice might be in English, Slovenian, German, or other languages. Understand the context of the columns. "
                    p += "STRICTLY EXCLUDE any VAT / DDV / Tax from your math. Give me only the final net cost per shipment. "
                    p += "Also find the total net invoice amount ('invoice_net_total'). Return as ONLY a JSON object."
                    
                    fb = uploaded_file.getvalue()
                    response = model.generate_content([p, {"mime_type": uploaded_file.type, "data": fb}])
                    
                    # Cleaning
                    raw = response.text.replace("```json", "").replace("```", "").strip()
                    data = json.loads(raw)
                    
                    shipments = data.get('shipments', [])
                    for s in shipments:
                        s['source_file'] = uploaded_file.name 
                    
                    all_shipments.extend(shipments)
                    total_reported_net += float(data.get('invoice_net_total', 0))
                    
                    # Anti-Spam Pause
                    if i < len(uploaded_files) - 1:
                        time.sleep(5) 
                        
                except Exception as e:
                    if "429" in str(e):
                        st.error(f"Google Rate Limit hit on {uploaded_file.name}. Too many files too fast.")
                    else:
                        st.error(f"Error on {uploaded_file.name}: {e}")
            
            progress_bar.progress((i + 1) / len(uploaded_files))

        # 3. Processing Combined Data
        if all_shipments:
            df = pd.DataFrame(all_shipments)
            df.columns = [c.lower() for c in df.columns]

            if 'country' in df.columns and 'cost' in df.columns:
                # Grouping
                summary = df.groupby('country')['cost'].sum().reset_index()
                transposed_summary = summary.set_index('country').T

                st.subheader("🌍 Combined Results (VAT Free)")
                st.table(summary)
                
                # --- NEW: THE MATH DOUBLE-CHECK ---
                calc_sum = df['cost'].sum()
                difference = abs(calc_sum - total_reported_net)
                
                col1, col2, col3 = st.columns(3)
                col1.metric("Calculated Sum (Shipments)", f"€{calc_sum:,.2f}")
                col2.metric("Reported Net Total (Invoice)", f"€{total_reported_net:,.2f}")
                
                if difference <= 0.10: # We allow a 10-cent difference for rounding math
                    col3.metric("Reconciliation", "✅ Match")
                    st.success("Audit verification passed! The individual shipments perfectly match the invoice total.")
                else:
                    col3.metric("Reconciliation", "⚠️ Discrepancy")
                    st.warning(f"Discrepancy of €{difference:,.2f} detected! The AI may have accidentally included VAT on a row, or a surcharge was misread. Please review the Excel export.")

                # Excel Logic
                out = BytesIO()
                with pd.ExcelWriter(out, engine='openpyxl') as writer:
                    df.to_excel(writer, index=False, sheet_name='All_Shipments')
                    transposed_summary.to_excel(writer, sheet_name='Country_Summary')
                
                st.divider()
                st.download_button(
                    label="📥 Download Verified Excel",
                    data=out.getvalue(),
                    file_name="verified_audit.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )
