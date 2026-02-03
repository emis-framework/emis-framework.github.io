"""
EMIS P1 全球验证：美国 + 欧洲 + 亚洲
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

START_DATE = '2010-01-01'
TRAIN_END = '2020-01-01'
WINDOW = 60
HORIZON = 30

# ============================================
# 三个市场的股票池
# ============================================

MARKETS = {
    'US': {
        'name': 'S&P 500 (美国)',
        'index': '^GSPC',
        'tickers': [
            'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META',
            'NVDA', 'BRK-B', 'JPM', 'JNJ', 'V',
            'PG', 'UNH', 'HD', 'MA', 'DIS',
            'PYPL', 'VZ', 'ADBE', 'NFLX', 'CRM',
            'INTC', 'CMCSA', 'PFE', 'KO', 'PEP',
            'T', 'MRK', 'WMT', 'ABT', 'CVX',
            'XOM', 'BA', 'CSCO', 'WFC', 'C',
            'ORCL', 'ACN', 'COST', 'NKE', 'MCD',
            'DHR', 'NEE', 'LLY', 'TXN', 'QCOM',
            'LOW', 'UPS', 'BMY', 'AMGN', 'IBM'
        ]
    },
    'EU': {
        'name': 'DAX 40 (德国)',
        'index': '^GDAXI',
        'tickers': [
            'SAP.DE', 'SIE.DE', 'ALV.DE', 'DTE.DE', 'BAS.DE',
            'BAYN.DE', 'MBG.DE', 'BMW.DE', 'MUV2.DE', 'ADS.DE',
            'AIR.DE', 'DPW.DE', 'DB1.DE', 'VOW3.DE', 'IFX.DE',
            'HEN3.DE', 'RWE.DE', 'EOAN.DE', 'FRE.DE', 'CON.DE',
            'BEI.DE', 'HEI.DE', 'MRK.DE', 'VNA.DE', 'FME.DE',
            'MTX.DE', 'SY1.DE', 'ENR.DE', 'ZAL.DE', 'PUM.DE'
        ]
    },
    'ASIA': {
        'name': 'Nikkei 225 (日本)',
        'index': '^N225',
        'tickers': [
            '7203.T', '6758.T', '9984.T', '6861.T', '8306.T',
            '9432.T', '6501.T', '7267.T', '4502.T', '6902.T',
            '7751.T', '8035.T', '6367.T', '4063.T', '6954.T',
            '7974.T', '8316.T', '9433.T', '6981.T', '4519.T',
            '8411.T', '6503.T', '7201.T', '2914.T', '3382.T',
            '4568.T', '6702.T', '8031.T', '9022.T', '6326.T'
        ]
    }
}

# ============================================
# 数据加载函数
# ============================================

def load_market_data(market_key, force_download=False):
    """加载某个市场的数据"""
    market = MARKETS[market_key]
    
    stock_file = f'stocks_{market_key}.csv'
    index_file = f'index_{market_key}.csv'
    
    # 加载股票数据
    if os.path.exists(stock_file) and not force_download:
        print(f"从本地加载: {stock_file}")
        prices = pd.read_csv(stock_file, index_col=0, parse_dates=True)
    else:
        print(f"下载 {market['name']} 股票...")
        all_data = []
        batch_size = 10
        
        for i in range(0, len(market['tickers']), batch_size):
            batch = market['tickers'][i:i+batch_size]
            print(f"  下载 {i+1}-{min(i+batch_size, len(market['tickers']))}...")
            try:
                data = yf.download(batch, start=START_DATE, progress=False)
                if not data.empty:
                    if 'Close' in data.columns:
                        all_data.append(data['Close'])
                    elif isinstance(data.columns, pd.MultiIndex):
                        all_data.append(data['Close'])
                time.sleep(1)
            except Exception as e:
                print(f"    错误: {e}")
                time.sleep(3)
        
        if all_data:
            prices = pd.concat(all_data, axis=1) if len(all_data) > 1 else all_data[0]
            prices.to_csv(stock_file)
            print(f"  已保存: {stock_file}")
        else:
            return None, None
    
    # 加载指数数据
    if os.path.exists(index_file) and not force_download:
        print(f"从本地加载: {index_file}")
        index = pd.read_csv(index_file, index_col=0, parse_dates=True).iloc[:, 0]
    else:
        print(f"下载 {market['name']} 指数...")
        time.sleep(2)
        try:
            data = yf.download(market['index'], start=START_DATE, progress=False)
            index = data['Close']
            if isinstance(index, pd.DataFrame):
                index = index.iloc[:, 0]
            index.to_csv(index_file)
            print(f"  已保存: {index_file}")
        except Exception as e:
            print(f"  错误: {e}")
            return prices, None
    
    # 清理数据
    if prices is not None:
        prices = prices.dropna(axis=1, how='all').ffill().dropna()
    
    return prices, index

# ============================================
# 计算函数
# ============================================

def compute_returns(prices):
    return np.log(prices / prices.shift(1)).dropna()

def compute_entanglement_entropy(returns, window=60):
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
    
    return pd.Series(S_list, index=dates)

def test_strategy(S, index, threshold, horizon=30):
    """测试策略效果"""
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
# 验证单个市场
# ============================================

def validate_market(market_key):
    """验证单个市场"""
    market = MARKETS[market_key]
    print(f"\n{'='*60}")
    print(f"验证市场: {market['name']}")
    print('='*60)
    
    # 加载数据
    prices, index = load_market_data(market_key)
    
    if prices is None or index is None:
        print("❌ 数据加载失败")
        return None
    
    if len(prices.columns) < 10:
        print(f"❌ 股票数量不足: {len(prices.columns)}")
        return None
    
    print(f"\n有效数据: {len(prices.columns)} 只股票, {len(prices)} 天")
    
    # 计算纠缠熵
    print("计算纠缠熵...")
    returns = compute_returns(prices)
    S = compute_entanglement_entropy(returns, window=WINDOW)
    
    # 保存
    S.to_csv(f'entropy_{market_key}.csv')
    
    print(f"纠缠熵范围: [{S.min():.2f}, {S.max():.2f}]")
    
    # 对齐时间
    common_idx = S.index.intersection(index.index)
    S = S.loc[common_idx]
    index = index.loc[common_idx]
    
    # 样本划分
    train_mask = S.index < TRAIN_END
    test_mask = S.index >= TRAIN_END
    
    S_train = S[train_mask]
    S_test = S[test_mask]
    index_train = index[train_mask]
    index_test = index[test_mask]
    
    print(f"\n训练集: {len(S_train)} 天")
    print(f"测试集: {len(S_test)} 天")
    
    if len(S_train) < 100 or len(S_test) < 100:
        print("❌ 数据量不足")
        return None
    
    # 计算阈值
    threshold = S_train.quantile(0.90)
    print(f"阈值 (90%分位): {threshold:.4f}")
    
    # 训练集效果
    train_results = test_strategy(S_train, index_train, threshold, HORIZON)
    
    # 测试集效果
    test_results = test_strategy(S_test, index_test, threshold, HORIZON)
    
    # 汇总结果
    result = {
        'market': market['name'],
        'n_stocks': len(prices.columns),
        'threshold': threshold,
        'train_n': len(train_results) if train_results is not None else 0,
        'train_wr': train_results['win'].mean() if train_results is not None and len(train_results) > 0 else 0,
        'train_ret': train_results['return'].mean() if train_results is not None and len(train_results) > 0 else 0,
        'test_n': len(test_results) if test_results is not None else 0,
        'test_wr': test_results['win'].mean() if test_results is not None and len(test_results) > 0 else 0,
        'test_ret': test_results['return'].mean() if test_results is not None and len(test_results) > 0 else 0,
    }
    
    # 打印结果
    print(f"\n{'集合':<10} {'交易次数':<10} {'胜率':<10} {'平均收益':<12}")
    print("-"*45)
    print(f"{'训练集':<10} {result['train_n']:<10} {result['train_wr']:<10.1%} {result['train_ret']:<12.1%}")
    print(f"{'测试集':<10} {result['test_n']:<10} {result['test_wr']:<10.1%} {result['test_ret']:<12.1%}")
    
    if result['test_wr'] > 0.6:
        print("\n✅ 样本外验证成功！")
    elif result['test_wr'] > 0.5:
        print("\n🔶 样本外效果一般")
    else:
        print("\n❌ 样本外验证失败")
    
    return result

# ============================================
# 主程序
# ============================================

def main():
    print("="*60)
    print("EMIS P1 全球验证")
    print("="*60)
    print(f"数据范围: {START_DATE} - 今天")
    print(f"训练集截止: {TRAIN_END}")
    print(f"验证市场: 美国, 德国, 日本")
    
    all_results = []
    
    for market_key in ['US', 'EU', 'ASIA']:
        result = validate_market(market_key)
        if result:
            all_results.append(result)
    
    # ============================================
    # 汇总对比
    # ============================================
    
    print("\n" + "="*60)
    print("全球验证汇总")
    print("="*60)
    
    print(f"\n{'市场':<20} {'股票数':<8} {'测试交易':<10} {'胜率':<10} {'平均收益':<12}")
    print("-"*60)
    
    for r in all_results:
        print(f"{r['market']:<20} {r['n_stocks']:<8} {r['test_n']:<10} {r['test_wr']:<10.1%} {r['test_ret']:<12.1%}")
    
    # 计算平均
    if len(all_results) > 0:
        avg_wr = np.mean([r['test_wr'] for r in all_results])
        avg_ret = np.mean([r['test_ret'] for r in all_results])
        
        print("-"*60)
        print(f"{'平均':<20} {'':<8} {'':<10} {avg_wr:<10.1%} {avg_ret:<12.1%}")
    
    # 最终结论
    print("\n" + "="*60)
    print("最终结论")
    print("="*60)
    
    success_count = sum(1 for r in all_results if r['test_wr'] > 0.6)
    
    if success_count == len(all_results):
        print("\n✅ 全部市场验证成功！EMIS 策略具有全球有效性")
    elif success_count > len(all_results) / 2:
        print(f"\n🔶 {success_count}/{len(all_results)} 个市场验证成功")
    else:
        print("\n❌ 多数市场验证失败")
    
    # 保存结果
    results_df = pd.DataFrame(all_results)
    results_df.to_csv('global_validation_results.csv', index=False)
    print("\n结果已保存: global_validation_results.csv")
    
    return all_results

# ============================================
# 运行
# ============================================

if __name__ == "__main__":
    results = main()