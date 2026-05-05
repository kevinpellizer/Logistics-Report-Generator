import streamlit as st
import google.generativeai as genai
import os

# 1. Page Config
st.set_page_config(page_title="Global Logistics Hub", layout="wide", page_icon="📦")

# 2. Setup API - Using the Gemini 3 Flash model
api_key = os.environ.get("GEMINI_API_KEY")
genai.configure(api_key=api_key)

# We are using 'gemini-3-flash' which is the standard for 2026
model = genai.GenerativeModel('gemini-3-flash')

# 3. Sidebar
with st.sidebar:
    st.title("Control Tower")
    st.info("System Online: Render-Host")
    st.divider()
    st.write("This hub uses Gemini 3 AI to analyze logistics documents in real-time.")

# 4. Main Interface
st.title("📦 Global Logistics & Courier Hub")

col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("Data Input")
    tracking_input = st.text_area("Paste Tracking Details or Logs", height=100)
    uploaded_file = st.file_uploader("Upload Document (PDF or Image)", type=['pdf', 'png', 'jpg'])

with col2:
    st.subheader("Quick Actions")
    analysis_type = st.selectbox("Analysis Depth", ["Standard Summary", "Deep Risk Audit", "Tax & Duty Estimate"])
    run_btn = st.button("Generate Intelligence Report", use_container_width=True, type="primary")

if run_btn:
    if tracking_input or uploaded_file:
        with st.spinner("Gemini 3 is analyzing data streams..."):
            try:
                # Prepare the content list for the AI
                content_to_send = [f"Perform a {analysis_type}. Logistics data: {tracking_input}"]
                
                # If a file is uploaded, add it to the request
                if uploaded_file:
                    file_data = uploaded_file.read()
                    content_to_send.append({
                        "mime_type": uploaded_file.type,
                        "data": file_data
                    })
                
                # Generate response
                response = model.generate_content(content_to_send)
                
                st.divider()
                st.success("Analysis Complete")
                st.markdown(response.text)
                
            except Exception as e:
                st.error(f"Analysis failed: {e}")
    else:
        st.warning("Please provide a tracking ID or upload a file.")
