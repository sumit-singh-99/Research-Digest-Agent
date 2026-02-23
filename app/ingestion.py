import requests
from bs4 import BeautifulSoup
import os
import logging
import re

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Config
MIN_CONTENT_LENGTH = 50
FETCH_TIMEOUT = 10

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "text/html",
}


def clean_text(text):
    """
    Clean raw text by removing citations, references, and noise.
    """

    # Remove [1], [23], etc.
    text = re.sub(r"\[[^\]]*\]", "", text)

    # Remove weird lines starting with ^
    text = re.sub(r"^\s*\^.*$", "", text, flags=re.MULTILINE)

    # Remove Wikipedia junk words
    junk_patterns = [
        "Privacy policy",
        "About Wikipedia",
        "Disclaimers",
        "Contact Wikipedia",
        "Code of Conduct",
        "Developers",
        "Statistics",
        "Cookie statement",
        "ISBN",
        "Retrieved",
        "Jump to content",
        "Main menu",
        "Navigation",
    ]

    for pattern in junk_patterns:
        text = text.replace(pattern, "")

    # Normalize spaces
    text = re.sub(r"\s+", " ", text).strip()

    return text


def fetch_url(url):
    """
    Fetch and extract meaningful content from URL.
    """
    try:
        logger.info(f"Fetching URL: {url}")
        res = requests.get(url, timeout=FETCH_TIMEOUT, headers=HEADERS)
        res.raise_for_status()

        soup = BeautifulSoup(res.text, "html.parser")

        # Title
        title = soup.title.string.strip() if soup.title else "No Title"

        # Remove scripts/styles
        for tag in soup(["script", "style", "nav", "footer", "header"]):
            tag.decompose()

        # ✅ IMPORTANT FIX: Only extract paragraph content
        paragraphs = soup.find_all("p")

        text = " ".join(p.get_text() for p in paragraphs)

        # Clean text
        text = clean_text(text)

        logger.info(f"Fetched {url} | Length: {len(text)}")

        return {
            "source": url,
            "title": title,
            "text": text,
            "length": len(text)
        }

    except requests.exceptions.Timeout:
        logger.warning(f"Timeout: {url}")
        return None
    except requests.exceptions.ConnectionError:
        logger.warning(f"Connection error: {url}")
        return None
    except requests.exceptions.HTTPError as e:
        logger.warning(f"HTTP error: {url} | {e}")
        return None
    except Exception as e:
        logger.error(f"Error fetching {url}: {e}")
        return None


def read_file(path):
    """
    Read and clean local file content.
    """
    try:
        logger.info(f"Reading file: {path}")

        if not os.path.exists(path):
            logger.warning(f"File not found: {path}")
            return None

        with open(path, "r", encoding="utf-8") as f:
            text = f.read()

        if not text.strip():
            logger.warning(f"Empty file: {path}")
            return None

        text = clean_text(text)

        return {
            "source": path,
            "title": os.path.basename(path),
            "text": text,
            "length": len(text)
        }

    except Exception as e:
        logger.error(f"Error reading {path}: {e}")
        return None


def ingest(inputs):
    """
    Ingest multiple sources.
    """
    docs = []
    failed = []

    for item in inputs:
        logger.info(f"Processing: {item}")

        if item.startswith("http"):
            data = fetch_url(item)
        else:
            data = read_file(item)

        if data is None:
            failed.append(item)
            continue

        if data["length"] < MIN_CONTENT_LENGTH:
            logger.warning(f"Too short: {item}")
            failed.append(item)
            continue

        docs.append(data)

    logger.info(f"Ingested {len(docs)} documents")

    if failed:
        logger.info(f"Failed sources: {len(failed)}")

    return docs