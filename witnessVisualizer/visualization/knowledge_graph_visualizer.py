#!/usr/bin/env python3

import json
import networkx as nx
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
from typing import Dict, List, Any, Tuple
import argparse
from collections import defaultdict, Counter
import numpy as np

class WitnessKnowledgeGraphVisualizer:
    """Creates interactive knowledge graphs from witness data"""
    
    def __init__(self, data_file: str):
        with open(data_file, 'r') as f:
            self.data = json.load(f)
        
        self.witnesses = self.data.get('witnesses', [])
        self.committees = self.data.get('committees', [])
        self.hearings = self.data.get('hearings', [])
        self.organizations = self.data.get('organizations', [])
        
        # Create NetworkX graph
        self.graph = nx.Graph()
        self._build_graph()
    
    def _build_graph(self):
        """Build the knowledge graph from witness data"""
        
        # Add witness nodes
        for witness in self.witnesses:
            self.graph.add_node(
                witness['id'],
                type='witness',
                name=witness['name'],
                title=witness.get('title', ''),
                organization=witness.get('organization', ''),
                topics=witness.get('topics', []),
                hearing_id=witness.get('hearing_id', ''),
                size=10 + witness.get('documents', 0) * 2  # Size based on document count
            )
        
        # Add committee nodes
        for committee in self.committees:
            self.graph.add_node(
                f"committee_{committee['code']}",
                type='committee',
                name=committee['name'],
                size=15
            )
        
        # Add topic nodes
        all_topics = set()
        for witness in self.witnesses:
            all_topics.update(witness.get('topics', []))
        
        for topic in all_topics:
            self.graph.add_node(
                f"topic_{topic}",
                type='topic',
                name=topic.replace('_', ' ').title(),
                size=8
            )
        
        # Add organization nodes
        all_orgs = set()
        for witness in self.witnesses:
            if witness.get('organization'):
                all_orgs.add(witness['organization'])
        
        for org in all_orgs:
            self.graph.add_node(
                f"org_{org}",
                type='organization',
                name=org,
                size=12
            )
        
        # Add edges
        self._add_witness_relationships()
        self._add_topic_relationships()
        self._add_organization_relationships()
        self._add_committee_relationships()
    
    def _add_witness_relationships(self):
        """Add edges between witnesses who appeared in same hearings"""
        hearing_witnesses = defaultdict(list)
        
        for witness in self.witnesses:
            hearing_id = witness.get('hearing_id')
            if hearing_id:
                hearing_witnesses[hearing_id].append(witness['id'])
        
        # Connect witnesses who appeared in same hearings
        for hearing_id, witness_ids in hearing_witnesses.items():
            for i, w1 in enumerate(witness_ids):
                for w2 in witness_ids[i+1:]:
                    self.graph.add_edge(w1, w2, 
                                      relationship='testified_together',
                                      weight=1.0)
    
    def _add_topic_relationships(self):
        """Add edges between witnesses and topics"""
        for witness in self.witnesses:
            witness_id = witness['id']
            for topic in witness.get('topics', []):
                topic_id = f"topic_{topic}"
                if self.graph.has_node(topic_id):
                    self.graph.add_edge(witness_id, topic_id,
                                      relationship='testified_about',
                                      weight=0.8)
    
    def _add_organization_relationships(self):
        """Add edges between witnesses and organizations"""
        for witness in self.witnesses:
            if witness.get('organization'):
                org_id = f"org_{witness['organization']}"
                if self.graph.has_node(org_id):
                    self.graph.add_edge(witness['id'], org_id,
                                      relationship='works_for',
                                      weight=0.9)
    
    def _add_committee_relationships(self):
        """Add edges between witnesses and committees"""
        hearing_to_committee = {}
        for hearing in self.hearings:
            hearing_to_committee[hearing['id']] = hearing.get('committee', '')
        
        for witness in self.witnesses:
            hearing_id = witness.get('hearing_id')
            if hearing_id and hearing_id in hearing_to_committee:
                committee_name = hearing_to_committee[hearing_id]
                # Find committee code
                committee_id = None
                for committee in self.committees:
                    if committee['name'] == committee_name:
                        committee_id = f"committee_{committee['code']}"
                        break
                
                if committee_id and self.graph.has_node(committee_id):
                    self.graph.add_edge(witness['id'], committee_id,
                                      relationship='appeared_before',
                                      weight=0.7)
    
    def create_interactive_plotly_graph(self, output_file: str = 'witness_knowledge_graph.html'):
        """Create an interactive Plotly visualization"""
        
        # Use spring layout for positioning
        pos = nx.spring_layout(self.graph, k=3, iterations=50)
        
        # Prepare node data
        node_data = defaultdict(list)
        
        for node_id, data in self.graph.nodes(data=True):
            x, y = pos[node_id]
            node_data['x'].append(x)
            node_data['y'].append(y)
            node_data['id'].append(node_id)
            node_data['name'].append(data.get('name', node_id))
            node_data['type'].append(data.get('type', 'unknown'))
            node_data['size'].append(data.get('size', 8))
            
            # Create hover text
            hover_text = f"<b>{data.get('name', node_id)}</b><br>"
            hover_text += f"Type: {data.get('type', 'unknown')}<br>"
            
            if data.get('type') == 'witness':
                hover_text += f"Title: {data.get('title', '')}<br>"
                hover_text += f"Organization: {data.get('organization', '')}<br>"
                hover_text += f"Topics: {', '.join(data.get('topics', []))}<br>"
            
            node_data['hover'].append(hover_text)
        
        # Prepare edge data
        edge_x, edge_y = [], []
        for edge in self.graph.edges():
            x0, y0 = pos[edge[0]]
            x1, y1 = pos[edge[1]]
            edge_x.extend([x0, x1, None])
            edge_y.extend([y0, y1, None])
        
        # Create the plot
        fig = go.Figure()
        
        # Add edges
        fig.add_trace(go.Scatter(
            x=edge_x, y=edge_y,
            line=dict(width=0.5, color='#888'),
            hoverinfo='none',
            mode='lines',
            name='Connections'
        ))
        
        # Color mapping for node types
        color_map = {
            'witness': '#FF6B6B',
            'committee': '#4ECDC4',
            'topic': '#45B7D1',
            'organization': '#96CEB4'
        }
        
        # Add nodes by type
        for node_type in ['witness', 'committee', 'topic', 'organization']:
            type_indices = [i for i, t in enumerate(node_data['type']) if t == node_type]
            if type_indices:
                fig.add_trace(go.Scatter(
                    x=[node_data['x'][i] for i in type_indices],
                    y=[node_data['y'][i] for i in type_indices],
                    mode='markers',
                    marker=dict(
                        size=[node_data['size'][i] for i in type_indices],
                        color=color_map.get(node_type, '#888'),
                        line=dict(width=2, color='DarkSlateGrey')
                    ),
                    text=[node_data['name'][i] for i in type_indices],
                    hovertext=[node_data['hover'][i] for i in type_indices],
                    hoverinfo='text',
                    textposition="middle center",
                    name=node_type.title()
                ))
        
        # Update layout
        fig.update_layout(
            title={
                'text': 'Congressional Witness Knowledge Graph',
                'x': 0.5,
                'xanchor': 'center',
                'font': {'size': 20}
            },
            showlegend=True,
            hovermode='closest',
            margin=dict(b=20,l=5,r=5,t=40),
            annotations=[ dict(
                text="Interactive visualization of Congressional witnesses, committees, topics, and organizations",
                showarrow=False,
                xref="paper", yref="paper",
                x=0.005, y=-0.002,
                xanchor='left', yanchor='bottom',
                font=dict(color='#888', size=12)
            )],
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            plot_bgcolor='white'
        )
        
        # Save the plot
        fig.write_html(output_file)
        print(f"Interactive graph saved to {output_file}")
        
        return fig
    
    def create_analysis_dashboard(self, output_file: str = 'witness_analysis_dashboard.html'):
        """Create a comprehensive analysis dashboard"""
        
        # Prepare data for analysis
        witness_df = pd.DataFrame(self.witnesses)
        
        # Create subplots
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=('Witness Types Distribution', 'Top Organizations', 
                          'Topic Frequency', 'Committee Activity'),
            specs=[[{"type": "pie"}, {"type": "bar"}],
                   [{"type": "bar"}, {"type": "bar"}]]
        )
        
        # 1. Witness Types Distribution
        if 'type' in witness_df.columns:
            type_counts = witness_df['type'].value_counts()
            fig.add_trace(go.Pie(
                labels=type_counts.index,
                values=type_counts.values,
                name="Witness Types"
            ), row=1, col=1)
        
        # 2. Top Organizations
        if 'organization' in witness_df.columns:
            org_counts = witness_df[witness_df['organization'].notna()]['organization'].value_counts().head(10)
            fig.add_trace(go.Bar(
                x=org_counts.values,
                y=org_counts.index,
                orientation='h',
                name="Organizations"
            ), row=1, col=2)
        
        # 3. Topic Frequency
        all_topics = []
        for witness in self.witnesses:
            all_topics.extend(witness.get('topics', []))
        topic_counts = pd.Series(all_topics).value_counts().head(10)
        
        fig.add_trace(go.Bar(
            x=topic_counts.index,
            y=topic_counts.values,
            name="Topics"
        ), row=2, col=1)
        
        # 4. Committee Activity
        committee_counts = pd.Series([h.get('committee', '') for h in self.hearings]).value_counts().head(5)
        fig.add_trace(go.Bar(
            x=committee_counts.index,
            y=committee_counts.values,
            name="Committees"
        ), row=2, col=2)
        
        # Update layout
        fig.update_layout(
            title_text="Congressional Witness Analysis Dashboard",
            showlegend=False,
            height=800
        )
        
        # Rotate x-axis labels for readability
        fig.update_xaxes(tickangle=45, row=2, col=1)
        fig.update_xaxes(tickangle=45, row=2, col=2)
        
        # Save the dashboard
        fig.write_html(output_file)
        print(f"Analysis dashboard saved to {output_file}")
        
        return fig
    
    def generate_summary_report(self) -> str:
        """Generate a text summary of the knowledge graph"""
        
        report = f"""
Congressional Witness Knowledge Graph Analysis
============================================

Dataset Overview:
- Total Witnesses: {len(self.witnesses)}
- Total Committees: {len(self.committees)}
- Total Hearings: {len(self.hearings)}
- Total Organizations: {len(self.organizations)}

Graph Statistics:
- Nodes: {self.graph.number_of_nodes()}
- Edges: {self.graph.number_of_edges()}
- Average Degree: {sum(dict(self.graph.degree()).values()) / len(self.graph.nodes()):.2f}

Network Analysis:
- Graph Density: {nx.density(self.graph):.4f}
- Number of Connected Components: {nx.number_connected_components(self.graph)}

Top Topics by Witness Count:
"""
        
        # Topic analysis
        all_topics = []
        for witness in self.witnesses:
            all_topics.extend(witness.get('topics', []))
        topic_counts = Counter(all_topics)
        
        for topic, count in topic_counts.most_common(10):
            report += f"- {topic.replace('_', ' ').title()}: {count} witnesses\n"
        
        # Organization analysis
        report += "\nTop Organizations by Witness Count:\n"
        org_counts = Counter(w.get('organization', 'Unknown') for w in self.witnesses if w.get('organization'))
        
        for org, count in org_counts.most_common(10):
            report += f"- {org}: {count} witnesses\n"
        
        # Network centrality
        centrality = nx.degree_centrality(self.graph)
        top_central = sorted(centrality.items(), key=lambda x: x[1], reverse=True)[:10]
        
        report += "\nMost Connected Entities (by degree centrality):\n"
        for node_id, centrality_score in top_central:
            node_data = self.graph.nodes[node_id]
            report += f"- {node_data.get('name', node_id)} ({node_data.get('type', 'unknown')}): {centrality_score:.3f}\n"
        
        return report

def main():
    """Main function to run the visualizer"""
    parser = argparse.ArgumentParser(description='Generate knowledge graph visualizations from witness data')
    parser.add_argument('data_file', help='JSON file containing scraped witness data')
    parser.add_argument('--output-graph', default='witness_knowledge_graph.html', 
                       help='Output file for interactive graph')
    parser.add_argument('--output-dashboard', default='witness_analysis_dashboard.html',
                       help='Output file for analysis dashboard')
    parser.add_argument('--output-report', default='witness_analysis_report.txt',
                       help='Output file for summary report')
    
    args = parser.parse_args()
    
    # Create visualizer
    visualizer = WitnessKnowledgeGraphVisualizer(args.data_file)
    
    # Generate visualizations
    print("Creating interactive knowledge graph...")
    visualizer.create_interactive_plotly_graph(args.output_graph)
    
    print("Creating analysis dashboard...")
    visualizer.create_analysis_dashboard(args.output_dashboard)
    
    print("Generating summary report...")
    report = visualizer.generate_summary_report()
    with open(args.output_report, 'w') as f:
        f.write(report)
    print(f"Summary report saved to {args.output_report}")
    
    print("\nVisualization complete!")
    print(f"Graph nodes: {visualizer.graph.number_of_nodes()}")
    print(f"Graph edges: {visualizer.graph.number_of_edges()}")

if __name__ == "__main__":
    main()