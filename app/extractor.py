import re
import logging

logger = logging.getLogger(__name__)

# Configuration
MIN_CLAIM_LENGTH = 80
MAX_CLAIM_LENGTH = 300
EVIDENCE_LENGTH = 200
MAX_CLAIMS_PER_DOC = 40


def extract_claims(doc):
    """
    Extract key claims from a document.

    Args:
        doc: Dictionary with text, source, title

    Returns:
        List of claim dictionaries
    """
    text = doc.get("text", "")
    source = doc.get("source", "unknown")

    if not text:
        logger.warning(f"No text content in source: {source}")
        return []

    # Split text into sentences
    sentences = re.split(r'(?<=[.!?])\s+', text)

    claims = []

    for sentence in sentences:
        sentence = sentence.strip()

        # Skip empty sentences
        if not sentence:
            continue

        # Length filtering
        if len(sentence) < MIN_CLAIM_LENGTH or len(sentence) > MAX_CLAIM_LENGTH:
            continue

        # Skip weak/connector sentences
        if sentence.lower().startswith((
            "as a result", "this", "however", "in addition", "therefore"
        )):
            continue

        # Skip non-meaningful sentences
        if is_likely_non_claim(sentence):
            continue

        # Extract evidence snippet
        evidence = extract_evidence(text, sentence)

        claim = {
            "claim": sentence,
            "evidence": evidence,
            "source": source,
            "length": len(sentence)
        }

        claims.append(claim)

    # Sort claims by length (longer = more informative)
    claims.sort(key=lambda x: x["length"], reverse=True)

    # Limit number of claims per document
    claims = claims[:MAX_CLAIMS_PER_DOC]

    logger.info(f"Extracted {len(claims)} claims from {source}")
    return claims


def is_likely_non_claim(sentence):
    """
    Determine if a sentence is likely not a meaningful claim.
    """

    # Too many numbers
    alpha_chars = sum(c.isalpha() for c in sentence)
    if alpha_chars / len(sentence) < 0.3:
        return True

    # URL-like content
    if sentence.startswith("http") or "www." in sentence.lower():
        return True

    # All uppercase (likely header)
    if sentence.isupper() and len(sentence) < 50:
        return True

    # Too few words
    if len(sentence.split()) < 5:
        return True

    return False


def extract_evidence(text, claim):
    """
    Extract surrounding context as evidence for a claim.
    """

    if claim in text:
        start_idx = text.index(claim)
    else:
        lower_claim = claim.lower()
        lower_text = text.lower()
        start_idx = lower_text.find(lower_claim)

    if start_idx == -1:
        return claim[:EVIDENCE_LENGTH]

    context_start = max(0, start_idx - 50)
    context_end = min(len(text), start_idx + len(claim) + 50)

    evidence = text[context_start:context_end].strip()

    if len(evidence) > EVIDENCE_LENGTH:
        evidence = evidence[:EVIDENCE_LENGTH] + "..."

    return evidence


def extract_claims_with_confidence(doc, threshold=0.5):
    """
    Optional: Extract claims with confidence scores.
    """

    claims = extract_claims(doc)

    for claim in claims:
        word_count = len(claim["claim"].split())
        base_confidence = 0.7
        length_bonus = min(0.2, word_count / 50)

        claim["confidence"] = min(0.95, base_confidence + length_bonus)

    if threshold > 0:
        claims = [c for c in claims if c.get("confidence", 0) >= threshold]

    return claims