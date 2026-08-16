#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#注册登录成功后 抓包抓next-action和cookie  其他的功能自己发掘 想用环境变量就用ai给你修改
import requests
import json

# 公共配置（复用你提供的可正常请求的参数）
URL = "https://nanophoto.ai/zh/settings/credits"
HEADERS = {
    'User-Agent': "Mozilla/5.0 (Linux; Android 14; 22041211AC Build/UP1A.231005.007; ) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/140.0.7339.207 Mobile Safari/537.36",
    'Accept': "text/x-component",
    'Accept-Encoding': "gzip, deflate, br, zstd",
    'Content-Type': "text/plain",
    'sec-ch-ua-platform': "\"Android\"",
    'next-action': "",#这里
    'sec-ch-ua': "\"Android WebView\";v=\"141\", \"Not?A_Brand\";v=\"8\", \"Chromium\";v=\"141\"",
    'sec-ch-ua-mobile': "?1",
    'next-router-state-tree': "%5B%22%22%2C%7B%22children%22%3A%5B%5B%22locale%22%2C%22zh%22%2C%22d%22%5D%2C%7B%22children%22%3A%5B%22(protected)%22%2C%7B%22children%22%3A%5B%22settings%22%2C%7B%22children%22%3A%5B%22credits%22%2C%7B%22children%22%3A%5B%22__PAGE__%22%2C%7B%7D%2C%22%2Fzh%2Fsettings%2Fcredits%22%2C%22refresh%22%5D%7D%5D%7D%5D%7D%2Cnull%2Cnull%2Ctrue%5D%7D%2Cnull%2Cnull%5D%7D%2Cnull%2Cnull%2Ctrue%5D",
    'content-type': "text/plain;charset=UTF-8",
    'origin': "https://nanophoto.ai",
    'x-requested-with': "com.microsoft.bing",
    'sec-fetch-site': "same-origin",
    'sec-fetch-mode': "cors",
    'sec-fetch-dest': "empty",
    'referer': "https://nanophoto.ai/zh/settings/credits",
    'accept-language': "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7",
    'priority': "u=1, i",
    'Cookie': ""#改这里
}

def get_credits():
    payload = "[]"
    try:
        response = requests.post(URL, data=payload, headers=HEADERS)
        response_lines = response.text.strip().split('\n')
        if len(response_lines) >= 2:
            # 严格按照你的解析逻辑处理
            data_line = response_lines[1].split(':', 1)[1]
            data_dict = json.loads(data_line)
            credits = data_dict.get('data', {}).get('credits', None)
            if credits is not None:
                print(f"当前积分：{credits}")
                return credits
            else:
                print("未获取到积分数据（data中无credits字段）")
                return None
        else:
            print(f"响应格式异常，仅返回 {len(response_lines)} 行数据")
            print(f"完整响应：{response.text}")
            return None
    except json.JSONDecodeError:
        print("JSON解析失败，响应内容：", response.text)
        return None
    except Exception as e:
        print(f"积分查询出错：{str(e)}")
        return None

def check_in():
    """执行签到（使用签到专属payload）"""
    payload = "[{}]"
    try:
        print("\n=== 开始执行签到 ===")
        response = requests.post(URL, data=payload, headers=HEADERS)
        response_lines = response.text.strip().split('\n')
        if len(response_lines) >= 2:
            data_line = response_lines[1].split(':', 1)[1]
            data_dict = json.loads(data_line)
            data = data_dict.get('data', {})
            success = data.get('success', False)
            
            if success:
                new_credits = data.get('credits', 0)
                checkin_date = data.get('checkinDate', '未知日期')
                print(f"✅ 签到成功！")
                print(f"📅 签到日期：{checkin_date}")
                print(f"💎 积分更新为：{new_credits}")
            else:
                error_msg = data.get('message', '未知错误')
                error_code = data.get('error', '无错误码')
                print(f"❌ 签到失败！")
                print(f"错误码：{error_code}")
                print(f"原因：{error_msg}")
        else:
            print(f"签到响应格式异常，完整响应：{response.text}")
    except json.JSONDecodeError:
        print("签到响应JSON解析失败，内容：", response.text)
    except Exception as e:
        print(f"签到出错：{str(e)}")

# 主流程：先查积分 → 签到 → 再查积分
if __name__ == "__main__":
    print("=== 积分查询与签到流程启动 ===")
    print("\n【签到前积分】")
    get_credits()
    
    check_in()
    
    print("\n【签到后积分】")
    get_credits()