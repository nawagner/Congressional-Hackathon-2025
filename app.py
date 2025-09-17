import streamlit as st
import json
import os
import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import requests
from bs4 import BeautifulSoup
import time
from dataclasses import dataclass
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


@dataclass
class LawData:
    """Data structure for law information"""

    title: str
    sponsor_name: str
    sponsor_website: Optional[str]
    sponsor_state: str
    sponsor_bioguide_id: str
    law_text: str
    actions: List[Dict]
    congress: int
    number: str
    origin_chamber: str


@dataclass
class CampaignObjectives:
    """Data structure for campaign objectives"""

    sponsor_name: str
    objectives: List[str]
    source: str  # 'website', 'social_media', 'manual'
    confidence_score: float


class LawDataLoader:
    """Loads and parses law data from JSON files"""

    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)

    def load_all_laws(self) -> List[LawData]:
        """Load all law files from the data directory"""
        laws = []

        for json_file in self.data_dir.glob("*.json"):
            try:
                with open(json_file, "r", encoding="utf-8") as f:
                    data = json.load(f)

                law = LawData(
                    title=data.get("title", ""),
                    sponsor_name=data.get("sponsor", {}).get("name", ""),
                    sponsor_website=data.get("sponsor", {}).get("websiteUrl"),
                    sponsor_state=data.get("sponsor", {}).get("state", ""),
                    sponsor_bioguide_id=data.get("sponsor", {}).get("bioguideId", ""),
                    law_text=data.get("text", ""),
                    actions=data.get("actions", []),
                    congress=data.get("congress", 0),
                    number=data.get("number", ""),
                    origin_chamber=data.get("originChamberCode", ""),
                )
                laws.append(law)

            except Exception as e:
                st.error(f"Error loading {json_file}: {e}")

        return laws


class CampaignScraper:
    """Scrapes campaign websites and social media for objectives"""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
        )

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
            st.warning(f"Failed to scrape {url}: {e}")
            return None

    def extract_objectives_from_text(self, text: str) -> List[str]:
        """Extract campaign objectives from scraped text using simple keyword matching"""
        objectives = []

        # Common campaign objective keywords
        objective_keywords = [
            "campaign",
            "platform",
            "priorities",
            "goals",
            "objectives",
            "issues",
            "policy",
            "legislation",
            "support",
            "oppose",
            "fight for",
            "stand for",
            "believe in",
            "commit to",
        ]

        sentences = text.split(".")
        for sentence in sentences:
            sentence = sentence.strip()
            if any(keyword in sentence.lower() for keyword in objective_keywords):
                if len(sentence) > 20 and len(sentence) < 200:  # Reasonable length
                    objectives.append(sentence)

        return objectives[:10]  # Limit to top 10 objectives


class LLMAnalyzer:
    """Uses LLM to analyze and compare laws against campaign objectives"""

    def __init__(self):
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")

    def analyze_campaign_objectives(
        self, text: str, sponsor_name: str
    ) -> CampaignObjectives:
        """Use LLM to extract campaign objectives from text"""

        if not self.openai_api_key and not self.anthropic_api_key:
            st.error(
                "No LLM API key found. Please set OPENAI_API_KEY or ANTHROPIC_API_KEY in your environment."
            )
            return CampaignObjectives(
                sponsor_name=sponsor_name,
                objectives=["No API key available"],
                source="manual",
                confidence_score=0.0,
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
                    model="gpt-5-nano",
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=500,
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
            import re

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
                )

        except Exception as e:
            st.error(f"LLM analysis failed: {e}")
            return CampaignObjectives(
                sponsor_name=sponsor_name,
                objectives=["Analysis failed"],
                source="error",
                confidence_score=0.0,
            )

    def compare_law_to_objectives(
        self, law: LawData, objectives: CampaignObjectives
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
        Law Text: {law.law_text[:2000]}
        
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
            import re

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
            st.error(f"Comparison analysis failed: {e}")
            return {
                "alignment_score": 0,
                "analysis": f"Analysis failed: {e}",
                "supporting_objectives": [],
                "conflicting_objectives": [],
                "detailed_assessment": "Error occurred during analysis",
            }


def main():
    st.set_page_config(
        page_title="Congressional Law vs Campaign Objectives Analyzer",
        page_icon="🏛️",
        layout="wide",
    )

    st.title("🏛️ Congressional Law vs Campaign Objectives Analyzer")
    st.markdown(
        "Compare passed laws against sponsors' campaign objectives using AI analysis"
    )

    # Initialize components
    loader = LawDataLoader()
    scraper = CampaignScraper()
    analyzer = LLMAnalyzer()

    # Load laws
    with st.spinner("Loading law data..."):
        laws = loader.load_all_laws()

    st.success(f"Loaded {len(laws)} laws from the data directory")

    # Sidebar for configuration
    st.sidebar.header("Configuration")

    # API Key status
    has_openai = bool(os.getenv("OPENAI_API_KEY"))
    has_anthropic = bool(os.getenv("ANTHROPIC_API_KEY"))

    if has_openai:
        st.sidebar.success("✅ OpenAI API Key found")
    elif has_anthropic:
        st.sidebar.success("✅ Anthropic API Key found")
    else:
        st.sidebar.error("❌ No LLM API Key found")
        st.sidebar.info("Set OPENAI_API_KEY or ANTHROPIC_API_KEY in your environment")

    # Law selection
    st.header("Select a Law to Analyze")

    law_options = {
        f"{law.origin_chamber}.{law.congress}.{law.number} ({law.sponsor_name})": law
        for law in laws
    }
    selected_law_name = st.selectbox("Choose a law:", list(law_options.keys()))
    selected_law = law_options[selected_law_name]

    # Display law details
    st.subheader("Law Details")
    col1, col2 = st.columns(2)

    with col1:
        st.write(f"**Title:** {selected_law.title}")
        st.write(f"**Sponsor:** {selected_law.sponsor_name}")
        st.write(f"**State:** {selected_law.sponsor_state}")
        st.write(f"**Congress:** {selected_law.congress}")
        st.write(f"**Number:** {selected_law.number}")

    with col2:
        if selected_law.sponsor_website:
            st.write(f"**Website:** {selected_law.sponsor_website}")
        else:
            st.write("**Website:** Not available")
        st.write(f"**Bioguide ID:** {selected_law.sponsor_bioguide_id}")
        st.write(f"**Origin Chamber:** {selected_law.origin_chamber}")

    # Campaign objectives analysis
    st.header("Campaign Objectives Analysis")

    if st.button(
        "Analyze Campaign Objectives", disabled=not (has_openai or has_anthropic)
    ):
        with st.spinner("Analyzing campaign objectives..."):
            # Scrape website if available
            website_content = ""
            if selected_law.sponsor_website:
                website_content = scraper.scrape_website(selected_law.sponsor_website)

            # Use LLM to analyze objectives
            if website_content:
                objectives = analyzer.analyze_campaign_objectives(
                    website_content, selected_law.sponsor_name
                )
            else:
                # Fallback: use law sponsor name for basic analysis
                objectives = CampaignObjectives(
                    sponsor_name=selected_law.sponsor_name,
                    objectives=["No website content available for analysis"],
                    source="manual",
                    confidence_score=0.0,
                )

            st.subheader("Extracted Campaign Objectives")
            st.write(f"**Source:** {objectives.source}")
            st.write(f"**Confidence:** {objectives.confidence_score:.2f}")

            for i, objective in enumerate(objectives.objectives, 1):
                st.write(f"{i}. {objective}")

            # Compare law to objectives
            st.header("Law vs Objectives Comparison")

            with st.spinner("Comparing law to campaign objectives..."):
                comparison = analyzer.compare_law_to_objectives(
                    selected_law, objectives
                )

            # Display comparison results
            col1, col2, col3 = st.columns(3)

            with col1:
                score = comparison.get("alignment_score", 0)
                if score >= 70:
                    st.success(f"**Alignment Score: {score}/100**")
                elif score >= 40:
                    st.warning(f"**Alignment Score: {score}/100**")
                else:
                    st.error(f"**Alignment Score: {score}/100**")

            with col2:
                st.metric(
                    "Supporting Objectives",
                    len(comparison.get("supporting_objectives", [])),
                )

            with col3:
                st.metric(
                    "Conflicting Objectives",
                    len(comparison.get("conflicting_objectives", [])),
                )

            # Detailed analysis
            st.subheader("Detailed Analysis")
            st.write(
                comparison.get(
                    "detailed_assessment",
                    comparison.get("analysis", "No analysis available"),
                )
            )

            # Supporting objectives
            if comparison.get("supporting_objectives"):
                st.subheader("✅ Supporting Objectives")
                for obj in comparison["supporting_objectives"]:
                    st.write(f"• {obj}")

            # Conflicting objectives
            if comparison.get("conflicting_objectives"):
                st.subheader("❌ Conflicting Objectives")
                for obj in comparison["conflicting_objectives"]:
                    st.write(f"• {obj}")

    # Law text display
    st.header("Law Text")
    with st.expander("View full law text"):
        st.text(selected_law.law_text)

    # Actions timeline
    st.header("Legislative Actions Timeline")
    actions_df = pd.DataFrame(selected_law.actions)
    if not actions_df.empty:
        st.dataframe(
            actions_df[["actionDate", "text", "type"]], use_container_width=True
        )
    else:
        st.write("No actions data available")


if __name__ == "__main__":
    main()
