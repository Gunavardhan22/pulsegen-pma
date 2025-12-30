import argparse
import json
import sys
import os
from typing import List

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.crawler import run_crawler
from app.module_inference import ModuleInference
from app.summarizer import Summarizer
from app.utils import setup_logger

logger = setup_logger()

def main():
    parser = argparse.ArgumentParser(description="AI-Powered Documentation Module Extractor")
    parser.add_argument("--url", required=True, help="Documentation URL to crawl (can be comma-separated)")
    parser.add_argument("--output", default="output.json", help="Path to save the output JSON")
    parser.add_argument("--max-depth", type=int, default=2, help="Maximum crawling depth")
    parser.add_argument("--use-ai", action="store_true", help="Use AI for summarization (requires pytorch/transformers)")
    parser.add_argument("--no-cache", action="store_true", help="Disable caching of crawled pages")
    
    args = parser.parse_args()
    
    start_urls = [u.strip() for u in args.url.split(',')]
    
    logger.info(f"Starting extraction for: {start_urls}")
    
    # 1. Crawl
    crawled_data = run_crawler(start_urls, max_depth=args.max_depth, use_cache=not args.no_cache)
    
    if not crawled_data:
        logger.error("No data crawled. Exiting.")
        return

    # 2. Infer Structure
    inference_engine = ModuleInference(start_urls)
    structure = inference_engine.infer_structure(crawled_data)
    
    # 3. Summarize and Format Output
    summarizer = Summarizer(use_ai=args.use_ai)
    final_output = []

    logger.info("Generating descriptions...")
    
    for module_name, module_data in structure.items():
        module_entry = {
            "module": module_name,
            "Description": "",
            "Submodules": {}
        }
        
        # Generate module description from its main pages
        if module_data["pages"]:
            # Combine content from all pages in this module root
            all_content = []
            for p in module_data["pages"]:
                all_content.extend(p["content"])
            module_entry["Description"] = summarizer.generate_description(all_content)
        else:
            module_entry["Description"] = "Container module."

        # Process Submodules
        for sub_name, sub_data in module_data.get("submodules", {}).items():
            sub_content = []
            for p in sub_data["pages"]:
                sub_content.extend(p["content"])
            
            sub_desc = summarizer.generate_description(sub_content)
            module_entry["Submodules"][sub_name] = sub_desc
            
        final_output.append(module_entry)

    # 4. Save
    try:
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(final_output, f, indent=2, ensure_ascii=False)
        logger.info(f"Successfully saved output to {args.output}")
    except Exception as e:
        logger.error(f"Failed to save output: {e}")

if __name__ == "__main__":
    main()
