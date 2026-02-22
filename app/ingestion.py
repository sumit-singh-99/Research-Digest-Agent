import requests
from bs4 import BeautifulSoup
import os
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
MIN_CONTENT_LENGTH = 50
FETCH_TIMEOUT = 10


# HTTP headers to avoid 403 errors from websites
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}


def fetch_url(url):
    """
    Fetch content from a URL.
    
    Args:
        url: The URL to fetch
        
    Returns:
        Dictionary with source, title, text, length or None on failure
    """
    try:
        logger.info(f"Fetching URL: {url}")
        res = requests.get(url, timeout=FETCH_TIMEOUT, headers=HEADERS)
        res.raise_for_status()
        
        soup = BeautifulSoup(res.text, "html.parser")
        
        # Extract title
        title = soup.title.string if soup.title else "No Title"
        title = title.strip() if title else "No Title"
        
        # Extract text content
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
        
        text = soup.get_text(separator=" ", strip=True)
        
        # Clean up whitespace
        text = " ".join(text.split())
        
        logger.info(f"Successfully fetched {url}, length: {len(text)} chars")
        
        return {
            "source": url,
            "title": title,
            "text": text,
            "length": len(text)
        }
    except requests.exceptions.Timeout:
        logger.warning(f"Timeout fetching {url}")
        return None
    except requests.exceptions.ConnectionError:
        logger.warning(f"Connection error for {url}")
        return None
    except requests.exceptions.HTTPError as e:
        logger.warning(f"HTTP error for {url}: {e}")
        return None
    except Exception as e:
        logger.error(f"Error fetching {url}: {e}")
        return None


def read_file(path):
    """
    Read content from a local file.
    
    Args:
        path: Path to the file
        
    Returns:
        Dictionary with source, title, text, length or None on failure
    """
    try:
        logger.info(f"Reading file: {path}")
        
        if not os.path.exists(path):
            logger.warning(f"File does not exist: {path}")
            return None
        
        with open(path, "r", encoding="utf-8") as f:
            text = f.read()
        
        # Check if file is empty
        if not text or not text.strip():
            logger.warning(f"File is empty: {path}")
            return None
        
        # Clean up whitespace
        text = " ".join(text.split())
        
        return {
            "source": path,
            "title": os.path.basename(path),
            "text": text,
            "length": len(text)
        }
    except UnicodeDecodeError:
        logger.error(f"Encoding error reading {path}")
        return None
    except PermissionError:
        logger.warning(f"Permission denied: {path}")
        return None
    except Exception as e:
        logger.error(f"Error reading {path}: {e}")
        return None


def ingest(inputs):
    """
    Ingest content from multiple sources (URLs or files).
    
    Args:
        inputs: List of URLs or file paths
        
    Returns:
        List of document dictionaries with metadata
    """
    docs = []
    failed = []
    
    for item in inputs:
        logger.info(f"Processing input: {item}")
        
        if item.startswith("http"):
            data = fetch_url(item)
        else:
            data = read_file(item)
        
        # Check if data is valid and has sufficient content
        if data is None:
            failed.append(item)
            logger.warning(f"Failed to process: {item}")
            continue
            
        if data["length"] < MIN_CONTENT_LENGTH:
            logger.warning(f"Content too short from {item}: {data['length']} chars")
            failed.append(item)
            continue
        
        docs.append(data)
        logger.info(f"Successfully processed {item}: {data['length']} chars")
    
    if failed:
        logger.info(f"Failed to process {len(failed)} out of {len(inputs)} sources")
    
    logger.info(f"Successfully ingested {len(docs)} documents")
    return docs
