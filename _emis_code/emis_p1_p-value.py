"""
三种交易方式的统计检验
"""

import numpy as np
import pandas as pd
from scipy import stats

# ============================================
# 三种交易方式
# ============================================

def compute_trades_overlapping(S, index_prices, S_threshold, horizon=30):
    """
    重叠交易：每天信号触发都算一次
    """
    if isinstance(S, pd.DataFrame):
        S = S.iloc[:, 0]
    if isinstance(index_prices, pd.DataFrame):
        index_prices = index_prices.iloc[:, 0]
    
    trades = []
    
    for t in range(len(S) - horizon):
        date = S.index[t]
        S_value = S.iloc[t]
        
        if S_value > S_threshold:
            if date in index_prices.index:
                try:
                    idx = index_prices.index.get_loc(date)
                    if idx + horizon < len(index_prices):
                        entry_price = float(index_prices.iloc[idx])
                        exit_price = float(index_prices.iloc[idx + horizon])
                        ret = np.log(exit_price / entry_price)
                        
                        trades.append({
                            'entry_date': date,
                            'exit_date': index_prices.index[idx + horizon],
                            'S': S_value,
                            'return': ret,
                            'win': ret > 0
                        })
                except:
                    pass
    
    return pd.DataFrame(trades)


def compute_trades_non_overlapping(S, index_prices, S_threshold, horizon=30):
    """
    不重叠交易：必须等上一笔结束才能开下一笔
    """
    if isinstance(S, pd.DataFrame):
        S = S.iloc[:, 0]
    if isinstance(index_prices, pd.DataFrame):
        index_prices = index_prices.iloc[:, 0]
    
    trades = []
    last_exit_date = None
    
    for t in range(len(S) - horizon):
        date = S.index[t]
        S_value = S.iloc[t]
        
        # 如果还在持仓期内，跳过
        if last_exit_date is not None and date <= last_exit_date:
            continue
        
        if S_value > S_threshold:
            if date in index_prices.index:
                try:
                    idx = index_prices.index.get_loc(date)
                    if idx + horizon < len(index_prices):
                        entry_price = float(index_prices.iloc[idx])
                        exit_price = float(index_prices.iloc[idx + horizon])
                        ret = np.log(exit_price / entry_price)
                        exit_date = index_prices.index[idx + horizon]
                        
                        trades.append({
                            'entry_date': date,
                            'exit_date': exit_date,
                            'S': S_value,
                            'return': ret,
                            'win': ret > 0
                        })
                        
                        last_exit_date = exit_date  # 更新最后退出日期
                except:
                    pass
    
    return pd.DataFrame(trades)


def compute_trades_weekly(S, index_prices, S_threshold, horizon=30, check_day=0):
    """
    每周一次交易：只在每周固定日期检查
    
    check_day: 0=周一, 1=周二, ..., 4=周五
    """
    if isinstance(S, pd.DataFrame):
        S = S.iloc[:, 0]
    if isinstance(index_prices, pd.DataFrame):
        index_prices = index_prices.iloc[:, 0]
    
    trades = []
    last_exit_date = None
    
    for t in range(len(S) - horizon):
        date = S.index[t]
        
        # 只在指定的星期几检查
        if date.dayofweek != check_day:
            continue
        
        # 如果还在持仓期内，跳过
        if last_exit_date is not None and date <= last_exit_date:
            continue
        
        S_value = S.iloc[t]
        
        if S_value > S_threshold:
            if date in index_prices.index:
                try:
                    idx = index_prices.index.get_loc(date)
                    if idx + horizon < len(index_prices):
                        entry_price = float(index_prices.iloc[idx])
                        exit_price = float(index_prices.iloc[idx + horizon])
                        ret = np.log(exit_price / entry_price)
                        exit_date = index_prices.index[idx + horizon]
                        
                        trades.append({
                            'entry_date': date,
                            'exit_date': exit_date,
                            'S': S_value,
                            'return': ret,
                            'win': ret > 0
                        })
                        
                        last_exit_date = exit_date
                except:
                    pass
    
    return pd.DataFrame(trades)


# ============================================
# 统计检验
# ============================================

def statistical_analysis(trades_df, name):
    """对交易结果进行统计检验"""
    
    if len(trades_df) == 0:
        return None
    
    returns = trades_df['return'].values
    n = len(returns)
    n_wins = int(trades_df['win'].sum())
    mean_ret = np.mean(returns)
    std_ret = np.std(returns, ddof=1) if n > 1 else 0
    
    # 胜率检验
    p_winrate = 1 - stats.binom.cdf(n_wins - 1, n, 0.5) if n > 0 else 1
    
    # 收益 t 检验
    if n > 1 and std_ret > 0:
        t_stat, p_two = stats.ttest_1samp(returns, 0)
        p_return = p_two / 2 if t_stat > 0 else 1
    else:
        t_stat, p_return = 0, 1
    
    # 置信区间
    se = std_ret / np.sqrt(n) if n > 0 else 0
    ci_low = mean_ret - 1.96 * se
    ci_high = mean_ret + 1.96 * se
    
    return {
        'name': name,
        'n_trades': n,
        'n_wins': n_wins,
        'win_rate': n_wins / n if n > 0 else 0,
        'mean_return': mean_ret,
        'std_return': std_ret,
        'min_return': np.min(returns) if n > 0 else 0,
        'max_return': np.max(returns) if n > 0 else 0,
        'p_winrate': p_winrate,
        't_stat': t_stat,
        'p_return': p_return,
        'ci_low': ci_low,
        'ci_high': ci_high
    }

def get_stars(p):
    if p < 0.001: return '***'
    elif p < 0.01: return '**'
    elif p < 0.05: return '*'
    else: return ''


# ============================================
# 主程序
# ============================================

def main():
    print("="*80)
    print("EMIS P1 三种交易方式统计检验")
    print("="*80)
    
    # 读取数据
    markets = {
        'US': {
            'entropy_file': 'entropy_US_since2005.csv',
            'index_file': 'sp500.csv'
        },
        'Japan': {
            'entropy_file': 'entropy_Japan_since2005_v2.csv',
            'index_file': 'index_Japan_since2005.csv'
        },
        'Germany': {
            'entropy_file': 'entropy_DAX_historical.csv',
            'index_file': 'index_DAX.csv'
        }
    }
    
    train_end = pd.Timestamp('2020-01-01')
    horizon = 30
    
    all_results = []
    
    for market, files in markets.items():
        print(f"\n{'='*80}")
        print(f"市场: {market}")
        print("="*80)
        
        try:
            S = pd.read_csv(files['entropy_file'], index_col=0, parse_dates=True)
            index_prices = pd.read_csv(files['index_file'], index_col=0, parse_dates=True)
        except FileNotFoundError as e:
            print(f"  文件未找到: {e}")
            continue
        
        if isinstance(S, pd.DataFrame):
            S = S.iloc[:, 0]
        if isinstance(index_prices, pd.DataFrame):
            index_prices = index_prices.iloc[:, 0]
        
        # 训练/测试划分
        S_train = S[S.index < train_end]
        S_test = S[S.index >= train_end]
        index_test = index_prices[index_prices.index >= train_end]
        
        S_threshold = S_train.quantile(0.90)
        print(f"  阈值 (训练集90%): {S_threshold:.4f}")
        
        # 三种交易方式
        methods = {
            '重叠': compute_trades_overlapping,
            '不重叠': compute_trades_non_overlapping,
            '每周一次': compute_trades_weekly
        }
        
        print(f"\n  {'方式':<12} {'交易次数':<10} {'胜率':<10} {'平均收益':<10} "
              f"{'标准差':<10} {'p值(胜率)':<15} {'p值(收益)':<15}")
        print("  " + "-"*90)
        
        for method_name, method_func in methods.items():
            trades = method_func(S_test, index_test, S_threshold, horizon)
            result = statistical_analysis(trades, f"{market}_{method_name}")
            
            if result:
                result['market'] = market
                result['method'] = method_name
                all_results.append(result)
                
                print(f"  {method_name:<12} {result['n_trades']:<10} "
                      f"{result['win_rate']:<10.1%} {result['mean_return']:<10.2%} "
                      f"{result['std_return']:<10.2%} "
                      f"{result['p_winrate']:<15.2e}{get_stars(result['p_winrate'])} "
                      f"{result['p_return']:<15.2e}{get_stars(result['p_return'])}")
                
                # 保存交易明细
                trades.to_csv(f"trades_{market}_{method_name}.csv", index=False)
    
    # VIX 对比
    print(f"\n{'='*80}")
    print("VIX 对比 (美国市场)")
    print("="*80)
    
    try:
        vix = pd.read_csv('vix.csv', index_col=0, parse_dates=True)
        sp500 = pd.read_csv('sp500.csv', index_col=0, parse_dates=True)
        
        if isinstance(vix, pd.DataFrame):
            vix = vix.iloc[:, 0]
        if isinstance(sp500, pd.DataFrame):
            sp500 = sp500.iloc[:, 0]
        
        vix_train = vix[vix.index < train_end]
        vix_test = vix[vix.index >= train_end]
        sp500_test = sp500[sp500.index >= train_end]
        
        vix_threshold = vix_train.quantile(0.90)
        print(f"  VIX 阈值: {vix_threshold:.2f}")
        
        print(f"\n  {'方式':<12} {'交易次数':<10} {'胜率':<10} {'平均收益':<10} "
              f"{'标准差':<10} {'p值(胜率)':<15} {'p值(收益)':<15}")
        print("  " + "-"*90)
        
        for method_name, method_func in methods.items():
            trades = method_func(vix_test, sp500_test, vix_threshold, horizon)
            result = statistical_analysis(trades, f"VIX_{method_name}")
            
            if result:
                result['market'] = 'VIX'
                result['method'] = method_name
                all_results.append(result)
                
                print(f"  {method_name:<12} {result['n_trades']:<10} "
                      f"{result['win_rate']:<10.1%} {result['mean_return']:<10.2%} "
                      f"{result['std_return']:<10.2%} "
                      f"{result['p_winrate']:<15.2e}{get_stars(result['p_winrate'])} "
                      f"{result['p_return']:<15.2e}{get_stars(result['p_return'])}")
    
    except FileNotFoundError:
        print("  VIX 文件未找到")
    
    # ============================================
    # 论文表格
    # ============================================
    
    print("\n" + "="*80)
    print("论文表格")
    print("="*80)
    
    print("""
Table X: Statistical Significance of EMIS Indicator by Trading Method
Out-of-Sample Period: 2020-01 to 2026-01

Panel A: Overlapping Trades (Signal Quality Assessment)
--------------------------------------------------------------------------------
Market          Trades   Win Rate   Mean Ret   Std Dev    p(WR)        p(Ret)
--------------------------------------------------------------------------------""")
    
    for r in all_results:
        if r['method'] == '重叠':
            print(f"{r['market']:<15} {r['n_trades']:<8} {r['win_rate']:<10.1%} "
                  f"{r['mean_return']:<10.2%} {r['std_return']:<10.2%} "
                  f"{r['p_winrate']:<12.2e} {r['p_return']:.2e}{get_stars(r['p_return'])}")
    
    print("""--------------------------------------------------------------------------------

Panel B: Non-Overlapping Trades (Implementable Strategy)
--------------------------------------------------------------------------------
Market          Trades   Win Rate   Mean Ret   Std Dev    p(WR)        p(Ret)
--------------------------------------------------------------------------------""")
    
    for r in all_results:
        if r['method'] == '不重叠':
            print(f"{r['market']:<15} {r['n_trades']:<8} {r['win_rate']:<10.1%} "
                  f"{r['mean_return']:<10.2%} {r['std_return']:<10.2%} "
                  f"{r['p_winrate']:<12.2e} {r['p_return']:.2e}{get_stars(r['p_return'])}")
    
    print("""--------------------------------------------------------------------------------

Panel C: Weekly Trades (Practical Strategy)
--------------------------------------------------------------------------------
Market          Trades   Win Rate   Mean Ret   Std Dev    p(WR)        p(Ret)
--------------------------------------------------------------------------------""")
    
    for r in all_results:
        if r['method'] == '每周一次':
            print(f"{r['market']:<15} {r['n_trades']:<8} {r['win_rate']:<10.1%} "
                  f"{r['mean_return']:<10.2%} {r['std_return']:<10.2%} "
                  f"{r['p_winrate']:<12.2e} {r['p_return']:.2e}{get_stars(r['p_return'])}")
    
    print("""--------------------------------------------------------------------------------

Note: *, **, *** indicate significance at 5%, 1%, 0.1% levels respectively.
p(WR): Binomial test for win rate > 50%
p(Ret): One-sample t-test for mean return > 0
""")
    
    # 保存结果
    results_df = pd.DataFrame(all_results)
    results_df.to_csv('statistical_results_all_methods.csv', index=False)
    print("\n结果已保存: statistical_results_all_methods.csv")
    
    return all_results

# 运行
if __name__ == "__main__":
    results = main()