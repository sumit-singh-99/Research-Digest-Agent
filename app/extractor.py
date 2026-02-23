import re
import logging

logger = logging.getLogger(__name__)

# Configuration
MIN_CLAIM_LENGTH = 50
MAX_CLAIM_LENGTH = 200
MAX_CLAIMS_PER_DOC = 25

# Weak starters to filter
WEAK_STARTERS = (
    "based on", "that,", "this", "these", "those", "it", "they",
    "as a result", "however", "in addition", "therefore",
    "for example", "for instance", "such as",
    "the result", "this result", "this leads", "this means",
    "several", "more", "which", "had", "their",
    "also", "additionally", "furthermore", "moreover",
    "on the other hand", "in contrast", "consequently",
    "overall", "thus", "hence", "eventually",
    "some researchers", "some studies", "some people",
    "many believe", "some argue", "critics say",
    "advocates say", "experts say", "researchers say",
    "according to", "in the study", "in this paper",
    "as shown", "as seen", "as can be", "it is shown",
    "it is believed", "it is argued", "it seems",
    "it appears", "there is", "there are",
    "we can", "we should", "we need", "we must",
    "you can", "you should", "one can", "one should",
    "in recent years", "over the past", "recent research"
)

# Topics to EXCLUDE - too generic/historical
EXCLUDED_TOPICS = [
    "ancient", "history", "historical", "fire", "stone age",
    "bronze age", "iron age", "medieval", "prehistoric",
    "early humans", "caveman", "hunter-gatherer",
    "animal technology", "beaver dam", "bird's nest",
    "stone tools", "wooden", "charcoal", "aqueduct",
    "roman", "ancient roman", "egypt", "pyramid"
]

# Definition patterns
DEFINITION_PATTERNS = [
    r"^\s*\w+\s+is\s+(a|an)\s+",
    r"^\s*\w+\s+are\s+",
    r"^\s*the\s+\w+\s+is\s+(a|an)\s+",
    r"^\s*\w+\s+refers\s+to\s+",
    r"^\s*\w+\s+means\s+",
    r"^\s*\w+\s+describes\s+",
    r"^\s*\w+\s+defined\s+as\s+",
    r"^\s*\w+\s+can\s+be\s+defined\s+",
    r"is\s+defined\s+as",
    r"refers\s+to\s+the",
    r"is\s+known\s+as",
    r"is\s+called",
]


def compute_confidence(claim, evidence):
    """Compute confidence based on overlap."""
    claim_words = set(claim.lower().split())
    evidence_words = set(evidence.lower().split())
    overlap = len(claim_words & evidence_words)
    return round(min(0.95, 0.4 + overlap / 60), 2)


def split_long_sentence(sentence):
    """Split long sentences."""
    parts = re.split(r'(?<=[.,;])\s+(?=[A-Z""])|(?<=[.!?])\s+(?=[A-Z""])', sentence)
    refined = []
    for part in parts:
        part = part.strip()
        if len(part.split()) >= 8 and len(part) >= 50:
            refined.append(part)
    return refined if refined else [sentence]


def is_complete_sentence(sentence):
    """Check if sentence is complete."""
    if not sentence:
        return False
    if not sentence[0].isupper():
        return False
    sentence = sentence.strip()
    if not sentence.endswith(('.', '!', '?')):
        return False
    return True


def is_weak_starter(sentence):
    """Check weak starter."""
    sentence_lower = sentence.lower().strip()
    for starter in WEAK_STARTERS:
        if sentence_lower.startswith(starter):
            return True
    return False


def is_definition_like(sentence):
    """Check definition-like."""
    for pattern in DEFINITION_PATTERNS:
        if re.search(pattern, sentence, re.IGNORECASE):
            return True
    if "is defined as" in sentence.lower():
        return True
    return False


def is_excluded_topic(sentence):
    """Check if sentence is about excluded topics."""
    sentence_lower = sentence.lower()
    for topic in EXCLUDED_TOPICS:
        if topic in sentence_lower:
            return True
    return False


def is_citation_heavy(sentence):
    """Check citation-heavy."""
    citation_patterns = [
        r'\[\d+\]', r'\(\d{4}\)', r'pp\.?\s*\d+', r'vol\.?\s*\d+',
        r'isbn\s*\d+', r'doi\s*:', r'retrieved\s+from',
        r'archived\s+at', r'viewed\s+on', r'accessed\s+',
    ]
    for pattern in citation_patterns:
        if re.search(pattern, sentence, re.IGNORECASE):
            return True
    return False


def is_insightful_claim(sentence):
    """Check if sentence is an insightful claim (not just fact/definition)."""
    sentence_lower = sentence.lower()
    
    # Insight indicators - sentences that should be KEPT
    insight_indicators = [
        "found that", "showed that", "demonstrated", "revealed",
        "suggests that", "indicates that", "evidence shows",
        "research found", "study shows", "analysis reveals",
        "results indicate", "data suggest", "experiments show",
        "scientists discovered", "researchers found", "published study",
        "concluded that", "determined that", "observed that",
        "significant", "increase", "decrease", "improve", "reduce",
        "may lead", "can cause", "could result", "affects", "impact",
        "survey", "study found", "analysis of", "investigation",
        "reported", "estimated", "potential", "associated with",
        "risk", "bias", "concern", "challenge", "benefit"
    ]
    
    for indicator in insight_indicators:
        if indicator in sentence_lower:
            return True
    
    return False


def extract_claims(doc):
    """Extract key claims with enhanced quality filters."""
    text = doc.get("text", "")
    source = doc.get("source", "unknown")

    if not text:
        logger.warning(f"No text content in source: {source}")
        return []

    sentences = re.split(r'(?<=[.!?])\s+(?=[A-Z""])', text)
    claims = []

    for sent in sentences:
        sent = sent.strip()
        if not sent:
            continue

        sub_sentences = split_long_sentence(sent)

        for s in sub_sentences:
            s = s.strip()
            if not s:
                continue

            # Remove quotes
            s = s.replace('"', '').replace('"', '').replace('"', '').replace('"', '')

            if s.count('.') > 1:
                continue

            if s.lower().startswith(("he", "she", "they", "this", "that")):
                continue
            
            if not s:
                continue

            # Skip broken quotes
            if '"' in s and s.count('"') % 2 != 0:
                continue

            # 1. MUST be complete sentence
            if not is_complete_sentence(s):
                continue

            # 2. Length filtering
            if len(s) < MIN_CLAIM_LENGTH or len(s) > MAX_CLAIM_LENGTH:
                continue

            # 3. Skip weak starters
            if is_weak_starter(s):
                continue

            # 4. Skip definition-like claims
            if is_definition_like(s):
                continue

            # 5. Skip excluded topics (historical, fire, animals, etc.)
            if is_excluded_topic(s):
                continue

            # 6. Skip citation-heavy sentences
            if is_citation_heavy(s):
                continue

            # 7. Skip likely non-claims
            if is_likely_non_claim(s):
                continue

            # 8. MUST be insightful
            if not is_insightful_claim(s):
                continue
            
            evidence = extract_evidence(text, s)
            confidence = compute_confidence(s, evidence)

            claims.append({
                "claim": s,
                "evidence": evidence,
                "source": source,
                "length": len(s),
                "confidence": confidence
            })

    claims.sort(key=lambda x: (x["confidence"], x["length"]), reverse=True)
    claims = claims[:MAX_CLAIMS_PER_DOC]

    logger.info(f"Extracted {len(claims)} claims from {source}")
    return claims


def is_likely_non_claim(sentence):
    """Detect noisy/non-informative sentences."""
    alpha_chars = sum(c.isalpha() for c in sentence)
    if alpha_chars / max(len(sentence), 1) < 0.4:
        return True

    if sentence.startswith("http") or "www." in sentence.lower():
        return True

    if sentence.isupper() and len(sentence) < 50:
        return True

    if len(sentence.split()) < 8:
        return True

    numbers = sum(c.isdigit() for c in sentence)
    if numbers / max(len(sentence), 1) > 0.3:
        return True

    return False


def extract_evidence(text, claim):
    """Extract surrounding context as evidence."""
    try:
        start_idx = text.lower().find(claim.lower())
    except Exception:
        return claim

    if start_idx == -1:
        return claim

    context_start = max(0, start_idx - 60)
    context_end = min(len(text), start_idx + len(claim) + 60)

    return text[context_start:context_end].strip()


def extract_claims_with_confidence(doc, threshold=0.65):
    """Extract claims with confidence filtering."""
    claims = extract_claims(doc)
    if threshold > 0:
        claims = [c for c in claims if c.get("confidence", 0) >= threshold]
    return claims
