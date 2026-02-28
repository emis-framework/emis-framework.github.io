# P1: Market Entanglement Entropy

This repository contains the code for computing market entanglement entropy, a correlation-based indicator for detecting market bottoms.

## Paper

**"Entanglement Entropy as a Universal Market Bottom Indicator: Evidence from Global Equity Markets"**

- SSRN: [link after upload]
- DOI: [link after publication]

## Key Formula

$$\mathcal{S}(t) = -\frac{1}{N}\log\det\Sigma(t)$$

Where:
- $\Sigma(t)$ = rolling correlation matrix of asset returns
- $N$ = number of assets
- Window = 60 trading days

## Main Finding

High entropy = market bottom (not crash warning)

| Market             | Win Rate | p-value |
| ------------------ | -------- | ------- |
| US (S&P 500)       | 90.4%    | < 10⁻⁴⁷ |
| Japan (Nikkei 225) | 87.0%    | < 10⁻³² |
| Germany (DAX 40)   | 95.1%    | < 10⁻²⁴ |

## Installation

```bash
pip install -r requirements.txt
```

## File Structure

```
p1-entanglement-entropy/
│
├── README.md
├── requirements.txt
│
├── emis_p1_vs_vix_since_2005.py          # US: download & compute entropy, compare with VIX
├── emis_p1_nikkie225_since_2005.py       # Japan: download & compute entropy
├── emis_p1_dax40_with_download.py        # Germany: download DAX 40 stock data
├── emis_p1_dax40_since_2005.py           # Germany: compute entropy
├── emis_p1_chart_since_2005.py           # Generate 4 paper figures
├── emis_p1_cmp_3_locations_3_trades_vix.py  # Generate comparison tables (3 markets × 3 strategies × VIX)
│
├── cache/                                 # Cached data files
│   ├── entropy_US_since2005.csv
│   ├── entropy_Japan_since2005_v2.csv
│   ├── entropy_DAX_historical.csv
│   ├── sp500.csv
│   ├── index_Japan_since2005.csv
│   ├── index_DAX.csv
│   ├── stocks_50_since2005.csv
│   ├── stocks_Japan_since2005_v2.csv
│   ├── stocks_DAX_v2.csv
│   └── vix.csv
│
└── data-figure/                           # Output figures and results
    ├── figure1_entropy_timeseries.png
    ├── figure2_return_distribution.png
    ├── figure3_cross_market.png
    ├── figure4_emis_vs_vix.png
    ├── emis_results_DAX.csv
    └── paper_results_complete.csv
```

## Scripts Description

| Script                                    | Description                                                          |
| ----------------------------------------- | -------------------------------------------------------------------- |
| `emis_p1_vs_vix_since_2005.py`            | Download S&P 500 top 50 stocks, compute entropy, compare with VIX    |
| `emis_p1_nikkie225_since_2005.py`         | Download Nikkei 225 top 50 stocks, compute entropy                   |
| `emis_p1_dax40_with_download.py`          | Download DAX 40 component stocks                                     |
| `emis_p1_dax40_since_2005.py`             | Compute entropy for DAX 40                                           |
| `emis_p1_chart_since_2005.py`             | Generate all 4 figures for the paper                                 |
| `emis_p1_cmp_3_locations_3_trades_vix.py` | Generate comparison tables (3 markets, 3 trading strategies, vs VIX) |

## Quick Start

### Step 1: Compute entropy for each market

```bash
# US market (S&P 500)
python emis_p1_vs_vix_since_2005.py

# Japan market (Nikkei 225)
python emis_p1_nikkie225_since_2005.py

# Germany market (DAX 40)
python emis_p1_dax40_with_download.py
python emis_p1_dax40_since_2005.py
```

### Step 2: Generate paper figures

```bash
python emis_p1_chart_since_2005.py
```

### Step 3: Generate comparison tables

```bash
python emis_p1_cmp_3_locations_3_trades_vix.py
```

## Core Algorithm

```python
import numpy as np
import pandas as pd

def compute_entropy(returns, window=60):
    """
    Compute market entanglement entropy.
    
    Parameters
    ----------
    returns : pd.DataFrame
        Daily log returns, shape (T, N) where T = days, N = assets
    window : int
        Rolling window size in trading days
    
    Returns
    -------
    pd.Series
        Entropy time series
    """
    entropy = []
    dates = []
    
    for t in range(window, len(returns)):
        # Get window data
        R = returns.iloc[t-window:t]
        
        # Compute correlation matrix
        corr = R.corr().values
        
        # Compute log-determinant (numerically stable)
        sign, logdet = np.linalg.slogdet(corr)
        if sign > 0:
            S = -logdet / len(corr)
        else:
            S = np.nan
        
        entropy.append(S)
        dates.append(returns.index[t])
    
    return pd.Series(entropy, index=dates, name='entropy')
```

## Parameters

| Parameter   | Default                       | Description                             |
| ----------- | ----------------------------- | --------------------------------------- |
| `window`    | 60                            | Rolling window (trading days)           |
| `threshold` | 90th percentile               | Signal threshold (from training period) |
| `holding`   | 30                            | Holding period (trading days)           |
| `n_stocks`  | 50 (US, Japan) / 40 (Germany) | Number of stocks                        |
| `training`  | 2005-2019                     | Training period                         |
| `testing`   | 2020-2026                     | Out-of-sample test period               |

## Data Sources

All price data obtained from Yahoo Finance via `yfinance` library.

| Market  | Index      | Stocks               | Period    |
| ------- | ---------- | -------------------- | --------- |
| US      | S&P 500    | Top 50 by market cap | 2005-2026 |
| Japan   | Nikkei 225 | Top 50 by market cap | 2005-2026 |
| Germany | DAX        | 40 components        | 2005-2026 |

## Output Files

### Cached Data (`cache/`)

| File                             | Description                 |
| -------------------------------- | --------------------------- |
| `entropy_US_since2005.csv`       | US entropy time series      |
| `entropy_Japan_since2005_v2.csv` | Japan entropy time series   |
| `entropy_DAX_historical.csv`     | Germany entropy time series |
| `sp500.csv`                      | S&P 500 index prices        |
| `vix.csv`                        | VIX index data              |

### Figures (`data-figure/`)

| File                              | Description                      |
| --------------------------------- | -------------------------------- |
| `figure1_entropy_timeseries.png`  | Entropy time series with signals |
| `figure2_return_distribution.png` | Return distribution comparison   |
| `figure3_cross_market.png`        | Cross-market validation          |
| `figure4_emis_vs_vix.png`         | EMIS vs VIX comparison           |
| `paper_results_complete.csv`      | All numerical results            |

## Citation

If you use this code, please cite:

```bibtex
@article{wang2026entropy,
  author  = {Wang, Fei-Yun},
  title   = {Entanglement Entropy as a Universal Market Bottom Indicator: 
             Evidence from Global Equity Markets},
  journal = {SSRN Working Paper},
  year    = {2026},
  url     = {https://ssrn.com/abstract=XXXXXXX}
}
```

## License

This project is part of the [EMIS Framework](https://github.com/emis-framework/emis-framework.github.io) and is licensed under the MIT License.

## Contact

- Email: wehelpwe@163.com
- EMIS Framework: https://emis-framework.github.io

## Related

- [EMIS Framework](https://github.com/emis-framework/emis-framework.github.io) - Parent project
