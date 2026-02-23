from sentence_transformers import SentenceTransformer
from sklearn.cluster import AgglomerativeClustering
from sklearn.metrics.pairwise import cosine_similarity
import logging
import hashlib

logger = logging.getLogger(__name__)

_model = None
MODEL_NAME = 'all-MiniLM-L6-v2'

# STRICT domain classification
REMOTE_WORK_KEYWORDS = [
    "remote work", "work from home", "work-from-home",
    "telecommut", "telecommuting", "flexible work",
    "hybrid work", "office attendance", "workplace",
    "employee", "productivity", "commute", "home office",
    "work arrangement", "work model", "return to office",
    "in-office", "out-of-office", "virtual meeting"
]

AI_CORE_KEYWORDS = [
    "artificial intelligence", "ai ", " ai,", "machine learning",
    "deep learning", "neural network", "algorithm", "algorithmic",
    "gpt", "llm", "language model", "transformer",
    "model", "models", "training data", "training set",
    "classifier", "prediction", "classification"
]

AI_RISK_KEYWORDS = [
    "risk", "risk", "danger", "harm", "misuse", "abuse",
    "bias", "biased", "fairness", "discriminat", "discrimination",
    "ethical", "ethics", "moral", "safety", "unsafe",
    "regulation", "regulate", "policy", "government",
    "privacy", "surveillance", "surveill",
    "weapon", "weaponize", "military", "attack",
    "existential", "catastrophic", "alignment",
    "deepfake", "disinformation", "misinformation",
    "job displacement", "unemployment", "automation"
]

TECH_SOCIETY_KEYWORDS = [
    "technology", "technological", "innovation",
    "energy", "emission", "carbon", "climate", "environment",
    "sustainability", "renewable", "pollution",
    "economic", "economy", "industry", "industries",
    "society", "social", "culture", "cultural"
]


def get_model():
    global _model
    if _model is None:
        logger.info(f"Loading sentence transformer model: {MODEL_NAME}")
        _model = SentenceTransformer(MODEL_NAME)
        logger.info("Model loaded successfully")
    return _model


def get_claim_hash(claim):
    return hashlib.md5(claim.lower().strip().encode()).hexdigest()


def assign_strict_domain(claim_text):
    """
    STRICT domain classification.
    Returns (domain_name, confidence) or (None, 0) if no match.
    """
    text_lower = claim_text.lower()
    
    # Check Remote Work
    remote_score = sum(1 for kw in REMOTE_WORK_KEYWORDS if kw in text_lower)
    if remote_score > 0:
        return ("Remote Work & Productivity", remote_score)
    
    # Check AI Risk keywords (must check before general AI)
    ai_risk_score = sum(1 for kw in AI_RISK_KEYWORDS if kw in text_lower)
    
    # Check AI core keywords
    ai_core_score = sum(1 for kw in AI_CORE_KEYWORDS if kw in text_lower)
    
    if ai_core_score > 0 or ai_risk_score > 0:
        # If has risk keywords, classify as AI Risks
        if ai_risk_score > 0:
            return ("AI Risks & Ethics", ai_risk_score + ai_core_score)
        else:
            return ("AI Technology", ai_core_score)
    
    # Check Tech & Society
    tech_score = sum(1 for kw in TECH_SOCIETY_KEYWORDS if kw in text_lower)
    if tech_score >= 2:  # Need at least 2 matches
        return ("Technology & Society", tech_score)
    
    # No match - discard
    return (None, 0)


def group_claims_by_strict_domain(claims):
    """
    Group claims using STRICT domain classification.
    Discards claims that don't fit any domain.
    """
    if not claims:
        return []
    
    domain_groups = {}
    discarded = 0
    
    for claim in claims:
        domain, score = assign_strict_domain(claim["claim"])
        
        if domain is None:
            discarded += 1
            continue
        
        if domain not in domain_groups:
            domain_groups[domain] = []
        
        domain_groups[domain].append(claim)
    
    logger.info(f"Strict domain grouping: {len(domain_groups)} domains, {discarded} discarded")
    
    # Sort claims within each domain by quality
    for domain in domain_groups:
        domain_groups[domain].sort(
            key=lambda x: x.get("quality_score", x.get("confidence", 0)),
            reverse=True
        )
    
    return list(domain_groups.values())


def compute_similarity(text1, text2):
    model = get_model()
    embeddings = model.encode([text1, text2])
    similarity = cosine_similarity([embeddings[0]], [embeddings[1]])[0][0]
    return similarity


def group_claims(claims, threshold=1.2):
    """Main grouping function - uses strict domain classification."""
    if not claims:
        logger.warning("No claims provided for grouping")
        return []
    
    logger.info(f"Grouping {len(claims)} claims with STRICT domain classification")
    
    # Use strict domain classification
    groups = group_claims_by_strict_domain(claims)
    
    if not groups:
        logger.warning("No claims after strict domain filtering")
        return []
    
    logger.info(f"Created {len(groups)} domain groups")
    return groups


def deduplicate_exact(claims):
    """Remove exact duplicate claims."""
    seen_hashes = set()
    unique_claims = []
    
    for claim in claims:
        claim_hash = get_claim_hash(claim["claim"])
        if claim_hash not in seen_hashes:
            seen_hashes.add(claim_hash)
            unique_claims.append(claim)
    
    logger.info(f"Removed {len(claims) - len(unique_claims)} exact duplicates")
    return unique_claims


def find_similar_claims(query_claim, claims, top_k=5):
    """Find similar claims."""
    model = get_model()
    query_embedding = model.encode([query_claim])
    claim_embeddings = model.encode([c["claim"] for c in claims])
    similarities = cosine_similarity(query_embedding, claim_embeddings)[0]
    
    indexed_similarities = list(enumerate(similarities))
    indexed_similarities.sort(key=lambda x: x[1], reverse=True)
    
    results = []
    for idx, score in indexed_similarities[:top_k]:
        results.append((claims[idx], score))
    
    return results
