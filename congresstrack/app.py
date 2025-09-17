import streamlit as st
import json
import os
import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional
import requests
from bs4 import BeautifulSoup
from dataclasses import dataclass
from dotenv import load_dotenv
import plotly.express as px
import plotly.graph_objects as go
from collections import Counter

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

    def search_campaign_website(
        self, sponsor_name: str, sponsor_state: str
    ) -> Optional[str]:
        """Search for campaign website using web search"""
        try:
            # Import duckduckgo search
            try:
                from ddgs import DDGS
            except ImportError:
                st.warning(
                    "duckduckgo-search not installed. Please install it with: pip install duckduckgo-search"
                )
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
            st.warning(f"Failed to search for campaign website: {e}")
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


class SponsorAnalyzer:
    """Analyzes sponsor data and creates visualizations"""

    def __init__(self, laws: List[LawData]):
        self.laws = laws

    def get_sponsor_counts(self) -> Dict[str, int]:
        """Count laws per sponsor"""
        sponsor_counts = Counter()
        for law in self.laws:
            sponsor_counts[law.sponsor_name] += 1
        return dict(sponsor_counts)

    def get_sponsor_dataframe(self) -> pd.DataFrame:
        """Create a DataFrame with sponsor information and law counts"""
        sponsor_data = []
        sponsor_counts = self.get_sponsor_counts()

        for law in self.laws:
            sponsor_data.append(
                {
                    "sponsor_name": law.sponsor_name,
                    "sponsor_state": law.sponsor_state,
                    "sponsor_bioguide_id": law.sponsor_bioguide_id,
                    "origin_chamber": law.origin_chamber,
                    "law_count": sponsor_counts[law.sponsor_name],
                    "congress": law.congress,
                }
            )

        # Remove duplicates and sort by law count
        df = pd.DataFrame(sponsor_data).drop_duplicates(subset=["sponsor_name"])
        return df.sort_values("law_count", ascending=False)

    def create_bar_chart(self, df: pd.DataFrame, top_n: int = 20) -> go.Figure:
        """Create a bar chart of top sponsors by law count"""
        top_sponsors = df.head(top_n)

        fig = px.bar(
            top_sponsors,
            x="law_count",
            y="sponsor_name",
            orientation="h",
            title=f"Top {top_n} Congressional Members by Number of Laws Sponsored",
            labels={
                "law_count": "Number of Laws Sponsored",
                "sponsor_name": "Congressional Member",
            },
            color="law_count",
            color_continuous_scale="Blues",
        )

        fig.update_layout(
            height=max(400, len(top_sponsors) * 25),
            yaxis={"categoryorder": "total ascending"},
            showlegend=False,
        )

        return fig

    def create_chamber_comparison(self, df: pd.DataFrame) -> go.Figure:
        """Create a comparison chart between House and Senate"""
        chamber_counts = df.groupby("origin_chamber")["law_count"].sum().reset_index()

        fig = px.pie(
            chamber_counts,
            values="law_count",
            names="origin_chamber",
            title="Laws Sponsored by Chamber",
            color_discrete_map={"H": "#1f77b4", "S": "#ff7f0e"},
        )

        return fig

    def create_state_analysis(self, df: pd.DataFrame) -> go.Figure:
        """Create a chart showing laws by state"""
        state_counts = df.groupby("sponsor_state")["law_count"].sum().reset_index()
        state_counts = state_counts.sort_values("law_count", ascending=False).head(15)

        fig = px.bar(
            state_counts,
            x="sponsor_state",
            y="law_count",
            title="Top 15 States by Total Laws Sponsored",
            labels={"law_count": "Number of Laws Sponsored", "sponsor_state": "State"},
            color="law_count",
            color_continuous_scale="Viridis",
        )

        fig.update_layout(xaxis_tickangle=-45)
        return fig


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
                    # temperature=0.3,
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


def show_sponsor_visualization_page():
    """Display the sponsor visualization page as a leaderboard"""
    # Custom CSS for leaderboard styling
    st.markdown(
        """
    <style>
    .leaderboard-header {
        background: linear-gradient(90deg, #1e3c72 0%, #2a5298 100%);
        padding: 2rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
    }
    .leaderboard-title {
        font-size: 3rem;
        font-weight: bold;
        margin-bottom: 0.5rem;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
    }
    .leaderboard-subtitle {
        font-size: 1.2rem;
        opacity: 0.9;
    }
    .rank-card {
        background: white;
        border-radius: 10px;
        padding: 1rem;
        margin: 0.5rem 0;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        border-left: 5px solid;
        transition: transform 0.2s;
    }
    .rank-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 20px rgba(0,0,0,0.15);
    }
    .rank-1 { border-left-color: #FFD700; }
    .rank-2 { border-left-color: #C0C0C0; }
    .rank-3 { border-left-color: #CD7F32; }
    .rank-other { border-left-color: #4CAF50; }
    .rank-number {
        font-size: 2rem;
        font-weight: bold;
        color: #333;
        display: inline-block;
        width: 60px;
        text-align: center;
    }
    .sponsor-name {
        font-size: 1.3rem;
        font-weight: bold;
        color: #2c3e50;
        margin-bottom: 0.3rem;
    }
    .sponsor-details {
        color: #7f8c8d;
        font-size: 0.9rem;
    }
    .law-count {
        font-size: 2rem;
        font-weight: bold;
        color: #e74c3c;
        text-align: right;
    }
    .medal {
        font-size: 1.5rem;
        margin-right: 0.5rem;
    }
    .stats-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 10px;
        text-align: center;
        margin: 0.5rem 0;
    }
    .stats-number {
        font-size: 2.5rem;
        font-weight: bold;
        margin-bottom: 0.5rem;
    }
    .stats-label {
        font-size: 1rem;
        opacity: 0.9;
    }
    </style>
    """,
        unsafe_allow_html=True,
    )

    # Leaderboard header
    st.markdown(
        """
    <div class="leaderboard-header">
        <div class="leaderboard-title">🏆 Congressional Leaderboard</div>
        <div class="leaderboard-subtitle">Most Active Law Sponsors in Congress</div>
    </div>
    """,
        unsafe_allow_html=True,
    )

    # Initialize components
    loader = LawDataLoader()

    # Load laws
    with st.spinner("Loading law data..."):
        laws = loader.load_all_laws()

    if not laws:
        st.error("No law data found. Please check the data directory.")
        return

    # Initialize sponsor analyzer
    analyzer = SponsorAnalyzer(laws)
    sponsor_df = analyzer.get_sponsor_dataframe()

    # Configuration options
    st.sidebar.header("🏆 Leaderboard Options")
    top_n = st.sidebar.slider("Number of leaders to show", 5, 50, 15)
    chamber_filter = st.sidebar.selectbox("Filter by Chamber", ["All", "H", "S"])
    show_charts = st.sidebar.checkbox("Show additional charts", False)

    # Filter data
    if chamber_filter != "All":
        filtered_df = sponsor_df[sponsor_df["origin_chamber"] == chamber_filter].copy()
    else:
        filtered_df = sponsor_df.copy()

    # Add ranking
    filtered_df = filtered_df.reset_index(drop=True)
    filtered_df["rank"] = filtered_df.index + 1

    # Summary statistics in cards
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown(
            f"""
        <div class="stats-card">
            <div class="stats-number">{len(laws)}</div>
            <div class="stats-label">Total Laws</div>
        </div>
        """,
            unsafe_allow_html=True,
        )

    with col2:
        st.markdown(
            f"""
        <div class="stats-card">
            <div class="stats-number">{len(filtered_df)}</div>
            <div class="stats-label">Active Sponsors</div>
        </div>
        """,
            unsafe_allow_html=True,
        )

    with col3:
        top_sponsor = filtered_df.iloc[0]["sponsor_name"]
        st.markdown(
            f"""
        <div class="stats-card">
            <div class="stats-number">🥇</div>
            <div class="stats-label">{top_sponsor}</div>
        </div>
        """,
            unsafe_allow_html=True,
        )

    with col4:
        max_laws = filtered_df.iloc[0]["law_count"]
        st.markdown(
            f"""
        <div class="stats-card">
            <div class="stats-number">{max_laws}</div>
            <div class="stats-label">Max Laws</div>
        </div>
        """,
            unsafe_allow_html=True,
        )

    # Main leaderboard
    st.markdown("## 🏆 Top Performers")

    # Display top performers as cards
    top_performers = filtered_df.head(top_n)

    for idx, row in top_performers.iterrows():
        rank = row["rank"]
        name = row["sponsor_name"]
        state = row["sponsor_state"]
        chamber = row["origin_chamber"]
        law_count = row["law_count"]

        # Determine medal and styling
        if rank == 1:
            medal = "🥇"
            rank_class = "rank-1"
        elif rank == 2:
            medal = "🥈"
            rank_class = "rank-2"
        elif rank == 3:
            medal = "🥉"
            rank_class = "rank-3"
        else:
            medal = f"#{rank}"
            rank_class = "rank-other"

        # Chamber icon
        chamber_icon = "🏛️" if chamber == "H" else "🏛️"
        chamber_name = "House" if chamber == "H" else "Senate"

        st.markdown(
            f"""
        <div class="rank-card {rank_class}">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div style="display: flex; align-items: center;">
                    <div class="rank-number">{medal}</div>
                    <div>
                        <div class="sponsor-name">{name}</div>
                        <div class="sponsor-details">{chamber_icon} {chamber_name} • {state}</div>
                    </div>
                </div>
                <div class="law-count">{law_count}</div>
            </div>
        </div>
        """,
            unsafe_allow_html=True,
        )

    # Additional charts (optional)
    if show_charts:
        st.markdown("## 📊 Additional Analytics")

        col1, col2 = st.columns(2)

        with col1:
            st.subheader("📈 Top Performers Chart")
            bar_chart = analyzer.create_bar_chart(filtered_df, top_n)
            st.plotly_chart(bar_chart, use_container_width=True)

        with col2:
            st.subheader("🏛️ Chamber Distribution")
            chamber_chart = analyzer.create_chamber_comparison(filtered_df)
            st.plotly_chart(chamber_chart, use_container_width=True)

        st.subheader("🗺️ State Leaders")
        state_chart = analyzer.create_state_analysis(filtered_df)
        st.plotly_chart(state_chart, use_container_width=True)

    # Achievement badges
    st.markdown("## 🏅 Achievement Badges")

    col1, col2, col3 = st.columns(3)

    with col1:
        # Most active overall
        most_active = filtered_df.iloc[0]
        st.markdown(
            f"""
        <div class="rank-card rank-1">
            <div style="text-align: center;">
                <div style="font-size: 2rem;">👑</div>
                <div class="sponsor-name">Most Active</div>
                <div class="sponsor-details">{most_active["sponsor_name"]}</div>
                <div class="law-count">{most_active["law_count"]} laws</div>
            </div>
        </div>
        """,
            unsafe_allow_html=True,
        )

    with col2:
        # House leader
        house_df = filtered_df[filtered_df["origin_chamber"] == "H"]
        if not house_df.empty:
            house_leader = house_df.iloc[0]
            st.markdown(
                f"""
            <div class="rank-card rank-2">
                <div style="text-align: center;">
                    <div style="font-size: 2rem;">🏛️</div>
                    <div class="sponsor-name">House Leader</div>
                    <div class="sponsor-details">{house_leader["sponsor_name"]}</div>
                    <div class="law-count">{house_leader["law_count"]} laws</div>
                </div>
            </div>
            """,
                unsafe_allow_html=True,
            )

    with col3:
        # Senate leader
        senate_df = filtered_df[filtered_df["origin_chamber"] == "S"]
        if not senate_df.empty:
            senate_leader = senate_df.iloc[0]
            st.markdown(
                f"""
            <div class="rank-card rank-3">
                <div style="text-align: center;">
                    <div style="font-size: 2rem;">🏛️</div>
                    <div class="sponsor-name">Senate Leader</div>
                    <div class="sponsor-details">{senate_leader["sponsor_name"]}</div>
                    <div class="law-count">{senate_leader["law_count"]} laws</div>
                </div>
            </div>
            """,
                unsafe_allow_html=True,
            )

    # Download option
    st.markdown("## 📥 Download Data")
    csv = filtered_df.to_csv(index=False)
    st.download_button(
        label="📊 Download Leaderboard as CSV",
        data=csv,
        file_name="congressional_leaderboard.csv",
        mime="text/csv",
    )


def show_law_analysis_page():
    """Display the original law analysis page"""
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
            # Get website URL - either from data or search for it
            website_url = selected_law.sponsor_website

            if not website_url:
                st.info(
                    "No website found in law data. Searching for campaign website..."
                )
                website_url = scraper.search_campaign_website(
                    selected_law.sponsor_name, selected_law.sponsor_state
                )

                if website_url:
                    st.success(f"Found campaign website: {website_url}")
                else:
                    st.warning("Could not find campaign website")

            # Scrape website if available
            website_content = ""
            if website_url:
                website_content = scraper.scrape_website(website_url)

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
        st.dataframe(actions_df[["actionDate", "text", "type"]], width="stretch")
    else:
        st.write("No actions data available")


def main():
    st.set_page_config(
        page_title="Congressional Law Analysis",
        page_icon="🏛️",
        layout="wide",
    )

    # Sidebar navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.selectbox(
        "Choose a page:", ["Law vs Campaign Analysis", "Sponsor Visualization"]
    )

    if page == "Law vs Campaign Analysis":
        show_law_analysis_page()
    elif page == "Sponsor Visualization":
        show_sponsor_visualization_page()


if __name__ == "__main__":
    main()
