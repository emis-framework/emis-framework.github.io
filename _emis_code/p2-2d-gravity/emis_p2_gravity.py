"""
EMIS P2: 流动性陷阱验证（不依赖pandas-datareader）
直接从FRED网站下载CSV
"""

import numpy as np
import pandas as pd
from scipy.optimize import curve_fit
from scipy import stats
import matplotlib.pyplot as plt
import os
import requests
from io import StringIO
import warnings
warnings.filterwarnings('ignore')

# ============================================
# 缓存配置
# ============================================

CACHE_DIR = './cache_p2/'
CACHE_FILES = {
    'M2V': 'fred_m2v.csv',
    'TED': 'fred_ted.csv',
    'BAA': 'fred_baa10y.csv',
    'VIX': 'fred_vix.csv',
    'COMBINED': 'p2_combined_data.csv'
}

# FRED API 配置（免费，无需API key也能用CSV下载）
FRED_CSV_URL = "https://fred.stlouisfed.org/graph/fredgraph.csv"

# ============================================
# 1. 数据获取（直接HTTP下载，不依赖任何额外包）
# ============================================

def ensure_cache_dir():
    """确保缓存目录存在"""
    if not os.path.exists(CACHE_DIR):
        os.makedirs(CACHE_DIR)
        print(f"创建缓存目录: {CACHE_DIR}")

def get_cache_path(name):
    """获取缓存文件完整路径"""
    return os.path.join(CACHE_DIR, CACHE_FILES.get(name, f'{name}.csv'))

def load_from_cache(name):
    """从缓存加载数据"""
    path = get_cache_path(name)
    if os.path.exists(path):
        print(f"  ✓ 从缓存加载: {path}")
        df = pd.read_csv(path, index_col=0, parse_dates=True)
        return df
    return None

def save_to_cache(df, name):
    """保存数据到缓存"""
    ensure_cache_dir()
    path = get_cache_path(name)
    df.to_csv(path)
    print(f"  ✓ 保存到缓存: {path}")

def download_fred_csv(series_id, start_date='1990-01-01', end_date='2024-12-31'):
    """
    直接从FRED下载CSV（不需要API key）
    
    参数:
        series_id: FRED序列ID (如 'M2V', 'TEDRATE')
        start_date: 开始日期
        end_date: 结束日期
    """
    url = f"{FRED_CSV_URL}?id={series_id}"
    
    print(f"  下载: {series_id} from FRED...")
    
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        # 解析CSV
        df = pd.read_csv(StringIO(response.text), 
                        index_col=0, 
                        parse_dates=True,
                        na_values=['.'])
        
        # 过滤日期范围
        df = df[start_date:end_date]
        
        # 重命名列
        df.columns = [series_id]
        
        print(f"    ✓ 成功: {len(df)} 条记录")
        return df
        
    except requests.exceptions.RequestException as e:
        print(f"    ✗ 下载失败: {e}")
        return None
    except Exception as e:
        print(f"    ✗ 解析失败: {e}")
        return None

def get_fred_data(start='1990-01-01', end='2024-12-31', force_download=False):
    """
    获取FRED数据（优先使用缓存）
    """
    
    ensure_cache_dir()
    
    # 尝试加载合并后的缓存
    if not force_download:
        combined = load_from_cache('COMBINED')
        if combined is not None and len(combined) > 100:
            print(f"  数据范围: {combined.index[0].date()} 到 {combined.index[-1].date()}")
            print(f"  样本数: {len(combined)}")
            return combined
    
    print("\n下载FRED数据...")
    
    # FRED序列ID映射
    series_map = {
        'M2V': 'M2V',           # M2货币流通速度（季度）
        'TED': 'TEDRATE',       # TED Spread（日度）
        'BAA': 'BAA10Y',        # BAA-10Y信用利差（日度）
        'VIX': 'VIXCLS'         # VIX（日度）
    }
    
    data_dict = {}
    
    for name, fred_id in series_map.items():
        # 先检查单独缓存
        if not force_download:
            cached = load_from_cache(name)
            if cached is not None and len(cached) > 0:
                data_dict[name] = cached.iloc[:, 0]
                continue
        
        # 下载
        df = download_fred_csv(fred_id, start, end)
        if df is not None and len(df) > 0:
            save_to_cache(df, name)
            data_dict[name] = df.iloc[:, 0]
        else:
            print(f"    ⚠ 跳过 {name}")
    
    if len(data_dict) == 0:
        print("错误: 无法获取任何数据")
        return None
    
    # 合并数据
    print("\n合并数据...")
    combined = pd.DataFrame(data_dict)
    
    # 重采样到月度（因为M2V是季度数据）
    # 先向前填充，再重采样
    combined = combined.resample('M').last().ffill()
    
    # 重命名列
    combined.columns = ['V', 'TED', 'BAA', 'VIX']
    
    # 计算流动性指标 Φ = 1/spread（spread越小，流动性越好）
    combined['Phi_TED'] = 1 / combined['TED'].replace(0, np.nan)
    combined['Phi_BAA'] = 1 / combined['BAA'].replace(0, np.nan)
    combined['Phi_VIX'] = 100 / combined['VIX'].replace(0, np.nan)  # VIX缩放
    
    # 删除缺失值
    combined = combined.dropna(subset=['V'])
    
    # 保存
    save_to_cache(combined, 'COMBINED')
    
    print(f"  数据范围: {combined.index[0].date()} 到 {combined.index[-1].date()}")
    print(f"  样本数: {len(combined)}")
    
    return combined

# ============================================
# 2. 模型定义
# ============================================

def model_emis(Phi, V0, Phi_c):
    """EMIS引力红移模型: V = V0 * sqrt(1 - (Phi_c/Phi)^2)"""
    ratio = np.clip(Phi_c / Phi, 0, 0.9999)
    return V0 * np.sqrt(1 - ratio**2)

def model_linear(Phi, a, b):
    """线性模型: V = a + b*Phi"""
    return a + b * Phi

def model_log(Phi, a, b):
    """对数模型: V = a + b*log(Phi)"""
    return a + b * np.log(np.maximum(Phi, 1e-10))

def model_power(Phi, a, b):
    """幂律模型: V = a * Phi^b"""
    return a * np.power(np.maximum(Phi, 1e-10), b)

# ============================================
# 3. 拟合函数
# ============================================

def fit_model(model_func, Phi, V, p0=None, bounds=None, name=''):
    """拟合单个模型"""
    try:
        if bounds:
            popt, pcov = curve_fit(model_func, Phi, V, p0=p0, bounds=bounds, maxfev=10000)
        else:
            popt, pcov = curve_fit(model_func, Phi, V, p0=p0, maxfev=10000)
        
        V_pred = model_func(Phi, *popt)
        
        # R²
        ss_res = np.sum((V - V_pred)**2)
        ss_tot = np.sum((V - V.mean())**2)
        r2 = 1 - ss_res / ss_tot
        
        # RMSE
        rmse = np.sqrt(np.mean((V - V_pred)**2))
        
        # AIC
        n = len(V)
        k = len(popt)
        aic = n * np.log(ss_res / n) + 2 * k
        
        return {
            'params': popt,
            'R2': r2,
            'RMSE': rmse,
            'AIC': aic,
            'pred': V_pred,
            'success': True
        }
    except Exception as e:
        print(f"    ⚠ {name} 拟合失败: {e}")
        return {'success': False, 'R2': np.nan}

def fit_all_models(V, Phi):
    """拟合所有模型"""
    
    results = {}
    
    # EMIS模型
    V0_init = V.max() * 1.2
    Phi_c_init = np.percentile(Phi, 10)
    
    res = fit_model(model_emis, Phi, V,
                   p0=[V0_init, Phi_c_init],
                   bounds=([V.min(), Phi.min()*0.1], [V.max()*3, Phi.max()]),
                   name='EMIS')
    if res['success']:
        results['EMIS'] = res
        results['EMIS']['param_names'] = ['V0', 'Phi_c']
    
    # 线性模型
    res = fit_model(model_linear, Phi, V, p0=[V.mean(), 1], name='Linear')
    if res['success']:
        results['Linear'] = res
        results['Linear']['param_names'] = ['a', 'b']
    
    # 对数模型
    res = fit_model(model_log, Phi, V, p0=[V.mean(), 1], name='Log')
    if res['success']:
        results['Log'] = res
        results['Log']['param_names'] = ['a', 'b']
    
    # 幂律模型
    res = fit_model(model_power, Phi, V,
                   p0=[V.mean(), 0.3],
                   bounds=([0, -2], [V.max()*3, 2]),
                   name='Power')
    if res['success']:
        results['Power'] = res
        results['Power']['param_names'] = ['a', 'b']
    
    return results

# ============================================
# 4. 可视化
# ============================================

def plot_fit_comparison(V, Phi, results, phi_name, save_path=None):
    """绘制拟合对比图"""
    
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    
    # 排序
    sort_idx = np.argsort(Phi)
    Phi_sorted = Phi[sort_idx]
    V_sorted = V[sort_idx]
    
    # 左图：数据和拟合曲线
    ax1 = axes[0]
    ax1.scatter(Phi, V, alpha=0.5, s=30, c='gray', label='Data', zorder=1)
    
    colors = {'EMIS': 'red', 'Linear': 'blue', 'Log': 'green', 'Power': 'orange'}
    linewidths = {'EMIS': 2.5, 'Linear': 2, 'Log': 2, 'Power': 2}
    
    for model_name, res in results.items():
        if res['success']:
            pred_sorted = res['pred'][sort_idx]
            ax1.plot(Phi_sorted, pred_sorted,
                    color=colors.get(model_name, 'black'),
                    linewidth=linewidths.get(model_name, 2),
                    label=f"{model_name} (R²={res['R2']:.4f})",
                    zorder=2)
    
    ax1.set_xlabel(f'Φ (Liquidity Indicator)', fontsize=11)
    ax1.set_ylabel('M2 Velocity (V)', fontsize=11)
    ax1.set_title(f'Model Comparison: {phi_name}', fontsize=12, fontweight='bold')
    ax1.legend(loc='best')
    ax1.grid(True, alpha=0.3)
    
    # 右图：R² 对比条形图
    ax2 = axes[1]
    
    model_names = list(results.keys())
    r2_values = [results[m]['R2'] for m in model_names if results[m]['success']]
    valid_names = [m for m in model_names if results[m]['success']]
    
    bars = ax2.bar(valid_names, r2_values, 
                   color=[colors.get(m, 'gray') for m in valid_names],
                   edgecolor='black')
    
    # 添加数值标签
    for bar, val in zip(bars, r2_values):
        ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01,
                f'{val:.4f}', ha='center', va='bottom', fontsize=10)
    
    ax2.set_ylabel('R²', fontsize=11)
    ax2.set_title('Model Comparison: R²', fontsize=12, fontweight='bold')
    ax2.set_ylim(0, 1)
    ax2.grid(True, alpha=0.3, axis='y')
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"  ✓ 图表已保存: {save_path}")
    
    plt.show()
    return fig

def plot_time_series(data, V, Phi, results, phi_name, save_path=None):
    """绘制时间序列"""
    
    fig, axes = plt.subplots(3, 1, figsize=(14, 10), sharex=True)
    
    # 获取有效数据的索引
    valid_idx = data.index[~data['V'].isna() & ~data[phi_name].isna()]
    
    # Panel A: M2 Velocity
    ax1 = axes[0]
    ax1.plot(valid_idx, data.loc[valid_idx, 'V'], 'b-', linewidth=1)
    ax1.set_ylabel('M2 Velocity (V)')
    ax1.set_title('(a) M2 Money Velocity', fontweight='bold')
    ax1.grid(True, alpha=0.3)
    
    # 标记2008年危机
    ax1.axvspan('2008-01-01', '2009-06-01', alpha=0.2, color='red', label='2008 Crisis')
    ax1.axvspan('2020-01-01', '2020-06-01', alpha=0.2, color='orange', label='COVID-19')
    ax1.legend(loc='upper right')
    
    # Panel B: 流动性指标
    ax2 = axes[1]
    ax2.plot(valid_idx, data.loc[valid_idx, phi_name], 'purple', linewidth=1)
    
    if 'EMIS' in results and results['EMIS']['success']:
        Phi_c = results['EMIS']['params'][1]
        ax2.axhline(y=Phi_c, color='red', linestyle='--', linewidth=2,
                   label=f'Φ_c = {Phi_c:.4f} (Critical Threshold)')
    
    ax2.set_ylabel(f'Φ ({phi_name})')
    ax2.set_title('(b) Liquidity Indicator', fontweight='bold')
    ax2.legend(loc='upper right')
    ax2.grid(True, alpha=0.3)
    
    # Panel C: 实际 vs 预测
    ax3 = axes[2]
    ax3.plot(valid_idx, V, 'b-', linewidth=1, alpha=0.7, label='Actual')
    
    if 'EMIS' in results and results['EMIS']['success']:
        ax3.plot(valid_idx, results['EMIS']['pred'], 'r-', linewidth=2, 
                label=f"EMIS (R²={results['EMIS']['R2']:.4f})")
    if 'Linear' in results and results['Linear']['success']:
        ax3.plot(valid_idx, results['Linear']['pred'], 'g--', linewidth=1.5, alpha=0.7,
                label=f"Linear (R²={results['Linear']['R2']:.4f})")
    
    ax3.set_ylabel('M2 Velocity')
    ax3.set_xlabel('Date')
    ax3.set_title('(c) Actual vs Predicted', fontweight='bold')
    ax3.legend(loc='upper right')
    ax3.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"  ✓ 图表已保存: {save_path}")
    
    plt.show()
    return fig

# ============================================
# 5. 主程序
# ============================================

def main():
    print("="*70)
    print("EMIS P2: 流动性陷阱验证")
    print("="*70)
    print("理论公式: V = V0 × √(1 - (Φc/Φ)²)")
    print("预测: 当Φ→Φc时，V急剧非线性下降（引力红移效应）")
    print("="*70)
    
    # 获取数据
    print("\n[1] 获取数据...")
    data = get_fred_data(force_download=False)
    
    if data is None:
        print("❌ 无法获取数据，请检查网络连接")
        return None
    
    # 测试不同流动性指标
    phi_columns = ['Phi_TED', 'Phi_BAA', 'Phi_VIX']
    all_results = {}
    
    for phi_name in phi_columns:
        print(f"\n{'='*70}")
        print(f"[2] 测试流动性指标: {phi_name}")
        print("="*70)
        
        # 准备数据
        valid = ~data['V'].isna() & ~data[phi_name].isna() & \
                ~np.isinf(data[phi_name]) & (data[phi_name] > 0)
        
        df_valid = data[valid].copy()
        
        if len(df_valid) < 20:
            print(f"  ⚠ 有效数据不足 ({len(df_valid)} 条)，跳过")
            continue
        
        V = df_valid['V'].values
        Phi = df_valid[phi_name].values
        
        print(f"  有效样本: {len(V)}")
        print(f"  V 范围: [{V.min():.2f}, {V.max():.2f}]")
        print(f"  Φ 范围: [{Phi.min():.4f}, {Phi.max():.4f}]")
        
        # 拟合所有模型
        print(f"\n  拟合模型...")
        results = fit_all_models(V, Phi)
        
        # 输出结果表格
        print(f"\n  {'模型':<10} {'R²':<12} {'RMSE':<12} {'参数':<40}")
        print("  " + "-"*70)
        
        for model_name, res in results.items():
            if res['success']:
                params_str = ', '.join([f"{n}={p:.4f}" 
                                       for n, p in zip(res['param_names'], res['params'])])
                print(f"  {model_name:<10} {res['R2']:<12.4f} {res['RMSE']:<12.4f} {params_str}")
        
        # 判定
        print(f"\n  判定:")
        if 'EMIS' in results and 'Linear' in results:
            if results['EMIS']['success'] and results['Linear']['success']:
                r2_emis = results['EMIS']['R2']
                r2_lin = results['Linear']['R2']
                diff = r2_emis - r2_lin
                
                print(f"  EMIS R² = {r2_emis:.4f}")
                print(f"  Linear R² = {r2_lin:.4f}")
                print(f"  差值 = {diff:.4f}")
                
                if diff > 0.05:
                    print("  ✅ EMIS模型显著优于线性模型")
                elif diff > 0.01:
                    print("  🔶 EMIS略优，但差距较小")
                elif diff > -0.01:
                    print("  ⚪ 两模型相当")
                else:
                    print("  ❌ 线性模型更好")
        
        # 保存结果
        all_results[phi_name] = {
            'data': df_valid,
            'V': V,
            'Phi': Phi,
            'models': results
        }
        
        # 绘图
        print(f"\n  生成图表...")
        plot_fit_comparison(V, Phi, results, phi_name,
                           save_path=f'p2_fit_{phi_name}.png')
        
        plot_time_series(df_valid, V, Phi, results, phi_name,
                        save_path=f'p2_timeseries_{phi_name}.png')
    
    # ============================================
    # 汇总
    # ============================================
    
    print("\n" + "="*70)
    print("汇总报告")
    print("="*70)
    
    print(f"\n{'指标':<15} {'EMIS R²':<12} {'Linear R²':<12} {'差值':<12} {'判定':<15}")
    print("-"*65)
    
    for phi_name, res in all_results.items():
        models = res['models']
        r2_emis = models.get('EMIS', {}).get('R2', np.nan)
        r2_lin = models.get('Linear', {}).get('R2', np.nan)
        
        if np.isnan(r2_emis) or np.isnan(r2_lin):
            continue
            
        diff = r2_emis - r2_lin
        
        if diff > 0.05:
            verdict = "✅ EMIS胜"
        elif diff > 0.01:
            verdict = "🔶 EMIS略优"
        elif diff > -0.01:
            verdict = "⚪ 相当"
        else:
            verdict = "❌ Linear胜"
        
        print(f"{phi_name:<15} {r2_emis:<12.4f} {r2_lin:<12.4f} {diff:<+12.4f} {verdict}")
    
    # EMIS参数解读
    print("\n" + "="*70)
    print("EMIS模型参数解读")
    print("="*70)
    
    for phi_name, res in all_results.items():
        if 'EMIS' in res['models'] and res['models']['EMIS']['success']:
            V0 = res['models']['EMIS']['params'][0]
            Phi_c = res['models']['EMIS']['params'][1]
            
            print(f"\n{phi_name}:")
            print(f"  V0 = {V0:.4f} (理论最大流通速度)")
            print(f"  Φc = {Phi_c:.4f} (流动性陷阱临界值)")
            print(f"  解释: 当流动性指标Φ接近{Phi_c:.4f}时，货币流通速度急剧下降")
    
    return all_results

# ============================================
# 运行
# ============================================

if __name__ == "__main__":
    results = main()