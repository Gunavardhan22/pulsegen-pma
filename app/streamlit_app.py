import streamlit as st
import json
import pandas as pd
import sys
import os
import time

# Add project root to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.crawler import run_crawler
from app.module_inference import ModuleInference
from app.summarizer import Summarizer
from app.utils import setup_logger

st.set_page_config(page_title="Doc Module Extractor", layout="wide")

st.title("📚 AI-Powered Documentation Module Extractor")
st.markdown("""
This tool recursively crawls documentation URLs, infers their structure (Modules & Submodules), 
and uses AI (or heuristics) to generate descriptions.
""")

# Sidebar settings
st.sidebar.header("Configuration")
url_input = st.sidebar.text_input("Documentation URL", "https://docs.python.org/3/")
max_depth = st.sidebar.slider("Crawling Depth", 1, 5, 2)
use_ai = st.sidebar.checkbox("Use AI Summarization", value=False, help="Uses a Transformer model. Slower but better quality.")

if st.sidebar.button("Start Extraction"):
    if not url_input:
        st.error("Please enter a URL.")
    else:
        status_container = st.container()
        
        with st.spinner("Initializing..."):
            logger = setup_logger()
            start_urls = [url_input.strip()]
            
        # 1. Crawling
        with status_container:
            st.info("Crawling documentation...")
            progress_bar = st.progress(0)
            
            # We can't easily hook into the loop for real-time progress without callback changes,
            # so we'll just show spinner.
            crawled_data = run_crawler(start_urls, max_depth=max_depth)
            progress_bar.progress(33)
            
        if not crawled_data:
            st.error("No pages found. Check the URL and domain restrictions.")
        else:
            st.success(f"Crawled {len(crawled_data)} pages.")
            
            # 2. Inference
            with status_container:
                st.info("Inferring Module Structure...")
                inference_engine = ModuleInference(start_urls)
                structure = inference_engine.infer_structure(crawled_data)
                progress_bar.progress(66)
            
            # 3. Summarization
            with status_container:
                st.info("Generating Descriptions...")
                summarizer = Summarizer(use_ai=use_ai)
                final_output = []

                for module_name, module_data in structure.items():
                    module_entry = {
                        "module": module_name,
                        "Description": "",
                        "Submodules": {}
                    }
                    
                    if module_data["pages"]:
                        all_content = []
                        for p in module_data["pages"]:
                            all_content.extend(p["content"])
                        module_entry["Description"] = summarizer.generate_description(all_content)
                    else:
                        module_entry["Description"] = "Container module."

                    for sub_name, sub_data in module_data.get("submodules", {}).items():
                        sub_content = []
                        for p in sub_data["pages"]:
                            sub_content.extend(p["content"])
                        
                        sub_desc = summarizer.generate_description(sub_content)
                        module_entry["Submodules"][sub_name] = sub_desc
                        
                    final_output.append(module_entry)
                
                progress_bar.progress(100)

            # Display Results
            st.header("Extraction Results")
            
            # Tab view
            tab1, tab2 = st.tabs(["JSON Output", "Interactive View"])
            
            with tab1:
                st.json(final_output)
                
                json_str = json.dumps(final_output, indent=2, ensure_ascii=False)
                st.download_button(
                    label="Download JSON",
                    data=json_str,
                    file_name="documentation_modules.json",
                    mime="application/json"
                )
            
            with tab2:
                for item in final_output:
                    with st.expander(f"📦 {item['module']}"):
                        st.markdown(f"**Description:** {item['Description']}")
                        if item['Submodules']:
                            st.divider()
                            st.markdown("### Submodules")
                            for sub_name, sub_desc in item['Submodules'].items():
                                st.markdown(f"**🔹 {sub_name}**")
                                st.caption(sub_desc)

