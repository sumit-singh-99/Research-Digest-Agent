"""
Research Digest Agent - Main Entry Point

This script demonstrates how to use the Research Digest Agent
to process multiple sources and generate a structured digest.

Usage:
    python main.py

The agent can process:
- Local text files (data/input/sample*.txt)
- URLs (http://example.com/article)
- Mixed sources
"""

from app.pipeline import run_pipeline
from app.generator import generate_digest, generate_sources_json
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Main function to run the research digest agent."""
    
    print("Running Research Digest Agent")
    print("=" * 50)
    
    # You can modify this section to use different sources
    
    # Option 1: Use local text files (default)
    # The sample files cover topics: AI, Remote Work
    # inputs = [
    #     "data/input/sample1.txt",
    #     "data/input/sample2.txt",
    #     "data/input/sample3.txt",
    #     "data/input/sample4.txt",
    #     "data/input/sample5.txt"
    # ]
    
    # Option 2: Use URLs (uncomment to use)
    # Note: Using Wikipedia articles as they are reliable public sources
    inputs = [
        "https://en.wikipedia.org/wiki/Artificial_intelligence",
        "https://en.wikipedia.org/wiki/Remote_work",
        "https://en.wikipedia.org/wiki/Machine_learning",
        "https://en.wikipedia.org/wiki/Technology",
        "https://en.wikipedia.org/wiki/Work_from_home"
    ]
    
    # Option 3: Mix local files and URLs
    # inputs = [
    #     "data/input/sample1.txt",
    #     "https://en.wikipedia.org/wiki/Artificial_intelligence",
    #     "data/input/sample2.txt"
    # ]
    
    # Clustering threshold (with cosine distance)

    threshold = 0.78
    
    # Include confidence scores (optional feature)
    include_confidence = True
    
    logger.info(f"Processing {len(inputs)} sources...")
    
    docs, claims, groups = run_pipeline(
        inputs, 
        threshold=threshold,
        include_confidence=include_confidence
    )
    
    if not docs:
        print("   No documents were successfully processed!")
        print("   Please check your input sources and try again.")
        return
      
    # OUTPUT GENERATION
    
    print(f"\n Processing Complete!")
    print(f"   Documents processed: {len(docs)}")
    print(f"   Claims extracted: {len(claims)}")
    print(f"   Theme groups: {len(groups)}")
    
    # Generate output files
    generate_digest(groups, "data/output/digest.md")
    generate_sources_json(claims, groups, "data/output/sources.json")
    
    print("\n   Output files generated:")
    print("   - data/output/digest.md")
    print("   - data/output/sources.json")
    print("\n" + "=" * 50)


if __name__ == "__main__":
    main()
