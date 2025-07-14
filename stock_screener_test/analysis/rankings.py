"""
Stock ranking algorithms
"""

import pandas as pd
import numpy as np
from typing import Dict, List
import logging

class StockRanker:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def rank_by_composite_score(self, stocks_df: pd.DataFrame, criteria: Dict) -> pd.DataFrame:
        """Rank stocks using a composite scoring system"""
        if stocks_df.empty:
            return stocks_df
        
        try:
            # Initialize ranking score
            stocks_df['ranking_score'] = 0.0
            
            # Financial ranking components
            if 'financial' in criteria:
                financial_score = self._calculate_financial_score(stocks_df, criteria['financial'])
                stocks_df['financial_score'] = financial_score
                stocks_df['ranking_score'] += financial_score * 0.4  # 40% weight
            
            # Technical ranking components
            if 'technical' in criteria:
                technical_score = self._calculate_technical_score(stocks_df, criteria['technical'])
                stocks_df['technical_score'] = technical_score
                stocks_df['ranking_score'] += technical_score * 0.4  # 40% weight
            
            # Market/momentum ranking components
            if 'market' in criteria:
                market_score = self._calculate_market_score(stocks_df, criteria['market'])
                stocks_df['market_score'] = market_score
                stocks_df['ranking_score'] += market_score * 0.2  # 20% weight
            
            # Sort by ranking score (highest first)
            stocks_df = stocks_df.sort_values('ranking_score', ascending=False)
            
            # Add ranking position
            stocks_df['rank'] = range(1, len(stocks_df) + 1)
            
            return stocks_df
            
        except Exception as e:
            self.logger.error(f"Error in composite ranking: {e}")
            return stocks_df
    
    def _calculate_financial_score(self, stocks_df: pd.DataFrame, financial_criteria: Dict) -> pd.Series:
        """Calculate financial component of ranking score"""
        score = pd.Series(0.0, index=stocks_df.index)
        
        # ROE scoring
        if 'roe' in stocks_df.columns:
            roe_scores = self._normalize_metric(stocks_df['roe'], higher_is_better=True)
            score += roe_scores * 0.3
        
        # P/E ratio scoring (lower is better, but not too low)
        if 'pe_ratio' in stocks_df.columns:
            # Ideal P/E range is 10-20
            pe_scores = stocks_df['pe_ratio'].apply(self._pe_scoring_function)
            pe_scores = (pe_scores - pe_scores.min()) / (pe_scores.max() - pe_scores.min())
            score += pe_scores * 0.25
        
        # Debt-to-equity scoring (lower is better)
        if 'debt_to_equity' in stocks_df.columns:
            debt_scores = self._normalize_metric(stocks_df['debt_to_equity'], higher_is_better=False)
            score += debt_scores * 0.2
        
        # Net margin scoring
        if 'net_margin' in stocks_df.columns:
            margin_scores = self._normalize_metric(stocks_df['net_margin'], higher_is_better=True)
            score += margin_scores * 0.25
        
        return score
    
    def _calculate_technical_score(self, stocks_df: pd.DataFrame, technical_criteria: Dict) -> pd.Series:
        """Calculate technical component of ranking score"""
        score = pd.Series(0.0, index=stocks_df.index)
        
        # Price momentum scoring
        momentum_weight = 0.4
        if 'price_change_1d' in stocks_df.columns:
            momentum_scores = self._normalize_metric(stocks_df['price_change_1d'], higher_is_better=True)
            score += momentum_scores * momentum_weight * 0.3
        
        if 'price_change_1m' in stocks_df.columns:
            momentum_scores = self._normalize_metric(stocks_df['price_change_1m'], higher_is_better=True)
            score += momentum_scores * momentum_weight * 0.7
        
        # RSI scoring (prefer values between 30-70, avoid extremes)
        if 'rsi' in stocks_df.columns:
            rsi_scores = stocks_df['rsi'].apply(self._rsi_scoring_function)
            rsi_scores = (rsi_scores - rsi_scores.min()) / (rsi_scores.max() - rsi_scores.min())
            score += rsi_scores * 0.2
        
        # Volume scoring
        if 'volume_ratio' in stocks_df.columns:
            volume_scores = self._normalize_metric(stocks_df['volume_ratio'], higher_is_better=True)
            score += volume_scores * 0.2
        
        # Moving average position scoring
        if 'price_above_ma20' in stocks_df.columns:
            ma_scores = stocks_df['price_above_ma20'].astype(float)
            score += ma_scores * 0.2
        
        return score
    
    def _calculate_market_score(self, stocks_df: pd.DataFrame, market_criteria: Dict) -> pd.Series:
        """Calculate market component of ranking score"""
        score = pd.Series(0.0, index=stocks_df.index)
        
        # Market cap scoring (prefer mid-cap to large-cap for growth)
        if 'market_cap' in stocks_df.columns:
            market_cap_scores = stocks_df['market_cap'].apply(self._market_cap_scoring_function)
            market_cap_scores = (market_cap_scores - market_cap_scores.min()) / (market_cap_scores.max() - market_cap_scores.min())
            score += market_cap_scores * 0.5
        
        # Volatility scoring (prefer moderate volatility)
        if 'atr_percent' in stocks_df.columns:
            vol_scores = stocks_df['atr_percent'].apply(self._volatility_scoring_function)
            vol_scores = (vol_scores - vol_scores.min()) / (vol_scores.max() - vol_scores.min())
            score += vol_scores * 0.3
        
        # Quality score if available
        if 'quality_score' in stocks_df.columns:
            quality_scores = self._normalize_metric(stocks_df['quality_score'], higher_is_better=True)
            score += quality_scores * 0.2
        
        return score
    
    def _normalize_metric(self, series: pd.Series, higher_is_better: bool = True) -> pd.Series:
        """Normalize a metric to 0-1 scale"""
        if series.isna().all():
            return pd.Series(0.0, index=series.index)
        
        series_clean = series.replace([np.inf, -np.inf], np.nan).dropna()
        
        if len(series_clean) == 0:
            return pd.Series(0.0, index=series.index)
        
        min_val = series_clean.min()
        max_val = series_clean.max()
        
        if max_val == min_val:
            return pd.Series(0.5, index=series.index)
        
        normalized = (series - min_val) / (max_val - min_val)
        
        if not higher_is_better:
            normalized = 1 - normalized
        
        return normalized.fillna(0)
    
    def _pe_scoring_function(self, pe: float) -> float:
        """Scoring function for P/E ratio (prefers moderate values)"""
        if pd.isna(pe) or pe <= 0:
            return 0
        
        if 10 <= pe <= 20:
            return 1.0
        elif 5 <= pe <= 25:
            return 0.7
        elif pe <= 30:
            return 0.4
        else:
            return 0.1
    
    def _rsi_scoring_function(self, rsi: float) -> float:
        """Scoring function for RSI (prefers non-extreme values)"""
        if pd.isna(rsi):
            return 0
        
        if 40 <= rsi <= 60:
            return 1.0
        elif 30 <= rsi <= 70:
            return 0.7
        elif 20 <= rsi <= 80:
            return 0.4
        else:
            return 0.1
    
    def _market_cap_scoring_function(self, market_cap: float) -> float:
        """Scoring function for market cap (prefers mid to large cap)"""
        if pd.isna(market_cap) or market_cap <= 0:
            return 0
        
        # Convert to billions for easier handling
        market_cap_b = market_cap / 1e9
        
        if 2 <= market_cap_b <= 10:  # $2B - $10B (mid-cap)
            return 1.0
        elif 10 <= market_cap_b <= 50:  # $10B - $50B (large-cap)
            return 0.9
        elif 1 <= market_cap_b <= 2:  # $1B - $2B (small-cap)
            return 0.6
        elif market_cap_b > 50:  # > $50B (mega-cap)
            return 0.7
        else:  # < $1B (micro-cap)
            return 0.3
    
    def _volatility_scoring_function(self, volatility: float) -> float:
        """Scoring function for volatility (prefers moderate volatility)"""
        if pd.isna(volatility):
            return 0
        
        if 1 <= volatility <= 3:  # Moderate volatility
            return 1.0
        elif 0.5 <= volatility <= 5:
            return 0.7
        elif volatility <= 8:
            return 0.4
        else:
            return 0.1
    
    def rank_by_single_metric(self, stocks_df: pd.DataFrame, metric: str, ascending: bool = False) -> pd.DataFrame:
        """Rank stocks by a single metric"""
        if metric not in stocks_df.columns:
            self.logger.warning(f"Metric {metric} not found in data")
            return stocks_df
        
        try:
            # Sort by the metric
            sorted_df = stocks_df.sort_values(metric, ascending=ascending, na_position='last')
            
            # Add ranking
            sorted_df['rank'] = range(1, len(sorted_df) + 1)
            
            return sorted_df
            
        except Exception as e:
            self.logger.error(f"Error ranking by {metric}: {e}")
            return stocks_df
    
    def get_top_stocks(self, stocks_df: pd.DataFrame, n: int = 10) -> pd.DataFrame:
        """Get top N stocks from ranked dataframe"""
        return stocks_df.head(n)
    
    def get_ranking_summary(self, stocks_df: pd.DataFrame) -> Dict:
        """Get summary statistics for the ranking"""
        if stocks_df.empty:
            return {}
        
        summary = {
            'total_stocks': len(stocks_df),
            'avg_ranking_score': stocks_df.get('ranking_score', pd.Series()).mean(),
            'top_10_avg_score': stocks_df.head(10).get('ranking_score', pd.Series()).mean(),
        }
        
        # Add metric-specific summaries
        if 'financial_score' in stocks_df.columns:
            summary['avg_financial_score'] = stocks_df['financial_score'].mean()
        
        if 'technical_score' in stocks_df.columns:
            summary['avg_technical_score'] = stocks_df['technical_score'].mean()
        
        if 'market_score' in stocks_df.columns:
            summary['avg_market_score'] = stocks_df['market_score'].mean()
        
        return summary
