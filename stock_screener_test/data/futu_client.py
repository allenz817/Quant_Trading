"""
Futu API Client for stock data retrieval
"""

import futu as ft
import pandas as pd
import logging
from typing import List, Dict, Optional
import time

class FutuClient:
    def __init__(self, config: Dict):
        """Initialize Futu client with configuration"""
        self.host = config.get('host', '127.0.0.1')
        self.port = config.get('port', 11111)
        self.timeout = config.get('timeout', 10)
        
        self.logger = logging.getLogger(__name__)
        
        # Initialize contexts
        self.quote_ctx = None
        self.trade_ctx = None
        
        self._connect()
    
    def _connect(self):
        """Establish connection to Futu OpenAPI"""
        try:
            self.quote_ctx = ft.OpenQuoteContext(host=self.host, port=self.port)
            self.logger.info(f"Connected to Futu OpenAPI at {self.host}:{self.port}")
        except Exception as e:
            self.logger.error(f"Failed to connect to Futu OpenAPI: {e}")
            raise
    
    def get_stock_list(self, market: str = 'US') -> List[str]:
        """Get list of stocks for a specific market"""
        try:
            if market.upper() == 'US':
                plate = ft.Plate.ALL
                market_code = ft.Market.US
            elif market.upper() == 'HK':
                plate = ft.Plate.ALL
                market_code = ft.Market.HK
            elif market.upper() == 'CN':
                plate = ft.Plate.ALL
                market_code = ft.Market.SH  # Shanghai
            else:
                raise ValueError(f"Unsupported market: {market}")
            
            ret, data = self.quote_ctx.get_plate_stock(plate, market_code)
            
            if ret == ft.RET_OK:
                return data['code'].tolist()
            else:
                self.logger.error(f"Failed to get stock list: {data}")
                return []
                
        except Exception as e:
            self.logger.error(f"Error getting stock list for {market}: {e}")
            return []
    
    def get_basic_info(self, stock_code: str) -> Dict:
        """Get basic stock information"""
        try:
            ret, data = self.quote_ctx.get_stock_basicinfo(market=ft.Market.US, 
                                                          stock_type=ft.SecurityType.STOCK,
                                                          code_list=[stock_code])
            
            if ret == ft.RET_OK and not data.empty:
                row = data.iloc[0]
                return {
                    'name': row.get('name', ''),
                    'sector': row.get('main_contract', ''),
                    'market_cap': row.get('market_val', 0),
                    'lot_size': row.get('lot_size', 0),
                    'stock_type': row.get('stock_type', ''),
                }
            else:
                self.logger.warning(f"No basic info found for {stock_code}")
                return {}
                
        except Exception as e:
            self.logger.error(f"Error getting basic info for {stock_code}: {e}")
            return {}
    
    def get_current_price(self, stock_code: str) -> Dict:
        """Get current price data"""
        try:
            ret, data = self.quote_ctx.get_market_snapshot([stock_code])
            
            if ret == ft.RET_OK and not data.empty:
                row = data.iloc[0]
                return {
                    'price': row.get('last_price', 0),
                    'change_rate': row.get('change_rate', 0),
                    'volume': row.get('volume', 0),
                    'turnover': row.get('turnover', 0),
                    'high': row.get('high_price', 0),
                    'low': row.get('low_price', 0),
                    'open': row.get('open_price', 0),
                }
            else:
                self.logger.warning(f"No price data found for {stock_code}")
                return {}
                
        except Exception as e:
            self.logger.error(f"Error getting price for {stock_code}: {e}")
            return {}
    
    def get_historical_data(self, stock_code: str, period: str = '1M') -> pd.DataFrame:
        """Get historical price data"""
        try:
            # Map period to Futu format
            if period == '1D':
                ktype = ft.KLType.K_DAY
                num = 1
            elif period == '1W':
                ktype = ft.KLType.K_WEEK
                num = 4
            elif period == '1M':
                ktype = ft.KLType.K_DAY
                num = 30
            elif period == '3M':
                ktype = ft.KLType.K_DAY
                num = 90
            elif period == '1Y':
                ktype = ft.KLType.K_DAY
                num = 252
            else:
                ktype = ft.KLType.K_DAY
                num = 30
            
            ret, data = self.quote_ctx.get_history_kline(stock_code, 
                                                        start=None, 
                                                        end=None, 
                                                        ktype=ktype, 
                                                        autype=ft.AuType.QFQ,
                                                        count=num)
            
            if ret == ft.RET_OK:
                return data
            else:
                self.logger.warning(f"No historical data for {stock_code}: {data}")
                return pd.DataFrame()
                
        except Exception as e:
            self.logger.error(f"Error getting historical data for {stock_code}: {e}")
            return pd.DataFrame()
    
    def get_financial_data(self, stock_code: str) -> Dict:
        """Get financial statement data"""
        try:
            ret, data = self.quote_ctx.get_financial(stock_code, quarter=None)
            
            if ret == ft.RET_OK and not data.empty:
                # Get the most recent quarter data
                latest = data.iloc[0]
                return {
                    'revenue': latest.get('total_revenue', 0),
                    'net_income': latest.get('net_income', 0),
                    'total_assets': latest.get('total_assets', 0),
                    'total_equity': latest.get('total_equity', 0),
                    'total_debt': latest.get('total_debt', 0),
                    'eps': latest.get('eps_basic', 0),
                    'book_value_per_share': latest.get('book_value_per_share', 0),
                }
            else:
                self.logger.warning(f"No financial data for {stock_code}")
                return {}
                
        except Exception as e:
            self.logger.error(f"Error getting financial data for {stock_code}: {e}")
            return {}
    
    def batch_get_quotes(self, stock_codes: List[str]) -> pd.DataFrame:
        """Get quotes for multiple stocks efficiently"""
        try:
            # Split into batches to avoid API limits
            batch_size = 200
            all_data = []
            
            for i in range(0, len(stock_codes), batch_size):
                batch = stock_codes[i:i + batch_size]
                
                ret, data = self.quote_ctx.get_market_snapshot(batch)
                
                if ret == ft.RET_OK:
                    all_data.append(data)
                else:
                    self.logger.warning(f"Failed to get batch quotes: {data}")
                
                # Rate limiting
                time.sleep(0.1)
            
            if all_data:
                return pd.concat(all_data, ignore_index=True)
            else:
                return pd.DataFrame()
                
        except Exception as e:
            self.logger.error(f"Error in batch quote retrieval: {e}")
            return pd.DataFrame()
    
    def close(self):
        """Close the connection"""
        if self.quote_ctx:
            self.quote_ctx.close()
        if self.trade_ctx:
            self.trade_ctx.close()
        self.logger.info("Futu connection closed")
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
