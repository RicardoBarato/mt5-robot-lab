# Excel Export Schema

Initial export columns:

```text
rank
candidate_id
lab_id
seed_family
symbol
broker_symbol
timeframe
years_tested
initial_balance_usd
net_profit_usd
final_balance_usd
max_drawdown_pct
profit_factor
total_trades
win_rate
martingale_used
grid_used
no_stop_used
intelligence_mode
source_file
report_path
notes
```

CSV and Markdown are required. XLSX is optional when `openpyxl` is available.
