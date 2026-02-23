#!/usr/bin/env python3
"""
Phase 3: CPI调整 + 统一Real 5000 Binning + 计算Tail Threshold
==============================================================

功能：
1. 读取CPIAUCSL月度数据，计算年度平均CPI
2. 将1994-2024收入数据转换为2024 constant dollars
3. 正确处理开放上限bin（upper = NaN → 标记为 tail，不参与 grid 映射）
4. 统一映射为5000美元Real bin（仅有上限的bin参与）
5. 计算2024年P90（线性插值，仅用grid rows）
6. 输出标准化数据文件（grid rows + tail rows 合并）

Author: Fei-Yun Wang
Date: 2026-02-20
Version: v1.4

变更说明 (v1.0 → v1.1)
-----------------------
[改动 A] adjust_income_to_real()
    原：open-ended bin 的 upper_real 设为 np.inf
    新：upper_real 保持 NaN，新增布尔列 is_tail=True 标记
    原因：不人为设置上限，保持原始语义，供 Phase 4 Pareto MLE 直接使用

[改动 B] remap_bins() — 跳过 tail
    原：对 upper_real=inf 的行做特殊分支（lower_old < upper_new 则整体计入）
    新：is_tail=True 的行直接跳过，不参与比例分配
    原因：开放区间无法做有意义的按比例分配

[改动 C] remap_bins() — 保留 tail rows
    原：仅返回 grid rows
    新：返回 grid rows + tail rows 合并（tail rows 含 is_tail=True 列）
    原因：tail 数据需传递到 Phase 4 做 Pareto MLE

[改动 D] compute_p90() — 排除 tail
    原：全量数据计算累积（含 inf upper，可能出错）
    新：只在 is_tail=False 的 grid rows 上计算 P90
    原因：tail bin 宽度未知，不能做线性插值

变更说明 (v1.1 → v1.2)
-----------------------
[改动 E] remap_bins() — 修复 tail lower_bound 与 grid 之间的空洞
    原：tail lower_bound_real = row['lower_real'] = income_min × factor
        （如 100000 × 2.116365 = 211636.50）
        非tail上界 = income_max × factor = 99999 × 2.116365 = 211634.38
        两者之间有 2.12 real dollars 空洞，既不在grid也不在tail
    新：tail lower_bound_real = max(df_grid['upper_real']) = 211634.38
        tail严格从非tail实际上界开始，空洞消除
    原因：Census原始数据 income_max=99999 与 income_min=100000 之间有1美元名义间隙，
          real化后产生2.12美元空洞；用非tail上界对齐可消除此间隙

变更说明 (v1.2 → v1.3)
-----------------------
[改动 F] compute_annual_cpi() — 新增年化CPI输出文件
    原：仅返回 {year: cpi} 字典，不落盘
    新：额外输出 data/cpi_yearly.csv，含三列：
        year, cpi, inflation_factor（= CPI_2024 / CPI_year）

变更说明 (v1.3 → v1.4)
-----------------------
[改动 G] remap_bins() — 最后一个grid格的上界截断为非tail实际上界
    原：最后一个grid格 upper_bound_real = upper_new（5000整数上界，如215000）
        但数据实际只覆盖到 grid_upper_max（如211634.38），导致bin宽度虚大
    新：year_grid_rows收集完后，将最后一格的 upper_bound_real 截断为 grid_upper_max
    结果：
        原 1994,210000.0,215000.0,124845.3,False
        新 1994,210000.0,211634.4,124845.3,False
        tail 1994,211634.4,,6581000.0,True  ← 严格衔接
    原因：bin宽度影响Phase 4的density计算（density = count / bin_width），
          虚假上界会低估最后一格的密度，扭曲指数段拟合
"""

import os
import pandas as pd
import numpy as np

# ============================================
# 配置
# ============================================

PROJECT_DIR = './_emis_code/census-1994-2024/'
DATA_DIR = os.path.join(PROJECT_DIR, 'data')
PARSED_DIR = os.path.join(PROJECT_DIR, 'parsed') 

CPI_FILE = os.path.join(DATA_DIR, 'CPIAUCSL.csv')
INPUT_FILE = os.path.join(PARSED_DIR, 'income_distribution_1994_2024_final.csv')
OUTPUT_FILE = os.path.join(PARSED_DIR, 'income_distribution_1994_2024_cpi_adjust.csv')

YEARS = range(1994, 2025)
REAL_BIN_WIDTH = 5000


# ============================================
# 1. 计算年度CPI（未改动）
# ============================================

def compute_annual_cpi(cpi_file):
    """
    读取月度CPI数据，计算年度平均CPI，并输出到 data/cpi_yearly.csv

    参数:
        cpi_file: CPIAUCSL.csv路径

    返回:
        annual_cpi: {year: cpi_value}

    [改动 F] 新增：将年化CPI保存到 data/cpi_yearly.csv
        列：year, cpi, inflation_factor（相对2024年）
    """
    df = pd.read_csv(cpi_file)
    df['observation_date'] = pd.to_datetime(df['observation_date'])
    df['year'] = df['observation_date'].dt.year

    annual = df.groupby('year')['CPIAUCSL'].mean()
    annual_dict = annual.to_dict()

    # [改动 F] 输出年化CPI及调整系数到文件
    cpi_2024 = annual_dict[2024]
    df_out = pd.DataFrame({
        'year': annual.index,
        'cpi': annual.values,
        'inflation_factor': cpi_2024 / annual.values   # 各年相对2024年的调整系数
    })
    out_path = os.path.join(DATA_DIR, 'cpi_yearly.csv')
    df_out.to_csv(out_path, index=False, float_format='%.6f')
    print(f"  年化CPI已保存: {out_path} （{len(df_out)} 行）")

    return annual_dict


# ============================================
# 2. 将nominal收入转为2024 real美元
# ============================================

def adjust_income_to_real(df, annual_cpi):
    """
    将nominal收入转换为2024 constant dollars

    Real = Nominal * (CPI_2024 / CPI_year)

    [改动 A]
    原：open-ended bin upper_real = np.inf
    新：upper_real 保持 NaN，新增 is_tail=True 列
    """
    cpi_2024 = annual_cpi[2024]

    df = df.copy()

    df['inflation_factor'] = df['year'].apply(
        lambda y: cpi_2024 / annual_cpi[y]
    )

    df['lower_real'] = df['income_min'] * df['inflation_factor']

    # [改动 A] open-ended bin 保持 NaN，不设 inf
    df['upper_real'] = df.apply(
        lambda row:
            row['income_max'] * row['inflation_factor']
            if not pd.isna(row['income_max'])
            else np.nan,
        axis=1
    )

    # [改动 A] 新增 is_tail 标记
    df['is_tail'] = df['upper_real'].isna()

    return df


# ============================================
# 3. 构建统一real 5000网格（未改动）
# ============================================

def create_real_bins(max_income=500000):
    """
    创建统一的real income grid

    返回:
        bins: [(lower, upper), ...]
    """
    bins = []
    current = 0

    while current < max_income:
        bins.append((current, current + REAL_BIN_WIDTH))
        current += REAL_BIN_WIDTH

    return bins


# ============================================
# 4. 将原始real bin映射到统一5000网格
# ============================================

def remap_bins(df, real_bins):
    """
    将real收入区间按比例分配到统一5000网格。
    is_tail=True 的 bin 不参与 grid 映射，直接保留到输出。

    [改动 B] 跳过 is_tail=True，不参与比例分配
    [改动 C] 返回 grid rows + tail rows 合并结果
    [改动 E] tail lower_bound_real 用非tail bins的 max(upper_real)，消除名义1美元空洞

    说明（以1994年为例）：
    - 非tail最后一行 income_max=99999，upper_real = 99999 × 2.116365 = 211634.38
    - tail行 income_min=100000，    lower_real = 100000 × 2.116365 = 211636.50
    - 两者之间有 2.12 real dollars 空洞（Census原始定义间隙），既不在grid也不在tail
    - 修复：tail lower_bound_real 改用 max(upper_real)=211634.38，严格与grid衔接
    """
    grid_rows = []
    tail_rows = []

    for year in YEARS:
        df_year = df[df['year'] == year]

        # [改动 B][改动 E] 先算非tail上界，再收集tail
        df_grid = df_year[~df_year['is_tail']]

        # [改动 E] 非tail bins的实际最大上界，作为tail的起点
        grid_upper_max = df_grid['upper_real'].max() if len(df_grid) > 0 else np.nan

        # [改动 C] 收集 tail rows
        for _, row in df_year[df_year['is_tail']].iterrows():
            tail_rows.append({
                'year': year,
                'lower_bound_real': grid_upper_max,  # [改动 E] 原为 row['lower_real']，有2.12元空洞
                'upper_bound_real': np.nan,
                'count': row['households'],
                'is_tail': True
            })

        year_grid_rows = []
        for lower_new, upper_new in real_bins:
            total_count = 0.0

            for _, row in df_grid.iterrows():
                lower_old = row['lower_real']
                upper_old = row['upper_real']    # 必定是有限值
                count = row['households']

                overlap_lower = max(lower_old, lower_new)
                overlap_upper = min(upper_old, upper_new)
                overlap = max(0, overlap_upper - overlap_lower)
                old_width = upper_old - lower_old

                if old_width > 0 and overlap > 0:
                    proportion = overlap / old_width
                    total_count += count * proportion

            if total_count > 0:
                year_grid_rows.append({
                    'year': year,
                    'lower_bound_real': lower_new,
                    'upper_bound_real': upper_new,
                    'count': total_count,
                    'is_tail': False
                })

        # [改动 G] 最后一个grid格的上界截断为非tail数据的实际上界
        # 避免虚假上界（如215000）导致bin宽度虚大，影响Phase 4的density计算
        if year_grid_rows and not np.isnan(grid_upper_max):
            year_grid_rows[-1]['upper_bound_real'] = grid_upper_max

        grid_rows.extend(year_grid_rows)

    # [改动 C] 合并 grid + tail，按年份和下界排序
    df_result = pd.concat(
        [pd.DataFrame(grid_rows), pd.DataFrame(tail_rows)],
        ignore_index=True
    )
    df_result = df_result.sort_values(['year', 'lower_bound_real']).reset_index(drop=True)

    return df_result


# ============================================
# 5. 计算P90（线性插值）
# ============================================

def compute_p90(df):
    """
    基于2024年real分布计算P90（线性插值）

    [改动 D]
    原：全量数据（含 inf upper_bound_real）计算累积，可能出错
    新：只在 is_tail=False 的 grid rows 上计算，tail 不参与
    """
    # [改动 D] 只用 grid rows
    df_2024 = df[(df['year'] == 2024) & (~df['is_tail'])].copy()
    df_2024 = df_2024.sort_values('lower_bound_real')

    total = df_2024['count'].sum()
    cumulative = df_2024['count'].cumsum()

    threshold = 0.9 * total

    row_index = cumulative.searchsorted(threshold)
    row = df_2024.iloc[row_index]

    prev_cum = cumulative.iloc[row_index - 1] if row_index > 0 else 0
    bin_count = row['count']
    fraction = (threshold - prev_cum) / bin_count

    lower = row['lower_bound_real']
    upper = row['upper_bound_real']
    p90_value = lower + fraction * (upper - lower)

    return p90_value


# ============================================
# 主程序（结构未改动）
# ============================================

def main():
    print("Phase 3 开始执行...")

    print("读取CPI数据...")
    annual_cpi = compute_annual_cpi(CPI_FILE)

    print("读取收入数据...")
    df = pd.read_csv(INPUT_FILE)

    required_cols = ['year', 'income_min', 'income_max', 'households']
    for col in required_cols:
        if col not in df.columns:
            raise ValueError(f"缺少必要字段: {col}")

    print("执行CPI调整...")
    df_real = adjust_income_to_real(df, annual_cpi)
    print(f"  grid行数: {(~df_real['is_tail']).sum()}，tail行数: {df_real['is_tail'].sum()}")

    print("创建统一5000美元real网格...")
    real_bins = create_real_bins()

    print("执行bin重映射...")
    df_remap = remap_bins(df_real, real_bins)
    print(f"  输出 grid rows: {(~df_remap['is_tail']).sum()}，tail rows: {df_remap['is_tail'].sum()}")

    print("计算2024年P90...")
    p90 = compute_p90(df_remap)
    print(f"2024年 Real P90 = ${p90:,.0f}")

    df_remap.to_csv(OUTPUT_FILE, index=False)

    print("Phase 3 完成")
    print(f"输出文件: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()