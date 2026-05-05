import streamlit as st
import google.generativeai as genai
import os
import pandas as pd

# 1. Page Config & Styling
st.set_page_config(page_title="Global Logistics Hub", layout="wide", page_icon="📦")

# Custom CSS for a professional "Dark Mode" look
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .stMetric { background-color: #1f2937; padding: 15px; border-radius: 10px; border: 1px solid #374151; }
    </style>
""", unsafe_allow_html=True)

# 2. Setup API
api_key = os.environ.get("GEMINI_API_KEY")
genai.configure(api_key=api_key)
model = genai.GenerativeModel('gemini-1.5-flash') # Using Flash for speed

# 3. Sidebar for Navigation
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2830/2830312.png", width=100)
    st.title("Control Tower")
    mode = st.radio("Select View", ["Instant Analysis", "Fleet Overview", "Settings"])
    st.divider()
    st.info("Status: System Online (Render-Host)")

# 4. Main Interface
st.title("📦 Global Logistics & Courier Hub")

if mode == "Instant Analysis":
    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader("Data Input")
        tracking_input = st.text_area("Paste Tracking Details, Waybills, or Logistics Logs", height=150)
        uploaded_file = st.file_uploader("Or Upload Document (PDF, Image, Excel)", type=['pdf', 'png', 'jpg', 'xlsx'])

    with col2:
        st.subheader("Quick Actions")
        analysis_type = st.selectbox("Analysis Depth", ["Standard Summary", "Deep Risk Audit", "Tax & Duty Estimate"])
        run_btn = st.button("Generate Intelligence Report", use_container_width=True, type="primary")

    if run_btn:
        if tracking_input or uploaded_file:
            with st.spinner("Analyzing Global Data Streams..."):
                # Constructing the AI Prompt
                full_prompt = f"Perform a {analysis_type} on the following logistics data: {tracking_input}. Format as a professional business report with sections for Status, Risk, and Next Steps."
                
                try:
                    # In a real scenario, we'd handle the file bytes here too
                    response = model.generate_content(full_prompt)
                    
                    st.divider()
                    st.success("Analysis Complete")
                    
                    # Layout results in a clean way
                    st.markdown(response.text)
                    
                except Exception as e:
                    st.error(f"Analysis failed: {e}")
        else:
            st.warning("Please provide data or a file to analyze.")

elif mode == "Fleet Overview":
    st.subheader("Live Shipment Tracking (Simulation)")
    # Example table
    df = pd.DataFrame({
        'Courier': ['DHL', 'FedEx', 'UPS'],
        'Status': ['In Transit', 'Delayed', 'Delivered'],
        'ETA': ['2 hours', '1 day', 'Completed']
    })
    st.table(df)
