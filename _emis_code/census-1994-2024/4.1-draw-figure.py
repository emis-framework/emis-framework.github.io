#!/usr/bin/env python3
"""
Phase 4.1: EMIS 2D模型可视化
==============================

输出两套图，每套3张（PDF + PNG）：
  套1 (94-24): 完整1994-2024数据
  套2 (00-24): 2000-2024数据（排除1994-1999早期粗粒度数据）

每套3张图：
  Figure 1: 4面板时间序列（T, tail_fraction, α, R²_exp）
  Figure 2: 相图（T vs α，颜色=年份，轨迹箭头）
  Figure 3: α(t) + 关键历史事件标注

2013年数据排除（Census数据源不同，hinc01替代hinc06，不可比）

Author: Fei-Yun Wang
Date: 2026-02-22
Version: v1.1
"""

import os
import numpy as np
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import matplotlib.patches as mpatches
from matplotlib.collections import LineCollection
from matplotlib.colors import Normalize

# ============================================
# 配置
# ============================================

PROJECT_DIR  = './_emis_code/census-1994-2024/'
PARSED_DIR   = os.path.join(PROJECT_DIR, 'parsed')
INPUT_FILE   = os.path.join(PARSED_DIR, 'emis_timeseries.csv')

# 两套数据集定义：(前缀, 起始年份, 标题后缀)
DATASETS = [
    ('94-24', 1994, '1994–2024'),
    ('00-24', 2000, '2000–2024'),
]

# 2013年排除（数据源不同）
EXCLUDE_YEARS = {2013}

# 关键历史事件
EVENTS = [
    (1997, 'Asian\nFinancial Crisis',  'above'),
    (2000, 'Dot-com\nBubble',          'below'),
    (2008, 'Global\nFinancial Crisis', 'above'),
    (2017, 'Tax Cuts &\nJobs Act',     'below'),
    (2020, 'COVID-19\n+ QE',           'above'),
    (2022, 'Fed Rate\nHikes',          'below'),
]

# 顶刊配色（Nature风格）
COLOR_MAIN   = '#2166AC'
COLOR_WARM   = '#D6604D'
COLOR_GRID   = '#CCCCCC'
COLOR_FILL   = '#AEC7E8'
ALPHA_FILL   = 0.25
DPI_PNG      = 300


# ============================================
# 数据加载
# ============================================

def load_data(year_start=1994):
    df = pd.read_csv(INPUT_FILE)
    df = df[~df['year'].isin(EXCLUDE_YEARS)].copy()
    df = df[df['year'] >= year_start].copy()
    df = df.sort_values('year').reset_index(drop=True)
    print(f"  加载: {len(df)} 年，{df['year'].min()}–{df['year'].max()}（已排除 {EXCLUDE_YEARS}）")
    return df


def outpath(prefix, name, ext):
    """生成带前缀的输出路径"""
    return os.path.join(PARSED_DIR, f'{prefix}-{name}.{ext}')


# ============================================
# Figure 1: 4面板时间序列
# ============================================

def draw_figure1(df, prefix, title_suffix):
    fig, axes = plt.subplots(4, 1, figsize=(10, 14), sharex=True)
    fig.subplots_adjust(hspace=0.08, top=0.93, bottom=0.07, left=0.12, right=0.95)

    years = df['year'].values

    # ── (a) 温度 T ──────────────────────────────
    ax = axes[0]
    ax.plot(years, df['T'] / 1000, color=COLOR_MAIN, lw=2, zorder=3)
    ax.fill_between(years, df['T'] / 1000, alpha=ALPHA_FILL, color=COLOR_FILL)
    ax.set_ylabel('Temperature $T$\n(thousand 2024 USD)', fontsize=10)
    ax.set_ylim(bottom=0)
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f'${x:.0f}k'))
    _style_ax(ax, label='(a)')

    # ── (b) Tail fraction ───────────────────────
    ax = axes[1]
    ax.plot(years, df['tail_fraction'] * 100, color=COLOR_WARM, lw=2, zorder=3)
    ax.fill_between(years, df['tail_fraction'] * 100, alpha=ALPHA_FILL, color='#F4A582')
    ax.set_ylabel('Power-law fraction\n(% of households)', fontsize=10)
    ax.set_ylim(bottom=0)
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f'{x:.0f}%'))
    _style_ax(ax, label='(b)')

    # ── (c) Pareto α ────────────────────────────
    ax = axes[2]
    ax.plot(years, df['alpha'], color='#1A7B3A', lw=2, zorder=3)
    # 误差带
    ax.fill_between(years,
                    df['alpha'] - df['alpha_se'],
                    df['alpha'] + df['alpha_se'],
                    alpha=0.2, color='#1A7B3A')
    # 理论临界线 α=2（2D平衡态边界）
    ax.axhline(2.0, color='gray', lw=1, ls='--', zorder=2, label='α = 2 (2D equilibrium)')
    ax.axhline(1.0, color='red',  lw=1, ls=':',  zorder=2, label='α = 1 (marginal stability)')
    ax.set_ylabel('Pareto exponent α', fontsize=10)
    ax.legend(fontsize=8, loc='upper right')
    _style_ax(ax, label='(c)')

    # ── (d) R²_exp ──────────────────────────────
    ax = axes[3]
    ax.plot(years, df['r2_exp'], color='#7B3294', lw=2, zorder=3)
    ax.fill_between(years, df['r2_exp'], alpha=ALPHA_FILL, color='#C2A5CF')
    ax.axhline(0.95, color='gray', lw=1, ls='--', zorder=2, label='$R^2 = 0.95$')
    ax.set_ylabel('Exponential fit $R^2$', fontsize=10)
    ax.set_ylim(0.4, 1.02)
    ax.legend(fontsize=8, loc='lower left')
    ax.set_xlabel('Year', fontsize=10)
    _style_ax(ax, label='(d)')

    # X轴设置
    xmin = df['year'].min() - 1
    ax.set_xlim(xmin, 2025)
    ax.xaxis.set_major_locator(plt.MultipleLocator(5))
    ax.xaxis.set_minor_locator(plt.MultipleLocator(1))

    # 标注2013缺失（仅94-24套需要）
    if 2013 > df['year'].min():
        for axi in axes:
            axi.axvline(2013, color='gray', lw=0.8, ls=':', alpha=0.6, zorder=1)

    fig.suptitle(f'EMIS 2D Statistical Mechanics: Evolution of U.S. Income Distribution\n'
                 f'({title_suffix}, 2024 constant dollars; 2013 excluded: data source change)',
                 fontsize=11, y=0.97)

    _save(fig, outpath(prefix, 'f1_timeseries', 'pdf'),
               outpath(prefix, 'f1_timeseries', 'png'))
    print(f"  Figure 1 saved → {prefix}-f1_timeseries")


# ============================================
# Figure 2: 相图 T vs α
# ============================================

def draw_figure2(df, prefix, title_suffix):
    fig, ax = plt.subplots(figsize=(9, 7))
    fig.subplots_adjust(left=0.12, right=0.88, top=0.90, bottom=0.10)

    T     = df['T'].values / 1000
    alpha = df['alpha'].values
    years = df['year'].values

    # 颜色映射：年份
    norm   = Normalize(vmin=years.min(), vmax=years.max())
    cmap   = cm.get_cmap('coolwarm')
    colors = [cmap(norm(y)) for y in years]

    # 轨迹线（渐变色）
    points   = np.array([T, alpha]).T.reshape(-1, 1, 2)
    segments = np.concatenate([points[:-1], points[1:]], axis=1)
    lc = LineCollection(segments, cmap='coolwarm', norm=norm, lw=1.5, alpha=0.6, zorder=2)
    lc.set_array(years[:-1].astype(float))
    ax.add_collection(lc)

    # 散点
    sc = ax.scatter(T, alpha, c=years, cmap='coolwarm', norm=norm,
                    s=60, zorder=3, edgecolors='white', linewidths=0.5)

    # 标注关键年份（只标注数据集内存在的年份）
    label_years = {1994, 2000, 2008, 2020, 2022, 2024} & set(years.tolist())
    for _, row in df.iterrows():
        y = int(row['year'])
        if y in label_years:
            t_val = row['T'] / 1000
            a_val = row['alpha']
            offset = (5, 8) if a_val > df['alpha'].median() else (5, -12)
            ax.annotate(str(y), xy=(t_val, a_val),
                        xytext=(t_val + offset[0], a_val + offset[1]/100),
                        fontsize=8, color='#333333',
                        arrowprops=dict(arrowstyle='-', color='#999999', lw=0.8))

    # 理论分界线
    ax.axhline(2.0, color='gray', lw=1, ls='--', label='α = 2 (2D equilibrium boundary)')
    ax.axhline(1.0, color='red',  lw=1, ls=':',  label='α = 1 (marginal stability)')

    # 区域标注
    ax.text(0.02, 0.92, 'Thermal Equilibrium\n(α > 2)', transform=ax.transAxes,
            fontsize=9, color='#2166AC', alpha=0.8)
    ax.text(0.02, 0.12, 'Gravitational Collapse\n(α < 2)', transform=ax.transAxes,
            fontsize=9, color='#D6604D', alpha=0.8)

    # 方向箭头
    mid = len(T) // 2
    ax.annotate('', xy=(T[mid+2], alpha[mid+2]),
                xytext=(T[mid], alpha[mid]),
                arrowprops=dict(arrowstyle='->', color='#555555', lw=1.5))

    # Colorbar
    cbar = plt.colorbar(sc, ax=ax, pad=0.02)
    cbar.set_label('Year', fontsize=10)
    tick_years = [y for y in [1994, 2000, 2008, 2016, 2024] if y >= years.min()]
    cbar.set_ticks(tick_years)

    ax.set_xlabel('Economic Temperature $T$ (thousand 2024 USD)', fontsize=11)
    ax.set_ylabel('Pareto Exponent α', fontsize=11)
    ax.legend(fontsize=9, loc='upper right')
    ax.set_title(f'Phase Diagram: U.S. Income Distribution {title_suffix}\n'
                 f'(Trajectory from thermal equilibrium toward gravitational collapse)',
                 fontsize=11)

    _save(fig, outpath(prefix, 'f2_phasediagram', 'pdf'),
               outpath(prefix, 'f2_phasediagram', 'png'))
    print(f"  Figure 2 saved → {prefix}-f2_phasediagram")


# ============================================
# Figure 3: α(t) + 历史事件
# ============================================

def draw_figure3(df, prefix, title_suffix):
    fig, ax = plt.subplots(figsize=(12, 5))
    fig.subplots_adjust(left=0.08, right=0.97, top=0.78, bottom=0.12)

    years = df['year'].values
    alpha = df['alpha'].values
    se    = df['alpha_se'].values

    ax.plot(years, alpha, color='#1A7B3A', lw=2.5, zorder=3)
    ax.fill_between(years, alpha - se, alpha + se,
                    alpha=0.2, color='#1A7B3A', label='±1 SE')

    # 理论线
    ax.axhline(2.0, color='gray', lw=1, ls='--', zorder=2)
    ax.axhline(1.0, color='red',  lw=1, ls=':',  zorder=2)
    ax.text(2024.2, 2.01, 'α=2', fontsize=8, color='gray', va='bottom')
    ax.text(2024.2, 1.01, 'α=1', fontsize=8, color='red',  va='bottom')

    # 历史事件标注
    y_top = ax.get_ylim()[1] if ax.get_ylim()[1] > 0 else 7.0
    for event_year, label, pos in EVENTS:
        ax.axvline(event_year, color='#888888', lw=1, ls=':', alpha=0.8, zorder=1)
        y_label = 6.8 if pos == 'above' else 5.8
        ax.text(event_year, y_label, label,
                ha='center', va='bottom', fontsize=7.5,
                color='#444444',
                bbox=dict(boxstyle='round,pad=0.2', facecolor='white',
                          edgecolor='#AAAAAA', alpha=0.85))

    # 标注2013缺失（仅94-24套）
    if df['year'].min() < 2013:
        ax.axvline(2013, color='gray', lw=0.8, ls=':', alpha=0.5)
        ax.text(2013, alpha.min() - 0.15, '2013\n(missing)', ha='center',
                fontsize=7, color='gray')

    xmin = df['year'].min() - 1
    ax.set_xlim(xmin, 2025)
    ax.set_ylim(alpha.min() - 0.5, alpha.max() + 1.0)
    ax.xaxis.set_major_locator(plt.MultipleLocator(5))
    ax.xaxis.set_minor_locator(plt.MultipleLocator(1))
    ax.set_xlabel('Year', fontsize=11)
    ax.set_ylabel('Pareto Exponent α', fontsize=11)
    ax.legend(fontsize=9, loc='upper right')
    ax.set_title(f'Pareto Exponent α(t) with Historical Events: U.S. Income Distribution {title_suffix}',
                 fontsize=11)

    _save(fig, outpath(prefix, 'f3_events', 'pdf'),
               outpath(prefix, 'f3_events', 'png'))
    print(f"  Figure 3 saved → {prefix}-f3_events")


# ============================================
# 工具函数
# ============================================

def _style_ax(ax, label=None):
    """统一坐标轴风格"""
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.grid(axis='y', color=COLOR_GRID, lw=0.5, zorder=0)
    ax.tick_params(labelsize=9)
    if label:
        ax.text(0.01, 0.92, label, transform=ax.transAxes,
                fontsize=11, fontweight='bold')


def _save(fig, pdf_path, png_path):
    fig.savefig(pdf_path, dpi=300, bbox_inches='tight')
    fig.savefig(png_path, dpi=DPI_PNG, bbox_inches='tight')
    plt.close(fig)


# ============================================
# 主程序
# ============================================

def main():
    print("=" * 60)
    print("Phase 4.1: 出图（两套）")
    print("=" * 60)

    all_files = []
    for prefix, year_start, title_suffix in DATASETS:
        print(f"\n{'─'*50}")
        print(f"套: {prefix}  ({title_suffix})")
        print(f"{'─'*50}")

        df = load_data(year_start=year_start)

        print(f"[Figure 1] 4面板时间序列...")
        draw_figure1(df, prefix, title_suffix)

        print(f"[Figure 2] 相图...")
        draw_figure2(df, prefix, title_suffix)

        print(f"[Figure 3] α(t) + 历史事件...")
        draw_figure3(df, prefix, title_suffix)

        for name, ext in [('f1_timeseries','pdf'), ('f1_timeseries','png'),
                          ('f2_phasediagram','pdf'), ('f2_phasediagram','png'),
                          ('f3_events','pdf'), ('f3_events','png')]:
            all_files.append(outpath(prefix, name, ext))

    print(f"\n{'='*60}")
    print("完成。输出文件：")
    for f in all_files:
        size = os.path.getsize(f) // 1024 if os.path.exists(f) else 0
        print(f"  {os.path.basename(f)}  ({size} KB)")


if __name__ == '__main__':
    main()