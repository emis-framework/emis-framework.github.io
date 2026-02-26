#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
EMIS P2: XLF 流动性验证（2D JT引力）- 修正版
================================================================================

核心公式（2D JT AdS₂黑洞红移）：
------------------------------
V = V₀ · √(1 - (φ/φₕ)²)

变量定义（修正版）：
---------
φ = |r|                          价格波动（摩擦/Dilaton场）
V = DollarVolume / |r| = 1/ILLIQ  流动性深度（本地速度）
φₕ = 临界波动率                   视界值（拟合确定）
V₀ = 正常状态流动性深度            渐近速度（拟合确定）

修正原因：
---------
原定义 φ=ILLIQ, V=DollarVolume 存在问题：
  - V出现在φ的分母里，不独立
  - 恐慌抛售时成交量反而高，导致V↑

新定义：
  - φ = |r| 纯度量波动（危机时确实↑）
  - V = DV/|r| 吸收波动的能力（危机时应该↓）

公式行为：
---------
φ/φₕ → 0  :  V → V₀   （低波动，正常流动性）
φ/φₕ → 1  :  V → 0    （高波动，流动性枯竭）

================================================================================
"""

import numpy as np
import pandas as pd
import yfinance as yf
from scipy.optimize import minimize
from scipy import stats
import os
import warnings
warnings.filterwarnings('ignore')

# ============================================
# 参数设置
# ============================================

START_DATE = '2007-01-01'
END_DATE = '2025-12-31'
CACHE_DIR = './cache_p2_xlf/'
SMOOTH_WINDOW = 5  # 5日移动平均

# ============================================
# 数据获取（带缓存）
# ============================================

def download_with_cache(ticker):
    """
    下载股票数据（带缓存）
    """
    os.makedirs(CACHE_DIR, exist_ok=True)
    cache_file = f'{ticker}_{START_DATE}_{END_DATE}.csv'
    cache_path = os.path.join(CACHE_DIR, cache_file)
    
    if os.path.exists(cache_path):
        print(f"  ✓ 缓存: {ticker}")
        df = pd.read_csv(cache_path, index_col=0, parse_dates=True)
        return df
    
    print(f"  下载: {ticker}...")
    df = yf.download(ticker, start=START_DATE, end=END_DATE, progress=False)
    
    # 处理MultiIndex列名
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    
    df.to_csv(cache_path)
    print(f"    ✓ {len(df)} 条记录")
    
    return df

# ============================================
# 核心计算（修正版）
# ============================================

def calc_phi_and_V(df):
    """
    计算φ和V（修正版定义）
    
    修正版公式：
        φ = |r|                    价格波动（摩擦）
        V = DollarVolume / |r|     流动性深度（吸收波动能力）
    
    物理对应：
        φ = Dilaton场（时空摩擦）
        V = 本地速度（物质运动速度）
    """
    # 查找收盘价列
    if 'Close' in df.columns:
        close = df['Close']
    elif 'Adj Close' in df.columns:
        close = df['Adj Close']
    else:
        raise KeyError(f"找不到收盘价列: {df.columns.tolist()}")
    
    volume = df['Volume']
    
    # 收益率
    ret = close.pct_change()
    
    # 成交金额
    dollar_volume = close * volume
    
    # φ = |收益率|（波动/摩擦）
    phi = np.abs(ret)
    
    # V = 成交金额 / |收益率| = 1/ILLIQ（流动性深度）
    # 即：每1%波动需要多少资金
    V = dollar_volume / np.maximum(phi, 1e-10)  # 避免除零
    
    # 处理异常值
    phi = phi.replace([np.inf, -np.inf], np.nan)
    V = V.replace([np.inf, -np.inf], np.nan)
    
    return phi, V, ret, dollar_volume

# ============================================
# 2D JT 引力公式
# ============================================

def jt_2d_velocity(phi, V0, phi_h):
    """
    2D JT引力红移公式（本地速度）
    
    公式：V = V₀ · √(1 - (φ/φₕ)²)
    """
    ratio_sq = (phi / phi_h) ** 2
    inner = np.clip(1 - ratio_sq, 0, None)
    V = V0 * np.sqrt(inner)
    return V

# ============================================
# 拟合
# ============================================

def fit_jt_model(phi, V):
    """
    拟合2D JT模型
    
    待拟合参数：V₀, φₕ
    约束：V₀ > 0, φₕ > max(φ)
    """
    phi_max = np.max(phi)
    phi_median = np.median(phi)
    V_max = np.max(V)
    V_median = np.median(V)
    
    # 初始估计
    V0_init = np.percentile(V, 95)  # 高V时对应低φ
    phi_h_init = phi_max * 1.5      # 临界值略大于最大观测值
    
    print(f"\n  初始估计:")
    print(f"    V₀ = {V0_init:.2e}")
    print(f"    φₕ = {phi_h_init:.4f}")
    print(f"    max(φ) = {phi_max:.4f}")
    print(f"    median(φ) = {phi_median:.4f}")
    
    def loss(params):
        V0, phi_h = params
        if V0 <= 0 or phi_h <= phi_max:
            return 1e20
        pred = jt_2d_velocity(phi, V0, phi_h)
        if np.any(np.isnan(pred)):
            return 1e20
        return np.mean((V - pred) ** 2)
    
    result = minimize(
        loss,
        x0=[V0_init, phi_h_init],
        method='Nelder-Mead',
        options={'maxiter': 10000}
    )
    
    if result.fun < 1e19:
        V0_fit, phi_h_fit = result.x
        pred = jt_2d_velocity(phi, V0_fit, phi_h_fit)
        
        ss_res = np.sum((V - pred) ** 2)
        ss_tot = np.sum((V - np.mean(V)) ** 2)
        r2 = 1 - ss_res / ss_tot
        rmse = np.sqrt(np.mean((V - pred) ** 2))
        
        return {
            'success': True,
            'V0': V0_fit,
            'phi_h': phi_h_fit,
            'R2': r2,
            'RMSE': rmse,
            'pred': pred
        }
    else:
        return {'success': False, 'R2': np.nan}


def fit_linear_model(phi, V):
    """拟合线性模型：V = a + b·φ"""
    slope, intercept, r_value, p_value, std_err = stats.linregress(phi, V)
    pred = intercept + slope * phi
    rmse = np.sqrt(np.mean((V - pred) ** 2))
    
    return {
        'success': True,
        'a': intercept,
        'b': slope,
        'R2': r_value ** 2,
        'RMSE': rmse,
        'pred': pred
    }


def fit_inverse_model(phi, V):
    """拟合反比模型：V = a + b/φ"""
    inv_phi = 1 / np.maximum(phi, 1e-10)
    slope, intercept, r_value, p_value, std_err = stats.linregress(inv_phi, V)
    pred = intercept + slope * inv_phi
    rmse = np.sqrt(np.mean((V - pred) ** 2))
    
    return {
        'success': True,
        'a': intercept,
        'b': slope,
        'R2': r_value ** 2,
        'RMSE': rmse,
        'pred': pred
    }


def fit_power_model(phi, V):
    """拟合幂律模型：log(V) = a + b·log(φ)"""
    log_phi = np.log(np.maximum(phi, 1e-10))
    log_V = np.log(np.maximum(V, 1))
    
    slope, intercept, r_value, p_value, std_err = stats.linregress(log_phi, log_V)
    pred = np.exp(intercept + slope * log_phi)
    
    ss_res = np.sum((V - pred) ** 2)
    ss_tot = np.sum((V - np.mean(V)) ** 2)
    r2 = 1 - ss_res / ss_tot
    rmse = np.sqrt(np.mean((V - pred) ** 2))
    
    return {
        'success': True,
        'a': np.exp(intercept),
        'b': slope,
        'R2': r2,
        'RMSE': rmse,
        'pred': pred
    }

# ============================================
# 验证
# ============================================

def validate_fit(phi, V, jt_result, data):
    """验证拟合结果"""
    print("\n" + "-" * 50)
    print("拟合结果验证")
    print("-" * 50)
    
    if not jt_result['success']:
        print("  ✗ JT模型拟合失败")
        return
    
    V0 = jt_result['V0']
    phi_h = jt_result['phi_h']
    phi_max = np.max(phi)
    V_max = np.max(V)
    V_mean = np.mean(V)
    
    # 检查1：φₕ > max(φ)
    print(f"\n1. 视界值检查:")
    print(f"   φₕ = {phi_h:.4f} ({phi_h*100:.2f}%)")
    print(f"   max(φ) = {phi_max:.4f} ({phi_max*100:.2f}%)")
    if phi_h > phi_max:
        print(f"   ✓ φₕ > max(φ)")
    else:
        print(f"   ✗ φₕ ≤ max(φ)")
    
    # 检查2：V₀
    print(f"\n2. 渐近速度检查:")
    print(f"   V₀ = {V0:.2e}")
    print(f"   max(V) = {V_max:.2e}")
    print(f"   mean(V) = {V_mean:.2e}")
    print(f"   V₀/max(V) = {V0/V_max:.2f}")
    
    # 检查3：φ/φₕ 分布
    ratio = phi / phi_h
    print(f"\n3. φ/φₕ 分布:")
    print(f"   最小值: {np.min(ratio):.4f}")
    print(f"   均值: {np.mean(ratio):.4f}")
    print(f"   中位数: {np.median(ratio):.4f}")
    print(f"   最大值: {np.max(ratio):.4f}")
    
    # 检查4：关键时期
    print(f"\n4. 关键时期 φ/φₕ:")
    
    periods = [
        ("2008年9-11月 (金融危机)", '2008-09-01', '2008-11-30'),
        ("2020年3-4月 (COVID)", '2020-03-01', '2020-04-30'),
        ("2013-2019年 (正常期)", '2013-01-01', '2019-12-31')
    ]
    
    for name, start, end in periods:
        mask = (data.index >= start) & (data.index <= end)
        if mask.any():
            ratio_period = ratio[mask]
            print(f"   {name}:")
            print(f"     均值: {ratio_period.mean():.4f}, 最大: {ratio_period.max():.4f}")

# ============================================
# 主程序
# ============================================

def main():
    print("=" * 70)
    print("EMIS P2: XLF 流动性验证（2D JT引力）- 修正版")
    print("=" * 70)
    print(f"\n参数设置:")
    print(f"  START_DATE = {START_DATE}")
    print(f"  END_DATE = {END_DATE}")
    print(f"  SMOOTH_WINDOW = {SMOOTH_WINDOW}")
    print("\n核心公式: V = V₀ · √(1 - (φ/φₕ)²)")
    print("\n修正版定义:")
    print("  φ = |r|                 价格波动（摩擦）")
    print("  V = DollarVolume / |r|  流动性深度（吸收波动能力）")
    print("\n预测: 高波动 → 低流动性深度 → 流动性陷阱")
    print("=" * 70)
    
    # ==========================================
    # 1. 下载数据
    # ==========================================
    print("\n【1】获取数据...")
    xlf = download_with_cache('XLF')
    print(f"  列名: {xlf.columns.tolist()}")
    
    # ==========================================
    # 2. 计算φ和V
    # ==========================================
    print("\n【2】计算指标（修正版）...")
    phi, V, ret, dollar_volume = calc_phi_and_V(xlf)
    
    # 构建数据框
    data = pd.DataFrame({
        'phi': phi,
        'V': V,
        'ret': ret,
        'DV': dollar_volume
    }).dropna()
    
    print(f"  原始样本数: {len(data)} 天")
    
    # ==========================================
    # 3. 平滑
    # ==========================================
    print(f"\n【3】{SMOOTH_WINDOW}日移动平均平滑...")
    data['phi_smooth'] = data['phi'].rolling(SMOOTH_WINDOW).mean()
    data['V_smooth'] = data['V'].rolling(SMOOTH_WINDOW).mean()
    data = data.dropna()
    
    print(f"  平滑后样本数: {len(data)} 天")
    print(f"  时间范围: {data.index[0].date()} 到 {data.index[-1].date()}")
    
    phi = data['phi_smooth'].values
    V = data['V_smooth'].values
    
    # ==========================================
    # 4. 基本统计
    # ==========================================
    print("\n【4】基本统计")
    print(f"\n  φ = |收益率| (波动/摩擦):")
    print(f"    均值: {np.mean(phi):.4f} ({np.mean(phi)*100:.2f}%)")
    print(f"    中位数: {np.median(phi):.4f} ({np.median(phi)*100:.2f}%)")
    print(f"    最小值: {np.min(phi):.4f} ({np.min(phi)*100:.2f}%)")
    print(f"    最大值: {np.max(phi):.4f} ({np.max(phi)*100:.2f}%)")
    
    print(f"\n  V = DV/|r| (流动性深度):")
    print(f"    均值: {np.mean(V):.2e}")
    print(f"    中位数: {np.median(V):.2e}")
    print(f"    最小值: {np.min(V):.2e}")
    print(f"    最大值: {np.max(V):.2e}")
    
    # ==========================================
    # 5. 相关性检验
    # ==========================================
    print("\n【5】相关性检验")
    corr, p_value = stats.pearsonr(phi, V)
    print(f"  Pearson相关系数: {corr:.4f}")
    print(f"  p值: {p_value:.2e}")
    
    if corr < 0:
        print("  ✓ 负相关，符合2D JT预测（高波动→低流动性深度）")
    else:
        print("  ⚠ 正相关，与2D JT预测相反")
    
    # ==========================================
    # 6. 拟合JT模型
    # ==========================================
    print("\n" + "=" * 70)
    print("【6】拟合2D JT模型: V = V₀ · √(1 - (φ/φₕ)²)")
    print("=" * 70)
    
    jt_result = fit_jt_model(phi, V)
    
    if jt_result['success']:
        print(f"\n  拟合成功!")
        print(f"    V₀ = {jt_result['V0']:.2e}")
        print(f"    φₕ = {jt_result['phi_h']:.4f} ({jt_result['phi_h']*100:.2f}%)")
        print(f"    R² = {jt_result['R2']:.4f}")
        print(f"    RMSE = {jt_result['RMSE']:.2e}")
    else:
        print(f"\n  ✗ JT模型拟合失败")
    
    # ==========================================
    # 7. 对比模型
    # ==========================================
    print("\n" + "-" * 50)
    print("【7】对比模型")
    print("-" * 50)
    
    results = {'JT_2D': jt_result}
    
    # 线性
    linear_result = fit_linear_model(phi, V)
    results['Linear'] = linear_result
    print(f"\n  线性模型: V = a + b·φ")
    print(f"    a = {linear_result['a']:.2e}")
    print(f"    b = {linear_result['b']:.2e}")
    print(f"    R² = {linear_result['R2']:.4f}")
    
    # 反比
    inverse_result = fit_inverse_model(phi, V)
    results['Inverse'] = inverse_result
    print(f"\n  反比模型: V = a + b/φ")
    print(f"    a = {inverse_result['a']:.2e}")
    print(f"    b = {inverse_result['b']:.2e}")
    print(f"    R² = {inverse_result['R2']:.4f}")
    
    # 幂律
    power_result = fit_power_model(phi, V)
    results['Power'] = power_result
    print(f"\n  幂律模型: V = a · φ^b")
    print(f"    a = {power_result['a']:.2e}")
    print(f"    b = {power_result['b']:.4f}")
    print(f"    R² = {power_result['R2']:.4f}")
    
    # ==========================================
    # 8. 模型对比
    # ==========================================
    print("\n" + "=" * 70)
    print("【8】模型对比")
    print("=" * 70)
    
    print(f"\n  {'模型':<15} {'R²':<12} {'RMSE':<15}")
    print("  " + "-" * 45)
    
    sorted_results = sorted(
        [(k, v) for k, v in results.items() if v.get('success', False)],
        key=lambda x: -x[1].get('R2', -999)
    )
    
    for name, res in sorted_results:
        print(f"  {name:<15} {res['R2']:<12.4f} {res['RMSE']:<15.2e}")
    
    # ==========================================
    # 9. 验证
    # ==========================================
    validate_fit(phi, V, jt_result, data)
    
    # ==========================================
    # 10. 极端日期分析
    # ==========================================
    print("\n" + "-" * 50)
    print("【10】极端日期分析")
    print("-" * 50)
    
    print("\n  波动最高的10天（φ最大）:")
    worst_phi = data.nlargest(10, 'phi_smooth')
    for i, (date, row) in enumerate(worst_phi.iterrows(), 1):
        print(f"    {i:2}. {date.date()}: φ={row['phi_smooth']*100:.2f}%, V={row['V_smooth']:.2e}")
    
    print("\n  流动性深度最低的10天（V最小）:")
    worst_V = data.nsmallest(10, 'V_smooth')
    for i, (date, row) in enumerate(worst_V.iterrows(), 1):
        print(f"    {i:2}. {date.date()}: φ={row['phi_smooth']*100:.2f}%, V={row['V_smooth']:.2e}")
    
    print("\n  流动性深度最高的10天（V最大）:")
    best_V = data.nlargest(10, 'V_smooth')
    for i, (date, row) in enumerate(best_V.iterrows(), 1):
        print(f"    {i:2}. {date.date()}: φ={row['phi_smooth']*100:.2f}%, V={row['V_smooth']:.2e}")
    
    # ==========================================
    # 11. 最终判定
    # ==========================================
    print("\n" + "=" * 70)
    print("【11】P2 验证结论")
    print("=" * 70)
    
    r2_jt = jt_result.get('R2', np.nan) if jt_result['success'] else np.nan
    r2_lin = linear_result.get('R2', np.nan)
    r2_power = power_result.get('R2', np.nan)
    
    print(f"\n1. 变量定义（修正版）:")
    print(f"   φ = |收益率|        （波动/摩擦）")
    print(f"   V = 成交额/|收益率| （流动性深度）")
    
    print(f"\n2. 相关性: Corr(φ, V) = {corr:.4f}")
    if corr < 0:
        print("   ✓ 方向正确（高波动→低流动性深度）")
    else:
        print("   ✗ 方向错误")
    
    print(f"\n3. 模型R²:")
    print(f"   JT_2D:  {r2_jt:.4f}" if not np.isnan(r2_jt) else "   JT_2D:  拟合失败")
    print(f"   Linear: {r2_lin:.4f}")
    print(f"   Power:  {r2_power:.4f}")
    
    # 找最佳模型
    best_model = sorted_results[0][0] if sorted_results else None
    best_r2 = sorted_results[0][1]['R2'] if sorted_results else np.nan
    
    print(f"\n4. 最佳模型: {best_model} (R²={best_r2:.4f})")
    
    if not np.isnan(r2_jt):
        diff = r2_jt - r2_lin
        print(f"\n5. JT vs Linear: {diff:+.4f}")
        
        if best_model == 'JT_2D' and corr < 0:
            verdict = "✅ P2预测成功: 2D JT是最佳模型！"
        elif r2_jt > r2_lin and corr < 0:
            verdict = "🔶 P2部分成功: JT优于线性"
        elif corr < 0:
            verdict = f"❌ P2失败: {best_model}更好（但方向正确）"
        else:
            verdict = "❌ P2失败: 相关性方向错误"
        
        print(f"\n   {verdict}")
    
    return {
        'data': data,
        'results': results,
        'correlation': corr,
        'jt_result': jt_result
    }

# ============================================
# 运行
# ============================================

if __name__ == "__main__":
    output = main()