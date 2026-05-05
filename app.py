import streamlit as st
import google.generativeai as genai
import os
import pandas as pd
import json
from io import BytesIO

# 1. Setup
st.set_page_config(page_title="Logistics Financial Auditor", layout="wide", page_icon="📊")

# Setup API with the 2026 Gemini 3 Model
api_key = os.environ.get("GEMINI_API_KEY")
genai.configure(api_key=api_key)
model = genai.GenerativeModel('gemini-3-flash-preview')

st.title("📊 Logistics Financial Auditor (Gemini 3)")
st.write("Extracting line-by-line shipment data, grouping by country, and verifying totals.")

# 2. File Upload
uploaded_file = st.file_uploader("Upload Invoice (PDF or Image)", type=['pdf', 'png', 'jpg'])

if uploaded_file:
    if st.button("Run Full Audit & Generate Excel", type="primary"):
        with st.spinner("Gemini 3 is auditing every shipment line-item..."):
            try:
                # The "Auditor" Prompt
                prompt = """
                Extract EVERY individual shipment from this document. 
                For each shipment, find:
                1. Tracking Number
                2. Destination Country Code (e.g., DE, FR, ES, NL, BE, AT, HR, CH, RO, FI, SI)
                3. Net Cost (the price WITHOUT VAT)

                Also, find the 'Invoice Net Total' stated on the document (the sum of all shipments before VAT).

                Return the data ONLY as a JSON object with this exact structure:
                {
                  "shipments": [
                    {"tracking_nr": "XYZ123", "country": "DE", "cost": 10.50},
                    {"tracking_nr": "ABC456", "country": "FR", "cost": 12.00}
                  ],
                  "invoice_net_total": 22.50
                }
                """
                
                file_bytes = uploaded_file.getvalue()
                response = model.generate_content([
                    prompt, 
                    {"mime_type": uploaded_file.type, "data": file_bytes}
                ])
                
                # Bulletproof JSON Cleaning
                res_text = response.text
                if "```json" in res_text:
                    res_text = res_text.split("
```json")[1].split("```")[0]
                elif "```" in res_text:
                    res_text = res_text.split("```")[1].split("```")[0]
                
                data = json.loads(res_text.strip())
                
                # 3. The Math Engine (Pandas)
                df = pd.DataFrame(data['shipments'])
                
                # Group by Country: Sum Cost and Count Shipments
                summary = df.groupby('country').agg(
                    Total_Cost=('cost', 'sum'),
                    Shipment_Count=('cost', 'count')
                ).reset_index()

                # 4. Validation Math
                calculated_total = df['cost'].sum()
                reported_total = data.get('invoice_net_total', 0)

                # 5. Display Results
                st.divider()
                st.subheader("🌍 Country-Wise Breakdown")
                st.table(summary)

                col1, col2 = st.columns(2)
                col1.metric("Calculated Sum (Line Items)", f"€{calculated_total:,.2f}")
                col2.metric("Invoice Reported Net Total", f"€{reported_total:,.2f}")

                # Audit Validation
                if abs(calculated_total - reported_total) < 0.05:
                    st.success("✅ Audit Passed: The sum of individual shipments matches the Net Total.")
                else:
                    diff = abs(calculated_total - reported_total)
                    st.warning(f"⚠️ Audit Discrepancy: Difference of €{diff:,.2f} detected.")

                # 6. Excel Generation
                output = BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    df.to_excel(writer, index=False, sheet_name='All_Shipments')
                    summary.to_excel(writer, index=False, sheet_name='Country_Summary')
                
                st.download_button(
                    label="📥 Download Audit Report (.xlsx)",
                    data=output.getvalue(),
                    file_name="logistics_audit_report.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )

            except Exception as e:
                st.error(f"Audit failed: {e}")
                st.info("Try uploading the file again or check if the API key is active.")
