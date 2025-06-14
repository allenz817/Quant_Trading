# Quantitative Finance - Trading Strategy Backtester

A comprehensive Python-based backtesting framework for evaluating trading strategies using technical indicators.

## Features

- **Multiple Technical Indicators**: RSI, MACD, Bollinger Bands, Stochastics, candlestick patterns, moving averages, ADX, and more
- **Flexible Strategy Testing**: Run strategies individually or combine multiple indicators with custom weights
- **Desktop GUI Application**: User-friendly interface for uploading CSV data and configuring backtests
- **Historical Data Integration**: Automated data retrieval via yfinance library
- **Comprehensive Analytics**: Detailed performance metrics including Sharpe ratio, drawdown analysis, and trade statistics

## Quick Start

### Command Line Usage
```bash
python Backtesting_New/execution.py
```

### Desktop Application
```bash
python backtesting_app.py
```

## Project Structure

- `Backtesting_New/` - Main backtesting framework
  - `signals/` - Individual technical indicator implementations
  - `strategy_combined.py` - Multi-indicator weighted strategies
  - `execution.py` - Command-line backtesting script
- `backtesting_app.py` - GUI desktop application

## Requirements

- Python 3.7+
- backtesting
- yfinance
- pandas
- numpy
- talib
- tkinter (for GUI)

Built on the Backtesting library for Python.