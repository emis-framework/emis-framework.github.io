"""
EMIS 论文图表生成
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

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
S_threshold = S[S.index < '2020-01-01'].quantile(0.90)
vix_threshold = vix[vix.index < '2020-01-01'].quantile(0.90)

# ============================================
# 图1: 时间序列对比
# ============================================

fig, axes = plt.subplots(3, 1, figsize=(14, 10), sharex=True)

# S&P 500
axes[0].plot(sp500.index, sp500.values, 'b-', linewidth=0.8)
axes[0].set_ylabel('S&P 500', fontsize=12)
axes[0].set_title('Market Index', fontsize=14)

# EMIS
axes[1].plot(S.index, S.values, 'purple', linewidth=0.8)
axes[1].axhline(y=S_threshold, color='red', linestyle='--', label=f'90th percentile = {S_threshold:.2f}')
axes[1].fill_between(S.index, S_threshold, S.values, 
                     where=(S.values > S_threshold), alpha=0.3, color='red')
axes[1].set_ylabel('EMIS Entropy S', fontsize=12)
axes[1].set_title('Entanglement Entropy', fontsize=14)
axes[1].legend()

# VIX
axes[2].plot(vix.index, vix.values, 'orange', linewidth=0.8)
axes[2].axhline(y=vix_threshold, color='red', linestyle='--', label=f'90th percentile = {vix_threshold:.1f}')
axes[2].fill_between(vix.index, vix_threshold, vix.values,
                     where=(vix.values > vix_threshold), alpha=0.3, color='red')
axes[2].set_ylabel('VIX', fontsize=12)
axes[2].set_title('Volatility Index', fontsize=14)
axes[2].legend()

plt.tight_layout()
plt.savefig('fig1_timeseries.png', dpi=150)
plt.show()
print("图1 已保存")

# ============================================
# 图2: 胜率对比
# ============================================

thresholds = [75, 80, 85, 90, 95]
emis_wr = [71.0, 73.1, 75.7, 81.5, 87.2]
vix_wr = [70.5, 71.2, 71.3, 72.1, 74.6]

fig, ax = plt.subplots(figsize=(10, 6))

x = np.arange(len(thresholds))
width = 0.35

bars1 = ax.bar(x - width/2, emis_wr, width, label='EMIS', color='purple', alpha=0.8)
bars2 = ax.bar(x + width/2, vix_wr, width, label='VIX', color='orange', alpha=0.8)

ax.set_xlabel('Threshold Percentile', fontsize=12)
ax.set_ylabel('Win Rate (%)', fontsize=12)
ax.set_title('Win Rate Comparison: EMIS vs VIX', fontsize=14)
ax.set_xticks(x)
ax.set_xticklabels([f'{t}%' for t in thresholds])
ax.legend()
ax.set_ylim([65, 95])

# 添加数值标签
for bar in bars1:
    height = bar.get_height()
    ax.annotate(f'{height:.1f}%', xy=(bar.get_x() + bar.get_width()/2, height),
                xytext=(0, 3), textcoords="offset points", ha='center', va='bottom')

for bar in bars2:
    height = bar.get_height()
    ax.annotate(f'{height:.1f}%', xy=(bar.get_x() + bar.get_width()/2, height),
                xytext=(0, 3), textcoords="offset points", ha='center', va='bottom')

plt.tight_layout()
plt.savefig('fig2_winrate.png', dpi=150)
plt.show()
print("图2 已保存")

# ============================================
# 图3: 散点图
# ============================================

future_30d = np.log(sp500.shift(-30) / sp500)

fig, ax = plt.subplots(figsize=(10, 8))

valid = ~(S.isna() | vix.isna() | future_30d.isna())
S_valid = S[valid]
vix_valid = vix[valid]
ret_valid = future_30d[valid]

scatter = ax.scatter(S_valid, vix_valid, c=ret_valid, cmap='RdYlGn', 
                     alpha=0.5, s=10, vmin=-0.15, vmax=0.15)

ax.axvline(x=S_threshold, color='purple', linestyle='--', label=f'EMIS threshold')
ax.axhline(y=vix_threshold, color='orange', linestyle='--', label=f'VIX threshold')

ax.set_xlabel('EMIS Entropy S', fontsize=12)
ax.set_ylabel('VIX', fontsize=12)
ax.set_title('EMIS vs VIX (color = 30-day forward return)', fontsize=14)

cbar = plt.colorbar(scatter)
cbar.set_label('30-day Return', fontsize=12)

ax.legend()
plt.tight_layout()
plt.savefig('fig3_scatter.png', dpi=150)
plt.show()
print("图3 已保存")

# ============================================
# 图4: 累计收益对比
# ============================================

def compute_cumulative_returns(indicator, sp500, threshold, horizon=30):
    """计算累计收益"""
    cum_ret = [0]
    dates = [indicator.index[0]]
    
    t = 0
    while t < len(indicator) - horizon:
        date = indicator.index[t]
        value = indicator.iloc[t]
        
        if value > threshold:
            if date in sp500.index:
                idx = sp500.index.get_loc(date)
                if idx + horizon < len(sp500):
                    ret = np.log(sp500.iloc[idx + horizon] / sp500.iloc[idx])
                    cum_ret.append(cum_ret[-1] + ret)
                    dates.append(sp500.index[idx + horizon])
                    t += horizon  # 跳过持有期
                    continue
        t += 1
    
    return pd.Series(cum_ret, index=dates)

# 只看测试集
test_start = '2020-01-01'
S_test = S[S.index >= test_start]
vix_test = vix[vix.index >= test_start]
sp500_test = sp500[sp500.index >= test_start]

emis_cum = compute_cumulative_returns(S_test, sp500_test, S_threshold)
vix_cum = compute_cumulative_returns(vix_test, sp500_test, vix_threshold)

fig, ax = plt.subplots(figsize=(12, 6))

ax.plot(emis_cum.index, emis_cum.values * 100, 'purple', linewidth=2, label='EMIS Strategy')
ax.plot(vix_cum.index, vix_cum.values * 100, 'orange', linewidth=2, label='VIX Strategy')

ax.set_xlabel('Date', fontsize=12)
ax.set_ylabel('Cumulative Return (%)', fontsize=12)
ax.set_title('Cumulative Returns: EMIS vs VIX (2020-2024)', fontsize=14)
ax.legend()
ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('fig4_cumulative.png', dpi=150)
plt.show()
print("图4 已保存")

print("\n所有图表已生成！")