"""
Screening criteria definitions
"""

from typing import Dict, Any, List
import logging

class ScreeningCriteria:
    """Define and validate screening criteria"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def validate_criteria(self, criteria: Dict) -> bool:
        """Validate that criteria are properly formatted"""
        try:
            valid_sections = ['financial', 'technical', 'market']
            
            for section in criteria:
                if section not in valid_sections:
                    self.logger.warning(f"Unknown criteria section: {section}")
                    return False
                
                if not isinstance(criteria[section], dict):
                    self.logger.error(f"Criteria section {section} must be a dictionary")
                    return False
                
                # Validate individual criteria
                for metric, condition in criteria[section].items():
                    if not self._validate_condition(condition):
                        self.logger.error(f"Invalid condition for {metric}: {condition}")
                        return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error validating criteria: {e}")
            return False
    
    def _validate_condition(self, condition: Any) -> bool:
        """Validate a single condition"""
        if isinstance(condition, dict):
            # Range condition
            valid_keys = {'min', 'max'}
            if not all(key in valid_keys for key in condition.keys()):
                return False
            
            # Check that min <= max if both are present
            if 'min' in condition and 'max' in condition:
                if condition['min'] > condition['max']:
                    return False
        
        elif isinstance(condition, (int, float, bool)):
            # Direct value condition
            return True
        
        else:
            return False
        
        return True
    
    def get_default_strategies(self) -> Dict:
        """Get predefined screening strategies"""
        return {
            'value_stocks': {
                'financial': {
                    'pe_ratio': {'min': 5, 'max': 15},
                    'pb_ratio': {'max': 1.5},
                    'debt_to_equity': {'max': 0.5},
                    'roe': {'min': 12}
                },
                'market': {
                    'market_cap': {'min': 1000000000}  # $1B+
                }
            },
            
            'growth_stocks': {
                'financial': {
                    'revenue_growth': {'min': 15},
                    'earnings_growth': {'min': 20},
                    'pe_ratio': {'max': 30}
                },
                'technical': {
                    'price_change_52w': {'min': 10}
                }
            },
            
            'momentum_breakout': {
                'technical': {
                    'price_change_1d': {'min': 3},
                    'volume_ratio': {'min': 2.0},
                    'rsi': {'min': 60, 'max': 80},
                    'price_above_ma20': True
                }
            },
            
            'oversold_recovery': {
                'technical': {
                    'rsi': {'min': 20, 'max': 35},
                    'price_change_5d': {'min': -10, 'max': -2},
                    'volume_ratio': {'min': 1.5}
                },
                'financial': {
                    'pe_ratio': {'max': 25}
                }
            },
            
            'dividend_aristocrats': {
                'financial': {
                    'dividend_yield': {'min': 3},
                    'payout_ratio': {'max': 70},
                    'debt_to_equity': {'max': 0.6},
                    'roe': {'min': 10}
                },
                'market': {
                    'market_cap': {'min': 500000000}  # $500M+
                }
            },
            
            'small_cap_rockets': {
                'financial': {
                    'revenue_growth': {'min': 25},
                    'pe_ratio': {'max': 35}
                },
                'market': {
                    'market_cap': {'min': 100000000, 'max': 2000000000}  # $100M - $2B
                },
                'technical': {
                    'price_change_1m': {'min': 5}
                }
            },
            
            'turnaround_candidates': {
                'technical': {
                    'price_change_52w': {'min': -50, 'max': -10},
                    'rsi': {'min': 25, 'max': 45}
                },
                'financial': {
                    'debt_to_equity': {'max': 1.0},
                    'pe_ratio': {'min': 5, 'max': 20}
                }
            },
            
            'quality_growth': {
                'financial': {
                    'roe': {'min': 15},
                    'revenue_growth': {'min': 10},
                    'debt_to_equity': {'max': 0.4},
                    'pe_ratio': {'max': 25}
                },
                'technical': {
                    'price_above_ma50': True
                }
            }
        }
    
    def combine_criteria(self, *strategies: str) -> Dict:
        """Combine multiple predefined strategies"""
        default_strategies = self.get_default_strategies()
        combined = {}
        
        for strategy in strategies:
            if strategy in default_strategies:
                strategy_criteria = default_strategies[strategy]
                
                for section, criteria in strategy_criteria.items():
                    if section not in combined:
                        combined[section] = {}
                    
                    combined[section].update(criteria)
        
        return combined
    
    def create_custom_criteria(self, 
                              financial_metrics: Dict = None,
                              technical_metrics: Dict = None,
                              market_metrics: Dict = None) -> Dict:
        """Create custom screening criteria"""
        criteria = {}
        
        if financial_metrics:
            criteria['financial'] = financial_metrics
        
        if technical_metrics:
            criteria['technical'] = technical_metrics
        
        if market_metrics:
            criteria['market'] = market_metrics
        
        return criteria
    
    def get_available_metrics(self) -> Dict[str, List[str]]:
        """Get list of available metrics for screening"""
        return {
            'financial': [
                'pe_ratio', 'pb_ratio', 'ps_ratio', 'ev_revenue',
                'roe', 'roa', 'net_margin', 'debt_to_equity', 'debt_to_assets',
                'revenue_growth', 'earnings_growth', 'dividend_yield', 'payout_ratio',
                'market_cap', 'enterprise_value', 'quality_score'
            ],
            'technical': [
                'price_change_1d', 'price_change_5d', 'price_change_1m', 'price_change_52w',
                'rsi', 'macd', 'macd_signal', 'macd_histogram',
                'ma20', 'ma50', 'ma200', 'price_above_ma20', 'price_above_ma50', 'price_above_ma200',
                'bb_upper', 'bb_lower', 'bb_position', 'volume_ratio', 'avg_volume_20d',
                'stoch_k', 'stoch_d', 'williams_r', 'atr', 'atr_percent', 'cci',
                'distance_from_52w_high', 'distance_from_ma20'
            ],
            'market': [
                'market_cap', 'sector', 'volume', 'turnover'
            ]
        }
    
    def get_criteria_description(self, criteria: Dict) -> str:
        """Generate human-readable description of criteria"""
        descriptions = []
        
        for section, metrics in criteria.items():
            section_desc = f"{section.title()} Criteria:"
            metric_descs = []
            
            for metric, condition in metrics.items():
                if isinstance(condition, dict):
                    if 'min' in condition and 'max' in condition:
                        metric_descs.append(f"  {metric}: {condition['min']} to {condition['max']}")
                    elif 'min' in condition:
                        metric_descs.append(f"  {metric}: > {condition['min']}")
                    elif 'max' in condition:
                        metric_descs.append(f"  {metric}: < {condition['max']}")
                else:
                    metric_descs.append(f"  {metric}: {condition}")
            
            if metric_descs:
                descriptions.append(section_desc)
                descriptions.extend(metric_descs)
        
        return "\n".join(descriptions)
