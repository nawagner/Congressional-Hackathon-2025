#!/usr/bin/env python3

"""
Congressional Witness Visualizer - Main Entry Point

This script provides a command-line interface for all the witness visualizer tools.
"""

import argparse
import sys
import os
from datetime import datetime

def run_scraper(args):
    """Run the House witness scraper"""
    from scrapers.house_witness_scraper import HouseWitnessScraper
    
    scraper = HouseWitnessScraper()
    database = scraper.scrape_all_witnesses(max_events=args.max_events)
    
    # Export to JSON
    output_filename = args.output or f"house_witnesses_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    scraper.export_to_json(output_filename, database)
    
    print(f"Scraping complete!")
    print(f"Total witnesses found: {database.total_witnesses}")
    print(f"Total committees: {len(database.committees)}")
    print(f"Total hearings: {len(database.hearings)}")
    print(f"Data exported to: {output_filename}")

def run_test(args):
    """Run the scraper test"""
    from scrapers.test_scraper import test_scraper
    
    success = test_scraper()
    if success:
        print("✅ All tests passed!")
    else:
        print("❌ Tests failed!")
        sys.exit(1)

def run_visualizer(args):
    """Run the knowledge graph visualizer"""
    from visualization.knowledge_graph_visualizer import WitnessKnowledgeGraphVisualizer
    
    if not os.path.exists(args.data_file):
        print(f"Error: Data file '{args.data_file}' not found")
        sys.exit(1)
    
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
    
    print(f"Visualization complete!")
    print(f"Graph: {args.output_graph}")
    print(f"Dashboard: {args.output_dashboard}")
    print(f"Report: {args.output_report}")

def run_loader(args):
    """Run the Supabase data loader"""
    from database.supabase_loader import SupabaseWitnessLoader
    
    if not args.supabase_url or not args.supabase_key:
        print("Error: SUPABASE_URL and SUPABASE_KEY must be provided")
        print("Set them as environment variables or use --supabase-url and --supabase-key")
        sys.exit(1)
    
    if not os.path.exists(args.data_file):
        print(f"Error: Data file '{args.data_file}' not found")
        sys.exit(1)
    
    loader = SupabaseWitnessLoader(args.supabase_url, args.supabase_key)
    
    print(f"Loading data from {args.data_file} into Supabase...")
    stats = loader.load_from_json(args.data_file, args.notes)
    
    print("\nLoading Statistics:")
    for key, value in stats.items():
        print(f"  {key.title()}: {value}")
    
    print("\nDatabase Statistics:")
    db_stats = loader.get_database_stats()
    for table, count in db_stats.items():
        print(f"  {table}: {count} records")
    
    print("\nData loading complete!")

def run_api(args):
    """Run the FastAPI server"""
    import uvicorn
    from api.witness_api import app
    
    print(f"Starting Congressional Witness API server...")
    print(f"Server will be available at: http://localhost:{args.port}")
    print(f"API documentation: http://localhost:{args.port}/docs")
    
    uvicorn.run(app, host=args.host, port=args.port, reload=args.reload)

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Congressional Witness Visualizer - Tools for scraping and analyzing House witness data",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run scraper to collect witness data
  python main.py scrape --max-events 10 --output my_data.json
  
  # Test the scraper
  python main.py test
  
  # Create visualizations from data
  python main.py visualize my_data.json
  
  # Load data into Supabase
  python main.py load my_data.json --supabase-url "https://xxx.supabase.co" --supabase-key "xxx"
  
  # Start API server
  python main.py api --port 8000
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Scraper command
    scraper_parser = subparsers.add_parser('scrape', help='Run the House witness scraper')
    scraper_parser.add_argument('--max-events', type=int, default=10, 
                               help='Maximum number of events to scrape (default: 10)')
    scraper_parser.add_argument('--output', '-o', 
                               help='Output JSON filename (default: auto-generated)')
    scraper_parser.set_defaults(func=run_scraper)
    
    # Test command
    test_parser = subparsers.add_parser('test', help='Run scraper tests')
    test_parser.set_defaults(func=run_test)
    
    # Visualizer command
    viz_parser = subparsers.add_parser('visualize', help='Create knowledge graph visualizations')
    viz_parser.add_argument('data_file', help='JSON file containing witness data')
    viz_parser.add_argument('--output-graph', default='witness_knowledge_graph.html',
                           help='Output file for interactive graph')
    viz_parser.add_argument('--output-dashboard', default='witness_analysis_dashboard.html',
                           help='Output file for analysis dashboard')
    viz_parser.add_argument('--output-report', default='witness_analysis_report.txt',
                           help='Output file for summary report')
    viz_parser.set_defaults(func=run_visualizer)
    
    # Loader command
    loader_parser = subparsers.add_parser('load', help='Load data into Supabase database')
    loader_parser.add_argument('data_file', help='JSON file containing witness data')
    loader_parser.add_argument('--supabase-url', 
                              default=os.getenv('SUPABASE_URL'),
                              help='Supabase project URL (or set SUPABASE_URL env var)')
    loader_parser.add_argument('--supabase-key',
                              default=os.getenv('SUPABASE_KEY'), 
                              help='Supabase service role key (or set SUPABASE_KEY env var)')
    loader_parser.add_argument('--notes', help='Optional notes for the loading session')
    loader_parser.set_defaults(func=run_loader)
    
    # API command
    api_parser = subparsers.add_parser('api', help='Start the REST API server')
    api_parser.add_argument('--host', default='127.0.0.1', help='Host to bind to')
    api_parser.add_argument('--port', type=int, default=8000, help='Port to bind to')
    api_parser.add_argument('--reload', action='store_true', 
                           help='Enable auto-reload for development')
    api_parser.set_defaults(func=run_api)
    
    # Parse arguments
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    # Run the selected command
    try:
        args.func(args)
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()