#!/usr/bin/env python3
"""
Phase 4.2: EMIS 2D模型可视化 — 固定 mc = $100k nominal × CPI
==============================================================

与 4.1 的区别：
  4.1: mc 由扫描确定（每年不同，导致2000-2012年mc虚高，α虚高）
  4.2: mc 固定为 $100,000 nominal × 各年CPI系数（= 各年real $100k购买力）
       与 Yakovenko 系列文献一致

输入：
  parsed/emis_timeseries.csv   （T、r2_exp、tail_fraction沿用Phase4结果）
  data/cpi_yearly.csv          （年化CPI，Phase3输出）

输出（94-24前缀）：
  parsed/94-24-f1_timeseries_fixmc.pdf/png
  parsed/94-24-f2_phasediagram_fixmc.pdf/png
  parsed/94-24-f3_events_fixmc.pdf/png

注意：
  - α 和 r2_pow 需要用固定mc重新从 cpi_adjust.csv 拟合
  - 本脚本直接读取 emis_timeseries.csv 中的 T、r2_exp，
    对 α 用固定mc重新从 cpi_adjust.csv 的grid数据做OLS
  - 2013年排除

Author: Fei-Yun Wang
Date: 2026-02-22
Version: v1.0
"""

import os
import numpy as np
import pandas as pd
from scipy import stats
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.cm as cm
from matplotlib.collections import LineCollection
from matplotlib.colors import Normalize

# ============================================
# 配置
# ============================================

PROJECT_DIR    = './_emis_code/census-1994-2024/'
PARSED_DIR     = os.path.join(PROJECT_DIR, 'parsed')
DATA_DIR       = os.path.join(PROJECT_DIR, 'data')

CPI_FILE       = os.path.join(DATA_DIR,   'cpi_yearly.csv')
GRID_FILE      = os.path.join(PARSED_DIR, 'income_distribution_1994_2024_cpi_adjust.csv')
TS_FILE        = os.path.join(PARSED_DIR, 'emis_timeseries.csv')

PREFIX         = '94-24'
EXCLUDE_YEARS  = {2013}
YEARS          = [y for y in range(1994, 2025) if y not in EXCLUDE_YEARS]

# 固定mc门槛（nominal美元）
MC_NOMINAL     = 100_000

# 关键历史事件
EVENTS = [
    (1997, 'Asian\nFinancial Crisis',  'above'),
    (2000, 'Dot-com\nBubble',          'below'),
    (2008, 'Global\nFinancial Crisis', 'above'),
    (2017, 'Tax Cuts &\nJobs Act',     'below'),
    (2020, 'COVID-19\n+ QE',           'above'),
    (2022, 'Fed Rate\nHikes',          'below'),
]

COLOR_MAIN  = '#2166AC'
COLOR_WARM  = '#D6604D'
COLOR_GRID  = '#CCCCCC'
COLOR_FILL  = '#AEC7E8'
ALPHA_FILL  = 0.25
DPI_PNG     = 300


# ============================================
# Step 1: 计算固定mc（real dollars）
# ============================================

def load_cpi(cpi_file):
    """读取 cpi_yearly.csv → {year: inflation_factor}"""
    df = pd.read_csv(cpi_file)
    return dict(zip(df['year'].astype(int), df['inflation_factor']))


def fixed_mc_real(cpi_factors):
    """mc_real[year] = $100k × inflation_factor"""
    return {y: MC_NOMINAL * cpi_factors[y] for y in YEARS if y in cpi_factors}


# ============================================
# Step 2: 重新拟合 α（固定mc）
# ============================================

def refit_alpha(grid_file, mc_real_dict):
    """
    对每年，在 lower_bound_real >= mc_real[year] 的 grid rows 上
    做 log-log OLS，重新估计 α 和 r2_pow。
    tail rows（is_tail=True）不参与OLS（宽度未知，density无意义）。
    """
    df_all = pd.read_csv(grid_file)

    results = []
    for year in YEARS:
        mc = mc_real_dict.get(year)
        if mc is None:
            continue

        df_year = df_all[df_all['year'] == year]
        df_grid = df_year[~df_year['is_tail']].copy()
        df_grid = df_grid.dropna(subset=['upper_bound_real'])

        # 中点和密度
        df_grid['mid']     = (df_grid['lower_bound_real'] + df_grid['upper_bound_real']) / 2
        df_grid['bw']      = df_grid['upper_bound_real'] - df_grid['lower_bound_real']
        df_grid['density'] = df_grid['count'] / df_grid['bw']

        # 幂律段：mid >= mc
        df_pow = df_grid[(df_grid['mid'] >= mc) & (df_grid['density'] > 0)].sort_values('mid')

        if len(df_pow) < 3:
            results.append({'year': year, 'alpha': np.nan, 'alpha_se': np.nan,
                            'r2_pow': np.nan, 'n_pow_bins': len(df_pow), 'mc_real': mc})
            continue

        log_m = np.log(df_pow['mid'].values)
        log_d = np.log(df_pow['density'].values)
        slope, intercept, r, p, se = stats.linregress(log_m, log_d)

        alpha   = -slope if slope < 0 else np.nan
        r2_pow  = r**2 if slope < 0 else np.nan
        alpha_se = abs(se)

        # tail fraction
        total_hh = df_year['count'].sum()
        tail_hh  = df_year[df_year['is_tail']]['count'].sum()
        tail_frac = tail_hh / total_hh if total_hh > 0 else np.nan

        results.append({
            'year': year, 'alpha': round(alpha, 4) if not np.isnan(alpha) else np.nan,
            'alpha_se': round(alpha_se, 4),
            'r2_pow': round(r2_pow, 4) if not np.isnan(r2_pow) else np.nan,
            'n_pow_bins': len(df_pow),
            'mc_real': round(mc, 0),
            'tail_fraction': round(tail_frac, 4),
        })

    return pd.DataFrame(results)


# ============================================
# Step 3: 合并数据
# ============================================

def build_df(ts_file, df_alpha):
    """合并原始timeseries（T, r2_exp）与新拟合的α"""
    df_ts = pd.read_csv(ts_file)
    df_ts = df_ts[~df_ts['year'].isin(EXCLUDE_YEARS)].copy()

    df = df_ts[['year', 'T', 'r2_exp', 'n_exp_bins']].merge(
        df_alpha[['year', 'alpha', 'alpha_se', 'r2_pow',
                  'n_pow_bins', 'mc_real', 'tail_fraction']],
        on='year', how='inner'
    ).sort_values('year').reset_index(drop=True)

    print(f"\n{'year':>6} {'T':>10} {'alpha':>7} {'se':>6} {'mc_real':>10} {'r2_exp':>7} {'r2_pow':>7} {'n_pow':>6}")
    for _, row in df.iterrows():
        flag = ' ←' if pd.isna(row['alpha']) else ''
        print(f"{int(row['year']):>6} {row['T']:>10,.0f} {row['alpha']:>7.4f} "
              f"{row['alpha_se']:>6.4f} {row['mc_real']:>10,.0f} "
              f"{row['r2_exp']:>7.4f} {row['r2_pow']:>7.4f} "
              f"{int(row['n_pow_bins']):>6}{flag}"
              if not pd.isna(row['alpha']) else
              f"{int(row['year']):>6} {row['T']:>10,.0f} {'NaN':>7} {'':>6} {row['mc_real']:>10,.0f} "
              f"{row['r2_exp']:>7.4f} {'NaN':>7} {int(row['n_pow_bins']):>6}{flag}")
    return df


# ============================================
# 出图工具
# ============================================

def outpath(name, ext):
    return os.path.join(PARSED_DIR, f'{PREFIX}-{name}_fixmc.{ext}')


def _style_ax(ax, label=None):
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.grid(axis='y', color=COLOR_GRID, lw=0.5, zorder=0)
    ax.tick_params(labelsize=9)
    if label:
        ax.text(0.01, 0.92, label, transform=ax.transAxes,
                fontsize=11, fontweight='bold')


def _save(fig, name):
    fig.savefig(outpath(name, 'pdf'), dpi=300, bbox_inches='tight')
    fig.savefig(outpath(name, 'png'), dpi=DPI_PNG, bbox_inches='tight')
    plt.close(fig)
    print(f"  saved → {PREFIX}-{name}_fixmc")


# ============================================
# Figure 1: 4面板时间序列
# ============================================

def draw_figure1(df):
    fig, axes = plt.subplots(4, 1, figsize=(10, 14), sharex=True)
    fig.subplots_adjust(hspace=0.08, top=0.93, bottom=0.07, left=0.12, right=0.95)

    years = df['year'].values

    # (a) 温度 T
    ax = axes[0]
    ax.plot(years, df['T']/1000, color=COLOR_MAIN, lw=2, zorder=3)
    ax.fill_between(years, df['T']/1000, alpha=ALPHA_FILL, color=COLOR_FILL)
    ax.set_ylabel('Temperature $T$\n(thousand 2024 USD)', fontsize=10)
    ax.set_ylim(bottom=0)
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f'${x:.0f}k'))
    _style_ax(ax, '(a)')

    # (b) Tail fraction
    ax = axes[1]
    ax.plot(years, df['tail_fraction']*100, color=COLOR_WARM, lw=2, zorder=3)
    ax.fill_between(years, df['tail_fraction']*100, alpha=ALPHA_FILL, color='#F4A582')
    ax.set_ylabel('Power-law fraction\n(% of households)', fontsize=10)
    ax.set_ylim(bottom=0)
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f'{x:.0f}%'))
    _style_ax(ax, '(b)')

    # (c) α — 1994-1999灰色区域，2000+实线
    ax = axes[2]
    df_valid   = df.dropna(subset=['alpha'])
    df_invalid = df[df['alpha'].isna()]

    if len(df_invalid) > 0:
        x_lo = df_invalid['year'].min() - 0.5
        x_hi = df_invalid['year'].max() + 0.5
        ax.axvspan(x_lo, x_hi, color='#DDDDDD', alpha=0.5, zorder=0,
                   label='Data insufficient (1994–1999)')

    ax.plot(df_valid['year'], df_valid['alpha'], color='#1A7B3A', lw=2, zorder=3)
    ax.fill_between(df_valid['year'],
                    df_valid['alpha'] - df_valid['alpha_se'],
                    df_valid['alpha'] + df_valid['alpha_se'],
                    alpha=0.2, color='#1A7B3A')
    ax.axhline(2.0, color='gray', lw=1, ls='--', label='α = 2 (2D equilibrium)')
    ax.axhline(1.0, color='red',  lw=1, ls=':',  label='α = 1 (marginal stability)')
    ax.set_ylabel('Pareto exponent α\n(fixed $100k nominal mc)', fontsize=10)
    ax.legend(fontsize=7, loc='upper right', ncol=2)
    _style_ax(ax, '(c)')

    # (d) R²_exp
    ax = axes[3]
    ax.plot(years, df['r2_exp'], color='#7B3294', lw=2, zorder=3)
    ax.fill_between(years, df['r2_exp'], alpha=ALPHA_FILL, color='#C2A5CF')
    ax.axhline(0.95, color='gray', lw=1, ls='--', label='$R^2=0.95$')
    ax.set_ylabel('Exponential fit $R^2$', fontsize=10)
    ax.set_ylim(0.4, 1.02)
    ax.legend(fontsize=8, loc='lower left')
    ax.set_xlabel('Year', fontsize=10)
    _style_ax(ax, '(d)')

    ax.set_xlim(1993, 2025)
    ax.xaxis.set_major_locator(plt.MultipleLocator(5))
    ax.xaxis.set_minor_locator(plt.MultipleLocator(1))

    for axi in axes:
        axi.axvline(2013, color='gray', lw=0.8, ls=':', alpha=0.6, zorder=1)

    fig.suptitle('EMIS 2D Statistical Mechanics: U.S. Income Distribution 1994–2024\n'
                 '(Fixed mc = $100k nominal × CPI; 2024 constant dollars; 2013 excluded)',
                 fontsize=11, y=0.97)
    _save(fig, 'f1_timeseries')


# ============================================
# Figure 2: 相图
# ============================================

def draw_figure2(df):
    df_v = df.dropna(subset=['alpha']).copy()
    fig, ax = plt.subplots(figsize=(9, 7))
    fig.subplots_adjust(left=0.12, right=0.88, top=0.90, bottom=0.10)

    T     = df_v['T'].values / 1000
    alpha = df_v['alpha'].values
    years = df_v['year'].values

    norm = Normalize(vmin=years.min(), vmax=years.max())
    cmap = cm.get_cmap('coolwarm')

    points   = np.array([T, alpha]).T.reshape(-1, 1, 2)
    segments = np.concatenate([points[:-1], points[1:]], axis=1)
    lc = LineCollection(segments, cmap='coolwarm', norm=norm, lw=1.5, alpha=0.6, zorder=2)
    lc.set_array(years[:-1].astype(float))
    ax.add_collection(lc)

    sc = ax.scatter(T, alpha, c=years, cmap='coolwarm', norm=norm,
                    s=60, zorder=3, edgecolors='white', linewidths=0.5)

    label_years = {1994, 2000, 2008, 2020, 2022, 2024} & set(years.tolist())
    for _, row in df_v.iterrows():
        y = int(row['year'])
        if y in label_years:
            t_v = row['T'] / 1000
            a_v = row['alpha']
            dy  = 0.08 if a_v > df_v['alpha'].median() else -0.12
            ax.annotate(str(y), xy=(t_v, a_v),
                        xytext=(t_v + 3, a_v + dy), fontsize=8, color='#333333',
                        arrowprops=dict(arrowstyle='-', color='#999999', lw=0.8))

    ax.axhline(2.0, color='gray', lw=1, ls='--', label='α = 2 (2D equilibrium)')
    ax.axhline(1.0, color='red',  lw=1, ls=':',  label='α = 1 (marginal stability)')

    ax.text(0.02, 0.92, 'Thermal Equilibrium\n(α > 2)', transform=ax.transAxes,
            fontsize=9, color='#2166AC', alpha=0.8)
    ax.text(0.02, 0.08, 'Gravitational Collapse\n(α < 2)', transform=ax.transAxes,
            fontsize=9, color='#D6604D', alpha=0.8)

    mid = len(T) // 2
    if mid + 2 < len(T):
        ax.annotate('', xy=(T[mid+2], alpha[mid+2]), xytext=(T[mid], alpha[mid]),
                    arrowprops=dict(arrowstyle='->', color='#555555', lw=1.5))

    cbar = plt.colorbar(sc, ax=ax, pad=0.02)
    cbar.set_label('Year', fontsize=10)
    cbar.set_ticks([y for y in [1994, 2000, 2008, 2016, 2024] if y >= years.min()])

    ax.set_xlabel('Economic Temperature $T$ (thousand 2024 USD)', fontsize=11)
    ax.set_ylabel('Pareto Exponent α', fontsize=11)
    ax.legend(fontsize=9, loc='upper right')
    ax.set_title('Phase Diagram: U.S. Income Distribution 1994–2024\n'
                 '(Fixed mc = $100k nominal × CPI)', fontsize=11)
    _save(fig, 'f2_phasediagram')


# ============================================
# Figure 3: α(t) + 历史事件
# ============================================

def draw_figure3(df):
    fig, ax = plt.subplots(figsize=(12, 5))
    fig.subplots_adjust(left=0.08, right=0.97, top=0.78, bottom=0.12)

    # 分段：有α的年份（实线）vs 无α的年份（虚线区域）
    df_valid   = df.dropna(subset=['alpha']).copy()   # 2000+
    df_invalid = df[df['alpha'].isna()].copy()         # 1994-1999

    years = df_valid['year'].values
    alpha = df_valid['alpha'].values
    se    = df_valid['alpha_se'].values

    # 1994-1999：灰色阴影区 + 虚线（用T/max_alpha做占位线）
    if len(df_invalid) > 0:
        x_lo = df_invalid['year'].min() - 0.5
        x_hi = df_invalid['year'].max() + 0.5
        ax.axvspan(x_lo, x_hi, color='#DDDDDD', alpha=0.5, zorder=0)
        ax.text((x_lo + x_hi) / 2, 0,   # y位置后面set_ylim后再定
                'Data\nInsufficient\n(1994–1999)',
                ha='center', va='bottom', fontsize=8, color='#888888',
                transform=ax.get_xaxis_transform(),
                bbox=dict(boxstyle='round,pad=0.3', facecolor='white',
                          edgecolor='#CCCCCC', alpha=0.9))

    # 2000+：实线 + 误差带
    ax.plot(years, alpha, color='#1A7B3A', lw=2.5, zorder=3,
            label='Pareto α (reliable)')
    ax.fill_between(years, alpha - se, alpha + se,
                    alpha=0.2, color='#1A7B3A', label='±1 SE')

    # 理论线
    ax.axhline(2.0, color='gray', lw=1, ls='--')
    ax.axhline(1.0, color='red',  lw=1, ls=':')
    ax.text(2024.3, 2.03, 'α=2', fontsize=8, color='gray')
    ax.text(2024.3, 1.03, 'α=1', fontsize=8, color='red')

    # 历史事件
    y_max = alpha.max() + 0.8
    for event_year, label, pos in EVENTS:
        ax.axvline(event_year, color='#888888', lw=1, ls=':', alpha=0.8, zorder=1)
        y_label = y_max - 0.1 if pos == 'above' else y_max - 0.7
        ax.text(event_year, y_label, label, ha='center', va='top', fontsize=7.5,
                color='#444444',
                bbox=dict(boxstyle='round,pad=0.2', facecolor='white',
                          edgecolor='#AAAAAA', alpha=0.85))

    # 2013缺失
    ax.axvline(2013, color='gray', lw=0.8, ls=':', alpha=0.5)
    ax.text(2013, alpha.min() - 0.25, '2013\n(missing)', ha='center',
            fontsize=7, color='gray')

    ax.set_xlim(1993, 2025)
    ax.set_ylim(alpha.min() - 0.5, y_max + 0.3)
    ax.xaxis.set_major_locator(plt.MultipleLocator(5))
    ax.xaxis.set_minor_locator(plt.MultipleLocator(1))
    ax.set_xlabel('Year', fontsize=11)
    ax.set_ylabel('Pareto Exponent α', fontsize=11)
    ax.legend(fontsize=9, loc='upper right')
    ax.set_title('Pareto Exponent α(t): U.S. Income Distribution 1994–2024\n'
                 '(Fixed mc = $100k nominal × CPI; 1994–1999: single open-ended bin, α not estimable)',
                 fontsize=11)
    _save(fig, 'f3_events')


# ============================================
# 主程序
# ============================================

def main():
    print("=" * 60)
    print("Phase 4.2: 固定mc重新拟合α + 出图")
    print(f"  mc = ${MC_NOMINAL:,} nominal × CPI (各年2024 real)")
    print("=" * 60)

    # 读取CPI
    print("\n读取CPI...")
    cpi_factors = load_cpi(CPI_FILE)
    mc_real_dict = fixed_mc_real(cpi_factors)
    print(f"  mc_real范围: ${min(mc_real_dict.values()):,.0f} – ${max(mc_real_dict.values()):,.0f}")

    # 重新拟合α
    print("\n重新拟合α（固定mc）...")
    df_alpha = refit_alpha(GRID_FILE, mc_real_dict)

    # 保存固定mc的拟合结果
    out_alpha = os.path.join(PARSED_DIR, '94-24-pareto_fit_fixmc.csv')
    df_alpha.to_csv(out_alpha, index=False)
    print(f"  保存 → {out_alpha}")

    # 合并数据
    print("\n合并数据...")
    df = build_df(TS_FILE, df_alpha)

    # 保存合并后的时间序列
    out_ts = os.path.join(PARSED_DIR, '94-24-emis_timeseries_fixmc.csv')
    df.to_csv(out_ts, index=False)
    print(f"  保存 → {out_ts}")

    # 出图
    print("\n[Figure 1] 4面板时间序列...")
    draw_figure1(df)

    print("[Figure 2] 相图...")
    draw_figure2(df)

    print("[Figure 3] α(t) + 历史事件...")
    draw_figure3(df)

    print("\n" + "=" * 60)
    print("完成。")


if __name__ == '__main__':
    main()