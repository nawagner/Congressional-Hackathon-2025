import requests
from dataclasses import dataclass, asdict
from typing import List, Optional, Dict
from bs4 import BeautifulSoup
from tqdm import tqdm
import os
import json
import re
from dotenv import load_dotenv

api_key = "0iVKSDmfcvLekS1QjsJRqpUaztocZ2eSFJD5gi29"
params = {"api_key": api_key, "format": "json", "limit": 50}
url = "https://api.congress.gov/v3/law/119"


@dataclass
class CampaignObjectives:
    """Data structure for campaign objectives"""

    sponsor_name: str
    objectives: List[str]
    source: str  # 'website', 'social_media', 'manual'
    confidence_score: float
    source_url: Optional[str] = None
    references: List[str] = None

    def __post_init__(self):
        if self.references is None:
            self.references = []


@dataclass
class Law:
    title: str
    sponsor: List[str]
    actions: List[dict]
    text: str
    originChamberCode: str
    congress: int
    number: int
    # Analysis results
    campaign_objectives: Optional[CampaignObjectives] = None
    alignment_score: Optional[float] = None
    supporting_objectives: Optional[List[str]] = None
    conflicting_objectives: Optional[List[str]] = None
    analysis: Optional[str] = None
    detailed_assessment: Optional[str] = None
    law_citations: Optional[List[str]] = None

    def __post_init__(self):
        if self.supporting_objectives is None:
            self.supporting_objectives = []
        if self.conflicting_objectives is None:
            self.conflicting_objectives = []
        if self.law_citations is None:
            self.law_citations = []

    def to_json(self) -> str:
        import json

        return json.dumps(asdict(self), indent=2)


class CampaignScraper:
    """Scrapes campaign websites and social media for objectives"""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
        )

    def search_campaign_website(
        self, sponsor_name: str, sponsor_state: str
    ) -> Optional[str]:
        """Search for campaign website using web search"""
        try:
            # Import duckduckgo search
            try:
                from ddgs import DDGS
            except ImportError:
                print("duckduckgo-search not installed. Skipping website search.")
                return None

            # Create search query
            search_query = f"{sponsor_name} {sponsor_state} campaign website official"

            # Perform web search
            with DDGS() as ddgs:
                search_results = list(ddgs.text(search_query, max_results=5))

            # Extract URLs from search results
            urls = []
            for result in search_results:
                if "href" in result:
                    urls.append(result["href"])

            # Try to find the most likely campaign website
            for url in urls:
                # Look for common campaign website patterns
                if any(
                    pattern in url.lower()
                    for pattern in [
                        "campaign",
                        "elect",
                        "vote",
                        "senate.gov",
                        "house.gov",
                        sponsor_name.lower().replace(" ", ""),
                        sponsor_name.lower().replace(" ", "-"),
                    ]
                ):
                    return url

            # If no obvious campaign site found, return the first result
            return urls[0] if urls else None

        except Exception as e:
            print(f"Failed to search for campaign website: {e}")
            return None

    def scrape_website(self, url: str) -> Optional[str]:
        """Scrape content from a campaign website"""
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, "html.parser")

            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()

            # Get text content
            text = soup.get_text()

            # Clean up text
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = " ".join(chunk for chunk in chunks if chunk)

            return text[:5000]  # Limit to first 5000 characters

        except Exception as e:
            print(f"Failed to scrape {url}: {e}")
            return None


class LLMAnalyzer:
    """Uses LLM to analyze and compare laws against campaign objectives"""

    def __init__(self):
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")

    def analyze_campaign_objectives(
        self, text: str, sponsor_name: str, website_url: Optional[str] = None
    ) -> CampaignObjectives:
        """Use LLM to extract campaign objectives from text"""

        if not self.openai_api_key and not self.anthropic_api_key:
            print("No LLM API key found. Skipping analysis.")
            return CampaignObjectives(
                sponsor_name=sponsor_name,
                objectives=["No API key available"],
                source="manual",
                confidence_score=0.0,
                source_url=website_url,
            )

        prompt = f"""
        Analyze the following campaign website/social media content for {sponsor_name} and extract their main campaign objectives and policy priorities.
        
        Content: {text[:3000]}
        
        Please provide:
        1. A list of 3-5 main campaign objectives
        2. Key policy areas they focus on
        3. Specific issues they want to address
        
        Format your response as a JSON object with this structure:
        {{
            "objectives": ["objective1", "objective2", "objective3"],
            "policy_areas": ["area1", "area2"],
            "key_issues": ["issue1", "issue2"]
        }}
        """

        try:
            if self.openai_api_key:
                import openai

                client = openai.OpenAI(api_key=self.openai_api_key)

                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.3,
                )

                result = response.choices[0].message.content

            elif self.anthropic_api_key:
                import anthropic

                client = anthropic.Anthropic(api_key=self.anthropic_api_key)

                response = client.messages.create(
                    model="claude-3-haiku-20240307",
                    max_tokens=500,
                    messages=[{"role": "user", "content": prompt}],
                )

                result = response.content[0].text

            # Parse JSON response
            json_match = re.search(r"\{.*\}", result, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
                objectives = (
                    data.get("objectives", [])
                    + data.get("policy_areas", [])
                    + data.get("key_issues", [])
                )
                return CampaignObjectives(
                    sponsor_name=sponsor_name,
                    objectives=objectives,
                    source="llm_analysis",
                    confidence_score=0.8,
                    source_url=website_url,
                )
            else:
                # Fallback: extract objectives from text
                objectives = [
                    line.strip()
                    for line in result.split("\n")
                    if line.strip() and not line.startswith("{")
                ]
                return CampaignObjectives(
                    sponsor_name=sponsor_name,
                    objectives=objectives[:5],
                    source="llm_fallback",
                    confidence_score=0.6,
                    source_url=website_url,
                )

        except Exception as e:
            print(f"LLM analysis failed: {e}")
            return CampaignObjectives(
                sponsor_name=sponsor_name,
                objectives=["Analysis failed"],
                source="error",
                confidence_score=0.0,
                source_url=website_url,
            )

    def compare_law_to_objectives(
        self, law: Law, objectives: CampaignObjectives
    ) -> Dict:
        """Compare a law against campaign objectives"""

        if not self.openai_api_key and not self.anthropic_api_key:
            return {
                "alignment_score": 0.0,
                "analysis": "No API key available for analysis",
                "supporting_objectives": [],
                "conflicting_objectives": [],
            }

        prompt = f"""
        Compare the following law against the campaign objectives of {objectives.sponsor_name}.
        
        Law Title: {law.title}
        Law Text: {law.text[:2000]}
        
        Campaign Objectives: {objectives.objectives}
        
        Analyze:
        1. How well does this law align with their campaign objectives? (0-100 score)
        2. Which objectives does this law support?
        3. Which objectives might this law conflict with?
        4. Overall assessment of alignment
        
        Format as JSON:
        {{
            "alignment_score": 85,
            "analysis": "Brief analysis of alignment",
            "supporting_objectives": ["objective1", "objective2"],
            "conflicting_objectives": ["objective3"],
            "detailed_assessment": "Detailed explanation"
        }}
        """

        try:
            if self.openai_api_key:
                import openai

                client = openai.OpenAI(api_key=self.openai_api_key)

                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=800,
                    temperature=0.3,
                )

                result = response.choices[0].message.content

            elif self.anthropic_api_key:
                import anthropic

                client = anthropic.Anthropic(api_key=self.anthropic_api_key)

                response = client.messages.create(
                    model="claude-3-haiku-20240307",
                    max_tokens=800,
                    messages=[{"role": "user", "content": prompt}],
                )

                result = response.content[0].text

            # Parse JSON response
            json_match = re.search(r"\{.*\}", result, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            else:
                return {
                    "alignment_score": 50,
                    "analysis": "Could not parse LLM response",
                    "supporting_objectives": [],
                    "conflicting_objectives": [],
                    "detailed_assessment": result,
                }

        except Exception as e:
            print(f"Comparison analysis failed: {e}")
            return {
                "alignment_score": 0,
                "analysis": f"Analysis failed: {e}",
                "supporting_objectives": [],
                "conflicting_objectives": [],
                "detailed_assessment": "Error occurred during analysis",
            }


# Load environment variables
load_dotenv()

# Initialize components
scraper = CampaignScraper()
analyzer = LLMAnalyzer()

# Get all laws
bills = requests.get(url, params=params).json().get("bills")
print(f"Processing {len(bills)} bills...")

# Get a bill
for bill_0 in tqdm(bills):
    bill = requests.get(bill_0.get("url"), params=params).json().get("bill")
    title = bill.get("title")
    sponsors = bill.get("sponsors")[0]
    originChamberCode = bill.get("originChamberCode")

    # Get member info
    member = requests.get(sponsors.get("url"), params=params).json().get("member")
    party = member.get("partyHistory")[0].get("partyName")
    officialWebsiteUrl = member.get("officialWebsiteUrl")
    # Get most recent term first
    terms = member.get("terms")
    terms.reverse()

    state = member.get("state")
    name = member.get("directOrderName")
    bioguideId = member.get("bioguideId")

    sponsor = {
        "name": name,
        "websiteUrl": officialWebsiteUrl,
        "terms": terms,
        "state": state,
        "bioguideId": bioguideId,
        "party": party,
    }

    number = bill.get("number")
    congress = bill.get("congress")

    # Get Bill actions
    actions = (
        requests.get(bill.get("actions").get("url"), params=params)
        .json()
        .get("actions")
    )
    actions.reverse()

    # Get Bill Text
    text = requests.get(bill.get("textVersions").get("url"), params=params).json()
    formats = text.get("textVersions")[0].get("formats")
    text = next((item for item in formats if item["type"] == "Formatted Text"), None)
    bill_text_raw = requests.get(text.get("url"))
    soup = BeautifulSoup(bill_text_raw.text, "html.parser")
    text = soup.find("pre").get_text().strip()

    # Create law object
    law = Law(title, sponsor, actions, text, originChamberCode, congress, number)

    # Perform campaign objectives analysis
    print(f"  Analyzing campaign objectives for {name}...")

    # Get website URL - either from data or search for it
    website_url = officialWebsiteUrl

    if not website_url:
        print("    No website found in law data. Searching for campaign website...")
        website_url = scraper.search_campaign_website(name, state)

        if website_url:
            print(f"    Found campaign website: {website_url}")
        else:
            print("    Could not find campaign website")

    # Scrape website if available
    website_content = ""
    if website_url:
        website_content = scraper.scrape_website(website_url)

    # Analyze objectives
    if website_content:
        objectives = analyzer.analyze_campaign_objectives(
            website_content, name, website_url
        )
    else:
        objectives = CampaignObjectives(
            sponsor_name=name,
            objectives=["No website content available"],
            source="manual",
            confidence_score=0.0,
            source_url=website_url,
        )

    # Compare law to objectives
    comparison = analyzer.compare_law_to_objectives(law, objectives)

    # Update law object with analysis results
    law.campaign_objectives = objectives
    law.alignment_score = comparison.get("alignment_score", 0)
    law.supporting_objectives = comparison.get("supporting_objectives", [])
    law.conflicting_objectives = comparison.get("conflicting_objectives", [])
    law.analysis = comparison.get("analysis", "")
    law.detailed_assessment = comparison.get("detailed_assessment", "")
    law.law_citations = comparison.get("law_citations", [])

    print(f"    Alignment score: {law.alignment_score}")

    # Small delay to avoid rate limiting
    import time

    time.sleep(1)

    with open(f"data/{originChamberCode}.{congress}.{number}.json", "w") as f:
        f.write(law.to_json())
