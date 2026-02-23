#!/usr/bin/env python3
"""
Census文件格式检测和转换助手
==================================

检测2010-2024年Census文件的实际格式，并提供转换建议

Author: Fei-Yun Wang
Date: 2026-02-19
"""

import os
import sys
import zipfile
from pathlib import Path

PROJECT_DIR = './_emis_code/census-1994-2024'
DATA_DIR = os.path.join(PROJECT_DIR, 'data')

def detect_file_type(filepath):
    """检测文件实际类型"""
    try:
        with open(filepath, 'rb') as f:
            header = f.read(8192)
        
        header_str = header.decode(errors='ignore').lower()
        
        if header.startswith(b'PK'):
            return 'XLSX', '✅ 可用openpyxl'
        elif header.startswith(b'\xD0\xCF\x11\xE0'):
            return 'XLS', '⚠️ 需要xlrd'
        elif '<html' in header_str:
            if 'window.location.href' in header_str:
                return 'HTML_REDIRECT', '❌ 重定向页面，需重新下载'
            else:
                return 'HTML', '⚠️ 需要html5lib'
        elif '<?xml' in header_str:
            return 'XML', '⚠️ Excel 2003 XML，建议转换'
        else:
            return 'UNKNOWN', '❌ 未知格式'
    
    except Exception as e:
        return 'ERROR', f'❌ 读取错误: {e}'


def scan_directory(directory, start_year=2010, end_year=2024):
    """扫描目录中的2010-2024年文件"""
    
    print("="*80)
    print("Census文件格式检测器 (2010-2024)")
    print("="*80)
    print(f"目录: {directory}\n")
    
    if not os.path.exists(directory):
        print(f"❌ 目录不存在: {directory}")
        return
    
    results = []
    
    for year in range(start_year, end_year + 1):
        # 尝试不同扩展名
        for ext in ['xlsx', 'xls', 'xml', 'html']:
            filename = f'{year}-hinc06.{ext}'
            filepath = os.path.join(directory, filename)
            
            if os.path.exists(filepath):
                file_type, status = detect_file_type(filepath)
                size_mb = os.path.getsize(filepath) / (1024 * 1024)
                
                results.append({
                    'year': year,
                    'filename': filename,
                    'size_mb': size_mb,
                    'type': file_type,
                    'status': status
                })
                break  # 找到后停止尝试其他扩展名
    
    # 显示结果
    print(f"{'年份':<6} {'文件名':<20} {'大小':<8} {'实际格式':<15} {'状态'}")
    print("-"*80)
    
    for r in results:
        print(f"{r['year']:<6} {r['filename']:<20} {r['size_mb']:>6.2f}MB {r['type']:<15} {r['status']}")
    
    # 统计
    print("\n" + "="*80)
    print("格式统计:")
    print("="*80)
    
    type_counts = {}
    for r in results:
        type_counts[r['type']] = type_counts.get(r['type'], 0) + 1
    
    for file_type, count in sorted(type_counts.items()):
        print(f"  {file_type:<15}: {count} 个文件")
    
    # 问题文件
    problem_files = [r for r in results if r['type'] in ['XLS', 'HTML_REDIRECT', 'XML', 'ERROR']]
    
    if problem_files:
        print("\n" + "="*80)
        print(f"需要处理的文件 ({len(problem_files)} 个):")
        print("="*80)
        
        for r in problem_files:
            print(f"\n{r['year']}: {r['filename']}")
            print(f"  类型: {r['type']}")
            print(f"  建议:")
            
            if r['type'] == 'XLS':
                print(f"    1. 安装xlrd: pip install xlrd")
                print(f"    2. 或转换为CSV: libreoffice --convert-to csv {r['filename']}")
            elif r['type'] == 'HTML_REDIRECT':
                print(f"    1. 从Census网站重新下载正确的文件")
                print(f"    2. URL: https://www.census.gov/data/tables/time-series/demo/income-poverty/cps-hinc/hinc-06.{r['year']}.html")
            elif r['type'] == 'XML':
                print(f"    1. 用Excel打开后另存为.xlsx")
                print(f"    2. 或转换为CSV: libreoffice --convert-to csv {r['filename']}")
            elif r['type'] == 'HTML':
                print(f"    1. 安装html5lib: pip install html5lib lxml")
                print(f"    2. 或转换为CSV: (用浏览器打开，另存为CSV)")
    else:
        print("\n✅ 所有文件格式正常，可直接解析！")
    
    print("\n" + "="*80)


def generate_conversion_script(directory, start_year=2010, end_year=2024):
    """生成批量转换脚本"""
    
    script_lines = ["#!/bin/bash", "# Census文件批量转换脚本", ""]
    
    for year in range(start_year, end_year + 1):
        for ext in ['xlsx', 'xls', 'xml']:
            filename = f'{year}-hinc06.{ext}'
            filepath = os.path.join(directory, filename)
            
            if os.path.exists(filepath):
                file_type, _ = detect_file_type(filepath)
                
                if file_type in ['XLS', 'XML']:
                    output = f'{year}-hinc06_converted.csv'
                    script_lines.append(f"# {year}年 ({file_type})")
                    script_lines.append(f"libreoffice --headless --convert-to csv --outdir {directory} {filepath}")
                    script_lines.append(f"mv {directory}/{year}-hinc06.csv {directory}/{output}")
                    script_lines.append("")
    
    script_path = os.path.join(directory, 'convert_census_files.sh')
    
    with open(script_path, 'w') as f:
        f.write('\n'.join(script_lines))
    
    os.chmod(script_path, 0o755)
    
    print(f"\n✅ 转换脚本已生成: {script_path}")
    print(f"   运行: bash {script_path}")


if __name__ == '__main__':
    
    import argparse
    
    parser = argparse.ArgumentParser(description='Census文件格式检测和转换助手')
    parser.add_argument('--dir', default=DATA_DIR, help='数据目录')
    parser.add_argument('--start', type=int, default=2010, help='起始年份')
    parser.add_argument('--end', type=int, default=2024, help='结束年份')
    parser.add_argument('--generate-script', action='store_true', help='生成转换脚本')
    
    args = parser.parse_args()
    
    scan_directory(args.dir, args.start, args.end)
    
    if args.generate_script:
        generate_conversion_script(args.dir, args.start, args.end)