from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import uvicorn
import os
import sys

# Add project root
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.crawler import run_crawler
from app.module_inference import ModuleInference
from app.summarizer import Summarizer

app = FastAPI(title="Doc Module Extractor API", version="1.0")

class ExtractionRequest(BaseModel):
    urls: List[str]
    max_depth: int = 2
    use_ai: bool = False
    use_cache: bool = True

@app.get("/")
def read_root():
    return {"message": "Welcome to the Documentation Module Extractor API. Use POST /extract to start a job."}

@app.post("/extract")
def extract_modules(request: ExtractionRequest):
    try:
        # Crawl
        crawled_data = run_crawler(request.urls, max_depth=request.max_depth, use_cache=request.use_cache)
        
        if not crawled_data:
            raise HTTPException(status_code=404, detail="No pages found to crawl.")

        # Infer
        inference = ModuleInference(request.urls)
        structure = inference.infer_structure(crawled_data)
        
        # Summarize
        summarizer = Summarizer(use_ai=request.use_ai)
        final_output = []

        for module_name, module_data in structure.items():
            entry = {
                "module": module_name,
                "Description": "",
                "Submodules": {}
            }
            
            # Module Desc
            if module_data["pages"]:
                all_content = []
                for p in module_data["pages"]:
                    all_content.extend(p["content"])
                entry["Description"] = summarizer.generate_description(all_content)
            else:
                entry["Description"] = "Container module."

            # Submodule Desc
            for sub_name, sub_data in module_data.get("submodules", {}).items():
                sub_content = []
                for p in sub_data["pages"]:
                    sub_content.extend(p["content"])
                entry["Submodules"][sub_name] = summarizer.generate_description(sub_content)
                
            final_output.append(entry)
            
        return final_output

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
