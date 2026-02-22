from app.ingestion import ingest
from app.extractor import extract_claims, extract_claims_with_confidence
from app.deduplicator import group_claims, deduplicate_exact
from app.generator import generate_digest, generate_sources_json, generate_summary_stats
import logging

logger = logging.getLogger(__name__)

# Default configuration
DEFAULT_THRESHOLD = 1.2
DEFAULT_CONFIDENCE = True  # Enable confidence scoring by default


def run_pipeline(inputs, threshold=DEFAULT_THRESHOLD, include_confidence=DEFAULT_CONFIDENCE):
    """
    Run the complete research digest pipeline.
    
    Args:
        inputs: List of URLs or file paths (minimum 5 recommended)
        threshold: Distance threshold for claim clustering (lower = stricter)
        include_confidence: Whether to include confidence scores
        
    Returns:
        Tuple of (docs, claims, groups)
    """
    logger.info(f"Starting pipeline with {len(inputs)} inputs")
    logger.info(f"Configuration: threshold={threshold}, confidence={include_confidence}")
    
    # Step 1: Content Ingestion
    logger.info("Step 1: Ingesting content...")
    docs = ingest(inputs)
    logger.info(f"Loaded {len(docs)} documents")
    
    if not docs:
        logger.warning("No valid documents found!")
        return [], [], []
    
    # Step 2: Claim Extraction
    logger.info("Step 2: Extracting claims...")
    all_claims = []
    
    for doc in docs:
        if include_confidence:
            claims = extract_claims_with_confidence(doc)
        else:
            claims = extract_claims(doc)
        all_claims.extend(claims)
    
    logger.info(f"Extracted {len(all_claims)} total claims")
    
    if not all_claims:
        logger.warning("No claims extracted from documents!")
        return docs, [], []
    
    # Step 3: Exact Deduplication (before semantic clustering)
    logger.info("Step 3: Removing exact duplicates...")
    unique_claims = deduplicate_exact(all_claims)
    logger.info(f"After deduplication: {len(unique_claims)} unique claims")
    
    # Step 4: Semantic Grouping
    logger.info("Step 4: Grouping similar claims...")
    groups = group_claims(unique_claims, threshold=threshold)
    logger.info(f"Formed {len(groups)} theme groups")
    
    # Generate summary statistics
    stats = generate_summary_stats(docs, unique_claims, groups)
    logger.info(f"Summary: {stats}")
    
    return docs, unique_claims, groups


def run_pipeline_with_config(inputs, config=None):
    """
    Run pipeline with custom configuration.
    
    Args:
        inputs: List of URLs or file paths
        config: Configuration dictionary with optional keys:
            - threshold: Clustering distance threshold
            - include_confidence: Whether to compute confidence scores
            - min_claim_length: Minimum claim length (default: 50)
            - max_claim_length: Maximum claim length (default: 300)
            
    Returns:
        Tuple of (docs, claims, groups)
    """
    if config is None:
        config = {}
    
    threshold = config.get("threshold", DEFAULT_THRESHOLD)
    include_confidence = config.get("include_confidence", DEFAULT_CONFIDENCE)
    
    return run_pipeline(inputs, threshold, include_confidence)


# Convenience function for quick usage
def quick_digest(input_path, output_dir="data/output"):
    """
    Quick way to generate a digest from a single source or list of sources.
    
    Args:
        input_path: Can be a single path or list of paths
        output_dir: Output directory for results
        
    Returns:
        Tuple of (docs, claims, groups)
    """
    import os
    
    # Convert single path to list
    if isinstance(input_path, str):
        inputs = [input_path]
    else:
        inputs = input_path
    
    docs, claims, groups = run_pipeline(inputs)
    
    # Generate outputs
    os.makedirs(output_dir, exist_ok=True)
    
    generate_digest(groups, os.path.join(output_dir, "digest.md"))
    generate_sources_json(claims, groups, os.path.join(output_dir, "sources.json"))
    
    return docs, claims, groups
