#!/usr/bin/env python3
"""
Stock Screener - Personal Use
Run: python main.py [strategy_name]
"""

import argparse
import yaml
import logging
import sys
import os
from datetime import datetime
from typing import Dict, List

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from data.futu_client import FutuClient
from data.data_fetcher import DataFetcher
from data.stock_universe import StockUniverse
from screening.filters import StockFilter
from screening.criteria import ScreeningCriteria
from output.excel_export import ExcelReporter
from output.csv_export import CSVExporter

def setup_logging(log_level: str = 'INFO'):
    """Setup logging configuration"""
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('screener.log')
        ]
    )

def load_config(config_path: str = 'config/settings.yaml') -> Dict:
    """Load configuration from YAML file"""
    try:
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    except Exception as e:
        logging.error(f"Failed to load config from {config_path}: {e}")
        raise

def load_strategies(strategies_path: str = 'config/strategies.yaml') -> Dict:
    """Load screening strategies from YAML file"""
    try:
        with open(strategies_path, 'r') as f:
            return yaml.safe_load(f)
    except Exception as e:
        logging.error(f"Failed to load strategies from {strategies_path}: {e}")
        raise

def get_stock_universe(args, stock_universe: StockUniverse, futu_client: FutuClient) -> List[str]:
    """Get the stock universe to screen"""
    
    if args.watchlist:
        # Use specific watchlist
        stocks = stock_universe.get_watchlist(args.watchlist)
        if not stocks:
            logging.warning(f"Watchlist '{args.watchlist}' is empty or not found")
            return []
        logging.info(f"Using watchlist '{args.watchlist}' with {len(stocks)} stocks")
        return stocks
    
    elif args.symbols:
        # Use specific symbols
        stocks = args.symbols.split(',')
        logging.info(f"Using specific symbols: {stocks}")
        return stocks
    
    else:
        # Use market data
        stocks = futu_client.get_stock_list(args.market)
        if args.max_stocks and len(stocks) > args.max_stocks:
            stocks = stocks[:args.max_stocks]
        logging.info(f"Using {len(stocks)} stocks from {args.market} market")
        return stocks

def run_screening(args, settings: Dict, strategies: Dict):
    """Main screening logic"""
    
    logger = logging.getLogger(__name__)
    
    logger.info(f"Starting stock screening - Strategy: {args.strategy}, Market: {args.market}")
    
    # Initialize components
    try:
        futu_client = FutuClient(settings['futu'])
        data_fetcher = DataFetcher(futu_client, settings.get('cache', {}))
        stock_universe = StockUniverse('config/watchlists.yaml')
        criteria_manager = ScreeningCriteria()
        
        # Initialize screener with max workers
        max_workers = min(args.max_workers, 20)  # Limit to prevent API overload
        screener = StockFilter(futu_client, max_workers=max_workers)
        
    except Exception as e:
        logger.error(f"Failed to initialize components: {e}")
        return
    
    # Get stock universe
    stock_list = get_stock_universe(args, stock_universe, futu_client)
    
    if not stock_list:
        logger.error("No stocks to screen")
        return
    
    # Determine strategies to run
    if args.strategy == 'all':
        strategy_list = list(strategies.keys())
    else:
        strategy_list = [s.strip() for s in args.strategy.split(',')]
    
    # Validate strategies
    for strategy_name in strategy_list:
        if strategy_name not in strategies:
            logger.error(f"Strategy '{strategy_name}' not found")
            logger.info(f"Available strategies: {list(strategies.keys())}")
            return
    
    # Run screening
    all_results = {}
    
    for strategy_name in strategy_list:
        logger.info(f"Running strategy: {strategy_name}")
        
        criteria = strategies[strategy_name]
        
        # Validate criteria
        if not criteria_manager.validate_criteria(criteria):
            logger.error(f"Invalid criteria for strategy {strategy_name}")
            continue
        
        # Log criteria description
        logger.info(f"Criteria for {strategy_name}:")
        logger.info(criteria_manager.get_criteria_description(criteria))
        
        try:
            # Apply quick pre-filtering if specified
            filtered_stocks = stock_list
            if args.quick_filter:
                filtered_stocks = screener.quick_screen(
                    stock_list, 
                    min_price=1.0,  # $1 minimum
                    min_volume=100000  # 100k minimum volume
                )
            
            # Run main screening
            results = screener.screen_stocks(
                filtered_stocks, 
                criteria, 
                max_results=args.max_results
            )
            
            all_results[strategy_name] = results
            
            if not results.empty:
                logger.info(f"Strategy '{strategy_name}': {len(results)} stocks found")
                logger.info(f"Top 5 stocks: {results.head()['symbol'].tolist()}")
            else:
                logger.info(f"Strategy '{strategy_name}': No stocks found")
                
        except Exception as e:
            logger.error(f"Error running strategy {strategy_name}: {e}")
            continue
    
    # Generate output
    if any(not df.empty for df in all_results.values()):
        generate_output(all_results, args, settings)
    else:
        logger.warning("No results to export")
    
    # Clean up
    futu_client.close()
    logger.info("Screening completed")

def generate_output(screening_results: Dict, args, settings: Dict):
    """Generate output files"""
    
    logger = logging.getLogger(__name__)
    
    # Create output directory if it doesn't exist
    output_dir = settings['output'].get('save_path', './results/')
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    base_filename = f"stock_screen_{timestamp}"
    
    # Generate reports based on output format
    output_formats = args.output.split(',') if ',' in args.output else [args.output]
    
    for output_format in output_formats:
        output_format = output_format.strip()
        
        if output_format in ['excel', 'both']:
            try:
                excel_reporter = ExcelReporter()
                excel_file = os.path.join(output_dir, f"{base_filename}.xlsx")
                excel_reporter.generate_report(screening_results, excel_file)
                logger.info(f"Excel report saved: {excel_file}")
            except Exception as e:
                logger.error(f"Failed to generate Excel report: {e}")
        
        if output_format in ['csv', 'both']:
            try:
                csv_exporter = CSVExporter()
                csv_exporter.export_screening_results(screening_results, 
                                                    os.path.join(output_dir, base_filename))
                logger.info(f"CSV reports saved in {output_dir}")
            except Exception as e:
                logger.error(f"Failed to generate CSV reports: {e}")
    
    # Generate watchlists if requested
    if args.watchlist_export:
        csv_exporter = CSVExporter()
        for strategy_name, results_df in screening_results.items():
            if not results_df.empty:
                watchlist_file = os.path.join(output_dir, f"{strategy_name}_watchlist_{timestamp}.txt")
                csv_exporter.export_watchlist(results_df, watchlist_file, 'simple')

def main():
    """Main entry point"""
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Stock Screener')
    parser.add_argument('--strategy', default='all', 
                       help='Screening strategy to run (or comma-separated list)')
    parser.add_argument('--market', default='US', 
                       help='Market to screen (US/HK/CN)')
    parser.add_argument('--output', default='excel', 
                       help='Output format (excel/csv/both)')
    parser.add_argument('--watchlist', 
                       help='Use specific watchlist instead of market data')
    parser.add_argument('--symbols', 
                       help='Comma-separated list of specific symbols to screen')
    parser.add_argument('--max-results', type=int, default=50,
                       help='Maximum number of results per strategy')
    parser.add_argument('--max-stocks', type=int, 
                       help='Maximum number of stocks to screen (for testing)')
    parser.add_argument('--max-workers', type=int, default=10,
                       help='Maximum number of parallel workers')
    parser.add_argument('--quick-filter', action='store_true',
                       help='Apply quick pre-filtering to reduce dataset size')
    parser.add_argument('--watchlist-export', action='store_true',
                       help='Export results as watchlist files')
    parser.add_argument('--log-level', default='INFO',
                       help='Logging level (DEBUG/INFO/WARNING/ERROR)')
    parser.add_argument('--config', default='config/settings.yaml',
                       help='Configuration file path')
    parser.add_argument('--strategies-file', default='config/strategies.yaml',
                       help='Strategies file path')
    parser.add_argument('--list-strategies', action='store_true',
                       help='List available strategies and exit')
    parser.add_argument('--list-watchlists', action='store_true',
                       help='List available watchlists and exit')
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.log_level)
    logger = logging.getLogger(__name__)
    
    try:
        # Load configuration
        settings = load_config(args.config)
        strategies = load_strategies(args.strategies_file)
        
        # Handle list commands
        if args.list_strategies:
            print("Available strategies:")
            for strategy_name in strategies.keys():
                print(f"  - {strategy_name}")
            return
        
        if args.list_watchlists:
            stock_universe = StockUniverse('config/watchlists.yaml')
            print("Available watchlists:")
            for watchlist_name in stock_universe.list_watchlists():
                watchlist_info = stock_universe.get_watchlist_info()[watchlist_name]
                print(f"  - {watchlist_name}: {watchlist_info['count']} stocks")
            return
        
        # Run screening
        run_screening(args, settings, strategies)
        
    except KeyboardInterrupt:
        logger.info("Screening interrupted by user")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise

if __name__ == "__main__":
    main()
