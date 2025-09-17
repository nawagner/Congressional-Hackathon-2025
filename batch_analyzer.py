#!/usr/bin/env python3
"""
Batch analyzer for comparing all laws against campaign objectives
"""

import json
import pandas as pd
from app import LawDataLoader, CampaignScraper, LLMAnalyzer, CampaignObjectives
from dotenv import load_dotenv


def analyze_all_laws():
    """Analyze all laws and create a comparison report"""

    load_dotenv()

    # Initialize components
    loader = LawDataLoader()
    scraper = CampaignScraper()
    analyzer = LLMAnalyzer()

    print("Loading all laws...")
    laws = loader.load_all_laws()
    print(f"Loaded {len(laws)} laws")

    results = []

    for i, law in enumerate(laws, 1):
        print(f"Processing {i}/{len(laws)}: {law.title}")

        # Get website URL - either from data or search for it
        website_url = law.sponsor_website

        if not website_url:
            print("  No website found in law data. Searching for campaign website...")
            website_url = scraper.search_campaign_website(
                law.sponsor_name, law.sponsor_state
            )

            if website_url:
                print(f"  Found campaign website: {website_url}")
            else:
                print("  Could not find campaign website")

        # Scrape website if available
        website_content = ""
        if website_url:
            website_content = scraper.scrape_website(website_url)

        # Analyze objectives
        if website_content:
            objectives = analyzer.analyze_campaign_objectives(
                website_content, law.sponsor_name
            )
        else:
            objectives = CampaignObjectives(
                sponsor_name=law.sponsor_name,
                objectives=["No website content available"],
                source="manual",
                confidence_score=0.0,
            )

        # Compare law to objectives
        comparison = analyzer.compare_law_to_objectives(law, objectives)

        # Store results
        result = {
            "law_title": law.title,
            "sponsor_name": law.sponsor_name,
            "sponsor_state": law.sponsor_state,
            "sponsor_website": law.sponsor_website,
            "found_website": website_url,
            "congress": law.congress,
            "number": law.number,
            "origin_chamber": law.origin_chamber,
            "objectives_source": objectives.source,
            "objectives_confidence": objectives.confidence_score,
            "alignment_score": comparison.get("alignment_score", 0),
            "supporting_objectives_count": len(
                comparison.get("supporting_objectives", [])
            ),
            "conflicting_objectives_count": len(
                comparison.get("conflicting_objectives", [])
            ),
            "analysis": comparison.get("analysis", ""),
            "supporting_objectives": comparison.get("supporting_objectives", []),
            "conflicting_objectives": comparison.get("conflicting_objectives", []),
            "detailed_assessment": comparison.get("detailed_assessment", ""),
        }

        results.append(result)

        # Small delay to avoid rate limiting
        import time

        time.sleep(1)

    # Save results
    output_file = "law_campaign_analysis_results.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"Results saved to {output_file}")

    # Create summary DataFrame
    df = pd.DataFrame(results)

    # Summary statistics
    print("\n=== SUMMARY STATISTICS ===")
    print(f"Total laws analyzed: {len(results)}")
    print(f"Average alignment score: {df['alignment_score'].mean():.1f}")
    print(f"Laws with high alignment (≥70): {len(df[df['alignment_score'] >= 70])}")
    print(
        f"Laws with medium alignment (40-69): {len(df[(df['alignment_score'] >= 40) & (df['alignment_score'] < 70)])}"
    )
    print(f"Laws with low alignment (<40): {len(df[df['alignment_score'] < 40])}")

    # Top aligned laws
    print("\n=== TOP 10 MOST ALIGNED LAWS ===")
    top_aligned = df.nlargest(10, "alignment_score")[
        ["law_title", "sponsor_name", "alignment_score"]
    ]
    for _, row in top_aligned.iterrows():
        print(
            f"{row['alignment_score']:.1f} - {row['law_title']} ({row['sponsor_name']})"
        )

    # Save CSV summary
    csv_file = "law_campaign_analysis_summary.csv"
    df.to_csv(csv_file, index=False)
    print(f"\nSummary saved to {csv_file}")

    return results


if __name__ == "__main__":
    analyze_all_laws()
