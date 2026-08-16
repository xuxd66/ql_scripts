#入口：https://s21.ax1x.com/2025/10/18/pVLYiCV.png
# -*- coding: utf-8 -*-
# @Time     : 2025-11-25
# @Author   : chmodxxoo
# @Version  ：3.0
# @Desc     : 蒙娜丽莎小程序签到脚本，支持青龙多账号。在 @重庆第一深情 大佬的基础上做了修复调整。

import os
import random
import re
import time

import requests

try:
    from notify import send
except ImportError:
    print("未找到 notify.py，将仅在控制台输出日志。")


    def send(title, content):
        print(f"--- 模拟发送通知 ---\n标题：{title}\n内容：{content}\n--------------------")


class MNLS:
    def __init__(self, index, account):
        self.customerId = account.split("#")[0]
        self.tokenStr = account.split("#")[1]
        self.index = int(index)
        self.headers = {
            "Host": "mcs.monalisagroup.com.cn",
            "Connection": "keep-alive",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36 MicroMessenger/7.0.20.1781(0x6700143B) NetType/WIFI MiniProgramEnv/Mac MacWechat/WMPF MacWechat/3.8.7(0x13080712) UnifiedPCMacWechat(0xf2641209) XWEB/16786",
            "xweb_xhr": "1",
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "*/*",
            "Sec-Fetch-Site": "cross-site",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Dest": "empty",
            "Referer": "https://servicewechat.com/wxce6a8f654e81b7a4/452/page-frame.html",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "zh-CN,zh;q=0.9"
        }
        self.msg = ''
        self.mobile = ''
        self.score = 0

    def hide_phone_number(self, text):
        if not text:
            return text
        if len(text) > 11:
            return text
        return re.sub(r'(\d{3})\d{4}(\d{4})', r'\1****\2', text)

    def getCustInfoByID(self):
        url = 'https://mcs.monalisagroup.com.cn/member/doAction'
        data = f'brand=MON&customerID={self.customerId}&action=getCustInfoByID'
        res = requests.post(url, headers=self.headers, data=data)
        if res.status_code == 200:
            rj = res.json()
            if rj['status'] == 0:
                print()
                self.mobile = self.hide_phone_number(rj['resultInfo'][0]['Telephone'])
                self.score = rj['resultInfo'][0]['Integral']
                return True
        return False

    def sign(self):
        url = 'https://mcs.monalisagroup.com.cn/member/doAction'
        data = f"action=sign&CustomerID={self.customerId}&CustomerName=%E5%BE%AE%E4%BF%A1%E7%94%A8%E6%88%B7&StoreID=0&OrganizationID=0&Brand=MON&ItemType=002&tokenStr={self.tokenStr}"
        signRes = ""
        try:
            res = requests.post(url, headers=self.headers, data=data)
            if res.status_code == 200:
                status_code = res.json().get("status", -1)  # 获取status值，如果不存在默认为-1

                if status_code == 0:
                    points = res.json().get("resultInfo", "未知")
                    signRes = f" 签到成功！获得积分: {points}"
                elif status_code == 7:
                    # print(f"😊今天已经签到过了，无需重复签到。")
                    signRes = f"😊 今天已经签到过了，无需重复签到。\n"
                else:
                    # print(f"❌ 账号 {id} 签到失败！")
                    signRes = f"签到失败❌:服务器返回: {res.text.strip()}"
        except Exception as e:
            print(f"❌ 账号 {id} 发生未知错误：{e}")
        self.msg += f"签到结果：{signRes}"

    def run(self):
        print(f"-----开始运行第{self.index}个账号-----")
        self.msg += f"账号序号：{self.index}\n"
        self.msg += f"账号ID：{self.customerId}\n"
        if self.getCustInfoByID():
            self.sign()
        self.getCustInfoByID()
        self.msg += f"手机号：{self.mobile}\n"
        self.msg += f"剩余积分：{self.score}\n"
        print(self.msg)
        sleep = random.randint(3, 5)
        print(f"-----随机{sleep}s后开始运行第{self.index}个账号-----")
        time.sleep(sleep)
        return self.msg


if __name__ == '__main__':
    tokens = os.getenv("mnls_token")
    if not tokens:
        print("❌ 未找到环境变量 mnls_token，请在青龙面板中添加！")
        print("💡 格式：'CustomerID#tokenStr' 多个变量请用&分割或者换行符分割")
        exit(0)
    # 使用正则表达式分割字符串，以兼容多种分隔符
    token_arr = re.split(r'[&\n\s]', tokens)
    # 过滤掉因分隔符产生的空字符串
    token_arr = [token for token in token_arr if token]
    if not token_arr:
        print("❌ 环境变量 mnls_token 的值无效，请检查！")
        exit(0)
    print(f"✅ 检测到 {len(token_arr)} 个账号，准备开始签到...\n")
    token_msg_res_arr = []
    for i, token in enumerate(token_arr, start=1):
        token_res = MNLS(i, token).run()
        token_msg_res_arr.append(token_res)
    print("🎉 所有账号签到任务执行完毕！")
    send('蒙娜丽莎签到', "\n".join(token_msg_res_arr))
