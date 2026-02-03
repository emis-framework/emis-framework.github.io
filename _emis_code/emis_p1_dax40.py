"""
修复德国 DAX 验证（带本地缓存）
"""

import numpy as np
import pandas as pd
import yfinance as yf
import time
import os
import warnings
warnings.filterwarnings('ignore')

# ============================================
# 参数设置
# ============================================

START_DATE = '2005-01-01'
TRAIN_END = '2020-01-01'
WINDOW = 60
HORIZON = 30

# 更新的德国股票列表
DAX_TICKERS = [
    'SAP.DE',      # SAP
    'SIE.DE',      # Siemens
    'ALV.DE',      # Allianz
    'DTE.DE',      # Deutsche Telekom
    'BAS.DE',      # BASF
    'BAYN.DE',     # Bayer
    'MBG.DE',      # Mercedes-Benz
    'BMW.DE',      # BMW
    'MUV2.DE',     # Munich Re
    'ADS.DE',      # Adidas
    'VOW3.DE',     # Volkswagen
    'IFX.DE',      # Infineon
    'HEN3.DE',     # Henkel
    'RWE.DE',      # RWE
    'EOAN.DE',     # E.ON
    'DBK.DE',      # Deutsche Bank
    'DHL.DE',      # Deutsche Post
    'CON.DE',      # Continental
    'BEI.DE',      # Beiersdorf
    'HEI.DE',      # HeidelbergCement
    'FRE.DE',      # Fresenius
    'LIN.DE',      # Linde
    'PAH3.DE',     # Porsche
    'SHL.DE',      # Siemens Healthineers
    'QIA.DE',      # QIAGEN
]

# 缓存文件名
STOCK_CACHE = 'stocks_DAX.csv'
INDEX_CACHE = 'index_DAX.csv'
ENTROPY_CACHE = 'entropy_DAX.csv'

# ============================================
# 数据加载函数
# ============================================

def load_stock_data():
    """加载股票数据（优先本地）"""
    
    if os.path.exists(STOCK_CACHE):
        print(f"从本地加载: {STOCK_CACHE}")
        prices = pd.read_csv(STOCK_CACHE, index_col=0, parse_dates=True)
        print(f"加载成功: {len(prices.columns)} 只股票, {len(prices)} 天")
        return prices
    
    print("本地无缓存，开始下载...")
    all_data = []
    
    for i in range(0, len(DAX_TICKERS), 5):
        batch = DAX_TICKERS[i:i+5]
        print(f"  下载 {i+1}-{min(i+5, len(DAX_TICKERS))}/{len(DAX_TICKERS)}: {batch}")
        
        try:
            data = yf.download(batch, start=START_DATE, progress=False)
            if not data.empty:
                if isinstance(data.columns, pd.MultiIndex):
                    all_data.append(data['Close'])
                else:
                    all_data.append(data['Close'])
            time.sleep(1)
        except Exception as e:
            print(f"    错误: {e}")
            time.sleep(3)
    
    if not all_data:
        print("❌ 下载失败")
        return None
    
    prices = pd.concat(all_data, axis=1)
    prices.to_csv(STOCK_CACHE)
    print(f"已保存: {STOCK_CACHE}")
    
    return prices

def load_index_data():
    """加载指数数据（优先本地）"""
    
    if os.path.exists(INDEX_CACHE):
        print(f"从本地加载: {INDEX_CACHE}")
        index = pd.read_csv(INDEX_CACHE, index_col=0, parse_dates=True).iloc[:, 0]
        print(f"加载成功: {len(index)} 天")
        return index
    
    print("下载 DAX 指数...")
    time.sleep(2)
    
    try:
        data = yf.download('^GDAXI', start=START_DATE, progress=False)
        if data.empty:
            print("❌ 下载失败")
            return None
        
        index = data['Close']
        if isinstance(index, pd.DataFrame):
            index = index.iloc[:, 0]
        
        index.to_csv(INDEX_CACHE)
        print(f"已保存: {INDEX_CACHE}")
        return index
        
    except Exception as e:
        print(f"错误: {e}")
        return None

# ============================================
# 计算函数
# ============================================

def compute_returns(prices):
    return np.log(prices / prices.shift(1)).dropna()

def compute_entanglement_entropy(returns, window=60):
    """计算纠缠熵"""
    S_list = []
    dates = []
    N = returns.shape[1]
    
    for t in range(window, len(returns)):
        window_returns = returns.iloc[t-window:t]
        Sigma = window_returns.corr().values
        Sigma = Sigma + np.eye(N) * 1e-6
        det_Sigma = np.linalg.det(Sigma)
        
        if det_Sigma > 0:
            S = -np.log(det_Sigma) / N
        else:
            S = np.nan
        
        S_list.append(S)
        dates.append(returns.index[t])
    
    return pd.Series(S_list, index=dates, name='S')

def test_strategy(S, index, threshold, horizon=30):
    """测试策略"""
    results = []
    
    for t in range(len(S) - horizon):
        date = S.index[t]
        value = S.iloc[t]
        
        if value > threshold and date in index.index:
            idx = index.index.get_loc(date)
            if idx + horizon < len(index):
                ret = np.log(index.iloc[idx + horizon] / index.iloc[idx])
                results.append({
                    'date': date,
                    'S': value,
                    'return': ret,
                    'win': ret > 0
                })
    
    return pd.DataFrame(results) if results else None

# ============================================
# 主程序
# ============================================

def main():
    print("="*60)
    print("德国 DAX 市场验证（修复版）")
    print("="*60)
    print(f"数据起始: {START_DATE}")
    print(f"训练截止: {TRAIN_END}")
    print("="*60)
    
    # 1. 加载股票数据
    prices = load_stock_data()
    if prices is None:
        return None
    
    # 清理数据
    prices = prices.dropna(axis=1, how='all').ffill().dropna()
    print(f"\n有效数据: {len(prices.columns)} 只股票")
    print(f"时间范围: {prices.index.min().date()} - {prices.index.max().date()}")
    print(f"总天数: {len(prices)}")
    
    # 2. 加载指数数据
    index = load_index_data()
    if index is None:
        return None
    
    # 3. 计算纠缠熵
    if os.path.exists(ENTROPY_CACHE):
        print(f"\n从本地加载纠缠熵: {ENTROPY_CACHE}")
        S = pd.read_csv(ENTROPY_CACHE, index_col=0, parse_dates=True).iloc[:, 0]
    else:
        print("\n计算纠缠熵...")
        returns = compute_returns(prices)
        S = compute_entanglement_entropy(returns, WINDOW)
        S.to_csv(ENTROPY_CACHE)
        print(f"已保存: {ENTROPY_CACHE}")
    
    print(f"纠缠熵范围: [{S.min():.2f}, {S.max():.2f}]")
    print(f"均值: {S.mean():.2f}, 标准差: {S.std():.2f}")
    
    # 4. 对齐时间
    common_idx = S.index.intersection(index.index)
    S = S.loc[common_idx]
    index = index.loc[common_idx]
    
    print(f"\n对齐后数据: {len(common_idx)} 天")
    
    # 5. 样本划分
    train_mask = S.index < TRAIN_END
    test_mask = S.index >= TRAIN_END
    
    S_train = S[train_mask]
    S_test = S[test_mask]
    index_train = index[train_mask]
    index_test = index[test_mask]
    
    print(f"\n训练集: {len(S_train)} 天")
    if len(S_train) > 0:
        print(f"  范围: {S_train.index.min().date()} - {S_train.index.max().date()}")
    
    print(f"测试集: {len(S_test)} 天")
    if len(S_test) > 0:
        print(f"  范围: {S_test.index.min().date()} - {S_test.index.max().date()}")
    
    # 检查数据量
    if len(S_train) < 100:
        print(f"\n⚠️ 训练集只有 {len(S_train)} 天，不足100天")
        print("尝试使用全部数据的前70%作为训练集...")
        
        # 备选方案：按比例划分
        split_idx = int(len(S) * 0.7)
        S_train = S.iloc[:split_idx]
        S_test = S.iloc[split_idx:]
        index_train = index.iloc[:split_idx]
        index_test = index.iloc[split_idx:]
        
        print(f"\n新划分:")
        print(f"训练集: {len(S_train)} 天 ({S_train.index.min().date()} - {S_train.index.max().date()})")
        print(f"测试集: {len(S_test)} 天 ({S_test.index.min().date()} - {S_test.index.max().date()})")
    
    # 6. 计算阈值
    threshold = S_train.quantile(0.90)
    print(f"\n阈值 (90%分位): {threshold:.4f}")
    
    # 7. 测试策略
    print("\n" + "="*60)
    print("策略测试结果")
    print("="*60)
    
    train_results = test_strategy(S_train, index_train, threshold, HORIZON)
    test_results = test_strategy(S_test, index_test, threshold, HORIZON)
    
    print(f"\n{'集合':<10} {'交易次数':<10} {'胜率':<10} {'平均收益':<12} {'累计收益':<12}")
    print("-"*55)
    
    if train_results is not None and len(train_results) > 0:
        train_wr = train_results['win'].mean()
        train_ret = train_results['return'].mean()
        train_cum = train_results['return'].sum()
        print(f"{'训练集':<10} {len(train_results):<10} {train_wr:<10.1%} {train_ret:<12.1%} {train_cum:<12.1%}")
    else:
        print(f"{'训练集':<10} {'无信号':<10}")
    
    if test_results is not None and len(test_results) > 0:
        test_wr = test_results['win'].mean()
        test_ret = test_results['return'].mean()
        test_cum = test_results['return'].sum()
        print(f"{'测试集':<10} {len(test_results):<10} {test_wr:<10.1%} {test_ret:<12.1%} {test_cum:<12.1%}")
        
        # 保存结果
        test_results.to_csv('emis_results_DAX.csv', index=False)
        print(f"\n结果已保存: emis_results_DAX.csv")
        
        # 结论
        print("\n" + "="*60)
        if test_wr > 0.6:
            print("✅ 德国市场验证成功！")
        elif test_wr > 0.5:
            print("🔶 德国市场效果一般，优于随机")
        else:
            print("❌ 德国市场验证失败")
        print("="*60)
        
    else:
        print(f"{'测试集':<10} {'无信号':<10}")
    
    # 8. 汇总三个市场
    print("\n" + "="*60)
    print("全球验证汇总（更新版）")
    print("="*60)
    
    print(f"\n{'市场':<20} {'测试交易':<10} {'胜率':<10} {'平均收益':<12}")
    print("-"*55)
    print(f"{'美国 S&P 500':<20} {'243':<10} {'81.5%':<10} {'5.1%':<12}")
    print(f"{'日本 Nikkei 225':<20} {'160':<10} {'90.6%':<10} {'5.8%':<12}")
    
    if test_results is not None and len(test_results) > 0:
        print(f"{'德国 DAX':<20} {len(test_results):<10} {test_wr:<10.1%} {test_ret:<12.1%}")
        
        # 计算三市场平均
        all_wr = [0.815, 0.906, test_wr]
        all_ret = [0.051, 0.058, test_ret]
        print("-"*55)
        print(f"{'平均':<20} {'':<10} {np.mean(all_wr):<10.1%} {np.mean(all_ret):<12.1%}")
    
    return test_results

# ============================================
# 运行
# ============================================

if __name__ == "__main__":
    results = main()