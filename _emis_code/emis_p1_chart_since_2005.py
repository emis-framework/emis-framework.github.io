"""
EMIS P1 论文图表生成
Figure 1: 纠缠熵时间序列
Figure 2: 收益分布图
Figure 3: 跨市场对比
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from scipy import stats
import warnings
warnings.filterwarnings('ignore')

# 设置全局字体和样式
plt.rcParams['font.size'] = 10
plt.rcParams['axes.labelsize'] = 11
plt.rcParams['axes.titlesize'] = 12
plt.rcParams['figure.dpi'] = 150
plt.rcParams['savefig.dpi'] = 300
plt.rcParams['figure.figsize'] = (10, 8)

# ============================================
# 读取数据
# ============================================

def load_data():
    """读取缓存数据"""
    data = {}
    
    # 美国
    data['US'] = {
        'entropy': pd.read_csv('entropy_US_since2005.csv', index_col=0, parse_dates=True),
        'index': pd.read_csv('sp500.csv', index_col=0, parse_dates=True)
    }
    
    # 日本
    data['Japan'] = {
        'entropy': pd.read_csv('entropy_Japan_since2005_v2.csv', index_col=0, parse_dates=True),
        'index': pd.read_csv('index_Japan_since2005.csv', index_col=0, parse_dates=True)
    }
    
    # 德国
    data['Germany'] = {
        'entropy': pd.read_csv('entropy_DAX_historical.csv', index_col=0, parse_dates=True),
        'index': pd.read_csv('index_DAX.csv', index_col=0, parse_dates=True)
    }
    
    # 转换为Series
    for market in data:
        if isinstance(data[market]['entropy'], pd.DataFrame):
            data[market]['entropy'] = data[market]['entropy'].iloc[:, 0]
        if isinstance(data[market]['index'], pd.DataFrame):
            data[market]['index'] = data[market]['index'].iloc[:, 0]
    
    return data

def compute_trade_returns(S, index_prices, S_threshold, horizon=30):
    """计算交易收益"""
    trades = []
    
    for t in range(len(S) - horizon):
        date = S.index[t]
        S_value = S.iloc[t]
        
        if date in index_prices.index:
            try:
                idx = index_prices.index.get_loc(date)
                if idx + horizon < len(index_prices):
                    ret = np.log(float(index_prices.iloc[idx + horizon]) / 
                                float(index_prices.iloc[idx]))
                    trades.append({
                        'date': date,
                        'S': S_value,
                        'return': ret,
                        'signal': S_value > S_threshold
                    })
            except:
                pass
    
    return pd.DataFrame(trades)

# ============================================
# Figure 1: 纠缠熵时间序列
# ============================================

def create_figure1(data, save_path='figure1_entropy_timeseries.pdf'):
    """
    Figure 1: 纠缠熵时间序列（三面板）
    """
    
    S = data['US']['entropy']
    index_prices = data['US']['index']
    
    # 参数
    train_end = pd.Timestamp('2020-01-01')
    S_train = S[S.index < train_end]
    S_threshold = S_train.quantile(0.90)
    
    # 创建图形
    fig, axes = plt.subplots(3, 1, figsize=(12, 10), sharex=True,
                              gridspec_kw={'height_ratios': [2, 2, 1]})
    
    # =====================================
    # Panel A: S&P 500 价格
    # =====================================
    ax1 = axes[0]
    ax1.plot(index_prices.index, index_prices.values, 'b-', linewidth=0.8, label='S&P 500')
    ax1.set_ylabel('S&P 500 Index', fontsize=11)
    ax1.set_title('(a) Market Index', fontsize=12, fontweight='bold')
    ax1.legend(loc='upper left')
    ax1.grid(True, alpha=0.3)
    
    # 标记危机时期
    crisis_periods = [
        ('2008-09-01', '2009-03-31', '2008\nCrisis'),
        ('2011-08-01', '2011-10-31', '2011'),
        ('2015-08-01', '2015-09-30', '2015'),
        ('2018-12-01', '2018-12-31', '2018'),
        ('2020-02-15', '2020-03-31', 'COVID-19'),
        ('2022-01-01', '2022-10-31', '2022\nBear'),
    ]
    
    for start, end, label in crisis_periods:
        try:
            ax1.axvspan(pd.Timestamp(start), pd.Timestamp(end), 
                       alpha=0.2, color='red')
        except:
            pass
    
    # =====================================
    # Panel B: 纠缠熵
    # =====================================
    ax2 = axes[1]
    ax2.plot(S.index, S.values, 'purple', linewidth=0.8, label='Entanglement Entropy $\\mathcal{S}(t)$')
    ax2.axhline(y=S_threshold, color='red', linestyle='--', linewidth=1.5,
                label=f'Threshold $\\mathcal{{S}}_c$ = {S_threshold:.2f} (90th percentile)')
    
    # 填充高S区域
    ax2.fill_between(S.index, S_threshold, S.values,
                     where=(S.values > S_threshold),
                     alpha=0.3, color='red', label='Buy Signal Region')
    
    ax2.set_ylabel('Entanglement Entropy $\\mathcal{S}(t)$', fontsize=11)
    ax2.set_title('(b) Market Entanglement Entropy', fontsize=12, fontweight='bold')
    ax2.legend(loc='upper left', fontsize=9)
    ax2.grid(True, alpha=0.3)
    
    # 标记训练/测试分界
    ax2.axvline(x=train_end, color='green', linestyle=':', linewidth=2, alpha=0.7)
    ax2.text(train_end, ax2.get_ylim()[1]*0.95, ' Test Period →', 
             fontsize=9, color='green', va='top')
    
    # 同样标记危机时期
    for start, end, label in crisis_periods:
        try:
            ax2.axvspan(pd.Timestamp(start), pd.Timestamp(end), 
                       alpha=0.2, color='red')
        except:
            pass
    
    # =====================================
    # Panel C: 未来30日收益
    # =====================================
    ax3 = axes[2]
    future_returns = np.log(index_prices.shift(-30) / index_prices) * 100  # 转为百分比
    
    # 用颜色区分正负
    colors = ['green' if r > 0 else 'red' for r in future_returns.values]
    ax3.bar(future_returns.index, future_returns.values, width=2, color=colors, alpha=0.5)
    ax3.axhline(y=0, color='black', linewidth=0.5)
    ax3.axhline(y=-10, color='red', linestyle='--', linewidth=1, alpha=0.5, label='Crash threshold (-10%)')
    
    ax3.set_ylabel('30-Day Return (%)', fontsize=11)
    ax3.set_title('(c) Forward 30-Day Returns', fontsize=12, fontweight='bold')
    ax3.set_xlabel('Date', fontsize=11)
    ax3.legend(loc='lower left', fontsize=9)
    ax3.grid(True, alpha=0.3)
    ax3.set_ylim(-30, 30)
    
    # 格式化x轴日期
    ax3.xaxis.set_major_locator(mdates.YearLocator(2))
    ax3.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
    
    plt.tight_layout()
    plt.savefig(save_path, bbox_inches='tight', dpi=300)
    plt.savefig(save_path.replace('.pdf', '.png'), bbox_inches='tight', dpi=300)
    print(f"Figure 1 saved: {save_path}")
    plt.show()
    
    return fig

# ============================================
# Figure 2: 收益分布图
# ============================================

def create_figure2(data, save_path='figure2_return_distribution.pdf'):
    """
    Figure 2: 收益分布对比
    """
    
    S = data['US']['entropy']
    index_prices = data['US']['index']
    
    # 参数
    train_end = pd.Timestamp('2020-01-01')
    S_train = S[S.index < train_end]
    S_test = S[S.index >= train_end]
    index_test = index_prices[index_prices.index >= train_end]
    S_threshold = S_train.quantile(0.90)
    
    # 计算所有交易
    trades = compute_trade_returns(S_test, index_test, S_threshold, horizon=30)
    
    # 分组
    signal_returns = trades[trades['signal']]['return'].values * 100  # 转百分比
    random_returns = trades[~trades['signal']]['return'].values * 100
    
    # 创建图形
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    
    # =====================================
    # Panel A: 直方图对比
    # =====================================
    ax1 = axes[0]
    
    bins = np.linspace(-20, 25, 30)
    
    ax1.hist(random_returns, bins=bins, alpha=0.5, color='gray', 
             label=f'Random periods (n={len(random_returns)}, μ={np.mean(random_returns):.1f}%)',
             density=True)
    ax1.hist(signal_returns, bins=bins, alpha=0.7, color='red',
             label=f'High entropy signals (n={len(signal_returns)}, μ={np.mean(signal_returns):.1f}%)',
             density=True)
    
    # 均值线
    ax1.axvline(x=np.mean(random_returns), color='gray', linestyle='--', linewidth=2)
    ax1.axvline(x=np.mean(signal_returns), color='red', linestyle='--', linewidth=2)
    ax1.axvline(x=0, color='black', linestyle='-', linewidth=1)
    
    ax1.set_xlabel('30-Day Return (%)', fontsize=11)
    ax1.set_ylabel('Density', fontsize=11)
    ax1.set_title('(a) Return Distribution: Signal vs Random', fontsize=12, fontweight='bold')
    ax1.legend(loc='upper left', fontsize=9)
    ax1.grid(True, alpha=0.3)
    
    # =====================================
    # Panel B: 箱线图
    # =====================================
    ax2 = axes[1]
    
    box_data = [random_returns, signal_returns]
    bp = ax2.boxplot(box_data, labels=['Random\nPeriods', 'High Entropy\nSignals'],
                     patch_artist=True, widths=0.6)
    
    bp['boxes'][0].set_facecolor('lightgray')
    bp['boxes'][1].set_facecolor('lightcoral')
    
    ax2.axhline(y=0, color='black', linestyle='-', linewidth=1)
    
    # 添加均值点
    means = [np.mean(random_returns), np.mean(signal_returns)]
    ax2.scatter([1, 2], means, color='black', s=100, zorder=5, marker='D', label='Mean')
    
    # 添加统计信息
    for i, (d, m) in enumerate(zip(box_data, means)):
        ax2.text(i+1, ax2.get_ylim()[1]*0.9, 
                f'μ={m:.1f}%\nσ={np.std(d):.1f}%\nn={len(d)}',
                ha='center', fontsize=9)
    
    ax2.set_ylabel('30-Day Return (%)', fontsize=11)
    ax2.set_title('(b) Return Comparison', fontsize=12, fontweight='bold')
    ax2.legend(loc='lower right', fontsize=9)
    ax2.grid(True, alpha=0.3, axis='y')
    
    plt.tight_layout()
    plt.savefig(save_path, bbox_inches='tight', dpi=300)
    plt.savefig(save_path.replace('.pdf', '.png'), bbox_inches='tight', dpi=300)
    print(f"Figure 2 saved: {save_path}")
    plt.show()
    
    return fig

# ============================================
# Figure 3: 跨市场对比
# ============================================

def create_figure3(data, save_path='figure3_cross_market.pdf'):
    """
    Figure 3: 跨市场验证
    """
    
    fig, axes = plt.subplots(2, 3, figsize=(15, 8))
    
    markets = ['US', 'Japan', 'Germany']
    market_names = ['US (S&P 500)', 'Japan (Nikkei)', 'Germany (DAX)']
    colors = ['blue', 'red', 'green']
    
    train_end = pd.Timestamp('2020-01-01')
    
    for i, (market, name, color) in enumerate(zip(markets, market_names, colors)):
        S = data[market]['entropy']
        index_prices = data[market]['index']
        
        S_train = S[S.index < train_end]
        S_test = S[S.index >= train_end]
        index_test = index_prices[index_prices.index >= train_end]
        S_threshold = S_train.quantile(0.90)
        
        # =====================================
        # 上行：纠缠熵时间序列（测试期）
        # =====================================
        ax_top = axes[0, i]
        ax_top.plot(S_test.index, S_test.values, color=color, linewidth=0.8)
        ax_top.axhline(y=S_threshold, color='red', linestyle='--', linewidth=1.5)
        ax_top.fill_between(S_test.index, S_threshold, S_test.values,
                           where=(S_test.values > S_threshold),
                           alpha=0.3, color='red')
        ax_top.set_title(f'{name}', fontsize=12, fontweight='bold')
        ax_top.set_ylabel('$\\mathcal{S}(t)$')
        ax_top.grid(True, alpha=0.3)
        ax_top.xaxis.set_major_locator(mdates.YearLocator())
        ax_top.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
        
        # =====================================
        # 下行：收益分布
        # =====================================
        ax_bot = axes[1, i]
        
        trades = compute_trade_returns(S_test, index_test, S_threshold, horizon=30)
        signal_returns = trades[trades['signal']]['return'].values * 100
        
        if len(signal_returns) > 0:
            ax_bot.hist(signal_returns, bins=15, alpha=0.7, color=color, edgecolor='black')
            ax_bot.axvline(x=np.mean(signal_returns), color='red', linestyle='--', linewidth=2,
                          label=f'Mean = {np.mean(signal_returns):.1f}%')
            ax_bot.axvline(x=0, color='black', linestyle='-', linewidth=1)
            
            # 统计信息
            win_rate = np.mean(signal_returns > 0) * 100
            ax_bot.text(0.95, 0.95, f'Win Rate: {win_rate:.1f}%\nn = {len(signal_returns)}',
                       transform=ax_bot.transAxes, ha='right', va='top',
                       fontsize=10, bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
        
        ax_bot.set_xlabel('30-Day Return (%)')
        ax_bot.set_ylabel('Frequency')
        ax_bot.legend(loc='upper left', fontsize=9)
        ax_bot.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(save_path, bbox_inches='tight', dpi=300)
    plt.savefig(save_path.replace('.pdf', '.png'), bbox_inches='tight', dpi=300)
    print(f"Figure 3 saved: {save_path}")
    plt.show()
    
    return fig

# ============================================
# Figure 4: EMIS vs VIX 对比
# ============================================

def create_figure4(save_path='figure4_emis_vs_vix.pdf'):
    """
    Figure 4: EMIS vs VIX 性能对比
    """
    
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    
    # =====================================
    # Panel A: 柱状图对比
    # =====================================
    ax1 = axes[0]
    
    metrics = ['Win Rate\n(%)', 'Mean Return\n(%)', 'Std Dev\n(%)', 'Sharpe\nRatio']
    emis_values = [90.4, 6.07, 4.64, 1.31]
    vix_values = [82.3, 5.46, 6.35, 0.86]
    
    x = np.arange(len(metrics))
    width = 0.35
    
    bars1 = ax1.bar(x - width/2, emis_values, width, label='EMIS', color='steelblue', edgecolor='black')
    bars2 = ax1.bar(x + width/2, vix_values, width, label='VIX', color='coral', edgecolor='black')
    
    ax1.set_ylabel('Value', fontsize=11)
    ax1.set_title('(a) Performance Comparison: EMIS vs VIX', fontsize=12, fontweight='bold')
    ax1.set_xticks(x)
    ax1.set_xticklabels(metrics)
    ax1.legend(loc='upper right')
    ax1.grid(True, alpha=0.3, axis='y')
    
    # 添加数值标签
    for bar, val in zip(bars1, emis_values):
        ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5,
                f'{val:.1f}', ha='center', va='bottom', fontsize=9)
    for bar, val in zip(bars2, vix_values):
        ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5,
                f'{val:.1f}', ha='center', va='bottom', fontsize=9)
    
    # =====================================
    # Panel B: 优势百分比
    # =====================================
    ax2 = axes[1]
    
    differences = ['Win Rate', 'Mean Return', 'Volatility\n(lower is better)', 'Sharpe Ratio']
    diff_values = [8.1, 0.61, -1.71, 0.45]
    diff_colors = ['green' if v > 0 else 'green' if i == 2 else 'red' 
                   for i, v in enumerate(diff_values)]
    diff_colors = ['green', 'green', 'green', 'green']  # EMIS在所有维度都更好
    
    bars = ax2.barh(differences, diff_values, color=diff_colors, edgecolor='black', alpha=0.7)
    ax2.axvline(x=0, color='black', linewidth=1)
    ax2.set_xlabel('EMIS Advantage', fontsize=11)
    ax2.set_title('(b) EMIS Improvement over VIX', fontsize=12, fontweight='bold')
    ax2.grid(True, alpha=0.3, axis='x')
    
    # 添加数值标签
    for bar, val in zip(bars, diff_values):
        x_pos = val + 0.1 if val > 0 else val - 0.3
        ax2.text(x_pos, bar.get_y() + bar.get_height()/2,
                f'{val:+.2f}', ha='left' if val > 0 else 'right', va='center', fontsize=10)
    
    plt.tight_layout()
    plt.savefig(save_path, bbox_inches='tight', dpi=300)
    plt.savefig(save_path.replace('.pdf', '.png'), bbox_inches='tight', dpi=300)
    print(f"Figure 4 saved: {save_path}")
    plt.show()
    
    return fig

# ============================================
# 主程序
# ============================================

def main():
    print("="*60)
    print("EMIS P1 论文图表生成")
    print("="*60)
    
    # 读取数据
    print("\n读取数据...")
    try:
        data = load_data()
        print("数据读取成功")
    except FileNotFoundError as e:
        print(f"错误: {e}")
        print("请确保以下文件存在:")
        print("  - entropy_US_since2005.csv")
        print("  - sp500.csv")
        print("  - entropy_Japan_since2005_v2.csv")
        print("  - index_Japan_since2005.csv")
        print("  - entropy_DAX_historical.csv")
        print("  - index_DAX.csv")
        return
    
    # 生成图表
    print("\n生成 Figure 1: 纠缠熵时间序列...")
    create_figure1(data)
    
    print("\n生成 Figure 2: 收益分布图...")
    create_figure2(data)
    
    print("\n生成 Figure 3: 跨市场对比...")
    create_figure3(data)
    
    print("\n生成 Figure 4: EMIS vs VIX...")
    create_figure4()
    
    print("\n" + "="*60)
    print("所有图表生成完成！")
    print("="*60)
    print("\n生成的文件:")
    print("  - figure1_entropy_timeseries.pdf/png")
    print("  - figure2_return_distribution.pdf/png")
    print("  - figure3_cross_market.pdf/png")
    print("  - figure4_emis_vs_vix.pdf/png")

if __name__ == "__main__":
    main()