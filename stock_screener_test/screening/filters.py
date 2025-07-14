"""
Stock filtering logic
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from analysis.technical import TechnicalAnalysis
from analysis.fundamental import FundamentalAnalysis
from analysis.rankings import StockRanker

class StockFilter:
    def __init__(self, futu_client, max_workers: int = 10):
        self.futu_client = futu_client
        self.max_workers = max_workers
        self.technical = TechnicalAnalysis(futu_client)
        self.fundamental = FundamentalAnalysis(futu_client)
        self.ranker = StockRanker()
        
        self.logger = logging.getLogger(__name__)
    
    def screen_stocks(self, stock_list: List[str], criteria: Dict, 
                     max_results: int = None) -> pd.DataFrame:
        """Apply screening criteria to stock list"""
        self.logger.info(f"Screening {len(stock_list)} stocks with {len(criteria)} criteria sections")
        
        # Get stock data in parallel
        stock_data_list = self._get_stocks_data_parallel(stock_list)
        
        if not stock_data_list:
            self.logger.warning("No stock data retrieved")
            return pd.DataFrame()
        
        # Convert to DataFrame
        stocks_df = pd.DataFrame(stock_data_list)
        
        self.logger.info(f"Retrieved data for {len(stocks_df)} stocks")
        
        # Apply filters
        filtered_df = self._apply_filters(stocks_df, criteria)
        
        self.logger.info(f"After filtering: {len(filtered_df)} stocks remain")
        
        # Rank results
        if not filtered_df.empty:
            ranked_df = self.ranker.rank_by_composite_score(filtered_df, criteria)
            
            # Limit results if specified
            if max_results and len(ranked_df) > max_results:
                ranked_df = ranked_df.head(max_results)
            
            return ranked_df
        
        return pd.DataFrame()
    
    def _get_stocks_data_parallel(self, stock_list: List[str]) -> List[Dict]:
        """Get stock data for multiple stocks in parallel"""
        stock_data_list = []
        
        # Process in smaller batches to manage memory and API limits
        batch_size = min(self.max_workers, 50)
        
        for i in range(0, len(stock_list), batch_size):
            batch = stock_list[i:i + batch_size]
            
            with ThreadPoolExecutor(max_workers=min(len(batch), self.max_workers)) as executor:
                # Submit tasks
                future_to_stock = {
                    executor.submit(self._get_stock_data, stock_code): stock_code
                    for stock_code in batch
                }
                
                # Collect results
                for future in as_completed(future_to_stock, timeout=60):
                    stock_code = future_to_stock[future]
                    try:
                        stock_data = future.result()
                        if stock_data:  # Only add if we got valid data
                            stock_data_list.append(stock_data)
                    except Exception as e:
                        self.logger.warning(f"Error processing {stock_code}: {e}")
            
            # Progress indicator
            self.logger.info(f"Processed {min(i + batch_size, len(stock_list))}/{len(stock_list)} stocks")
        
        return stock_data_list
    
    def _get_stock_data(self, stock_code: str) -> Dict:
        """Fetch all required data for a stock"""
        try:
            stock_data = {'symbol': stock_code}
            
            # Basic info
            basic_info = self.futu_client.get_basic_info(stock_code)
            stock_data.update(basic_info)
            
            # Current price data
            price_data = self.futu_client.get_current_price(stock_code)
            stock_data.update(price_data)
            
            # Skip if no price data (likely delisted or invalid symbol)
            if not price_data or price_data.get('price', 0) <= 0:
                return None
            
            # Financial data
            financial_data = self.fundamental.get_financial_metrics(stock_code)
            stock_data.update(financial_data)
            
            # Technical data
            technical_data = self.technical.get_technical_metrics(stock_code)
            stock_data.update(technical_data)
            
            # Quality score
            quality_data = self.fundamental.get_quality_score(stock_code)
            if quality_data:
                stock_data['quality_score'] = quality_data.get('quality_score', 0)
            
            return stock_data
            
        except Exception as e:
            self.logger.error(f"Error getting data for {stock_code}: {e}")
            return None
    
    def _apply_filters(self, stocks_df: pd.DataFrame, criteria: Dict) -> pd.DataFrame:
        """Apply filtering criteria to stocks DataFrame"""
        if stocks_df.empty:
            return stocks_df
        
        filtered_df = stocks_df.copy()
        initial_count = len(filtered_df)
        
        # Apply each criteria section
        for section, section_criteria in criteria.items():
            section_count = len(filtered_df)
            
            for metric, condition in section_criteria.items():
                filtered_df = self._apply_single_filter(filtered_df, metric, condition)
                
                if filtered_df.empty:
                    self.logger.info(f"No stocks passed {metric} filter")
                    return filtered_df
            
            remaining_after_section = len(filtered_df)
            self.logger.info(f"{section} filters: {section_count} -> {remaining_after_section} stocks")
        
        self.logger.info(f"Total filtering: {initial_count} -> {len(filtered_df)} stocks")
        
        return filtered_df
    
    def _apply_single_filter(self, df: pd.DataFrame, metric: str, condition) -> pd.DataFrame:
        """Apply a single filter condition"""
        if metric not in df.columns:
            self.logger.warning(f"Metric {metric} not found in data")
            return df
        
        try:
            if isinstance(condition, dict):
                # Range condition
                mask = pd.Series(True, index=df.index)
                
                if 'min' in condition:
                    mask &= (df[metric] >= condition['min']) | df[metric].isna()
                
                if 'max' in condition:
                    mask &= (df[metric] <= condition['max']) | df[metric].isna()
                
                # Remove rows where the metric is NaN (unless we want to keep them)
                mask &= ~df[metric].isna()
                
                return df[mask]
            
            elif isinstance(condition, bool):
                # Boolean condition
                return df[df[metric] == condition]
            
            else:
                # Direct value condition
                return df[df[metric] == condition]
                
        except Exception as e:
            self.logger.error(f"Error applying filter for {metric}: {e}")
            return df
    
    def quick_screen(self, stock_list: List[str], 
                    min_price: float = None,
                    min_volume: float = None,
                    min_market_cap: float = None) -> List[str]:
        """Quick screening based on basic criteria to reduce dataset size"""
        
        if not any([min_price, min_volume, min_market_cap]):
            return stock_list
        
        self.logger.info(f"Quick screening {len(stock_list)} stocks")
        
        # Get batch quotes for quick filtering
        quotes_df = self.futu_client.batch_get_quotes(stock_list)
        
        if quotes_df.empty:
            return stock_list
        
        # Apply quick filters
        mask = pd.Series(True, index=quotes_df.index)
        
        if min_price:
            mask &= quotes_df['last_price'] >= min_price
        
        if min_volume:
            mask &= quotes_df['volume'] >= min_volume
        
        if min_market_cap:
            # This requires market cap calculation or basic info lookup
            pass
        
        filtered_quotes = quotes_df[mask]
        filtered_stocks = filtered_quotes['code'].tolist()
        
        self.logger.info(f"Quick screening: {len(stock_list)} -> {len(filtered_stocks)} stocks")
        
        return filtered_stocks
    
    def screen_by_pattern(self, stock_list: List[str], pattern_name: str) -> pd.DataFrame:
        """Screen stocks based on technical patterns"""
        results = []
        
        for stock_code in stock_list:
            try:
                patterns = self.technical.detect_patterns(stock_code)
                
                if patterns.get(pattern_name, False):
                    stock_data = self._get_stock_data(stock_code)
                    if stock_data:
                        stock_data['pattern_detected'] = pattern_name
                        results.append(stock_data)
                        
            except Exception as e:
                self.logger.warning(f"Error checking pattern for {stock_code}: {e}")
        
        return pd.DataFrame(results)
    
    def get_filter_summary(self, original_count: int, filtered_df: pd.DataFrame, 
                          criteria: Dict) -> Dict:
        """Generate summary of filtering results"""
        return {
            'original_count': original_count,
            'filtered_count': len(filtered_df),
            'filter_rate': len(filtered_df) / original_count if original_count > 0 else 0,
            'criteria_sections': list(criteria.keys()),
            'top_stocks': filtered_df.head(5)['symbol'].tolist() if not filtered_df.empty else []
        }
