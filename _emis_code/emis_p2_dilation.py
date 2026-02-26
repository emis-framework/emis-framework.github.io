#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
EMIS P2: JT引力Dilaton场验证 - 流动性陷阱预测
================================================================================

理论基础：
---------
JT (Jackiw-Teitelboim) 引力的Dilaton场映射到经济学

核心公式：
---------
V = V₀ · √(1 - (φ/φₕ)²)

其中：
  V    = M2货币流通速度 (M2V)
  V₀   = 正常状态流速 (TED=TED₀时的V)
  φ    = TED - TED₀ (周期性摩擦)
  φₕ   = TED_crit - TED₀ (临界摩擦，视界值)

变量定义：
---------
+-------------+------------------------+--------------------------------+
| 符号        | 物理意义               | 经济意义                       |
+-------------+------------------------+--------------------------------+
| Φ (Phi)     | Dilaton场总值          | TED spread (总摩擦)            |
| Φ₀          | 基态Dilaton (极端黑洞)  | 结构性摩擦 (时间加权最小值)     |
| φ = Φ - Φ₀  | Dilaton波动            | 周期性摩擦                     |
| φₕ          | 视界处Dilaton          | 临界摩擦 (流动性陷阱阈值)       |
| V           | 本地速度 V_local       | M2货币流速                     |
| V₀          | 渐近速度 V_∞           | 正常状态流速                   |
+-------------+------------------------+--------------------------------+

公式行为：
---------
| TED状态           | φ/φₕ  | V        | 经济含义           |
|-------------------|-------|----------|-------------------|
| TED = TED₀        | 0     | V₀       | 正常流动性         |
| TED = 中间值       | 0.5   | 0.87 V₀  | 轻度收紧           |
| TED → TED_crit    | 1     | 0        | 流动性陷阱         |

================================================================================
"""

import numpy as np
import pandas as pd
from scipy.optimize import curve_fit, minimize
import os
import requests
from io import StringIO
import warnings
warnings.filterwarnings('ignore')

# ============================================
# 配置
# ============================================

CACHE_DIR = './cache_p2_dilaton/'

# ============================================
# 数据获取（带缓存）
# ============================================

def ensure_cache_dir():
    """确保缓存目录存在"""
    if not os.path.exists(CACHE_DIR):
        os.makedirs(CACHE_DIR)

def download_fred(series_id):
    """
    下载FRED数据（带缓存）
    
    参数:
        series_id: FRED序列ID
    返回:
        DataFrame或None
    """
    cache_path = os.path.join(CACHE_DIR, f'{series_id}.csv')
    
    # 检查缓存
    if os.path.exists(cache_path):
        print(f"  ✓ 缓存: {series_id}")
        return pd.read_csv(cache_path, index_col=0, parse_dates=True)
    
    # 下载
    url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={series_id}"
    print(f"  下载: {series_id}...")
    
    try:
        response = requests.get(url, timeout=30)
        df = pd.read_csv(StringIO(response.text), index_col=0, parse_dates=True, na_values=['.'])
        df.columns = [series_id]
        
        ensure_cache_dir()
        df.to_csv(cache_path)
        print(f"    ✓ {len(df)} 条记录")
        return df
    except Exception as e:
        print(f"    ✗ 下载失败: {e}")
        return None

def get_quarterly_data():
    """
    获取季度数据
    
    返回:
        DataFrame: 包含V, TED, BAA, VIX的季度数据
    """
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
        print("  ✗ M2V数据获取失败")
        return None
    
    print("\n转换到季度频率...")
    
    # M2V转Period
    m2v_q = m2v.copy()
    m2v_q.index = m2v_q.index.to_period('Q')
    m2v_q.columns = ['V']
    
    # 其他转季度均值
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
    print(f"  时间范围: {data.index[0].date()} 到 {data.index[-1].date()}")
    
    return data

# ============================================
# 参数估计
# ============================================

def estimate_TED_0(TED, method='time_weighted'):
    """
    估计TED₀（结构性摩擦基准）
    
    物理对应: Φ₀ = 基态Dilaton
    """
    TED_clean = TED[~np.isnan(TED)]
    
    if method == 'time_weighted':
        epsilon = 0.01
        min_TED = TED_clean.min()
        weights = 1 / (TED_clean - min_TED + epsilon)
        TED_0 = np.average(TED_clean, weights=weights)
    elif method == 'percentile':
        TED_0 = np.percentile(TED_clean, 5)
    else:
        TED_0 = TED_clean.min()
    
    return float(TED_0)

def estimate_TED_crit(TED, method='percentile'):
    """
    估计TED_crit（临界值/视界）
    
    物理对应: Φₕ = 视界处Dilaton
    """
    TED_clean = TED[~np.isnan(TED)]
    
    if method == 'max':
        TED_crit = TED_clean.max()
    elif method == 'percentile':
        TED_crit = np.percentile(TED_clean, 99)
    else:
        TED_crit = TED_clean.max()
    
    return float(TED_crit)

# ============================================
# 核心物理公式
# ============================================

def dilaton_velocity(TED, V0, TED_0, TED_crit):
    """
    Dilaton速度公式（本地速度，JT引力）
    
    公式:
        V = V₀ · √(1 - (φ/φₕ)²)
    
    其中:
        φ = TED - TED₀ (周期性摩擦)
        φₕ = TED_crit - TED₀ (临界摩擦)
    """
    phi = TED - TED_0
    phi_h = TED_crit - TED_0
    
    if phi_h <= 0:
        return np.full_like(TED, np.nan, dtype=float)
    
    ratio_sq = (phi / phi_h) ** 2
    inner = np.clip(1 - ratio_sq, 0, None)
    V = V0 * np.sqrt(inner)
    
    return V

# ============================================
# 对比模型
# ============================================

def model_linear(x, a, b):
    """线性模型: V = a + b·Φ"""
    return a + b * x

def model_log(x, a, b):
    """对数模型: V = a + b·log(Φ)"""
    return a + b * np.log(np.maximum(x, 1e-10))

def model_power(x, a, b):
    """幂律模型: V = a · Φ^b"""
    return a * np.power(np.maximum(x, 1e-10), b)

# ============================================
# 拟合函数
# ============================================

def fit_model_simple(func, X, Y, p0, bounds=None, name=''):
    """
    拟合单个模型（简化版）
    """
    try:
        if bounds:
            popt, pcov = curve_fit(func, X, Y, p0=p0, bounds=bounds, maxfev=10000)
        else:
            popt, pcov = curve_fit(func, X, Y, p0=p0, maxfev=10000)
        
        pred = func(X, *popt)
        
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
        return {'success': False, 'R2': np.nan, 'error': str(e)}

def fit_dilaton_model(V, TED):
    """
    拟合Dilaton模型（使用优化器而非curve_fit）
    
    公式: V = V₀ · √(1 - ((TED-TED₀)/(TED_crit-TED₀))²)
    """
    # 估计初始参数
    TED_0_init = np.percentile(TED, 5)  # 简化：用5%分位数
    TED_crit_init = TED.max() * 1.5     # 临界值必须大于最大TED
    V0_init = V.max()
    
    print(f"\n  初始估计:")
    print(f"    TED₀ = {TED_0_init:.4f}")
    print(f"    TED_crit = {TED_crit_init:.4f}")
    print(f"    V₀ = {V0_init:.4f}")
    
    # 定义损失函数
    def loss(params):
        V0, TED_0, TED_crit = params
        
        # 约束检查
        if TED_0 < 0 or TED_crit <= TED.max() or V0 <= 0:
            return 1e10
        if TED_crit <= TED_0:
            return 1e10
        
        pred = dilaton_velocity(TED, V0, TED_0, TED_crit)
        
        if np.any(np.isnan(pred)):
            return 1e10
        
        mse = np.mean((V - pred)**2)
        return mse
    
    # 优化
    x0 = [V0_init, TED_0_init, TED_crit_init]
    bounds = [(V.min() * 0.5, V.max() * 2),      # V0
              (0, TED.min()),                      # TED_0
              (TED.max() * 1.01, TED.max() * 10)]  # TED_crit
    
    try:
        result = minimize(loss, x0, method='L-BFGS-B', bounds=bounds)
        
        if result.success or result.fun < 1e9:
            V0_fit, TED_0_fit, TED_crit_fit = result.x
            
            pred = dilaton_velocity(TED, V0_fit, TED_0_fit, TED_crit_fit)
            
            ss_res = np.sum((V - pred)**2)
            ss_tot = np.sum((V - V.mean())**2)
            r2 = 1 - ss_res / ss_tot
            rmse = np.sqrt(np.mean((V - pred)**2))
            
            print(f"\n  拟合结果:")
            print(f"    V₀ = {V0_fit:.4f}")
            print(f"    TED₀ = {TED_0_fit:.4f}")
            print(f"    TED_crit = {TED_crit_fit:.4f}")
            print(f"    φₕ = {TED_crit_fit - TED_0_fit:.4f}")
            print(f"    R² = {r2:.4f}")
            
            return {
                'success': True,
                'params': result.x,
                'V0': V0_fit,
                'TED_0': TED_0_fit,
                'TED_crit': TED_crit_fit,
                'phi_h': TED_crit_fit - TED_0_fit,
                'R2': r2,
                'RMSE': rmse,
                'pred': pred
            }
        else:
            print(f"\n  ⚠ Dilaton拟合未收敛")
            return {'success': False, 'R2': np.nan}
            
    except Exception as e:
        print(f"\n  ✗ Dilaton拟合失败: {e}")
        return {'success': False, 'R2': np.nan, 'error': str(e)}

def fit_all_models(V, TED, phi_name='TED'):
    """
    拟合所有模型进行对比
    """
    results = {}
    
    V_max, V_min, V_mean = V.max(), V.min(), V.mean()
    TED_max, TED_min = TED.max(), TED.min()
    
    print(f"\n  V范围: [{V_min:.3f}, {V_max:.3f}], 均值={V_mean:.3f}")
    print(f"  Φ范围: [{TED_min:.4f}, {TED_max:.4f}]")
    
    # 1. Dilaton模型
    dilaton_result = fit_dilaton_model(V, TED)
    if dilaton_result['success']:
        results['Dilaton'] = dilaton_result
    
    # 2. 线性模型
    res = fit_model_simple(model_linear, TED, V, p0=[V_mean, 0], name='Linear')
    if res['success']:
        results['Linear'] = res
        print(f"\n  线性模型: a={res['params'][0]:.4f}, b={res['params'][1]:.4f}, R²={res['R2']:.4f}")
    
    # 3. 对数模型
    res = fit_model_simple(model_log, TED, V, p0=[V_mean, 0], name='Log')
    if res['success']:
        results['Log'] = res
        print(f"  对数模型: a={res['params'][0]:.4f}, b={res['params'][1]:.4f}, R²={res['R2']:.4f}")
    
    # 4. 幂律模型
    res = fit_model_simple(model_power, TED, V,
                          p0=[V_mean, -0.1],
                          bounds=([0, -3], [V_max * 3, 1]),
                          name='Power')
    if res['success']:
        results['Power'] = res
        print(f"  幂律模型: a={res['params'][0]:.4f}, b={res['params'][1]:.4f}, R²={res['R2']:.4f}")
    
    return results

# ============================================
# 主程序
# ============================================

def main():
    """主程序入口"""
    
    print("=" * 70)
    print("EMIS P2: JT引力Dilaton场验证")
    print("=" * 70)
    print("\n核心公式: V = V₀ · √(1 - (φ/φₕ)²)")
    print("其中: φ = TED - TED₀, φₕ = TED_crit - TED₀")
    print("预测: 高TED → V下降 → 流动性陷阱")
    print("=" * 70)
    
    # 获取数据
    data = get_quarterly_data()
    if data is None:
        return None
    
    # 测试不同Φ指标
    phi_tests = [
        ('TED', 'TED Spread'),
        ('BAA', 'BAA Spread'),
        ('VIX', 'VIX')
    ]
    
    all_results = {}
    
    for phi_col, phi_desc in phi_tests:
        if phi_col not in data.columns:
            continue
        
        print(f"\n{'=' * 70}")
        print(f"测试: V vs Φ = {phi_desc}")
        print("=" * 70)
        
        # 准备数据
        valid = data['V'].notna() & data[phi_col].notna() & (data[phi_col] > 0)
        df = data[valid].copy()
        
        if len(df) < 30:
            print(f"  ⚠ 数据不足: {len(df)} 条")
            continue
        
        V = df['V'].values
        TED = df[phi_col].values
        
        print(f"  样本: {len(V)} 个季度")
        
        # 相关性
        corr = np.corrcoef(V, TED)[0, 1]
        print(f"  相关系数 Corr(V, Φ): {corr:.4f}")
        
        if corr < 0:
            print("  ✓ 负相关，符合Dilaton预测（高Φ → 低V）")
        else:
            print("  ⚠ 正相关，与Dilaton预测方向相反")
        
        # 拟合所有模型
        results = fit_all_models(V, TED, phi_col)
        
        # 输出结果表格
        print(f"\n  {'模型':<15} {'R²':<12} {'RMSE':<12}")
        print("  " + "-" * 40)
        
        for name, res in sorted(results.items(), key=lambda x: -x[1].get('R2', -999)):
            if res['success']:
                print(f"  {name:<15} {res['R2']:<12.4f} {res['RMSE']:<12.4f}")
        
        # 判定
        r2_dil = results.get('Dilaton', {}).get('R2', np.nan)
        r2_lin = results.get('Linear', {}).get('R2', np.nan)
        
        if not np.isnan(r2_dil) and not np.isnan(r2_lin):
            diff = r2_dil - r2_lin
            print(f"\n  Dilaton R² - Linear R² = {diff:+.4f}")
            
            if diff > 0.05:
                print("  ✅ Dilaton显著优于线性模型！")
            elif diff > 0:
                print("  🔶 Dilaton略优于线性模型")
            else:
                print("  ❌ 线性模型更好")
        
        all_results[phi_col] = {
            'data': df,
            'V': V,
            'TED': TED,
            'models': results,
            'corr': corr
        }
    
    # ============================================
    # 汇总报告
    # ============================================
    
    print("\n" + "=" * 70)
    print("汇总报告")
    print("=" * 70)
    
    print(f"\n{'Φ指标':<10} {'样本':<8} {'相关系数':<12} {'Dilaton R²':<14} {'Linear R²':<14} {'判定':<10}")
    print("-" * 75)
    
    for phi_col, res in all_results.items():
        models = res['models']
        n = len(res['V'])
        corr = res['corr']
        r2_dil = models.get('Dilaton', {}).get('R2', np.nan)
        r2_lin = models.get('Linear', {}).get('R2', np.nan)
        
        diff = r2_dil - r2_lin if not np.isnan(r2_dil) else np.nan
        
        if not np.isnan(diff):
            if diff > 0.05:
                verdict = "✅ Dilaton"
            elif diff > 0:
                verdict = "🔶 略优"
            else:
                verdict = "❌ Linear"
        else:
            verdict = "N/A"
        
        r2_dil_str = f"{r2_dil:.4f}" if not np.isnan(r2_dil) else "拟合失败"
        r2_lin_str = f"{r2_lin:.4f}" if not np.isnan(r2_lin) else "拟合失败"
        
        print(f"{phi_col:<10} {n:<8} {corr:<+12.4f} {r2_dil_str:<14} {r2_lin_str:<14} {verdict}")
    
    # ============================================
    # P2 最终判定
    # ============================================
    
    print("\n" + "=" * 70)
    print("P2 验证结论")
    print("=" * 70)
    
    if 'TED' in all_results:
        models = all_results['TED']['models']
        corr = all_results['TED']['corr']
        
        print(f"\n1. 相关性检验:")
        print(f"   Corr(V, TED) = {corr:.4f}")
        if corr < 0:
            print("   ✓ 负相关，符合Dilaton预测")
        else:
            print("   ✗ 正相关，与Dilaton预测相反")
            print("   物理解释：Dilaton公式预测高TED→低V")
            print("   但数据显示高TED时期V也较高")
        
        print(f"\n2. 模型拟合:")
        if 'Dilaton' in models and models['Dilaton']['success']:
            res = models['Dilaton']
            print(f"   Dilaton公式: V = {res['V0']:.4f} · √(1 - ((TED-{res['TED_0']:.4f})/({res['TED_crit']:.4f}-{res['TED_0']:.4f}))²)")
            print(f"   参数:")
            print(f"     V₀ (正常流速) = {res['V0']:.4f}")
            print(f"     TED₀ (结构摩擦) = {res['TED_0']:.4f}%")
            print(f"     TED_crit (视界) = {res['TED_crit']:.4f}%")
            print(f"     φₕ (临界摩擦) = {res['phi_h']:.4f}%")
            print(f"   R² = {res['R2']:.4f}")
        else:
            print("   Dilaton模型拟合失败")
        
        if 'Linear' in models:
            print(f"   Linear R² = {models['Linear']['R2']:.4f}")
        
        print(f"\n3. 最终判定:")
        if corr > 0:
            print("   ❌ P2预测失败: V与TED正相关，与Dilaton理论相反")
            print("   可能原因:")
            print("     - TED不是正确的Φ映射")
            print("     - 需要考虑滞后效应")
            print("     - 需要分危机/正常时期分析")
        else:
            r2_dil = models.get('Dilaton', {}).get('R2', 0)
            if r2_dil > 0.5:
                print("   ✅ P2预测成功: Dilaton模型解释力强")
            elif r2_dil > 0.3:
                print("   🔶 P2部分成功: Dilaton模型有一定解释力")
            else:
                print("   ❌ P2预测失败: Dilaton模型解释力弱")
    
    return all_results

# ============================================
# 运行
# ============================================

if __name__ == "__main__":
    results = main()