"""
Stock universe management
"""

import yaml
from typing import List, Set
import logging

class StockUniverse:
    def __init__(self, watchlists_config_path: str):
        self.logger = logging.getLogger(__name__)
        self.watchlists = self._load_watchlists(watchlists_config_path)
    
    def _load_watchlists(self, config_path: str) -> dict:
        """Load watchlists from YAML configuration"""
        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
                return config.get('watchlists', {})
        except Exception as e:
            self.logger.error(f"Failed to load watchlists config: {e}")
            return {}
    
    def get_watchlist(self, name: str) -> List[str]:
        """Get stocks from a specific watchlist"""
        return self.watchlists.get(name, [])
    
    def get_all_watchlist_stocks(self) -> Set[str]:
        """Get all stocks from all watchlists"""
        all_stocks = set()
        for watchlist in self.watchlists.values():
            all_stocks.update(watchlist)
        return all_stocks
    
    def add_to_watchlist(self, watchlist_name: str, stock_codes: List[str]):
        """Add stocks to a watchlist"""
        if watchlist_name not in self.watchlists:
            self.watchlists[watchlist_name] = []
        
        for stock in stock_codes:
            if stock not in self.watchlists[watchlist_name]:
                self.watchlists[watchlist_name].append(stock)
        
        self.logger.info(f"Added {len(stock_codes)} stocks to {watchlist_name}")
    
    def remove_from_watchlist(self, watchlist_name: str, stock_codes: List[str]):
        """Remove stocks from a watchlist"""
        if watchlist_name not in self.watchlists:
            return
        
        for stock in stock_codes:
            if stock in self.watchlists[watchlist_name]:
                self.watchlists[watchlist_name].remove(stock)
        
        self.logger.info(f"Removed {len(stock_codes)} stocks from {watchlist_name}")
    
    def list_watchlists(self) -> List[str]:
        """Get list of available watchlists"""
        return list(self.watchlists.keys())
    
    def get_watchlist_info(self) -> dict:
        """Get information about all watchlists"""
        info = {}
        for name, stocks in self.watchlists.items():
            info[name] = {
                'count': len(stocks),
                'stocks': stocks[:5] + ['...'] if len(stocks) > 5 else stocks
            }
        return info
