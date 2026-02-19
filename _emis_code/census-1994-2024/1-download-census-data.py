#!/usr/bin/env python3
"""
批量下载Census收入数据 (1994-2024)
========================================

自动下载HINC-01和HINC-06数据表的Excel文件

Author: Fei-Yun Wang
Date: 2026-02-18
Version: v1.0
"""

import os
import sys
import time
import requests
from bs4 import BeautifulSoup
from pathlib import Path
import urllib.parse

# ============================================
# 配置
# ============================================

# 项目目录
PROJECT_DIR = './_emis_code/census-1994-2024/'
DATA_DIR = os.path.join(PROJECT_DIR, 'data')

# 年份范围
START_YEAR = 2010 # 1994-2009格式不同，手动下载了
END_YEAR = 2024

# 下载延迟（秒，避免过于频繁请求）
DOWNLOAD_DELAY = 30

# User-Agent (模拟浏览器)
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                  '(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

# ============================================
# 工具函数
# ============================================

def ensure_dir(directory):
    """确保目录存在"""
    Path(directory).mkdir(parents=True, exist_ok=True)


def download_file(url, save_path):
    """
    下载文件
    
    参数：
    - url: 文件URL
    - save_path: 保存路径
    
    返回：
    - True: 成功
    - False: 失败
    """
    try:
        response = requests.get(url, headers=HEADERS, timeout=30, stream=True)
        response.raise_for_status()
        
        with open(save_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        # 验证文件大小
        file_size = os.path.getsize(save_path)
        if file_size < 1000:  # 小于1KB可能是错误页面
            print(f"      ⚠️ 文件太小 ({file_size} bytes)，可能下载失败")
            os.remove(save_path)
            return False
        
        print(f"      ✅ 成功 ({file_size/1024:.1f} KB)")
        return True
        
    except Exception as e:
        print(f"      ❌ 失败: {e}")
        if os.path.exists(save_path):
            os.remove(save_path)
        return False


def parse_census_page(url):
    """
    解析Census网页，提取Excel下载链接
    
    参数：
    - url: Census网页URL
    
    返回：
    - excel_urls: Excel文件下载链接列表
    """
    try:
        response = requests.get(url, headers=HEADERS, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # 查找所有包含.xls/.xlsx的链接
        excel_urls = []
        for link in soup.find_all('a', href=True):
            href = link['href']
            if '.xls' in href.lower():
                # 处理相对URL
                if not href.startswith('http'):
                    href = urllib.parse.urljoin(url, href)
                excel_urls.append(href)
        
        return excel_urls
        
    except Exception as e:
        print(f"      ❌ 解析失败: {e}")
        return []


# ============================================
# 主下载逻辑
# ============================================

def select_best_excel(excel_urls, table_type):
    """
    从多个Excel链接中智能选择最合适的
    
    选择逻辑：
    1. 优先选择文件名包含"all"或"tot"的（总表）
    2. 排除包含"white"、"black"、"asian"、"hispanic"的（种族细分表）
    3. 排除包含"age"的（年龄细分表）
    4. 优先选择文件名最短的（通常是主表）
    
    参数：
    - excel_urls: Excel链接列表
    - table_type: 'hinc-01' 或 'hinc-06'
    
    返回：
    - (selected_url, reason): 选中的URL和选择理由
    """
    if not excel_urls:
        return None, "无可用文件"
    
    # 评分系统
    scored_urls = []
    
    for url in excel_urls:
        score = 0
        reasons = []
        url_lower = url.lower()
        
        # 从URL提取文件名
        filename = url.split('/')[-1].lower()
        
        # 加分项
        if 'all' in filename or 'tot' in filename:
            score += 10
            reasons.append("包含'all/total'")
        
        if table_type in filename:
            score += 5
            reasons.append(f"文件名匹配{table_type}")
        
        # 减分项（排除细分表）
        race_keywords = ['white', 'black', 'asian', 'hispanic', 'latino']
        if any(kw in filename for kw in race_keywords):
            score -= 20
            reasons.append("种族细分表（排除）")
        
        if 'age' in filename:
            score -= 10
            reasons.append("年龄细分表（排除）")
        
        # 文件名长度（越短越可能是主表）
        name_length_penalty = len(filename) / 10
        score -= name_length_penalty
        
        scored_urls.append({
            'url': url,
            'score': score,
            'reasons': reasons,
            'filename': filename
        })
    
    # 按分数排序
    scored_urls.sort(key=lambda x: x['score'], reverse=True)
    
    best = scored_urls[0]
    reason = '; '.join(best['reasons']) if best['reasons'] else "默认首选"
    
    return best['url'], reason, scored_urls


def list_available_files(year, table_type, dry_run=True):
    """
    列出指定年份表格的所有可用Excel文件
    
    参数：
    - year: 年份
    - table_type: 'hinc-01' 或 'hinc-06'
    - dry_run: 是否只列出不下载
    
    返回：
    - 如果dry_run=True: 返回(selected_url, all_urls)
    - 如果dry_run=False: 返回文件路径
    """
    # 构造Census网页URL
    base_url = f'https://www.census.gov/data/tables/time-series/demo/income-poverty/cps-hinc/{table_type}.{year}.html'
    
    print(f"    访问: {base_url}")
    
    # 解析网页获取Excel链接
    excel_urls = parse_census_page(base_url)
    
    if not excel_urls:
        print(f"      ⚠️ 未找到Excel下载链接")
        return None, []
    
    print(f"      找到 {len(excel_urls)} 个Excel文件:")
    
    # 智能选择最佳文件
    selected_url, reason, scored_urls = select_best_excel(excel_urls, table_type)
    
    # 显示所有文件
    for i, item in enumerate(scored_urls, 1):
        marker = "✅ [选中]" if item['url'] == selected_url else "   "
        print(f"        {marker} [{i}] {item['filename']}")
        print(f"            URL: {item['url']}")
        print(f"            评分: {item['score']:.1f}")
        if item['reasons']:
            print(f"            理由: {'; '.join(item['reasons'])}")
    
    if selected_url:
        print(f"      🎯 将下载: {scored_urls[0]['filename']}")
        print(f"      📌 选择理由: {reason}")
    
    if dry_run:
        return selected_url, excel_urls
    
    # 实际下载
    return download_selected_file(year, table_type, selected_url)


def download_selected_file(year, table_type, url):
    """
    下载选定的文件
    
    参数：
    - year: 年份
    - table_type: 'hinc-01' 或 'hinc-06'
    - url: 下载链接
    
    返回：
    - 文件路径（成功）或 None（失败）
    """
    # 生成文件名
    if table_type == 'hinc-01':
        if year == 2019:
            filename = f'{year}-hinc01_1.xlsx'
        else:
            filename = f'{year}-hinc01.xlsx'
    else:
        filename = f'{year}-hinc06.xlsx'
    
    save_path = os.path.join(DATA_DIR, filename)
    
    # 如果文件已存在，跳过
    if os.path.exists(save_path):
        file_size = os.path.getsize(save_path)
        print(f"      ⏭️  已存在 ({file_size/1024:.1f} KB)")
        return save_path
    
    print(f"      下载: {url}")
    success = download_file(url, save_path)
    
    if success:
        return save_path
    
    return None


def download_year_data(year, dry_run=False):
    """
    下载指定年份的所有数据
    
    参数：
    - year: 年份
    - dry_run: True=仅列出文件，False=实际下载
    
    返回：
    - (hinc01_path, hinc06_path): 文件路径元组（或URL元组如果dry_run）
    """
    mode_str = "【预览模式】" if dry_run else ""
    print(f"\n{'='*80}")
    print(f"{mode_str}处理 {year} 年数据")
    print(f"{'='*80}")
    
    # 下载HINC-01
    print(f"  [1/2] HINC-01 (主要收入分布)")
    hinc01_result = list_available_files(year, 'hinc-01', dry_run=dry_run)
    if not dry_run:
        time.sleep(DOWNLOAD_DELAY)
    
    # 下载HINC-06
    print(f"  [2/2] HINC-06 (高收入细分)")
    hinc06_result = list_available_files(year, 'hinc-06', dry_run=dry_run)
    if not dry_run:
        time.sleep(DOWNLOAD_DELAY)
    
    # 解包结果
    if dry_run:
        hinc01_url = hinc01_result[0] if hinc01_result else None
        hinc06_url = hinc06_result[0] if hinc06_result else None
        
        # 总结
        if hinc01_url and hinc06_url:
            print(f"  ✅ {year} 数据完整（预览）")
        elif hinc01_url:
            print(f"  ⚠️  {year} 仅HINC-01（预览）")
        else:
            print(f"  ❌ {year} 无可用文件（预览）")
        
        return hinc01_url, hinc06_url
    else:
        hinc01_path = hinc01_result
        hinc06_path = hinc06_result
        
        # 总结
        if hinc01_path and hinc06_path:
            print(f"  ✅ {year} 数据完整")
        elif hinc01_path:
            print(f"  ⚠️  {year} 仅HINC-01（HINC-06可能不存在）")
        else:
            print(f"  ❌ {year} 下载失败")
        
        return hinc01_path, hinc06_path


# ============================================
# 主程序
# ============================================

def main(dry_run=False):
    """
    主程序
    
    参数：
    - dry_run: True=仅列出文件不下载，False=实际下载
    """
    
    mode_str = "【预览模式 - 不会实际下载】" if dry_run else ""
    
    print("="*80)
    print(f"Census收入数据批量下载工具 {mode_str}")
    print("="*80)
    print(f"年份范围: {START_YEAR} - {END_YEAR}")
    print(f"数据目录: {DATA_DIR}")
    if not dry_run:
        print(f"下载延迟: {DOWNLOAD_DELAY} 秒/文件")
    
    # 创建数据目录
    if not dry_run:
        ensure_dir(DATA_DIR)
    
    # 统计
    total_years = END_YEAR - START_YEAR + 1
    success_count = 0
    partial_count = 0
    fail_count = 0
    
    # 逐年处理
    for year in range(START_YEAR, END_YEAR + 1):
        hinc01, hinc06 = download_year_data(year, dry_run=dry_run)
        
        if hinc01 and hinc06:
            success_count += 1
        elif hinc01:
            partial_count += 1
        else:
            fail_count += 1
    
    # 最终总结
    print("\n" + "="*80)
    print(f"{'预览' if dry_run else '下载'}完成")
    print("="*80)
    print(f"总年份: {total_years}")
    print(f"  ✅ 完整数据: {success_count} 年")
    print(f"  ⚠️  部分数据: {partial_count} 年 (仅HINC-01)")
    print(f"  ❌ 失败: {fail_count} 年")
    
    if dry_run:
        print(f"\n💡 这只是预览，没有实际下载文件")
        print(f"   如果文件选择正确，运行:")
        print(f"   python 1-download-census-data.py")
    elif fail_count > 0:
        print(f"\n建议:")
        print(f"  1. 检查网络连接")
        print(f"  2. 手动访问Census网站确认数据是否可用")
        print(f"  3. 对于失败的年份，可以手动下载后放入 {DATA_DIR}")
    
    if not dry_run:
        print(f"\n数据目录: {os.path.abspath(DATA_DIR)}")
        print(f"下一步: 运行 2-batch-analysis.py 进行批量分析")


# ============================================
# 辅助功能：检查已下载的数据
# ============================================

def test_single_year(year=2019):
    """快速测试单个年份的文件选择逻辑"""
    print("="*80)
    print(f"快速测试: {year} 年")
    print("="*80)
    print("这个测试会访问Census网站并列出所有Excel文件\n")
    
    download_year_data(year, dry_run=True)
    
    print("\n如果文件选择正确，可以:")
    print(f"  1. 运行 python 1-download-census-data.py --dry-run   # 预览所有年份")
    print(f"  2. 运行 python 1-download-census-data.py             # 实际下载")


def check_downloaded_data():
    """检查已下载的数据完整性"""
    
    print("="*80)
    print("检查已下载数据")
    print("="*80)
    
    if not os.path.exists(DATA_DIR):
        print(f"数据目录不存在: {DATA_DIR}")
        return
    
    files = sorted(os.listdir(DATA_DIR))
    
    if not files:
        print("数据目录为空")
        return
    
    print(f"共找到 {len(files)} 个文件:\n")
    
    years_hinc01 = set()
    years_hinc06 = set()
    
    for filename in files:
        if 'hinc01' in filename.lower():
            year = int(filename.split('-')[0])
            years_hinc01.add(year)
            size = os.path.getsize(os.path.join(DATA_DIR, filename))
            print(f"  {filename:<30} ({size/1024:>7.1f} KB)")
        elif 'hinc06' in filename.lower():
            year = int(filename.split('-')[0])
            years_hinc06.add(year)
            size = os.path.getsize(os.path.join(DATA_DIR, filename))
            print(f"  {filename:<30} ({size/1024:>7.1f} KB)")
    
    print(f"\n统计:")
    print(f"  HINC-01: {len(years_hinc01)} 年")
    print(f"  HINC-06: {len(years_hinc06)} 年")
    print(f"  完整数据: {len(years_hinc01 & years_hinc06)} 年")
    
    missing_hinc06 = years_hinc01 - years_hinc06
    if missing_hinc06:
        print(f"  仅HINC-01（缺HINC-06）: {sorted(missing_hinc06)}")


# ============================================
# 运行
# ============================================

if __name__ == '__main__':
    
    # 检查命令行参数
    if len(sys.argv) > 1:
        if sys.argv[1] == '--check':
            check_downloaded_data()
        elif sys.argv[1] == '--test':
            # 快速测试2019年
            test_year = int(sys.argv[2]) if len(sys.argv) > 2 else 2019
            test_single_year(test_year)
        elif sys.argv[1] == '--dry-run' or sys.argv[1] == '--preview':
            print("\n💡 预览模式：只显示会下载哪些文件，不实际下载\n")
            try:
                main(dry_run=True)
            except KeyboardInterrupt:
                print("\n\n⚠️ 用户中断预览")
            except Exception as e:
                print(f"\n\n❌ 程序错误: {e}")
                import traceback
                traceback.print_exc()
        elif sys.argv[1] == '--help' or sys.argv[1] == '-h':
            print("""
Census收入数据批量下载工具

用法:
    python 1-download-census-data.py                 # 实际下载全部年份
    python 1-download-census-data.py --test [year]   # 快速测试单个年份（默认2019）
    python 1-download-census-data.py --dry-run       # 预览全部年份（推荐）
    python 1-download-census-data.py --check         # 检查已下载数据
    python 1-download-census-data.py --help          # 显示帮助

推荐流程:
    1. python 1-download-census-data.py --test 2019     # 先测试一年
    2. python 1-download-census-data.py --dry-run       # 预览全部
    3. python 1-download-census-data.py                 # 确认无误后下载

说明:
    --test      快速测试单个年份，查看文件选择逻辑（推荐先运行）
    --dry-run   预览全部年份会下载哪些Excel文件，不实际下载
    --check     检查data/目录中已下载的文件
    --help      显示此帮助信息
    
选择逻辑:
    程序会智能选择Census网页上的主表（All races/Total）:
      ✅ 优先选择: 文件名包含"all"或"tot"的
      ✅ 优先选择: 文件名最短的（通常是主表）
      ❌ 排除: 按种族细分的表（white, black, asian, hispanic）
      ❌ 排除: 按年龄细分的表（age）
      
    如果有疑问，先运行 --test 2019 查看实际会选哪个文件
            """)
        else:
            print(f"未知参数: {sys.argv[1]}")
            print("运行 python 1-download-census-data.py --help 查看帮助")
    else:
        # 默认：实际下载
        try:
            main(dry_run=False)
        except KeyboardInterrupt:
            print("\n\n⚠️ 用户中断下载")
            print("已下载的文件已保存")
        except Exception as e:
            print(f"\n\n❌ 程序错误: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "="*80)