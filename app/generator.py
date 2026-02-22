import json
import os
import logging

logger = logging.getLogger(__name__)


def generate_sources_json(claims, groups, path):
    """
    Generate JSON file with all claims, evidence, and group assignments.
    
    Args:
        claims: List of all claims
        groups: List of claim groups
        path: Output file path
    """
    os.makedirs(os.path.dirname(path), exist_ok=True)
    
    output = []
    
    for group_id, group in enumerate(groups):
        for claim in group:
            entry = {
                "claim": claim["claim"],
                "evidence": claim["evidence"],
                "source": claim["source"],
                "group_id": group_id,
                "claim_length": claim.get("length", len(claim["claim"]))
            }
            
            # Include confidence if available
            if "confidence" in claim:
                entry["confidence"] = claim["confidence"]
            
            output.append(entry)
    
    with open(path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    logger.info(f"Generated sources.json with {len(output)} claims")


def generate_digest(groups, path):
    """
    Generate markdown digest with themed sections.
    
    Args:
        groups: List of claim groups
        path: Output file path
    """
    os.makedirs(os.path.dirname(path), exist_ok=True)
    
    with open(path, "w", encoding="utf-8") as f:
        f.write("# Research Digest\n\n")
        f.write(f"## Summary\n\n")
        f.write(f"- Total Themes: {len(groups)}\n\n")
        total_claims = sum(len(g) for g in groups)
        f.write(f"- Total Claims: {total_claims}\n\n")
        
        sources = set()
        for group in groups:
            for claim in group:
                sources.add(claim["source"])
        f.write(f"- Sources: {len(sources)}\n\n")
        
        f.write("---\n\n")
        
        for i, group in enumerate(groups):
            # Generate theme title from first claim
            theme_title = generate_theme_title(group)
            f.write(f"## Theme {i+1}: {theme_title}\n\n")
            
            # List unique sources
            sources = set(c["source"] for c in group)
            f.write("**Sources:**\n")
            for s in sources:
                f.write(f"- {s}\n")
            f.write("\n")
            
            # List all claims
            f.write("**Claims:**\n")
            for c in group:
                # Add confidence badge if available
                conf = c.get("confidence")
                if conf:
                    conf_str = f" [Confidence: {conf:.0%}]"
                else:
                    conf_str = ""
                f.write(f"- {c['claim']}{conf_str}\n")
            
            f.write("\n**Evidence:**\n")
            for c in group:
                f.write(f"> {c['evidence']}\n")
                f.write(f"> — *Source: {c['source']}*\n\n")
            
            f.write("---\n\n")
    
    logger.info(f"Generated digest.md with {len(groups)} themes")


def generate_theme_title(group):
    """
    Generate a descriptive title for a theme group.
    
    Args:
        group: List of claims in the group
        
    Returns:
        Theme title string
    """
    if not group:
        return "Untitled Theme"
    
    # Use first claim as basis for title
    first_claim = group[0]["claim"]
    
    # Truncate and clean up
    if len(first_claim) > 60:
        title = first_claim[:60].rsplit(" ", 1)[0] + "..."
    else:
        title = first_claim
    
    return title


def generate_summary_stats(docs, claims, groups):
    """
    Generate summary statistics about the processing.
    
    Args:
        docs: List of processed documents
        claims: List of extracted claims
        groups: List of claim groups
        
    Returns:
        Dictionary with statistics
    """
    sources = set(d["source"] for d in docs)
    
    return {
        "total_documents": len(docs),
        "total_sources": len(sources),
        "total_claims": len(claims),
        "total_themes": len(groups),
        "avg_claims_per_doc": len(claims) / len(docs) if docs else 0,
        "avg_claims_per_theme": len(claims) / len(groups) if groups else 0
    }
