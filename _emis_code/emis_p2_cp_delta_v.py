#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
EMIS P2: 商业票据市场验证（2D JT引力）- 修正版
================================================================================

修正：用余额变化ΔV代替余额V

核心公式：
  V = V₀ · √(1 - (φ/φₕ)²)

变量：
  φ = CP利差 = 商业票据利率 - 国债利率
  V = ΔCP余额 = 周度余额变化（新发行代理）

预测：高利差 → 余额下降（ΔV<0）→ 融资冻结

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
SMOOTH_WINDOW = 1  # 不平滑，用原始周数据

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
    """准备数据（用余额变化代替余额）"""
    print("\n【数据获取】")
    
    cp_rate = download_fred('DCPF3M')
    tbill = download_fred('DTB3')
    cp_outstanding = download_fred('COMPOUT')
    
    if cp_rate is None or tbill is None or cp_outstanding is None:
        return None
    
    print("\n【原始数据】")
    cp_vals = cp_outstanding.iloc[:, 0].dropna()
    print(f"  CP余额范围: {cp_vals.min():.0f}B 到 {cp_vals.max():.0f}B")
    
    print("\n【数据处理】")
    
    # 1. 利差
    rates = pd.DataFrame(index=cp_rate.index)
    rates['CP_rate'] = cp_rate.iloc[:, 0]
    rates['Tbill'] = tbill.reindex(cp_rate.index).iloc[:, 0]
    rates['phi'] = rates['CP_rate'] - rates['Tbill']
    rates = rates.dropna()
    
    rates_weekly = rates.resample('W-WED').mean().dropna()
    print(f"  周频利差: {len(rates_weekly)} 周")
    
    # 2. CP余额 → 变化量
    cp_outstanding.columns = ['V_level']
    cp_outstanding['V_level'] = cp_outstanding['V_level'] * 1e9  # 转为美元
    
    # 计算周度变化（ΔV）
    cp_outstanding['V'] = cp_outstanding['V_level'].diff()
    cp_outstanding = cp_outstanding.dropna()
    
    print(f"  CP余额变化: {len(cp_outstanding)} 周")
    print(f"    ΔV范围: {cp_outstanding['V'].min()/1e9:.1f}B 到 {cp_outstanding['V'].max()/1e9:.1f}B")
    
    # 3. 对齐
    all_weeks = pd.date_range(
        start=max(rates_weekly.index.min(), cp_outstanding.index.min()),
        end=min(rates_weekly.index.max(), cp_outstanding.index.max()),
        freq='W-WED'
    )
    
    data = pd.DataFrame(index=all_weeks)
    data['phi'] = rates_weekly['phi'].reindex(all_weeks, method='ffill')
    data['V'] = cp_outstanding['V'].reindex(all_weeks, method='ffill')
    data = data.dropna()
    
    data = data[(data.index >= START_DATE) & (data.index <= END_DATE)]
    
    print(f"\n【最终数据】")
    print(f"  时间: {data.index[0].date()} 到 {data.index[-1].date()}")
    print(f"  样本: {len(data)} 周")
    print(f"  φ范围: {data['phi'].min():.3f}% 到 {data['phi'].max():.3f}%")
    print(f"  ΔV范围: {data['V'].min()/1e9:.1f}B 到 {data['V'].max()/1e9:.1f}B")
    
    return data

# ============================================
# 2D JT 引力公式
# ============================================

def jt_2d_velocity(phi, V0, phi_h):
    """V = V₀ · √(1 - (φ/φₕ)²)"""
    ratio_sq = (phi / phi_h) ** 2
    inner = np.clip(1 - ratio_sq, 0, None)
    return V0 * np.sqrt(inner)

# ============================================
# 拟合
# ============================================

def fit_jt_model(phi, V):
    """拟合JT模型"""
    phi_max = np.max(phi)
    V_max = np.max(V)
    V_min = np.min(V)
    
    # 注意：V现在可能是负数（余额下降）
    # JT公式要求V≥0，所以需要调整
    
    # 方案：将V平移，使最小值为0
    V_shift = V - V_min  # 现在V_shift ≥ 0
    V_shift_max = np.max(V_shift)
    
    V0_init = V_shift_max * 1.1
    phi_h_init = phi_max * 1.5
    
    print(f"\n  数据范围:")
    print(f"    φ: {np.min(phi):.3f}% 到 {phi_max:.3f}%")
    print(f"    V: {V_min/1e9:.1f}B 到 {V_max/1e9:.1f}B")
    print(f"    V_shift: 0 到 {V_shift_max/1e9:.1f}B")
    
    print(f"\n  初始估计:")
    print(f"    V₀ = {V0_init/1e9:.1f}B")
    print(f"    φₕ = {phi_h_init:.3f}%")
    
    def loss(params):
        V0, phi_h = params
        if V0 <= 0 or phi_h <= phi_max:
            return 1e20
        pred = jt_2d_velocity(phi, V0, phi_h)
        if np.any(np.isnan(pred)):
            return 1e20
        return np.mean((V_shift - pred) ** 2)
    
    result = minimize(loss, x0=[V0_init, phi_h_init], method='Nelder-Mead', options={'maxiter': 10000})
    
    if result.fun < 1e19:
        V0_fit, phi_h_fit = result.x
        pred = jt_2d_velocity(phi, V0_fit, phi_h_fit)
        ss_res = np.sum((V_shift - pred) ** 2)
        ss_tot = np.sum((V_shift - np.mean(V_shift)) ** 2)
        r2 = 1 - ss_res / ss_tot
        
        return {'success': True, 'V0': V0_fit, 'phi_h': phi_h_fit, 'R2': r2, 
                'V_min_original': V_min, 'pred': pred}
    return {'success': False, 'R2': np.nan}


def fit_linear_model(phi, V):
    """线性模型"""
    slope, intercept, r_value, _, _ = stats.linregress(phi, V)
    return {'success': True, 'a': intercept, 'b': slope, 'R2': r_value ** 2}

# ============================================
# 主程序
# ============================================

def main():
    print("=" * 70)
    print("EMIS P2: 商业票据验证 - 修正版（用ΔV）")
    print("=" * 70)
    print(f"\n公式: V = V₀ · √(1 - (φ/φₕ)²)")
    print(f"  φ = CP利差")
    print(f"  V = ΔCP余额（周变化）")
    print(f"\n预测: 高利差 → ΔV<0 → 融资冻结")
    print("=" * 70)
    
    # 1. 准备数据
    data = prepare_data()
    if data is None:
        return None
    
    # 2. 平滑（如果需要）
    if SMOOTH_WINDOW > 1:
        print(f"\n【平滑】{SMOOTH_WINDOW}周移动平均")
        data['phi_smooth'] = data['phi'].rolling(SMOOTH_WINDOW, min_periods=1).mean()
        data['V_smooth'] = data['V'].rolling(SMOOTH_WINDOW, min_periods=1).mean()
    else:
        print(f"\n【不平滑】使用原始周数据")
        data['phi_smooth'] = data['phi']
        data['V_smooth'] = data['V']
    
    phi = data['phi_smooth'].values
    V = data['V_smooth'].values
    
    # 3. 统计
    print("\n【统计】")
    print(f"  φ: 均值={np.mean(phi):.3f}%, 范围=[{np.min(phi):.3f}%, {np.max(phi):.3f}%]")
    print(f"  ΔV: 均值={np.mean(V)/1e9:.1f}B, 范围=[{np.min(V)/1e9:.1f}B, {np.max(V)/1e9:.1f}B]")
    
    # 4. 相关性
    print("\n【相关性】")
    corr, p_value = stats.pearsonr(phi, V)
    print(f"  Corr(φ, ΔV) = {corr:.4f}, p = {p_value:.2e}")
    
    if corr < 0:
        print("  ✓ 负相关：高利差 → ΔV下降（符合预测）")
    else:
        print("  ⚠ 正相关：高利差 → ΔV上升（与预测相反）")
    
    # 5. 拟合
    print("\n" + "=" * 70)
    print("【拟合JT模型】")
    print("=" * 70)
    
    jt_result = fit_jt_model(phi, V)
    
    if jt_result['success']:
        print(f"\n  ✓ 拟合成功")
        print(f"    V₀ = {jt_result['V0']/1e9:.1f}B")
        print(f"    φₕ = {jt_result['phi_h']:.3f}%")
        print(f"    R² = {jt_result['R2']:.4f}")
    else:
        print(f"\n  ✗ 拟合失败")
    
    # 6. 对比
    print("\n【对比模型】")
    linear_result = fit_linear_model(phi, V)
    print(f"  Linear: R²={linear_result['R2']:.4f}, b={linear_result['b']/1e9:.2f}B/%")
    
    # 7. 关键时期
    print("\n【关键时期分析】")
    for name, start, end in [
        ("2008年9-10月 (雷曼破产)", '2008-09-01', '2008-10-31'),
        ("2008年11-12月 (Fed干预后)", '2008-11-01', '2008-12-31'),
        ("2020年3-4月 (COVID)", '2020-03-01', '2020-04-30'),
        ("2019年 (正常期)", '2019-01-01', '2019-12-31'),
    ]:
        mask = (data.index >= start) & (data.index <= end)
        if mask.any():
            phi_p = phi[mask]
            V_p = V[mask]
            print(f"\n  {name}:")
            print(f"    φ: 均值={phi_p.mean():.3f}%, 最大={phi_p.max():.3f}%")
            print(f"    ΔV: 均值={V_p.mean()/1e9:.1f}B, 最小={V_p.min()/1e9:.1f}B, 最大={V_p.max()/1e9:.1f}B")
            print(f"    ΔV<0的周数: {(V_p < 0).sum()} / {len(V_p)}")
    
    # 8. 极端周
    print("\n【极端时期】")
    print("  ΔV最负的5周（融资流出最多）:")
    for date, row in data.nsmallest(5, 'V_smooth').iterrows():
        print(f"    {date.date()}: φ={row['phi_smooth']:.3f}%, ΔV={row['V_smooth']/1e9:.1f}B")
    
    print("\n  利差最高的5周:")
    for date, row in data.nlargest(5, 'phi_smooth').iterrows():
        print(f"    {date.date()}: φ={row['phi_smooth']:.3f}%, ΔV={row['V_smooth']/1e9:.1f}B")
    
    # 9. 结论
    print("\n" + "=" * 70)
    print("【结论】")
    print("=" * 70)
    
    r2_jt = jt_result.get('R2', np.nan) if jt_result['success'] else np.nan
    r2_lin = linear_result['R2']
    
    print(f"\n  相关性: Corr(φ, ΔV) = {corr:.4f}")
    
    if corr < 0:
        print("  ✓ 方向正确：高利差 → 融资流出")
        if r2_jt > r2_lin:
            print(f"  ✅ P2成功: JT R²={r2_jt:.4f} > Linear R²={r2_lin:.4f}")
        else:
            print(f"  🔶 P2部分成功: 方向对但JT不优于Linear")
    else:
        print("  ✗ 方向错误：高利差 → 融资流入？")
        print("  ❌ P2失败")
    
    return {'data': data, 'corr': corr, 'jt': jt_result, 'linear': linear_result}

if __name__ == "__main__":
    output = main()