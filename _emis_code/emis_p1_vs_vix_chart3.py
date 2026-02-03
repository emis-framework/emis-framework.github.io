"""
更合理的对比方式
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# 加载数据
S = pd.read_csv('entanglement_entropy.csv', index_col=0, parse_dates=True).iloc[:, 0]
sp500 = pd.read_csv('sp500.csv', index_col=0, parse_dates=True).iloc[:, 0]
vix = pd.read_csv('vix.csv', index_col=0, parse_dates=True).iloc[:, 0]

# 对齐
common_idx = S.index.intersection(vix.index).intersection(sp500.index)
S = S.loc[common_idx]
vix = vix.loc[common_idx]
sp500 = sp500.loc[common_idx]

# 阈值
train_end = '2020-01-01'
S_threshold = S[S.index < train_end].quantile(0.90)
vix_threshold = vix[vix.index < train_end].quantile(0.90)

# 测试集
S_test = S[S.index >= train_end]
vix_test = vix[vix.index >= train_end]
sp500_test = sp500[sp500.index >= train_end]

# ============================================
# 三种对比方式
# ============================================

def get_trades_overlapping(indicator, sp500, threshold, horizon=30):
    """重叠交易（每个信号都算）"""
    results = []
    for t in range(len(indicator) - horizon):
        date = indicator.index[t]
        if indicator.iloc[t] > threshold and date in sp500.index:
            idx = sp500.index.get_loc(date)
            if idx + horizon < len(sp500):
                ret = np.log(sp500.iloc[idx + horizon] / sp500.iloc[idx])
                results.append({'return': ret, 'win': ret > 0})
    return pd.DataFrame(results)

def get_trades_non_overlapping(indicator, sp500, threshold, horizon=30):
    """不重叠交易（等待持有期结束）"""
    results = []
    t = 0
    while t < len(indicator) - horizon:
        date = indicator.index[t]
        if indicator.iloc[t] > threshold and date in sp500.index:
            idx = sp500.index.get_loc(date)
            if idx + horizon < len(sp500):
                ret = np.log(sp500.iloc[idx + horizon] / sp500.iloc[idx])
                results.append({'return': ret, 'win': ret > 0})
                t += horizon  # 跳过持有期
                continue
        t += 1
    return pd.DataFrame(results)

def get_trades_weekly(indicator, sp500, threshold, horizon=30):
    """每周最多一次交易"""
    results = []
    last_trade_week = None
    
    for t in range(len(indicator) - horizon):
        date = indicator.index[t]
        week = date.isocalendar()[1]
        year = date.year
        week_id = (year, week)
        
        if indicator.iloc[t] > threshold and week_id != last_trade_week:
            if date in sp500.index:
                idx = sp500.index.get_loc(date)
                if idx + horizon < len(sp500):
                    ret = np.log(sp500.iloc[idx + horizon] / sp500.iloc[idx])
                    results.append({'return': ret, 'win': ret > 0})
                    last_trade_week = week_id
    
    return pd.DataFrame(results)

# ============================================
# 计算三种方式的结果
# ============================================

print("="*70)
print("三种交易方式对比")
print("="*70)

methods = [
    ("重叠（每日）", get_trades_overlapping),
    ("不重叠（30天间隔）", get_trades_non_overlapping),
    ("每周最多一次", get_trades_weekly),
]

print(f"\n{'方式':<20} {'指标':<8} {'交易次数':<10} {'胜率':<10} {'平均收益':<12} {'夏普':<8}")
print("-"*70)

all_results = {}

for method_name, method_func in methods:
    emis_trades = method_func(S_test, sp500_test, S_threshold)
    vix_trades = method_func(vix_test, sp500_test, vix_threshold)
    
    all_results[method_name] = {'EMIS': emis_trades, 'VIX': vix_trades}
    
    for name, trades in [('EMIS', emis_trades), ('VIX', vix_trades)]:
        if len(trades) > 0:
            wr = trades['win'].mean()
            avg_ret = trades['return'].mean()
            sharpe = avg_ret / trades['return'].std() if trades['return'].std() > 0 else 0
            print(f"{method_name:<20} {name:<8} {len(trades):<10} {wr:<10.1%} {avg_ret:<12.1%} {sharpe:<8.2f}")

# ============================================
# 推荐的对比方式：每周最多一次
# ============================================

print("\n" + "="*70)
print("推荐方式：每周最多一次交易")
print("="*70)

emis_weekly = all_results["每周最多一次"]['EMIS']
vix_weekly = all_results["每周最多一次"]['VIX']

print(f"""
EMIS:
  交易次数: {len(emis_weekly)}
  胜率: {emis_weekly['win'].mean():.1%}
  平均收益: {emis_weekly['return'].mean():.1%}
  累计收益: {emis_weekly['return'].sum():.1%}

VIX:
  交易次数: {len(vix_weekly)}
  胜率: {vix_weekly['win'].mean():.1%}
  平均收益: {vix_weekly['return'].mean():.1%}
  累计收益: {vix_weekly['return'].sum():.1%}
""")

# 判断谁赢
emis_wr = emis_weekly['win'].mean()
vix_wr = vix_weekly['win'].mean()
emis_ret = emis_weekly['return'].mean()
vix_ret = vix_weekly['return'].mean()

print("="*70)
if emis_wr > vix_wr and emis_ret > vix_ret:
    print("✅ EMIS 全面优于 VIX")
elif emis_wr > vix_wr:
    print("🔶 EMIS 胜率更高，VIX 收益更高")
elif emis_ret > vix_ret:
    print("🔶 EMIS 收益更高，VIX 胜率更高")
else:
    print("⚠️ VIX 优于 EMIS")
print("="*70)

# ============================================
# 修正版图表
# ============================================

fig, axes = plt.subplots(2, 2, figsize=(14, 10))

# 图1: 重叠交易累计收益
ax = axes[0, 0]
emis_ov = all_results["重叠（每日）"]['EMIS']['return'].cumsum() * 100
vix_ov = all_results["重叠（每日）"]['VIX']['return'].cumsum() * 100
ax.plot(emis_ov.values, 'purple', label=f'EMIS (n={len(emis_ov)})', linewidth=2)
ax.plot(vix_ov.values, 'orange', label=f'VIX (n={len(vix_ov)})', linewidth=2)
ax.set_title('Overlapping Trades (Original Method)')
ax.set_xlabel('Trade #')
ax.set_ylabel('Cumulative Return (%)')
ax.legend()
ax.grid(True, alpha=0.3)

# 图2: 每周交易累计收益
ax = axes[0, 1]
emis_wk = all_results["每周最多一次"]['EMIS']['return'].cumsum() * 100
vix_wk = all_results["每周最多一次"]['VIX']['return'].cumsum() * 100
ax.plot(emis_wk.values, 'purple', label=f'EMIS (n={len(emis_wk)})', linewidth=2)
ax.plot(vix_wk.values, 'orange', label=f'VIX (n={len(vix_wk)})', linewidth=2)
ax.set_title('Weekly Trades (Recommended)')
ax.set_xlabel('Trade #')
ax.set_ylabel('Cumulative Return (%)')
ax.legend()
ax.grid(True, alpha=0.3)

# 图3: 收益分布对比（每周）
ax = axes[1, 0]
ax.hist(emis_weekly['return']*100, bins=20, alpha=0.6, color='purple', label='EMIS')
ax.hist(vix_weekly['return']*100, bins=20, alpha=0.6, color='orange', label='VIX')
ax.axvline(x=0, color='black', linestyle='--')
ax.axvline(x=emis_weekly['return'].mean()*100, color='purple', linestyle='-', linewidth=2)
ax.axvline(x=vix_weekly['return'].mean()*100, color='orange', linestyle='-', linewidth=2)
ax.set_title('Return Distribution (Weekly)')
ax.set_xlabel('Return (%)')
ax.set_ylabel('Frequency')
ax.legend()

# 图4: 指标对比（使用每周数据）
ax = axes[1, 1]
metrics = ['Win Rate\n(%)', 'Avg Return\n(%)', 'Sharpe\n(×10)']

emis_sharpe = emis_weekly['return'].mean() / emis_weekly['return'].std() if emis_weekly['return'].std() > 0 else 0
vix_sharpe = vix_weekly['return'].mean() / vix_weekly['return'].std() if vix_weekly['return'].std() > 0 else 0

emis_vals = [emis_weekly['win'].mean()*100, emis_weekly['return'].mean()*100, emis_sharpe*10]
vix_vals = [vix_weekly['win'].mean()*100, vix_weekly['return'].mean()*100, vix_sharpe*10]

x = np.arange(len(metrics))
width = 0.35
bars1 = ax.bar(x - width/2, emis_vals, width, label='EMIS', color='purple', alpha=0.8)
bars2 = ax.bar(x + width/2, vix_vals, width, label='VIX', color='orange', alpha=0.8)

ax.set_xticks(x)
ax.set_xticklabels(metrics)
ax.set_title('Performance Metrics (Weekly Trades)')
ax.legend()

# 添加数值
for bar in bars1:
    h = bar.get_height()
    ax.annotate(f'{h:.1f}', xy=(bar.get_x() + bar.get_width()/2, h),
                xytext=(0, 3), textcoords="offset points", ha='center')
for bar in bars2:
    h = bar.get_height()
    ax.annotate(f'{h:.1f}', xy=(bar.get_x() + bar.get_width()/2, h),
                xytext=(0, 3), textcoords="offset points", ha='center')

plt.tight_layout()
plt.savefig('fig4_final.png', dpi=150)
plt.show()

print("\n图表已保存: fig4_final.png")