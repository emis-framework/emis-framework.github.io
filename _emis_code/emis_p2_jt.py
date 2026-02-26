"""
EMIS P2: JT引力正确公式验证
V_local = V0 / sqrt(1 - (Φ/Φh)²)
其中 Φ = TED spread（不是1/TED）
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

# ============================================
# 数据获取
# ============================================

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
    """获取季度数据"""
    
    print("\n获取数据...")
    
    # M2V - 季度
    m2v = download_fred('M2V')
    
    # TED Spread - 日度
    ted = download_fred('TEDRATE')
    
    # BAA 信用利差 - 日度
    baa = download_fred('BAA10Y')
    
    # VIX - 日度
    vix = download_fred('VIXCLS')
    
    if m2v is None:
        return None
    
    print("\n转换到季度...")
    
    # M2V转Period
    m2v_q = m2v.copy()
    m2v_q.index = m2v_q.index.to_period('Q')
    m2v_q.columns = ['V']
    
    # 其他转季度
    def to_quarterly(df, name):
        if df is None:
            return None
        q = df.resample('QE').mean()
        q.index = q.index.to_period('Q')
        q.columns = [name]
        return q
    
    ted_q = to_quarterly(ted, 'TED')
    baa_q = to_quarterly(baa, 'BAA')
    vix_q = to_quarterly(vix, 'VIX')
    
    # 合并
    data = m2v_q.copy()
    for df in [ted_q, baa_q, vix_q]:
        if df is not None:
            data = data.join(df, how='left')
    
    data.index = data.index.to_timestamp()
    
    print(f"  样本数: {len(data)}")
    print(f"  时间: {data.index[0].date()} 到 {data.index[-1].date()}")
    
    return data

# ============================================
# 正确的JT引力模型
# ============================================

def jt_correct(Phi, V0, Phi_h):
    """
    正确的JT引力红移公式（本地速度）
    V_local = V0 / sqrt(1 - (Φ/Φh)²)
    
    Φ = TED spread（摩擦，不是流动性）
    Φh = 临界值（视界）
    """
    ratio = Phi / Phi_h
    # 只有 Φ < Φh 才有实数解
    result = np.where(ratio < 1, V0 / np.sqrt(1 - ratio**2), np.inf)
    return result

def jt_correct_v2(Phi, V0, Phi_h, alpha):
    """
    广义JT公式
    V = V0 / (1 - (Φ/Φh)²)^alpha
    """
    ratio = Phi / Phi_h
    result = np.where(ratio < 1, V0 / np.power(1 - ratio**2, alpha), np.inf)
    return result

def jt_obs(Phi, V0, Phi_h):
    """
    JT红移公式（观测速度，对比用）
    V_obs = V0 * sqrt(1 - (Φ/Φh)²)
    """
    ratio = Phi / Phi_h
    result = np.where(ratio < 1, V0 * np.sqrt(1 - ratio**2), 0)
    return result

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

def fit_model(func, X, Y, p0, bounds=None, name=''):
    """拟合单个模型"""
    try:
        if bounds:
            popt, pcov = curve_fit(func, X, Y, p0=p0, bounds=bounds, maxfev=10000)
        else:
            popt, pcov = curve_fit(func, X, Y, p0=p0, maxfev=10000)
        
        pred = func(X, *popt)
        
        # 处理无穷大
        valid = np.isfinite(pred)
        if valid.sum() < len(Y) * 0.5:
            return {'success': False, 'R2': np.nan}
        
        ss_res = np.sum((Y[valid] - pred[valid])**2)
        ss_tot = np.sum((Y - Y.mean())**2)
        r2 = 1 - ss_res / ss_tot
        rmse = np.sqrt(np.mean((Y[valid] - pred[valid])**2))
        
        return {
            'params': popt,
            'R2': r2,
            'RMSE': rmse,
            'pred': pred,
            'success': True
        }
    except Exception as e:
        print(f"    {name} 拟合失败: {e}")
        return {'success': False, 'R2': np.nan}

def fit_all_models(V, Phi, phi_name='TED'):
    """拟合所有模型"""
    
    results = {}
    
    V_max, V_min, V_mean = V.max(), V.min(), V.mean()
    Phi_max, Phi_min = Phi.max(), Phi.min()
    
    print(f"\n  V: [{V_min:.3f}, {V_max:.3f}], mean={V_mean:.3f}")
    print(f"  Φ: [{Phi_min:.4f}, {Phi_max:.4f}]")
    
    # 1. JT正确公式（本地速度）
    #    V = V0 / sqrt(1 - (Φ/Φh)²)
    #    需要 Φh > Φ_max
    res = fit_model(jt_correct, Phi, V,
                   p0=[V_min, Phi_max * 1.5],
                   bounds=([0, Phi_max * 1.01], [V_max * 2, Phi_max * 10]),
                   name='JT_local')
    if res['success']:
        results['JT_local'] = res
        print(f"    JT_local: V0={res['params'][0]:.4f}, Φh={res['params'][1]:.4f}")
    
    # 2. JT广义公式
    res = fit_model(jt_correct_v2, Phi, V,
                   p0=[V_min, Phi_max * 1.5, 0.5],
                   bounds=([0, Phi_max * 1.01, 0.1], [V_max * 2, Phi_max * 10, 2]),
                   name='JT_general')
    if res['success']:
        results['JT_general'] = res
        print(f"    JT_general: V0={res['params'][0]:.4f}, Φh={res['params'][1]:.4f}, α={res['params'][2]:.4f}")
    
    # 3. JT观测速度（对比）
    res = fit_model(jt_obs, Phi, V,
                   p0=[V_max, Phi_max * 1.5],
                   bounds=([0, Phi_max * 1.01], [V_max * 3, Phi_max * 10]),
                   name='JT_obs')
    if res['success']:
        results['JT_obs'] = res
        print(f"    JT_obs: V0={res['params'][0]:.4f}, Φh={res['params'][1]:.4f}")
    
    # 4. 线性
    res = fit_model(model_linear, Phi, V, p0=[V_mean, 0], name='Linear')
    if res['success']:
        results['Linear'] = res
    
    # 5. 对数
    res = fit_model(model_log, Phi, V, p0=[V_mean, 0], name='Log')
    if res['success']:
        results['Log'] = res
    
    # 6. 幂律
    res = fit_model(model_power, Phi, V,
                   p0=[V_mean, 0.1],
                   bounds=([0, -3], [V_max * 3, 3]),
                   name='Power')
    if res['success']:
        results['Power'] = res
    
    # 7. 反比
    res = fit_model(model_inverse, Phi, V, p0=[V_mean, 0], name='Inverse')
    if res['success']:
        results['Inverse'] = res
    
    return results

# ============================================
# 可视化
# ============================================

def plot_results(V, Phi, results, phi_name, data, save_path=None):
    """绘制结果"""
    
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    
    colors = {
        'JT_local': 'red', 
        'JT_general': 'darkred',
        'JT_obs': 'orange',
        'Linear': 'blue', 
        'Log': 'green', 
        'Power': 'purple',
        'Inverse': 'brown'
    }
    
    # =====================================
    # 左上：散点图 + 拟合曲线
    # =====================================
    ax1 = axes[0, 0]
    ax1.scatter(Phi, V, alpha=0.6, s=40, c='gray', label='Data')
    
    # 排序用于绘制曲线
    sort_idx = np.argsort(Phi)
    Phi_sorted = Phi[sort_idx]
    
    for name, res in results.items():
        if res['success']:
            pred_sorted = res['pred'][sort_idx]
            # 过滤无穷大
            valid = np.isfinite(pred_sorted)
            ax1.plot(Phi_sorted[valid], pred_sorted[valid],
                    color=colors.get(name, 'black'),
                    linewidth=2.5 if 'JT' in name else 2,
                    linestyle='-' if 'JT' in name else '--',
                    label=f"{name} (R²={res['R2']:.4f})")
    
    ax1.set_xlabel(f'Φ = {phi_name} (Friction/Spread)', fontsize=11)
    ax1.set_ylabel('V (M2 Velocity)', fontsize=11)
    ax1.set_title('(a) Model Fit: JT Gravity vs Alternatives', fontweight='bold')
    ax1.legend(loc='best', fontsize=9)
    ax1.grid(True, alpha=0.3)
    
    # =====================================
    # 右上：R² 对比条形图
    # =====================================
    ax2 = axes[0, 1]
    
    valid_models = {k: v for k, v in results.items() if v['success']}
    names = list(valid_models.keys())
    r2_vals = [valid_models[n]['R2'] for n in names]
    
    # 排序
    sorted_idx = np.argsort(r2_vals)[::-1]
    names_sorted = [names[i] for i in sorted_idx]
    r2_sorted = [r2_vals[i] for i in sorted_idx]
    
    bars = ax2.bar(range(len(names_sorted)), r2_sorted,
                   color=[colors.get(n, 'gray') for n in names_sorted],
                   edgecolor='black')
    
    ax2.set_xticks(range(len(names_sorted)))
    ax2.set_xticklabels(names_sorted, rotation=45, ha='right')
    ax2.set_ylabel('R²', fontsize=11)
    ax2.set_title('(b) Model R² Comparison', fontweight='bold')
    ax2.grid(True, alpha=0.3, axis='y')
    
    for bar, r2 in zip(bars, r2_sorted):
        ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01,
                f'{r2:.4f}', ha='center', fontsize=9, fontweight='bold')
    
    # =====================================
    # 左下：时间序列
    # =====================================
    ax3 = axes[1, 0]
    
    ax3.plot(data.index, V, 'b-', linewidth=1.5, label='M2 Velocity (V)')
    ax3.set_ylabel('V (M2 Velocity)', color='b', fontsize=11)
    ax3.tick_params(axis='y', labelcolor='b')
    
    ax3_twin = ax3.twinx()
    ax3_twin.plot(data.index, Phi, 'r-', linewidth=1.5, alpha=0.7, label=f'Φ ({phi_name})')
    ax3_twin.set_ylabel(f'Φ = {phi_name}', color='r', fontsize=11)
    ax3_twin.tick_params(axis='y', labelcolor='r')
    
    # 标记Φh（如果JT_local成功）
    if 'JT_local' in results:
        Phi_h = results['JT_local']['params'][1]
        ax3_twin.axhline(y=Phi_h, color='red', linestyle='--', linewidth=2,
                        label=f'Φh = {Phi_h:.2f} (Horizon)')
    
    ax3.axvspan('2008-01-01', '2009-12-31', alpha=0.2, color='gray', label='2008 Crisis')
    ax3.axvspan('2020-01-01', '2021-06-01', alpha=0.2, color='orange', label='COVID')
    
    ax3.set_title('(c) Time Series: V and Φ', fontweight='bold')
    ax3.legend(loc='upper left', fontsize=8)
    ax3_twin.legend(loc='upper right', fontsize=8)
    ax3.grid(True, alpha=0.3)
    
    # =====================================
    # 右下：JT公式的物理解释
    # =====================================
    ax4 = axes[1, 1]
    
    if 'JT_local' in results:
        V0 = results['JT_local']['params'][0]
        Phi_h = results['JT_local']['params'][1]
        
        # 绘制理论曲线
        Phi_theory = np.linspace(0.01, Phi_h * 0.99, 100)
        V_theory = jt_correct(Phi_theory, V0, Phi_h)
        
        ax4.plot(Phi_theory / Phi_h, V_theory / V0, 'r-', linewidth=2.5,
                label='JT: $V/V_0 = 1/\\sqrt{1-(\\Phi/\\Phi_h)^2}$')
        
        # 标记数据点
        ax4.scatter(Phi / Phi_h, V / V0, alpha=0.5, s=30, c='gray', label='Data')
        
        ax4.axvline(x=1, color='black', linestyle='--', linewidth=1.5, label='Horizon (Φ=Φh)')
        ax4.set_xlabel('Φ / Φh (Normalized Friction)', fontsize=11)
        ax4.set_ylabel('V / V0 (Normalized Velocity)', fontsize=11)
        ax4.set_title('(d) JT Gravity: Normalized View', fontweight='bold')
        ax4.set_xlim(0, 1.2)
        ax4.legend(loc='upper left', fontsize=9)
        ax4.grid(True, alpha=0.3)
    else:
        ax4.text(0.5, 0.5, 'JT model fitting failed', ha='center', va='center',
                transform=ax4.transAxes, fontsize=12)
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"\n  ✓ 图表保存: {save_path}")
    
    plt.show()
    return fig

# ============================================
# 主程序
# ============================================

def main():
    print("="*70)
    print("EMIS P2: JT引力正确公式验证")
    print("="*70)
    print("公式: V_local = V0 / sqrt(1 - (Φ/Φh)²)")
    print("映射: Φ = TED spread（摩擦，不是1/TED）")
    print("      Φh = 临界值（视界，流动性陷阱）")
    print("="*70)
    
    # 获取数据
    data = get_quarterly_data()
    if data is None:
        return None
    
    # 测试不同的Φ指标
    phi_tests = [
        ('TED', 'TED Spread'),
        ('BAA', 'BAA Credit Spread'),
        ('VIX', 'VIX Index')
    ]
    
    all_results = {}
    
    for phi_col, phi_desc in phi_tests:
        if phi_col not in data.columns:
            continue
        
        print(f"\n{'='*70}")
        print(f"测试: V vs Φ = {phi_desc}")
        print("="*70)
        
        # 准备数据
        valid = data['V'].notna() & data[phi_col].notna() & (data[phi_col] > 0)
        df = data[valid].copy()
        
        if len(df) < 30:
            print(f"  ⚠ 数据不足: {len(df)} 条")
            continue
        
        V = df['V'].values
        Phi = df[phi_col].values
        
        print(f"  样本: {len(V)} 季度")
        
        # 相关性
        corr = np.corrcoef(V, Phi)[0, 1]
        print(f"  Corr(V, Φ): {corr:.4f}")
        
        if corr < 0:
            print(f"  ⚠ 负相关，JT_local预测正相关")
        else:
            print(f"  ✓ 正相关，符合JT_local预测")
        
        # 拟合所有模型
        results = fit_all_models(V, Phi, phi_col)
        
        # 输出结果
        print(f"\n  {'模型':<15} {'R²':<12} {'RMSE':<12}")
        print("  " + "-"*40)
        
        for name, res in sorted(results.items(), key=lambda x: -x[1].get('R2', -999)):
            if res['success']:
                print(f"  {name:<15} {res['R2']:<12.4f} {res['RMSE']:<12.4f}")
        
        # 判定
        r2_jt = results.get('JT_local', {}).get('R2', np.nan)
        r2_lin = results.get('Linear', {}).get('R2', np.nan)
        
        if not np.isnan(r2_jt) and not np.isnan(r2_lin):
            diff = r2_jt - r2_lin
            print(f"\n  JT_local R² - Linear R² = {diff:+.4f}")
            
            if diff > 0.05:
                print("  ✅ JT引力显著优于线性模型！")
            elif diff > 0.01:
                print("  🔶 JT略优")
            elif diff > -0.01:
                print("  ⚪ 相当")
            else:
                print("  ❌ 线性更好")
        
        all_results[phi_col] = {
            'data': df,
            'V': V,
            'Phi': Phi,
            'models': results,
            'corr': corr
        }
        
        # 绘图
        plot_results(V, Phi, results, phi_col, df,
                    save_path=f'p2_jt_correct_{phi_col}.png')
    
    # ============================================
    # 汇总报告
    # ============================================
    
    print("\n" + "="*70)
    print("汇总报告")
    print("="*70)
    
    print(f"\n{'Φ指标':<10} {'样本':<8} {'Corr':<10} {'JT_local':<12} {'Linear':<12} {'差值':<12} {'判定':<10}")
    print("-"*75)
    
    for phi_col, res in all_results.items():
        models = res['models']
        n = len(res['V'])
        corr = res['corr']
        r2_jt = models.get('JT_local', {}).get('R2', np.nan)
        r2_lin = models.get('Linear', {}).get('R2', np.nan)
        
        diff = r2_jt - r2_lin if not np.isnan(r2_jt) else np.nan
        
        if diff > 0.05:
            verdict = "✅ JT胜"
        elif diff > 0:
            verdict = "🔶 JT略优"
        elif not np.isnan(diff):
            verdict = "❌ Linear胜"
        else:
            verdict = "N/A"
        
        r2_jt_str = f"{r2_jt:.4f}" if not np.isnan(r2_jt) else "N/A"
        r2_lin_str = f"{r2_lin:.4f}" if not np.isnan(r2_lin) else "N/A"
        diff_str = f"{diff:+.4f}" if not np.isnan(diff) else "N/A"
        
        print(f"{phi_col:<10} {n:<8} {corr:<+10.4f} {r2_jt_str:<12} {r2_lin_str:<12} {diff_str:<12} {verdict}")
    
    # ============================================
    # P2 最终判定
    # ============================================
    
    print("\n" + "="*70)
    print("P2 预测判定")
    print("="*70)
    
    if 'TED' in all_results:
        models = all_results['TED']['models']
        r2_jt = models.get('JT_local', {}).get('R2', np.nan)
        r2_lin = models.get('Linear', {}).get('R2', np.nan)
        
        if not np.isnan(r2_jt):
            V0 = models['JT_local']['params'][0]
            Phi_h = models['JT_local']['params'][1]
            
            print(f"\nJT引力公式: V = {V0:.4f} / sqrt(1 - (TED/{Phi_h:.4f})²)")
            print(f"临界TED值: {Phi_h:.4f}%")
            print(f"解释: 当TED接近{Phi_h:.2f}%时，货币流速趋向无穷（流动性危机）")
        
        diff = r2_jt - r2_lin if not np.isnan(r2_jt) else np.nan
        
        print(f"\nJT_local R²: {r2_jt:.4f}" if not np.isnan(r2_jt) else "\nJT_local: 拟合失败")
        print(f"Linear R²: {r2_lin:.4f}")
        
        if not np.isnan(diff):
            print(f"差值: {diff:+.4f}")
            
            if diff > 0.05:
                print("\n✅ P2 预测成功：JT引力红移效应得到验证！")
            elif diff > 0:
                print("\n🔶 P2 部分成功：JT略优于线性")
            else:
                print("\n❌ P2 预测失败：JT未优于线性模型")
    
    return all_results

# ============================================
# 运行
# ============================================

if __name__ == "__main__":
    results = main()