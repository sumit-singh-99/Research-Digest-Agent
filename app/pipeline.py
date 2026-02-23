from app.ingestion import ingest
from app.extractor import extract_claims, extract_claims_with_confidence
from app.deduplicator import group_claims, deduplicate_exact
from app.generator import generate_digest, generate_sources_json, generate_summary_stats
import logging

logger = logging.getLogger(__name__)

DEFAULT_THRESHOLD = 1.2
DEFAULT_CONFIDENCE = True

MIN_CONFIDENCE = 0.60
MAX_CLAIMS_GLOBAL = 15


def run_pipeline(inputs, threshold=DEFAULT_THRESHOLD, include_confidence=DEFAULT_CONFIDENCE):
    logger.info(f"Starting pipeline with {len(inputs)} inputs")
    logger.info(f"Configuration: threshold={threshold}, confidence={include_confidence}")
    
    # Step 1: Ingestion
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
            claims = extract_claims_with_confidence(doc, threshold=MIN_CONFIDENCE)
        else:
            claims = extract_claims(doc)
        all_claims.extend(claims)
    
    logger.info(f"Extracted {len(all_claims)} total claims")
    
    if not all_claims:
        logger.warning("No claims extracted from documents!")
        return docs, [], []
    
    # Step 3: Exact Deduplication
    logger.info("Step 3: Removing exact duplicates...")
    unique_claims = deduplicate_exact(all_claims)
    logger.info(f"After deduplication: {len(unique_claims)} unique claims")
    
    # Step 4: Quality Filtering
    logger.info("Step 4: Applying quality filtering...")
    unique_claims = apply_quality_filter(unique_claims)
    logger.info(f"After quality filtering: {len(unique_claims)} high-quality claims")
    
    if not unique_claims:
        logger.warning("No high-quality claims after filtering!")
        return docs, [], []
    
    # Step 5: Strict Domain Grouping
    logger.info("Step 5: Grouping by strict domains...")
    groups = group_claims(unique_claims, threshold=threshold)
    logger.info(f"Formed {len(groups)} domain groups")
    
    # Post-process: limit claims per group
    groups = post_process_groups(groups)
    logger.info(f"After post-processing: {len(groups)} final groups")
    
    stats = generate_summary_stats(docs, unique_claims, groups)
    logger.info(f"Summary: {stats}")
    
    return docs, unique_claims, groups


def apply_quality_filter(claims):
    if not claims:
        return claims
    
    max_length = max(c.get("length", 0) for c in claims) or 1
    
    for claim in claims:
        length_score = claim.get("length", 0) / max_length
        confidence = claim.get("confidence", 0)
        claim["quality_score"] = (0.7 * confidence) + (0.3 * length_score)
    
    claims.sort(key=lambda x: x["quality_score"], reverse=True)
    filtered = claims[:MAX_CLAIMS_GLOBAL]
    
    logger.info(f"Quality filter: kept {len(filtered)} out of {len(claims)} claims")
    return filtered


def post_process_groups(groups):
    if not groups:
        return groups
    
    # Limit to max 3 claims per group
    final_groups = []
    for group in groups:
        group.sort(key=lambda x: x.get("quality_score", x.get("confidence", 0)), reverse=True)
        limited_group = group[:3]
        if len(limited_group) >= 2:  # Only keep groups with 2+ claims
            final_groups.append(limited_group)
    
    return final_groups


def run_pipeline_with_config(inputs, config=None):
    if config is None:
        config = {}
    
    threshold = config.get("threshold", DEFAULT_THRESHOLD)
    include_confidence = config.get("include_confidence", DEFAULT_CONFIDENCE)
    
    if "max_claims_global" in config:
        global MAX_CLAIMS_GLOBAL
        MAX_CLAIMS_GLOBAL = config["max_claims_global"]
    
    return run_pipeline(inputs, threshold, include_confidence)


def quick_digest(input_path, output_dir="data/output"):
    import os
    
    if isinstance(input_path, str):
        inputs = [input_path]
    else:
        inputs = input_path
    
    docs, claims, groups = run_pipeline(inputs)
    
    os.makedirs(output_dir, exist_ok=True)
    generate_digest(groups, os.path.join(output_dir, "digest.md"))
    generate_sources_json(claims, groups, os.path.join(output_dir, "sources.json"))
    
    return docs, claims, groups
