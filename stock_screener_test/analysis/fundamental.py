"""
Fundamental analysis calculations
"""

import pandas as pd
import numpy as np
from typing import Dict
import logging

class FundamentalAnalysis:
    def __init__(self, futu_client):
        self.futu_client = futu_client
        self.logger = logging.getLogger(__name__)
    
    def get_financial_metrics(self, stock_code: str) -> Dict:
        """Calculate fundamental financial metrics"""
        try:
            # Get financial data
            financial_data = self.futu_client.get_financial_data(stock_code)
            
            if not financial_data:
                self.logger.warning(f"No financial data for {stock_code}")
                return {}
            
            # Get current price for market-based ratios
            price_data = self.futu_client.get_current_price(stock_code)
            current_price = price_data.get('price', 0)
            
            # Get basic info for shares outstanding
            basic_info = self.futu_client.get_basic_info(stock_code)
            market_cap = basic_info.get('market_cap', 0)
            
            metrics = {}
            
            # Extract financial data
            revenue = financial_data.get('revenue', 0)
            net_income = financial_data.get('net_income', 0)
            total_assets = financial_data.get('total_assets', 0)
            total_equity = financial_data.get('total_equity', 0)
            total_debt = financial_data.get('total_debt', 0)
            eps = financial_data.get('eps', 0)
            book_value_per_share = financial_data.get('book_value_per_share', 0)
            
            # Calculate shares outstanding from market cap and price
            shares_outstanding = market_cap / current_price if current_price > 0 else 0
            
            # Valuation Ratios
            if eps > 0:
                metrics['pe_ratio'] = current_price / eps
            
            if book_value_per_share > 0:
                metrics['pb_ratio'] = current_price / book_value_per_share
            
            if revenue > 0 and shares_outstanding > 0:
                revenue_per_share = revenue / shares_outstanding
                metrics['ps_ratio'] = current_price / revenue_per_share
            
            # Profitability Ratios
            if total_equity > 0:
                metrics['roe'] = (net_income / total_equity) * 100  # ROE as percentage
            
            if total_assets > 0:
                metrics['roa'] = (net_income / total_assets) * 100  # ROA as percentage
            
            if revenue > 0:
                metrics['net_margin'] = (net_income / revenue) * 100
                
            # Calculate gross profit margin (if available)
            # Note: This would require more detailed financial data
            
            # Leverage Ratios
            if total_equity > 0:
                metrics['debt_to_equity'] = total_debt / total_equity
            
            if total_assets > 0:
                metrics['debt_to_assets'] = total_debt / total_assets
            
            # Asset efficiency
            if total_assets > 0:
                metrics['asset_turnover'] = revenue / total_assets
            
            # Market metrics
            metrics['market_cap'] = market_cap
            
            # Calculate enterprise value (simplified)
            # EV = Market Cap + Total Debt - Cash
            # Note: We don't have cash data, so this is simplified
            metrics['enterprise_value'] = market_cap + total_debt
            
            # EV/Revenue ratio
            if revenue > 0:
                metrics['ev_revenue'] = metrics['enterprise_value'] / revenue
            
            # Working capital related metrics would require balance sheet details
            
            # Growth metrics (would require historical data)
            # This is a placeholder - you'd need multiple quarters of data
            metrics['revenue_growth'] = None  # Year-over-year revenue growth
            metrics['earnings_growth'] = None  # Year-over-year earnings growth
            
            # Dividend metrics (would require dividend data from API)
            metrics['dividend_yield'] = None
            metrics['payout_ratio'] = None
            
            # Clean up any infinite or NaN values
            for key, value in metrics.items():
                if value is not None and (np.isinf(value) or np.isnan(value)):
                    metrics[key] = None
            
            return metrics
            
        except Exception as e:
            self.logger.error(f"Error calculating financial metrics for {stock_code}: {e}")
            return {}
    
    def calculate_intrinsic_value(self, stock_code: str, method: str = 'dcf') -> Dict:
        """Calculate intrinsic value using various methods"""
        try:
            financial_data = self.futu_client.get_financial_data(stock_code)
            
            if not financial_data:
                return {}
            
            valuation = {}
            
            if method == 'dcf':
                # Simplified DCF model
                # This is a very basic implementation
                free_cash_flow = financial_data.get('net_income', 0)  # Simplified
                growth_rate = 0.05  # Assumed 5% growth
                discount_rate = 0.10  # Assumed 10% discount rate
                terminal_growth = 0.03  # Assumed 3% terminal growth
                
                if free_cash_flow > 0:
                    # 5-year projection
                    years = 5
                    pv_sum = 0
                    for year in range(1, years + 1):
                        future_cf = free_cash_flow * ((1 + growth_rate) ** year)
                        pv = future_cf / ((1 + discount_rate) ** year)
                        pv_sum += pv
                    
                    # Terminal value
                    terminal_cf = free_cash_flow * ((1 + growth_rate) ** years) * (1 + terminal_growth)
                    terminal_value = terminal_cf / (discount_rate - terminal_growth)
                    pv_terminal = terminal_value / ((1 + discount_rate) ** years)
                    
                    enterprise_value = pv_sum + pv_terminal
                    valuation['dcf_enterprise_value'] = enterprise_value
            
            elif method == 'pe_relative':
                # P/E relative valuation
                industry_pe = 20  # This would come from industry averages
                eps = financial_data.get('eps', 0)
                
                if eps > 0:
                    valuation['relative_value_pe'] = eps * industry_pe
            
            return valuation
            
        except Exception as e:
            self.logger.error(f"Error calculating intrinsic value for {stock_code}: {e}")
            return {}
    
    def get_quality_score(self, stock_code: str) -> Dict:
        """Calculate a quality score based on fundamental metrics"""
        try:
            metrics = self.get_financial_metrics(stock_code)
            
            if not metrics:
                return {}
            
            score = 0
            max_score = 0
            details = {}
            
            # ROE score (0-20 points)
            roe = metrics.get('roe', 0)
            if roe is not None:
                if roe > 20:
                    roe_score = 20
                elif roe > 15:
                    roe_score = 15
                elif roe > 10:
                    roe_score = 10
                elif roe > 5:
                    roe_score = 5
                else:
                    roe_score = 0
                score += roe_score
                details['roe_score'] = roe_score
            max_score += 20
            
            # Debt-to-equity score (0-15 points)
            debt_to_equity = metrics.get('debt_to_equity', float('inf'))
            if debt_to_equity is not None:
                if debt_to_equity < 0.3:
                    debt_score = 15
                elif debt_to_equity < 0.5:
                    debt_score = 10
                elif debt_to_equity < 1.0:
                    debt_score = 5
                else:
                    debt_score = 0
                score += debt_score
                details['debt_score'] = debt_score
            max_score += 15
            
            # P/E ratio score (0-15 points)
            pe_ratio = metrics.get('pe_ratio', float('inf'))
            if pe_ratio is not None and pe_ratio > 0:
                if 10 <= pe_ratio <= 20:
                    pe_score = 15
                elif 5 <= pe_ratio <= 25:
                    pe_score = 10
                elif pe_ratio <= 30:
                    pe_score = 5
                else:
                    pe_score = 0
                score += pe_score
                details['pe_score'] = pe_score
            max_score += 15
            
            # Net margin score (0-10 points)
            net_margin = metrics.get('net_margin', 0)
            if net_margin is not None:
                if net_margin > 20:
                    margin_score = 10
                elif net_margin > 10:
                    margin_score = 7
                elif net_margin > 5:
                    margin_score = 5
                elif net_margin > 0:
                    margin_score = 2
                else:
                    margin_score = 0
                score += margin_score
                details['margin_score'] = margin_score
            max_score += 10
            
            # Calculate final quality score as percentage
            quality_score = (score / max_score) * 100 if max_score > 0 else 0
            
            return {
                'quality_score': quality_score,
                'score_breakdown': details,
                'total_score': score,
                'max_possible_score': max_score
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating quality score for {stock_code}: {e}")
            return {}
