"""
EMIS P2: 日度数据验证（修正版）
V = 股市换手率
Φ = 1/TED Spread（保持原定义）
"""

"""
EMIS P2: 日度数据验证（修复下载问题）
"""

import numpy as np
import pandas as pd
from scipy.optimize import curve_fit
import matplotlib.pyplot as plt
import os
import requests
from io import StringIO
import warnings
warnings.filterwarnings('ignore')

# ============================================
# 缓存配置
# ============================================

CACHE_DIR = './cache_p2_daily/'

def ensure_cache_dir():
    if not os.path.exists(CACHE_DIR):
        os.makedirs(CACHE_DIR)

def get_cache_path(name):
    return os.path.join(CACHE_DIR, f'{name}.csv')

def load_cache(name):
    path = get_cache_path(name)
    if os.path.exists(path):
        print(f"  ✓ 缓存加载: {name}")
        return pd.read_csv(path, index_col=0, parse_dates=True)
    return None

def save_cache(df, name):
    ensure_cache_dir()
    df.to_csv(get_cache_path(name))
    print(f"  ✓ 缓存保存: {name}")

# ============================================
# 数据获取（多种方法）
# ============================================

def download_fred_csv(series_id):
    """从FRED下载"""
    cache = load_cache(f'fred_{series_id}')
    if cache is not None:
        return cache
    
    url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={series_id}"
    print(f"  下载FRED: {series_id}...")
    
    try:
        response = requests.get(url, timeout=30)
        df = pd.read_csv(StringIO(response.text), 
                        index_col=0, parse_dates=True, na_values=['.'])
        df.columns = [series_id]
        save_cache(df, f'fred_{series_id}')
        print(f"    ✓ {len(df)} 条记录")
        return df
    except Exception as e:
        print(f"    ✗ 失败: {e}")
        return None

def download_spy_yfinance():
    """方法1: 用yfinance下载SPY"""
    try:
        import yfinance as yf
        print("  尝试 yfinance...")
        
        spy = yf.download('SPY', start='1993-01-01', progress=False)
        
        if len(spy) > 0:
            print(f"    ✓ yfinance成功: {len(spy)} 条记录")
            return spy
        else:
            print("    ✗ yfinance返回空数据")
            return None
    except Exception as e:
        print(f"    ✗ yfinance失败: {e}")
        return None

def download_spy_stooq():
    """方法2: 从Stooq下载SPY"""
    try:
        print("  尝试 Stooq...")
        url = "https://stooq.com/q/d/l/?s=spy.us&i=d"
        
        response = requests.get(url, timeout=30)
        df = pd.read_csv(StringIO(response.text))
        
        if len(df) > 0:
            df['Date'] = pd.to_datetime(df['Date'])
            df.set_index('Date', inplace=True)
            df = df.sort_index()
            print(f"    ✓ Stooq成功: {len(df)} 条记录")
            return df
        else:
            print("    ✗ Stooq返回空数据")
            return None
    except Exception as e:
        print(f"    ✗ Stooq失败: {e}")
        return None

def download_spy_yahoo_direct():
    """方法3: 直接从Yahoo Finance下载"""
    try:
        print("  尝试 Yahoo直接下载...")
        
        # Yahoo Finance CSV URL
        import time
        end_ts = int(time.time())
        start_ts = 725846400  # 1993-01-01
        
        url = f"https://query1.finance.yahoo.com/v7/finance/download/SPY?period1={start_ts}&period2={end_ts}&interval=1d&events=history"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=30)
        
        if response.status_code == 200:
            df = pd.read_csv(StringIO(response.text))
            df['Date'] = pd.to_datetime(df['Date'])
            df.set_index('Date', inplace=True)
            print(f"    ✓ Yahoo直接下载成功: {len(df)} 条记录")
            return df
        else:
            print(f"    ✗ Yahoo返回状态码: {response.status_code}")
            return None
    except Exception as e:
        print(f"    ✗ Yahoo直接下载失败: {e}")
        return None

def get_spy_data():
    """获取SPY数据（尝试多种方法）"""
    
    # 首先检查缓存
    cache = load_cache('spy_data')
    if cache is not None and len(cache) > 1000:
        return cache
    
    print("\n下载SPY数据（尝试多种方法）...")
    
    # 方法1: yfinance
    spy = download_spy_yfinance()
    
    # 方法2: Stooq
    if spy is None or len(spy) == 0:
        spy = download_spy_stooq()
    
    # 方法3: Yahoo直接
    if spy is None or len(spy) == 0:
        spy = download_spy_yahoo_direct()
    
    if spy is None or len(spy) == 0:
        print("  ❌ 所有方法都失败")
        return None
    
    # 标准化列名
    spy.columns = [c.title() if isinstance(c, str) else c for c in spy.columns]
    
    # 处理MultiIndex（yfinance有时返回这种格式）
    if isinstance(spy.columns, pd.MultiIndex):
        spy.columns = spy.columns.get_level_values(0)
    
    # 确保有必要的列
    required_cols = ['Close', 'Volume']
    for col in required_cols:
        if col not in spy.columns:
            # 尝试找类似的列
            for c in spy.columns:
                if col.lower() in str(c).lower():
                    spy[col] = spy[c]
                    break
    
    # 计算换手率
    if 'Volume' in spy.columns:
        spy['Turnover'] = spy['Volume'] / 900_000_000
        spy['Turnover_MA20'] = spy['Turnover'].rolling(20).mean()
    
    save_cache(spy, 'spy_data')
    
    return spy

def get_daily_data():
    """获取所有日度数据"""
    
    cache = load_cache('p2_daily_combined')
    if cache is not None and len(cache) > 1000:
        return cache
    
    print("\n获取日度数据...")
    
    # 1. SPY
    spy = get_spy_data()
    if spy is None:
        print("  ❌ 无法获取SPY数据")
        return None
    
    # 2. TED Spread
    ted = download_fred_csv('TEDRATE')
    
    # 3. BAA信用利差
    baa = download_fred_csv('BAA10Y')
    
    # 4. VIX
    vix = download_fred_csv('VIXCLS')
    
    # 合并
    print("\n合并数据...")
    
    data = pd.DataFrame(index=spy.index)
    
    if 'Turnover_MA20' in spy.columns:
        data['V'] = spy['Turnover_MA20']
        data['V_raw'] = spy['Turnover']
    elif 'Turnover' in spy.columns:
        data['V'] = spy['Turnover'].rolling(20).mean()
        data['V_raw'] = spy['Turnover']
    
    if 'Volume' in spy.columns:
        data['Volume'] = spy['Volume']
    
    if 'Close' in spy.columns:
        data['Price'] = spy['Close']
    
    # 合并FRED数据
    if ted is not None:
        data = data.join(ted, how='left')
        data.rename(columns={'TEDRATE': 'TED'}, inplace=True)
    
    if baa is not None:
        data = data.join(baa, how='left')
        data.rename(columns={'BAA10Y': 'BAA'}, inplace=True)
    
    if vix is not None:
        data = data.join(vix, how='left')
        data.rename(columns={'VIXCLS': 'VIX'}, inplace=True)
    
    # 前向填充
    data = data.ffill()
    
    # 计算流动性指标
    if 'TED' in data.columns:
        data['Phi_TED'] = 1 / data['TED'].replace(0, np.nan)
    
    if 'BAA' in data.columns:
        data['Phi_BAA'] = 1 / data['BAA'].replace(0, np.nan)
    
    if 'VIX' in data.columns:
        data['Phi_VIX'] = 100 / data['VIX'].replace(0, np.nan)
    
    # 删除缺失
    data = data.dropna(subset=['V'])
    
    save_cache(data, 'p2_daily_combined')
    
    print(f"\n  数据范围: {data.index[0].date()} 到 {data.index[-1].date()}")
    print(f"  样本数: {len(data)}")
    
    return data

# ============================================
# 模型定义
# ============================================

def model_emis(Phi, V0, Phi_c):
    """EMIS模型"""
    ratio = np.clip(Phi_c / Phi, 0, 0.9999)
    return V0 * np.sqrt(1 - ratio**2)

def model_linear(Phi, a, b):
    """线性模型"""
    return a + b * Phi

def model_log(Phi, a, b):
    """对数模型"""
    return a + b * np.log(np.maximum(Phi, 1e-10))

def model_power(Phi, a, b):
    """幂律模型"""
    return a * np.power(np.maximum(Phi, 1e-10), b)

def model_inverse(Phi, a, b):
    """反比模型"""
    return a + b / np.maximum(Phi, 1e-10)

# ============================================
# 拟合
# ============================================

def fit_model(model_func, Phi, V, p0, bounds=None, name=''):
    """拟合模型"""
    try:
        if bounds:
            popt, _ = curve_fit(model_func, Phi, V, p0=p0, bounds=bounds, maxfev=10000)
        else:
            popt, _ = curve_fit(model_func, Phi, V, p0=p0, maxfev=10000)
        
        V_pred = model_func(Phi, *popt)
        
        ss_res = np.sum((V - V_pred)**2)
        ss_tot = np.sum((V - V.mean())**2)
        r2 = 1 - ss_res / ss_tot
        rmse = np.sqrt(np.mean((V - V_pred)**2))
        
        return {
            'params': popt,
            'R2': r2,
            'RMSE': rmse,
            'pred': V_pred,
            'success': True
        }
    except Exception as e:
        return {'success': False, 'R2': np.nan, 'error': str(e)}

def fit_all_models(V, Phi):
    """拟合所有模型"""
    results = {}
    
    V_max, V_min, V_mean = V.max(), V.min(), V.mean()
    Phi_max, Phi_min = Phi.max(), Phi.min()
    
    # EMIS
    res = fit_model(model_emis, Phi, V,
                   p0=[V_max, Phi_min * 0.1],
                   bounds=([0, 0], [V_max * 3, Phi_max]),
                   name='EMIS')
    if res['success']:
        results['EMIS'] = res
        results['EMIS']['param_names'] = ['V0', 'Phi_c']
    
    # Linear
    res = fit_model(model_linear, Phi, V, p0=[V_mean, 0], name='Linear')
    if res['success']:
        results['Linear'] = res
        results['Linear']['param_names'] = ['a', 'b']
    
    # Log
    res = fit_model(model_log, Phi, V, p0=[V_mean, 0], name='Log')
    if res['success']:
        results['Log'] = res
        results['Log']['param_names'] = ['a', 'b']
    
    # Power
    res = fit_model(model_power, Phi, V,
                   p0=[V_mean, 0.1],
                   bounds=([0, -2], [V_max * 3, 2]),
                   name='Power')
    if res['success']:
        results['Power'] = res
        results['Power']['param_names'] = ['a', 'b']
    
    # Inverse
    res = fit_model(model_inverse, Phi, V, p0=[V_mean, 0], name='Inverse')
    if res['success']:
        results['Inverse'] = res
        results['Inverse']['param_names'] = ['a', 'b']
    
    return results

# ============================================
# 可视化
# ============================================

def plot_results(V, Phi, results, data, phi_name, save_path=None):
    """绘制结果"""
    
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    
    sort_idx = np.argsort(Phi)
    Phi_sorted = Phi[sort_idx]
    
    colors = {'EMIS': 'red', 'Linear': 'blue', 'Log': 'green', 
              'Power': 'orange', 'Inverse': 'purple'}
    
    # 左上：散点图
    ax1 = axes[0, 0]
    n_sample = min(3000, len(Phi))
    sample_idx = np.random.choice(len(Phi), n_sample, replace=False)
    ax1.scatter(Phi[sample_idx], V[sample_idx], alpha=0.2, s=5, c='gray')
    
    for model_name, res in results.items():
        if res['success']:
            pred_sorted = res['pred'][sort_idx]
            step = max(1, len(Phi_sorted) // 500)
            ax1.plot(Phi_sorted[::step], pred_sorted[::step],
                    color=colors.get(model_name, 'black'),
                    linewidth=2.5,
                    label=f"{model_name} (R²={res['R2']:.4f})")
    
    ax1.set_xlabel(f'Φ = 1/{phi_name}')
    ax1.set_ylabel('V = Turnover')
    ax1.set_title('(a) Model Fit', fontweight='bold')
    ax1.legend(loc='best', fontsize=9)
    ax1.grid(True, alpha=0.3)
    
    # 右上：R²对比
    ax2 = axes[0, 1]
    valid_models = {k: v for k, v in results.items() if v['success']}
    names = list(valid_models.keys())
    r2_vals = [valid_models[m]['R2'] for m in names]
    
    bars = ax2.bar(names, r2_vals,
                   color=[colors.get(m, 'gray') for m in names],
                   edgecolor='black')
    
    for bar, val in zip(bars, r2_vals):
        ax2.text(bar.get_x() + bar.get_width()/2, max(0, bar.get_height()) + 0.005,
                f'{val:.4f}', ha='center', fontsize=10)
    
    ax2.axhline(y=0, color='black', linewidth=0.5)
    ax2.set_ylabel('R²')
    ax2.set_title('(b) R² Comparison', fontweight='bold')
    ax2.tick_params(axis='x', rotation=45)
    ax2.grid(True, alpha=0.3, axis='y')
    
    # 左下：V时间序列
    ax3 = axes[1, 0]
    ax3.plot(data.index, data['V'], 'b-', alpha=0.3, linewidth=0.5)
    V_ma = data['V'].rolling(60).mean()
    ax3.plot(data.index, V_ma, 'b-', linewidth=1.5, label='Turnover (60d MA)')
    
    ax3.axvspan('2008-09-01', '2009-06-01', alpha=0.3, color='red', label='2008')
    ax3.axvspan('2020-02-01', '2020-05-01', alpha=0.3, color='orange', label='COVID')
    
    ax3.set_ylabel('V (Turnover)')
    ax3.set_title('(c) Velocity Proxy', fontweight='bold')
    ax3.legend(loc='upper right')
    ax3.grid(True, alpha=0.3)
    
    # 右下：Φ时间序列
    ax4 = axes[1, 1]
    phi_col = f'Phi_{phi_name}'
    if phi_col in data.columns:
        ax4.plot(data.index, data[phi_col], 'purple', alpha=0.3, linewidth=0.5)
        Phi_ma = data[phi_col].rolling(60).mean()
        ax4.plot(data.index, Phi_ma, 'purple', linewidth=1.5)
        
        if 'EMIS' in results and results['EMIS']['success']:
            Phi_c = results['EMIS']['params'][1]
            ax4.axhline(y=Phi_c, color='red', linestyle='--', linewidth=2,
                       label=f'Φc = {Phi_c:.4f}')
    
    ax4.set_ylabel(f'Φ = 1/{phi_name}')
    ax4.set_title('(d) Liquidity', fontweight='bold')
    ax4.legend(loc='upper right')
    ax4.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"  ✓ 保存: {save_path}")
    
    plt.show()
    return fig

# ============================================
# 主程序
# ============================================

def main():
    print("="*70)
    print("EMIS P2: 日度数据验证")
    print("="*70)
    print("V = 股市换手率, Φ = 1/TED")
    print("理论: V = V0 × √(1 - (Φc/Φ)²)")
    print("="*70)
    
    # 获取数据
    print("\n[1] 获取数据...")
    data = get_daily_data()
    
    if data is None:
        print("❌ 无法获取数据")
        return None
    
    print(f"\n数据概览:")
    print(f"  样本数: {len(data)}")
    print(f"  时间: {data.index[0].date()} 到 {data.index[-1].date()}")
    
    # 测试
    phi_tests = ['TED', 'BAA', 'VIX']
    all_results = {}
    
    for phi_name in phi_tests:
        phi_col = f'Phi_{phi_name}'
        
        if phi_col not in data.columns:
            print(f"\n  ⚠ {phi_col} 不存在，跳过")
            continue
        
        print(f"\n{'='*70}")
        print(f"[2] V vs 1/{phi_name}")
        print("="*70)
        
        valid = ~data['V'].isna() & ~data[phi_col].isna() & \
                ~np.isinf(data[phi_col]) & (data[phi_col] > 0) & (data['V'] > 0)
        
        df_valid = data[valid].copy()
        V = df_valid['V'].values
        Phi = df_valid[phi_col].values
        
        print(f"  样本: {len(V)}")
        
        # 拟合
        results = fit_all_models(V, Phi)
        
        # 输出
        print(f"\n  {'模型':<12} {'R²':<12} {'RMSE':<15}")
        print("  " + "-"*40)
        
        for name, res in results.items():
            if res['success']:
                print(f"  {name:<12} {res['R2']:<12.4f} {res['RMSE']:<15.6f}")
        
        # 判定
        if 'EMIS' in results and 'Linear' in results:
            r2_emis = results['EMIS']['R2']
            r2_lin = results['Linear']['R2']
            diff = r2_emis - r2_lin
            
            print(f"\n  EMIS R² - Linear R² = {diff:+.4f}")
            
            if diff > 0.05:
                print("  ✅ EMIS显著优于Linear")
            elif diff > 0:
                print("  🔶 EMIS略优")
            else:
                print("  ❌ Linear更好或相当")
        
        all_results[phi_name] = {'models': results, 'data': df_valid, 'V': V, 'Phi': Phi}
        
        # 绘图
        plot_results(V, Phi, results, df_valid, phi_name,
                    save_path=f'p2_daily_{phi_name}.png')
    
    # 汇总
    print("\n" + "="*70)
    print("汇总")
    print("="*70)
    
    for phi_name, res in all_results.items():
        r2_emis = res['models'].get('EMIS', {}).get('R2', np.nan)
        r2_lin = res['models'].get('Linear', {}).get('R2', np.nan)
        print(f"  1/{phi_name}: EMIS={r2_emis:.4f}, Linear={r2_lin:.4f}, 差={r2_emis-r2_lin:+.4f}")
    
    return all_results

if __name__ == "__main__":
    results = main()