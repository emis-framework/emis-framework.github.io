#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
EMIS P2: XLF Amihud ILLIQ 验证（2D JT引力）
================================================================================

核心公式（2D JT AdS₂黑洞红移）：
------------------------------
V = V₀ · √(1 - (φ/φₕ)²)

变量定义：
---------
φ = ILLIQ = |r| / DollarVolume    金融股摩擦（Dilaton场）
V = DollarVolume = P × Volume      金融股流动性（本地速度）
φₕ = 临界ILLIQ                     视界值（拟合确定）
V₀ = 正常状态成交金额               渐近速度（拟合确定）

设计决策：
---------
1. φ 不取log（因为公式用比值 φ/φₕ，量纲消掉）
2. φₕ 和 V₀ 都由拟合确定，事后验证合理性
3. V 用5日移动平均平滑（减少日频噪音）

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
# 配置
# ============================================

START_DATE = '2007-01-01'
END_DATE = '2025-12-31'
CACHE_DIR = './cache_p2_xlf/'
SMOOTH_WINDOW = 5  # 5日移动平均

# ============================================
# 数据获取（带缓存）
# ============================================

def download_with_cache(ticker, start=START_DATE, end=END_DATE):
    """
    下载股票数据（带缓存）
    
    参数：
        ticker: 股票代码
        start: 开始日期
        end: 结束日期
    返回：
        DataFrame: OHLCV数据（列名已标准化）
    """
    os.makedirs(CACHE_DIR, exist_ok=True)
    cache_path = os.path.join(CACHE_DIR, f'{ticker}_clean.csv')
    
    if os.path.exists(cache_path):
        print(f"  ✓ 缓存: {ticker}")
        df = pd.read_csv(cache_path, index_col=0, parse_dates=True)
        return df
    
    print(f"  下载: {ticker}...")
    df = yf.download(ticker, start=start, end=end, progress=False)
    
    # 处理MultiIndex列名（yfinance新版本）
    if isinstance(df.columns, pd.MultiIndex):
        # 只取第一层列名
        df.columns = df.columns.get_level_values(0)
    
    # 标准化列名
    df = df.rename(columns={
        'Adj Close': 'AdjClose',
        'Close': 'Close',
        'Volume': 'Volume',
        'Open': 'Open',
        'High': 'High',
        'Low': 'Low'
    })
    
    # 保存清理后的数据
    df.to_csv(cache_path)
    print(f"    ✓ {len(df)} 条记录")
    
    return df

# ============================================
# 核心计算
# ============================================

def calc_illiq_and_volume(df):
    """
    计算Amihud ILLIQ和成交金额
    
    公式：
        ILLIQ = |收益率| / 成交金额
        DollarVolume = 收盘价 × 成交量
    
    参数：
        df: 包含OHLCV的DataFrame
    返回：
        illiq: ILLIQ序列
        dollar_volume: 成交金额序列
    """
    # 查找收盘价列
    if 'AdjClose' in df.columns:
        close = df['AdjClose']
    elif 'Adj Close' in df.columns:
        close = df['Adj Close']
    elif 'Close' in df.columns:
        close = df['Close']
    else:
        raise KeyError(f"找不到收盘价列，可用列: {df.columns.tolist()}")
    
    # 查找成交量列
    if 'Volume' in df.columns:
        volume = df['Volume']
    else:
        raise KeyError(f"找不到成交量列，可用列: {df.columns.tolist()}")
    
    # 收益率
    ret = close.pct_change()
    
    # 成交金额 V = P × Volume
    dollar_volume = close * volume
    
    # ILLIQ = |收益率| / 成交金额
    illiq = np.abs(ret) / dollar_volume
    
    # 处理无穷大和零
    illiq = illiq.replace([np.inf, -np.inf], np.nan)
    
    return illiq, dollar_volume

# ============================================
# 2D JT 引力公式
# ============================================

def jt_2d_velocity(phi, V0, phi_h):
    """
    2D JT引力红移公式（本地速度）
    
    公式：
        V = V₀ · √(1 - (φ/φₕ)²)
    
    参数：
        phi: ILLIQ值（摩擦/Dilaton场）
        V0: 渐近速度（正常状态成交金额）
        phi_h: 临界ILLIQ（视界值）
    
    返回：
        V: 预测的成交金额
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
    V_max = np.max(V)
    
    # 初始估计
    V0_init = V_max * 1.2
    phi_h_init = phi_max * 2.0
    
    print(f"\n  初始估计:")
    print(f"    V₀ = {V0_init:.2e}")
    print(f"    φₕ = {phi_h_init:.2e}")
    print(f"    max(φ) = {phi_max:.2e}")
    
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
    inv_phi = 1 / phi
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

# ============================================
# 验证检查
# ============================================

def validate_fit(phi, V, jt_result, data):
    """验证拟合结果是否合理"""
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
    
    # 检查1：φₕ > max(φ)
    print(f"\n1. 视界值检查:")
    print(f"   φₕ = {phi_h:.2e}")
    print(f"   max(φ) = {phi_max:.2e}")
    if phi_h > phi_max:
        print(f"   ✓ φₕ > max(φ)，所有点在视界外")
    else:
        print(f"   ✗ φₕ ≤ max(φ)，存在视界内的点！")
    
    # 检查2：V₀ 与 max(V) 比较
    print(f"\n2. 渐近速度检查:")
    print(f"   V₀ = {V0:.2e}")
    print(f"   max(V) = {V_max:.2e}")
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
    
    for period_name, start, end in [
        ("2008年9-11月 (金融危机)", '2008-09-01', '2008-11-30'),
        ("2020年3-4月 (COVID)", '2020-03-01', '2020-04-30'),
        ("2013-2019年 (正常期)", '2013-01-01', '2019-12-31')
    ]:
        mask = (data.index >= start) & (data.index <= end)
        if mask.any():
            ratio_period = ratio[mask]
            print(f"   {period_name}:")
            print(f"     均值: {ratio_period.mean():.4f}, 最大: {ratio_period.max():.4f}")

# ============================================
# 主程序
# ============================================

def main():
    print("=" * 70)
    print("EMIS P2: XLF Amihud ILLIQ 验证（2D JT引力）")
    print("=" * 70)
    print("\n核心公式: V = V₀ · √(1 - (φ/φₕ)²)")
    print("其中: φ = ILLIQ = |r|/DollarVolume")
    print("      V = DollarVolume = P × Volume")
    print("预测: 高ILLIQ → 低成交金额 → 流动性陷阱")
    print("=" * 70)
    
    # ==========================================
    # 1. 下载数据
    # ==========================================
    print("\n【1】获取数据...")
    xlf = download_with_cache('XLF')
    
    print(f"  列名: {xlf.columns.tolist()}")
    
    # ==========================================
    # 2. 计算ILLIQ和成交金额
    # ==========================================
    print("\n【2】计算指标...")
    illiq, dollar_volume = calc_illiq_and_volume(xlf)
    
    # 构建数据框
    data = pd.DataFrame({
        'phi': illiq,
        'V': dollar_volume
    }).dropna()
    
    print(f"  原始样本数: {len(data)} 天")
    
    # ==========================================
    # 3. 5日移动平均平滑
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
    print(f"\n  φ (ILLIQ):")
    print(f"    均值: {np.mean(phi):.2e}")
    print(f"    中位数: {np.median(phi):.2e}")
    print(f"    最小值: {np.min(phi):.2e}")
    print(f"    最大值: {np.max(phi):.2e}")
    
    print(f"\n  V (成交金额):")
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
        print("  ✓ 负相关，符合2D JT预测（高摩擦→低流动性）")
    else:
        print("  ⚠ 正相关，与2D JT预测相反")
        print("  可能原因: 恐慌抛售时成交量反而增加")
    
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
        print(f"    φₕ = {jt_result['phi_h']:.2e}")
        print(f"    R² = {jt_result['R2']:.4f}")
        print(f"    RMSE = {jt_result['RMSE']:.2e}")
    else:
        print(f"\n  ✗ JT模型拟合失败")
    
    # ==========================================
    # 7. 拟合对比模型
    # ==========================================
    print("\n" + "-" * 50)
    print("【7】对比模型")
    print("-" * 50)
    
    results = {'JT_2D': jt_result}
    
    linear_result = fit_linear_model(phi, V)
    results['Linear'] = linear_result
    print(f"\n  线性模型: V = a + b·φ")
    print(f"    a = {linear_result['a']:.2e}")
    print(f"    b = {linear_result['b']:.2e}")
    print(f"    R² = {linear_result['R2']:.4f}")
    
    inverse_result = fit_inverse_model(phi, V)
    results['Inverse'] = inverse_result
    print(f"\n  反比模型: V = a + b/φ")
    print(f"    a = {inverse_result['a']:.2e}")
    print(f"    b = {inverse_result['b']:.2e}")
    print(f"    R² = {inverse_result['R2']:.4f}")
    
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
    # 9. 验证拟合结果
    # ==========================================
    validate_fit(phi, V, jt_result, data)
    
    # ==========================================
    # 10. 极端日期分析
    # ==========================================
    print("\n" + "-" * 50)
    print("【10】极端日期分析")
    print("-" * 50)
    
    print("\n  ILLIQ最高的10天（流动性最差）:")
    worst = data.nlargest(10, 'phi_smooth')
    for i, (date, row) in enumerate(worst.iterrows(), 1):
        print(f"    {i:2}. {date.date()}: φ={row['phi_smooth']:.2e}, V={row['V_smooth']:.2e}")
    
    print("\n  ILLIQ最低的10天（流动性最好）:")
    best = data.nsmallest(10, 'phi_smooth')
    for i, (date, row) in enumerate(best.iterrows(), 1):
        print(f"    {i:2}. {date.date()}: φ={row['phi_smooth']:.2e}, V={row['V_smooth']:.2e}")
    
    # ==========================================
    # 11. 最终判定
    # ==========================================
    print("\n" + "=" * 70)
    print("【11】P2 验证结论")
    print("=" * 70)
    
    r2_jt = jt_result.get('R2', np.nan) if jt_result['success'] else np.nan
    r2_lin = linear_result.get('R2', np.nan)
    
    print(f"\n1. 相关性: Corr(φ, V) = {corr:.4f}")
    if corr < 0:
        print("   ✓ 方向正确")
    else:
        print("   ✗ 方向错误")
    
    print(f"\n2. JT模型 R² = {r2_jt:.4f}" if not np.isnan(r2_jt) else "\n2. JT模型拟合失败")
    print(f"3. Linear R² = {r2_lin:.4f}")
    
    if not np.isnan(r2_jt):
        diff = r2_jt - r2_lin
        print(f"4. 差值: JT - Linear = {diff:+.4f}")
        
        if diff > 0.05 and corr < 0:
            verdict = "✅ P2预测成功: 2D JT显著优于线性！"
        elif diff > 0 and corr < 0:
            verdict = "🔶 P2部分成功: JT略优"
        elif corr < 0:
            verdict = "❌ P2失败: JT不优于线性（方向正确）"
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