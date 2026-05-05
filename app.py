import streamlit as st
import google.generativeai as genai
import os

# 1. Page Configuration
st.set_page_config(page_title="Global Logistics Hub", layout="wide", page_icon="📦")

# 2. Setup API
api_key = os.environ.get("GEMINI_API_KEY")
genai.configure(api_key=api_key)

# The missing "-preview" was the culprit!
# If this still errors, change it to 'gemini-2.5-flash' (the stable version).
model = genai.GenerativeModel('gemini-3-flash-preview')

# 3. Sidebar
with st.sidebar:
    st.title("Control Tower")
    st.info("System Online: Render-Host")
    st.divider()
    st.write("Using Gemini 3 Flash Preview (May 2026 release).")

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
        with st.spinner("Gemini 3 is analyzing your document..."):
            try:
                # We build the request as a list of parts
                prompt_text = f"Perform a {analysis_type}. Logistics data provided: {tracking_input}"
                request_content = [prompt_text]
                
                if uploaded_file:
                    # We use .getvalue() to get the clean data for the API
                    file_bytes = uploaded_file.getvalue()
                    request_content.append({
                        "mime_type": uploaded_file.type,
                        "data": file_bytes
                    })
                
                # Generate response
                response = model.generate_content(request_content)
                
                st.divider()
                st.success("Analysis Complete")
                st.markdown(response.text)
                
            except Exception as e:
                # This will tell us if it's still a 404 or something else
                st.error(f"Analysis failed: {e}")
    else:
        st.warning("Please provide data or a file to analyze.")
