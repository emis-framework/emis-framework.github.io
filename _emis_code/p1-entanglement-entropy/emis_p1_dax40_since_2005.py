"""
德国 DAX 验证（修复时区问题 v3）
"""

import numpy as np
import pandas as pd
import yfinance as yf
import time
import os
import warnings
warnings.filterwarnings('ignore')

# ============================================
# 参数
# ============================================

PROJECT_DIR     = './_emis_code/p1-entanglement-entropy/'
CACHE_DIR       = os.path.join(PROJECT_DIR, 'cache')
DATA_FIGURE_DIR = os.path.join(PROJECT_DIR, 'data-figure')

# 缓存文件
STOCK_CACHE = os.path.join(CACHE_DIR,'stocks_DAX_v2.csv')
INDEX_CACHE = os.path.join(CACHE_DIR,'index_DAX.csv')
ENTROPY_CACHE = os.path.join(CACHE_DIR,'entropy_DAX_historical.csv')  


START_DATE = '2005-01-01'
TRAIN_END = '2020-01-01'
WINDOW = 60
HORIZON = 30




# ============================================
# ★★★ 修复的时区处理函数 ★★★
# ============================================

def fix_timezone(df):
    """
    修复时区问题 - 简单粗暴版
    """
    # 如果是 Series，转为 DataFrame 处理
    is_series = isinstance(df, pd.Series)
    if is_series:
        name = df.name
        df = df.to_frame()
    
    # 重置索引，把日期变成普通列
    df = df.reset_index()
    
    # 第一列是日期，转为字符串再转回日期（去掉时区）
    date_col = df.columns[0]
    df[date_col] = pd.to_datetime(df[date_col].astype(str).str[:10])
    
    # 设回索引
    df = df.set_index(date_col)
    
    # 如果原来是 Series，转回去
    if is_series:
        return df.iloc[:, 0].rename(name)
    return df

# ============================================
# 计算函数
# ============================================

def compute_returns(prices):
    return np.log(prices / prices.shift(1)).dropna()

def compute_entropy(returns, window=60):
    S_list = []
    dates = []
    N = returns.shape[1]
    
    for t in range(window, len(returns)):
        win = returns.iloc[t-window:t]
        Sigma = win.corr().values + np.eye(N) * 1e-6
        det = np.linalg.det(Sigma)
        S = -np.log(det) / N if det > 0 else np.nan
        S_list.append(S)
        dates.append(returns.index[t])
    
    return pd.Series(S_list, index=dates)

def test_strategy(S, index, threshold, horizon=30):
    results = []
    for t in range(len(S) - horizon):
        date = S.index[t]
        if S.iloc[t] > threshold and date in index.index:
            idx = index.index.get_loc(date)
            if idx + horizon < len(index):
                ret = np.log(index.iloc[idx + horizon] / index.iloc[idx])
                results.append({'return': ret, 'win': ret > 0})
    return pd.DataFrame(results) if results else None

# ============================================
# 主程序
# ============================================

def main():
    print("="*60)
    print("德国 DAX 验证（时区修复 v3）")
    print("="*60)
    
    # 加载股票数据
    if os.path.exists(STOCK_CACHE):
        print(f"从本地加载: {STOCK_CACHE}")
        prices = pd.read_csv(STOCK_CACHE, index_col=0, parse_dates=True)
        print(f"成功: {len(prices.columns)} 只股票, {len(prices)} 天")
    else:
        print("❌ 找不到缓存文件")
        return
    
    # ★★★ 修复时区 ★★★
    prices = fix_timezone(prices)
    prices = prices.dropna(axis=1, how='all').ffill().dropna()
    
    print(f"\n有效: {len(prices.columns)} 只股票, {len(prices)} 天")
    print(f"范围: {prices.index.min()} - {prices.index.max()}")
    
    # 加载指数
    if os.path.exists(INDEX_CACHE):
        print(f"从本地加载: {INDEX_CACHE}")
        index = pd.read_csv(INDEX_CACHE, index_col=0, parse_dates=True).iloc[:, 0]
    else:
        print("❌ 找不到指数文件")
        return
    
    # ★★★ 修复时区 ★★★
    index = fix_timezone(index)
    
    print(f"指数: {len(index)} 天")
    
    # ★★★ 计算或加载纠缠熵 ★★★
    if os.path.exists(ENTROPY_CACHE):
        print(f"\n从本地加载纠缠熵: {ENTROPY_CACHE}")
        S = pd.read_csv(ENTROPY_CACHE, index_col=0, parse_dates=True).iloc[:, 0]
        S = fix_timezone(S)
    else:
        print("\n计算纠缠熵...")
        returns = compute_returns(prices)
        S = compute_entropy(returns, WINDOW)
        
        # ★★★ 保存纠缠熵 ★★★
        S.to_csv(ENTROPY_CACHE)
        print(f"已保存: {ENTROPY_CACHE}")
    
    print(f"纠缠熵范围: [{S.min():.2f}, {S.max():.2f}]")
    print(f"纠缠熵天数: {len(S)}")
    
    # 对齐
    common = S.index.intersection(index.index)
    print(f"对齐后: {len(common)} 天")
    
    S = S.loc[common]
    index = index.loc[common]
    
    # 划分
    train_end_dt = pd.to_datetime(TRAIN_END)
    S_train = S[S.index < train_end_dt]
    S_test = S[S.index >= train_end_dt]
    idx_train = index[index.index < train_end_dt]
    idx_test = index[index.index >= train_end_dt]
    
    print(f"\n训练集: {len(S_train)} 天")
    print(f"测试集: {len(S_test)} 天")
    
    if len(S_train) < 100:
        print("⚠️ 使用70/30划分")
        n = int(len(S) * 0.7)
        S_train, S_test = S.iloc[:n], S.iloc[n:]
        idx_train, idx_test = index.iloc[:n], index.iloc[n:]
        print(f"新训练集: {len(S_train)} 天")
        print(f"新测试集: {len(S_test)} 天")
    
    # 阈值
    threshold = S_train.quantile(0.90)
    print(f"\n阈值: {threshold:.4f}")
    
    # 测试
    train_res = test_strategy(S_train, idx_train, threshold, HORIZON)
    test_res = test_strategy(S_test, idx_test, threshold, HORIZON)
    
    print(f"\n{'集合':<8} {'次数':<8} {'胜率':<10} {'收益':<10}")
    print("-"*40)
    
    if train_res is not None and len(train_res) > 0:
        print(f"{'训练':<8} {len(train_res):<8} {train_res['win'].mean():<10.1%} {train_res['return'].mean():<10.1%}")
    
    if test_res is not None and len(test_res) > 0:
        wr = test_res['win'].mean()
        ret = test_res['return'].mean()
        print(f"{'测试':<8} {len(test_res):<8} {wr:<10.1%} {ret:<10.1%}")
        
        print("\n" + "="*60)
        if wr > 0.6:
            print("✅ 德国验证成功！")
        elif wr > 0.5:
            print("🔶 效果一般")
        else:
            print("❌ 失败")
        print("="*60)
    
    # 全球汇总
    print("\n" + "="*60)
    print("全球汇总")
    print("="*60)
    print(f"\n{'市场':<18} {'交易':<8} {'胜率':<10} {'收益':<10}")
    print("-"*50)
    print(f"{'美国 S&P 500':<18} {'243':<8} {'81.5%':<10} {'5.1%':<10}")
    print(f"{'日本 Nikkei':<18} {'160':<8} {'90.6%':<10} {'5.8%':<10}")
    
    if test_res is not None and len(test_res) > 0:
        print(f"{'德国 DAX':<18} {len(test_res):<8} {wr:<10.1%} {ret:<10.1%}")
        print("-"*50)
        avg_wr = np.mean([0.815, 0.906, wr])
        avg_ret = np.mean([0.051, 0.058, ret])
        print(f"{'全球平均':<18} {'':<8} {avg_wr:<10.1%} {avg_ret:<10.1%}")

if __name__ == "__main__":
    main()