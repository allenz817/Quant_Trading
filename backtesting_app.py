import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import threading
import os
import sys

# Add the Backtesting_New directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'Backtesting_New'))

from backtesting import Backtest
from Backtesting_New.strategy_combined import WeightedStrat
from Backtesting_New.signals.rsi import RSIStrategy
from Backtesting_New.signals.macd import MACDStrategy
from Backtesting_New.signals.bb import BBStrategy

class BacktestingApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Stock Trading Strategy Backtester")
        self.root.geometry("1000x700")
        
        # Variables
        self.data_file = tk.StringVar()
        self.strategy_var = tk.StringVar(value="WeightedStrat")
        self.timeframe_var = tk.StringVar(value="1D")
        self.cash_var = tk.DoubleVar(value=10000)
        self.commission_var = tk.DoubleVar(value=0.002)
        
        # Strategy parameters
        self.strategy_params = {}
        
        self.create_widgets()
        
    def create_widgets(self):
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        # File upload section
        file_frame = ttk.LabelFrame(main_frame, text="Data File", padding="10")
        file_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        file_frame.columnconfigure(1, weight=1)
        
        ttk.Label(file_frame, text="CSV File:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        ttk.Entry(file_frame, textvariable=self.data_file, state="readonly").grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 5))
        ttk.Button(file_frame, text="Browse", command=self.browse_file).grid(row=0, column=2)
        
        # Strategy selection
        strategy_frame = ttk.LabelFrame(main_frame, text="Strategy Configuration", padding="10")
        strategy_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        strategy_frame.columnconfigure(1, weight=1)
        
        ttk.Label(strategy_frame, text="Strategy:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        strategy_combo = ttk.Combobox(strategy_frame, textvariable=self.strategy_var, 
                                    values=["WeightedStrat", "RSIStrategy", "MACDStrategy", "BBStrategy"],
                                    state="readonly")
        strategy_combo.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 5))
        strategy_combo.bind('<<ComboboxSelected>>', self.on_strategy_change)
        
        # Backtest parameters
        params_frame = ttk.LabelFrame(main_frame, text="Backtest Parameters", padding="10")
        params_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        params_frame.columnconfigure(1, weight=1)
        
        ttk.Label(params_frame, text="Initial Cash:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        ttk.Entry(params_frame, textvariable=self.cash_var).grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 10))
        
        ttk.Label(params_frame, text="Commission:").grid(row=0, column=2, sticky=tk.W, padx=(0, 5))
        ttk.Entry(params_frame, textvariable=self.commission_var).grid(row=0, column=3, sticky=(tk.W, tk.E))
        
        ttk.Label(params_frame, text="Timeframe:").grid(row=1, column=0, sticky=tk.W, padx=(0, 5))
        timeframe_combo = ttk.Combobox(params_frame, textvariable=self.timeframe_var,
                                     values=["1D", "1W", "1M"], state="readonly")
        timeframe_combo.grid(row=1, column=1, sticky=(tk.W, tk.E), padx=(0, 10))
        
        # Strategy-specific parameters frame
        self.strategy_params_frame = ttk.LabelFrame(main_frame, text="Strategy Parameters", padding="10")
        self.strategy_params_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        self.strategy_params_frame.columnconfigure(1, weight=1)
        
        # Initialize with default strategy parameters
        self.create_strategy_params()
        
        # Control buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=4, column=0, columnspan=2, pady=(0, 10))
        
        ttk.Button(button_frame, text="Run Backtest", command=self.run_backtest).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="Clear Results", command=self.clear_results).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="Save Results", command=self.save_results).pack(side=tk.LEFT)
        
        # Results display
        results_frame = ttk.LabelFrame(main_frame, text="Backtest Results", padding="10")
        results_frame.grid(row=5, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S))
        results_frame.columnconfigure(0, weight=1)
        results_frame.rowconfigure(0, weight=1)
        main_frame.rowconfigure(5, weight=1)
        
        self.results_text = scrolledtext.ScrolledText(results_frame, height=15, width=80)
        self.results_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Progress bar
        self.progress = ttk.Progressbar(main_frame, mode='indeterminate')
        self.progress.grid(row=6, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(5, 0))
        
    def browse_file(self):
        filename = filedialog.askopenfilename(
            title="Select CSV file",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        if filename:
            self.data_file.set(filename)
            self.validate_csv_file(filename)
    
    def validate_csv_file(self, filename):
        try:
            df = pd.read_csv(filename, index_col=0, parse_dates=True)
            required_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
            
            if not all(col in df.columns for col in required_columns):
                messagebox.showerror("Invalid File", 
                                   f"CSV file must contain columns: {', '.join(required_columns)}")
                self.data_file.set("")
                return False
            
            self.results_text.insert(tk.END, f"✓ File loaded successfully: {len(df)} rows\n")
            self.results_text.insert(tk.END, f"  Date range: {df.index[0]} to {df.index[-1]}\n")
            self.results_text.insert(tk.END, f"  Columns: {', '.join(df.columns)}\n\n")
            return True
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to read CSV file: {str(e)}")
            self.data_file.set("")
            return False
    
    def on_strategy_change(self, event=None):
        self.create_strategy_params()
    
    def create_strategy_params(self):
        # Clear existing parameters
        for widget in self.strategy_params_frame.winfo_children():
            widget.destroy()
        
        self.strategy_params.clear()
        
        strategy = self.strategy_var.get()
        
        if strategy == "WeightedStrat":
            self.create_weighted_strat_params()
        elif strategy == "RSIStrategy":
            self.create_rsi_params()
        elif strategy == "MACDStrategy":
            self.create_macd_params()
        elif strategy == "BBStrategy":
            self.create_bb_params()
    
    def create_weighted_strat_params(self):
        params = [
            ("RSI Period", "rsi_daily_days", 10),
            ("RSI Upper Bound", "rsi_upper_bound", 70),
            ("RSI Lower Bound", "rsi_lower_bound", 30),
            ("MACD Fast", "fast_period", 12),
            ("MACD Slow", "slow_period", 26),
            ("MACD Signal", "signal_period", 9),
            ("BB Period", "bb_period", 20),
            ("BB Std Dev", "bb_stdev", 2.1),
            ("RSI Buy Weight", "rsi_daily_weight_buy", 0.5),
            ("RSI Sell Weight", "rsi_daily_weight_sell", 0.25),
            ("MACD Weight", "macd_daily_weight", 0.5),
            ("BB Weight", "bb_weight_buy", 0.5),
            ("Buy Threshold", "buy_threshold", 1.0),
            ("Sell Threshold", "sell_threshold", -1.0),
        ]
        
        self.create_param_widgets(params)
    
    def create_rsi_params(self):
        params = [
            ("RSI Period", "rsi_daily_days", 12),
            ("RSI Upper Bound", "rsi_upper_bound", 75),
            ("RSI Lower Bound", "rsi_lower_bound", 25),
        ]
        
        self.create_param_widgets(params)
    
    def create_macd_params(self):
        params = [
            ("Fast Period", "fast_period", 12),
            ("Slow Period", "slow_period", 26),
            ("Signal Period", "signal_period", 9),
        ]
        
        self.create_param_widgets(params)
    
    def create_bb_params(self):
        params = [
            ("BB Period", "bb_period", 20),
            ("BB Std Dev", "bb_stdev", 2.1),
            ("Volume Avg Period", "volume_avg_period", 20),
        ]
        
        self.create_param_widgets(params)
    
    def create_param_widgets(self, params):
        row = 0
        col = 0
        for label, param_name, default_value in params:
            ttk.Label(self.strategy_params_frame, text=f"{label}:").grid(
                row=row, column=col*2, sticky=tk.W, padx=(0, 5), pady=2)
            
            var = tk.DoubleVar(value=default_value)
            self.strategy_params[param_name] = var
            
            ttk.Entry(self.strategy_params_frame, textvariable=var, width=10).grid(
                row=row, column=col*2+1, sticky=tk.W, padx=(0, 15), pady=2)
            
            col += 1
            if col >= 2:  # 2 columns
                col = 0
                row += 1
    
    def load_and_process_data(self, filename):
        """Load and process the CSV data"""
        try:
            # Load the data
            data = pd.read_csv(filename, index_col=0, parse_dates=True)
            
            # Ensure we have the required columns
            required_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
            if not all(col in data.columns for col in required_columns):
                raise ValueError(f"Missing required columns: {set(required_columns) - set(data.columns)}")
            
            # Select only the required columns in the correct order
            data = data[required_columns]
            
            # Remove any rows with NaN values
            data = data.dropna()
            
            # Sort by date
            data = data.sort_index()
            
            return data
            
        except Exception as e:
            raise Exception(f"Error processing data: {str(e)}")
    
    def get_strategy_class_and_params(self):
        """Get the strategy class and parameters based on user selection"""
        strategy_name = self.strategy_var.get()
        
        # Create parameters dictionary
        params = {}
        for param_name, var in self.strategy_params.items():
            params[param_name] = var.get()
        
        # Get strategy class
        if strategy_name == "WeightedStrat":
            strategy_class = WeightedStrat
        elif strategy_name == "RSIStrategy":
            strategy_class = RSIStrategy
        elif strategy_name == "MACDStrategy":
            strategy_class = MACDStrategy
        elif strategy_name == "BBStrategy":
            strategy_class = BBStrategy
        else:
            raise ValueError(f"Unknown strategy: {strategy_name}")
        
        return strategy_class, params
    
    def run_backtest_thread(self):
        """Run backtest in a separate thread"""
        try:
            if not self.data_file.get():
                messagebox.showerror("Error", "Please select a CSV file first")
                return
            
            self.results_text.insert(tk.END, "=" * 50 + "\n")
            self.results_text.insert(tk.END, f"Starting backtest at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            self.results_text.insert(tk.END, "=" * 50 + "\n\n")
            
            # Load and process data
            self.results_text.insert(tk.END, "Loading data...\n")
            data = self.load_and_process_data(self.data_file.get())
            
            # Get strategy and parameters
            strategy_class, strategy_params = self.get_strategy_class_and_params()
            
            self.results_text.insert(tk.END, f"Strategy: {self.strategy_var.get()}\n")
            self.results_text.insert(tk.END, f"Data points: {len(data)}\n")
            self.results_text.insert(tk.END, f"Date range: {data.index[0]} to {data.index[-1]}\n\n")
            
            # Create strategy class with parameters
            class DynamicStrategy(strategy_class):
                pass
            
            # Set strategy parameters
            for param_name, param_value in strategy_params.items():
                setattr(DynamicStrategy, param_name, param_value)
            
            # Run backtest
            self.results_text.insert(tk.END, "Running backtest...\n")
            bt = Backtest(
                data, 
                DynamicStrategy, 
                cash=self.cash_var.get(),
                commission=self.commission_var.get(),
                exclusive_orders=True
            )
            
            # Run the backtest
            result = bt.run()
            
            # Store results for saving
            self.last_result = result
            self.last_bt = bt
            
            # Display results
            self.results_text.insert(tk.END, "\n" + "=" * 30 + " RESULTS " + "=" * 30 + "\n\n")
            
            # Key performance metrics
            metrics = [
                ("Start", result['Start']),
                ("End", result['End']),
                ("Duration", result['Duration']),
                ("Exposure Time [%]", f"{result['Exposure Time [%]']:.2f}%"),
                ("Equity Final [$]", f"${result['Equity Final [$]']:,.2f}"),
                ("Equity Peak [$]", f"${result['Equity Peak [$]']:,.2f}"),
                ("Return [%]", f"{result['Return [%]']:.2f}%"),
                ("Buy & Hold Return [%]", f"{result['Buy & Hold Return [%]']:.2f}%"),
                ("Return (Ann.) [%]", f"{result['Return (Ann.) [%]']:.2f}%"),
                ("Volatility (Ann.) [%]", f"{result['Volatility (Ann.) [%]']:.2f}%"),
                ("Sharpe Ratio", f"{result['Sharpe Ratio']:.3f}"),
                ("Sortino Ratio", f"{result['Sortino Ratio']:.3f}"),
                ("Calmar Ratio", f"{result['Calmar Ratio']:.3f}"),
                ("Max. Drawdown [%]", f"{result['Max. Drawdown [%]']:.2f}%"),
                ("Avg. Drawdown [%]", f"{result['Avg. Drawdown [%]']:.2f}%"),
                ("Max. Drawdown Duration", result['Max. Drawdown Duration']),
                ("Avg. Drawdown Duration", result['Avg. Drawdown Duration']),
                ("# Trades", result['# Trades']),
                ("Win Rate [%]", f"{result['Win Rate [%]']:.2f}%"),
                ("Best Trade [%]", f"{result['Best Trade [%]']:.2f}%"),
                ("Worst Trade [%]", f"{result['Worst Trade [%]']:.2f}%"),
                ("Avg. Trade [%]", f"{result['Avg. Trade [%]']:.2f}%"),
                ("Max. Trade Duration", result['Max. Trade Duration']),
                ("Avg. Trade Duration", result['Avg. Trade Duration']),
                ("Profit Factor", f"{result['Profit Factor']:.3f}"),
                ("Expectancy [%]", f"{result['Expectancy [%]']:.2f}%"),
                ("SQN", f"{result['SQN']:.3f}"),
            ]
            
            for metric, value in metrics:
                self.results_text.insert(tk.END, f"{metric:<25}: {value}\n")
            
            self.results_text.insert(tk.END, "\n" + "=" * 66 + "\n\n")
            self.results_text.insert(tk.END, f"Backtest completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            # Auto-scroll to bottom
            self.results_text.see(tk.END)
            
        except Exception as e:
            self.results_text.insert(tk.END, f"\nERROR: {str(e)}\n\n")
            messagebox.showerror("Backtest Error", str(e))
        
        finally:
            # Hide progress bar
            self.root.after(0, self.progress.stop)
    
    def run_backtest(self):
        """Start backtest in a separate thread"""
        # Show progress bar
        self.progress.start()
        
        # Run backtest in separate thread to prevent GUI freezing
        thread = threading.Thread(target=self.run_backtest_thread)
        thread.daemon = True
        thread.start()
    
    def clear_results(self):
        """Clear the results text"""
        self.results_text.delete(1.0, tk.END)
    
    def save_results(self):
        """Save results to file"""
        if not hasattr(self, 'last_result'):
            messagebox.showwarning("No Results", "No backtest results to save")
            return
        
        filename = filedialog.asksaveasfilename(
            title="Save Results",
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("CSV files", "*.csv"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                if filename.endswith('.csv'):
                    # Save as CSV
                    df = pd.DataFrame([self.last_result])
                    df.to_csv(filename, index=False)
                else:
                    # Save as text
                    with open(filename, 'w') as f:
                        f.write(self.results_text.get(1.0, tk.END))
                
                messagebox.showinfo("Success", f"Results saved to {filename}")
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save results: {str(e)}")

def main():
    root = tk.Tk()
    app = BacktestingApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()