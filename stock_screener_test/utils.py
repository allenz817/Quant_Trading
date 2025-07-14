"""
Utility functions for the stock screener
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
from typing import List, Dict, Any

def format_currency(value: float, currency: str = 'USD') -> str:
    """Format currency values"""
    if pd.isna(value) or value is None:
        return 'N/A'
    
    if value >= 1e12:
        return f"${value/1e12:.2f}T"
    elif value >= 1e9:
        return f"${value/1e9:.2f}B"
    elif value >= 1e6:
        return f"${value/1e6:.2f}M"
    elif value >= 1e3:
        return f"${value/1e3:.2f}K"
    else:
        return f"${value:.2f}"

def format_percentage(value: float, decimals: int = 2) -> str:
    """Format percentage values"""
    if pd.isna(value) or value is None:
        return 'N/A'
    return f"{value:.{decimals}f}%"

def format_number(value: float, decimals: int = 2) -> str:
    """Format numeric values"""
    if pd.isna(value) or value is None:
        return 'N/A'
    return f"{value:.{decimals}f}"

def clean_symbol(symbol: str) -> str:
    """Clean and standardize stock symbols"""
    if not symbol:
        return ''
    
    # Remove common prefixes/suffixes
    symbol = symbol.strip().upper()
    
    # Handle different market formats
    if '.' in symbol:
        # Handle formats like "AAPL.US"
        symbol = symbol.split('.')[0]
    
    return symbol

def validate_date_range(start_date: str, end_date: str) -> bool:
    """Validate date range"""
    try:
        start = datetime.strptime(start_date, '%Y-%m-%d')
        end = datetime.strptime(end_date, '%Y-%m-%d')
        return start < end
    except ValueError:
        return False

def get_market_hours(market: str = 'US') -> Dict[str, str]:
    """Get market trading hours"""
    market_hours = {
        'US': {'open': '09:30', 'close': '16:00', 'timezone': 'US/Eastern'},
        'HK': {'open': '09:30', 'close': '16:00', 'timezone': 'Asia/Hong_Kong'},
        'CN': {'open': '09:30', 'close': '15:00', 'timezone': 'Asia/Shanghai'}
    }
    
    return market_hours.get(market.upper(), market_hours['US'])

def is_market_open(market: str = 'US') -> bool:
    """Check if market is currently open (simplified)"""
    # This is a basic implementation
    # In practice, you'd want to account for holidays, etc.
    
    from datetime import datetime
    import pytz
    
    hours = get_market_hours(market)
    tz = pytz.timezone(hours['timezone'])
    now = datetime.now(tz)
    
    # Check if it's a weekday
    if now.weekday() >= 5:  # Saturday = 5, Sunday = 6
        return False
    
    # Check if it's within trading hours
    open_time = now.replace(hour=int(hours['open'][:2]), 
                           minute=int(hours['open'][3:]), 
                           second=0, microsecond=0)
    close_time = now.replace(hour=int(hours['close'][:2]), 
                            minute=int(hours['close'][3:]), 
                            second=0, microsecond=0)
    
    return open_time <= now <= close_time

def calculate_sharpe_ratio(returns: pd.Series, risk_free_rate: float = 0.02) -> float:
    """Calculate Sharpe ratio"""
    if len(returns) < 2:
        return 0
    
    excess_returns = returns - risk_free_rate / 252  # Daily risk-free rate
    return excess_returns.mean() / excess_returns.std() * np.sqrt(252)

def calculate_max_drawdown(prices: pd.Series) -> float:
    """Calculate maximum drawdown"""
    if len(prices) < 2:
        return 0
    
    peak = prices.expanding().max()
    drawdown = (prices - peak) / peak * 100
    return drawdown.min()

def rank_stocks_by_score(df: pd.DataFrame, score_column: str = 'ranking_score') -> pd.DataFrame:
    """Rank stocks by score and add percentile rankings"""
    if df.empty or score_column not in df.columns:
        return df
    
    df = df.copy()
    df['rank'] = df[score_column].rank(ascending=False, method='dense')
    df['percentile'] = df[score_column].rank(pct=True) * 100
    
    return df.sort_values('rank')

def filter_outliers(series: pd.Series, method: str = 'iqr', factor: float = 1.5) -> pd.Series:
    """Filter outliers from a series"""
    if method == 'iqr':
        Q1 = series.quantile(0.25)
        Q3 = series.quantile(0.75)
        IQR = Q3 - Q1
        lower_bound = Q1 - factor * IQR
        upper_bound = Q3 + factor * IQR
        return series[(series >= lower_bound) & (series <= upper_bound)]
    
    elif method == 'zscore':
        z_scores = np.abs((series - series.mean()) / series.std())
        return series[z_scores < factor]
    
    return series

def create_performance_summary(results_df: pd.DataFrame) -> Dict[str, Any]:
    """Create performance summary statistics"""
    if results_df.empty:
        return {}
    
    summary = {
        'total_stocks': len(results_df),
        'date_generated': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
    }
    
    # Price statistics
    if 'price' in results_df.columns:
        summary.update({
            'avg_price': results_df['price'].mean(),
            'price_range': [results_df['price'].min(), results_df['price'].max()]
        })
    
    # Market cap statistics
    if 'market_cap' in results_df.columns:
        summary.update({
            'avg_market_cap': results_df['market_cap'].mean(),
            'total_market_cap': results_df['market_cap'].sum(),
            'market_cap_range': [results_df['market_cap'].min(), results_df['market_cap'].max()]
        })
    
    # Financial ratios
    if 'pe_ratio' in results_df.columns:
        pe_clean = results_df['pe_ratio'].replace([np.inf, -np.inf], np.nan).dropna()
        if not pe_clean.empty:
            summary['avg_pe_ratio'] = pe_clean.mean()
    
    if 'roe' in results_df.columns:
        roe_clean = results_df['roe'].dropna()
        if not roe_clean.empty:
            summary['avg_roe'] = roe_clean.mean()
    
    # Technical indicators
    if 'rsi' in results_df.columns:
        rsi_clean = results_df['rsi'].dropna()
        if not rsi_clean.empty:
            summary['avg_rsi'] = rsi_clean.mean()
    
    return summary

def export_to_trading_platform(symbols: List[str], platform: str = 'generic') -> str:
    """Export symbols in format suitable for trading platforms"""
    
    if platform.lower() == 'tradingview':
        return ','.join(symbols)
    
    elif platform.lower() == 'thinkorswim':
        return ' '.join(symbols)
    
    elif platform.lower() == 'interactive_brokers':
        return '\n'.join(symbols)
    
    else:
        # Generic format - one symbol per line
        return '\n'.join(symbols)

def calculate_portfolio_metrics(holdings: Dict[str, float], prices: Dict[str, float]) -> Dict[str, float]:
    """Calculate basic portfolio metrics"""
    
    if not holdings or not prices:
        return {}
    
    # Calculate weights
    total_value = sum(holdings[symbol] * prices.get(symbol, 0) for symbol in holdings)
    
    if total_value == 0:
        return {}
    
    weights = {symbol: (holdings[symbol] * prices.get(symbol, 0)) / total_value 
              for symbol in holdings}
    
    return {
        'total_value': total_value,
        'num_positions': len(holdings),
        'largest_position': max(weights.values()),
        'smallest_position': min(weights.values()),
        'concentration_top_5': sum(sorted(weights.values(), reverse=True)[:5])
    }

def validate_screening_criteria(criteria: Dict) -> List[str]:
    """Validate screening criteria and return any errors"""
    errors = []
    
    valid_sections = {'financial', 'technical', 'market'}
    
    for section, section_criteria in criteria.items():
        if section not in valid_sections:
            errors.append(f"Invalid section: {section}")
            continue
        
        if not isinstance(section_criteria, dict):
            errors.append(f"Section {section} must be a dictionary")
            continue
        
        for metric, condition in section_criteria.items():
            if isinstance(condition, dict):
                # Range condition
                if 'min' in condition and 'max' in condition:
                    if condition['min'] > condition['max']:
                        errors.append(f"{metric}: min value cannot be greater than max value")
                
                # Check for valid keys
                valid_keys = {'min', 'max'}
                invalid_keys = set(condition.keys()) - valid_keys
                if invalid_keys:
                    errors.append(f"{metric}: invalid keys {invalid_keys}")
            
            elif not isinstance(condition, (int, float, bool)):
                errors.append(f"{metric}: condition must be number, boolean, or range dict")
    
    return errors

def log_screening_session(strategy_name: str, results_count: int, 
                         execution_time: float, criteria: Dict):
    """Log screening session for performance tracking"""
    
    logger = logging.getLogger(__name__)
    
    log_entry = {
        'timestamp': datetime.now().isoformat(),
        'strategy': strategy_name,
        'results_count': results_count,
        'execution_time_seconds': execution_time,
        'criteria_sections': list(criteria.keys()) if criteria else [],
    }
    
    logger.info(f"Screening session: {log_entry}")
    
    # Could also write to a separate performance log file
    # with open('performance.log', 'a') as f:
    #     f.write(f"{json.dumps(log_entry)}\n")
