#!/usr/bin/env python3
"""
Phase 2: 解析Census收入数据 (1994-2024)
==========================================

解析HINC-06数据（高收入细分表），提取All Races数据

支持4种历史格式：
  1994-1997: CSV (.csv)      文件名: {YEAR}-4_001.csv
  1998-2006: TXT (.txt)      文件名: {YEAR}-new0{4|2|7|6}_000.txt
  2007-2009: CSV (.csv)      文件名: {YEAR}-new06_000.csv
  2010-2024: Excel (.xlsx)   文件名: {YEAR}-hinc06.xlsx (实际是.xls格式)

Author: Fei-Yun Wang
Date: 2026-02-19
Version: v1.0
"""

import os
import sys
import re
import csv
import glob
import pandas as pd
import numpy as np
from pathlib import Path

# ============================================
# 配置
# ============================================

PROJECT_DIR = './_emis_code/census-1994-2024/'
DATA_DIR = os.path.join(PROJECT_DIR, 'data')
OUTPUT_DIR = os.path.join(PROJECT_DIR, 'parsed')
OUTPUT_FILE = os.path.join(OUTPUT_DIR, 'income_distribution_1994_2024.csv')

YEARS = range(1994, 2024)

# ============================================
# 工具函数：解析收入区间
# ============================================

def parse_income_range(income_str):
    """
    解析收入区间字符串，提取最小值和最大值
    
    示例：
    - "Under $2,500" → (0, 2500)
    - "$2,500 to $4,999" → (2500, 4999)
    - "$100,000 and over" → (100000, None)
    - "$250,000 and above" → (250000, None)
    
    参数：
    - income_str: 收入区间字符串
    
    返回：
    - (min_income, max_income): 元组，max_income为None表示开放区间
    """
    income_str = str(income_str).strip()
    
    # 移除逗号
    income_str = income_str.replace(',', '')
    
    # Under $X
    match = re.match(r'Under\s*\$\s*(\d+)', income_str, re.IGNORECASE)
    if match:
        return (0, int(match.group(1)))
    
    # $X to $Y
    match = re.match(r'\$\s*(\d+)\s+to\s+\$\s*(\d+)', income_str, re.IGNORECASE)
    if match:
        return (int(match.group(1)), int(match.group(2)))
    
    # $X and over/above
    match = re.match(r'\$\s*(\d+)\s+and\s+(over|above)', income_str, re.IGNORECASE)
    if match:
        return (int(match.group(1)), None)
    
    # 无法解析
    return (None, None)


# ============================================
# 解析器：1994-1997年格式 (CSV)
# ============================================

def parse_1994_1997_csv(filepath, year):
    """
    解析1994-1997年的CSV格式数据
    
    文件格式：
    - 第8行开始数据
    - 第一列标记："Total- hh type All races"
    - 第二列"Total"是我们需要的总数
    
    参数：
    - filepath: 文件路径
    - year: 年份
    
    返回：
    - DataFrame with columns: year, income_min, income_max, households
    """
    print(f"    格式: 1994-1997 CSV")
    
    try:
        # 读取CSV文件
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
        
        # 找到"Total- hh type All races"行（通常在第8行附近）
        data_start = None
        for i, line in enumerate(lines):
            if 'All races' in line and 'Total' in line:
                data_start = i
                break
        
        if data_start is None:
            raise ValueError("无法找到数据起始行")
        
        # 解析数据
        records = []
        for i in range(data_start + 1, len(lines)):
            line = lines[i].strip()
            
            # 跳过空行或统计行
            if not line or 'Median' in line or 'Mean' in line or 'Gini' in line:
                continue
            
            # 解析CSV行
            parts = list(csv.reader([line]))[0]
            if len(parts) < 2:
                continue
            
            income_str = parts[0].strip().strip('"')
            
            # 解析收入区间
            income_min, income_max = parse_income_range(income_str)
            if income_min is None:
                continue
            
            # 提取家庭数（第二列"Total"）
            try:
                households = int(parts[1].replace(',', ''))
            except (ValueError, IndexError):
                continue
            
            records.append({
                'year': year,
                'income_min': income_min,
                'income_max': income_max,
                'households': households
            })
        
        df = pd.DataFrame(records)
        print(f"      ✅ 解析成功: {len(df)} 个收入区间")
        return df
        
    except Exception as e:
        print(f"      ❌ 解析失败: {e}")
        return None


# ============================================
# 解析器：1998-2006年格式 (TXT)
# ============================================

def parse_1998_2006_txt(filepath, year):
    """
    解析1998-2006年的TXT格式数据
    
    文件格式：
    - 第12行附近："ALL RACES"标记
    - 第12行的"Total"后第一个数字是总家庭数
    - 之后每行第一列是收入区间，第二列是总数
    
    参数：
    - filepath: 文件路径
    - year: 年份
    
    返回：
    - DataFrame with columns: year, income_min, income_max, households
    """
    print(f"    格式: 1998-2006 TXT")
    
    try:
        # 读取TXT文件
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
        
        # 找到"ALL RACES"标记行
        data_start = None
        for i, line in enumerate(lines):
            if 'ALL RACES' in line:
                data_start = i + 1  # 下一行是"Total"行
                break
        
        if data_start is None:
            raise ValueError("无法找到ALL RACES标记")
        
        # 解析数据
        records = []
        for i in range(data_start, len(lines)):
            line = lines[i].strip()
            
            # 遇到新的分组标题，停止
            if 'WHITE' in line or 'BLACK' in line or 'HISPANIC' in line:
                break
            
            # 跳过空行或统计行
            if not line or 'Median' in line or 'Mean' in line:
                continue
            
            # 跳过"Total"行（第一行数据）
            if line.startswith('Total'):
                continue
            
            # 解析数据行（用正则表达式处理空格分隔）
            # 格式：收入区间 + 一堆数字
            parts = line.split()
            if len(parts) < 2:
                continue
            
            # 找到收入区间部分（可能包含多个单词）
            income_str_parts = []
            first_number_idx = None
            for j, part in enumerate(parts):
                # 检查是否是数字
                if re.match(r'^\d{1,3}(,\d{3})*$', part):
                    first_number_idx = j
                    break
                income_str_parts.append(part)
            
            if first_number_idx is None or not income_str_parts:
                continue
            
            income_str = ' '.join(income_str_parts)
            
            # 解析收入区间
            income_min, income_max = parse_income_range(income_str)
            if income_min is None:
                continue
            
            # 提取家庭数（第一个数字列）
            try:
                households = int(parts[first_number_idx].replace(',', ''))
            except (ValueError, IndexError):
                continue
            
            records.append({
                'year': year,
                'income_min': income_min,
                'income_max': income_max,
                'households': households
            })
        
        df = pd.DataFrame(records)
        print(f"      ✅ 解析成功: {len(df)} 个收入区间")
        return df
        
    except Exception as e:
        print(f"      ❌ 解析失败: {e}")
        return None


# ============================================
# 解析器：2007-2009年格式 (CSV)
# ============================================

def parse_2007_2009_csv(filepath, year):
    """
    解析2007-2009年的CSV格式数据
    
    文件格式：
    - 第6行: 列标题，包含"All Races"
    - 第9行: "Total"行，第一个数字是总家庭数
    - 之后每行第一列是收入区间，第二列("All Races"下的"Number")是总数
    
    参数：
    - filepath: 文件路径
    - year: 年份
    
    返回：
    - DataFrame with columns: year, income_min, income_max, households
    """
    print(f"    格式: 2007-2009 CSV")
    
    try:
        # 读取CSV文件
        df_raw = pd.read_csv(filepath, header=None, skiprows=5, nrows=100)
        
        # 第一行应该是标题行（All Races, White, etc.）
        # 第二行应该是子标题（Number, Mean Income, etc.）
        # 跳过这两行，从第三行开始是数据
        
        # 找到"Total"行（通常是第一行数据）
        total_row_idx = None
        for i, row in df_raw.iterrows():
            if str(row[0]).strip().lower() == 'total':
                total_row_idx = i
                break
        
        if total_row_idx is None:
            raise ValueError("无法找到Total行")
        
        # 解析数据（从Total行的下一行开始）
        records = []
        for i in range(total_row_idx + 1, len(df_raw)):
            row = df_raw.iloc[i]
            
            # 第一列是收入区间
            income_str = str(row[0]).strip().strip('"')
            
            # 解析收入区间
            income_min, income_max = parse_income_range(income_str)
            if income_min is None:
                continue
            
            # 第二列("All Races" → "Number")是家庭数
            try:
                households_str = str(row[1]).replace(',', '').strip()
                if not households_str or households_str == 'nan':
                    continue
                households = int(float(households_str))
            except (ValueError, IndexError):
                continue
            
            records.append({
                'year': year,
                'income_min': income_min,
                'income_max': income_max,
                'households': households
            })
        
        df = pd.DataFrame(records)
        print(f"      ✅ 解析成功: {len(df)} 个收入区间")
        return df
        
    except Exception as e:
        print(f"      ❌ 解析失败: {e}")
        return None


# ============================================
# 解析器：2010-2024年格式 (XLSX/XLS)
# ============================================

def parse_2010_2024_excel(filepath, year):
    """
    解析2010-2024年的Excel格式数据
    
    文件格式（类似2019年之前用的格式）：
    - 使用pd.read_excel读取
    - 需要找到"All races"列
    - 收入区间在某一列，家庭数在对应列
    
    参数：
    - filepath: 文件路径
    - year: 年份
    
    返回：
    - DataFrame with columns: year, income_min, income_max, households
    """
    print(f"    格式: 2010-2024 Excel")
    
    try:
        # 读取Excel文件（可能是.xls或.xlsx）
        # 尝试使用不同的引擎
        df_raw = None
        for engine in ['openpyxl', 'xlrd', None]:
            try:
                if engine:
                    df_raw = pd.read_excel(filepath, header=None, engine=engine)
                else:
                    df_raw = pd.read_excel(filepath, header=None)
                break
            except:
                continue
        
        if df_raw is None:
            raise ValueError("无法读取Excel文件")
        
        # 查找"All races"列和数据起始行
        all_races_col = None
        data_start_row = None
        
        for i, row in df_raw.iterrows():
            for j, cell in enumerate(row):
                cell_str = str(cell).strip().lower()
                if 'all races' in cell_str or 'all race' in cell_str:
                    # 找到"All races"列
                    # 通常在这一行或下一行会有"Number"子标题
                    # 再下一行是"Total"
                    all_races_col = j
                    
                    # 向下查找"Total"行
                    for k in range(i+1, min(i+10, len(df_raw))):
                        if str(df_raw.iloc[k, 0]).strip().lower() == 'total':
                            data_start_row = k
                            break
                    break
            if all_races_col is not None:
                break
        
        if all_races_col is None or data_start_row is None:
            raise ValueError(f"无法定位All races列或数据起始行 (all_races_col={all_races_col}, data_start_row={data_start_row})")
        
        print(f"      定位: All races列={all_races_col}, 数据起始行={data_start_row}")
        
        # 解析数据（从Total行的下一行开始）
        records = []
        for i in range(data_start_row + 1, len(df_raw)):
            row = df_raw.iloc[i]
            
            # 第一列（或income列）是收入区间
            income_str = str(row[0]).strip()
            if not income_str or income_str == 'nan':
                continue
            
            # 解析收入区间
            income_min, income_max = parse_income_range(income_str)
            if income_min is None:
                continue
            
            # All races列是家庭数
            try:
                households_val = row[all_races_col]
                if pd.isna(households_val):
                    continue
                households_str = str(households_val).replace(',', '').strip()
                households = int(float(households_str))
            except (ValueError, IndexError):
                continue
            
            records.append({
                'year': year,
                'income_min': income_min,
                'income_max': income_max,
                'households': households
            })
        
        df = pd.DataFrame(records)
        print(f"      ✅ 解析成功: {len(df)} 个收入区间")
        return df
        
    except Exception as e:
        print(f"      ❌ 解析失败: {e}")
        import traceback
        traceback.print_exc()
        return None


# ============================================
# 主解析函数：智能识别格式
# ============================================

def parse_year_data(year, data_dir):
    """
    解析指定年份的数据（自动识别格式）
    
    参数：
    - year: 年份
    - data_dir: 数据目录
    
    返回：
    - DataFrame 或 None
    """
    print(f"\n{'='*80}")
    print(f"解析 {year} 年数据")
    print(f"{'='*80}")
    
    # 根据年份确定文件名模式
    if 1994 <= year <= 1997:
        # 1994-1997: CSV, {YEAR}-4_001.csv
        pattern = f'{year}-4_001.csv'
        filepath = os.path.join(data_dir, pattern)
        if not os.path.exists(filepath):
            print(f"  ❌ 文件不存在: {pattern}")
            return None
        return parse_1994_1997_csv(filepath, year)
        
    elif 1998 <= year <= 2006:
        # 1998-2006: TXT, {YEAR}-new0{4|2|7|6}_001.txt
        patterns = [
            f'{year}-new04_000.txt',
            f'{year}-new02_000.txt',
            f'{year}-new07_000.txt',
            f'{year}-new06_000.txt',
        ]
        filepath = None
        for pattern in patterns:
            test_path = os.path.join(data_dir, pattern)
            if os.path.exists(test_path):
                filepath = test_path
                break
        
        if filepath is None:
            print(f"  ❌ 文件不存在（尝试了: {patterns}）")
            return None
        return parse_1998_2006_txt(filepath, year)
        
    elif 2007 <= year <= 2009:
        # 2007-2009: CSV, {YEAR}-new06_000.csv
        pattern = f'{year}-new06_000.csv'
        filepath = os.path.join(data_dir, pattern)
        if not os.path.exists(filepath):
            # 尝试备用模式
            pattern = f'{year}-new06_001.csv'
            filepath = os.path.join(data_dir, pattern)
        
        if not os.path.exists(filepath):
            print(f"  ❌ 文件不存在: {pattern}")
            return None
        return parse_2007_2009_csv(filepath, year)
        
    elif 2010 <= year <= 2024:
        # 2010-2024: XLSX, {YEAR}-hinc06.xlsx
        pattern = f'{year}-hinc06.xlsx'
        filepath = os.path.join(data_dir, pattern)
        if not os.path.exists(filepath):
            print(f"  ❌ 文件不存在: {pattern}")
            return None
        return parse_2010_2024_excel(filepath, year)
    
    else:
        print(f"  ❌ 不支持的年份: {year}")
        return None


# ============================================
# 批量解析所有年份
# ============================================

def parse_all_years(data_dir, output_file):
    """
    批量解析1994-2024所有年份的数据
    
    参数：
    - data_dir: 数据目录
    - output_file: 输出CSV文件路径
    
    返回：
    - 成功解析的年份列表
    """
    print("="*80)
    print("Census HINC-06数据批量解析")
    print("="*80)
    print(f"数据目录: {data_dir}")
    print(f"输出文件: {output_file}")
    print(f"年份范围: {YEARS[0]} - {YEARS[-1]}")
    
    # 创建输出目录
    Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)
    
    # 批量解析
    all_data = []
    success_years = []
    
    for year in YEARS:
        df = parse_year_data(year, data_dir)
        
        if df is not None and len(df) > 0:
            all_data.append(df)
            success_years.append(year)
        else:
            print(f"  ⚠️  {year} 年解析失败或无数据")
    
    # 合并所有数据
    if all_data:
        df_combined = pd.concat(all_data, ignore_index=True)
        
        # 排序
        df_combined = df_combined.sort_values(['year', 'income_min'])
        
        # 保存
        df_combined.to_csv(output_file, index=False)
        
        print("\n" + "="*80)
        print("解析完成")
        print("="*80)
        print(f"成功解析: {len(success_years)}/{len(YEARS)} 年")
        print(f"总记录数: {len(df_combined)}")
        print(f"输出文件: {output_file}")
        print(f"\n成功年份: {success_years}")
        
        # 显示数据样本
        print("\n数据样本（前10行）:")
        print(df_combined.head(10))
        
        print("\n数据样本（后10行）:")
        print(df_combined.tail(10))
        
    else:
        print("\n❌ 没有成功解析任何年份的数据")
    
    return success_years


# ============================================
# 主程序
# ============================================

def main():
    """主程序"""
    
    # 检查数据目录
    if not os.path.exists(DATA_DIR):
        print(f"❌ 数据目录不存在: {DATA_DIR}")
        print(f"请先运行 Phase 1 (1-download-census-data.py) 下载数据")
        return
    
    # 批量解析
    success_years = parse_all_years(DATA_DIR, OUTPUT_FILE)
    
    if success_years:
        print(f"\n✅ Phase 2 完成！")
        print(f"下一步: 运行 Phase 3 (3-time-series-analysis.py) 进行时间序列分析")


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️ 用户中断")
    except Exception as e:
        print(f"\n\n❌ 程序错误: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "="*80)