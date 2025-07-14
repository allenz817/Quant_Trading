#!/usr/bin/env python3
"""
Daily automated screening script
Schedule and run stock screening automatically
"""

import schedule
import time
import subprocess
import logging
import yaml
import os
from datetime import datetime
from typing import List

def setup_logging():
    """Setup logging for the scheduler"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('scheduler.log')
        ]
    )

def load_schedule_config() -> dict:
    """Load scheduling configuration"""
    try:
        with open('config/settings.yaml', 'r') as f:
            config = yaml.safe_load(f)
            return config.get('schedule', {})
    except Exception as e:
        logging.error(f"Failed to load schedule config: {e}")
        return {}

def run_screening(strategies: List[str] = None, market: str = 'US', output: str = 'both'):
    """Run screening with specified parameters"""
    
    logger = logging.getLogger(__name__)
    
    try:
        strategies_arg = ','.join(strategies) if strategies else 'all'
        
        cmd = [
            'python', 'main.py',
            '--strategy', strategies_arg,
            '--market', market,
            '--output', output,
            '--quick-filter',
            '--watchlist-export',
            '--max-results', '30'
        ]
        
        logger.info(f"Running screening: {' '.join(cmd)}")
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=1800)  # 30 min timeout
        
        if result.returncode == 0:
            logger.info(f"Screening completed successfully")
            # Log some of the output for monitoring
            if result.stdout:
                lines = result.stdout.split('\n')
                for line in lines[-10:]:  # Last 10 lines
                    if line.strip():
                        logger.info(f"Output: {line}")
        else:
            logger.error(f"Screening failed with return code {result.returncode}")
            if result.stderr:
                logger.error(f"Error output: {result.stderr}")
                
    except subprocess.TimeoutExpired:
        logger.error("Screening timed out after 30 minutes")
    except Exception as e:
        logger.error(f"Error running screening: {e}")

def morning_screening():
    """Morning screening routine"""
    logger = logging.getLogger(__name__)
    logger.info("Starting morning screening routine")
    
    # Run momentum and breakout strategies for day trading opportunities
    morning_strategies = ['momentum_breakout', 'oversold_bounce']
    run_screening(strategies=morning_strategies, market='US', output='both')

def midday_screening():
    """Midday screening routine"""
    logger = logging.getLogger(__name__)
    logger.info("Starting midday screening routine")
    
    # Run value and quality strategies for swing trading
    midday_strategies = ['value_stocks', 'quality_growth']
    run_screening(strategies=midday_strategies, market='US', output='csv')

def evening_screening():
    """Evening comprehensive screening"""
    logger = logging.getLogger(__name__)
    logger.info("Starting evening comprehensive screening")
    
    # Run all strategies for comprehensive analysis
    run_screening(strategies=None, market='US', output='both')  # All strategies

def weekly_screening():
    """Weekly comprehensive screening for all markets"""
    logger = logging.getLogger(__name__)
    logger.info("Starting weekly comprehensive screening")
    
    markets = ['US', 'HK']  # Add more markets as needed
    
    for market in markets:
        logger.info(f"Screening {market} market")
        run_screening(strategies=None, market=market, output='both')
        time.sleep(60)  # Wait between markets to avoid API overload

def earnings_season_screening():
    """Special screening during earnings season"""
    logger = logging.getLogger(__name__)
    logger.info("Starting earnings season screening")
    
    # Focus on growth and momentum strategies during earnings
    earnings_strategies = ['growth_stocks', 'momentum_breakout', 'small_cap_rockets']
    run_screening(strategies=earnings_strategies, market='US', output='both')

def setup_schedules():
    """Setup all scheduled tasks"""
    
    schedule_config = load_schedule_config()
    
    # Default schedules
    market_open = schedule_config.get('market_open', "09:35")
    market_close = schedule_config.get('market_close', "16:05")
    evening_time = schedule_config.get('evening_analysis', "18:00")
    
    # Daily schedules
    schedule.every().monday.at(market_open).do(morning_screening)
    schedule.every().tuesday.at(market_open).do(morning_screening)
    schedule.every().wednesday.at(market_open).do(morning_screening)
    schedule.every().thursday.at(market_open).do(morning_screening)
    schedule.every().friday.at(market_open).do(morning_screening)
    
    # Midday screens (less frequent)
    schedule.every().monday.at("12:00").do(midday_screening)
    schedule.every().wednesday.at("12:00").do(midday_screening)
    schedule.every().friday.at("12:00").do(midday_screening)
    
    # Evening comprehensive screening
    schedule.every().day.at(evening_time).do(evening_screening)
    
    # Weekly comprehensive screening
    schedule.every().sunday.at("10:00").do(weekly_screening)
    
    # Special schedules
    # Run earnings season screening during typical earnings months
    # This is a simplified approach - you might want to use a more sophisticated earnings calendar
    schedule.every().day.at("07:00").do(earnings_season_screening).tag('earnings')
    
    logging.info("Schedules configured successfully")

def run_scheduler():
    """Main scheduler loop"""
    
    logger = logging.getLogger(__name__)
    
    logger.info("Starting automated stock screener scheduler")
    logger.info("Configured schedules:")
    
    for job in schedule.jobs:
        logger.info(f"  {job}")
    
    # Run initial screening to test setup
    if not os.path.exists('results'):
        logger.info("Running initial test screening...")
        run_screening(strategies=['value_stocks'], market='US', output='csv')
    
    # Main scheduler loop
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
            
            # Log heartbeat every hour
            if datetime.now().minute == 0:
                logger.info(f"Scheduler running - Next job: {schedule.next_run()}")
                
    except KeyboardInterrupt:
        logger.info("Scheduler stopped by user")
    except Exception as e:
        logger.error(f"Scheduler error: {e}")
        raise

def manual_run():
    """Manual run for testing"""
    
    logger = logging.getLogger(__name__)
    
    import argparse
    
    parser = argparse.ArgumentParser(description='Manual screening run')
    parser.add_argument('--test', action='store_true', help='Run test screening')
    parser.add_argument('--morning', action='store_true', help='Run morning screening')
    parser.add_argument('--evening', action='store_true', help='Run evening screening')
    parser.add_argument('--weekly', action='store_true', help='Run weekly screening')
    
    args = parser.parse_args()
    
    if args.test:
        logger.info("Running test screening")
        run_screening(strategies=['value_stocks'], market='US', output='csv')
    elif args.morning:
        morning_screening()
    elif args.evening:
        evening_screening()
    elif args.weekly:
        weekly_screening()
    else:
        logger.info("No action specified. Use --test, --morning, --evening, or --weekly")

def check_system_status():
    """Check if system is ready for automated screening"""
    
    logger = logging.getLogger(__name__)
    
    # Check if config files exist
    required_files = [
        'config/settings.yaml',
        'config/strategies.yaml',
        'config/watchlists.yaml',
        'main.py'
    ]
    
    for file_path in required_files:
        if not os.path.exists(file_path):
            logger.error(f"Required file missing: {file_path}")
            return False
    
    # Check if results directory exists
    if not os.path.exists('results'):
        os.makedirs('results')
        logger.info("Created results directory")
    
    # Test Futu connection (simplified)
    try:
        result = subprocess.run(['python', 'main.py', '--list-strategies'], 
                              capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            logger.info("System check passed")
            return True
        else:
            logger.error("System check failed - unable to list strategies")
            return False
    except Exception as e:
        logger.error(f"System check failed: {e}")
        return False

if __name__ == "__main__":
    
    setup_logging()
    
    import sys
    
    if len(sys.argv) > 1:
        # Manual run mode
        manual_run()
    else:
        # Automated scheduler mode
        if check_system_status():
            setup_schedules()
            run_scheduler()
        else:
            logging.error("System check failed. Please fix issues before running scheduler.")
            sys.exit(1)
