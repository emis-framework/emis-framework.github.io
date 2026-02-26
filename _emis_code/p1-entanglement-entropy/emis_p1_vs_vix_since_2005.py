"""
EMIS vs VIX 完整对比（使用2005年前上市的股票）
"""

"""
# ★★★ 2005年前上市的50只大盘股 ★★★
TICKERS_2005 = [
    # 科技
    'AAPL',   # Apple (1980)
    'MSFT',   # Microsoft (1986)
    'INTC',   # Intel (1971)
    'IBM',    # IBM (1911)
    'CSCO',   # Cisco (1990)
    'ORCL',   # Oracle (1986)
    'TXN',    # Texas Instruments (1953)
    'QCOM',   # Qualcomm (1991)
    'AMAT',   # Applied Materials (1972)
    'ADI',    # Analog Devices (1969)
    
    # 金融
    'JPM',    # JPMorgan (1799)
    'BAC',    # Bank of America (1904)
    'WFC',    # Wells Fargo (1852)
    'C',      # Citigroup (1812)
    'GS',     # Goldman Sachs (1999)
    'MS',     # Morgan Stanley (1986)
    'AXP',    # American Express (1850)
    'USB',    # US Bancorp (1863)
    'PNC',    # PNC Financial (1845)
    'BK',     # Bank of New York (1784)
    
    # 医疗
    'JNJ',    # Johnson & Johnson (1886)
    'PFE',    # Pfizer (1942)
    'MRK',    # Merck (1891)
    'ABT',    # Abbott (1929)
    'BMY',    # Bristol-Myers (1887)
    'AMGN',   # Amgen (1983)
    'LLY',    # Eli Lilly (1876)
    'MDT',    # Medtronic (1977)
    
    # 消费
    'PG',     # Procter & Gamble (1837)
    'KO',     # Coca-Cola (1919)
    'PEP',    # PepsiCo (1919)
    'WMT',    # Walmart (1970)
    'MCD',    # McDonald's (1965)
    'HD',     # Home Depot (1981)
    'NKE',    # Nike (1980)
    'COST',   # Costco (1983)
    'TGT',    # Target (1967)
    'LOW',    # Lowe's (1961)
    
    # 工业
    'GE',     # General Electric (1892)
    'MMM',    # 3M (1902)
    'CAT',    # Caterpillar (1925)
    'BA',     # Boeing (1934)
    'HON',    # Honeywell (1906)
    'UPS',    # UPS (1999)
    'DE',     # John Deere (1837)
    
    # 能源
    'XOM',    # Exxon Mobil (1870)
    'CVX',    # Chevron (1879)
    'COP',    # ConocoPhillips (1875)
    
    # 电信/媒体
    'T',      # AT&T (1877)
    'VZ',     # Verizon (1983)
    'DIS',    # Disney (1923)
    'CMCSA',  # Comcast (1963)
]
"""

"""
EMIS vs VIX 完整对比（修复下载问题）
"""

import numpy as np
import pandas as pd
import yfinance as yf
import time
import os
import warnings
warnings.filterwarnings('ignore')

# ============================================
# 参数设置
# ============================================

PROJECT_DIR     = './_emis_code/p1-entanglement-entropy/'
CACHE_DIR       = os.path.join(PROJECT_DIR, 'cache')
DATA_FIGURE_DIR = os.path.join(PROJECT_DIR, 'data-figure')

# 缓存文件
STOCK_CACHE = os.path.join(CACHE_DIR,'stocks_50_since2005.csv')
SP500_CACHE = os.path.join(CACHE_DIR,'sp500.csv')
VIX_CACHE = os.path.join(CACHE_DIR,'vix.csv')
ENTROPY_CACHE = os.path.join(CACHE_DIR,'entropy_US_since2005.csv')    

START_DATE = '2005-01-01'
TRAIN_END = '2020-01-01'
WINDOW = 60
HORIZON = 30

# 2005年前上市的股票（精简稳定版42只）
TICKERS_2005 = [
    # 科技 (10)
    'AAPL', 'MSFT', 'INTC', 'IBM', 'ORCL',
    'CSCO', 'TXN', 'QCOM', 'AMAT', 'ADI',
    
    # 金融 (10)
    'JPM', 'BAC', 'WFC', 'C', 'GS',
    'MS', 'AXP', 'USB', 'PNC', 'BK',
    
    # 医疗 (8)
    'JNJ', 'PFE', 'MRK', 'ABT', 'BMY',
    'AMGN', 'LLY', 'MDT',
    
    # 消费 (10)
    'PG', 'KO', 'PEP', 'WMT', 'MCD',
    'HD', 'NKE', 'COST', 'TGT', 'LOW',
    
    # 工业 (7)
    'GE', 'MMM', 'CAT', 'BA', 'HON',
    'UPS', 'DE',
    
    # 能源 (3)
    'XOM', 'CVX', 'COP',
    
    # 电信/媒体 (4)
    'T', 'VZ', 'DIS', 'CMCSA',
]



# ============================================
# 时区修复
# ============================================

def fix_timezone(df):
    is_series = isinstance(df, pd.Series)
    if is_series:
        name = df.name
        df = df.to_frame()
    
    df = df.reset_index()
    date_col = df.columns[0]
    df[date_col] = pd.to_datetime(df[date_col].astype(str).str[:10])
    df = df.set_index(date_col)
    
    if is_series:
        return df.iloc[:, 0].rename(name)
    return df

# ============================================
# 单只股票下载（带重试）
# ============================================

def download_single(ticker, start, max_retries=3):
    """下载单只股票，带重试"""
    for attempt in range(max_retries):
        try:
            # 方法1：使用 Ticker 对象
            stock = yf.Ticker(ticker)
            df = stock.history(start=start)
            if len(df) > 100:
                return df['Close'].rename(ticker)
        except:
            pass
        
        try:
            # 方法2：使用 download
            df = yf.download(ticker, start=start, progress=False)
            if len(df) > 100:
                close = df['Close']
                if isinstance(close, pd.DataFrame):
                    close = close.iloc[:, 0]
                return close.rename(ticker)
        except:
            pass
        
        time.sleep(1)
    
    return None

# ============================================
# 数据加载
# ============================================

def load_stock_data():
    """加载股票数据"""
    
    # 检查缓存
    if os.path.exists(STOCK_CACHE):
        print(f"从本地加载: {STOCK_CACHE}")
        prices = pd.read_csv(STOCK_CACHE, index_col=0, parse_dates=True)
        prices = fix_timezone(prices)
        
        start = prices.index.min()
        if start.year <= 2006:
            print(f"  天数: {len(prices)}, 股票: {len(prices.columns)}")
            print(f"  范围: {start.date()} ~ {prices.index.max().date()}")
            return prices
        else:
            print(f"  ⚠️ 数据不完整，重新下载...")
    
    # 逐只下载
    print(f"下载股票数据 (从 {START_DATE})...")
    
    all_data = []
    success = []
    failed = []
    
    for i, ticker in enumerate(TICKERS_2005):
        print(f"  [{i+1}/{len(TICKERS_2005)}] {ticker}...", end=" ")
        
        series = download_single(ticker, START_DATE)
        
        if series is not None and len(series) > 1000:
            all_data.append(series)
            success.append(ticker)
            print(f"✓ ({len(series)} 天)")
        else:
            failed.append(ticker)
            print("✗")
        
        time.sleep(0.5)
    
    print(f"\n成功: {len(success)}, 失败: {len(failed)}")
    if failed:
        print(f"失败列表: {failed}")
    
    if len(all_data) < 20:
        print("❌ 股票数量不足")
        return None
    
    prices = pd.concat(all_data, axis=1)
    prices = fix_timezone(prices)
    prices.to_csv(STOCK_CACHE)
    print(f"已保存: {STOCK_CACHE}")
    
    return prices

def load_sp500():
    """加载 S&P 500"""
    if os.path.exists(SP500_CACHE):
        print(f"从本地加载: {SP500_CACHE}")
        sp500 = pd.read_csv(SP500_CACHE, index_col=0, parse_dates=True).iloc[:, 0]
        sp500 = fix_timezone(sp500)
    else:
        print("下载 S&P 500...")
        sp500 = download_single('^GSPC', START_DATE)
        if sp500 is not None:
            sp500.to_csv(SP500_CACHE)
    
    print(f"S&P 500: {len(sp500)} 天, {sp500.index.min().date()} ~ {sp500.index.max().date()}")
    return sp500

def load_vix():
    """加载 VIX"""
    if os.path.exists(VIX_CACHE):
        print(f"从本地加载: {VIX_CACHE}")
        vix = pd.read_csv(VIX_CACHE, index_col=0, parse_dates=True).iloc[:, 0]
        vix = fix_timezone(vix)
    else:
        print("下载 VIX...")
        vix = download_single('^VIX', START_DATE)
        if vix is not None:
            vix.to_csv(VIX_CACHE)
    
    print(f"VIX: {len(vix)} 天, {vix.index.min().date()} ~ {vix.index.max().date()}")
    return vix

# ============================================
# 计算函数
# ============================================

def compute_returns(prices):
    return np.log(prices / prices.shift(1)).dropna()

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
    
    return pd.Series(S_list, index=dates, name='S')

def test_indicator(indicator, sp500, threshold, horizon=30):
    results = []
    
    for t in range(len(indicator) - horizon):
        date = indicator.index[t]
        value = indicator.iloc[t]
        
        if value > threshold:
            if date in sp500.index:
                idx = sp500.index.get_loc(date)
                if idx + horizon < len(sp500):
                    ret = np.log(sp500.iloc[idx + horizon] / sp500.iloc[idx])
                    results.append({
                        'date': date,
                        'value': value,
                        'return': ret,
                        'win': ret > 0
                    })
    
    return pd.DataFrame(results) if results else None

# ============================================
# 主程序
# ============================================

def main():
    print("="*70)
    print("EMIS vs VIX 对比分析（完整历史版）")
    print("="*70)
    print(f"数据范围: {START_DATE} ~ 今天")
    print(f"训练集: {START_DATE} ~ {TRAIN_END}")
    print(f"测试集: {TRAIN_END} ~ 今天")
    print("="*70)
    
    # 1. 加载数据
    prices = load_stock_data()
    if prices is None:
        return None, None, None, None
    
    # 清理：只保留2006年前就有数据的股票
    prices = prices.dropna(axis=1, how='all')
    
    valid_cols = []
    for col in prices.columns:
        first = prices[col].first_valid_index()
        if first is not None and first.year <= 2006:
            valid_cols.append(col)
    
    prices = prices[valid_cols].ffill().dropna()
    
    print(f"\n有效股票: {len(prices.columns)} 只")
    print(f"数据范围: {prices.index.min().date()} ~ {prices.index.max().date()}")
    print(f"数据天数: {len(prices)}")
    
    sp500 = load_sp500()
    vix = load_vix()
    
    # 2. 计算或加载纠缠熵
    if os.path.exists(ENTROPY_CACHE):
        print(f"\n从本地加载: {ENTROPY_CACHE}")
        S = pd.read_csv(ENTROPY_CACHE, index_col=0, parse_dates=True).iloc[:, 0]
        S = fix_timezone(S)
        print(f"  天数: {len(S)}, 范围: {S.index.min().date()} ~ {S.index.max().date()}")
    else:
        print(f"\n计算纠缠熵 (使用 {len(prices.columns)} 只股票)...")
        returns = compute_returns(prices)
        S = compute_entanglement_entropy(returns, window=WINDOW)
        S.to_csv(ENTROPY_CACHE)
        print(f"  已保存: {ENTROPY_CACHE}")
    
    print(f"纠缠熵范围: [{S.min():.2f}, {S.max():.2f}]")
    
    # 3. 对齐
    common_idx = S.index.intersection(vix.index).intersection(sp500.index)
    S = S.loc[common_idx]
    vix = vix.loc[common_idx]
    sp500 = sp500.loc[common_idx]
    
    print(f"\n对齐后: {len(common_idx)} 天")
    print(f"  范围: {common_idx.min().date()} ~ {common_idx.max().date()}")
    
    # 4. 划分
    train_end_dt = pd.to_datetime(TRAIN_END)
    
    S_train = S[S.index < train_end_dt]
    S_test = S[S.index >= train_end_dt]
    vix_train = vix[vix.index < train_end_dt]
    vix_test = vix[vix.index >= train_end_dt]
    sp500_test = sp500[sp500.index >= train_end_dt]
    
    print(f"\n训练集: {len(S_train)} 天 ({S_train.index.min().date()} ~ {S_train.index.max().date()})")
    print(f"测试集: {len(S_test)} 天 ({S_test.index.min().date()} ~ {S_test.index.max().date()})")
    
    # 5. 阈值
    S_threshold = S_train.quantile(0.90)
    vix_threshold = vix_train.quantile(0.90)
    
    print(f"\n训练集阈值 (90%分位):")
    print(f"  EMIS: {S_threshold:.2f}")
    print(f"  VIX: {vix_threshold:.2f}")
    
    # 6. 测试
    print("\n" + "="*70)
    print("测试集效果对比")
    print("="*70)
    
    emis_results = test_indicator(S_test, sp500_test, S_threshold, HORIZON)
    vix_results = test_indicator(vix_test, sp500_test, vix_threshold, HORIZON)
    
    print(f"\n{'指标':<15} {'触发次数':<10} {'胜率':<10} {'平均收益':<12}")
    print("-"*50)
    
    if emis_results is not None:
        print(f"{'EMIS':<15} {len(emis_results):<10} {emis_results['win'].mean():<10.1%} {emis_results['return'].mean():<12.1%}")
    
    if vix_results is not None:
        print(f"{'VIX':<15} {len(vix_results):<10} {vix_results['win'].mean():<10.1%} {vix_results['return'].mean():<12.1%}")
    
    # 7. 相关性
    corr = S.corr(vix)
    print(f"\n相关系数: r = {corr:.3f}")
    
    # 8. 不同阈值
    print("\n" + "="*70)
    print("不同阈值对比")
    print("="*70)
    print(f"\n{'阈值':<10} {'EMIS胜率':<12} {'EMIS收益':<12} {'VIX胜率':<12} {'VIX收益':<12}")
    print("-"*60)
    
    for pct in [80, 85, 90, 95]:
        s_th = S_train.quantile(pct/100)
        v_th = vix_train.quantile(pct/100)
        
        s_res = test_indicator(S_test, sp500_test, s_th, HORIZON)
        v_res = test_indicator(vix_test, sp500_test, v_th, HORIZON)
        
        s_wr = s_res['win'].mean() if s_res is not None else 0
        s_ret = s_res['return'].mean() if s_res is not None else 0
        v_wr = v_res['win'].mean() if v_res is not None else 0
        v_ret = v_res['return'].mean() if v_res is not None else 0
        
        print(f"{pct}%       {s_wr:<12.1%} {s_ret:<12.1%} {v_wr:<12.1%} {v_ret:<12.1%}")
    
    # 9. 总结
    print("\n" + "="*70)
    print("总结")
    print("="*70)
    
    if emis_results is not None and vix_results is not None:
        emis_wr = emis_results['win'].mean()
        vix_wr = vix_results['win'].mean()
        
        print(f"\nEMIS: {len(emis_results)} 次, 胜率 {emis_wr:.1%}")
        print(f"VIX:  {len(vix_results)} 次, 胜率 {vix_wr:.1%}")
        print(f"胜率差: {(emis_wr - vix_wr)*100:+.1f}%")
        
        if emis_wr > vix_wr + 0.05:
            print("\n✅ EMIS 显著优于 VIX")
        elif emis_wr > vix_wr:
            print("\n🔶 EMIS 略优于 VIX")
        else:
            print("\n⚠️ VIX 优于或持平 EMIS")
    
    return S, vix, emis_results, vix_results

if __name__ == "__main__":
    S, vix, emis_results, vix_results = main()