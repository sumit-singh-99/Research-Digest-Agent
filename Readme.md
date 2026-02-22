# Research Digest Agent

An autonomous research digest agent that ingests multiple sources, extracts key information, removes redundancy, and produces a structured, evidence-backed brief.

## Overview

This agent helps summarize research on any topic by reading multiple sources (local files or URLs) and producing a concise, structured digest with:

- Key claims extracted from each source
- Evidence snippets supporting each claim
- Grouped similar claims by theme
- Source attribution for all claims

## Features

- **Content Ingestion**: Supports both local text files and URLs
- **Claim Extraction**: Extracts key claims with supporting evidence quotes
- **Deduplication**: Removes exact and near-duplicate claims using semantic similarity
- **Grouping**: Clusters related claims into themes using sentence embeddings
- **Confidence Scores**: Assigns confidence scores to each claim
- **Configurable Threshold**: Adjust grouping sensitivity

## Installation

```
bash
# Create and activate virtual environment
python -m venv .venv
.venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt
```

## Usage

### Basic Usage

```
bash
python main.py
```

The agent processes sources defined in `main.py` and generates:

- `data/output/digest.md` - Structured digest with themed sections
- `data/output/sources.json` - All claims with metadata

### Configuration

Modify the `inputs` list in `main.py` to specify your sources:

```
python
# Local files
inputs = [
    "data/input/sample1.txt",
    "data/input/sample2.txt",
    "data/input/sample3.txt"
]

# URLs
inputs = [
    "https://example.com/article1",
    "https://example.com/article2"
]

# Mixed sources
inputs = [
    "data/input/sample1.txt",
    "https://example.com/article"
]
```

### Clustering Threshold

The `threshold` parameter in `main.py` controls how claims are grouped:

- **0.2** = Very strict (only very similar claims grouped)
- **0.3** = Strict
- **0.4** = Moderate (recommended - balances grouping)
- **0.5** = Loose (groups more things together)

## How It Works

### Step-by-Step Processing

1. **Content Ingestion**
   - URLs: Fetch HTML, extract title and text using BeautifulSoup
   - Files: Read local text files
   - Clean and normalize text
   - Skip content under 50 characters

2. **Claim Extraction**
   - Split text into sentences (50-300 characters)
   - Extract each sentence as a potential claim
   - Capture surrounding context as evidence

3. **Deduplication**
   - Remove exact duplicates using MD5 hash
   - Use sentence embeddings for semantic similarity

4. **Grouping**
   - Generate embeddings using `all-MiniLM-L6-v2`
   - Apply Agglomerative Clustering with cosine distance
   - Group claims within threshold distance

5. **Output Generation**
   - Create themed sections in digest.md
   - Generate sources.json with all metadata

### Claims Grounding

Each claim includes:

- Claim text
- Evidence snippet (context from source)
- Source attribution

Claims are never invented - extracted directly from source text.

## Tests

Run all tests:

```
bash
pytest tests/test_agent.py -v
```

### Test Coverage

- Empty/unreachable source handling
- Deduplication of duplicate content
- Preservation of conflicting claims
- Complete pipeline integration

## Project Structure

```
research_digest_agent/
├── app/
│   ├── __init__.py
│   ├── ingestion.py       # URL/file content fetching
│   ├── extractor.py       # Claim extraction
│   ├── deduplicator.py    # Semantic clustering
│   ├── generator.py       # Output generation
│   └── pipeline.py        # Main pipeline
├── data/
│   ├── input/             # Sample input files (5 sources)
│   └── output/            # Generated outputs
├── tests/
│   └── test_agent.py     # Test cases (14 tests)
├── main.py                # Entry point
├── requirements.txt       # Dependencies
└── README.md              # This file
```

## Dependencies

- `requests` - HTTP requests for URL fetching
- `beautifulsoup4` - HTML parsing
- `sentence-transformers` - Sentence embeddings
- `scikit-learn` - Clustering algorithms

## Limitations

- Claim quality depends on sentence boundary detection
- Short content (<50 chars) is skipped
- Multiple unrelated topics may affect grouping
- Confidence scores are approximated

## Potential Improvements

1. Use NLP models (spaCy) for better claim boundaries
2. Named Entity Recognition for fact extraction
3. Multi-language support with cross-lingual embeddings
4. Embedding caching for faster re-runs
5. Clustering visualization
6. Source credibility weighting

## License

MIT License
