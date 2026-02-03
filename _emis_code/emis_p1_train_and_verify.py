"""
EMIS P1 修正版：正确的变量顺序
"""

import numpy as np
import pandas as pd
import yfinance as yf
import time
import os
import warnings
warnings.filterwarnings('ignore')

# ============================================
# 参数设置（放在最前面！）
# ============================================

START_DATE = '2005-01-01'    # 数据起始
TRAIN_END = '2020-01-01'     # 训练集截止
WINDOW = 60                   # 滚动窗口
HORIZON = 30                  # 预测天数

# ============================================
# 股票列表
# ============================================

TICKERS = [
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

# ============================================
# 数据加载函数
# ============================================

def load_or_download_stocks(tickers, start_date, cache_file='stocks_50.csv'):
    """加载或下载股票数据"""
    if os.path.exists(cache_file):
        print(f"从本地加载: {cache_file}")
        prices = pd.read_csv(cache_file, index_col=0, parse_dates=True)
        print(f"加载成功: {len(prices.columns)} 只股票, {len(prices)} 天")
        return prices
    
    print(f"下载 {len(tickers)} 只股票...")
    
    # 分批下载
    all_data = []
    batch_size = 10
    
    for i in range(0, len(tickers), batch_size):
        batch = tickers[i:i+batch_size]
        print(f"  下载 {i+1}-{min(i+batch_size, len(tickers))}...")
        
        try:
            data = yf.download(batch, start=start_date, progress=False)
            if not data.empty:
                all_data.append(data['Close'])
            time.sleep(1)
        except Exception as e:
            print(f"  错误: {e}")
            time.sleep(5)
    
    if all_data:
        prices = pd.concat(all_data, axis=1)
        prices.to_csv(cache_file)
        print(f"已保存: {cache_file}")
        return prices
    
    return None

def load_or_download_sp500(start_date, cache_file='sp500.csv'):
    """加载或下载 S&P 500"""
    if os.path.exists(cache_file):
        print(f"从本地加载: {cache_file}")
        sp500 = pd.read_csv(cache_file, index_col=0, parse_dates=True).iloc[:, 0]
        return sp500
    
    print("下载 S&P 500...")
    time.sleep(2)
    
    try:
        data = yf.download('^GSPC', start=start_date, progress=False)
        if data.empty:
            return None
        sp500 = data['Close']
        if isinstance(sp500, pd.DataFrame):
            sp500 = sp500.iloc[:, 0]
        sp500.to_csv(cache_file)
        print(f"已保存: {cache_file}")
        return sp500
    except Exception as e:
        print(f"错误: {e}")
        return None

# ============================================
# 计算函数
# ============================================

def compute_returns(prices):
    """计算对数收益率"""
    return np.log(prices / prices.shift(1)).dropna()

def compute_entanglement_entropy(returns, window=60):
    """计算纠缠熵"""
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
    
    return pd.Series(S_list, index=dates)

def test_strategy(S, sp500, S_threshold, horizon=30):
    """测试策略"""
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
    
    return pd.DataFrame(results) if results else None

# ============================================
# 主程序
# ============================================

def main():
    print("="*60)
    print("EMIS P1: 纠缠熵危机指标")
    print("="*60)
    print(f"数据范围: {START_DATE} - 今天")
    print(f"训练集截止: {TRAIN_END}")
    print("="*60)
    
    # 1. 加载数据
    prices = load_or_download_stocks(TICKERS, START_DATE)
    if prices is None or prices.empty:
        print("❌ 无法获取股票数据，请等待后重试")
        return
    
    sp500 = load_or_download_sp500(START_DATE)
    if sp500 is None or sp500.empty:
        print("❌ 无法获取 S&P 500，请等待后重试")
        return
    
    # 2. 清理数据
    prices = prices.dropna(axis=1, how='all').ffill().dropna()
    print(f"\n有效数据: {len(prices.columns)} 只股票, {len(prices)} 天")
    print(f"时间范围: {prices.index.min().date()} - {prices.index.max().date()}")
    
    # 3. 计算纠缠熵
    print("\n计算纠缠熵...")
    returns = compute_returns(prices)
    S = compute_entanglement_entropy(returns, window=WINDOW)
    print(f"纠缠熵范围: [{S.min():.2f}, {S.max():.2f}]")
    print(f"均值: {S.mean():.2f}, 标准差: {S.std():.2f}")
    
    # 4. 样本划分
    S_train = S[S.index < TRAIN_END]
    S_test = S[S.index >= TRAIN_END]
    sp500_train = sp500[sp500.index < TRAIN_END]
    sp500_test = sp500[sp500.index >= TRAIN_END]
    
    print(f"\n训练集: {S_train.index.min().date()} - {S_train.index.max().date()} ({len(S_train)} 天)")
    print(f"测试集: {S_test.index.min().date()} - {S_test.index.max().date()} ({len(S_test)} 天)")
    
    # 5. 计算阈值（只用训练集！）
    S_threshold = S_train.quantile(0.90)
    print(f"\n训练集 90% 分位阈值: {S_threshold:.4f}")
    
    # 6. 训练集效果
    print("\n" + "="*60)
    print("训练集效果 (样本内)")
    print("="*60)
    train_results = test_strategy(S_train, sp500_train, S_threshold, HORIZON)
    if train_results is not None and len(train_results) > 0:
        print(f"触发次数: {len(train_results)}")
        print(f"胜率: {train_results['win'].mean():.1%}")
        print(f"平均{HORIZON}日收益: {train_results['return'].mean():.1%}")
    else:
        print("无触发信号")
    
    # 7. 测试集效果（真正的验证！）
    print("\n" + "="*60)
    print("测试集效果 (样本外) ← 真正的验证！")
    print("="*60)
    test_results = test_strategy(S_test, sp500_test, S_threshold, HORIZON)
    if test_results is not None and len(test_results) > 0:
        win_rate = test_results['win'].mean()
        avg_return = test_results['return'].mean()
        
        print(f"触发次数: {len(test_results)}")
        print(f"胜率: {win_rate:.1%}")
        print(f"平均{HORIZON}日收益: {avg_return:.1%}")
        
        print("\n" + "="*60)
        if win_rate > 0.6:
            print("✅ 样本外验证成功！EMIS 策略有效")
        elif win_rate > 0.5:
            print("🔶 样本外效果一般")
        else:
            print("❌ 样本外验证失败")
        print("="*60)
    else:
        print("无触发信号")
    
    # 8. 分段分析
    print("\n" + "="*60)
    print("分段分析")
    print("="*60)
    
    future_ret = np.log(sp500.shift(-HORIZON) / sp500)
    common_idx = S.index.intersection(future_ret.dropna().index)
    
    for label, low_q, high_q in [('最低20%', 0, 0.2), 
                                   ('中间60%', 0.2, 0.8), 
                                   ('最高20%', 0.8, 1.0)]:
        low_val = S.quantile(low_q)
        high_val = S.quantile(high_q)
        mask = (S >= low_val) & (S < high_val)
        
        valid_idx = common_idx[mask.reindex(common_idx).fillna(False)]
        if len(valid_idx) > 0:
            avg = future_ret.loc[valid_idx].mean()
            wr = (future_ret.loc[valid_idx] > 0).mean()
            print(f"{label}: 平均收益 = {avg:.1%}, 胜率 = {wr:.1%}")
    
    return S, S_threshold, test_results

# ============================================
# 运行
# ============================================

if __name__ == "__main__":
    main()