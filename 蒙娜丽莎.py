#入口：https://s21.ax1x.com/2025/10/18/pVLYiCV.png
#环境变量名：MLLS
#环境变量值：抓CustomerID
#多用户用@分割
#签到得金币，金币兑换实物
#by 重庆第一深情

import os 
import requests
import json
from notify import send

url = "https://mcs.monalisagroup.com.cn/member/doAction"
customer_ids = os.getenv("MLLS", "").split("@")
# 过滤空字符串（处理环境变量为空或只有@的情况）
customer_ids = [cid for cid in customer_ids if cid.strip()]

headers = {
  'User-Agent': "Mozilla/5.0 (Linux; Android 15; PKG110 Build/UKQ1.231108.001; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/138.0.7204.180 Mobile Safari/537.36 XWEB/1380215 MMWEBSDK/20250904 MMWEBID/6169 MicroMessenger/8.0.64.2940(0x28004034) WeChat/arm64 Weixin NetType/WIFI Language/zh_CN ABI/arm64 MiniProgramEnv/android",
}

# 存储所有用户的签到结果
all_results = []

for cid in customer_ids:
    payload = {
        'action': "sign",
        'CustomerID': cid,
#       'CustomerName': "微信用户",
        'StoreID': "0",
        'OrganizationID': "0",
        'Brand': "MON",
        'ItemType': "002"
    }
    
    try:
        response = requests.post(url, data=payload, headers=headers, timeout=10)
        response.raise_for_status()  # 抛出HTTP请求错误
        result = json.loads(response.text)
        status = result.get('status')
        
        if status == 0:
            result_info = result.get('resultInfo', '未知数量')
            msg = f"👥账户{cid}：签到成功，获得金币{result_info}✅\n"
        elif status == -200:
            msg = f"👥账户{cid}：签到失败，请检查环境变量❎\n"
        elif status == 7:
            msg = f"👥账户{cid}：今日已签到，请勿重复签到🤖\n"
        else:
            msg = f"👥账户{cid}：签到失败，状态码：{status}❎\n"
            
    except Exception as e:
        msg = f"👥账户{cid}：签到请求异常，错误信息：{str(e)}⚠️\n"
    
    print(msg)
    all_results.append(msg)

# 合并所有结果并推送
if all_results:
    # 计算统计信息
    success_count = sum(1 for msg in all_results if "签到成功" in msg)
    total_count = len(all_results)
    summary = f"📊 签到统计：共{total_count}个账户，成功{success_count}个，失败{total_count - success_count}个\n\n"
    full_msg = summary + "\n".join(all_results)
    send("蒙娜丽莎签到结果", full_msg)
else:
    no_user_msg = "⚠️ 未检测到有效用户ID，请检查环境变量配置"
    print(no_user_msg)
    send("蒙娜丽莎签到结果", no_user_msg)