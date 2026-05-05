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
model = genai.GenerativeModel('gemini-1.5-flash') # Using 1.5-flash for high-speed data extraction

st.title("📊 Logistics Financial Auditor")
st.write("Upload your invoice to split costs by country and generate an Excel report.")

# 2. Input
uploaded_file = st.file_uploader("Upload Invoice (PDF or Image)", type=['pdf', 'png', 'jpg'])

if uploaded_file:
    if st.button("Analyze & Calculate Totals", type="primary"):
        with st.spinner("Processing every shipment line-by-line..."):
            try:
                # Instruction for the AI to be a data extractor
                prompt = """
                Extract every single shipment from this document. 
                For each shipment, identify:
                1. Tracking Number
                2. Destination Country Code (e.g., DE, US, GB)
                3. Net Cost (the price without VAT)

                Also, find the 'Invoice Net Total' (the sum of all shipments before VAT).

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
                
                # Clean and Parse JSON
                raw_text = response.text.replace("```json", "").replace("
```", "").strip()
                data = json.loads(raw_text)
                
                # 3. Processing with Pandas (The Math)
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
                st.subheader("Country-Wise Breakdown")
                st.table(summary)

                col1, col2 = st.columns(2)
                col1.metric("Calculated Net Total", f"${calculated_total:,.2f}")
                col2.metric("Invoice Reported Total", f"${reported_total:,.2f}")

                if round(calculated_total, 2) == round(reported_total, 2):
                    st.success("✅ Audit Passed: Calculated sum matches Invoice Net Total.")
                else:
                    st.warning("⚠️ Audit Discrepancy: The sum of line items differs from the reported total.")

                # 6. Excel Download Logic
                output = BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    df.to_sheet(writer, index=False, sheet_name='All_Shipments')
                    summary.to_sheet(writer, index=False, sheet_name='Country_Summary')
                
                st.download_button(
                    label="📥 Download Excel Report",
                    data=output.getvalue(),
                    file_name="logistics_audit_report.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

            except Exception as e:
                st.error(f"Error processing data: {e}")
                st.info("Check if the AI returned a non-JSON response. Try re-running.")
