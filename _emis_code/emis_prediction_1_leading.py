"""
EMIS P1: 危机预警指标 - 纠缠熵
================================

核心公式：S(t) = -1/N * log(det(Σ(t)))

作者：EMIS Framework
"""

import numpy as np
import pandas as pd
import yfinance as yf
import matplotlib.pyplot as plt
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# ============================================
# 第一部分：数据获取
# ============================================

def get_stock_data(tickers, start='2000-01-01', end=None):
    """
    获取股票价格数据
    """
    if end is None:
        end = datetime.today().strftime('%Y-%m-%d')
    
    print(f"下载 {len(tickers)} 只股票数据...")
    data = yf.download(tickers, start=start, end=end, progress=False)
    prices = data['Close']
    
    # 处理缺失值
    prices = prices.dropna(axis=1, how='all')
    prices = prices.ffill()
    prices = prices.dropna()
    
    print(f"获取 {len(prices.columns)} 只股票, {len(prices)} 天数据")
    return prices

def compute_returns(prices):
    """
    计算对数收益率
    """
    returns = np.log(prices / prices.shift(1))
    returns = returns.dropna()
    return returns

# ============================================
# 第二部分：纠缠熵计算
# ============================================

def compute_entanglement_entropy(returns, window=60):
    """
    计算市场纠缠熵
    
    公式: S(t) = -1/N * log(det(Σ(t)))
    """
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

# ============================================
# 第三部分：危机检测（已修复）
# ============================================

def identify_crashes(prices, threshold=-0.10, horizon=30):
    """
    识别市场崩盘
    
    参数:
        prices: 价格序列（Series，不是DataFrame）
        threshold: 跌幅阈值（如-10%）
        horizon: 检测窗口（天）
    
    返回:
        crashes: 崩盘日期列表
    """
    # 确保是 Series
    if isinstance(prices, pd.DataFrame):
        prices = prices.iloc[:, 0]  # 取第一列
    
    crashes = []
    
    for i in range(len(prices) - horizon):
        # 计算未来收益
        current_price = prices.iloc[i]
        future_price = prices.iloc[i + horizon]
        future_return = np.log(future_price / current_price)
        
        # 判断是否崩盘
        if future_return < threshold:
            crashes.append(prices.index[i])
    
    return crashes

def find_critical_threshold(S, crashes, window_before=5):
    """
    从历史崩盘找临界阈值
    """
    pre_crash_S = []
    
    for crash_date in crashes:
        if crash_date in S.index:
            idx = S.index.get_loc(crash_date)
            if idx >= window_before:
                pre_S = S.iloc[idx-window_before:idx].max()
                pre_crash_S.append(pre_S)
    
    if len(pre_crash_S) > 0:
        S_c = np.percentile(pre_crash_S, 25)
        return S_c
    else:
        return S.quantile(0.9)

# ============================================
# 第四部分：验证（已修复）
# ============================================

def evaluate_prediction(S, S_c, index_prices, horizon=30, threshold=-0.10):
    """
    评估预测准确性
    """
    # 确保 index_prices 是 Series
    if isinstance(index_prices, pd.DataFrame):
        index_prices = index_prices.iloc[:, 0]
    
    predictions = []
    
    for t in range(len(S) - horizon):
        date = S.index[t]
        S_value = S.iloc[t]
        
        if S_value > S_c:
            if date in index_prices.index:
                idx = index_prices.index.get_loc(date)
                if idx + horizon < len(index_prices):
                    current_price = index_prices.iloc[idx]
                    future_price = index_prices.iloc[idx + horizon]
                    future_return = np.log(future_price / current_price)
                    crash = future_return < threshold
                    predictions.append({
                        'date': date,
                        'S': S_value,
                        'future_return': future_return,
                        'crash': crash
                    })
    
    if len(predictions) == 0:
        return 0, 0, pd.DataFrame()
    
    df = pd.DataFrame(predictions)
    hit_rate = df['crash'].mean()
    
    return hit_rate, len(df), df

# ============================================
# 第五部分：主程序
# ============================================

def main():
    # 股票池
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
    print("EMIS P1: 危机预警指标")
    print("="*60)
    
    # 1. 获取数据
    prices = get_stock_data(tickers, start='2005-01-01')
    returns = compute_returns(prices)
    
    # 2. 计算纠缠熵
    print("\n计算纠缠熵...")
    S = compute_entanglement_entropy(returns, window=60)
    print(f"纠缠熵范围: [{S.min():.2f}, {S.max():.2f}]")
    print(f"均值: {S.mean():.2f}, 标准差: {S.std():.2f}")
    
    # 3. 获取市场指数
    print("\n下载 S&P 500 指数...")
    sp500_data = yf.download('^GSPC', start='2005-01-01', progress=False)
    sp500 = sp500_data['Close']
    
    # 确保是 Series
    if isinstance(sp500, pd.DataFrame):
        sp500 = sp500.iloc[:, 0]
    
    print(f"S&P 500 数据: {len(sp500)} 天")
    
    # 4. 识别历史崩盘
    print("\n识别历史崩盘...")
    crashes = identify_crashes(sp500, threshold=-0.10, horizon=30)
    print(f"发现 {len(crashes)} 次崩盘事件")
    
    # 显示崩盘日期
    if len(crashes) > 0:
        print("崩盘事件:")
        for c in crashes[:10]:  # 只显示前10个
            print(f"  {c.strftime('%Y-%m-%d')}")
        if len(crashes) > 10:
            print(f"  ... 共 {len(crashes)} 次")
    
    # 5. 计算临界阈值（样本内）
    train_end = '2020-01-01'
    S_train = S[S.index < train_end]
    crashes_train = [c for c in crashes if c < pd.Timestamp(train_end)]
    
    S_c = find_critical_threshold(S_train, crashes_train)
    print(f"\n临界阈值 S_c = {S_c:.4f}")
    print(f"（基于 {len(crashes_train)} 次样本内崩盘事件）")
    
    # 6. 样本外验证
    print("\n" + "-"*60)
    print("样本外验证 (2020-2024)")
    print("-"*60)
    
    S_test = S[S.index >= train_end]
    sp500_test = sp500[sp500.index >= train_end]
    
    hit_rate, n_pred, results = evaluate_prediction(
        S_test, S_c, sp500_test, horizon=30, threshold=-0.10
    )
    
    print(f"预警触发次数: {n_pred}")
    print(f"实际崩盘次数: {results['crash'].sum() if len(results) > 0 else 0}")
    print(f"命中率: {hit_rate:.1%}")
    
    # 显示预警详情
    if len(results) > 0:
        print("\n预警详情:")
        print(results.to_string())
    
    # 7. 可视化
    print("\n生成图表...")
    
    fig, axes = plt.subplots(3, 1, figsize=(14, 10), sharex=True)
    
    # 图1：市场指数
    axes[0].plot(sp500.index, sp500.values, 'b-', linewidth=0.8)
    axes[0].set_ylabel('S&P 500')
    axes[0].set_title('Market Index')
    axes[0].grid(True, alpha=0.3)
    
    # 图2：纠缠熵
    axes[1].plot(S.index, S.values, 'purple', linewidth=0.8)
    axes[1].axhline(y=S_c, color='red', linestyle='--', linewidth=2,
                    label=f'Critical Threshold S_c = {S_c:.2f}')
    axes[1].fill_between(S.index, S_c, S.values, 
                         where=(S.values > S_c), 
                         alpha=0.3, color='red',
                         label='Danger Zone')
    axes[1].set_ylabel('Entanglement Entropy S(t)')
    axes[1].set_title('EMIS Crisis Indicator')
    axes[1].legend(loc='upper right')
    axes[1].grid(True, alpha=0.3)
    
    # 图3：30日未来收益
    future_returns = np.log(sp500.shift(-30) / sp500)
    axes[2].plot(future_returns.index, future_returns.values, 
                 'g-', linewidth=0.8)
    axes[2].axhline(y=-0.10, color='red', linestyle='--', linewidth=2,
                    label='Crash Threshold (-10%)')
    axes[2].axhline(y=0, color='black', linestyle='-', linewidth=0.5)
    axes[2].set_ylabel('30-Day Forward Return')
    axes[2].set_title('Future Returns')
    axes[2].legend(loc='upper right')
    axes[2].grid(True, alpha=0.3)
    
    # 标注关键危机
    crisis_events = [
        ('2008-09-15', 'Lehman'),
        ('2020-02-20', 'COVID'),
        ('2022-01-03', '2022 Bear'),
    ]
    
    for date_str, label in crisis_events:
        try:
            date = pd.Timestamp(date_str)
            for ax in axes:
                ax.axvline(x=date, color='orange', linestyle=':', alpha=0.7)
            axes[0].annotate(label, xy=(date, axes[0].get_ylim()[1]), 
                           fontsize=8, rotation=90, va='top')
        except:
            pass
    
    plt.tight_layout()
    plt.savefig('EMIS_P1_crisis_indicator.png', dpi=150, bbox_inches='tight')
    print("图表已保存: EMIS_P1_crisis_indicator.png")
    plt.show()
    
    # 8. 输出结论
    print("\n" + "="*60)
    print("结论")
    print("="*60)
    
    if hit_rate > 0.6:
        print("✅ 预测成功！命中率 > 60%")
        print("   EMIS 纠缠熵临界假说得到支持")
    elif hit_rate > 0.4:
        print("🔶 部分成功。命中率在40-60%之间")
        print("   需要调整参数或扩大样本")
    else:
        print("❌ 预测失败。命中率 < 40%")
        print("   需要重新审视理论假设")
    
    print("="*60)
    
    return S, S_c, results

# ============================================
# 执行
# ============================================

if __name__ == "__main__":
    S, S_c, results = main()