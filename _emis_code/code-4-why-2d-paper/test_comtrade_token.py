#!/usr/bin/env python3
"""
UN Comtrade Token 测试脚本
=========================

快速测试你的API token是否有效

使用方法：
1. 将你的token粘贴到下面第15行
2. 运行：python test_comtrade_token.py
3. 查看结果
"""

import requests
import json
import os
import sys

# ============================================
# 配置：从环境变量中读取你的token
# PowerShell
# $env:COMTRADE_TOKEN="your_real_token"
# setx 设为系统环境变量
# setx COMTRADE_TOKEN "your_real_token"
# ============================================

COMTRADE_TOKEN = os.getenv("COMTRADE_TOKEN")

if not COMTRADE_TOKEN:
    print("Error: COMTRADE_TOKEN environment variable is not set.")
    sys.exit(1)

# ============================================
# 测试脚本
# ============================================

print("="*60)
print("UN Comtrade API Token 测试")
print("="*60)

if COMTRADE_TOKEN == 'YOUR_TOKEN_HERE':
    print("\n❌ 错误：请先配置token")
    print("   在第15行粘贴你的实际token")
    print("   获取token: https://comtradeplus.un.org/")
    exit(1)

print(f"\n✓ Token已配置")
print(f"  长度: {len(COMTRADE_TOKEN)} 字符")
print(f"  前8位: {COMTRADE_TOKEN[:8]}...")

# 测试1：最简单的请求
print("\n" + "-"*60)
print("测试1：基本连接测试")
print("-"*60)

url = "https://comtradeapi.un.org/data/v1/get/C/A/HS"



headers = {"Ocp-Apim-Subscription-Key": COMTRADE_TOKEN}
params = {
    # "typeCode": "C",      # C = commodity
    # "freqCode": "A",      # A = annual
    # "clCode": "HS",
    "reporterCode": "842",   # USA = 842
    "partnerCode": "156",    # China = 156
    "flowCode": "M",      # M = import
    "period": "2019",
    "maxRecords": "10"
}

print("请求参数：")
print(f"  报告国: USA")
print(f"  伙伴国: CHN")
print(f"  年份: 2019")
print(f"  流向: Import")

print("\n⏳ 发送请求...")

try:
    response = requests.get(url, headers=headers, params=params, timeout=30)
    
    print(f"✓ 响应状态码: {response.status_code}")
    
    if response.status_code == 200:
        print("\n🎉 成功！Token有效！")
        
        result = response.json()
        
        if 'data' in result:
            print(f"   返回数据: {len(result['data'])} 条记录")
            
            if len(result['data']) > 0:
                print("\n📊 示例记录（第1条）：")
                first_record = result['data'][0]
                print(f"   报告国: {first_record.get('reporterCode', 'N/A')}")
                print(f"   伙伴国: {first_record.get('partnerCode', 'N/A')}")
                print(f"   贸易额: ${first_record.get('primaryValue', 0):,.0f}")
                print(f"   年份: {first_record.get('period', 'N/A')}")
        
        print("\n✅ 结论：你的token完全正常，可以下载数据！")
        print("   现在可以运行 trade_gravity_download.py 了")
    
    elif response.status_code == 400:
        print("\n❌ 400错误：请求格式问题")
        print("\n可能原因：")
        print("  1. 参数格式不对")
        print("  2. API端点已更新")
        print("  3. 某些字段值无效")
        
        print("\n响应内容：")
        try:
            error = response.json()
            print(json.dumps(error, indent=2, ensure_ascii=False))
        except:
            print(response.text[:500])
        
        print("\n建议：")
        print("  - 检查UN Comtrade官方文档")
        print("  - 或使用合成数据继续工作")
    
    elif response.status_code == 401:
        print("\n❌ 401错误：Token无效")
        print("\n请检查：")
        print("  1. Token是否复制完整？")
        print("  2. Token是否还有效？（可能过期）")
        print("  3. 是否是正确的token类型？")
        
        print("\n如何重新获取token：")
        print("  1. 登录 https://comtradeplus.un.org/")
        print("  2. Profile → API Management")
        print("  3. 复制 Primary Key")
    
    elif response.status_code == 429:
        print("\n⚠️  429错误：请求过于频繁")
        print("\n说明：")
        print("  - 达到了API速率限制")
        print("  - 免费账户：100次/小时")
        print("\n建议：")
        print("  - 等待1小时后重试")
        print("  - 或升级到付费账户")
    
    else:
        print(f"\n❌ 未知错误：{response.status_code}")
        print("\n响应内容：")
        print(response.text[:500])

except requests.exceptions.Timeout:
    print("\n❌ 超时错误")
    print("   网络连接太慢或服务器无响应")
    print("   建议：检查网络连接后重试")

except requests.exceptions.ConnectionError:
    print("\n❌ 连接错误")
    print("   无法连接到UN Comtrade服务器")
    print("   建议：检查网络连接")

except Exception as e:
    print(f"\n❌ 意外错误: {type(e).__name__}")
    print(f"   {str(e)}")

# 测试2：检查配额（如果第一个测试成功）
if response.status_code == 200:
    print("\n" + "-"*60)
    print("测试2：检查API配额")
    print("-"*60)
    
    # 检查响应头中的配额信息
    if 'X-RateLimit-Remaining' in response.headers:
        remaining = response.headers['X-RateLimit-Remaining']
        limit = response.headers.get('X-RateLimit-Limit', 'N/A')
        print(f"✓ 剩余配额: {remaining} / {limit}")
    else:
        print("  (API未返回配额信息)")

print("\n" + "="*60)
print("测试完成")
print("="*60)
