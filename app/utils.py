import logging
import sys

def setup_logger(name: str = "module_extractor") -> logging.Logger:
    """Configures and returns a logger instance."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        
        # Console Handler
        ch = logging.StreamHandler(sys.stdout)
        ch.setFormatter(formatter)
        logger.addHandler(ch)
        
        # File Handler (Optional, helps with debugging)
        fh = logging.FileHandler("extractor.log", mode='a', encoding='utf-8')
        fh.setFormatter(formatter)
        logger.addHandler(fh)
        
    return logger
