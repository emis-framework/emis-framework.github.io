"""
EMIS P1 修正版：S 作为市场状态指标
"""

import numpy as np
import pandas as pd
import yfinance as yf
import matplotlib.pyplot as plt
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

def get_stock_data(tickers, start='2000-01-01', end=None):
    if end is None:
        end = datetime.today().strftime('%Y-%m-%d')
    print(f"下载 {len(tickers)} 只股票数据...")
    data = yf.download(tickers, start=start, end=end, progress=False)
    prices = data['Close']
    prices = prices.dropna(axis=1, how='all')
    prices = prices.ffill()
    prices = prices.dropna()
    print(f"获取 {len(prices.columns)} 只股票, {len(prices)} 天数据")
    return prices

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

def main():
    tickers = [
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
    
    print("="*60)
    print("EMIS P1 修正版：纠缠熵作为市场状态指标")
    print("="*60)
    
    # 获取数据
    prices = get_stock_data(tickers, start='2005-01-01')
    returns = compute_returns(prices)
    
    # 计算纠缠熵
    print("\n计算纠缠熵...")
    S = compute_entanglement_entropy(returns, window=60)
    
    # 获取市场指数
    print("下载 S&P 500...")
    sp500_data = yf.download('^GSPC', start='2005-01-01', progress=False)
    sp500 = sp500_data['Close']
    if isinstance(sp500, pd.DataFrame):
        sp500 = sp500.iloc[:, 0]
    
    # ============================================
    # 测试 1：S 高 = 买入信号（抄底）
    # ============================================
    print("\n" + "="*60)
    print("测试 1：高 S 作为买入信号")
    print("="*60)
    
    S_high_threshold = S.quantile(0.90)  # 90%分位数
    print(f"高S阈值（90%分位）: {S_high_threshold:.2f}")
    
    buy_results = []
    for t in range(len(S) - 30):
        date = S.index[t]
        S_value = S.iloc[t]
        
        if S_value > S_high_threshold:
            if date in sp500.index:
                idx = sp500.index.get_loc(date)
                if idx + 30 < len(sp500):
                    future_ret = np.log(sp500.iloc[idx+30] / sp500.iloc[idx])
                    buy_results.append({
                        'date': date,
                        'S': S_value,
                        'return_30d': future_ret
                    })
    
    if len(buy_results) > 0:
        df_buy = pd.DataFrame(buy_results)
        avg_return = df_buy['return_30d'].mean()
        win_rate = (df_buy['return_30d'] > 0).mean()
        print(f"触发次数: {len(df_buy)}")
        print(f"平均30日收益率: {avg_return:.1%}")
        print(f"胜率（正收益）: {win_rate:.1%}")
        
        if avg_return > 0.02 and win_rate > 0.6:
            print("✅ 高S是有效的买入信号！")
        else:
            print("🔶 效果一般")
    
    # ============================================
    # 测试 2：S 突然上升 = 危机开始
    # ============================================
    print("\n" + "="*60)
    print("测试 2：S 变化率作为预警信号")
    print("="*60)
    
    # 计算 S 的5日变化
    dS = S.diff(5)
    dS_threshold = dS.quantile(0.95)  # 95%分位的变化
    print(f"dS阈值（95%分位）: {dS_threshold:.3f}")
    
    crisis_signals = []
    for t in range(5, len(S) - 30):
        date = S.index[t]
        dS_value = dS.iloc[t]
        
        if dS_value > dS_threshold:
            if date in sp500.index:
                idx = sp500.index.get_loc(date)
                if idx + 30 < len(sp500):
                    future_ret = np.log(sp500.iloc[idx+30] / sp500.iloc[idx])
                    crisis_signals.append({
                        'date': date,
                        'dS': dS_value,
                        'return_30d': future_ret
                    })
    
    if len(crisis_signals) > 0:
        df_crisis = pd.DataFrame(crisis_signals)
        avg_return = df_crisis['return_30d'].mean()
        crash_rate = (df_crisis['return_30d'] < -0.05).mean()
        print(f"触发次数: {len(df_crisis)}")
        print(f"平均30日收益: {avg_return:.1%}")
        print(f"崩盘率（跌>5%）: {crash_rate:.1%}")
        
        if crash_rate > 0.4:
            print("✅ dS突增是有效的危机预警！")
        else:
            print("🔶 效果一般")
    
    # ============================================
    # 测试 3：S 从低突破到高
    # ============================================
    print("\n" + "="*60)
    print("测试 3：S 突破信号")
    print("="*60)
    
    S_low = S.quantile(0.5)   # 中位数以下算"低"
    S_high = S.quantile(0.75) # 75%分位以上算"高"
    print(f"低S阈值: {S_low:.2f}, 高S阈值: {S_high:.2f}")
    
    breakout_signals = []
    for t in range(20, len(S) - 30):
        # 过去20天最高S低于中位数
        past_max = S.iloc[t-20:t].max()
        current = S.iloc[t]
        
        if past_max < S_low and current > S_high:
            date = S.index[t]
            if date in sp500.index:
                idx = sp500.index.get_loc(date)
                if idx + 30 < len(sp500):
                    future_ret = np.log(sp500.iloc[idx+30] / sp500.iloc[idx])
                    breakout_signals.append({
                        'date': date,
                        'S': current,
                        'return_30d': future_ret
                    })
    
    if len(breakout_signals) > 0:
        df_break = pd.DataFrame(breakout_signals)
        avg_return = df_break['return_30d'].mean()
        crash_rate = (df_break['return_30d'] < -0.05).mean()
        print(f"触发次数: {len(df_break)}")
        print(f"平均30日收益: {avg_return:.1%}")
        print(f"崩盘率（跌>5%）: {crash_rate:.1%}")
        print("\n信号详情:")
        print(df_break.to_string())
    else:
        print("没有检测到突破信号")
    
    # ============================================
    # 测试 4：相关性分析
    # ============================================
    print("\n" + "="*60)
    print("测试 4：相关性分析")
    print("="*60)
    
    # 对齐数据
    common_idx = S.index.intersection(sp500.index)
    S_aligned = S.loc[common_idx]
    
    # 未来收益
    future_5d = np.log(sp500.shift(-5) / sp500).loc[common_idx]
    future_10d = np.log(sp500.shift(-10) / sp500).loc[common_idx]
    future_30d = np.log(sp500.shift(-30) / sp500).loc[common_idx]
    
    # 删除 NaN
    valid = ~(S_aligned.isna() | future_30d.isna())
    
    print("S 与未来收益的相关性:")
    print(f"  5日后收益:  r = {S_aligned[valid].corr(future_5d[valid]):.3f}")
    print(f"  10日后收益: r = {S_aligned[valid].corr(future_10d[valid]):.3f}")
    print(f"  30日后收益: r = {S_aligned[valid].corr(future_30d[valid]):.3f}")
    
    # dS 与未来收益
    dS_aligned = dS.loc[common_idx]
    valid2 = ~(dS_aligned.isna() | future_30d.isna())
    print(f"\ndS(5日变化) 与未来收益的相关性:")
    print(f"  5日后收益:  r = {dS_aligned[valid2].corr(future_5d[valid2]):.3f}")
    print(f"  10日后收益: r = {dS_aligned[valid2].corr(future_10d[valid2]):.3f}")
    print(f"  30日后收益: r = {dS_aligned[valid2].corr(future_30d[valid2]):.3f}")
    
    # ============================================
    # 可视化
    # ============================================
    print("\n生成图表...")
    
    fig, axes = plt.subplots(4, 1, figsize=(14, 12), sharex=True)
    
    # 图1：市场指数
    axes[0].plot(sp500.index, sp500.values, 'b-', linewidth=0.8)
    axes[0].set_ylabel('S&P 500')
    axes[0].set_title('Market Index')
    axes[0].grid(True, alpha=0.3)
    
    # 图2：纠缠熵
    axes[1].plot(S.index, S.values, 'purple', linewidth=0.8)
    axes[1].axhline(y=S.quantile(0.9), color='red', linestyle='--', 
                    label=f'90% = {S.quantile(0.9):.2f}')
    axes[1].axhline(y=S.quantile(0.5), color='orange', linestyle='--',
                    label=f'50% = {S.quantile(0.5):.2f}')
    axes[1].set_ylabel('S(t)')
    axes[1].set_title('Entanglement Entropy')
    axes[1].legend(loc='upper right')
    axes[1].grid(True, alpha=0.3)
    
    # 图3：S的变化率
    axes[2].plot(dS.index, dS.values, 'green', linewidth=0.8)
    axes[2].axhline(y=dS.quantile(0.95), color='red', linestyle='--',
                    label=f'95% = {dS.quantile(0.95):.3f}')
    axes[2].axhline(y=0, color='black', linestyle='-', linewidth=0.5)
    axes[2].set_ylabel('dS/dt')
    axes[2].set_title('Rate of Change of S')
    axes[2].legend(loc='upper right')
    axes[2].grid(True, alpha=0.3)
    
    # 图4：30日未来收益
    future_30d_full = np.log(sp500.shift(-30) / sp500)
    axes[3].plot(future_30d_full.index, future_30d_full.values, 'gray', linewidth=0.8)
    axes[3].axhline(y=0, color='black', linestyle='-', linewidth=0.5)
    axes[3].axhline(y=-0.10, color='red', linestyle='--', label='-10%')
    axes[3].set_ylabel('30d Return')
    axes[3].set_title('Future 30-Day Return')
    axes[3].legend(loc='upper right')
    axes[3].grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('EMIS_P1_revised.png', dpi=150, bbox_inches='tight')
    print("图表已保存: EMIS_P1_revised.png")
    plt.show()
    
    # ============================================
    # 总结
    # ============================================
    print("\n" + "="*60)
    print("关键发现")
    print("="*60)
    print("""
1. 纠缠熵 S 是**滞后指标**，不是领先指标
   - S 在崩盘**期间**达到最高值
   - S 最高时往往是底部，之后是反弹

2. 正确用法：
   - S 极高 → 买入信号（抄底）
   - dS 突然变大 → 危机正在发生
   - S 从低突破到高 → 危机刚开始

3. 对 EMIS 理论的修正：
   - RT 公式依然成立：高相关性 = 高纠缠熵
   - 但"时空塌缩"是危机**结果**，不是**原因**
   - 塌缩的终点是反弹的起点
    """)
    
    return S, dS

if __name__ == "__main__":
    S, dS = main()