#!/usr/bin/env python3
"""
Census文件转换工具（无需LibreOffice）
======================================

使用纯Python库转换Census Excel文件为CSV

支持格式：
- XLS (Binary BIFF) → 需要xlrd
- Excel 2003 XML → 手动解析XML
- HTML表格 → 使用BeautifulSoup

Author: Fei-Yun Wang
Date: 2026-02-19
"""

import os
import sys
import csv
import xml.etree.ElementTree as ET
from pathlib import Path

PROJECT_DIR = './_emis_code/census-1994-2024'
DATA_DIR = os.path.join(PROJECT_DIR, 'data')

# ============================================
# 方案1: 转换Excel 2003 XML格式
# ============================================

def convert_excel_2003_xml_to_csv(xml_file, csv_file):
    """
    转换Excel 2003 XML格式到CSV
    
    这种格式是纯文本XML，不需要额外库
    """
    print(f"转换 Excel 2003 XML: {xml_file}")
    
    try:
        # 解析XML
        tree = ET.parse(xml_file)
        root = tree.getroot()
        
        # XML命名空间
        ns = {
            'ss': 'urn:schemas-microsoft-com:office:spreadsheet',
            'o': 'urn:schemas-microsoft-com:office:office',
            'x': 'urn:schemas-microsoft-com:office:excel',
            'html': 'http://www.w3.org/TR/REC-html40'
        }
        
        # 找到第一个Worksheet
        worksheet = root.find('.//ss:Worksheet', ns)
        if worksheet is None:
            raise ValueError("未找到Worksheet")
        
        # 找到Table
        table = worksheet.find('.//ss:Table', ns)
        if table is None:
            raise ValueError("未找到Table")
        
        # 提取所有行
        rows = []
        for row_elem in table.findall('.//ss:Row', ns):
            row_data = []
            for cell_elem in row_elem.findall('.//ss:Cell', ns):
                data_elem = cell_elem.find('.//ss:Data', ns)
                if data_elem is not None:
                    cell_value = data_elem.text or ''
                else:
                    cell_value = ''
                row_data.append(cell_value)
            rows.append(row_data)
        
        # 写入CSV
        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            for row in rows:
                writer.writerow(row)
        
        print(f"  ✅ 成功转换: {len(rows)} 行")
        print(f"  输出: {csv_file}")
        return True
        
    except Exception as e:
        print(f"  ❌ 转换失败: {e}")
        return False


# ============================================
# 方案2: 转换XLS (Binary) - 需要xlrd
# ============================================

def convert_xls_to_csv(xls_file, csv_file):
    """
    转换XLS (Binary BIFF)格式到CSV
    
    需要xlrd库
    """
    print(f"转换 XLS (Binary): {xls_file}")
    
    try:
        import xlrd
    except ImportError:
        print(f"  ❌ xlrd未安装")
        print(f"  安装命令: pip install xlrd")
        return False
    
    try:
        # 读取XLS
        workbook = xlrd.open_workbook(xls_file)
        sheet = workbook.sheet_by_index(0)
        
        # 写入CSV
        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            for row_idx in range(sheet.nrows):
                row_data = []
                for col_idx in range(sheet.ncols):
                    cell = sheet.cell(row_idx, col_idx)
                    row_data.append(str(cell.value))
                writer.writerow(row_data)
        
        print(f"  ✅ 成功转换: {sheet.nrows} 行 × {sheet.ncols} 列")
        print(f"  输出: {csv_file}")
        return True
        
    except Exception as e:
        print(f"  ❌ 转换失败: {e}")
        return False


# ============================================
# 方案3: 转换HTML表格 - 需要BeautifulSoup
# ============================================

def convert_html_to_csv(html_file, csv_file):
    """
    转换HTML表格到CSV
    
    需要BeautifulSoup
    """
    print(f"转换 HTML: {html_file}")
    
    try:
        from bs4 import BeautifulSoup
    except ImportError:
        print(f"  ❌ BeautifulSoup未安装")
        print(f"  安装命令: pip install beautifulsoup4")
        return False
    
    try:
        # 读取HTML
        with open(html_file, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        # 检查是否是重定向页面
        if 'window.location.href' in content.lower():
            print(f"  ❌ 这是重定向页面，不包含数据")
            print(f"  建议: 从Census网站重新下载")
            return False
        
        soup = BeautifulSoup(content, 'html.parser')
        
        # 找表格
        tables = soup.find_all('table')
        if not tables:
            raise ValueError("未找到表格")
        
        table = tables[0]
        
        # 提取数据
        rows = []
        for tr in table.find_all('tr'):
            row_data = []
            for td in tr.find_all(['td', 'th']):
                row_data.append(td.get_text().strip())
            rows.append(row_data)
        
        # 写入CSV
        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            for row in rows:
                writer.writerow(row)
        
        print(f"  ✅ 成功转换: {len(rows)} 行")
        print(f"  输出: {csv_file}")
        return True
        
    except Exception as e:
        print(f"  ❌ 转换失败: {e}")
        return False


# ============================================
# 智能转换（自动检测格式）
# ============================================

def smart_convert(input_file, output_file=None):
    """
    智能转换：自动检测文件格式并选择转换方法
    """
    
    if not os.path.exists(input_file):
        print(f"❌ 文件不存在: {input_file}")
        return False
    
    # 生成输出文件名
    if output_file is None:
        base = os.path.splitext(input_file)[0]
        output_file = f"{base}_converted.csv"
    
    # 检测文件类型
    with open(input_file, 'rb') as f:
        header = f.read(8192)
    
    header_str = header.decode(errors='ignore').lower()
    
    # 根据格式选择转换方法
    if header.startswith(b'\xD0\xCF\x11\xE0'):
        # XLS (Binary)
        return convert_xls_to_csv(input_file, output_file)
    
    elif '<?xml' in header_str and 'excel' in header_str:
        # Excel 2003 XML
        return convert_excel_2003_xml_to_csv(input_file, output_file)
    
    elif '<html' in header_str:
        # HTML
        return convert_html_to_csv(input_file, output_file)
    
    elif header.startswith(b'PK'):
        # XLSX (已经是现代格式，可以直接用pandas读取)
        print(f"  ℹ️  XLSX格式可直接用pandas读取，无需转换")
        return True
    
    else:
        print(f"  ❌ 未知格式")
        return False


# ============================================
# 批量转换目录中的文件
# ============================================

def batch_convert(directory, start_year=2010, end_year=2024):
    """
    批量转换2010-2024年的Census文件
    """
    
    print("="*80)
    print("Census文件批量转换工具")
    print("="*80)
    print(f"目录: {directory}\n")
    
    if not os.path.exists(directory):
        print(f"❌ 目录不存在: {directory}")
        return
    
    success_count = 0
    fail_count = 0
    skip_count = 0
    
    for year in range(start_year, end_year + 1):
        # 尝试找文件
        found = False
        for ext in ['xls', 'xlsx', 'xml', 'html']:
            filename = f'{year}-hinc06.{ext}'
            filepath = os.path.join(directory, filename)
            
            if os.path.exists(filepath):
                found = True
                
                # 检查是否已转换
                csv_filename = f'{year}-hinc06_converted.csv'
                csv_filepath = os.path.join(directory, csv_filename)
                
                if os.path.exists(csv_filepath):
                    print(f"{year}: ⏭️  已存在转换后的CSV，跳过")
                    skip_count += 1
                else:
                    print(f"\n{year}: {filename}")
                    if smart_convert(filepath, csv_filepath):
                        success_count += 1
                    else:
                        fail_count += 1
                
                break
        
        if not found:
            print(f"{year}: ⚠️  未找到文件")
    
    # 总结
    print("\n" + "="*80)
    print("转换完成")
    print("="*80)
    print(f"成功: {success_count} 个")
    print(f"失败: {fail_count} 个")
    print(f"跳过: {skip_count} 个")
    
    if fail_count > 0:
        print("\n建议:")
        print("  - 对于XLS文件: pip install xlrd")
        print("  - 对于HTML文件: pip install beautifulsoup4")
        print("  - 对于重定向页面: 从Census网站重新下载")


# ============================================
# 主程序
# ============================================

if __name__ == '__main__':
    
    import argparse
    
    parser = argparse.ArgumentParser(description='Census文件转换工具（无需LibreOffice）')
    parser.add_argument('input', nargs='?', help='输入文件（单文件模式）')
    parser.add_argument('-o', '--output', help='输出文件（单文件模式）')
    parser.add_argument('--batch', action='store_true', help='批量转换模式')
    parser.add_argument('--dir', default=DATA_DIR, help='数据目录（批量模式）')
    parser.add_argument('--start', type=int, default=2010, help='起始年份（批量模式）')
    parser.add_argument('--end', type=int, default=2024, help='结束年份（批量模式）')
    
    args = parser.parse_args()
    
    if args.batch:
        # 批量模式
        batch_convert(args.dir, args.start, args.end)
    
    elif args.input:
        # 单文件模式
        smart_convert(args.input, args.output)
    
    else:
        # 无参数，显示帮助
        parser.print_help()
        print("\n示例:")
        print("  # 单文件转换")
        print("  python 2-convert-files.py 2015-hinc06.xls")
        print("")
        print("  # 批量转换")
        print("  python 2-convert-files.py --batch")
        print("")
        print("  # 批量转换指定年份")
        print("  python 2-convert-files.py --batch --start 2010 --end 2015")