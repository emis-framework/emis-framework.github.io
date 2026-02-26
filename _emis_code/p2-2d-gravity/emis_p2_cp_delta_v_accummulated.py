#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
EMIS P2: 商业票据市场验证（2D JT引力）- 累积流出版
================================================================================

核心公式：
  V = V₀ · √(1 - (φ/φₕ)²)

变量定义（修正版）：
  φ = CP利差 = 商业票据利率 - 国债利率（信用摩擦）
  V = 累积流出量 = -sum(ΔV, 4周).clip(0)（4周累积资金流出）

物理映射：
  高利差φ → 接近视界 → 累积流出V增加
  视界φₕ → V达到最大（完全冻结）

================================================================================
"""

import numpy as np
import pandas as pd
import requests
from io import StringIO
from scipy.optimize import minimize
from scipy import stats
import os
import warnings
warnings.filterwarnings('ignore')

# ============================================
# 参数设置
# ============================================

START_DATE = '2001-01-01'
END_DATE = '2025-12-31'
CACHE_DIR = './cache_p2_cp/'
CUMSUM_WINDOW = 4  # 4周累积

# ============================================
# 数据获取
# ============================================

def download_fred(series_id):
    """从FRED下载数据（带缓存）"""
    os.makedirs(CACHE_DIR, exist_ok=True)
    cache_path = os.path.join(CACHE_DIR, f'{series_id}.csv')
    
    if os.path.exists(cache_path):
        print(f"  ✓ 缓存: {series_id}")
        df = pd.read_csv(cache_path, index_col=0, parse_dates=True)
        return df
    
    print(f"  下载: {series_id}...")
    url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={series_id}"
    
    try:
        response = requests.get(url, timeout=30)
        df = pd.read_csv(StringIO(response.text), index_col=0, parse_dates=True, na_values=['.'])
        df.columns = [series_id]
        df.to_csv(cache_path)
        print(f"    ✓ {len(df)} 条记录")
        return df
    except Exception as e:
        print(f"    ✗ 下载失败: {e}")
        return None

# ============================================
# 数据处理
# ============================================

def prepare_data():
    """准备数据（累积流出量）"""
    print("\n【数据获取】")
    
    cp_rate = download_fred('DCPF3M')
    tbill = download_fred('DTB3')
    cp_outstanding = download_fred('COMPOUT')
    
    if cp_rate is None or tbill is None or cp_outstanding is None:
        return None
    
    print("\n【数据处理】")
    
    # 1. 利差
    rates = pd.DataFrame(index=cp_rate.index)
    rates['CP_rate'] = cp_rate.iloc[:, 0]
    rates['Tbill'] = tbill.reindex(cp_rate.index).iloc[:, 0]
    rates['phi'] = rates['CP_rate'] - rates['Tbill']
    rates = rates.dropna()
    
    rates_weekly = rates.resample('W-WED').mean().dropna()
    print(f"  周频利差: {len(rates_weekly)} 周")
    
    # 2. CP余额变化
    cp_outstanding.columns = ['V_level']
    cp_outstanding['V_level'] = cp_outstanding['V_level'] * 1e9
    cp_outstanding['dV'] = cp_outstanding['V_level'].diff()
    cp_outstanding = cp_outstanding.dropna()
    
    # 3. 计算4周累积流出量
    # V = -sum(ΔV, 4周)，然后取正（只看流出）
    cp_outstanding['V_cum'] = -cp_outstanding['dV'].rolling(CUMSUM_WINDOW).sum()
    cp_outstanding['V'] = cp_outstanding['V_cum'].clip(lower=0)  # 只看流出（V≥0）
    cp_outstanding = cp_outstanding.dropna()
    
    print(f"  {CUMSUM_WINDOW}周累积流出量: {len(cp_outstanding)} 周")
    print(f"    范围: {cp_outstanding['V'].min()/1e9:.1f}B 到 {cp_outstanding['V'].max()/1e9:.1f}B")
    
    # 4. 对齐
    all_weeks = pd.date_range(
        start=max(rates_weekly.index.min(), cp_outstanding.index.min()),
        end=min(rates_weekly.index.max(), cp_outstanding.index.max()),
        freq='W-WED'
    )
    
    data = pd.DataFrame(index=all_weeks)
    data['phi'] = rates_weekly['phi'].reindex(all_weeks, method='ffill')
    data['V'] = cp_outstanding['V'].reindex(all_weeks, method='ffill')
    data['dV'] = cp_outstanding['dV'].reindex(all_weeks, method='ffill')  # 保留原始ΔV
    data = data.dropna()
    
    data = data[(data.index >= START_DATE) & (data.index <= END_DATE)]
    
    print(f"\n【最终数据】")
    print(f"  时间: {data.index[0].date()} 到 {data.index[-1].date()}")
    print(f"  样本: {len(data)} 周")
    print(f"  φ范围: {data['phi'].min():.3f}% 到 {data['phi'].max():.3f}%")
    print(f"  V范围: {data['V'].min()/1e9:.1f}B 到 {data['V'].max()/1e9:.1f}B")
    print(f"  V>0的周数: {(data['V'] > 0).sum()} ({(data['V'] > 0).mean()*100:.1f}%)")
    
    return data

# ============================================
# 2D JT 引力公式
# ============================================

def jt_2d_velocity(phi, V0, phi_h):
    """
    V = V₀ · √(1 - (φ/φₕ)²)
    
    注意：这里V是"流出量"，所以：
      φ小 → V小（没有流出）
      φ大 → V大（大量流出）
    
    需要反转公式！
    """
    ratio_sq = (phi / phi_h) ** 2
    inner = np.clip(1 - ratio_sq, 0, None)
    return V0 * np.sqrt(inner)


def jt_2d_outflow(phi, V0, phi_h):
    """
    反转的JT公式：流出量随φ增加
    
    V = V₀ · √((φ/φₕ)²) = V₀ · |φ/φₕ|
    
    或者用：
    V = V₀ · (1 - √(1 - (φ/φₕ)²))
    
    这样：φ=0 → V=0，φ=φₕ → V=V₀
    """
    ratio_sq = (phi / phi_h) ** 2
    ratio_sq = np.clip(ratio_sq, 0, 1)  # 防止超过1
    inner = np.clip(1 - ratio_sq, 0, None)
    return V0 * (1 - np.sqrt(inner))


def jt_2d_simple(phi, V0, phi_h):
    """
    简化版：线性映射
    V = V₀ · (φ/φₕ)
    """
    return V0 * np.clip(phi / phi_h, 0, 1)

# ============================================
# 拟合
# ============================================

def fit_jt_outflow(phi, V):
    """拟合反转JT模型（流出量）"""
    phi_max = np.max(phi)
    phi_positive = phi[phi > 0]  # 只用正利差
    V_max = np.max(V)
    
    V0_init = V_max * 1.2
    phi_h_init = phi_max * 1.2
    
    print(f"\n  初始估计:")
    print(f"    V₀ = {V0_init/1e9:.1f}B")
    print(f"    φₕ = {phi_h_init:.3f}%")
    
    def loss(params):
        V0, phi_h = params
        if V0 <= 0 or phi_h <= 0:
            return 1e20
        pred = jt_2d_outflow(phi, V0, phi_h)
        if np.any(np.isnan(pred)):
            return 1e20
        return np.mean((V - pred) ** 2)
    
    result = minimize(loss, x0=[V0_init, phi_h_init], method='Nelder-Mead', 
                     options={'maxiter': 10000})
    
    if result.fun < 1e19:
        V0_fit, phi_h_fit = result.x
        pred = jt_2d_outflow(phi, V0_fit, phi_h_fit)
        ss_res = np.sum((V - pred) ** 2)
        ss_tot = np.sum((V - np.mean(V)) ** 2)
        r2 = 1 - ss_res / ss_tot
        
        return {'success': True, 'V0': V0_fit, 'phi_h': phi_h_fit, 
                'R2': r2, 'pred': pred, 'formula': 'V = V₀·(1-√(1-(φ/φₕ)²))'}
    return {'success': False, 'R2': np.nan}


def fit_jt_simple(phi, V):
    """拟合简化JT模型（线性）"""
    phi_max = np.max(phi)
    V_max = np.max(V)
    
    V0_init = V_max * 1.2
    phi_h_init = phi_max * 1.2
    
    def loss(params):
        V0, phi_h = params
        if V0 <= 0 or phi_h <= 0:
            return 1e20
        pred = jt_2d_simple(phi, V0, phi_h)
        return np.mean((V - pred) ** 2)
    
    result = minimize(loss, x0=[V0_init, phi_h_init], method='Nelder-Mead',
                     options={'maxiter': 10000})
    
    if result.fun < 1e19:
        V0_fit, phi_h_fit = result.x
        pred = jt_2d_simple(phi, V0_fit, phi_h_fit)
        ss_res = np.sum((V - pred) ** 2)
        ss_tot = np.sum((V - np.mean(V)) ** 2)
        r2 = 1 - ss_res / ss_tot
        
        return {'success': True, 'V0': V0_fit, 'phi_h': phi_h_fit,
                'R2': r2, 'pred': pred, 'formula': 'V = V₀·(φ/φₕ)'}
    return {'success': False, 'R2': np.nan}


def fit_linear_model(phi, V):
    """线性模型"""
    slope, intercept, r_value, _, _ = stats.linregress(phi, V)
    pred = intercept + slope * phi
    return {'success': True, 'a': intercept, 'b': slope, 
            'R2': r_value ** 2, 'pred': pred}


def fit_quadratic_model(phi, V):
    """二次模型：V = a + b·φ + c·φ²"""
    coeffs = np.polyfit(phi, V, 2)
    pred = np.polyval(coeffs, phi)
    ss_res = np.sum((V - pred) ** 2)
    ss_tot = np.sum((V - np.mean(V)) ** 2)
    r2 = 1 - ss_res / ss_tot
    return {'success': True, 'coeffs': coeffs, 'R2': r2, 'pred': pred}

# ============================================
# 主程序
# ============================================

def main():
    print("=" * 70)
    print("EMIS P2: 商业票据验证 - 累积流出版")
    print("=" * 70)
    print(f"\n变量定义:")
    print(f"  φ = CP利差（信用摩擦）")
    print(f"  V = {CUMSUM_WINDOW}周累积流出量 = -sum(ΔV).clip(0)")
    print(f"\n预测: 高利差 → 累积流出增加")
    print("=" * 70)
    
    # 1. 准备数据
    data = prepare_data()
    if data is None:
        return None
    
    phi = data['phi'].values
    V = data['V'].values
    
    # 2. 统计
    print("\n【统计】")
    print(f"  φ: 均值={np.mean(phi):.3f}%, 范围=[{np.min(phi):.3f}%, {np.max(phi):.3f}%]")
    print(f"  V: 均值={np.mean(V)/1e9:.1f}B, 范围=[{np.min(V)/1e9:.1f}B, {np.max(V)/1e9:.1f}B]")
    
    # 3. 相关性
    print("\n【相关性】")
    corr, p_value = stats.pearsonr(phi, V)
    print(f"  Corr(φ, V) = {corr:.4f}, p = {p_value:.2e}")
    
    if corr > 0:
        print("  ✓ 正相关：高利差 → 累积流出增加（符合预测！）")
    else:
        print("  ⚠ 负相关：与预测相反")
    
    # 4. 拟合模型
    print("\n" + "=" * 70)
    print("【拟合模型】")
    print("=" * 70)
    
    results = {}
    
    # 反转JT公式
    print("\n--- JT反转公式: V = V₀·(1-√(1-(φ/φₕ)²)) ---")
    jt_result = fit_jt_outflow(phi, V)
    if jt_result['success']:
        results['JT_outflow'] = jt_result
        print(f"  ✓ 拟合成功")
        print(f"    V₀ = {jt_result['V0']/1e9:.1f}B")
        print(f"    φₕ = {jt_result['phi_h']:.3f}%")
        print(f"    R² = {jt_result['R2']:.4f}")
    else:
        print(f"  ✗ 拟合失败")
    
    # 简化JT公式
    print("\n--- JT简化公式: V = V₀·(φ/φₕ) ---")
    jt_simple = fit_jt_simple(phi, V)
    if jt_simple['success']:
        results['JT_simple'] = jt_simple
        print(f"  ✓ 拟合成功")
        print(f"    V₀ = {jt_simple['V0']/1e9:.1f}B")
        print(f"    φₕ = {jt_simple['phi_h']:.3f}%")
        print(f"    R² = {jt_simple['R2']:.4f}")
    
    # 线性模型
    print("\n--- 线性模型: V = a + b·φ ---")
    linear = fit_linear_model(phi, V)
    results['Linear'] = linear
    print(f"  a = {linear['a']/1e9:.1f}B")
    print(f"  b = {linear['b']/1e9:.2f}B/%")
    print(f"  R² = {linear['R2']:.4f}")
    
    # 二次模型
    print("\n--- 二次模型: V = a + b·φ + c·φ² ---")
    quad = fit_quadratic_model(phi, V)
    results['Quadratic'] = quad
    print(f"  R² = {quad['R2']:.4f}")
    
    # 5. 模型排名
    print("\n【模型排名】")
    sorted_results = sorted(
        [(k, v) for k, v in results.items() if v.get('success', False)],
        key=lambda x: -x[1].get('R2', -999)
    )
    for i, (name, res) in enumerate(sorted_results, 1):
        print(f"  {i}. {name}: R²={res['R2']:.4f}")
    
    best_name, best_result = sorted_results[0]
    
    # 6. 关键时期
    print("\n【关键时期分析】")
    for name, start, end in [
        ("2008年9-10月 (雷曼)", '2008-09-01', '2008-10-31'),
        ("2008年11-12月 (Fed干预)", '2008-11-01', '2008-12-31'),
        ("2020年3-4月 (COVID)", '2020-03-01', '2020-04-30'),
        ("2019年 (正常期)", '2019-01-01', '2019-12-31'),
    ]:
        mask = (data.index >= start) & (data.index <= end)
        if mask.any():
            phi_p = phi[mask]
            V_p = V[mask]
            print(f"\n  {name}:")
            print(f"    φ: 均值={phi_p.mean():.3f}%, 最大={phi_p.max():.3f}%")
            print(f"    V: 均值={V_p.mean()/1e9:.1f}B, 最大={V_p.max()/1e9:.1f}B")
    
    # 7. 极端周
    print("\n【极端时期】")
    print("  累积流出最大的5周:")
    for date, row in data.nlargest(5, 'V').iterrows():
        print(f"    {date.date()}: φ={row['phi']:.3f}%, V={row['V']/1e9:.1f}B")
    
    print("\n  利差最高的5周:")
    for date, row in data.nlargest(5, 'phi').iterrows():
        print(f"    {date.date()}: φ={row['phi']:.3f}%, V={row['V']/1e9:.1f}B")
    
    # 8. 物理解释
    if jt_result['success']:
        print("\n【物理解释】")
        phi_h = jt_result['phi_h']
        V0 = jt_result['V0']
        print(f"  JT公式: V = {V0/1e9:.0f}B · (1 - √(1 - (φ/{phi_h:.2f}%)²))")
        print(f"  视界利差: φₕ = {phi_h:.2f}%")
        print(f"  最大流出: V₀ = {V0/1e9:.0f}B")
        print(f"\n  2008年10月:")
        print(f"    最大利差 = {np.max(phi):.2f}%")
        print(f"    达到视界的 {np.max(phi)/phi_h*100:.0f}%")
    
    # 9. 结论
    print("\n" + "=" * 70)
    print("【结论】")
    print("=" * 70)
    
    print(f"\n  相关性: Corr(φ, V) = {corr:.4f}")
    if corr > 0:
        print("  ✓ 方向正确：高利差 → 累积流出增加")
    else:
        print("  ✗ 方向错误")
    
    print(f"\n  最佳模型: {best_name} (R²={best_result['R2']:.4f})")
    
    r2_jt = jt_result.get('R2', np.nan) if jt_result.get('success') else np.nan
    r2_lin = linear['R2']
    
    if not np.isnan(r2_jt):
        diff = r2_jt - r2_lin
        print(f"  JT R²={r2_jt:.4f}, Linear R²={r2_lin:.4f}, 差={diff:+.4f}")
    
    if best_name.startswith('JT') and corr > 0:
        print("\n  ✅ P2成功: JT模型是最佳！")
    elif corr > 0 and r2_jt > r2_lin:
        print("\n  🔶 P2部分成功: JT优于线性")
    elif corr > 0:
        print(f"\n  🔶 P2部分成功: 方向对，但{best_name}更好")
    else:
        print("\n  ❌ P2失败")
    
    return {'data': data, 'results': results, 'corr': corr}

# ============================================
# 运行
# ============================================

if __name__ == "__main__":
    output = main()