#!/usr/bin/env python3
"""
Example usage and testing script for the stock screener
"""

import sys
import os
import logging

# Add the stock_screener directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from screening.criteria import ScreeningCriteria
from data.stock_universe import StockUniverse

def example_criteria_usage():
    """Example of how to use screening criteria"""
    
    print("=== Screening Criteria Examples ===\n")
    
    criteria_manager = ScreeningCriteria()
    
    # Get default strategies
    strategies = criteria_manager.get_default_strategies()
    
    print("Available default strategies:")
    for strategy_name in strategies.keys():
        print(f"  - {strategy_name}")
    
    print(f"\nExample strategy (value_stocks):")
    value_strategy = strategies['value_stocks']
    description = criteria_manager.get_criteria_description(value_strategy)
    print(description)
    
    # Create custom criteria
    print(f"\n=== Custom Criteria Example ===")
    custom_criteria = criteria_manager.create_custom_criteria(
        financial_metrics={
            'pe_ratio': {'min': 5, 'max': 20},
            'roe': {'min': 15},
            'debt_to_equity': {'max': 0.5}
        },
        technical_metrics={
            'rsi': {'min': 30, 'max': 70},
            'price_change_1m': {'min': 5}
        },
        market_metrics={
            'market_cap': {'min': 1000000000}  # $1B minimum
        }
    )
    
    print("Custom criteria:")
    print(criteria_manager.get_criteria_description(custom_criteria))
    
    # Available metrics
    print(f"\n=== Available Metrics ===")
    metrics = criteria_manager.get_available_metrics()
    for section, metric_list in metrics.items():
        print(f"\n{section.title()} metrics:")
        for metric in metric_list[:10]:  # Show first 10
            print(f"  - {metric}")
        if len(metric_list) > 10:
            print(f"  ... and {len(metric_list) - 10} more")

def example_watchlist_usage():
    """Example of how to use watchlists"""
    
    print(f"\n=== Watchlist Examples ===\n")
    
    stock_universe = StockUniverse('config/watchlists.yaml')
    
    # List available watchlists
    watchlists = stock_universe.list_watchlists()
    print("Available watchlists:")
    for watchlist_name in watchlists:
        print(f"  - {watchlist_name}")
    
    # Get watchlist info
    print(f"\nWatchlist details:")
    watchlist_info = stock_universe.get_watchlist_info()
    for name, info in watchlist_info.items():
        print(f"  {name}: {info['count']} stocks")
        print(f"    Sample: {', '.join(info['stocks'])}")
    
    # Get specific watchlist
    if 'tech_giants' in watchlists:
        tech_stocks = stock_universe.get_watchlist('tech_giants')
        print(f"\nTech giants watchlist: {tech_stocks}")

def example_command_line_usage():
    """Show example command line usage"""
    
    print(f"\n=== Command Line Usage Examples ===\n")
    
    examples = [
        ("Basic screening", "python main.py"),
        ("Specific strategy", "python main.py --strategy value_stocks"),
        ("Multiple strategies", "python main.py --strategy \"value_stocks,growth_stocks\""),
        ("Use watchlist", "python main.py --strategy momentum_breakout --watchlist tech_giants"),
        ("Hong Kong market", "python main.py --strategy growth_stocks --market HK"),
        ("CSV output only", "python main.py --strategy value_stocks --output csv"),
        ("Limited results", "python main.py --strategy all --max-results 20"),
        ("Quick filtering", "python main.py --strategy momentum_breakout --quick-filter"),
        ("Export watchlists", "python main.py --strategy value_stocks --watchlist-export"),
        ("Specific symbols", "python main.py --symbols \"AAPL,MSFT,GOOGL\" --strategy value_stocks"),
        ("List strategies", "python main.py --list-strategies"),
        ("List watchlists", "python main.py --list-watchlists"),
    ]
    
    for description, command in examples:
        print(f"{description}:")
        print(f"  {command}\n")

def test_configuration():
    """Test if configuration files are properly set up"""
    
    print(f"=== Configuration Test ===\n")
    
    config_files = [
        'config/settings.yaml',
        'config/strategies.yaml',
        'config/watchlists.yaml'
    ]
    
    all_good = True
    
    for config_file in config_files:
        if os.path.exists(config_file):
            print(f"✓ {config_file} exists")
            
            try:
                import yaml
                with open(config_file, 'r') as f:
                    yaml.safe_load(f)
                print(f"✓ {config_file} is valid YAML")
            except Exception as e:
                print(f"✗ {config_file} has YAML errors: {e}")
                all_good = False
        else:
            print(f"✗ {config_file} missing")
            all_good = False
    
    # Test results directory
    if not os.path.exists('results'):
        os.makedirs('results')
        print(f"✓ Created results directory")
    else:
        print(f"✓ Results directory exists")
    
    if all_good:
        print(f"\n✓ All configuration files are properly set up!")
    else:
        print(f"\n✗ Some configuration issues found. Please fix before running.")
    
    return all_good

def create_sample_config():
    """Create sample configuration files if they don't exist"""
    
    print(f"=== Creating Sample Configuration ===\n")
    
    # Check if config directory exists
    if not os.path.exists('config'):
        os.makedirs('config')
        print("Created config directory")
    
    # Sample settings.yaml
    if not os.path.exists('config/settings.yaml'):
        sample_settings = """# Futu API Configuration
futu:
  host: "127.0.0.1"
  port: 11111
  timeout: 10

# Markets to screen
markets:
  - "US"
  - "HK"

# Output settings
output:
  format: ["excel", "csv"]
  save_path: "./results/"
  email_alerts: false

# Data caching
cache:
  enabled: true
  ttl_minutes: 30
"""
        with open('config/settings.yaml', 'w') as f:
            f.write(sample_settings)
        print("Created sample config/settings.yaml")
    
    # Sample strategies.yaml (simplified)
    if not os.path.exists('config/strategies.yaml'):
        sample_strategies = """value_stocks:
  financial:
    pe_ratio: {min: 5, max: 15}
    roe: {min: 12}
    debt_to_equity: {max: 0.5}
  market:
    market_cap: {min: 1000000000}

growth_stocks:
  financial:
    revenue_growth: {min: 15}
    pe_ratio: {max: 30}
  technical:
    price_change_1m: {min: 5}

momentum_breakout:
  technical:
    price_change_1d: {min: 3}
    volume_ratio: {min: 2.0}
    rsi: {min: 60, max: 80}
"""
        with open('config/strategies.yaml', 'w') as f:
            f.write(sample_strategies)
        print("Created sample config/strategies.yaml")
    
    # Sample watchlists.yaml
    if not os.path.exists('config/watchlists.yaml'):
        sample_watchlists = """watchlists:
  tech_giants:
    - "AAPL"
    - "MSFT"
    - "GOOGL"
    - "AMZN"
    - "META"
  
  dow_30:
    - "AAPL"
    - "MSFT"
    - "JNJ"
    - "V"
    - "PG"
  
  custom:
    - "SPY"
    - "QQQ"
"""
        with open('config/watchlists.yaml', 'w') as f:
            f.write(sample_watchlists)
        print("Created sample config/watchlists.yaml")

def main():
    """Main example function"""
    
    print("Stock Screener - Examples and Testing")
    print("=" * 50)
    
    # Create sample config if needed
    create_sample_config()
    
    # Test configuration
    config_ok = test_configuration()
    
    if config_ok:
        # Show examples
        example_criteria_usage()
        example_watchlist_usage()
        example_command_line_usage()
        
        print("=== Next Steps ===\n")
        print("1. Ensure Futu OpenAPI is running")
        print("2. Test with a simple command:")
        print("   python main.py --list-strategies")
        print("3. Run a basic screening:")
        print("   python main.py --strategy value_stocks --max-stocks 10")
        print("4. Check the results/ directory for output files")
        
    else:
        print("Please fix configuration issues before proceeding.")

if __name__ == "__main__":
    main()
