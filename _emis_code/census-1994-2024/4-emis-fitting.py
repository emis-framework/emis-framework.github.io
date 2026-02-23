#!/usr/bin/env python3
"""
Phase 4: EMIS 2D模型批量拟合
==============================

对1994-2024每年数据：
  Step 1: 扫描候选 m_c，找到最优相变点        → parsed/mc_scan.csv
  Step 2: 在 [0, m_c) 拟合指数段，提取温度T   → parsed/exp_fit.csv
  Step 3: 在 [m_c, ∞) 做 Pareto MLE，提取α   → parsed/pareto_fit.csv
  Step 4: 合并输出时间序列                    → parsed/emis_timeseries.csv

每个Step有独立缓存：若输出文件已存在则跳过，强制重跑用 FORCE=True。

模型：
  P(m) = P₀ · exp(-m/T)       for m < m_c   (thermal equilibrium)
  P(m) = P₀ · (m/m_c)^(-α)    for m >= m_c  (gravitational tail)

Pareto MLE（Hill estimator，Clauset et al. 2009）：
  α = 1 + n · [Σ ln(mᵢ / m_min)]⁻¹

Author: Fei-Yun Wang
Date: 2026-02-21
Version: v1.0
"""

import os
import numpy as np
import pandas as pd
from scipy import stats
from scipy.optimize import curve_fit

# ============================================
# 配置
# ============================================

PROJECT_DIR = './_emis_code/census-1994-2024/'
PARSED_DIR  = os.path.join(PROJECT_DIR, 'parsed')

INPUT_FILE       = os.path.join(PARSED_DIR, 'income_distribution_1994_2024_cpi_adjust.csv')
MC_SCAN_FILE     = os.path.join(PARSED_DIR, 'p4_mc_scan.csv')
EXP_FIT_FILE     = os.path.join(PARSED_DIR, 'p4_exp_fit.csv')
PARETO_FIT_FILE  = os.path.join(PARSED_DIR, 'p4_pareto_fit.csv')
TIMESERIES_FILE  = os.path.join(PARSED_DIR, 'p4_emis_timeseries.csv')

YEARS = range(1994, 2025)
FORCE = False   # True = 忽略缓存，强制重跑所有步骤

# m_c 扫描范围（2024 real dollars）
MC_MIN   = 50_000
MC_MAX   = 350_000
MC_STEP  = 5_000


# ============================================
# 工具函数
# ============================================

def cached(output_file, force=FORCE):
    """装饰器：若输出文件已存在且不强制重跑，跳过该步骤"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            if not force and os.path.exists(output_file):
                print(f"  [缓存] 跳过，已存在: {output_file}")
                return pd.read_csv(output_file)
            result = func(*args, **kwargs)
            result.to_csv(output_file, index=False)
            print(f"  [保存] {output_file}  ({len(result)} 行)")
            return result
        return wrapper
    return decorator


def midpoint(row):
    """取grid格中点作为代表收入值"""
    return (row['lower_bound_real'] + row['upper_bound_real']) / 2


def density(row):
    """count / bin_width = 概率密度（未归一化）"""
    return row['count'] / (row['upper_bound_real'] - row['lower_bound_real'])


# ============================================
# Step 1: 扫描 m_c
# ============================================

def _fit_exp_r2(m_vals, d_vals):
    """
    在给定数据点上拟合 log(d) = a - m/T，返回 R²
    m_vals: 收入中点数组
    d_vals: 密度数组
    """
    if len(m_vals) < 3:
        return 0.0
    try:
        log_d = np.log(d_vals)
        slope, intercept, r, _, _ = stats.linregress(m_vals, log_d)
        if slope >= 0:   # 温度为负，物理上无意义
            return 0.0
        return r ** 2
    except Exception:
        return 0.0


def _fit_pow_r2(m_vals, d_vals):
    """
    在给定数据点上拟合 log(d) = b - α·log(m)，返回 R²
    """
    if len(m_vals) < 3:
        return 0.0
    try:
        log_m = np.log(m_vals)
        log_d = np.log(d_vals)
        slope, intercept, r, _, _ = stats.linregress(log_m, log_d)
        if slope >= 0:   # α 为负，物理上无意义
            return 0.0
        return r ** 2
    except Exception:
        return 0.0


def scan_mc_one_year(df_year):
    """
    对单年数据扫描候选 m_c，返回最优 m_c 及各候选得分
    使用 grid rows（is_tail=False）做扫描
    """
    df_grid = df_year[~df_year['is_tail']].copy()
    df_grid = df_grid.dropna(subset=['upper_bound_real'])
    df_grid['mid']     = df_grid.apply(midpoint, axis=1)
    df_grid['density'] = df_grid.apply(density, axis=1)
    df_grid = df_grid[df_grid['density'] > 0].sort_values('mid')

    candidates = np.arange(MC_MIN, MC_MAX + MC_STEP, MC_STEP)
    best_mc, best_score = MC_MIN, -np.inf
    scores = []

    for mc in candidates:
        exp_data = df_grid[df_grid['mid'] < mc]
        pow_data = df_grid[df_grid['mid'] >= mc]

        r2_exp = _fit_exp_r2(exp_data['mid'].values, exp_data['density'].values)
        r2_pow = _fit_pow_r2(pow_data['mid'].values, pow_data['density'].values)

        # 两段都至少需要3个点
        if len(exp_data) < 3 or len(pow_data) < 3:
            score = 0.0
        else:
            score = r2_exp + r2_pow   # 等权重，可改为加权

        scores.append({'mc_candidate': mc, 'r2_exp': r2_exp, 'r2_pow': r2_pow, 'score': score})

        if score > best_score:
            best_score = score
            best_mc    = mc

    return best_mc, best_score, scores


@cached(MC_SCAN_FILE)
def step1_scan_mc(df):
    """Step 1: 对所有年份扫描 m_c"""
    print("\n[Step 1] 扫描相变点 m_c ...")
    rows = []
    for year in YEARS:
        df_year = df[df['year'] == year]
        if len(df_year) == 0:
            print(f"  {year}: 无数据，跳过")
            continue
        best_mc, best_score, _ = scan_mc_one_year(df_year)
        rows.append({'year': year, 'mc': best_mc, 'mc_score': round(best_score, 4)})
        print(f"  {year}: m_c = ${best_mc:,.0f}  score = {best_score:.4f}")
    return pd.DataFrame(rows)


# ============================================
# Step 2: 拟合指数段，提取温度 T
# ============================================

def fit_exp_one_year(df_year, mc):
    """
    在 m < mc 的 grid rows 上拟合指数段
    log P(m) = log P₀ - m/T  →  slope = -1/T
    返回: T, r2_exp, n_exp_bins
    """
    df_grid = df_year[~df_year['is_tail']].copy()
    df_grid = df_grid.dropna(subset=['upper_bound_real'])
    df_grid['mid']     = df_grid.apply(midpoint, axis=1)
    df_grid['density'] = df_grid.apply(density, axis=1)
    df_exp = df_grid[(df_grid['mid'] < mc) & (df_grid['density'] > 0)].sort_values('mid')

    if len(df_exp) < 3:
        return np.nan, np.nan, 0

    m_vals  = df_exp['mid'].values
    log_d   = np.log(df_exp['density'].values)
    slope, intercept, r, _, stderr = stats.linregress(m_vals, log_d)

    if slope >= 0:
        return np.nan, np.nan, len(df_exp)

    T    = -1.0 / slope
    r2   = r ** 2
    return T, r2, len(df_exp)


@cached(EXP_FIT_FILE)
def step2_fit_exp(df, df_mc):
    """Step 2: 对所有年份拟合指数段"""
    print("\n[Step 2] 拟合指数段（温度 T）...")
    rows = []
    for _, mc_row in df_mc.iterrows():
        year = int(mc_row['year'])
        mc   = mc_row['mc']
        df_year = df[df['year'] == year]
        T, r2_exp, n_bins = fit_exp_one_year(df_year, mc)
        rows.append({'year': year, 'T': round(T, 2) if not np.isnan(T) else np.nan,
                     'r2_exp': round(r2_exp, 4) if not np.isnan(r2_exp) else np.nan,
                     'n_exp_bins': n_bins})
        print(f"  {year}: T = ${T:,.0f}  R²_exp = {r2_exp:.4f}  bins = {n_bins}"
              if not np.isnan(T) else f"  {year}: 拟合失败")
    return pd.DataFrame(rows)


# ============================================
# Step 3: Pareto MLE，提取 α
# ============================================

def pareto_mle_one_year(df_year, mc):
    """
    Hill estimator（Clauset et al. 2009 eq.3）：
      α̂ = 1 + n · [Σ ln(xᵢ / x_min)]⁻¹
      SE  = (α̂ - 1) / √n

    使用 tail rows（is_tail=True）的 count 和 lower_bound_real
    x_min = tail lower_bound_real（已由Phase 3对齐为非tail的max upper_real）

    注意：Census数据每年只有1个tail bin（open-ended），
    不能直接用Hill estimator（需要个体观测值）。
    改用：对数均值估计，基于 x_min 和已知 count 的矩估计。
    
    对于单一open-ended bin，用 grid rows 中 m >= mc 的部分
    + tail bin count，在 log-log 空间做OLS，作为α的近似估计。
    """
    df_grid = df_year[~df_year['is_tail']].copy()
    df_grid = df_grid.dropna(subset=['upper_bound_real'])
    df_grid['mid']     = df_grid.apply(midpoint, axis=1)
    df_grid['density'] = df_grid.apply(density, axis=1)

    df_pow = df_grid[(df_grid['mid'] >= mc) & (df_grid['density'] > 0)].sort_values('mid')

    # tail bin：加入最后一个数据点估计
    df_tail = df_year[df_year['is_tail']].copy()
    total_hh = df_year['count'].sum()

    if len(df_tail) > 0 and total_hh > 0:
        tail_count     = df_tail['count'].values[0]
        tail_lower     = df_tail['lower_bound_real'].values[0]
        tail_fraction  = tail_count / total_hh
    else:
        tail_count    = 0
        tail_lower    = np.nan
        tail_fraction = 0.0

    # 用 grid 幂律段 + tail 做 log-log OLS
    if len(df_pow) < 2:
        return np.nan, np.nan, tail_fraction

    log_m = np.log(df_pow['mid'].values)
    log_d = np.log(df_pow['density'].values)
    slope, intercept, r, _, stderr = stats.linregress(log_m, log_d)

    if slope >= 0:
        return np.nan, np.nan, tail_fraction

    alpha     = -slope          # P(m) ~ m^(-α)，slope = -α
    alpha_se  = abs(stderr)
    r2_pow    = r ** 2

    return alpha, alpha_se, tail_fraction, r2_pow, len(df_pow)


@cached(PARETO_FIT_FILE)
def step3_fit_pareto(df, df_mc):
    """Step 3: 对所有年份拟合幂律段"""
    print("\n[Step 3] 拟合幂律段（Pareto α）...")
    rows = []
    for _, mc_row in df_mc.iterrows():
        year = int(mc_row['year'])
        mc   = mc_row['mc']
        df_year = df[df['year'] == year]
        result = pareto_mle_one_year(df_year, mc)

        if len(result) == 3:   # 拟合失败（只返回3个值）
            alpha, alpha_se, tail_frac = result
            r2_pow, n_pow = np.nan, 0
        else:
            alpha, alpha_se, tail_frac, r2_pow, n_pow = result

        rows.append({
            'year':          year,
            'alpha':         round(alpha, 4)    if not np.isnan(alpha)    else np.nan,
            'alpha_se':      round(alpha_se, 4) if not np.isnan(alpha_se) else np.nan,
            'r2_pow':        round(r2_pow, 4)   if not np.isnan(r2_pow)   else np.nan,
            'tail_fraction': round(tail_frac, 4),
            'n_pow_bins':    n_pow,
        })
        if not np.isnan(alpha):
            print(f"  {year}: α = {alpha:.4f} ± {alpha_se:.4f}  R²_pow = {r2_pow:.4f}  "
                  f"tail = {tail_frac*100:.1f}%  bins = {n_pow}")
        else:
            print(f"  {year}: 拟合失败")
    return pd.DataFrame(rows)


# ============================================
# Step 4: 合并时间序列
# ============================================

@cached(TIMESERIES_FILE)
def step4_merge_timeseries(df_mc, df_exp, df_pareto):
    """Step 4: 合并所有参数为统一时间序列"""
    print("\n[Step 4] 合并时间序列...")
    df = df_mc.merge(df_exp, on='year', how='left') \
              .merge(df_pareto, on='year', how='left')

    # 列顺序
    cols = ['year', 'T', 'alpha', 'alpha_se', 'mc', 'mc_score',
            'r2_exp', 'r2_pow', 'tail_fraction', 'n_exp_bins', 'n_pow_bins']
    df = df[cols]

    print(df.to_string(index=False))
    return df


# ============================================
# 主程序
# ============================================

def main():
    print("=" * 60)
    print("Phase 4: EMIS 2D 批量拟合")
    print("=" * 60)
    print(f"输入: {INPUT_FILE}")
    print(f"强制重跑: {FORCE}")

    if not os.path.exists(INPUT_FILE):
        raise FileNotFoundError(f"找不到输入文件: {INPUT_FILE}")

    df = pd.read_csv(INPUT_FILE)
    print(f"读取完成: {len(df)} 行，{df['year'].nunique()} 年")

    # Step 1
    df_mc = step1_scan_mc(df)

    # Step 2
    df_exp = step2_fit_exp(df, df_mc)

    # Step 3
    df_pareto = step3_fit_pareto(df, df_mc)

    # Step 4
    df_ts = step4_merge_timeseries(df_mc, df_exp, df_pareto)

    print("\n" + "=" * 60)
    print("Phase 4 完成")
    print(f"  mc_scan:       {MC_SCAN_FILE}")
    print(f"  exp_fit:       {EXP_FIT_FILE}")
    print(f"  pareto_fit:    {PARETO_FIT_FILE}")
    print(f"  timeseries:    {TIMESERIES_FILE}")
    print("=" * 60)


if __name__ == '__main__':
    main()