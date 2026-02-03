"""
论文数据完整版：三种交易方式 × 三个市场 × EMIS vs VIX
使用完整的2005年数据
"""

import numpy as np
import pandas as pd
import os
import warnings
warnings.filterwarnings('ignore')

# ============================================
# 参数
# ============================================

TRAIN_END = '2020-01-01'
HORIZON = 30

# ============================================
# 时区修复
# ============================================

def fix_timezone(df):
    is_series = isinstance(df, pd.Series)
    if is_series:
        name = df.name
        df = df.to_frame()
    
    df = df.reset_index()
    date_col = df.columns[0]
    df[date_col] = pd.to_datetime(df[date_col].astype(str).str[:10])
    df = df.set_index(date_col)
    
    if is_series:
        return df.iloc[:, 0].rename(name)
    return df

# ============================================
# 三种交易方式
# ============================================

def trades_overlapping(S, index, threshold, horizon=30):
    """重叠交易：每个信号都算"""
    results = []
    for t in range(len(S) - horizon):
        date = S.index[t]
        if S.iloc[t] > threshold and date in index.index:
            idx = index.index.get_loc(date)
            if idx + horizon < len(index):
                ret = np.log(index.iloc[idx + horizon] / index.iloc[idx])
                results.append({'date': date, 'return': ret, 'win': ret > 0})
    return pd.DataFrame(results) if results else None

def trades_non_overlapping(S, index, threshold, horizon=30):
    """不重叠交易：持有期内不交易"""
    results = []
    t = 0
    while t < len(S) - horizon:
        date = S.index[t]
        if S.iloc[t] > threshold and date in index.index:
            idx = index.index.get_loc(date)
            if idx + horizon < len(index):
                ret = np.log(index.iloc[idx + horizon] / index.iloc[idx])
                results.append({'date': date, 'return': ret, 'win': ret > 0})
                t += horizon
                continue
        t += 1
    return pd.DataFrame(results) if results else None

def trades_weekly(S, index, threshold, horizon=30):
    """每周一次：同一周只交易一次"""
    results = []
    last_week = None
    
    for t in range(len(S) - horizon):
        date = S.index[t]
        week = (date.year, date.isocalendar()[1])
        
        if S.iloc[t] > threshold and week != last_week:
            if date in index.index:
                idx = index.index.get_loc(date)
                if idx + horizon < len(index):
                    ret = np.log(index.iloc[idx + horizon] / index.iloc[idx])
                    results.append({'date': date, 'return': ret, 'win': ret > 0})
                    last_week = week
    
    return pd.DataFrame(results) if results else None

# ============================================
# 加载数据
# ============================================

def load_data(entropy_file, index_file):
    if not os.path.exists(entropy_file) or not os.path.exists(index_file):
        return None, None
    
    S = pd.read_csv(entropy_file, index_col=0, parse_dates=True)
    if isinstance(S, pd.DataFrame):
        S = S.iloc[:, 0]
    S = fix_timezone(S)
    
    index = pd.read_csv(index_file, index_col=0, parse_dates=True)
    if isinstance(index, pd.DataFrame):
        index = index.iloc[:, 0]
    index = fix_timezone(index)
    
    return S, index

# ============================================
# 处理单个市场
# ============================================

def process_market(market_name, entropy_file, index_file):
    print(f"\n{'='*60}")
    print(f"市场: {market_name}")
    print("="*60)
    
    S, index = load_data(entropy_file, index_file)
    if S is None:
        print(f"  ❌ 找不到文件")
        return []
    
    print(f"  纠缠熵: {entropy_file} ({len(S)} 天)")
    print(f"  指数: {index_file} ({len(index)} 天)")
    
    # 对齐
    common = S.index.intersection(index.index)
    S = S.loc[common]
    index = index.loc[common]
    
    # 划分
    train_end = pd.to_datetime(TRAIN_END)
    S_train = S[S.index < train_end]
    S_test = S[S.index >= train_end]
    index_test = index[index.index >= train_end]
    
    if len(S_train) == 0:
        print(f"  ❌ 训练集为空")
        return []
    
    print(f"  训练集: {S_train.index.min().date()} ~ {S_train.index.max().date()} ({len(S_train)} 天)")
    print(f"  测试集: {S_test.index.min().date()} ~ {S_test.index.max().date()} ({len(S_test)} 天)")
    
    # 阈值
    threshold = S_train.quantile(0.90)
    print(f"  阈值 (90%): {threshold:.4f}")
    
    # 三种交易方式
    results_list = []
    
    print(f"\n  {'方式':<12} {'交易次数':<10} {'胜率':<10} {'平均收益':<12} {'累计收益':<12}")
    print("  " + "-"*58)
    
    for method_name, method_func in [
        ('重叠', trades_overlapping),
        ('不重叠', trades_non_overlapping),
        ('每周一次', trades_weekly)
    ]:
        results = method_func(S_test, index_test, threshold, HORIZON)
        
        if results is not None and len(results) > 0:
            wr = results['win'].mean()
            avg_ret = results['return'].mean()
            cum_ret = results['return'].sum()
            print(f"  {method_name:<12} {len(results):<10} {wr:<10.1%} {avg_ret:<12.1%} {cum_ret:<12.1%}")
            
            results_list.append({
                'market': market_name,
                'method': method_name,
                'indicator': 'EMIS',
                'trades': len(results),
                'win_rate': wr,
                'avg_return': avg_ret,
                'cum_return': cum_ret
            })
        else:
            print(f"  {method_name:<12} {'无信号':<10}")
    
    return results_list

# ============================================
# 主程序
# ============================================

def main():
    print("="*70)
    print("论文数据完整版（三种交易方式 × 三个市场 × EMIS vs VIX）")
    print("="*70)
    print(f"训练集截止: {TRAIN_END}")
    print(f"测试集: 2020-01-01 ~ 2026-01-30")
    print(f"持有期: {HORIZON} 天")
    
    all_results = []
    
    # ============================================
    # 美国市场（使用新的完整数据）
    # ============================================
    
    us_results = process_market(
        "US (S&P 500)", 
        'entropy_US_since2005.csv',  # 新的完整数据
        'sp500.csv'
    )
    all_results.extend(us_results)
    
    # ============================================
    # 日本市场
    # ============================================
    
    jp_results = process_market(
        "Japan (Nikkei)", 
        'entropy_Japan_since2005_v2.csv', 
        'index_Japan_since2005.csv'
    )
    all_results.extend(jp_results)
    
    # ============================================
    # 德国市场
    # ============================================
    
    de_results = process_market(
        "Germany (DAX)", 
        'entropy_DAX_historical.csv', 
        'index_DAX.csv'
    )
    all_results.extend(de_results)
    
    # ============================================
    # VIX 对比（美国市场）
    # ============================================
    
    print(f"\n{'='*60}")
    print("VIX 对比 (美国市场)")
    print("="*60)
    
    if os.path.exists('vix.csv') and os.path.exists('sp500.csv'):
        vix = pd.read_csv('vix.csv', index_col=0, parse_dates=True).iloc[:, 0]
        vix = fix_timezone(vix)
        
        sp500 = pd.read_csv('sp500.csv', index_col=0, parse_dates=True).iloc[:, 0]
        sp500 = fix_timezone(sp500)
        
        # 对齐
        common = vix.index.intersection(sp500.index)
        vix = vix.loc[common]
        sp500 = sp500.loc[common]
        
        # 划分
        train_end = pd.to_datetime(TRAIN_END)
        vix_train = vix[vix.index < train_end]
        vix_test = vix[vix.index >= train_end]
        sp500_test = sp500[sp500.index >= train_end]
        
        vix_threshold = vix_train.quantile(0.90)
        
        print(f"  训练集: {vix_train.index.min().date()} ~ {vix_train.index.max().date()} ({len(vix_train)} 天)")
        print(f"  测试集: {vix_test.index.min().date()} ~ {vix_test.index.max().date()} ({len(vix_test)} 天)")
        print(f"  阈值 (90%): {vix_threshold:.2f}")
        
        print(f"\n  {'方式':<12} {'交易次数':<10} {'胜率':<10} {'平均收益':<12} {'累计收益':<12}")
        print("  " + "-"*58)
        
        for method_name, method_func in [
            ('重叠', trades_overlapping),
            ('不重叠', trades_non_overlapping),
            ('每周一次', trades_weekly)
        ]:
            results = method_func(vix_test, sp500_test, vix_threshold, HORIZON)
            
            if results is not None and len(results) > 0:
                wr = results['win'].mean()
                avg_ret = results['return'].mean()
                cum_ret = results['return'].sum()
                print(f"  {method_name:<12} {len(results):<10} {wr:<10.1%} {avg_ret:<12.1%} {cum_ret:<12.1%}")
                
                all_results.append({
                    'market': 'US (S&P 500)',
                    'method': method_name,
                    'indicator': 'VIX',
                    'trades': len(results),
                    'win_rate': wr,
                    'avg_return': avg_ret,
                    'cum_return': cum_ret
                })
    
    # ============================================
    # 汇总表格
    # ============================================
    
    if len(all_results) == 0:
        print("\n❌ 没有数据")
        return
    
    df = pd.DataFrame(all_results)
    
    print(f"\n{'='*70}")
    print("论文 Table: 全球验证结果")
    print("="*70)
    
    # Panel A: 重叠交易
    print("\nPanel A: Overlapping Trades (Signal Effectiveness)")
    print("-"*75)
    print(f"{'Market':<20} {'Indicator':<10} {'Trades':<10} {'Win Rate':<12} {'Avg Return':<12} {'Cum Return':<12}")
    print("-"*75)
    overlap = df[df['method'] == '重叠']
    for _, row in overlap.iterrows():
        print(f"{row['market']:<20} {row['indicator']:<10} {row['trades']:<10} {row['win_rate']:<12.1%} {row['avg_return']:<12.1%} {row['cum_return']:<12.1%}")
    
    # Panel B: 不重叠交易
    print("\nPanel B: Non-overlapping Trades (Implementable)")
    print("-"*75)
    print(f"{'Market':<20} {'Indicator':<10} {'Trades':<10} {'Win Rate':<12} {'Avg Return':<12} {'Cum Return':<12}")
    print("-"*75)
    non_overlap = df[df['method'] == '不重叠']
    for _, row in non_overlap.iterrows():
        print(f"{row['market']:<20} {row['indicator']:<10} {row['trades']:<10} {row['win_rate']:<12.1%} {row['avg_return']:<12.1%} {row['cum_return']:<12.1%}")
    
    # Panel C: 每周交易
    print("\nPanel C: Weekly Trades (Practical)")
    print("-"*75)
    print(f"{'Market':<20} {'Indicator':<10} {'Trades':<10} {'Win Rate':<12} {'Avg Return':<12} {'Cum Return':<12}")
    print("-"*75)
    weekly = df[df['method'] == '每周一次']
    for _, row in weekly.iterrows():
        print(f"{row['market']:<20} {row['indicator']:<10} {row['trades']:<10} {row['win_rate']:<12.1%} {row['avg_return']:<12.1%} {row['cum_return']:<12.1%}")
    
    # 保存
    df.to_csv('paper_results_complete.csv', index=False)
    print(f"\n结果已保存: paper_results_complete.csv")
    
    # ============================================
    # 论文摘要关键数据
    # ============================================
    
    print(f"\n{'='*70}")
    print("论文摘要关键数据")
    print("="*70)
    
    # EMIS 全球平均（重叠）
    emis_overlap = df[(df['indicator'] == 'EMIS') & (df['method'] == '重叠')]
    if len(emis_overlap) > 0:
        print(f"\nEMIS 全球平均 (重叠, {len(emis_overlap)} 个市场):")
        print(f"  胜率: {emis_overlap['win_rate'].mean():.1%}")
        print(f"  收益: {emis_overlap['avg_return'].mean():.1%}")
    
    # EMIS 全球平均（不重叠）
    emis_non = df[(df['indicator'] == 'EMIS') & (df['method'] == '不重叠')]
    if len(emis_non) > 0:
        print(f"\nEMIS 全球平均 (不重叠, {len(emis_non)} 个市场):")
        print(f"  胜率: {emis_non['win_rate'].mean():.1%}")
        print(f"  收益: {emis_non['avg_return'].mean():.1%}")
    
    # EMIS 全球平均（每周）
    emis_weekly = df[(df['indicator'] == 'EMIS') & (df['method'] == '每周一次')]
    if len(emis_weekly) > 0:
        print(f"\nEMIS 全球平均 (每周一次, {len(emis_weekly)} 个市场):")
        print(f"  胜率: {emis_weekly['win_rate'].mean():.1%}")
        print(f"  收益: {emis_weekly['avg_return'].mean():.1%}")
    
    # EMIS vs VIX（美国，重叠）
    emis_us = df[(df['market'] == 'US (S&P 500)') & (df['indicator'] == 'EMIS') & (df['method'] == '重叠')]
    vix_us = df[(df['market'] == 'US (S&P 500)') & (df['indicator'] == 'VIX') & (df['method'] == '重叠')]
    
    if len(emis_us) > 0 and len(vix_us) > 0:
        emis_wr = emis_us['win_rate'].values[0]
        vix_wr = vix_us['win_rate'].values[0]
        emis_ret = emis_us['avg_return'].values[0]
        vix_ret = vix_us['avg_return'].values[0]
        
        print(f"\nEMIS vs VIX (美国, 重叠):")
        print(f"  EMIS: {emis_us['trades'].values[0]} 次, 胜率 {emis_wr:.1%}, 收益 {emis_ret:.1%}")
        print(f"  VIX:  {vix_us['trades'].values[0]} 次, 胜率 {vix_wr:.1%}, 收益 {vix_ret:.1%}")
        print(f"  胜率优势: {(emis_wr - vix_wr)*100:+.1f}%")
        print(f"  收益优势: {(emis_ret - vix_ret)*100:+.1f}%")
        
        if emis_wr > vix_wr:
            print("\n  ✅ EMIS 优于 VIX")
    
    return df

# ============================================
# 运行
# ============================================

if __name__ == "__main__":
    df = main()