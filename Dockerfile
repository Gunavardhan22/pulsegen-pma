FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
# gcc and python3-dev might be needed for some python packages like spacy/numpy
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt
# Download spacy model if needed, otherwise comment out
# RUN python -m spacy download en_core_web_sm

COPY . .

# Expose ports for Streamlit (8501) and FastAPI (8000)
EXPOSE 8501 8000

# Default command runs the CLI help to show usage
CMD ["python", "cli/module_extractor.py", "--help"]
