# Research Digest Agent

An autonomous research digest agent that ingests multiple sources, extracts key information, removes redundancy, and produces a structured, evidence-backed brief.

## What it Generates

After running the pipeline, the agent outputs:

- `data/output/digest.md` — a themed, sectioned research brief with source references
- `data/output/sources.json` — per-source claims + evidence snippets + metadata

## Features

- **Content Ingestion**: Supports both local text/HTML files and URLs
- **Claim Extraction**: Extracts key claims with supporting evidence quotes/snippets
- **Deduplication**: Removes exact and near-duplicate claims
- **Grouping**: Groups similar claims into themes
- **Configurable Threshold**: Adjust grouping sensitivity
- **(Optional/Stretch)** Confidence Scores: confidence is approximated (if enabled in code)

---

## Installation

```bash
# Create and activate virtual environment
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## Usage

### Basic Usage

```bash
python main.py
```

The agent processes sources defined in `main.py`.

### Configure Inputs (URLs or Local Files)

Edit the `inputs` list in `main.py`:

```python
# Local files
inputs = [
    "data/input/sample1.txt",
    "data/input/sample2.txt",
    "data/input/sample3.txt",
]

# URLs
inputs = [
    "https://example.com/article1",
    "https://example.com/article2",
]

# Mixed sources
inputs = [
    "data/input/sample1.txt",
    "https://example.com/article",
]
```

### Grouping / Dedup Threshold

The `threshold` parameter controls how aggressively claims are grouped:

- **lower** = stricter grouping (only very similar claims)
- **higher** = looser grouping (more claims clustered together)

---

## Assignment Answers (Required README Items)

### 1) How the agent processes sources (step by step)

1. **Content ingestion**
   - If the input is a **URL**, the agent fetches the page and extracts readable text (and title when available).
   - If the input is a **local file**, the agent reads the file from disk.
   - Text is **cleaned/normalized** (whitespace cleanup etc.).
   - If a source is empty/too short/unreadable, it is **skipped safely** (no crash).

2. **Metadata capture**
   - For each source, the agent stores basic metadata such as:
     - source identifier (URL/path)
     - title (if available)
     - content length

3. **Claim extraction**
   - The cleaned text is split into candidate sentences/claims.
   - Each extracted claim is paired with a **supporting evidence snippet** from the same source.

4. **Deduplication & grouping**
   - Exact duplicates are removed first.
   - Remaining claims are embedded and clustered using semantic similarity so overlapping claims land in the same group/theme.

5. **Digest generation**
   - The agent writes:
     - `digest.md`: grouped themes with claims and source references
     - `sources.json`: per-source claims + evidence + metadata for traceability

### 2) How claims are grounded

- The agent **does not invent facts**: claims are extracted from the source text.
- Each claim includes an **evidence snippet/quote** taken directly from the same source content.
- Every claim is stored with **source attribution** (URL/path), allowing reviewers to trace claims back to origin.

### 3) How deduplication / grouping works

- **Exact deduplication**: removes identical claim strings (hash-based).
- **Semantic grouping**:
  - Encodes claims into vector embeddings (e.g., `all-MiniLM-L6-v2`).
  - Uses clustering (e.g., agglomerative clustering with cosine distance).
  - Claims within the configured similarity threshold are grouped together.
- Each group tracks **which sources** support it so the digest can cite multiple sources for the same theme.
- If sources disagree, conflicting claims can exist **side-by-side with attribution** (not merged into a single “average” claim).

### 4) One limitation

**Limitation:** Sentence-based extraction is a simple heuristic; some extracted “claims” may be incomplete or not truly claim-like (e.g., sentence fragments or context-dependent statements).

### 5) One improvement with more time

**Improvement:** Add a stronger claim extraction step (LLM- or classifier-based) that outputs structured claims (claim → entities → metric/value → timeframe) while still attaching verbatim evidence snippets for grounding.

---

## Tests

Run tests:

```bash
pytest -v
```

Minimum required behaviors covered by tests (as per assignment):
- Empty/unreachable source handling
- Deduplication of duplicate content
- Preservation of conflicting claims

## Project Structure

```text
app/                     # core pipeline modules
data/input/              # sample sources (>= 5)
data/output/             # generated digest + sources.json
tests/                   # test suite
main.py                  # entry point
requirements.txt
Readme.md
```

## License

MIT License