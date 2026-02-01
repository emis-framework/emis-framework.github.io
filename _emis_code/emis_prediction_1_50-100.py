"""
测试不同股票数量对纠缠熵效果的影响
"""

import numpy as np
import pandas as pd
import yfinance as yf
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

def get_sp500_tickers():
    """获取S&P 500成分股"""
    # 常用的大盘股列表（按市值排序）
    tickers_50 = [
        'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META',
        'NVDA', 'BRK-B', 'JPM', 'JNJ', 'V',
        'PG', 'UNH', 'HD', 'MA', 'DIS',
        'PYPL', 'VZ', 'ADBE', 'NFLX', 'CRM',
        'INTC', 'CMCSA', 'PFE', 'KO', 'PEP',
        'T', 'MRK', 'WMT', 'ABT', 'CVX',
        'XOM', 'BA', 'CSCO', 'WFC', 'C',
        'ORCL', 'ACN', 'COST', 'NKE', 'MCD',
        'DHR', 'NEE', 'LLY', 'TXN', 'QCOM',
        'LOW', 'UPS', 'BMY', 'AMGN', 'IBM'
    ]
    
    tickers_100 = tickers_50 + [
        'GS', 'CAT', 'HON', 'AMD', 'SBUX',
        'ISRG', 'BKNG', 'MDLZ', 'GILD', 'ADI',
        'AXP', 'BLK', 'SPGI', 'SYK', 'MMC',
        'CB', 'PLD', 'MO', 'DUK', 'SO',
        'CL', 'GD', 'USB', 'TJX', 'PNC',
        'ITW', 'CME', 'CI', 'ZTS', 'REGN',
        'BDX', 'AON', 'NSC', 'SCHW', 'FIS',
        'EQIX', 'SHW', 'ATVI', 'TGT', 'APD',
        'CSX', 'ICE', 'HUM', 'MU', 'LRCX',
        'CCI', 'D', 'FISV', 'KMB', 'NOC'
    ]
    
    return {
        50: tickers_50,
        100: tickers_100
    }

def compute_returns(prices):
    returns = np.log(prices / prices.shift(1))
    returns = returns.dropna()
    return returns

def compute_entanglement_entropy(returns, window=60):
    S_list = []
    dates = []
    N = returns.shape[1]
    
    for t in range(window, len(returns)):
        window_returns = returns.iloc[t-window:t]
        Sigma = window_returns.corr().values
        Sigma = Sigma + np.eye(N) * 1e-6
        det_Sigma = np.linalg.det(Sigma)
        
        if det_Sigma > 0:
            S = -np.log(det_Sigma) / N
        else:
            S = np.nan
        
        S_list.append(S)
        dates.append(returns.index[t])
    
    return pd.Series(S_list, index=dates, name='EntanglementEntropy')

def test_strategy(S, sp500, S_percentile=90, horizon=30):
    """测试高S买入策略"""
    S_threshold = S.quantile(S_percentile / 100)
    
    results = []
    for t in range(len(S) - horizon):
        date = S.index[t]
        S_value = S.iloc[t]
        
        if S_value > S_threshold:
            if date in sp500.index:
                idx = sp500.index.get_loc(date)
                if idx + horizon < len(sp500):
                    ret = np.log(sp500.iloc[idx + horizon] / sp500.iloc[idx])
                    results.append({
                        'date': date,
                        'S': S_value,
                        'return': ret,
                        'win': ret > 0
                    })
    
    if len(results) > 0:
        df = pd.DataFrame(results)
        return {
            'n_trades': len(df),
            'win_rate': df['win'].mean(),
            'avg_return': df['return'].mean(),
            'threshold': S_threshold
        }
    return None

def main():
    print("="*60)
    print("测试不同股票数量的效果")
    print("="*60)
    
    # 获取 S&P 500 指数
    print("\n下载 S&P 500 指数...")
    sp500_data = yf.download('^GSPC', start='2010-01-01', progress=False)
    sp500 = sp500_data['Close']
    if isinstance(sp500, pd.DataFrame):
        sp500 = sp500.iloc[:, 0]
    
    # 测试不同股票数量
    ticker_sets = get_sp500_tickers()
    results = {}
    
    for n_stocks, tickers in ticker_sets.items():
        print(f"\n{'='*60}")
        print(f"测试 {n_stocks} 只股票")
        print("="*60)
        
        # 下载数据
        print(f"下载 {len(tickers)} 只股票...")
        data = yf.download(tickers, start='2010-01-01', progress=False)
        prices = data['Close']
        
        # 清理数据
        prices = prices.dropna(axis=1, how='all')
        prices = prices.ffill()
        prices = prices.dropna()
        
        actual_n = len(prices.columns)
        print(f"实际获取: {actual_n} 只股票, {len(prices)} 天")
        
        # 计算收益率和纠缠熵
        returns = compute_returns(prices)
        S = compute_entanglement_entropy(returns, window=60)
        
        print(f"纠缠熵范围: [{S.min():.2f}, {S.max():.2f}]")
        print(f"均值: {S.mean():.2f}, 标准差: {S.std():.2f}")
        
        # 测试策略
        result = test_strategy(S, sp500, S_percentile=90, horizon=30)
        
        if result:
            print(f"\n策略结果 (S > 90%分位):")
            print(f"  阈值: {result['threshold']:.2f}")
            print(f"  交易次数: {result['n_trades']}")
            print(f"  胜率: {result['win_rate']:.1%}")
            print(f"  平均收益: {result['avg_return']:.1%}")
            
            results[n_stocks] = result
        
        # 计算相关性
        common_idx = S.index.intersection(sp500.index)
        S_aligned = S.loc[common_idx]
        future_30d = np.log(sp500.shift(-30) / sp500).loc[common_idx]
        valid = ~(S_aligned.isna() | future_30d.isna())
        corr = S_aligned[valid].corr(future_30d[valid])
        print(f"  S与30日收益相关性: r = {corr:.3f}")
        
        results[n_stocks]['correlation'] = corr
    
    # 汇总对比
    print("\n" + "="*60)
    print("汇总对比")
    print("="*60)
    print(f"\n{'股票数':<10} {'胜率':<10} {'平均收益':<12} {'相关性':<10}")
    print("-"*42)
    for n, r in results.items():
        print(f"{n:<10} {r['win_rate']:<10.1%} {r['avg_return']:<12.1%} {r['correlation']:<10.3f}")
    
    return results

if __name__ == "__main__":
    results = main()