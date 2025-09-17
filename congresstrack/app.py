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
    party: str
    # Analysis results (pre-computed)
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

                # Parse campaign objectives if available
                campaign_objectives = None
                if "campaign_objectives" in data and data["campaign_objectives"]:
                    obj_data = data["campaign_objectives"]
                    campaign_objectives = CampaignObjectives(
                        sponsor_name=obj_data.get("sponsor_name", ""),
                        objectives=obj_data.get("objectives", []),
                        source=obj_data.get("source", "manual"),
                        confidence_score=obj_data.get("confidence_score", 0.0),
                        source_url=obj_data.get("source_url"),
                        references=obj_data.get("references", []),
                    )

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
                    # Analysis results (pre-computed)
                    campaign_objectives=campaign_objectives,
                    alignment_score=data.get("alignment_score"),
                    supporting_objectives=data.get("supporting_objectives", []),
                    conflicting_objectives=data.get("conflicting_objectives", []),
                    analysis=data.get("analysis", ""),
                    detailed_assessment=data.get("detailed_assessment", ""),
                    law_citations=data.get("law_citations", []),
                    party=data.get("sponsor", {}).get("party", ""),
                )
                laws.append(law)

            except Exception as e:
                st.error(f"Error loading {json_file}: {e}")

        return laws


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
                    "party": law.party,
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
            color_discrete_map={"H": "#0057b7", "S": "#d7263d"},
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
        color: black;
        margin-bottom: 0.3rem;
    }
    .sponsor-details {
        color: black;
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
    top_n = 50
    chamber_filter = st.sidebar.selectbox(
        "Filter by Chamber", ["All", "House", "Senate"]
    )

    # Filter data
    if chamber_filter != "All":
        chamber_filter = "H" if chamber_filter == "House" else "S"
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
        party = row["party"]

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

        party_highlight = "lightcoral" if party == "Republican" else "lightblue"
        st.markdown(
            f"""
        <div class="rank-card {rank_class}" style="background-color: {party_highlight};">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div style="display: flex; align-items: center;">
                    <div class="rank-number">{medal}</div>
                    <div>
                        <div class="sponsor-name">{name}</div>
                        <div class="sponsor-details">{chamber_icon} {chamber_name} • {state} • {party}</div>
                    </div>
                </div>
                <div class="law-count">{law_count}</div>
            </div>
        </div>
        """,
            unsafe_allow_html=True,
        )

    # Additional charts (optional)
    st.markdown("## 📊 Additional Analytics")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📈 Top Performers Chart")
        bar_chart = analyzer.create_bar_chart(filtered_df, top_n)
        st.plotly_chart(bar_chart, width="stretch")

    with col2:
        st.subheader("🏛️ Chamber Distribution")
        chamber_chart = analyzer.create_chamber_comparison(filtered_df)
        st.plotly_chart(chamber_chart, width="stretch")

    st.subheader("🗺️ State Leaders")
    state_chart = analyzer.create_state_analysis(filtered_df)
    st.plotly_chart(state_chart, width="stretch")

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
    """Display the law analysis page with pre-computed results"""
    st.title("🏛️ Congressional Law vs Campaign Objectives Analyzer")
    st.markdown(
        "View pre-computed analysis of passed laws against sponsors' campaign objectives"
    )

    # Initialize components
    loader = LawDataLoader()

    # Load laws
    with st.spinner("Loading law data..."):
        laws = loader.load_all_laws()

    st.success(f"Loaded {len(laws)} laws from the data directory")

    # Filter laws with analysis data
    analyzed_laws = [law for law in laws if law.alignment_score is not None]
    st.info(f"Found {len(analyzed_laws)} laws with analysis data")

    # Sidebar for configuration
    st.sidebar.header("Configuration")

    # Analysis summary
    if analyzed_laws:
        avg_score = sum(law.alignment_score for law in analyzed_laws) / len(
            analyzed_laws
        )
        st.sidebar.metric("Average Alignment Score", f"{avg_score:.1f}")

        high_alignment = len(
            [law for law in analyzed_laws if law.alignment_score >= 70]
        )
        st.sidebar.metric("High Alignment Laws (≥70)", high_alignment)

    # Law selection
    st.header("Select a Law to View Analysis")

    if analyzed_laws:
        law_options = {
            f"{law.origin_chamber}.{law.congress}.{law.number} ({law.sponsor_name} - {law.party[0]}) - Score: {law.alignment_score}": law
            for law in analyzed_laws
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

        if selected_law.campaign_objectives:
            objectives = selected_law.campaign_objectives

            st.subheader("Extracted Campaign Objectives")
            st.write(f"**Source:** {objectives.source}")
            st.write(f"**Confidence:** {objectives.confidence_score:.2f}")
            if objectives.source_url:
                st.write(f"**Source URL:** {objectives.source_url}")

            for i, objective in enumerate(objectives.objectives, 1):
                st.write(f"{i}. {objective}")
        else:
            st.warning("No campaign objectives data available for this law")

        # Law vs Objectives Comparison
        st.header("Law vs Objectives Comparison")

        # Display comparison results
        col1, col2, col3 = st.columns(3)

        with col1:
            score = selected_law.alignment_score or 0
            if score >= 70:
                st.success(f"**Alignment Score: {score}/100**")
            elif score >= 40:
                st.warning(f"**Alignment Score: {score}/100**")
            else:
                st.error(f"**Alignment Score: {score}/100**")

        with col2:
            st.metric(
                "Supporting Objectives",
                len(selected_law.supporting_objectives or []),
            )

        with col3:
            st.metric(
                "Conflicting Objectives",
                len(selected_law.conflicting_objectives or []),
            )

        # Detailed analysis
        if selected_law.detailed_assessment:
            st.subheader("Detailed Analysis")
            st.write(selected_law.detailed_assessment)
        elif selected_law.analysis:
            st.subheader("Analysis")
            st.write(selected_law.analysis)

        # Supporting objectives
        if selected_law.supporting_objectives:
            st.subheader("✅ Supporting Objectives")
            for obj in selected_law.supporting_objectives:
                st.write(f"• {obj}")

        # Conflicting objectives
        if selected_law.conflicting_objectives:
            st.subheader("❌ Conflicting Objectives")
            for obj in selected_law.conflicting_objectives:
                st.write(f"• {obj}")

        # Law citations
        if selected_law.law_citations:
            st.subheader("📋 Law Citations")
            for citation in selected_law.law_citations:
                st.write(f"• {citation}")

    else:
        st.warning(
            "No laws with analysis data found. Please run the data pipeline first."
        )

    # Law text display
    if analyzed_laws:
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


def show_analysis_summary_page():
    """Display analysis summary and rankings"""
    st.title("📊 Analysis Summary & Rankings")
    st.markdown("Overview of law alignment scores and top performers")

    # Initialize components
    loader = LawDataLoader()

    # Load laws
    with st.spinner("Loading law data..."):
        laws = loader.load_all_laws()

    # Filter laws with analysis data
    analyzed_laws = [law for law in laws if law.alignment_score is not None]

    if not analyzed_laws:
        st.warning(
            "No laws with analysis data found. Please run the data pipeline first."
        )
        return

    st.success(f"Analyzed {len(analyzed_laws)} laws")

    # Summary statistics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        avg_score = sum(law.alignment_score for law in analyzed_laws) / len(
            analyzed_laws
        )
        st.metric("Average Alignment Score", f"{avg_score:.1f}")

    with col2:
        high_alignment = len(
            [law for law in analyzed_laws if law.alignment_score >= 70]
        )
        st.metric("High Alignment (≥70)", high_alignment)

    with col3:
        medium_alignment = len(
            [law for law in analyzed_laws if 40 <= law.alignment_score < 70]
        )
        st.metric("Medium Alignment (40-69)", medium_alignment)

    with col4:
        low_alignment = len([law for law in analyzed_laws if law.alignment_score < 40])
        st.metric("Low Alignment (<40)", low_alignment)

    # Top aligned laws
    st.header("🏆 Top 10 Most Aligned Laws")
    top_laws = sorted(analyzed_laws, key=lambda x: x.alignment_score, reverse=True)[:10]

    for i, law in enumerate(top_laws, 1):
        with st.expander(f"#{i} - {law.title} (Score: {law.alignment_score})"):
            col1, col2 = st.columns(2)

            with col1:
                st.write(f"**Sponsor:** {law.sponsor_name}")
                st.write(f"**State:** {law.sponsor_state}")
                st.write(f"**Chamber:** {law.origin_chamber}")
                st.write(f"**Congress:** {law.congress}")

            with col2:
                st.write(f"**Alignment Score:** {law.alignment_score}")
                st.write(
                    f"**Supporting Objectives:** {len(law.supporting_objectives or [])}"
                )
                st.write(
                    f"**Conflicting Objectives:** {len(law.conflicting_objectives or [])}"
                )

            if law.detailed_assessment:
                st.write("**Analysis:**")
                st.write(law.detailed_assessment)

    # Sponsor rankings by average alignment
    st.header("👥 Sponsor Rankings by Average Alignment")

    sponsor_scores = {}
    sponsor_counts = {}

    for law in analyzed_laws:
        sponsor = law.sponsor_name
        if sponsor not in sponsor_scores:
            sponsor_scores[sponsor] = []
            sponsor_counts[sponsor] = 0
        sponsor_scores[sponsor].append(law.alignment_score)
        sponsor_counts[sponsor] += 1

    sponsor_avg_scores = {
        sponsor: sum(scores) / len(scores)
        for sponsor, scores in sponsor_scores.items()
        if len(scores) >= 2  # Only sponsors with 2+ laws
    }

    if sponsor_avg_scores:
        top_sponsors = sorted(
            sponsor_avg_scores.items(), key=lambda x: x[1], reverse=True
        )[:10]

        for i, (sponsor, avg_score) in enumerate(top_sponsors, 1):
            law_count = sponsor_counts[sponsor]
            st.write(
                f"**#{i} {sponsor}** - Avg Score: {avg_score:.1f} ({law_count} laws)"
            )

    # Alignment distribution chart
    st.header("📈 Alignment Score Distribution")

    scores = [law.alignment_score for law in analyzed_laws]

    fig = px.histogram(
        x=scores,
        nbins=20,
        title="Distribution of Alignment Scores",
        labels={"x": "Alignment Score", "y": "Number of Laws"},
        color_discrete_sequence=["#1f77b4"],
    )

    fig.update_layout(
        xaxis_title="Alignment Score (0-100)",
        yaxis_title="Number of Laws",
        showlegend=False,
    )

    st.plotly_chart(fig, width="stretch")


def main():
    st.set_page_config(
        page_title="Congressional Law Analysis",
        page_icon="🏛️",
        layout="wide",
    )

    # Sidebar navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.selectbox(
        "Choose a page:",
        ["Law vs Campaign Analysis", "Analysis Summary", "Sponsor Visualization"],
    )

    if page == "Law vs Campaign Analysis":
        show_law_analysis_page()
    elif page == "Analysis Summary":
        show_analysis_summary_page()
    elif page == "Sponsor Visualization":
        show_sponsor_visualization_page()


if __name__ == "__main__":
    main()
