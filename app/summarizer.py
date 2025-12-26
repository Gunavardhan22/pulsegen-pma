from typing import List, Dict
import logging
from app.utils import setup_logger

logger = setup_logger()

# Optional: Try importing transformers, but provide fallback if not installed/too heavy
try:
    from transformers import pipeline
    has_transformers = True
except ImportError:
    has_transformers = False

class Summarizer:
    """
    Generates summaries/descriptions for modules using extracted text.
    """
    def __init__(self, use_ai: bool = False):
        self.use_ai = use_ai and has_transformers
        self.summarizer_pipeline = None
        
        if self.use_ai:
            try:
                # Use a small, fast model for CPU inference
                logger.info("Loading summarization model (sshleifer/distilbart-cnn-12-6)...")
                self.summarizer_pipeline = pipeline("summarization", model="sshleifer/distilbart-cnn-12-6")
            except Exception as e:
                logger.warning(f"Failed to load AI model: {e}. Falling back to heuristic summarization.")
                self.use_ai = False

    def generate_description(self, content_blocks: List[Dict]) -> str:
        """
        Generates a summary from a list of content blocks.
        """
        # Aggregate text, tailored to not be too long
        full_text = " ".join([b['text'] for b in content_blocks if b['text']])
        
        if not full_text:
            return "No content available for description."

        if self.use_ai and len(full_text) > 200:
            try:
                # Truncate for model input limit (approx 1024 tokens)
                input_text = full_text[:3000] 
                summary = self.summarizer_pipeline(input_text, max_length=130, min_length=30, do_sample=False)
                return summary[0]['summary_text']
            except Exception as e:
                logger.error(f"AI summarization failed: {e}")
                return self._heuristic_summary(full_text)
        else:
            return self._heuristic_summary(full_text)

    def _heuristic_summary(self, text: str) -> str:
        """Returns the first few meaningful sentences."""
        sentences = text.split('.')
        summary = ". ".join(sentences[:3]).strip()
        if summary:
            return summary + "."
        return text[:300] + "..."
