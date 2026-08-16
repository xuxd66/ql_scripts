#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""

🍷 酒仙网自动化脚本 🍷


操作步骤：
1. 打开上方链接
2. 截图保存二维码
3. 微信扫码参与活动
4. 点击"立即领取"获得1000积分！！


✨ 脚本特色
• 自动完成每日签到 + 13个浏览任务 + 抽奖（需第二次运行才会正常抽奖）
• 支持多账号批量运行
• 智能登录（Token优先，密码备用）
• 青龙推送通知
• 平均每日可获得 160-225 金币

📋 任务清单
┌──────────────────┬────────────┬─────────────────┐
│ 任务类型         │ 金币收益   │ 说明             │
├──────────────────┼────────────┼─────────────────┤
│ 每日签到         │ 10-60金币  │  连续签到奖励更高│
│ 每日浏览任务     │ 160金币    │    4个常规任务   │
│ 隐藏任务         │ 65金币     │   10个额外任务   │
│ 每日抽奖         │ 随机奖品   │  实物/红包1-2元  │
└──────────────────┴────────────┴─────────────────┘

💰 收益估算
• 基础收益：每日 160-225 金币
• 月累计：5700-7600 金币
• 年累计：约 7-9万 金币

🔄 执行逻辑
1. 首次运行：账号密码登录 → 自动保存Token到本地
2. 后续运行：使用保存的Token登录
3. Token过期时：自动切换密码登录并更新Token
4. 执行顺序：登录 → 签到 → 浏览任务 → 抽奖 → 推送

⚙️ 配置说明

【环境变量】
变量名：jiuxian
格式：
手机号#密码
13800138000#123456
13900139000#abcdef

【定时任务】
名称：酒仙
命令：task 酒仙.py
规则：10 9,10 * * *

❌ 重要提醒：请勿在 0-1 点之间运行！



📦 积分兑换
• 多种实物商品可选
• 有效期：当年积分次年年底失效
• 注意及时使用，避免过期清空

🔧 故障排除

【常见问题】
• 报错显示 nickName 相关：请修改用户昵称
• 小程序收不到验证码：尝试使用酒仙APP修改密码
• 不想运行隐藏任务：跳转到脚本763行并查看下一行的注释修改

【文件说明】
• jiuxian_tokens.json - 自动保存的登录Token（自动生成在脚本同目录下）
• notify.py - 青龙推送配置文件（需自备在同目录下）

📊 任务详情


【浏览任务】
• 4个常规任务 + 10个隐藏任务
• 每个任务自动等待15秒
• 自动领取任务奖励

【抽奖任务】
• 每日1次抽奖机会（完成所有任务会执行抽奖，但第一会莫名失败，第二次运行可以正确抽奖）
• 连续签到第7天额外抽奖1次（未能实现，7天抽奖全是抽金币的，30-100金币，不想弄了）
• 自动解析奖品信息

💡 使用建议
• 建议设置合理的执行频率
• 妥善保管账号信息
• 关注平台规则变化
• 如发现异常请立即停止使用


🎯 版本信息
• 当前版本：V3.0 稳定版
• 更新日期：2025-11-04
• 主要功能：签到、任务、抽奖、推送

-----------------------------------------------------------
免责声明：本脚本仅供学习交流使用，请合理使用并遵守相关平台规则。
------------------------------------------------------------


------------------------------------------------------------
"""

import os
import json
import time
import random
import requests
import sys
from typing import Dict, List, Optional, Tuple
import urllib3

# 禁用SSL警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 应用配置
class JiuxianConfig:
    # 应用基本信息
    APP_NAME = "酒仙"
    VERSION = "9.2.13"
    APP_KEY = "1ba8b341-5a56-49dc-8ee3-92b32db7fc21"
    
    # API接口
    LOGIN_URL = "https://newappuser.jiuxian.com/user/loginUserNamePassWd.htm"
    MEMBER_INFO_URL = "https://newappuser.jiuxian.com/memberChannel/memberInfo.htm"
    RECEIVE_REWARD_URL = "https://newappuser.jiuxian.com/memberChannel/receiveRewards.htm"
    TASK_COMPLETE_URL = "https://shop.jiuxian.com/show/wap/addJinBi.htm"
    SIGN_URL = "https://newappuser.jiuxian.com/memberChannel/userSign.htm"
    
    # 抽奖相关API - 使用小程序接口
    LOTTERY_DRAW_URL = "https://h5market2.jiuxian.com/drawObject"
    DRAW_PAGE_URL = "https://h5market2.jiuxian.com/draw.htm"
    
    # 小程序设备信息
    MINI_PROGRAM_INFO = {
        'appKey': '1ba8b341-5a56-49dc-8ee3-92b32db7fc21',
        'appVersion': '9.2.12',
        'apiVersion': '1.0',
        'areaId': '2048',
        'channelCode': '0, 1',
        'appChannel': 'xiaochengxu',
        'deviceType': 'XIAOCHENGXU',
        'supportWebp': '2',
        'longi': '115.80287868923611',
        'lati': '28.155340440538193',
        'screenReslolution': '412x915',
        'sysVersion': 'Android 14'
    }
    
    # APP设备信息
    APP_DEVICE_INFO = {
        "appVersion": "9.2.13",
        "areaId": "500",
        "channelCode": "0", 
        "cpsId": "xiaomi",
        "deviceIdentify": "ad96ade2-b918-3e05-86b8-ba8c34747b0c",
        "deviceType": "ANDROID",
        "deviceTypeExtra": "0",
        "equipmentType": "M2011K2C",
        "netEnv": "wifi",
        "screenReslolution": "1080x2297",
        "supportWebp": "1",
        "sysVersion": "14",
        "appKey": "ad96ade2-b918-3e05-86b8-ba8c34747b0c"
    }
    
    # 小程序请求头
    MINI_PROGRAM_HEADERS = {
        "Host": "newappuser.jiuxian.com",
        "Connection": "keep-alive",
        "content-type": "application/json",
        "secure": "false",
        "charset": "utf-8",
        "Referer": "https://servicewechat.com/wx244a18142bb0c78a/144/page-frame.html",
        "User-Agent": "Mozilla/5.0 (Linux; Android 14; M2011K2C Build/UKQ1.230804.001; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/138.0.7258.158 Mobile Safari/537.36 XWEB/1380267 MMWEBSDK/20250904 MMWEBID/6819 MicroMessenger/8.0.64.2940(0x2800403C) WeChat/arm64 Weixin NetType/WIFI Language/zh_CN ABI/arm64 MiniProgramEnv/android",
        "Accept-Encoding": "gzip, deflate, br"
    }
    
    # APP请求头
    APP_HEADERS = {
        "User-Agent": "okhttp/3.14.9",
        "Content-Type": "application/x-www-form-urlencoded",
        "Host": "newappuser.jiuxian.com",
        "Connection": "Keep-Alive",
        "Accept-Encoding": "gzip"
    }
    
    # Token存储文件路径
    @staticmethod
    def get_token_file():
        script_dir = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(script_dir, "jiuxian_tokens.json")

# Token管理器（保持不变）
class TokenManager:
    def __init__(self, token_file: str):
        self.token_file = token_file
        self.tokens = self._load_tokens()
    
    def _load_tokens(self) -> Dict:
        try:
            if os.path.exists(self.token_file):
                with open(self.token_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            print(f"❌ 加载Token文件失败: {e}")
        return {}
    
    def _save_tokens(self):
        try:
            os.makedirs(os.path.dirname(self.token_file), exist_ok=True)
            with open(self.token_file, 'w', encoding='utf-8') as f:
                json.dump(self.tokens, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"❌ 保存Token文件失败: {e}")
    
    def get_token(self, username: str) -> Optional[Dict]:
        return self.tokens.get(username)
    
    def save_token(self, username: str, token_data: Dict):
        self.tokens[username] = {
            "token": token_data.get("token"),
            "uid": token_data.get("uid"),
            "nickname": token_data.get("nickname"),
            "update_time": token_data.get("update_time")
        }
        self._save_tokens()
    
    def delete_token(self, username: str):
        if username in self.tokens:
            del self.tokens[username]
            self._save_tokens()
    
    def is_token_valid(self, username: str) -> bool:
        return username in self.tokens and self.tokens[username].get("token")

# 抽奖模块 - 使用你提供的小程序接口
class JiuxianLotteryModule:
    """酒仙抽奖模块 - 使用小程序接口"""
    
    def __init__(self, session: requests.Session, token: str, username: str = None):
        self.session = session
        self.token = token
        self.username = username
        
        # 小程序User-Agent
        self.user_agent = 'Mozilla/5.0 (Linux; Android 14; M2011K2C Build/UKQ1.230804.001; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/138.0.7258.158 Mobile Safari/537.36 XWEB/1380283 MMWEBSDK/20250904 MMWEBID/2537 MicroMessenger/8.0.64.2940(0x2800403E) WeChat/arm64 Weixin NetType/WIFI Language/zh_CN ABI/arm64 miniProgram/wx244a18142bb0c78a'

    def get_phone_tail(self) -> str:
        if self.username and len(self.username) >= 4:
            return self.username[-4:]
        return "未知"

    def lottery_draw(self) -> Tuple[bool, str]:
        """抽奖功能 - 使用小程序接口"""
        try:
            phone_tail = self.get_phone_tail()
            print(f"🎰 开始抽奖 ({phone_tail})...")
            
            # 先访问抽奖页面获取cookie
            draw_url = JiuxianConfig.DRAW_PAGE_URL
            params = {
                'id': '8e8b7f5386194798ab1ae7647f4af6ba',
                'token': self.token
            }
            
            draw_headers = {
                'User-Agent': self.user_agent,
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/wxpic,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
                'X-Requested-With': 'com.tencent.mm',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-User': '?1',
                'Sec-Fetch-Dest': 'document',
                'Accept-Encoding': 'gzip, deflate, br, zstd',
                'Accept-Language': 'zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7'
            }
            
            response = self.session.get(draw_url, params=params, headers=draw_headers, verify=False)
            print(f"🎰 抽奖页面访问 ({phone_tail}): {response.status_code}")
            
            # 执行抽奖
            lottery_url = JiuxianConfig.LOTTERY_DRAW_URL
            current_time = int(time.time() * 1000)
            
            data = {
                'id': '8e8b7f5386194798ab1ae7647f4af6ba',
                'isOrNotAlert': 'false',
                'orderSn': '',
                'advId': '',
                'time': str(current_time)
            }
            
            lottery_headers = {
                'User-Agent': self.user_agent,
                'Accept': '*/*',
                'X-Requested-With': 'XMLHttpRequest',
                'Content-Type': 'application/x-www-form-urlencoded',
                'Origin': 'https://h5market2.jiuxian.com',
                'Sec-Fetch-Site': 'same-origin',
                'Sec-Fetch-Mode': 'cors',
                'Sec-Fetch-Dest': 'empty',
                'Referer': f'https://h5market2.jiuxian.com/draw.htm?id=8e8b7f5386194798ab1ae7647f4af6ba&token={self.token}',
                'Accept-Encoding': 'gzip, deflate, br, zstd',
                'Accept-Language': 'zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7'
            }
            
            response = self.session.post(lottery_url, data=data, headers=lottery_headers, verify=False)
            
            if response.status_code != 200:
                print(f"❌ 抽奖请求失败 ({phone_tail}): HTTP {response.status_code}")
                return False, "请求失败"
            
            try:
                result = response.json()
            except:
                print(f" 抽奖返回数据解析失败 ({phone_tail})")
                return False, "数据解析失败"
            
            print(f"🎰 抽奖返回数据: {result}")
            
            # 解析抽奖结果
            if 'luck' in result:
                if result['luck'] is False:
                    print(f" 今日已抽奖 ({phone_tail})")
                    return False, "已抽过"
                else:
                    luck_info = result.get('luck', {})
                    luck_name = luck_info.get('luckname', '未知')
                    state = luck_info.get('State', 0)
                    object_id = luck_info.get('ObjectID', 0)
                    
                    # State=1, ObjectID=0 是未中奖
                    if state == 1 and object_id == 0:
                        print(f" 抽奖完成 ({phone_tail}): {luck_name}")
                        return False, luck_name
                    elif state == 1 and object_id > 0:
                        print(f"🎉 中奖 ({phone_tail}): {luck_name}")
                        return True, luck_name
                    else:
                        print(f"❓ 未知抽奖结果 ({phone_tail}): state={state}, object_id={object_id}, prize={luck_name}")
                        return False, luck_name
            else:
                print(f"❌ 抽奖失败 ({phone_tail})")
                return False, "失败"
            
        except Exception as e:
            phone_tail = self.get_phone_tail()
            print(f"❌ 抽奖异常 ({phone_tail}): {str(e)}")
            return False, "异常"

# 青龙推送模块
class QLNotifier:
    @staticmethod
    def send(title: str, content: str):
        try:
            from notify import send as ql_send
            ql_send(title, content)
            print(f"✅ 青龙通知发送成功: {title}")
        except ImportError:
            print(f"📢 {title}")
            print(f"📝 {content}")
        except Exception as e:
            print(f"❌ 发送通知异常: {str(e)}")

# 主业务类（只修改抽奖相关部分，其他保持不变）
class Jiuxian:
    def __init__(self, username: str = None, password: str = None):
        self.username = username
        self.password = password
        self.token = None
        self.uid = None
        self.nickname = None
        self.task_token = None
        self.session = requests.Session()
        self.session.verify = False
        self.token_manager = TokenManager(JiuxianConfig.get_token_file())
        self.lottery_module = None
        self.continuous_sign_days = 0
        self.total_gold = 0
        self.today_gold = 0
        self.is_signed_today = False
        
    def get_phone_tail(self, phone: str = None) -> str:
        if not phone:
            phone = self.username or ""
        if phone and len(phone) >= 4:
            return phone[-4:]
        return "未知"
        
    def load_saved_token(self) -> bool:
        if not self.username:
            return False
        token_data = self.token_manager.get_token(self.username)
        if token_data and self.token_manager.is_token_valid(self.username):
            self.token = token_data.get("token")
            self.uid = token_data.get("uid")
            self.nickname = token_data.get("nickname")
            phone_tail = self.get_phone_tail()
            print(f"🔑 加载已保存的Token: {self.nickname} ({phone_tail})")
            return True
        return False
    
    def save_current_token(self):
        if self.token and self.uid and self.username:
            token_data = {
                "token": self.token,
                "uid": self.uid,
                "nickname": self.nickname,
                "update_time": int(time.time())
            }
            self.token_manager.save_token(self.username, token_data)
            phone_tail = self.get_phone_tail()
            print(f"💾 保存Token信息: {self.nickname} ({phone_tail})")
    
    def login_with_password(self) -> bool:
        try:
            if not self.username or not self.password:
                print("❌ 缺少账号或密码")
                return False
                
            login_data = JiuxianConfig.APP_DEVICE_INFO.copy()
            login_data.update({
                "userName": self.username,
                "passWord": self.password
            })
            
            response = self.session.post(
                JiuxianConfig.LOGIN_URL,
                data=login_data,
                headers=JiuxianConfig.APP_HEADERS,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get("success") == "1":
                    user_info = result["result"]["userInfo"]
                    self.token = user_info["token"]
                    self.uid = user_info["uid"]
                    self.nickname = user_info["nickName"]
                    
                    self.lottery_module = JiuxianLotteryModule(self.session, self.token, self.username)
                    self.save_current_token()
                    phone_tail = self.get_phone_tail()
                    print(f"✅ 密码登录成功: {self.nickname} ({phone_tail})")
                    return True
                else:
                    phone_tail = self.get_phone_tail()
                    print(f"❌ 密码登录失败 ({phone_tail}): {result.get('errMsg', '未知错误')}")
                    if self.username:
                        self.token_manager.delete_token(self.username)
                    return False
            else:
                phone_tail = self.get_phone_tail()
                print(f"❌ 登录请求失败 ({phone_tail}): HTTP {response.status_code}")
                return False
                
        except Exception as e:
            phone_tail = self.get_phone_tail()
            print(f"❌ 登录异常 ({phone_tail}): {str(e)}")
            return False
    
    def check_token_valid(self) -> bool:
        if not self.token:
            return False
        try:
            member_info = self.get_member_info()
            if member_info:
                if not self.nickname and member_info.get('userInfo'):
                    self.nickname = member_info['userInfo'].get('nickName', '未知用户')
                elif not self.nickname:
                    self.nickname = "Token用户"
                phone_tail = self.get_phone_tail()
                print(f"✅ Token验证成功: {self.nickname} ({phone_tail})")
                return True
            return False
        except Exception:
            return False
    
    def smart_login(self) -> bool:
        if self.username and self.load_saved_token():
            if self.check_token_valid():
                phone_tail = self.get_phone_tail()
                print(f"✅ Token登录成功: {self.nickname} ({phone_tail})")
                self.lottery_module = JiuxianLotteryModule(self.session, self.token, self.username)
                return True
            else:
                phone_tail = self.get_phone_tail()
                print(f"🔄 保存的Token已过期 ({phone_tail})，尝试密码登录...")
                self.token_manager.delete_token(self.username)
        
        if self.username and self.password:
            password_login_success = self.login_with_password()
            if password_login_success:
                self.get_member_info()
                return True
        
        phone_tail = self.get_phone_tail()
        print(f"❌ 所有登录方式都失败了 ({phone_tail})")
        return False
    
    def get_member_info(self) -> Optional[Dict]:
        if not self.token:
            phone_tail = self.get_phone_tail()
            print(f"❌ 请先登录 ({phone_tail})")
            return None
            
        try:
            params = JiuxianConfig.MINI_PROGRAM_INFO.copy()
            params["token"] = self.token
            
            params["equipmentType"] = json.dumps({
                "deviceAbi": "arm64-v8a",
                "benchmarkLevel": 33,
                "cpuType": "Venus based on Qualcomm Technologies, Inc SM8350",
                "system": "Android 14",
                "memorySize": 11228,
                "abi": "arm64-v8a",
                "model": "M2011K2C",
                "brand": "Xiaomi",
                "platform": "android"
            })
            
            response = self.session.get(
                JiuxianConfig.MEMBER_INFO_URL,
                params=params,
                headers=JiuxianConfig.MINI_PROGRAM_HEADERS,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get("success") == "1":
                    member_data = result["result"]
                    
                    task_channel = member_data.get("taskChannel", {})
                    self.task_token = task_channel.get("taskToken", "")
                    
                    self.total_gold = member_data.get("goldMoney", 0)
                    self.is_signed_today = member_data.get("isSignTody", False)
                    self.continuous_sign_days = member_data.get("signDays", 0)
                    
                    if self.task_token:
                        phone_tail = self.get_phone_tail()
                        print(f"🔑 获取到taskToken ({phone_tail}): {self.task_token}")
                    
                    print(f"💰 当前总金币: {self.total_gold}")
                    print(f"📅 今日是否签到: {'是' if self.is_signed_today else '否'}")
                    print(f"📅 累计签到天数: {self.continuous_sign_days}")
                    
                    return member_data
                else:
                    if result.get("errCode") in ["TOKEN_EXPIRED", "INVALID_TOKEN"]:
                        phone_tail = self.get_phone_tail()
                        print(f"❌ Token已过期 ({phone_tail})")
                        if self.username:
                            self.token_manager.delete_token(self.username)
                    else:
                        phone_tail = self.get_phone_tail()
                        print(f"❌ 获取会员信息失败 ({phone_tail}): {result.get('errMsg', '未知错误')}")
            else:
                phone_tail = self.get_phone_tail()
                print(f"❌ 会员信息请求失败 ({phone_tail}): HTTP {response.status_code}")
            return None
        except Exception as e:
            phone_tail = self.get_phone_tail()
            print(f"❌ 获取会员信息异常 ({phone_tail}): {str(e)}")
            return None
    
    def user_sign(self) -> Tuple[bool, int]:
        if not self.token:
            phone_tail = self.get_phone_tail()
            print(f"❌ 请先登录 ({phone_tail})")
            return False, 0
            
        try:
            params = JiuxianConfig.MINI_PROGRAM_INFO.copy()
            params["token"] = self.token
            
            params["equipmentType"] = json.dumps({
                "deviceAbi": "arm64-v8a",
                "benchmarkLevel": 33,
                "cpuType": "Venus based on Qualcomm Technologies, Inc SM8350",
                "system": "Android 14",
                "memorySize": 11228,
                "abi": "arm64-v8a",
                "model": "M2011K2C",
                "brand": "Xiaomi",
                "platform": "android"
            })
            
            response = self.session.get(
                JiuxianConfig.SIGN_URL,
                params=params,
                headers=JiuxianConfig.MINI_PROGRAM_HEADERS,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get("success") == "1":
                    sign_result = result["result"]
                    earned_gold = sign_result.get("receivedGoldNums", 0)
                    new_sign_days = sign_result.get("signDays", 0)
                    will_get_golds = sign_result.get("willGetGolds", 0)
                    
                    self.continuous_sign_days = new_sign_days
                    phone_tail = self.get_phone_tail()
                    
                    print(f"✅ 签到成功 ({phone_tail})")
                    print(f"   📅 累计签到天数: {new_sign_days}")
                    print(f"   💰 获得金币: {earned_gold}")
                    print(f"   💰 将获得金币: {will_get_golds}")
                    
                    return True, earned_gold
                else:
                    err_msg = result.get("errMsg", "未知错误")
                    phone_tail = self.get_phone_tail()
                    print(f"❌ 签到失败 ({phone_tail}): {err_msg}")
                    if "已签到" in err_msg or "重复" in err_msg:
                        phone_tail = self.get_phone_tail()
                        print(f"ℹ️ 今日已签到过 ({phone_tail})")
                        self.get_member_info()
                        return True, 0
            else:
                phone_tail = self.get_phone_tail()
                print(f"❌ 签到请求失败 ({phone_tail}): HTTP {response.status_code}")
            return False, 0
        except Exception as e:
            phone_tail = self.get_phone_tail()
            print(f"❌ 签到异常 ({phone_tail}): {str(e)}")
            return False, 0

    def complete_browse_task_original(self, task_id: str, task_name: str) -> Tuple[bool, int]:
        try:
            if not self.task_token:
                phone_tail = self.get_phone_tail()
                print(f"❌ 未获取到taskToken ({phone_tail})，无法完成任务")
                return False, 0
                
            phone_tail = self.get_phone_tail()
            print(f"🔄 开始浏览任务 ({phone_tail}): {task_name}")
            
            headers = {
                "User-Agent": "Mozilla/5.0 (Linux; Android 14; M2011K2C Build/UKQ1.230804.001; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/139.0.7258.158 Mobile Safari/537.36 jiuxianApp/9.2.13 from/ANDROID suptwebp/1 netEnv/wifi oadzApp lati/null long/null shopId/ areaId/500",
                "Cookie": f"token={self.token}",
                "Referer": "https://shop.jiuxian.com/",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
                "Accept-Language": "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7"
            }

            task_url = f"https://shop.jiuxian.com/show/wap/act/viewShopActivity.htm?viewType=2&actId=7418&taskToken={self.task_token}&taskId={task_id}&token={self.token}"
            browse_response = self.session.get(task_url, headers=headers, timeout=30)
            if browse_response.status_code != 200:
                phone_tail = self.get_phone_tail()
                print(f"❌ 任务页面访问失败 ({phone_tail}): HTTP {browse_response.status_code}")
                return False, 0
            
            print("✅ 任务页面访问成功，开始计时...")
            
            wait_time = 15
            print(f"⏰ 等待浏览计时 {wait_time} 秒...")
            time.sleep(wait_time)
            
            print("✅ 浏览完成，提交任务完成状态...")
            
            complete_headers = {
                "User-Agent": "Mozilla/5.0 (Linux; Android 14; M2011K2C Build/UKQ1.230804.001; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/139.0.7258.158 Mobile Safari/537.36 jiuxianApp/9.2.13 from/ANDROID suptwebp/1 netEnv/wifi oadzApp lati/null long/null shopId/ areaId/500",
                "Cookie": f"token={self.token}",
                "Referer": task_url,
                "X-Requested-With": "XMLHttpRequest",
                "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"
            }

            data = {
                "taskId": str(task_id),
                "taskToken": self.task_token
            }
            
            response = self.session.post(
                JiuxianConfig.TASK_COMPLETE_URL,
                data=data,
                headers=complete_headers,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get("code") == 1:
                    print("✅ 任务完成状态提交成功")
                    
                    params = JiuxianConfig.MINI_PROGRAM_INFO.copy()
                    params["token"] = self.token
                    params["taskId"] = str(task_id)
                    
                    reward_response = self.session.get(
                        JiuxianConfig.RECEIVE_REWARD_URL,
                        params=params,
                        headers=JiuxianConfig.MINI_PROGRAM_HEADERS,
                        timeout=30
                    )
                    
                    if reward_response.status_code == 200:
                        reward_result = reward_response.json()
                        if reward_result.get("success") == "1":
                            reward_data = reward_result["result"]
                            gold_num = reward_data.get("goldNum", 20)
                            phone_tail = self.get_phone_tail()
                            print(f"🎉 任务 '{task_name}' 完成 ({phone_tail})，获得 {gold_num} 金币")
                            return True, gold_num
                        else:
                            phone_tail = self.get_phone_tail()
                            print(f"❌ 领取奖励失败 ({phone_tail}): {reward_result.get('errMsg', '未知错误')}")
                            return False, 0
                    else:
                        phone_tail = self.get_phone_tail()
                        print(f"❌ 领取奖励请求失败 ({phone_tail}): HTTP {reward_response.status_code}")
                        return False, 0
                else:
                    phone_tail = self.get_phone_tail()
                    print(f"❌ 任务完成提交失败 ({phone_tail}): {result.get('msg', '未知错误')}")
                    return False, 0
            else:
                phone_tail = self.get_phone_tail()
                print(f"❌ 任务完成提交请求失败 ({phone_tail}): HTTP {response.status_code}")
                return False, 0
                
        except Exception as e:
            phone_tail = self.get_phone_tail()
            print(f"❌ 浏览任务异常 ({phone_tail}): {str(e)}")
            return False, 0

    def get_task_name_by_id(self, task_id: str) -> str:
        try:
            member_info = self.get_member_info()
            if member_info:
                task_channel = member_info.get("taskChannel", {})
                task_list = task_channel.get("taskList", [])
                
                for task in task_list:
                    if str(task.get("id")) == str(task_id):
                        return task.get("taskName", f"任务{task_id}")
            
            return f"任务{task_id}"
        except Exception:
            return f"任务{task_id}"

    def run_all_possible_tasks(self) -> int:
        phone_tail = self.get_phone_tail()
        print(f"\n🎯 开始执行指定浏览任务 ({phone_tail})")
        
        all_task_ids = list(range(1, 15))
        # 如果只想运行正常任务列表内的4个任务，将上面一行改行all_task_ids = [10, 11, 12, 14]
        total_gold = 0
        success_count = 0
        
        for task_id in all_task_ids:
            task_name = self.get_task_name_by_id(str(task_id))
            print(f"🔄 尝试执行{task_name} (ID:{task_id}) ({phone_tail})...")
            
            success, gold = self.complete_browse_task_original(str(task_id), task_name)
            if success:
                success_count += 1
                total_gold += gold
                print(f"✅ {task_name} 完成，获得 {gold} 金币")
            else:
                print(f"❌ {task_name} 执行失败或已完成")
            
            time.sleep(random.uniform(2, 4))
        
        phone_tail = self.get_phone_tail()
        print(f"📊 指定任务完成统计 ({phone_tail}): {success_count}/{len(all_task_ids)}，获得 {total_gold} 金币")
        return total_gold

    def run_lottery_task(self) -> Tuple[str, str]:
        """运行抽奖任务"""
        if not self.lottery_module:
            self.lottery_module = JiuxianLotteryModule(self.session, self.token, self.username)
        
        lottery_success, lottery_prize = self.lottery_module.lottery_draw()
        lottery_status = '完成' if lottery_success else '失败'
        return lottery_status, lottery_prize
    
    def run_seventh_day_lottery(self) -> str:
        if self.continuous_sign_days >= 7:
            phone_tail = self.get_phone_tail()
            print(f"\n🎉 连续签到{self.continuous_sign_days}天，执行额外抽奖 ({phone_tail})")
            if self.lottery_module:
                lottery_success, lottery_prize = self.lottery_module.lottery_draw()
                return lottery_prize
        return ""
    
    def run_all_tasks(self) -> Dict:
        phone_tail = self.get_phone_tail()
        print(f"\n🚀 开始执行所有任务 ({phone_tail})")
        
        results = {
            'phone_tail': phone_tail,
            'nickname': self.nickname,
            'login_success': False,
            'sign_success': False,
            'sign_gold': 0,
            'continuous_days': 0,
            'total_gold': 0,
            'today_gold': 0,
            'lottery_status': '未执行',
            'lottery_prize': '',
            'all_possible_tasks_gold': 0
        }
        
        # 1. 登录
        print(f"🔐 登录账号 ({phone_tail})...")
        if not self.smart_login():
            print(f"❌ 登录失败 ({phone_tail})")
            return results
        results['login_success'] = True
        results['nickname'] = self.nickname
        
        # 2. 获取会员信息
        member_info = self.get_member_info()
        if member_info:
            results['total_gold'] = self.total_gold
            results['continuous_days'] = self.continuous_sign_days
            print(f"💰 当前总金币: {results['total_gold']}")
            print(f"📅 连续签到天数: {results['continuous_days']}")
        
        # 3. 签到
        if not self.is_signed_today:
            print(f"📝 执行签到 ({phone_tail})...")
            sign_success, sign_gold = self.user_sign()
            results['sign_success'] = sign_success
            results['sign_gold'] = sign_gold
            results['today_gold'] += sign_gold
            results['continuous_days'] = self.continuous_sign_days
        else:
            print(f"✅ 今日已签到过 ({phone_tail})")
            results['sign_success'] = True
            results['sign_gold'] = 0
            results['continuous_days'] = self.continuous_sign_days
        
        # 4. 浏览任务
        print(f"🎯 执行所有可能浏览任务 ({phone_tail})...")
        all_tasks_gold = self.run_all_possible_tasks()
        results['today_gold'] += all_tasks_gold
        results['all_possible_tasks_gold'] = all_tasks_gold
        
        # 5. 抽奖任务
        print(f"🎰 运行抽奖任务 ({phone_tail})...")
        lottery_status, lottery_prize = self.run_lottery_task()
        results['lottery_status'] = lottery_status
        results['lottery_prize'] = lottery_prize
        
        # 6. 连续签到额外抽奖
        seventh_lottery_prize = ""
        if self.continuous_sign_days >= 7:
            print(f"🎉 连续签到{self.continuous_sign_days}天，执行额外抽奖 ({phone_tail})...")
            seventh_lottery_prize = self.run_seventh_day_lottery()
            if seventh_lottery_prize and seventh_lottery_prize != "已抽过":
                if results['lottery_prize'] and results['lottery_prize'] != "未执行":
                    results['lottery_prize'] = f"{results['lottery_prize']}, {seventh_lottery_prize}"
                else:
                    results['lottery_prize'] = seventh_lottery_prize
        
        # 7. 更新信息
        updated_member_info = self.get_member_info()
        if updated_member_info:
            results['total_gold'] = self.total_gold
            results['continuous_days'] = self.continuous_sign_days
        
        # 打印最终结果
        print(f"\n📊 任务执行完成 ({phone_tail})")
        print(f"✅ 签到: {'成功' if results['sign_success'] else '失败'}")
        print(f"💰 签到金币: {results['sign_gold']}")
        print(f"📅 连续签到: {results['continuous_days']} 天")
        print(f"🎯 浏览任务金币: {results['all_possible_tasks_gold']}")
        print(f"🎰 抽奖: {results['lottery_status']} - {results['lottery_prize']}")
        print(f"💰 今日获得: {results['today_gold']} 金币")
        print(f"💰 当前总金币: {results['total_gold']}")
        
        return results

# 批量运行管理器（保持不变）
class JiuxianBatchRunner:
    def __init__(self):
        self.results = []
        self.total_accounts = 0
        self.success_accounts = 0
    
    def parse_accounts_from_env(self) -> List[Tuple[str, str]]:
        accounts = []
        jiuxian_env = os.getenv('jiuxian')
        
        if jiuxian_env:
            print(f"📝 从环境变量读取账号配置")
            for line in jiuxian_env.strip().split('\n'):
                line = line.strip()
                if line and '#' in line:
                    parts = line.split('#', 1)
                    if len(parts) == 2:
                        username = parts[0].strip()
                        password = parts[1].strip()
                        if username and password:
                            accounts.append((username, password))
                            print(f"📱 账号: {username[:3]}****{username[-4:]}")
        
        return accounts
    
    def generate_report_content(self) -> str:
        """生成简洁的报告内容"""
        total_today_gold = sum(result.get('today_gold', 0) for result in self.results)
        total_current_gold = sum(result.get('total_gold', 0) for result in self.results)
        success_count = sum(1 for result in self.results if result.get('login_success'))
        
        # 构建简洁的报告内容
        content = f"🍷 酒仙网任务执行报告\n\n"
        content += f"📱 总账号数: {self.total_accounts}\n"
        content += f"✅ 成功账号: {success_count}\n"
        content += f"❌ 失败账号: {self.total_accounts - success_count}\n"
        content += f"💰 今日总获得金币: {total_today_gold}\n"
        content += f"💰 当前总金币: {total_current_gold}\n\n"
        
        content += f"📋 详细结果:\n"
        for result in self.results:
            if result.get('login_success'):
                phone_tail = result.get("phone_tail", "未知")
                nickname = result.get("nickname", "未知用户")
                
                sign_gold = result.get("sign_gold", 0)
                tasks_gold = result.get("all_possible_tasks_gold", 0)
                today_gold = result.get("today_gold", 0)
                total_gold_user = result.get("total_gold", 0)
                continuous_days = result.get("continuous_days", 0)
                lottery_prize = result.get("lottery_prize", "未知")
                
                content += f"  📱 {nickname} ({phone_tail}): "
                content += f"签到{sign_gold}金, "
                content += f"任务{tasks_gold}金, "
                content += f"今日{today_gold}金, "
                content += f"总{total_gold_user}金, "
                content += f"连续{continuous_days}天, "
                content += f"抽奖:{lottery_prize}\n"
        
        # 添加执行时间
        exec_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        content += f"\n🕐 执行时间: {exec_time}"
        
        return content
    
    def run_batch(self):
        print("🚀 开始批量运行酒仙签到脚本")
        print("=" * 50)
        
        accounts = self.parse_accounts_from_env()
        self.total_accounts = len(accounts)
        
        if self.total_accounts == 0:
            print("❌ 未找到有效的账号配置")
            return
        
        print(f"📊 共找到 {self.total_accounts} 个账号")
        
        for i, (username, password) in enumerate(accounts, 1):
            print(f"\n{'='*30}")
            print(f"👤 处理第 {i}/{self.total_accounts} 个账号: {username[:3]}****{username[-4:]}")
            print(f"{'='*30}")
            
            try:
                jiuxian = Jiuxian(username, password)
                result = jiuxian.run_all_tasks()
                self.results.append(result)
                
                if result['login_success']:
                    self.success_accounts += 1
                
                if i < self.total_accounts:
                    delay = random.uniform(5, 10)
                    print(f"⏳ 随机延迟 {delay:.1f} 秒后处理下一个账号...")
                    time.sleep(delay)
                    
            except Exception as e:
                print(f"❌ 处理账号 {username[:3]}****{username[-4:]} 时发生异常: {str(e)}")
        
        self.print_summary()
        
        report_content = self.generate_report_content()
        title = f"🍷 酒仙网任务报告 - {self.success_accounts}/{self.total_accounts}成功"
        QLNotifier.send(title, report_content)
    
    def print_summary(self):
        print(f"\n{'='*50}")
        print("📊 批量执行汇总")
        print(f"{'='*50}")
        print(f"📱 总账号数: {self.total_accounts}")
        print(f"✅ 成功账号: {self.success_accounts}")
        print(f"❌ 失败账号: {self.total_accounts - self.success_accounts}")
        
        if self.success_accounts > 0:
            total_today_gold = sum(result.get('today_gold', 0) for result in self.results)
            total_current_gold = sum(result.get('total_gold', 0) for result in self.results)
            print(f"💰 今日总获得金币: {total_today_gold}")
            print(f"💰 当前总金币: {total_current_gold}")
            
            print(f"\n📋 详细结果:")
            for result in self.results:
                if result.get('login_success'):
                    print(f"  📱 {result.get('nickname', '未知用户')} ({result.get('phone_tail', '未知')}): "
                          f"签到{result.get('sign_gold', 0)}金, "
                          f"任务{result.get('all_possible_tasks_gold', 0)}金, "
                          f"今日{result.get('today_gold', 0)}金, "
                          f"总{result.get('total_gold', 0)}金, "
                          f"连续{result.get('continuous_days', 0)}天, "
                          f"抽奖:{result.get('lottery_prize', '未知')}")

# 主函数
def main():
    print("🍷 酒仙网签到脚本 - 抽奖修复最终版")
    print("=" * 50)
    
    runner = JiuxianBatchRunner()
    runner.run_batch()

if __name__ == "__main__":
    main()