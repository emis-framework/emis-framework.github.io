#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
EMIS P2: 商业票据市场验证（2D JT引力）
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
SMOOTH_WINDOW = 4

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
    """准备商业票据市场数据"""
    print("\n【数据获取】")
    
    cp_rate = download_fred('DCPF3M')
    tbill = download_fred('DTB3')
    cp_outstanding = download_fred('COMPOUT')
    
    if cp_rate is None or tbill is None or cp_outstanding is None:
        return None
    
    # 诊断原始数据
    print("\n【原始数据诊断】")
    print(f"  CP利率 (DCPF3M):")
    print(f"    范围: {cp_rate.iloc[:, 0].min():.4f} 到 {cp_rate.iloc[:, 0].max():.4f}")
    print(f"    单位: 百分比 (%)")
    
    print(f"  国债利率 (DTB3):")
    print(f"    范围: {tbill.iloc[:, 0].min():.4f} 到 {tbill.iloc[:, 0].max():.4f}")
    print(f"    单位: 百分比 (%)")
    
    print(f"  CP余额 (COMPOUT):")
    cp_vals = cp_outstanding.iloc[:, 0].dropna()
    print(f"    范围: {cp_vals.min():.4f} 到 {cp_vals.max():.4f}")
    print(f"    均值: {cp_vals.mean():.4f}")
    print(f"    样本前5个值: {cp_vals.head().tolist()}")
    print(f"    样本后5个值: {cp_vals.tail().tolist()}")
    
    # COMPOUT 单位是 十亿美元（Billions of Dollars）
    # 需要确认是否需要转换
    
    print("\n【数据处理】")
    
    # 1. 利差计算
    rates = pd.DataFrame(index=cp_rate.index)
    rates['CP_rate'] = cp_rate.iloc[:, 0]
    rates['Tbill'] = tbill.reindex(cp_rate.index).iloc[:, 0]
    rates['phi'] = rates['CP_rate'] - rates['Tbill']
    rates = rates.dropna()
    
    print(f"  日频利差: {len(rates)} 条")
    
    # 2. 转周频（周三）
    rates_weekly = rates.resample('W-WED').mean()
    rates_weekly = rates_weekly.dropna()
    
    print(f"  周频利差: {len(rates_weekly)} 条")
    
    # 3. CP余额处理
    cp_outstanding.columns = ['V_raw']
    cp_outstanding = cp_outstanding.dropna()
    
    # 检查V是否需要缩放
    # COMPOUT 单位是十亿美元，数值应该在 几百到几千
    print(f"  CP余额原始值范围: {cp_outstanding['V_raw'].min():.2f} 到 {cp_outstanding['V_raw'].max():.2f}")
    
    # 转换为实际美元（乘以1e9）
    cp_outstanding['V'] = cp_outstanding['V_raw'] * 1e9
    
    print(f"  CP余额(美元)范围: {cp_outstanding['V'].min():.2e} 到 {cp_outstanding['V'].max():.2e}")
    
    # 4. 对齐
    all_weeks = pd.date_range(
        start=max(rates_weekly.index.min(), cp_outstanding.index.min()),
        end=min(rates_weekly.index.max(), cp_outstanding.index.max()),
        freq='W-WED'
    )
    
    data = pd.DataFrame(index=all_weeks)
    data['phi'] = rates_weekly['phi'].reindex(all_weeks, method='ffill')
    data['V'] = cp_outstanding['V'].reindex(all_weeks, method='ffill')
    data = data.dropna()
    
    print(f"  对齐后: {len(data)} 周")
    
    if len(data) == 0:
        return None
    
    data = data[(data.index >= START_DATE) & (data.index <= END_DATE)]
    
    print(f"\n【最终数据】")
    print(f"  时间: {data.index[0].date()} 到 {data.index[-1].date()}")
    print(f"  样本: {len(data)} 周")
    print(f"  φ范围: {data['phi'].min():.3f}% 到 {data['phi'].max():.3f}%")
    print(f"  V范围: {data['V'].min()/1e9:.0f}B 到 {data['V'].max()/1e9:.0f}B")
    
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
    """拟合2D JT模型"""
    phi_max = np.max(phi)
    V_max = np.max(V)
    
    V0_init = V_max * 1.1
    phi_h_init = phi_max * 1.5
    
    print(f"\n  初始估计:")
    print(f"    V₀ = {V0_init/1e9:.0f}B")
    print(f"    φₕ = {phi_h_init:.3f}%")
    
    def loss(params):
        V0, phi_h = params
        if V0 <= 0 or phi_h <= phi_max:
            return 1e20
        pred = jt_2d_velocity(phi, V0, phi_h)
        if np.any(np.isnan(pred)):
            return 1e20
        return np.mean((V - pred) ** 2)
    
    result = minimize(loss, x0=[V0_init, phi_h_init], method='Nelder-Mead', options={'maxiter': 10000})
    
    if result.fun < 1e19:
        V0_fit, phi_h_fit = result.x
        pred = jt_2d_velocity(phi, V0_fit, phi_h_fit)
        ss_res = np.sum((V - pred) ** 2)
        ss_tot = np.sum((V - np.mean(V)) ** 2)
        r2 = 1 - ss_res / ss_tot
        
        return {'success': True, 'V0': V0_fit, 'phi_h': phi_h_fit, 'R2': r2, 'pred': pred}
    return {'success': False, 'R2': np.nan}


def fit_linear_model(phi, V):
    """线性模型"""
    slope, intercept, r_value, _, _ = stats.linregress(phi, V)
    return {'success': True, 'a': intercept, 'b': slope, 'R2': r_value ** 2}


def fit_exp_model(phi, V):
    """指数模型"""
    log_V = np.log(np.maximum(V, 1))
    slope, intercept, r_value, _, _ = stats.linregress(phi, log_V)
    pred = np.exp(intercept + slope * phi)
    ss_res = np.sum((V - pred) ** 2)
    ss_tot = np.sum((V - np.mean(V)) ** 2)
    return {'success': True, 'a': np.exp(intercept), 'b': -slope, 'R2': 1 - ss_res / ss_tot}

# ============================================
# 主程序
# ============================================

def main():
    print("=" * 70)
    print("EMIS P2: 商业票据市场验证（2D JT引力）")
    print("=" * 70)
    print(f"\n公式: V = V₀ · √(1 - (φ/φₕ)²)")
    print(f"  φ = CP利率 - 国债利率")
    print(f"  V = 商业票据余额")
    print("=" * 70)
    
    # 1. 准备数据
    data = prepare_data()
    if data is None:
        print("\n✗ 数据准备失败")
        return None
    
    # 2. 平滑
    print(f"\n【平滑】{SMOOTH_WINDOW}周移动平均")
    data['phi_smooth'] = data['phi'].rolling(SMOOTH_WINDOW, min_periods=1).mean()
    data['V_smooth'] = data['V'].rolling(SMOOTH_WINDOW, min_periods=1).mean()
    
    phi = data['phi_smooth'].values
    V = data['V_smooth'].values
    
    # 3. 统计
    print("\n【统计】")
    print(f"  φ: 均值={np.mean(phi):.3f}%, 范围=[{np.min(phi):.3f}%, {np.max(phi):.3f}%]")
    print(f"  V: 均值={np.mean(V)/1e9:.0f}B, 范围=[{np.min(V)/1e9:.0f}B, {np.max(V)/1e9:.0f}B]")
    
    # 4. 相关性
    print("\n【相关性】")
    corr, p_value = stats.pearsonr(phi, V)
    print(f"  Corr(φ, V) = {corr:.4f}, p = {p_value:.2e}")
    print(f"  {'✓ 负相关' if corr < 0 else '⚠ 正相关'}")
    
    # 5. 拟合
    print("\n" + "=" * 70)
    print("【拟合JT模型】")
    print("=" * 70)
    
    jt_result = fit_jt_model(phi, V)
    
    if jt_result['success']:
        print(f"\n  ✓ 拟合成功")
        print(f"    V₀ = {jt_result['V0']/1e9:.0f}B")
        print(f"    φₕ = {jt_result['phi_h']:.3f}%")
        print(f"    R² = {jt_result['R2']:.4f}")
    else:
        print(f"\n  ✗ 拟合失败")
    
    # 6. 对比
    print("\n【对比模型】")
    linear_result = fit_linear_model(phi, V)
    print(f"  Linear: R²={linear_result['R2']:.4f}, b={linear_result['b']/1e9:.1f}B/%")
    
    exp_result = fit_exp_model(phi, V)
    print(f"  Exp:    R²={exp_result['R2']:.4f}")
    
    # 7. 排名
    results = {'JT_2D': jt_result, 'Linear': linear_result, 'Exp': exp_result}
    sorted_results = sorted(
        [(k, v) for k, v in results.items() if v.get('success', False)],
        key=lambda x: -x[1].get('R2', -999)
    )
    
    print("\n【模型排名】")
    for i, (name, res) in enumerate(sorted_results, 1):
        print(f"  {i}. {name}: R²={res['R2']:.4f}")
    
    # 8. 关键时期
    print("\n【关键时期】")
    for name, start, end in [
        ("2008年9-12月(雷曼)", '2008-09-01', '2008-12-31'),
        ("2020年3-4月(COVID)", '2020-03-01', '2020-04-30'),
    ]:
        mask = (data.index >= start) & (data.index <= end)
        if mask.any():
            print(f"  {name}:")
            print(f"    φ: {phi[mask].mean():.3f}% ~ {phi[mask].max():.3f}%")
            print(f"    V: {V[mask].min()/1e9:.0f}B ~ {V[mask].max()/1e9:.0f}B")
    
    # 9. 极端日期
    print("\n【极端时期】")
    print("  利差最高5周:")
    for date, row in data.nlargest(5, 'phi_smooth').iterrows():
        print(f"    {date.date()}: φ={row['phi_smooth']:.3f}%, V={row['V_smooth']/1e9:.0f}B")
    
    print("  余额最低5周:")
    for date, row in data.nsmallest(5, 'V_smooth').iterrows():
        print(f"    {date.date()}: φ={row['phi_smooth']:.3f}%, V={row['V_smooth']/1e9:.0f}B")
    
    # 10. 结论
    print("\n" + "=" * 70)
    print("【结论】")
    print("=" * 70)
    
    r2_jt = jt_result.get('R2', np.nan) if jt_result['success'] else np.nan
    r2_lin = linear_result['R2']
    best = sorted_results[0][0]
    
    print(f"\n  相关性: {corr:.4f} ({'✓负' if corr < 0 else '✗正'})")
    if not np.isnan(r2_jt):
        print(f"  JT R²: {r2_jt:.4f}")
    print(f"  Linear R²: {r2_lin:.4f}")
    print(f"  最佳模型: {best}")
    
    if best == 'JT_2D' and corr < 0:
        print("\n  ✅ P2成功!")
    elif corr < 0 and r2_jt > r2_lin:
        print("\n  🔶 P2部分成功")
    elif corr < 0:
        print("\n  ❌ P2失败: JT不是最佳")
    else:
        print("\n  ❌ P2失败: 方向错误")
    
    return {'data': data, 'results': results, 'corr': corr}

if __name__ == "__main__":
    output = main()