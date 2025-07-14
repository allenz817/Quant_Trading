"""
CSV export functionality
"""

import pandas as pd
import numpy as np
from datetime import datetime
import logging
from typing import Dict, List
import os

class CSVExporter:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def export_screening_results(self, screening_results: Dict[str, pd.DataFrame], 
                                base_filename: str):
        """Export screening results to CSV files"""
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_name = os.path.splitext(base_filename)[0]
        
        # Export summary
        self._export_summary(screening_results, f"{base_name}_summary_{timestamp}.csv")
        
        # Export individual strategies
        for strategy_name, results_df in screening_results.items():
            if not results_df.empty:
                filename = f"{base_name}_{strategy_name}_{timestamp}.csv"
                self._export_strategy_results(results_df, filename, strategy_name)
    
    def _export_summary(self, screening_results: Dict, filename: str):
        """Export summary statistics to CSV"""
        summary_data = []
        
        for strategy_name, results_df in screening_results.items():
            if not results_df.empty:
                summary_row = {
                    'strategy': strategy_name,
                    'stocks_found': len(results_df),
                    'avg_ranking_score': results_df['ranking_score'].mean() if 'ranking_score' in results_df.columns else None,
                    'top_stock': results_df.iloc[0]['symbol'] if 'symbol' in results_df.columns else None,
                    'top_stock_score': results_df.iloc[0]['ranking_score'] if 'ranking_score' in results_df.columns else None,
                }
                
                # Add average metrics
                if 'pe_ratio' in results_df.columns:
                    summary_row['avg_pe_ratio'] = results_df['pe_ratio'].mean()
                
                if 'roe' in results_df.columns:
                    summary_row['avg_roe'] = results_df['roe'].mean()
                
                if 'market_cap' in results_df.columns:
                    summary_row['avg_market_cap'] = results_df['market_cap'].mean()
                
                summary_data.append(summary_row)
        
        if summary_data:
            summary_df = pd.DataFrame(summary_data)
            summary_df = summary_df.round(2)
            summary_df.to_csv(filename, index=False)
            self.logger.info(f"Summary exported to {filename}")
    
    def _export_strategy_results(self, results_df: pd.DataFrame, filename: str, strategy_name: str):
        """Export individual strategy results to CSV"""
        
        # Select and order columns for export
        export_df = self._prepare_export_dataframe(results_df)
        
        # Add metadata header
        with open(filename, 'w') as f:
            f.write(f"# Stock Screening Results - {strategy_name}\n")
            f.write(f"# Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"# Total stocks: {len(export_df)}\n")
            f.write("# \n")
        
        # Append the data
        export_df.to_csv(filename, mode='a', index=False)
        self.logger.info(f"Strategy results exported to {filename}")
    
    def _prepare_export_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Prepare DataFrame for export with proper column ordering and formatting"""
        
        # Define preferred column order
        preferred_order = [
            'rank', 'symbol', 'name', 'ranking_score',
            'price', 'change_rate', 'volume', 'market_cap',
            'pe_ratio', 'pb_ratio', 'roe', 'roa', 'debt_to_equity', 'net_margin',
            'rsi', 'macd', 'price_change_1d', 'price_change_1m', 'volume_ratio',
            'price_above_ma20', 'price_above_ma50', 'quality_score'
        ]
        
        # Select available columns in preferred order
        available_columns = [col for col in preferred_order if col in df.columns]
        
        # Add remaining columns
        remaining_columns = [col for col in df.columns if col not in available_columns]
        export_columns = available_columns + remaining_columns
        
        export_df = df[export_columns].copy()
        
        # Round numeric columns
        numeric_columns = export_df.select_dtypes(include=[np.number]).columns
        export_df[numeric_columns] = export_df[numeric_columns].round(4)
        
        # Format percentage columns
        percentage_columns = ['change_rate', 'roe', 'roa', 'net_margin', 'price_change_1d', 'price_change_1m']
        for col in percentage_columns:
            if col in export_df.columns:
                export_df[col] = export_df[col].round(2)
        
        return export_df
    
    def export_watchlist(self, results_df: pd.DataFrame, filename: str, format_type: str = 'simple'):
        """Export stock symbols as a watchlist"""
        
        if results_df.empty or 'symbol' not in results_df.columns:
            self.logger.warning("No symbols available for watchlist export")
            return
        
        symbols = results_df['symbol'].tolist()
        
        if format_type == 'simple':
            # Simple list of symbols
            with open(filename, 'w') as f:
                for symbol in symbols:
                    f.write(f"{symbol}\n")
        
        elif format_type == 'detailed':
            # Detailed watchlist with additional info
            watchlist_data = []
            for _, row in results_df.iterrows():
                watchlist_data.append({
                    'symbol': row.get('symbol', ''),
                    'name': row.get('name', ''),
                    'rank': row.get('rank', ''),
                    'score': row.get('ranking_score', ''),
                    'price': row.get('price', ''),
                    'market_cap': row.get('market_cap', '')
                })
            
            watchlist_df = pd.DataFrame(watchlist_data)
            watchlist_df.to_csv(filename, index=False)
        
        elif format_type == 'trading_view':
            # TradingView compatible format
            with open(filename, 'w') as f:
                symbol_string = ','.join(symbols)
                f.write(symbol_string)
        
        self.logger.info(f"Watchlist exported to {filename} in {format_type} format")
    
    def export_comparison(self, screening_results: Dict[str, pd.DataFrame], filename: str):
        """Export comparison between different strategies"""
        
        if len(screening_results) < 2:
            self.logger.warning("Need at least 2 strategies for comparison")
            return
        
        # Find common stocks across strategies
        all_symbols = set()
        strategy_symbols = {}
        
        for strategy_name, results_df in screening_results.items():
            if not results_df.empty and 'symbol' in results_df.columns:
                symbols = set(results_df['symbol'].tolist())
                strategy_symbols[strategy_name] = symbols
                all_symbols.update(symbols)
        
        # Create comparison matrix
        comparison_data = []
        
        for symbol in sorted(all_symbols):
            row = {'symbol': symbol}
            
            # Check which strategies contain this symbol
            for strategy_name in strategy_symbols:
                row[f'{strategy_name}_included'] = symbol in strategy_symbols[strategy_name]
                
                # Add rank if available
                if symbol in strategy_symbols[strategy_name]:
                    strategy_df = screening_results[strategy_name]
                    stock_row = strategy_df[strategy_df['symbol'] == symbol]
                    if not stock_row.empty and 'rank' in stock_row.columns:
                        row[f'{strategy_name}_rank'] = stock_row.iloc[0]['rank']
            
            # Count how many strategies include this stock
            row['strategy_count'] = sum(1 for strategy in strategy_symbols 
                                      if symbol in strategy_symbols[strategy])
            
            comparison_data.append(row)
        
        comparison_df = pd.DataFrame(comparison_data)
        comparison_df = comparison_df.sort_values('strategy_count', ascending=False)
        
        comparison_df.to_csv(filename, index=False)
        self.logger.info(f"Strategy comparison exported to {filename}")
    
    def export_performance_tracking(self, results_df: pd.DataFrame, filename: str):
        """Export data for performance tracking"""
        
        if results_df.empty:
            return
        
        # Create a simplified tracking format
        tracking_data = []
        
        for _, row in results_df.iterrows():
            tracking_data.append({
                'date': datetime.now().strftime('%Y-%m-%d'),
                'symbol': row.get('symbol', ''),
                'rank': row.get('rank', ''),
                'score': row.get('ranking_score', ''),
                'price': row.get('price', ''),
                'pe_ratio': row.get('pe_ratio', ''),
                'roe': row.get('roe', ''),
                'rsi': row.get('rsi', ''),
                'price_change_1d': row.get('price_change_1d', '')
            })
        
        tracking_df = pd.DataFrame(tracking_data)
        
        # Check if file exists to append or create new
        if os.path.exists(filename):
            # Append to existing file
            tracking_df.to_csv(filename, mode='a', header=False, index=False)
        else:
            # Create new file
            tracking_df.to_csv(filename, index=False)
        
        self.logger.info(f"Performance tracking data exported to {filename}")
    
    def create_batch_export(self, screening_results: Dict[str, pd.DataFrame], output_dir: str):
        """Create a complete batch export with all formats"""
        
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Export summary
        summary_file = os.path.join(output_dir, f"summary_{timestamp}.csv")
        self._export_summary(screening_results, summary_file)
        
        # Export individual strategies
        for strategy_name, results_df in screening_results.items():
            if not results_df.empty:
                strategy_file = os.path.join(output_dir, f"{strategy_name}_{timestamp}.csv")
                self._export_strategy_results(results_df, strategy_file, strategy_name)
                
                # Export watchlist
                watchlist_file = os.path.join(output_dir, f"{strategy_name}_watchlist_{timestamp}.txt")
                self.export_watchlist(results_df, watchlist_file, 'simple')
        
        # Export comparison if multiple strategies
        if len(screening_results) > 1:
            comparison_file = os.path.join(output_dir, f"strategy_comparison_{timestamp}.csv")
            self.export_comparison(screening_results, comparison_file)
        
        self.logger.info(f"Batch export completed in {output_dir}")
