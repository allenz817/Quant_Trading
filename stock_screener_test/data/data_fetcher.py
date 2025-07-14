"""
Data fetcher with caching capabilities
"""

import pandas as pd
import pickle
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging
from .futu_client import FutuClient

class DataFetcher:
    def __init__(self, futu_client: FutuClient, cache_config: Dict):
        self.futu_client = futu_client
        self.cache_enabled = cache_config.get('enabled', True)
        self.cache_ttl = cache_config.get('ttl_minutes', 30)
        self.cache_dir = 'cache'
        
        self.logger = logging.getLogger(__name__)
        
        # Create cache directory if it doesn't exist
        if self.cache_enabled and not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)
    
    def _get_cache_path(self, key: str) -> str:
        """Generate cache file path"""
        return os.path.join(self.cache_dir, f"{key}.pkl")
    
    def _is_cache_valid(self, cache_path: str) -> bool:
        """Check if cache file is still valid"""
        if not os.path.exists(cache_path):
            return False
        
        file_time = datetime.fromtimestamp(os.path.getmtime(cache_path))
        return datetime.now() - file_time < timedelta(minutes=self.cache_ttl)
    
    def _load_from_cache(self, key: str) -> Optional[any]:
        """Load data from cache if valid"""
        if not self.cache_enabled:
            return None
        
        cache_path = self._get_cache_path(key)
        
        if self._is_cache_valid(cache_path):
            try:
                with open(cache_path, 'rb') as f:
                    data = pickle.load(f)
                    self.logger.debug(f"Loaded {key} from cache")
                    return data
            except Exception as e:
                self.logger.warning(f"Failed to load cache for {key}: {e}")
        
        return None
    
    def _save_to_cache(self, key: str, data: any):
        """Save data to cache"""
        if not self.cache_enabled:
            return
        
        cache_path = self._get_cache_path(key)
        
        try:
            with open(cache_path, 'wb') as f:
                pickle.dump(data, f)
                self.logger.debug(f"Saved {key} to cache")
        except Exception as e:
            self.logger.warning(f"Failed to save cache for {key}: {e}")
    
    def get_stock_universe(self, market: str) -> List[str]:
        """Get stock universe with caching"""
        cache_key = f"stock_universe_{market}"
        
        # Try cache first
        cached_data = self._load_from_cache(cache_key)
        if cached_data is not None:
            return cached_data
        
        # Fetch from API
        stock_list = self.futu_client.get_stock_list(market)
        
        # Cache the result
        self._save_to_cache(cache_key, stock_list)
        
        return stock_list
    
    def get_stock_data(self, stock_code: str, include_history: bool = True) -> Dict:
        """Get comprehensive stock data with caching"""
        cache_key = f"stock_data_{stock_code}"
        
        # Try cache first
        cached_data = self._load_from_cache(cache_key)
        if cached_data is not None:
            return cached_data
        
        # Fetch from API
        stock_data = {}
        
        # Basic info
        basic_info = self.futu_client.get_basic_info(stock_code)
        stock_data.update(basic_info)
        
        # Current price
        price_data = self.futu_client.get_current_price(stock_code)
        stock_data.update(price_data)
        
        # Financial data
        financial_data = self.futu_client.get_financial_data(stock_code)
        stock_data.update(financial_data)
        
        # Historical data if requested
        if include_history:
            hist_data = self.futu_client.get_historical_data(stock_code, '3M')
            if not hist_data.empty:
                stock_data['historical_data'] = hist_data
        
        # Add metadata
        stock_data['symbol'] = stock_code
        stock_data['last_updated'] = datetime.now()
        
        # Cache the result
        self._save_to_cache(cache_key, stock_data)
        
        return stock_data
    
    def get_batch_quotes(self, stock_codes: List[str]) -> pd.DataFrame:
        """Get batch quotes with caching"""
        cache_key = f"batch_quotes_{len(stock_codes)}_{hash(tuple(sorted(stock_codes)))}"
        
        # Try cache first
        cached_data = self._load_from_cache(cache_key)
        if cached_data is not None:
            return cached_data
        
        # Fetch from API
        quotes_df = self.futu_client.batch_get_quotes(stock_codes)
        
        # Cache the result
        self._save_to_cache(cache_key, quotes_df)
        
        return quotes_df
    
    def clear_cache(self):
        """Clear all cached data"""
        if not self.cache_enabled or not os.path.exists(self.cache_dir):
            return
        
        try:
            for filename in os.listdir(self.cache_dir):
                if filename.endswith('.pkl'):
                    os.remove(os.path.join(self.cache_dir, filename))
            self.logger.info("Cache cleared successfully")
        except Exception as e:
            self.logger.error(f"Failed to clear cache: {e}")
    
    def get_cache_stats(self) -> Dict:
        """Get cache statistics"""
        if not self.cache_enabled or not os.path.exists(self.cache_dir):
            return {'enabled': False}
        
        cache_files = [f for f in os.listdir(self.cache_dir) if f.endswith('.pkl')]
        total_size = sum(os.path.getsize(os.path.join(self.cache_dir, f)) for f in cache_files)
        
        return {
            'enabled': True,
            'files': len(cache_files),
            'total_size_mb': round(total_size / (1024 * 1024), 2),
            'ttl_minutes': self.cache_ttl
        }
