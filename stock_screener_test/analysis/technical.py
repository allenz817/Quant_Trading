"""
Technical analysis calculations
"""

import pandas as pd
import numpy as np
import talib as ta
from typing import Dict
import logging

class TechnicalAnalysis:
    def __init__(self, futu_client):
        self.futu_client = futu_client
        self.logger = logging.getLogger(__name__)
    
    def get_technical_metrics(self, stock_code: str) -> Dict:
        """Calculate technical indicators for a stock"""
        try:
            # Get historical data
            hist_data = self.futu_client.get_historical_data(stock_code, '3M')
            
            if hist_data.empty:
                self.logger.warning(f"No historical data for {stock_code}")
                return {}
            
            # Ensure we have required columns
            required_cols = ['close', 'high', 'low', 'volume']
            if not all(col in hist_data.columns for col in required_cols):
                self.logger.warning(f"Missing required columns for {stock_code}")
                return {}
            
            close = hist_data['close'].values
            high = hist_data['high'].values
            low = hist_data['low'].values
            volume = hist_data['volume'].values
            
            metrics = {}
            
            # Price change metrics
            if len(close) >= 2:
                metrics['price_change_1d'] = ((close[-1] - close[-2]) / close[-2]) * 100
            
            if len(close) >= 5:
                metrics['price_change_5d'] = ((close[-1] - close[-6]) / close[-6]) * 100
            
            if len(close) >= 20:
                metrics['price_change_1m'] = ((close[-1] - close[-21]) / close[-21]) * 100
            
            if len(close) >= 252:
                metrics['price_change_52w'] = ((close[-1] - close[-253]) / close[-253]) * 100
                # 52-week high/low
                metrics['price_52w_high'] = np.max(close[-253:])
                metrics['price_52w_low'] = np.min(close[-253:])
                metrics['distance_from_52w_high'] = ((close[-1] - metrics['price_52w_high']) / metrics['price_52w_high']) * 100
            
            # RSI
            if len(close) >= 14:
                rsi = ta.RSI(close, timeperiod=14)
                metrics['rsi'] = rsi[-1] if not np.isnan(rsi[-1]) else None
            
            # MACD
            if len(close) >= 26:
                macd, macd_signal, macd_hist = ta.MACD(close)
                if not np.isnan(macd[-1]):
                    metrics['macd'] = macd[-1]
                    metrics['macd_signal'] = macd_signal[-1]
                    metrics['macd_histogram'] = macd_hist[-1]
            
            # Moving averages
            if len(close) >= 20:
                ma20 = ta.SMA(close, timeperiod=20)
                metrics['ma20'] = ma20[-1] if not np.isnan(ma20[-1]) else None
                if metrics['ma20']:
                    metrics['price_above_ma20'] = close[-1] > metrics['ma20']
                    metrics['distance_from_ma20'] = ((close[-1] - metrics['ma20']) / metrics['ma20']) * 100
            
            if len(close) >= 50:
                ma50 = ta.SMA(close, timeperiod=50)
                metrics['ma50'] = ma50[-1] if not np.isnan(ma50[-1]) else None
                if metrics['ma50']:
                    metrics['price_above_ma50'] = close[-1] > metrics['ma50']
            
            if len(close) >= 200:
                ma200 = ta.SMA(close, timeperiod=200)
                metrics['ma200'] = ma200[-1] if not np.isnan(ma200[-1]) else None
                if metrics['ma200']:
                    metrics['price_above_ma200'] = close[-1] > metrics['ma200']
            
            # Bollinger Bands
            if len(close) >= 20:
                bb_upper, bb_middle, bb_lower = ta.BBANDS(close, timeperiod=20)
                if not np.isnan(bb_upper[-1]):
                    metrics['bb_upper'] = bb_upper[-1]
                    metrics['bb_middle'] = bb_middle[-1]
                    metrics['bb_lower'] = bb_lower[-1]
                    metrics['bb_position'] = (close[-1] - bb_lower[-1]) / (bb_upper[-1] - bb_lower[-1])
            
            # Volume analysis
            if len(volume) >= 20:
                avg_volume_20d = np.mean(volume[-20:])
                metrics['avg_volume_20d'] = avg_volume_20d
                if avg_volume_20d > 0:
                    metrics['volume_ratio'] = volume[-1] / avg_volume_20d
            
            # Stochastic
            if len(close) >= 14:
                stoch_k, stoch_d = ta.STOCH(high, low, close)
                if not np.isnan(stoch_k[-1]):
                    metrics['stoch_k'] = stoch_k[-1]
                    metrics['stoch_d'] = stoch_d[-1]
            
            # Williams %R
            if len(close) >= 14:
                williams_r = ta.WILLR(high, low, close, timeperiod=14)
                if not np.isnan(williams_r[-1]):
                    metrics['williams_r'] = williams_r[-1]
            
            # Average True Range (ATR)
            if len(close) >= 14:
                atr = ta.ATR(high, low, close, timeperiod=14)
                if not np.isnan(atr[-1]):
                    metrics['atr'] = atr[-1]
                    metrics['atr_percent'] = (atr[-1] / close[-1]) * 100
            
            # Commodity Channel Index (CCI)
            if len(close) >= 14:
                cci = ta.CCI(high, low, close, timeperiod=14)
                if not np.isnan(cci[-1]):
                    metrics['cci'] = cci[-1]
            
            return metrics
            
        except Exception as e:
            self.logger.error(f"Error calculating technical metrics for {stock_code}: {e}")
            return {}
    
    def calculate_volatility(self, hist_data: pd.DataFrame, periods: int = 20) -> float:
        """Calculate historical volatility"""
        if len(hist_data) < periods:
            return None
        
        returns = hist_data['close'].pct_change().dropna()
        return returns.std() * np.sqrt(252) * 100  # Annualized volatility
    
    def detect_patterns(self, stock_code: str) -> Dict:
        """Detect candlestick patterns"""
        try:
            hist_data = self.futu_client.get_historical_data(stock_code, '1M')
            
            if len(hist_data) < 10:
                return {}
            
            open_prices = hist_data['open'].values
            high_prices = hist_data['high'].values
            low_prices = hist_data['low'].values
            close_prices = hist_data['close'].values
            
            patterns = {}
            
            # Doji
            doji = ta.CDLDOJI(open_prices, high_prices, low_prices, close_prices)
            patterns['doji'] = bool(doji[-1])
            
            # Hammer
            hammer = ta.CDLHAMMER(open_prices, high_prices, low_prices, close_prices)
            patterns['hammer'] = bool(hammer[-1])
            
            # Shooting Star
            shooting_star = ta.CDLSHOOTINGSTAR(open_prices, high_prices, low_prices, close_prices)
            patterns['shooting_star'] = bool(shooting_star[-1])
            
            # Engulfing patterns
            engulfing_bullish = ta.CDLENGULFING(open_prices, high_prices, low_prices, close_prices)
            patterns['engulfing_bullish'] = bool(engulfing_bullish[-1] > 0)
            patterns['engulfing_bearish'] = bool(engulfing_bullish[-1] < 0)
            
            return patterns
            
        except Exception as e:
            self.logger.error(f"Error detecting patterns for {stock_code}: {e}")
            return {}
