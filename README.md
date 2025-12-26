# AI-Powered Documentation Module Extractor

## Project Overview

This project is a Python-based tool designed to accept documentation URLs, recursively crawl them, extract structured content, and intelligently infer high-level modules and submodules. It generates detailed descriptions strictly from the documentation content, ensuring no hallucinations.

The system is designed to be modular, scalable, and production-ready, featuring both a Command Line Interface (CLI) and a Streamlit Web Application.

## Key Features

- **Recursive Crawling**: Intelligent crawling ensuring domain restriction and handling of redirects/broken links.
- **Content Extraction**: Parsing of meaningful content while stripping noise (navbars, footers).
- **Module Inference**: Logic to group content into Modules and Submodules based on document hierarchy.
- **AI-Powered Summarization**: Generates descriptions using NLP techniques (or heuristic extraction) strictly from source text.
- **Multiple Interfaces**: CLI for automation and Streamlit for interactive exploration.
- **Structured Output**: JSON output ready for downstream processing.

## Architecture

The project is organized into modular components:

- **app/**: Contains the core logic.
    - `crawler.py`: Handles web crawling and URL validation.
    - `parser.py`: Parses HTML and cleans content.
    - `module_inference.py`: Infers module structure.
    - `summarizer.py`: Generates descriptions.
    - `streamlit_app.py`: Web interface.
- **cli/**: Command-line entry point.
- **tests/**: Unit and integration tests.

## Installation

1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd module-extractor
    ```

2.  **Create a virtual environment (optional but recommended):**
    ```bash
    python -m venv venv
    # Windows
    .\venv\Scripts\activate
    # Linux/Mac
    source venv/bin/activate
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    python -m spacy download en_core_web_sm
    ```

## Usage

### Streamlit App

Run the interactive web interface:

```bash
streamlit run app/streamlit_app.py
```

### CLI Tool

Run the extractor from the command line:

```bash
python cli/module_extractor.py --url "https://example.com/docs" --output "output.json"
```

## detailed documentation

Please refer to individual module docstrings for more detailed technical information.
