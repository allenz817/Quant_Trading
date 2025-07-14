# Stock Screener

A comprehensive Python-based stock screening application that filters stocks based on financial metrics and technical indicators using the Futu API.

## Features

- **Multiple Screening Strategies**: Pre-configured strategies for value, growth, momentum, and dividend stocks
- **Futu API Integration**: Real-time data from US, Hong Kong, and Chinese markets
- **Technical Analysis**: RSI, MACD, Bollinger Bands, moving averages, and more
- **Fundamental Analysis**: P/E ratio, ROE, debt ratios, growth metrics
- **Automated Scheduling**: Run screenings automatically at market open/close
- **Multiple Output Formats**: Excel, CSV, and watchlist exports
- **Parallel Processing**: Efficient data retrieval with configurable worker threads
- **Caching System**: Reduces API calls and improves performance

## Installation

### Prerequisites

1. **Futu OpenAPI**: Install and configure Futu client software
2. **Python 3.7+**: Required for the application

### Setup

1. Clone or download the stock screener files
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Configure Futu OpenAPI:
   - Install Futu software and enable OpenAPI
   - Note: Some features require a valid trading account

## Configuration

### Settings (config/settings.yaml)
```yaml
futu:
  host: "127.0.0.1"
  port: 11111
  timeout: 10

markets:
  - "US"
  - "HK"
  - "CN"

output:
  format: ["excel", "csv"]
  save_path: "./results/"
```

### Strategies (config/strategies.yaml)
Pre-configured screening strategies:
- **value_stocks**: Low P/E, high ROE, low debt
- **growth_stocks**: High revenue/earnings growth
- **momentum_breakout**: High price momentum with volume
- **oversold_bounce**: RSI oversold with recent decline
- **dividend_stocks**: High dividend yield, stable metrics
- **small_cap_growth**: Small-cap stocks with growth metrics

### Watchlists (config/watchlists.yaml)
Custom stock lists for focused screening:
- tech_giants
- financial
- healthcare
- custom (add your own symbols)

## Usage

### Basic Commands

```bash
# Run all strategies for US market
python main.py

# Run specific strategy
python main.py --strategy value_stocks

# Run multiple strategies
python main.py --strategy "value_stocks,growth_stocks"

# Use specific market
python main.py --strategy momentum_breakout --market HK

# Use watchlist instead of full market
python main.py --strategy growth_stocks --watchlist tech_giants

# Export as CSV only
python main.py --strategy value_stocks --output csv

# Limit results and use quick filtering
python main.py --strategy all --max-results 20 --quick-filter
```

### Advanced Usage

```bash
# Screen specific symbols
python main.py --symbols "AAPL,MSFT,GOOGL" --strategy value_stocks

# Use fewer workers for API rate limiting
python main.py --strategy growth_stocks --max-workers 5

# Export watchlists
python main.py --strategy momentum_breakout --watchlist-export

# List available strategies
python main.py --list-strategies

# List available watchlists
python main.py --list-watchlists
```

### Automated Scheduling

```bash
# Start automated daily screening
python run_daily_screen.py

# Manual runs for testing
python run_daily_screen.py --test
python run_daily_screen.py --morning
python run_daily_screen.py --evening
```

## Output Files

### Excel Reports
- **Summary sheet**: Overview of all strategies
- **Individual strategy sheets**: Detailed results for each strategy
- **Analysis sheet**: Cross-strategy comparisons and insights

### CSV Files
- `summary_YYYYMMDD_HHMMSS.csv`: Summary statistics
- `{strategy_name}_YYYYMMDD_HHMMSS.csv`: Individual strategy results
- `strategy_comparison_YYYYMMDD_HHMMSS.csv`: Cross-strategy analysis

### Watchlists
- Simple text files with stock symbols
- Compatible with most trading platforms

## Screening Criteria

### Financial Metrics
- **Valuation**: P/E ratio, P/B ratio, P/S ratio, EV/Revenue
- **Profitability**: ROE, ROA, net margin, gross margin
- **Leverage**: Debt-to-equity, debt-to-assets
- **Growth**: Revenue growth, earnings growth
- **Quality**: Composite quality score

### Technical Indicators
- **Price Action**: Daily, weekly, monthly, 52-week changes
- **Momentum**: RSI, MACD, Stochastic, Williams %R
- **Trend**: Moving averages (20, 50, 200-day)
- **Volatility**: Bollinger Bands, ATR
- **Volume**: Volume ratio, average volume

### Market Metrics
- **Size**: Market capitalization ranges
- **Liquidity**: Trading volume, turnover
- **Sector**: Industry classification

## Customization

### Creating Custom Strategies

Edit `config/strategies.yaml` to add new strategies:

```yaml
my_custom_strategy:
  financial:
    pe_ratio: {min: 5, max: 20}
    roe: {min: 15}
    debt_to_equity: {max: 0.5}
  technical:
    rsi: {min: 30, max: 70}
    price_change_1m: {min: 5}
  market:
    market_cap: {min: 1000000000}  # $1B minimum
```

### Adding Watchlists

Edit `config/watchlists.yaml`:

```yaml
watchlists:
  my_stocks:
    - "AAPL"
    - "MSFT"
    - "GOOGL"
```

## Performance Optimization

### API Rate Limiting
- Use `--max-workers` to control parallel requests
- Enable `--quick-filter` for large stock universes
- Configure caching in settings.yaml

### Memory Management
- Use `--max-stocks` to limit dataset size for testing
- Process in batches for large markets

## Troubleshooting

### Common Issues

1. **Futu Connection Error**:
   - Ensure Futu software is running
   - Check OpenAPI is enabled
   - Verify host/port settings

2. **No Data Retrieved**:
   - Check market hours
   - Verify stock symbols are valid
   - Check API rate limits

3. **Import Errors**:
   - Install all requirements: `pip install -r requirements.txt`
   - For TA-Lib issues, may need binary installation

### Logging

Check log files for detailed error information:
- `screener.log`: Main application logs
- `scheduler.log`: Automated scheduling logs

## File Structure

```
stock_screener/
├── main.py                 # Main application entry point
├── run_daily_screen.py     # Automated scheduling
├── requirements.txt        # Python dependencies
├── config/
│   ├── settings.yaml      # Application configuration
│   ├── strategies.yaml    # Screening strategies
│   └── watchlists.yaml    # Custom stock lists
├── data/
│   ├── futu_client.py     # Futu API integration
│   ├── data_fetcher.py    # Data retrieval with caching
│   └── stock_universe.py  # Stock list management
├── screening/
│   ├── criteria.py        # Criteria definitions
│   └── filters.py         # Filtering logic
├── analysis/
│   ├── technical.py       # Technical indicators
│   ├── fundamental.py     # Financial metrics
│   └── rankings.py        # Stock ranking algorithms
├── output/
│   ├── excel_export.py    # Excel report generation
│   └── csv_export.py      # CSV export functionality
└── results/               # Output directory
```

## License

For personal use only. Ensure compliance with Futu API terms of service.

## Disclaimer

This tool is for educational and research purposes. Past performance does not guarantee future results. Always conduct your own research before making investment decisions.
