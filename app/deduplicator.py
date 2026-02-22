from sentence_transformers import SentenceTransformer
from sklearn.cluster import AgglomerativeClustering
import logging
import hashlib

logger = logging.getLogger(__name__)

# Global model instance (loaded once)
_model = None

# Default configuration
# Note: With cosine distance, threshold ranges from 0 (identical) to 2 (opposite)
# Lower threshold = stricter grouping (fewer claims per group)
# Higher threshold = looser grouping (more claims grouped together)
# 0.2 = very strict, 0.3 = strict, 0.5 = moderate, 1.0 = loose
DEFAULT_THRESHOLD = 1.2
MODEL_NAME = 'all-MiniLM-L6-v2'


def get_model():
    """Get or load the sentence transformer model"""
    global _model
    if _model is None:
        logger.info(f"Loading sentence transformer model: {MODEL_NAME}")
        _model = SentenceTransformer(MODEL_NAME)
        logger.info("Model loaded successfully")
    return _model


def compute_similarity(text1, text2):
    """
    Compute cosine similarity between two texts.
    
    Args:
        text1: First text
        text2: Second text
        
    Returns:
        Similarity score (0-1)
    """
    model = get_model()
    embeddings = model.encode([text1, text2])
    
    # Cosine similarity
    from sklearn.metrics.pairwise import cosine_similarity
    similarity = cosine_similarity([embeddings[0]], [embeddings[1]])[0][0]
    
    return similarity


def get_claim_hash(claim):
    """
    Generate a simple hash for a claim to help with exact duplicate detection.
    
    Args:
        claim: The claim text
        
    Returns:
        Hash string
    """
    return hashlib.md5(claim.lower().strip().encode()).hexdigest()


def group_claims(claims, threshold=DEFAULT_THRESHOLD):
    """
    Group similar claims together using semantic clustering.
    
    Args:
        claims: List of claim dictionaries
        threshold: Distance threshold for clustering (lower = stricter)
        
    Returns:
        List of groups, each containing related claims
    """
    if not claims:
        logger.warning("No claims provided for grouping")
        return []
    
    logger.info(f"Grouping {len(claims)} claims with threshold {threshold}")
    
    model = get_model()
    
    # Extract claim texts
    texts = [c["claim"] for c in claims]
    
    # Generate embeddings
    logger.info("Computing embeddings...")
    embeddings = model.encode(texts)
    
    # Perform clustering
    logger.info("Performing clustering...")
    clustering = AgglomerativeClustering(
        n_clusters=None,
        distance_threshold=threshold,
        metric='cosine',  # Use cosine distance for better semantic matching
        linkage='average'  # Use average linkage for more balanced groups
    ).fit(embeddings)
    
    # Organize into groups
    groups = {}
    for idx, label in enumerate(clustering.labels_):
        groups.setdefault(label, []).append(claims[idx])
    
    result = list(groups.values())
    logger.info(f"Created {len(result)} groups from {len(claims)} claims")
    
    return result


def find_similar_claims(query_claim, claims, top_k=5):
    """
    Find claims similar to a query claim.
    
    Args:
        query_claim: The claim to find similar ones for
        claims: List of all claims
        top_k: Number of similar claims to return
        
    Returns:
        List of (claim, similarity_score) tuples
    """
    model = get_model()
    
    query_embedding = model.encode([query_claim])
    claim_embeddings = model.encode([c["claim"] for c in claims])
    
    from sklearn.metrics.pairwise import cosine_similarity
    
    similarities = cosine_similarity(query_embedding, claim_embeddings)[0]
    
    # Get top-k similar claims
    indexed_similarities = list(enumerate(similarities))
    indexed_similarities.sort(key=lambda x: x[1], reverse=True)
    
    results = []
    for idx, score in indexed_similarities[:top_k]:
        results.append((claims[idx], score))
    
    return results


def deduplicate_exact(claims):
    """
    Remove exact duplicate claims.
    
    Args:
        claims: List of claim dictionaries
        
    Returns:
        List of claims with exact duplicates removed
    """
    seen_hashes = set()
    unique_claims = []
    
    for claim in claims:
        claim_hash = get_claim_hash(claim["claim"])
        
        if claim_hash not in seen_hashes:
            seen_hashes.add(claim_hash)
            unique_claims.append(claim)
    
    logger.info(f"Removed {len(claims) - len(unique_claims)} exact duplicates")
    return unique_claims
