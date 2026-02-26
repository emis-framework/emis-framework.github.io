"""
EMIS P2: 季度数据验证（修复日期匹配）
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

CACHE_DIR = './cache_p2_quarterly/'

def ensure_cache_dir():
    if not os.path.exists(CACHE_DIR):
        os.makedirs(CACHE_DIR)

def download_fred(series_id):
    """下载FRED数据"""
    cache_path = os.path.join(CACHE_DIR, f'{series_id}.csv')
    
    if os.path.exists(cache_path):
        print(f"  ✓ 缓存: {series_id}")
        return pd.read_csv(cache_path, index_col=0, parse_dates=True)
    
    url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={series_id}"
    print(f"  下载: {series_id}...")
    
    try:
        response = requests.get(url, timeout=30)
        df = pd.read_csv(StringIO(response.text), index_col=0, parse_dates=True, na_values=['.'])
        df.columns = [series_id]
        
        ensure_cache_dir()
        df.to_csv(cache_path)
        print(f"    ✓ {len(df)} 条")
        return df
    except Exception as e:
        print(f"    ✗ 失败: {e}")
        return None

def get_quarterly_data():
    """获取季度数据（修复日期匹配）"""
    
    print("\n获取原始数据...")
    
    # 下载所有数据
    m2v = download_fred('M2V')
    ted = download_fred('TEDRATE')
    baa = download_fred('BAA10Y')
    vix = download_fred('VIXCLS')
    fedfunds = download_fred('FEDFUNDS')
    gs10 = download_fred('GS10')
    
    if m2v is None:
        return None
    
    print("\n处理数据...")
    
    # 关键修复：统一转换为季度周期（Period），再对齐
    
    # 1. M2V转为季度Period
    m2v_q = m2v.copy()
    m2v_q.index = m2v_q.index.to_period('Q')
    m2v_q.columns = ['V']
    print(f"  M2V: {len(m2v_q)} 季度")
    
    # 2. 其他数据重采样到季度，也转为Period
    def to_quarterly(df, name):
        if df is None or len(df) == 0:
            return None
        # 重采样到季度末取平均
        q = df.resample('QE').mean()
        # 转为季度Period
        q.index = q.index.to_period('Q')
        q.columns = [name]
        print(f"  {name}: {len(q)} 季度")
        return q
    
    ted_q = to_quarterly(ted, 'TED')
    baa_q = to_quarterly(baa, 'BAA')
    vix_q = to_quarterly(vix, 'VIX')
    fedfunds_q = to_quarterly(fedfunds, 'FEDFUNDS')
    gs10_q = to_quarterly(gs10, 'GS10')
    
    # 3. 合并（现在index都是Period，可以正确匹配）
    print("\n合并数据...")
    data = m2v_q.copy()
    
    for df in [ted_q, baa_q, vix_q, fedfunds_q, gs10_q]:
        if df is not None:
            data = data.join(df, how='left')
    
    # 转回DatetimeIndex便于绘图
    data.index = data.index.to_timestamp()
    
    print(f"\n合并后列: {list(data.columns)}")
    print(f"合并后行数: {len(data)}")
    
    # 检查每列有效数据
    print("\n每列有效数据:")
    for col in data.columns:
        valid = data[col].notna().sum()
        print(f"  {col}: {valid}/{len(data)}")
    
    # 计算Φ
    if 'TED' in data.columns:
        data['Phi_TED'] = 1 / data['TED'].replace(0, np.nan)
    
    if 'BAA' in data.columns:
        data['Phi_BAA'] = 1 / data['BAA'].replace(0, np.nan)
    
    if 'VIX' in data.columns:
        data['Phi_VIX'] = 100 / data['VIX'].replace(0, np.nan)
    
    if 'FEDFUNDS' in data.columns and 'GS10' in data.columns:
        data['SPREAD'] = data['GS10'] - data['FEDFUNDS']
        data['Phi_SPREAD'] = 1 / np.abs(data['SPREAD']).replace(0, np.nan)
    
    print(f"\n最终数据: {len(data)} 季度")
    print(f"时间范围: {data.index[0].date()} 到 {data.index[-1].date()}")
    
    return data

# ============================================
# 模型
# ============================================

def model_emis(Phi, V0, Phi_c):
    ratio = np.clip(Phi_c / Phi, 0, 0.9999)
    return V0 * np.sqrt(1 - ratio**2)

def model_linear(Phi, a, b):
    return a + b * Phi

def model_log(Phi, a, b):
    return a + b * np.log(np.maximum(Phi, 1e-10))

def model_power(Phi, a, b):
    return a * np.power(np.maximum(Phi, 1e-10), b)

def model_inverse(Phi, a, b):
    return a + b / np.maximum(Phi, 1e-10)

def fit_model(func, Phi, V, p0, bounds=None):
    try:
        if bounds:
            popt, _ = curve_fit(func, Phi, V, p0=p0, bounds=bounds, maxfev=10000)
        else:
            popt, _ = curve_fit(func, Phi, V, p0=p0, maxfev=10000)
        
        pred = func(Phi, *popt)
        ss_res = np.sum((V - pred)**2)
        ss_tot = np.sum((V - V.mean())**2)
        r2 = 1 - ss_res / ss_tot
        rmse = np.sqrt(np.mean((V - pred)**2))
        
        return {'params': popt, 'R2': r2, 'RMSE': rmse, 'pred': pred, 'success': True}
    except Exception as e:
        return {'success': False, 'R2': np.nan, 'error': str(e)}

def fit_all(V, Phi):
    results = {}
    
    # EMIS
    res = fit_model(model_emis, Phi, V, 
                   p0=[V.max(), Phi.min()*0.5],
                   bounds=([0, 0], [V.max()*3, Phi.max()]))
    if res['success']:
        results['EMIS'] = res
    
    # Linear
    res = fit_model(model_linear, Phi, V, p0=[V.mean(), 0])
    if res['success']:
        results['Linear'] = res
    
    # Log
    res = fit_model(model_log, Phi, V, p0=[V.mean(), 0])
    if res['success']:
        results['Log'] = res
    
    # Power
    res = fit_model(model_power, Phi, V, p0=[V.mean(), 0.1], 
                   bounds=([0, -2], [V.max()*3, 2]))
    if res['success']:
        results['Power'] = res
    
    # Inverse
    res = fit_model(model_inverse, Phi, V, p0=[V.mean(), 0])
    if res['success']:
        results['Inverse'] = res
    
    return results

# ============================================
# 主程序
# ============================================

def main():
    print("="*70)
    print("EMIS P2: 季度数据验证（日期匹配修复版）")
    print("="*70)
    
    # 清除缓存重新下载
    import shutil
    if os.path.exists(CACHE_DIR):
        shutil.rmtree(CACHE_DIR)
        print("已清除旧缓存\n")
    
    data = get_quarterly_data()
    
    if data is None:
        return None
    
    # 显示数据样本
    print("\n" + "="*70)
    print("数据样本（最近10季度）")
    print("="*70)
    print(data.tail(10))
    
    # 测试
    phi_cols = [c for c in data.columns if c.startswith('Phi_')]
    print(f"\n找到的Φ指标: {phi_cols}")
    
    all_results = {}
    
    for phi_col in phi_cols:
        print(f"\n{'='*70}")
        print(f"测试: V (M2V) vs {phi_col}")
        print("="*70)
        
        valid = data['V'].notna() & data[phi_col].notna() & \
                (data[phi_col] > 0) & np.isfinite(data[phi_col])
        
        df = data[valid].copy()
        
        if len(df) < 20:
            print(f"  ⚠ 有效数据不足: {len(df)} 条")
            continue
        
        V = df['V'].values
        Phi = df[phi_col].values
        
        print(f"  样本: {len(V)} 季度")
        print(f"  V: [{V.min():.3f}, {V.max():.3f}]")
        print(f"  Φ: [{Phi.min():.4f}, {Phi.max():.4f}]")
        
        # 相关性
        corr = np.corrcoef(V, Phi)[0, 1]
        print(f"  Corr(V, Φ): {corr:.4f}")
        
        # 拟合
        results = fit_all(V, Phi)
        
        print(f"\n  {'模型':<12} {'R²':<12} {'RMSE':<12}")
        print("  " + "-"*35)
        for name, res in sorted(results.items(), key=lambda x: -x[1].get('R2', -999)):
            if res['success']:
                print(f"  {name:<12} {res['R2']:<12.4f} {res['RMSE']:<12.4f}")
        
        # 判定
        r2_emis = results.get('EMIS', {}).get('R2', np.nan)
        r2_lin = results.get('Linear', {}).get('R2', np.nan)
        
        if not np.isnan(r2_emis) and not np.isnan(r2_lin):
            diff = r2_emis - r2_lin
            print(f"\n  EMIS R² - Linear R² = {diff:+.4f}")
            if diff > 0.05:
                print("  ✅ EMIS显著优于Linear")
            elif diff > 0:
                print("  🔶 EMIS略优")
            else:
                print("  ❌ Linear更好或相当")
        
        all_results[phi_col] = {'data': df, 'V': V, 'Phi': Phi, 'models': results}
        
        # 绘图
        fig, axes = plt.subplots(1, 2, figsize=(14, 5))
        
        ax1 = axes[0]
        ax1.scatter(Phi, V, alpha=0.6, s=40, c='gray', label='Data')
        
        sort_idx = np.argsort(Phi)
        colors = {'EMIS': 'red', 'Linear': 'blue', 'Log': 'green', 
                  'Power': 'orange', 'Inverse': 'purple'}
        
        for name, res in results.items():
            if res['success']:
                ax1.plot(Phi[sort_idx], res['pred'][sort_idx],
                        color=colors.get(name, 'black'),
                        linewidth=2.5,
                        label=f"{name} (R²={res['R2']:.3f})")
        
        ax1.set_xlabel(f'Φ = {phi_col.replace("Phi_", "1/")}', fontsize=11)
        ax1.set_ylabel('V (M2 Velocity)', fontsize=11)
        ax1.set_title('Model Fit Comparison', fontweight='bold')
        ax1.legend(loc='best')
        ax1.grid(True, alpha=0.3)
        
        ax2 = axes[1]
        ax2.plot(df.index, V, 'b-', linewidth=1.5, label='M2V')
        ax2.set_ylabel('V (M2 Velocity)', color='b', fontsize=11)
        ax2.tick_params(axis='y', labelcolor='b')
        
        ax2_twin = ax2.twinx()
        ax2_twin.plot(df.index, Phi, 'r-', linewidth=1.5, alpha=0.7, label='Φ')
        ax2_twin.set_ylabel(f'Φ ({phi_col})', color='r', fontsize=11)
        ax2_twin.tick_params(axis='y', labelcolor='r')
        
        ax2.axvspan('2008-01-01', '2009-12-31', alpha=0.2, color='gray')
        ax2.axvspan('2020-01-01', '2021-06-01', alpha=0.2, color='gray')
        
        ax2.set_title('Time Series', fontweight='bold')
        ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(f'p2_quarterly_{phi_col}.png', dpi=300, bbox_inches='tight')
        print(f"  ✓ 保存: p2_quarterly_{phi_col}.png")
        plt.show()
    
    # 汇总
    print("\n" + "="*70)
    print("汇总报告")
    print("="*70)
    
    print(f"\n{'指标':<15} {'样本':<8} {'EMIS':<10} {'Linear':<10} {'最佳':<10} {'差值':<10}")
    print("-"*65)
    
    for phi_col, res in all_results.items():
        models = res['models']
        n = len(res['V'])
        r2_emis = models.get('EMIS', {}).get('R2', np.nan)
        r2_lin = models.get('Linear', {}).get('R2', np.nan)
        
        valid_models = {k: v for k, v in models.items() if v['success']}
        if valid_models:
            best = max(valid_models.items(), key=lambda x: x[1]['R2'])
            best_name = best[0]
        else:
            best_name = 'N/A'
        
        diff = r2_emis - r2_lin if not np.isnan(r2_emis) else np.nan
        
        r2_emis_str = f"{r2_emis:.4f}" if not np.isnan(r2_emis) else "N/A"
        r2_lin_str = f"{r2_lin:.4f}" if not np.isnan(r2_lin) else "N/A"
        diff_str = f"{diff:+.4f}" if not np.isnan(diff) else "N/A"
        
        print(f"{phi_col:<15} {n:<8} {r2_emis_str:<10} {r2_lin_str:<10} {best_name:<10} {diff_str:<10}")
    
    # P2判定
    print("\n" + "="*70)
    print("P2 预测判定")
    print("="*70)
    
    # 主要看TED
    if 'Phi_TED' in all_results:
        models = all_results['Phi_TED']['models']
        r2_emis = models.get('EMIS', {}).get('R2', 0)
        r2_lin = models.get('Linear', {}).get('R2', 0)
        diff = r2_emis - r2_lin
        
        print(f"\n主指标 (1/TED):")
        print(f"  EMIS R²: {r2_emis:.4f}")
        print(f"  Linear R²: {r2_lin:.4f}")
        print(f"  差值: {diff:+.4f}")
        
        if diff > 0.05:
            print("\n  ✅ P2 预测成功")
        elif diff > 0:
            print("\n  🔶 P2 部分成功")
        else:
            print("\n  ❌ P2 预测失败：EMIS公式未优于线性模型")
    
    return all_results

if __name__ == "__main__":
    results = main()