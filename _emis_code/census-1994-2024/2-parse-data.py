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

YEARS = range(1994, 2025)

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
    
    文件格式（宽表格式）：
    - 第7行: 列标题（Total,Total,15 to 24 years,...）
    - 第8行: "Total- hh type All races,Total,98990,..." （总家庭数）
    - 之后每行: "收入区间,家庭数(Total列),家庭数(15-24岁列),..."
    
    我们只需要：
    - 第1列：收入区间字符串
    - 第2列：Total列的家庭数（all ages）
    
    参数：
    - filepath: 文件路径
    - year: 年份
    
    返回：
    - DataFrame with columns: year, income_min, income_max, households
    """
    print(f"    格式: 1994-1997 CSV (宽表)")
    
    try:
        # 读取CSV文件
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
        
        # 找到"Total- hh type All races"行（这是数据的第一行，包含总家庭数）
        data_start = None
        for i, line in enumerate(lines):
            if 'All races' in line and 'hh type' in line:
                data_start = i
                print(f"      定位数据起始行: {i}")
                break
        
        if data_start is None:
            raise ValueError("无法找到'All races'数据起始行")
        
        # 解析数据（从data_start的下一行开始，即收入区间行）
        records = []
        for i in range(data_start + 1, len(lines)):
            line = lines[i].strip()
            
            # 遇到下一个表格标题，停止
            if 'TABLE' in line or not line:
                break
            
            # 跳过统计行
            if any(keyword in line for keyword in ['Median', 'Mean', 'Gini', 'Standard error', 'Income Per']):
                continue
            
            # 解析CSV行
            try:
                parts = list(csv.reader([line]))[0]
            except:
                continue
            
            # 至少需要2列
            if len(parts) < 2:
                continue
            
            # Census格式特殊：第一列可能为空，收入区间可能在第1或第2列
            # 第一行："Under $2,500",1992,... → parts = ['', 'Under $2,500', '1992', ...]
            # 其他行："$2,500 to $4,999",2053,... → parts = ['$2,500 to $4,999', '2053', ...]
            
            # 确定收入区间在哪一列
            if parts[0].strip().strip('"'):
                # 第1列有内容，这是收入区间
                income_str = parts[0].strip().strip('"')
                households_col = 1
            elif len(parts) >= 3 and parts[1].strip().strip('"'):
                # 第1列为空，第2列是收入区间
                income_str = parts[1].strip().strip('"')
                households_col = 2
            else:
                continue
            
            # 跳过非收入区间行（如"B-Cell"等）
            if not income_str or income_str.startswith('B-Cell') or income_str.startswith('A-Cell'):
                continue
            
            # 解析收入区间
            income_min, income_max = parse_income_range(income_str)
            if income_min is None:
                continue
            
            # 第2列或第3列：Total列的家庭数（单位：千户）
            try:
                households_str = parts[households_col].strip().replace(',', '')
                if not households_str or households_str == '':
                    continue
                # Census数据单位是"thousands"，需要乘以1000
                households = int(float(households_str)) * 1000
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
        
        # 验证数据
        if len(df) > 0:
            total_households = df['households'].sum()
            print(f"      总家庭数: {total_households/1e6:.1f}M 户")
        
        return df
        
    except Exception as e:
        print(f"      ❌ 解析失败: {e}")
        import traceback
        traceback.print_exc()
        return None

# ============================================
# 解析器：1998-2006年格式 (TXT)
# ============================================

def parse_1998_2006_txt(filepath, year):
    """
    解析1998-2006年的TXT格式数据
    
    文件格式：
    - 支持 HINC-02, HINC-04, HINC-06, HINC-07 等不同表格
    - 第10-12行附近："ALL RACES"或"All Races"标记
    - 之后第一行是"Total"行，包含总家庭数
    - 每行格式：收入区间 + 数字列（第1个数字是Total）
    
    特殊处理：
    - 文件中间可能有分页标题（包含"HINC-"字样），需要跳过
    - 遇到统计行（MEDIAN/MEAN/GINI）停止（避免解析其他年龄段）
    - 支持1998年（HINC-04）和1999年（HINC-02）等不同格式
    
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
        
        # 找到"ALL RACES"或"All Races"标记行
        data_start = None
        for i, line in enumerate(lines):
            if 'ALL RACES' in line or 'All Races' in line:
                data_start = i + 1  # 下一行是"Total"行
                print(f"      定位数据起始行: {i}")
                break
        
        if data_start is None:
            raise ValueError("无法找到ALL RACES标记")
        
        # 解析数据
        records = []
        first_all_races_block = True  # 标记：只解析第一个ALL RACES块
        
        for i in range(data_start, len(lines)):
            line = lines[i].strip()
            
            # 遇到第二个"ALL RACES"或"All Races"标记，停止（说明进入下一个年龄段）
            if i > data_start and ('ALL RACES' in line or 'All Races' in line or 'Table HINC-06' in line):
                print(f"      遇到第二个All Races块，停止解析")
                break
            
            # 跳过分页标题行（包含"HINC-"字样）
            if 'HINC-04' in line or 'HINC-06' in line or 'HINC-02' in line or 'HINC-07' in line:
                continue
            
            # 跳过分页后的重复标题行
            if 'Race, and Hispanic Origin' in line:
                continue
            if 'Numbers in thousands' in line:
                continue
            if 'Under 65 years' in line or '25 to 34 years' in line:
                continue
            if 'Total      Total      years' in line:
                continue
            
            # 遇到统计行（MEDIAN, MEAN, GINI等），说明数据块结束
            if any(keyword in line for keyword in ['MEDIAN', 'MEAN', 'GINI', 'WGTD-AGG', 'B-CELL', 'A-CELL']):
                print(f"      遇到统计行，停止解析")
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
                # 检查是否是数字（千位逗号格式）
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
            
            # 提取家庭数（第一个数字列，单位：千户）
            try:
                households = int(parts[first_number_idx].replace(',', '')) * 1000
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
        
        # 验证数据
        if len(df) > 0:
            total_households = df['households'].sum()
            print(f"      总家庭数: {total_households/1e6:.1f}M 户")
        
        return df
        
    except Exception as e:
        print(f"      ❌ 解析失败: {e}")
        import traceback
        traceback.print_exc()
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
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
        
        # 找到"Total"行（这是数据的第一行，包含总家庭数）
        data_start = None
        for i, line in enumerate(lines):
            if 'Total' in line:
                data_start = i
                print(f"      定位数据起始行: {i}")
                break
        
        if data_start is None:
            raise ValueError("无法找到'Total'数据起始行")
        
        # 解析数据（从data_start的下一行开始，即收入区间行）
        records = []
        for i in range(data_start + 1, len(lines)):
            line = lines[i].strip()
            
            # 遇到下一个表格标题，停止
            if 'White alone' in line or not line:
                break
            
            # 跳过统计行
            # if any(keyword in line for keyword in ['Median', 'Mean', 'Gini', 'Standard error', 'Income Per']):
            #     continue
            
            # 解析CSV行
            try:
                parts = list(csv.reader([line]))[0]
            except:
                continue
            
            # 至少需要2列
            if len(parts) < 2:
                continue
            
            # Census格式特殊：第一列可能为空，收入区间可能在第1或第2列
            # 第一行："Under $2,500",1992,... → parts = ['', 'Under $2,500', '1992', ...]
            # 其他行："$2,500 to $4,999",2053,... → parts = ['$2,500 to $4,999', '2053', ...]
            
            # 确定收入区间在哪一列
            if parts[0].strip().strip('"'):
                # 第1列有内容，这是收入区间
                income_str = parts[0].strip().strip('"')
                households_col = 1
            elif len(parts) >= 3 and parts[1].strip().strip('"'):
                # 第1列为空，第2列是收入区间
                income_str = parts[1].strip().strip('"')
                households_col = 2
            else:
                continue
            
            # 跳过非收入区间行（如"B-Cell"等）
            if not income_str or income_str.startswith('B-Cell') or income_str.startswith('A-Cell'):
                continue
            
            # 解析收入区间
            income_min, income_max = parse_income_range(income_str)
            if income_min is None:
                continue
            
            # 第2列或第3列：Total列的家庭数（单位：千户）
            try:
                households_str = parts[households_col].strip().replace(',', '')
                if not households_str or households_str == '':
                    continue
                # Census数据单位是"thousands"，需要乘以1000
                households = int(float(households_str)) * 1000
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
        
        # 验证数据
        if len(df) > 0:
            total_households = df['households'].sum()
            print(f"      总家庭数: {total_households/1e6:.1f}M 户")
        
        return df
        
    except Exception as e:
        print(f"      ❌ 解析失败: {e}")
        import traceback
        traceback.print_exc()
        return None


# ============================================
# 解析器：转换后的CSV (2010-2024)
# ============================================

def parse_converted_csv(filepath, year):
    """
    解析转换后的CSV文件（从XML/XLS转换而来）
    
    这些CSV已经是非标准的表格格式，可以直接用txt方式读取
    
    文件格式：
    - 前几行: 标题、说明等
    - 某一行: 列标题，包含"All Races"
    - 之后: 数据行（收入区间 + 家庭数）
    
    参数：
    - filepath: CSV文件路径
    - year: 年份
    
    返回：
    - DataFrame with columns: year, income_min, income_max, households
    """
    print(f"    格式: 转换后的CSV")
    
    try:
        # 读取CSV文件
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
        
        # 找到"Under $5,000"行（这是数据的第一行，包含总家庭数）
        data_start = None
        for i, line in enumerate(lines):
            if 'Under $5,000' in line:
                data_start = i
                print(f"      定位数据起始行: {i}")
                break
        
        if data_start is None:
            raise ValueError("无法找到'Under $5,000'数据起始行")
        
        # 解析数据（从data_start的行开始，即收入区间行）
        records = []
        for i in range(data_start , len(lines)):
            line = lines[i].strip()
            
            # 遇到下一个表格标题，停止
            # if 'White alone' in line or not line:
            #     break
            
            # 跳过统计行
            # if any(keyword in line for keyword in ['Median', 'Mean', 'Gini', 'Standard error', 'Income Per']):
            #     continue
            
            # 解析CSV行
            try:
                parts = list(csv.reader([line]))[0]
            except:
                continue
            
            # 至少需要2列
            if len(parts) < 2:
                continue
            
            # Census格式特殊：第一列可能为空，收入区间可能在第1或第2列
            # 第一行："Under $2,500",1992,... → parts = ['', 'Under $2,500', '1992', ...]
            # 其他行："$2,500 to $4,999",2053,... → parts = ['$2,500 to $4,999', '2053', ...]
            
            # 确定收入区间在哪一列
            if parts[0].strip().strip('"'):
                # 第1列有内容，这是收入区间
                income_str = parts[0].strip().strip('"')
                households_col = 1
            elif len(parts) >= 3 and parts[1].strip().strip('"'):
                # 第1列为空，第2列是收入区间
                income_str = parts[1].strip().strip('"')
                households_col = 2
            else:
                continue
            
            # 跳过非收入区间行（如"B-Cell"等）
            if not income_str or income_str.startswith('B-Cell') or income_str.startswith('A-Cell'):
                continue
            
            # 解析收入区间
            income_min, income_max = parse_income_range(income_str)
            if income_min is None:
                continue
            
            # 第2列或第3列：Total列的家庭数（单位：千户）
            try:
                households_str = parts[households_col].strip().replace(',', '')
                if not households_str or households_str == '':
                    continue
                # Census数据单位是"thousands"，需要乘以1000
                households = int(float(households_str)) * 1000
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
        
       
        # 验证数据
        if len(df) > 0:
            total_households = df['households'].sum()
            print(f"      总家庭数: {total_households/1e6:.1f}M 户")
            
            # 如果总数明显不对（<50M或>200M），可能单位有问题
            if total_households < 50e6:
                print(f"      ⚠️  总数偏小，可能需要调整单位")
            elif total_households > 200e6:
                print(f"      ⚠️  总数偏大，可能重复计算了")
        
        return df
        
    except Exception as e:
        print(f"      ❌ 解析失败: {e}")
        import traceback
        traceback.print_exc()
        return None
        

# ============================================
# 解析器：2010-2024年格式 (Excel/HTML/XML)
# ============================================

"""
2010-2024年数据格式说明：

Census在这个时期使用了多种文件格式，扩展名可能与实际格式不符：
- .xls → 可能是Binary BIFF, HTML, 或XML
- .xlsx → 可能是真XLSX或HTML重定向页面

文件格式检测：
- 前4字节 PK → XLSX (ZIP格式)
- 前4字节 D0CF11E0 → XLS (Binary BIFF)
- 包含<html → HTML
- 包含<?xml → XML

依赖要求：
- XLS (Binary): xlrd
- XLSX: openpyxl
- HTML: html5lib, lxml
- XML: openpyxl或手动转换

如果解析失败，建议：
1. 安装缺失的依赖
2. 手动转换为CSV: libreoffice --convert-to csv <file>
3. 用Excel打开后另存为.xlsx
"""

def parse_2010_2024_excel(filepath, year):
    """
    解析2010-2024年的Excel格式数据

    文件格式约定（HINC-06）：
    - col 0: 收入区间（XLS/BIFF格式可能带前导点号，如 ".Under $5,000"）
    - col 1: All Races → Number（千户单位）
    - 前8~9行：标题/说明行，跳过
    - 含 "Total" 的行（如 "....Total"）：汇总行，跳过
    - 数据行：col 0 以 "Under" 或 "$" 开头（去掉前导点后）
    - 结束标志：遇到 "Footnote" / 空行 / 非收入区间字符串

    支持的实际文件类型（根据文件头自动判断，与扩展名无关）：
    - XLSX (PK 头): engine='openpyxl'
    - XLS BIFF (D0CF11E0 头): engine='xlrd'（需 pip install xlrd）
    - HTML: pandas.read_html
    - XML (Excel 2003): engine='openpyxl'

    参数：
    - filepath: 文件路径
    - year: 年份

    返回：
    - DataFrame with columns: year, income_min, income_max, households
    """
    print(f"    格式: 2010-2024 Excel")

    try:
        # ============================================
        # Step 1: 检测实际文件类型（按文件头，不依赖扩展名）
        # ============================================

        with open(filepath, 'rb') as f:
            raw_header = f.read(512)

        header_str = raw_header.decode(errors='ignore').lower()

        if raw_header.startswith(b'PK'):
            file_type = 'XLSX'
            print(f"      检测到: XLSX (ZIP格式)")
        elif raw_header.startswith(b'\xD0\xCF\x11\xE0'):
            file_type = 'XLS'
            print(f"      检测到: XLS (Binary BIFF)")
        elif '<html' in header_str:
            file_type = 'HTML'
            print(f"      检测到: HTML表格")
        elif '<?xml' in header_str:
            file_type = 'XML'
            print(f"      检测到: XML格式")
        else:
            raise ValueError(f"无法识别的文件格式，前8字节: {raw_header[:8].hex()}")

        # ============================================
        # Step 2: 加载为 DataFrame
        # ============================================

        df_raw = None

        if file_type == 'XLS':
            try:
                df_raw = pd.read_excel(filepath, header=None, engine='xlrd')
                print(f"      xlrd 读取成功")
            except ImportError:
                print(f"      ❌ xlrd 未安装，请执行: pip install xlrd")
                return None
            except Exception as e:
                print(f"      ❌ xlrd 读取失败: {e}")
                return None

        elif file_type == 'XLSX':
            try:
                df_raw = pd.read_excel(filepath, header=None, engine='openpyxl')
            except Exception as e:
                print(f"      ❌ openpyxl 读取失败: {e}")
                return None

        elif file_type == 'HTML':
            if 'window.location.href' in header_str or 'redirectafterdelay' in header_str:
                print(f"      ❌ 这是重定向页面，请重新下载正确文件")
                return None
            try:
                tables = pd.read_html(filepath, header=None)
                if not tables:
                    raise ValueError("未找到表格")
                df_raw = tables[0]
            except ImportError:
                print(f"      ❌ 缺少依赖: pip install html5lib lxml")
                return None
            except Exception as e:
                print(f"      ❌ HTML解析失败: {e}")
                return None

        elif file_type == 'XML':
            try:
                df_raw = pd.read_excel(filepath, header=None, engine='openpyxl')
            except Exception:
                try:
                    df_raw = pd.read_excel(filepath, header=None)
                except Exception as e:
                    print(f"      ❌ XML读取失败: {e}")
                    return None

        if df_raw is None:
            raise ValueError("无法读取文件")

        print(f"      读取成功: {df_raw.shape[0]} 行 × {df_raw.shape[1]} 列")

        # ============================================
        # Step 3: 定位 All Races Number 列
        # 扫描表头行，找 "All Races" 所在列，
        # 再在下一行确认 "Number" 子标题
        # ============================================

        all_races_col = 1  # 默认值（所有已知年份均为 col 1）

        for i in range(min(10, len(df_raw))):
            row_vals = [str(v).strip() for v in df_raw.iloc[i]]
            for j, v in enumerate(row_vals):
                if 'all races' in v.lower() or 'all race' in v.lower():
                    # 在下一行确认 "Number" 标题
                    if i + 1 < len(df_raw):
                        next_row = [str(x).strip().lower() for x in df_raw.iloc[i + 1]]
                        for k in range(j, min(j + 4, len(next_row))):
                            if next_row[k] == 'number':
                                all_races_col = k
                                break
                        else:
                            all_races_col = j  # 没找到 Number，就用 All Races 本列
                    print(f"      All Races Number 列: 第{all_races_col}列")
                    break
            else:
                continue
            break

        # ============================================
        # Step 4: 定位数据起始行
        # 第一个 col0 以 "Under $" 或 "$" 开头的行（去掉前导点后）
        # ============================================

        data_start_row = None
        for i in range(len(df_raw)):
            cell = str(df_raw.iloc[i, 0]).strip().lstrip('.')
            if cell.startswith('Under $') or cell.startswith('$'):
                data_start_row = i
                print(f"      数据起始行: 第{i}行")
                break

        if data_start_row is None:
            raise ValueError("无法找到收入区间数据起始行（没有以 '$' 开头的行）")

        # ============================================
        # Step 5: 逐行解析收入区间和家庭数
        # ============================================

        records = []
        for i in range(data_start_row, len(df_raw)):
            # col 0: 收入区间（去掉 XLS 格式里的前导点号）
            income_str = str(df_raw.iloc[i, 0]).strip().lstrip('.')

            # 终止条件：遇到空值、Footnote、或非收入区间字符串
            if not income_str or income_str.lower() in ('nan', ''):
                break
            if income_str.lower().startswith('footnote'):
                break
            if not (income_str.startswith('Under') or income_str.startswith('$')):
                break

            income_min, income_max = parse_income_range(income_str)
            if income_min is None:
                continue

            # col all_races_col: All Races Number（单位：千户）
            try:
                val = df_raw.iloc[i, all_races_col]
                if pd.isna(val):
                    continue
                val_str = str(val).replace(',', '').strip()
                if not val_str or val_str == '(B)':
                    continue
                households = int(float(val_str)) * 1000  # 千户 → 户
            except (ValueError, IndexError, TypeError):
                continue

            records.append({
                'year': year,
                'income_min': income_min,
                'income_max': income_max,
                'households': households
            })

        df = pd.DataFrame(records)
        print(f"      ✅ 解析成功: {len(df)} 个收入区间")

        if len(df) > 0:
            total_households = df['households'].sum()
            print(f"      总家庭数: {total_households/1e6:.1f}M 户")

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
        # 1998-2006: TXT, 文件名可能是：
        # - {YEAR}-new04_001.txt  (HINC-04)
        # - {YEAR}-new02_001.txt  (HINC-02, 如1999年)
        # - {YEAR}-new06_001.txt  (HINC-06)
        # - {YEAR}-new07_001.txt  (HINC-07)
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
        # 2010-2024: 多种格式
        # 优先尝试转换后的CSV（最简单、最可靠）
        csv_pattern = f'{year}-hinc06_converted.csv'
        csv_path = os.path.join(data_dir, csv_pattern)
        
        if os.path.exists(csv_path):
            print(f"  ✅ 找到转换后的CSV: {csv_pattern}")
            return parse_converted_csv(csv_path, year)
        
        # 否则尝试原始Excel文件
        pattern = f'{year}-hinc06.xlsx'
        filepath = os.path.join(data_dir, pattern)
        if not os.path.exists(filepath):
            # 尝试.xls扩展名
            pattern = f'{year}-hinc06.xls'
            filepath = os.path.join(data_dir, pattern)
        
        if not os.path.exists(filepath):
            print(f"  ❌ 文件不存在: {year}-hinc06.xlsx/.xls")
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