import os
import sys
import logging
import zipfile
import urllib.request

# Dynamic path resolution relative to this file
SRC_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SRC_DIR)

DATA_DIR = os.path.join(PROJECT_ROOT, "data")
DATA_RAW_DIR = os.path.join(DATA_DIR, "raw")
DATA_PROCESSED_DIR = os.path.join(DATA_DIR, "processed")
NOTEBOOKS_DIR = os.path.join(PROJECT_ROOT, "notebooks")
API_DIR = os.path.join(PROJECT_ROOT, "api")

# Create necessary directories
for path in [DATA_RAW_DIR, DATA_PROCESSED_DIR, NOTEBOOKS_DIR, API_DIR]:
    os.makedirs(path, exist_ok=True)

def setup_logger(name: str) -> logging.Logger:
    """
    Sets up a logger that outputs to both a platform.log file in the project root
    and the standard output console.
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    # Avoid duplicate handlers if setup multiple times
    if not logger.handlers:
        formatter = logging.Formatter(
            '[%(asctime)s] %(levelname)s [%(name)s:%(lineno)d]: %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        # File Handler
        log_file_path = os.path.join(PROJECT_ROOT, "platform.log")
        file_handler = logging.FileHandler(log_file_path, encoding='utf-8')
        file_handler.setFormatter(formatter)
        file_handler.setLevel(logging.INFO)

        # Console Handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        console_handler.setLevel(logging.INFO)

        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

    return logger

logger = setup_logger("Utils")

def download_and_extract_zip(url: str, dest_dir: str):
    """
    Downloads a ZIP file from url and extracts it to dest_dir.
    """
    os.makedirs(dest_dir, exist_ok=True)
    zip_path = os.path.join(dest_dir, "temp_dataset.zip")
    
    logger.info(f"Downloading from {url} to {zip_path}...")
    try:
        urllib.request.urlretrieve(url, zip_path)
        logger.info("Download completed. Extracting files...")
        
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(dest_dir)
        
        logger.info("Extraction complete. Deleting ZIP file...")
        os.remove(zip_path)
    except Exception as e:
        logger.error(f"Failed to download/extract zip: {e}")
        if os.path.exists(zip_path):
            os.remove(zip_path)
        raise e
