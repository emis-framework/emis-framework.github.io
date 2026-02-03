"""
EMIS vs VIX 完整对比（一体化版本）
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

START_DATE = '2005-01-01'
TRAIN_END = '2020-01-01'
WINDOW = 60
HORIZON = 30

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
# 数据加载
# ============================================

def load_stock_data():
    """加载股票数据"""
    cache_file = 'stocks_50.csv'
    
    if os.path.exists(cache_file):
        print(f"从本地加载: {cache_file}")
        prices = pd.read_csv(cache_file, index_col=0, parse_dates=True)
    else:
        print("下载股票数据...")
        prices = yf.download(TICKERS, start=START_DATE, progress=False)['Close']
        prices.to_csv(cache_file)
    
    prices = prices.dropna(axis=1, how='all').ffill().dropna()
    print(f"股票数据: {len(prices.columns)} 只, {len(prices)} 天")
    return prices

def load_sp500():
    """加载 S&P 500"""
    cache_file = 'sp500.csv'
    
    if os.path.exists(cache_file):
        print(f"从本地加载: {cache_file}")
        sp500 = pd.read_csv(cache_file, index_col=0, parse_dates=True).iloc[:, 0]
    else:
        print("下载 S&P 500...")
        data = yf.download('^GSPC', start=START_DATE, progress=False)['Close']
        if isinstance(data, pd.DataFrame):
            data = data.iloc[:, 0]
        data.to_csv(cache_file)
        sp500 = data
    
    print(f"S&P 500: {len(sp500)} 天")
    return sp500

def load_vix():
    """加载 VIX"""
    cache_file = 'vix.csv'
    
    if os.path.exists(cache_file):
        print(f"从本地加载: {cache_file}")
        vix = pd.read_csv(cache_file, index_col=0, parse_dates=True).iloc[:, 0]
    else:
        print("下载 VIX...")
        time.sleep(2)
        data = yf.download('^VIX', start=START_DATE, progress=False)['Close']
        if isinstance(data, pd.DataFrame):
            data = data.iloc[:, 0]
        data.to_csv(cache_file)
        vix = data
    
    print(f"VIX: {len(vix)} 天")
    return vix

# ============================================
# 计算函数
# ============================================

def compute_returns(prices):
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
    
    return pd.Series(S_list, index=dates, name='S')

def test_indicator(indicator, sp500, threshold, horizon=30):
    """测试指标效果"""
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
    print("="*60)
    print("EMIS vs VIX 对比分析")
    print("="*60)
    
    # 1. 加载数据
    prices = load_stock_data()
    sp500 = load_sp500()
    vix = load_vix()
    
    # 2. 计算纠缠熵
    print("\n计算纠缠熵...")
    returns = compute_returns(prices)
    S = compute_entanglement_entropy(returns, window=WINDOW)
    
    # 保存纠缠熵
    S.to_csv('entanglement_entropy.csv')
    print(f"纠缠熵已保存，范围: [{S.min():.2f}, {S.max():.2f}]")
    
    # 3. 对齐时间
    common_idx = S.index.intersection(vix.index).intersection(sp500.index)
    S = S.loc[common_idx]
    vix = vix.loc[common_idx]
    sp500 = sp500.loc[common_idx]
    
    print(f"\n对齐后数据: {len(common_idx)} 天")
    print(f"时间范围: {common_idx.min().date()} - {common_idx.max().date()}")
    
    # 4. 样本划分
    train_mask = S.index < TRAIN_END
    test_mask = S.index >= TRAIN_END
    
    S_train, S_test = S[train_mask], S[test_mask]
    vix_train, vix_test = vix[train_mask], vix[test_mask]
    sp500_train, sp500_test = sp500[train_mask], sp500[test_mask]
    
    print(f"\n训练集: {len(S_train)} 天")
    print(f"测试集: {len(S_test)} 天")
    
    # 5. 计算阈值（只用训练集）
    S_threshold = S_train.quantile(0.90)
    vix_threshold = vix_train.quantile(0.90)
    
    print(f"\n训练集阈值 (90%分位):")
    print(f"  EMIS S: {S_threshold:.2f}")
    print(f"  VIX: {vix_threshold:.2f}")
    
    # 6. 测试集对比
    print("\n" + "="*60)
    print("测试集效果对比 (2020-今天)")
    print("="*60)
    
    emis_results = test_indicator(S_test, sp500_test, S_threshold, HORIZON)
    vix_results = test_indicator(vix_test, sp500_test, vix_threshold, HORIZON)
    
    print(f"\n{'指标':<15} {'触发次数':<10} {'胜率':<10} {'平均收益':<12}")
    print("-"*50)
    
    if emis_results is not None and len(emis_results) > 0:
        print(f"{'EMIS 纠缠熵':<15} {len(emis_results):<10} {emis_results['win'].mean():<10.1%} {emis_results['return'].mean():<12.1%}")
    
    if vix_results is not None and len(vix_results) > 0:
        print(f"{'VIX':<15} {len(vix_results):<10} {vix_results['win'].mean():<10.1%} {vix_results['return'].mean():<12.1%}")
    
    # 7. 相关性分析
    print("\n" + "="*60)
    print("EMIS 与 VIX 的关系")
    print("="*60)
    
    corr = S.corr(vix)
    print(f"\n相关系数: r = {corr:.3f}")
    
    if corr > 0.7:
        print("⚠️ 高度相关：EMIS 可能与 VIX 重复")
    elif corr > 0.4:
        print("🔶 中度相关：有重叠信息")
    else:
        print("✅ 低相关：EMIS 提供独特信息")
    
    # 8. 不同阈值对比
    print("\n" + "="*60)
    print("不同阈值对比")
    print("="*60)
    
    print(f"\n{'阈值':<12} {'EMIS胜率':<12} {'EMIS收益':<12} {'VIX胜率':<12} {'VIX收益':<12}")
    print("-"*60)
    
    for pct in [80, 85, 90, 95]:
        s_th = S_train.quantile(pct/100)
        v_th = vix_train.quantile(pct/100)
        
        s_res = test_indicator(S_test, sp500_test, s_th, HORIZON)
        v_res = test_indicator(vix_test, sp500_test, v_th, HORIZON)
        
        s_wr = s_res['win'].mean() if s_res is not None and len(s_res) > 0 else 0
        s_ret = s_res['return'].mean() if s_res is not None and len(s_res) > 0 else 0
        v_wr = v_res['win'].mean() if v_res is not None and len(v_res) > 0 else 0
        v_ret = v_res['return'].mean() if v_res is not None and len(v_res) > 0 else 0
        
        print(f"{pct}%分位      {s_wr:<12.1%} {s_ret:<12.1%} {v_wr:<12.1%} {v_ret:<12.1%}")
    
    # 9. 组合策略
    print("\n" + "="*60)
    print("组合策略: EMIS + VIX 双重确认")
    print("="*60)
    
    combo_results = []
    for t in range(len(S_test) - HORIZON):
        date = S_test.index[t]
        s_val = S_test.iloc[t]
        
        if date in vix_test.index:
            v_val = vix_test.loc[date]
            
            if s_val > S_threshold and v_val > vix_threshold:
                if date in sp500_test.index:
                    idx = sp500_test.index.get_loc(date)
                    if idx + HORIZON < len(sp500_test):
                        ret = np.log(sp500_test.iloc[idx + HORIZON] / sp500_test.iloc[idx])
                        combo_results.append({'return': ret, 'win': ret > 0})
    
    if len(combo_results) > 0:
        df_combo = pd.DataFrame(combo_results)
        print(f"\n触发次数: {len(df_combo)}")
        print(f"胜率: {df_combo['win'].mean():.1%}")
        print(f"平均收益: {df_combo['return'].mean():.1%}")
    else:
        print("\n无双重确认信号")
    
    # 10. 总结
    print("\n" + "="*60)
    print("总结")
    print("="*60)
    
    if emis_results is not None and vix_results is not None:
        emis_wr = emis_results['win'].mean()
        vix_wr = vix_results['win'].mean()
        
        if emis_wr > vix_wr + 0.05:
            print("\n✅ EMIS 显著优于 VIX")
        elif emis_wr > vix_wr:
            print("\n🔶 EMIS 略优于 VIX")
        elif abs(emis_wr - vix_wr) < 0.03:
            print("\n🔶 EMIS 与 VIX 效果相当")
        else:
            print("\n⚠️ VIX 优于 EMIS")
        
        if corr < 0.5:
            print("✅ 但 EMIS 提供了不同的信息，可以与 VIX 组合使用")
    
    # 保存结果
    if emis_results is not None:
        emis_results.to_csv('emis_results.csv', index=False)
        print("\n结果已保存到 emis_results.csv")
    
    return S, vix, emis_results, vix_results

# ============================================
# 运行
# ============================================

if __name__ == "__main__":
    S, vix, emis_results, vix_results = main()