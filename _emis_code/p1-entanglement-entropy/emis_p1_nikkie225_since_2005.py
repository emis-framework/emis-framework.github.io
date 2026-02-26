"""
重新下载日本数据（剔除数据不完整的股票）
"""

import numpy as np
import pandas as pd
import yfinance as yf
import time
import os
import warnings
warnings.filterwarnings('ignore')

# ============================================
# 参数
# ============================================

PROJECT_DIR     = './_emis_code/p1-entanglement-entropy/'
CACHE_DIR       = os.path.join(PROJECT_DIR, 'cache')
DATA_FIGURE_DIR = os.path.join(PROJECT_DIR, 'data-figure')

# 缓存文件
STOCK_CACHE = os.path.join(CACHE_DIR,'stocks_Japan_since2005_v2.csv')
INDEX_CACHE = os.path.join(CACHE_DIR,'index_Japan_since2005.csv')
ENTROPY_CACHE = os.path.join(CACHE_DIR,'entropy_Japan_since2005_v2.csv')  

START_DATE = '2005-01-01'
TRAIN_END = '2020-01-01'
WINDOW = 60
HORIZON = 30

# 剔除 8306.T 和其他数据不完整的股票 39只
JAPAN_TICKERS = [
    # 汽车
    '7203.T',   # Toyota
    '7267.T',   # Honda
    '7201.T',   # Nissan
    '7261.T',   # Mazda
    '7269.T',   # Suzuki
    
    # 电子/科技
    '6758.T',   # Sony
    '6861.T',   # Keyence
    '6902.T',   # Denso
    '6501.T',   # Hitachi
    '6752.T',   # Panasonic
    '6702.T',   # Fujitsu
    '6503.T',   # Mitsubishi Electric
    '6762.T',   # TDK
    '6971.T',   # Kyocera
    
    # 金融（剔除 8306.T）
    '8316.T',   # Sumitomo Mitsui
    '8411.T',   # Mizuho
    '8766.T',   # Tokio Marine
    '8801.T',   # Mitsui Fudosan
    
    # 通信（剔除 9434.T）
    '9432.T',   # NTT
    '9433.T',   # KDDI
    
    # 消费/零售
    '9983.T',   # Fast Retailing
    '2914.T',   # Japan Tobacco
    '4452.T',   # Kao
    '4911.T',   # Shiseido
    '7751.T',   # Canon
    
    # 制药
    '4502.T',   # Takeda
    '4503.T',   # Astellas
    '4519.T',   # Chugai
    '4568.T',   # Daiichi Sankyo
    
    # 工业
    '6301.T',   # Komatsu
    '6326.T',   # Kubota
    '7011.T',   # Mitsubishi Heavy
    '7012.T',   # Kawasaki Heavy
    
    # 材料
    '4063.T',   # Shin-Etsu Chemical
    '5401.T',   # Nippon Steel
    '3407.T',   # Asahi Kasei
    
    # 其他
    '9020.T',   # JR East
    '9022.T',   # JR Central
    '9984.T',   # Softbank Group
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
# 下载函数
# ============================================

def download_single(ticker, start, max_retries=3):
    for attempt in range(max_retries):
        try:
            stock = yf.Ticker(ticker)
            df = stock.history(start=start)
            if len(df) > 100:
                return df['Close'].rename(ticker)
        except:
            pass
        
        try:
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
    
    for i, ticker in enumerate(JAPAN_TICKERS):
        print(f"  [{i+1}/{len(JAPAN_TICKERS)}] {ticker}...", end=" ")
        
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

def test_indicator(indicator, index, threshold, horizon=30):
    results = []
    for t in range(len(indicator) - horizon):
        date = indicator.index[t]
        if indicator.iloc[t] > threshold and date in index.index:
            idx = index.index.get_loc(date)
            if idx + horizon < len(index):
                ret = np.log(index.iloc[idx + horizon] / index.iloc[idx])
                results.append({'return': ret, 'win': ret > 0})
    return pd.DataFrame(results) if results else None

# ============================================
# 主程序
# ============================================

def main():
    print("="*70)
    print("日本市场数据 v2（剔除数据不完整的股票）")
    print("="*70)
    
    # # 下载股票
    # print(f"\n下载日本股票 ({len(JAPAN_TICKERS)} 只)...")
    
    # all_data = []
    # success = []
    
    # for i, ticker in enumerate(JAPAN_TICKERS):
    #     print(f"  [{i+1}/{len(JAPAN_TICKERS)}] {ticker}...", end=" ")
        
    #     series = download_single(ticker, START_DATE)
        
    #     if series is not None:
    #         # 检查是否从2005年初开始
    #         first = series.first_valid_index()
    #         if first is not None and first.year == 2005 and first.month <= 2:
    #             all_data.append(series)
    #             success.append(ticker)
    #             print(f"✓ ({len(series)} 天, 从 {first.date()})")
    #         else:
    #             print(f"✗ (从 {first.date()} 开始，太晚)")
    #     else:
    #         print("✗ (下载失败)")
        
    #     time.sleep(0.5)
    
    # print(f"\n成功: {len(success)} 只")
    
    # if len(all_data) < 15:
    #     print("❌ 股票数量不足")
    #     return
    
    # prices = pd.concat(all_data, axis=1)
    # prices = fix_timezone(prices)
    # prices = prices.ffill().dropna()
    
    # prices.to_csv(STOCK_CACHE)
    # print(f"已保存: {STOCK_CACHE}")

    # 1. 加载数据
    prices = load_stock_data()
    if prices is None:
        return None, None, None, None
    
    print(f"\n有效数据: {len(prices.columns)} 只股票, {len(prices)} 天")
    print(f"范围: {prices.index.min().date()} ~ {prices.index.max().date()}")
    
    # 加载指数
    if os.path.exists(INDEX_CACHE):
        print(f"\n从本地加载: {INDEX_CACHE}")
        index = pd.read_csv(INDEX_CACHE, index_col=0, parse_dates=True).iloc[:, 0]
        index = fix_timezone(index)
    else:
        print("\n下载 Nikkei 225...")
        index = download_single('^N225', START_DATE)
        index = fix_timezone(index.to_frame()).iloc[:, 0]
        index.to_csv(INDEX_CACHE)
    
    print(f"Nikkei 225: {len(index)} 天, {index.index.min().date()} ~ {index.index.max().date()}")
    
    # 计算纠缠熵
    print(f"\n计算纠缠熵 ({len(prices.columns)} 只股票)...")
    returns = compute_returns(prices)
    S = compute_entanglement_entropy(returns, window=WINDOW)
    S.to_csv(ENTROPY_CACHE)
    print(f"已保存: {ENTROPY_CACHE}")
    
    print(f"纠缠熵: {len(S)} 天, [{S.min():.2f}, {S.max():.2f}]")
    print(f"范围: {S.index.min().date()} ~ {S.index.max().date()}")
    
    # 对齐
    common = S.index.intersection(index.index)
    S = S.loc[common]
    index = index.loc[common]
    
    print(f"\n对齐后: {len(common)} 天")
    print(f"范围: {common.min().date()} ~ {common.max().date()}")
    
    # 划分
    train_end = pd.to_datetime(TRAIN_END)
    S_train = S[S.index < train_end]
    S_test = S[S.index >= train_end]
    index_test = index[index.index >= train_end]
    
    print(f"\n训练集: {len(S_train)} 天 ({S_train.index.min().date()} ~ {S_train.index.max().date()})")
    print(f"测试集: {len(S_test)} 天 ({S_test.index.min().date()} ~ {S_test.index.max().date()})")
    
    # 测试
    threshold = S_train.quantile(0.90)
    print(f"\n阈值 (90%): {threshold:.4f}")
    
    results = test_indicator(S_test, index_test, threshold, HORIZON)
    
    # ★★★ 修复：检查 results 是否为 None 或空 ★★★
    if results is not None and len(results) > 0:
        n_trades = len(results)
        wr = results['win'].mean()
        ret = results['return'].mean()
        
        print(f"\n测试集结果:")
        print(f"  交易次数: {n_trades}")
        print(f"  胜率: {wr:.1%}")
        print(f"  平均收益: {ret:.1%}")
        
        if wr > 0.6:
            print("\n✅ 日本市场验证成功！")
    else:
        n_trades = 0
        wr = 0
        ret = 0
        print("\n❌ 无交易信号")
    
    # 三个市场对比
    print("\n" + "="*70)
    print("三个市场汇总")
    print("="*70)
    
    train_start = S_train.index.min().strftime('%Y-%m')
    
    print(f"\n{'市场':<18} {'训练集起始':<15} {'测试交易':<10} {'胜率':<10} {'收益':<10}")
    print("-"*65)
    print(f"{'美国 S&P 500':<18} {'2005-04':<15} {'208':<10} {'90.4%':<10} {'6.1%':<10}")
    print(f"{'日本 Nikkei':<18} {train_start:<15} {n_trades:<10} {wr*100:.1f}%{'':5} {ret*100:.1f}%")
    print(f"{'德国 DAX':<18} {'2005-04':<15} {'102':<10} {'95.1%':<10} {'8.4%':<10}")
    
    print(f"\n已保存文件:")
    print(f"  {STOCK_CACHE}")
    print(f"  {ENTROPY_CACHE}")

if __name__ == "__main__":
    main()