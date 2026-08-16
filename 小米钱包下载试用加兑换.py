#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
===============================================================================
                        🎯 小米钱包自动任务脚本 - 环境变量版
===============================================================================

📋 功能说明：
• 自动执行每日任务获取视频会员天数
• 支持应用下载试用任务
• 自动兑换会员功能（10点抢兑）
• 显示总收益、每日收益和预估兑换时间
• 支持多账号批量处理
• 智能识别无效账号

🔧 环境变量配置：

【必需配置】
环境变量名: xmqb
格式说明: passToken&userId
单账号示例: xmqb="abc123def456&987654321"
多账号示例: xmqb="token1&user1@token2&user2@token3&user3"

【可选配置】
环境变量名: EXCHANGE_PHONES
格式说明: 兑换手机号，与账号一一对应
示例: EXCHANGE_PHONES="13800138000@13900139000@13700137000"

📱 Token获取方法：
1. 使用抓包工具（Charles、Fiddler、浏览器F12等）
2. 访问以下链接并登录小米账号：
   https://account.xiaomi.com/pass/serviceLogin?callback=https%3A%2F%2Fapi.jr.airstarfinance.net%2Fsts%3Fsign%3D1dbHuyAmee0NAZ2xsRw5vhdVQQ8%253D%26followup%3Dhttps%253A%252F%252Fm.jr.airstarfinance.net%252Fmp%252Fapi%252Flogin%253Ffrom%253Dmipay_indexicon_TVcard%2526deepLinkEnable%253Dfalse%2526requestUrl%253Dhttps%25253A%25252F%25252Fm.jr.airstarfinance.net%25252Fmp%25252Factivity%25252FvideoActivity%25253Ffrom%25253Dmipay_indexicon_TVcard%252526_noDarkMode%25253Dtrue%252526_transparentNaviBar%25253Dtrue%252526cUserId%25253Dusyxgr5xjumiQLUoAKTOgvi858Q%252526_statusBarHeight%25253D137&sid=jrairstar&_group=DEFAULT&_snsNone=true&_loginType=ticket
3. 在Cookie中找到passToken和userId参数

🚀 青龙面板部署：
1. 添加环境变量 xmqb="你的token&你的userid"
2. （可选）添加环境变量 EXCHANGE_PHONES="你的手机号"
3. 上传脚本文件
4. 设置定时任务（建议每天运行1-2次）

💻 本地运行：
export xmqb="你的token&你的userid"
export EXCHANGE_PHONES="你的手机号"
python3 xiaomi_wallet.py

⚙️ 自动兑换配置：
• 兑换条件：总天数≥7天 且 从未兑换过 且 当前时间为10点
• 支持会员类型：iqiyi(爱奇艺)/tencent(腾讯)/youku(优酷)/mango(芒果)
• 修改 EXCHANGE_TYPE 变量可切换兑换类型
• 修改 AUTO_EXCHANGE_SWITCH 可开启/关闭自动兑换

🔒 安全间隔说明：
• 多账号间隔：30秒（避免风控）
• 浏览任务间隔：20秒（模拟真实操作）
• 奖励领取间隔：5秒（稳定性保证）
• 可在脚本顶部配置区域自定义调整

⚠️ 注意事项：
1. Token有时效性，失效后需重新抓包
2. 多账号使用建议错峰运行
3. 首次使用建议先测试单账号
4. 定期检查运行日志确保正常

===============================================================================
"""
import os
import sys
import time
import requests
import urllib3
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Union
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 尝试导入通知模块
try:
    import notify
    NOTIFY_AVAILABLE = True
    print("📢 通知功能已启用")
except ImportError:
    NOTIFY_AVAILABLE = False
    print("⚠️ 未找到notify模块，将跳过消息推送")
# 环境变量名称
ENV_NAME = "xmqb"
# 目标兑换天数
TARGET_DAYS = 30
# ==================== 自动兑换功能设置 ====================
# 总开关：是否开启自动兑换功能 (True/False)
AUTO_EXCHANGE_SWITCH = True
# 兑换会员类型 (目前支持: iqiyi/tencent/youku/mango)
EXCHANGE_TYPE = "iqiyi"
# =======================================================

# ==================== 安全间隔配置 ====================
# 多账号间隔（秒）- 账号处理完成后的等待时间
ACCOUNT_INTERVAL = 30
# 浏览任务间隔（秒）- 每个浏览任务之间的等待时间
TASK_INTERVAL = 20
# 奖励领取间隔（秒）- 领取奖励后的等待时间
REWARD_INTERVAL = 5
# 应用下载奖励等待时间（秒）
APP_REWARD_WAIT = 8
# 任务完成后等待时间（秒）
TASK_COMPLETE_WAIT = 3
# =======================================================

class RnlRequest:
    def __init__(self, cookies: Union[str, dict]):
        self.session = requests.Session()
        self._base_headers = {
            'Host': 'm.jr.airstarfinance.net',
            'User-Agent': 'Mozilla/5.0 (Linux; U; Android 14; zh-CN; M2012K11AC Build/UKQ1.230804.001; AppBundle/com.mipay.wallet; AppVersionName/6.89.1.5275.2323; AppVersionCode/20577595; MiuiVersion/stable-V816.0.13.0.UMNCNXM; DeviceId/alioth; NetworkType/WIFI; mix_version; WebViewVersion/118.0.0.0) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Mobile Safari/537.36 XiaoMi/MiuiBrowser/4.3',
        }
        self.update_cookies(cookies)
    def request(
        self,
        method: str,
        url: str,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Union[Dict[str, Any], str, bytes]] = None,
        json: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Optional[Dict[str, Any]]:
        headers = {**self._base_headers, **kwargs.pop('headers', {})}
        try:
            resp = self.session.request(
                verify=False,
                method=method.upper(),
                url=url,
                params=params,
                data=data,
                json=json,
                headers=headers,
                **kwargs
            )
            resp.raise_for_status()
            return resp.json()
        except:
            return None
    def update_cookies(self, cookies: Union[str, dict]) -> None:
        if cookies:
            if isinstance(cookies, str):
                dict_cookies = self._parse_cookies(cookies)
            else:
                dict_cookies = cookies
            self.session.cookies.update(dict_cookies)
            self._base_headers['Cookie'] = self.dict_cookie_to_string(dict_cookies)
    @staticmethod
    def _parse_cookies(cookies_str: str) -> Dict[str, str]:
        return dict(
            item.strip().split('=', 1)
            for item in cookies_str.split(';')
            if '=' in item
        )
    @staticmethod
    def dict_cookie_to_string(cookie_dict):
        cookie_list = []
        for key, value in cookie_dict.items():
            cookie_list.append(f"{key}={value}")
        return "; ".join(cookie_list)
    def get(self, url: str, params: Optional[Dict[str, Any]] = None, **kwargs) -> Optional[Dict[str, Any]]:
        return self.request('GET', url, params=params, **kwargs)
    def post(self, url: str, data: Optional[Union[Dict[str, Any], str, bytes]] = None,
             json: Optional[Dict[str, Any]] = None, **kwargs) -> Optional[Dict[str, Any]]:
        return self.request('POST', url, data=data, json=json, **kwargs)
    def __enter__(self):
        return self
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.session.close()
class RNL:
    def __init__(self, c):
        self.t_id = None
        self.activity_code = '2211-videoWelfare'
        self.rr = RnlRequest(c)
        self.total_days = 0.0
        self.today_gain = 0.0
        self.exchanged = False  # 记录是否已兑换
        self.has_exchanged_before = False  # 记录是否曾经兑换过
        self.current_user_id = None  # 存储当前处理的用户ID
        self.today_records = []  # 存储今日任务记录
        self.error_info = ""  # 存储错误信息
    def get_task_list(self):
        data = {'activityCode': self.activity_code}
        try:
            response = self.rr.post(
                'https://m.jr.airstarfinance.net/mp/api/generalActivity/getTaskList',
                data=data,
            )
            if response and response['code'] == 0:
                return [task for task in response['value']['taskInfoList'] if '浏览组浏览任务' in task['taskName']]
        except:
            pass
        return None
    def get_task(self, task_code):
        try:
            data = {
                'activityCode': self.activity_code,
                'taskCode': task_code,
                'jrairstar_ph': '98lj8puDf9Tu/WwcyMpVyQ==',
            }
            response = self.rr.post(
                'https://m.jr.airstarfinance.net/mp/api/generalActivity/getTask',
                data=data,
            )
            if response and response['code'] == 0:
                return response['value']['taskInfo']['userTaskId']
        except:
            pass
        return None
    def complete_task(self, task_id, t_id, brows_click_urlId):
        try:
            url = f'https://m.jr.airstarfinance.net/mp/api/generalActivity/completeTask?activityCode={self.activity_code}&app=com.mipay.wallet&isNfcPhone=true&channel=mipay_indexicon_TVcard&deviceType=2&system=1&visitEnvironment=2&userExtra=%7B%22platformType%22:1,%22com.miui.player%22:%224.27.0.4%22,%22com.miui.video%22:%22v2024090290(MiVideo-UN)%22,%22com.mipay.wallet%22:%226.83.0.5175.2256%22%7D&taskId={task_id}&browsTaskId={t_id}&browsClickUrlId={brows_click_urlId}&clickEntryType=undefined&festivalStatus=0'
            response = self.rr.get(url)
            if response and response['code'] == 0:
                return response['value']
        except:
            pass
        return None
    def receive_award(self, user_task_id):
        try:
            url = f'https://m.jr.airstarfinance.net/mp/api/generalActivity/luckDraw?imei=&device=manet&appLimit=%7B%22com.qiyi.video%22:false,%22com.youku.phone%22:true,%22com.tencent.qqlive%22:true,%22com.hunantv.imgo.activity%22:true,%22com.cmcc.cmvideo%22:false,%22com.sankuai.meituan%22:true,%22com.anjuke.android.app%22:false,%22com.tal.abctimelibrary%22:false,%22com.lianjia.beike%22:false,%22com.kmxs.reader%22:true,%22com.jd.jrapp%22:false,%22com.smile.gifmaker%22:true,%22com.kuaishou.nebula%22:false%7D&activityCode={self.activity_code}&userTaskId={user_task_id}&app=com.mipay.wallet&isNfcPhone=true&channel=mipay_indexicon_TVcard&deviceType=2&system=1&visitEnvironment=2&userExtra=%7B%22platformType%22:1,%22com.miui.player%22:%224.27.0.4%22,%22com.miui.video%22:%22v2024090290(MiVideo-UN)%22,%22com.mipay.wallet%22:%226.83.0.5175.2256%22%7D'
            response = self.rr.get(url)
            if response and response['code'] == 0:
                return int(response.get('value', {}).get('value', 0))
        except:
            pass
        return 0
    
    def complete_new_user_task(self):
        """完成应用下载试用任务"""
        try:
            print("📲 开始执行应用下载试用任务...")
            
            headers = {
                'Connection': 'keep-alive',
                'Accept': 'application/json, text/plain, */*',
                'Cache-Control': 'no-cache',
                'X-Request-ID': '1281eea0-e268-4fcc-9a5f-7dc11475b7db',
                'X-Requested-With': 'com.mipay.wallet',
                'Sec-Fetch-Site': 'same-origin',
                'Sec-Fetch-Mode': 'cors',
                'Sec-Fetch-Dest': 'empty',
                'Accept-Encoding': 'gzip, deflate',
                'Accept-Language': 'zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7'
            }
            
            url = 'https://m.jr.airstarfinance.net/mp/api/generalActivity/completeTask?activityCode=2211-videoWelfare&app=com.mipay.wallet&oaid=8c45c5802867e923&regId=KWkK5VsKXiIbAH8Rf6kgU6tpDPyNWgXY8YCM1mQtt5nd7i1%2F4BqzPq0uY7OlIEOd&versionCode=20577622&versionName=6.96.0.5453.2620&isNfcPhone=true&channel=mipay_indexicon_TVcard2test&deviceType=2&system=1&visitEnvironment=2&userExtra=%7B%22platformType%22:1,%22com.miui.video%22:%22v2023091090(MiVideo-ROM)%22,%22com.mipay.wallet%22:%226.96.0.5453.2620%22%7D&taskCode=NEW_USER_CAMPAIGN&browsTaskId=&browsClickUrlId=1306285&adInfoId=&triggerId='
            
            response = self.rr.get(url, headers=headers)
            if response:
                if response['code'] != 0:
                    # 检查是否是"今日任务已完成"的情况
                    error_msg = response.get('message', '')
                    if '今日任务已完成' in error_msg or '已领取' in error_msg:
                        print("✅ 应用下载试用任务今日已完成")
                        return "already_completed"
                    else:
                        print(f"❌ 应用下载试用任务失败: {error_msg}")
                        return None
                else:
                    print("✅ 应用下载试用任务完成成功")
                    return response["value"]
            else:
                print("❌ 应用下载试用任务失败: 无响应")
                return None
        except Exception as e:
            print(f"❌ 应用下载试用任务失败: {e}")
            return None

    def receive_new_user_award(self, user_task_id):
        """领取应用下载试用奖励"""
        try:
            # 如果任务已经完成，直接返回
            if user_task_id == "already_completed":
                return 0
                
            # 发送领取请求前延时
            print(f"⏳ 等待{APP_REWARD_WAIT}秒后领取奖励...")
            time.sleep(APP_REWARD_WAIT)
            
            headers = {
                'Connection': 'keep-alive',
                'sec-ch-ua': '"Chromium";v="118", "Android WebView";v="118", "Not=A?Brand";v="99"',
                'Accept': 'application/json, text/plain, */*',
                'Cache-Control': 'no-cache',
                'sec-ch-ua-mobile': '?1',
                'X-Request-ID': 'c09abfa7-6ea4-4435-a741-dff3622215cf',
                'sec-ch-ua-platform': '"Android"',
                'X-Requested-With': 'com.mipay.wallet',
                'Sec-Fetch-Site': 'same-origin',
                'Sec-Fetch-Mode': 'cors',
                'Sec-Fetch-Dest': 'empty',
                'Accept-Encoding': 'gzip, deflate, br',
                'Accept-Language': 'zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7'
            }
            
            url = f'https://m.jr.airstarfinance.net/mp/api/generalActivity/luckDraw?imei=&device=alioth&appLimit=%7B%22com.qiyi.video%22:false,%22com.youku.phone%22:false,%22com.tencent.qqlive%22:false,%22com.hunantv.imgo.activity%22:false,%22com.cmcc.cmvideo%22:false,%22com.sankuai.meituan%22:false,%22com.anjuke.android.app%22:false,%22com.tal.abctimelibrary%22:false,%22com.lianjia.beike%22:false,%22com.kmxs.reader%22:false,%22com.jd.jrapp%22:false,%22com.smile.gifmaker%22:true,%22com.kuaishou.nebula%22:false%7D&activityCode=2211-videoWelfare&userTaskId={user_task_id}&app=com.mipay.wallet&oaid=8c45c5802867e923&regId=L522i5qLZR9%2Bs25kEqPBJYbbHqUS4LrpuTsgl9kdsbcyU7tjWmx1BewlRNSSZaOT&versionCode=20577622&versionName=6.96.0.5453.2620&isNfcPhone=true&channel=mipay_indexicon_TVcard2test&deviceType=2&system=1&visitEnvironment=2&userExtra=%7B%22platformType%22:1,%22com.miui.video%22:%22v2023091090(MiVideo-ROM)%22,%22com.mipay.wallet%22:%226.96.0.5453.2620%22%7D'
            
            response = self.rr.get(url, headers=headers)
            if response:
                if response['code'] != 0:
                    # 检查是否是"今日奖励已领取"的情况
                    error_msg = response.get('message', '')
                    if '今日奖励已领取' in error_msg or '已领取' in error_msg:
                        print("✅ 应用下载试用奖励今日已领取")
                        return 0
                    else:
                        print(f"❌ 领取应用下载试用奖励失败: {error_msg}")
                        return 0
                else:
                    prize_info = response['value']['prizeInfo']
                    award_days = int(prize_info["amount"]) / 100
                    print(f"🎉 应用下载试用奖励领取成功: 获得 {award_days:.2f}天 {prize_info['prizeDesc']}")
                    return award_days
            else:
                print("❌ 领取应用下载试用奖励失败: 无响应")
                return 0
        except Exception as e:
            print(f"❌ 领取应用下载试用奖励失败: {e}")
            return 0
    
    def query_user_info(self):
        """查询用户总天数和今日收益"""
        try:
            # 查询总天数
            total_res = self.rr.get('https://m.jr.airstarfinance.net/mp/api/generalActivity/queryUserGoldRichSum?app=com.mipay.wallet&deviceType=2&system=1&visitEnvironment=2&userExtra={"platformType":1,"com.miui.player":"4.27.0.4","com.miui.video":"v2024090290(MiVideo-UN)","com.mipay.wallet":"6.83.0.5175.2256"}&activityCode=2211-videoWelfare')
            if total_res and total_res['code'] == 0:
                self.total_days = int(total_res['value']) / 100
            
            # 查询当天记录
            self.today_gain = 0.0
            current_date = datetime.now().strftime("%Y-%m-%d")
            history_res = self.rr.get(
                f'https://m.jr.airstarfinance.net/mp/api/generalActivity/queryUserJoinList?&userExtra=%7B%22platformType%22:1,%22com.miui.player%22:%224.27.0.4%22,%22com.miui.video%22:%22v2024090290(MiVideo-UN)%22,%22com.mipay.wallet%22:%226.83.0.5175.2256%22%7D&activityCode={self.activity_code}&pageNum=1&pageSize=20',
            )
            
            # 清空今日记录
            self.today_records = []
            
            if history_res and history_res['code'] == 0:
                for record in history_res['value']['data']:
                    if record['createTime'].startswith(current_date):
                        self.today_gain += int(record['value']) / 100
                        # 保存今日记录用于通知
                        self.today_records.append({
                            'createTime': record['createTime'],
                            'value': record['value']
                        })
            
            # 检查是否曾经兑换过
            self.has_exchanged_before = self.check_exchange_history()
            
            return True
        except Exception as e:
            self.error_info = f'查询用户信息失败：{e}'
            return False
    def check_exchange_history(self):
        """检查兑换历史记录，判断是否曾经兑换过"""
        try:
            # 查询兑换记录
            history_res = self.rr.get(
                f'https://m.jr.airstarfinance.net/mp/api/generalActivity/queryUserExchangeList?activityCode={self.activity_code}&pageNum=1&pageSize=20',
            )
            
            if history_res and history_res['code'] == 0:
                # 如果有兑换记录，则说明曾经兑换过
                return len(history_res['value']['data']) > 0
        except:
            pass
        return False
    def run_tasks(self):
        """执行任务并返回是否有效账号"""
        # 查询用户信息
        if not self.query_user_info():
            return False, "无法查询账户信息"
        
        # 记录初始今日收益
        initial_gain = self.today_gain
        
        # 先尝试完成新手任务
        print("\n📥 开始执行应用下载试用任务")
        new_user_task_id = self.complete_new_user_task()
        if new_user_task_id:
            time.sleep(TASK_COMPLETE_WAIT)
            new_user_award = self.receive_new_user_award(new_user_task_id)
            if new_user_award > 0:
                # 更新今日收益
                self.today_gain += new_user_award
                print(f"💫 应用下载试用任务完成，获得 {new_user_award:.2f} 天奖励")
            time.sleep(TASK_COMPLETE_WAIT)
        
        # 获取任务列表
        tasks = self.get_task_list()
        if not tasks:
            return False, "无法获取任务列表"
        
        # 执行任务
        for i, task in enumerate(tasks[:2]):  # 只执行前两个任务
            try:
                t_id = task['generalActivityUrlInfo']['id']
                self.t_id = t_id
            except:
                t_id = self.t_id or ""
            
            task_id = task.get('taskId', "")
            task_code = task.get('taskCode', "")
            brows_click_url_id = task['generalActivityUrlInfo'].get('browsClickUrlId', "")
            
            # 等待
            print(f"⏳ 开始执行第 {i+1} 个浏览任务，等待{TASK_INTERVAL}秒...")
            time.sleep(TASK_INTERVAL)
            
            # 完成任务
            user_task_id = self.complete_task(
                task_id=task_id,
                t_id=t_id,
                brows_click_urlId=brows_click_url_id,
            )
            
            if not user_task_id:
                user_task_id = self.get_task(task_code=task_code)
                time.sleep(TASK_COMPLETE_WAIT)
            
            # 领取奖励
            if user_task_id:
                award_value = self.receive_award(user_task_id=user_task_id)
                if award_value > 0:
                    # 更新今日收益
                    award_days = award_value / 100
                    self.today_gain += award_days
                    print(f"✅ 第 {i+1} 个浏览任务完成，获得 {award_days:.2f} 天奖励")
                time.sleep(REWARD_INTERVAL)
        
        # 更新用户信息
        self.query_user_info()
        
        # 计算本次获得的收益
        gain_this_run = self.today_gain - initial_gain
        
        # 计算预估天数
        remaining_days = TARGET_DAYS - self.total_days
        if gain_this_run > 0 and remaining_days > 0:
            estimated_days = remaining_days / gain_this_run
        else:
            estimated_days = 0
        
        # 有效账号
        return True, {
            "total_days": self.total_days,
            "today_gain": self.today_gain,
            "gain_this_run": gain_this_run,
            "estimated_days": estimated_days,
            "has_exchanged_before": self.has_exchanged_before
        }
    def exchange_member(self, phone: str) -> bool:
        """兑换会员"""
        try:
            # 检查是否已兑换过
            if self.exchanged:
                print("⚠️ 该账号今日已兑换过，跳过")
                return False
                
            # 兑换请求
            url = f"https://m.jr.airstarfinance.net/mp/api/generalActivity/exchange?activityCode={self.activity_code}&exchangeCode={EXCHANGE_TYPE}&phone={phone}&app=com.mipay.wallet&deviceType=2&system=1&visitEnvironment=2&userExtra=%7B%22platformType%22:1%7D"
            response = self.rr.get(url)
            
            if response:
                if response.get('code') == 0:
                    self.exchanged = True
                    return True
                else:
                    # 如果返回了错误消息，显示具体错误
                    print(f"❌ 兑换失败: {response.get('message', '未知错误')}")
            else:
                print("❌ 兑换失败: 缺货补货中，明天再试")
        except Exception as e:
            print(f"❌ 兑换请求异常: {str(e)}")
        return False
def get_xiaomi_cookies(pass_token, user_id):
    """获取小米钱包cookies"""
    login_url = 'https://account.xiaomi.com/pass/serviceLogin?callback=https%3A%2F%2Fapi.jr.airstarfinance.net%2Fsts%3Fsign%3D1dbHuyAmee0NAZ2xsRw5vhdVQQ8%253D%26followup%3Dhttps%253A%252F%252Fm.jr.airstarfinance.net%252Fmp%252Fapi%252Flogin%253Ffrom%253Dmipay_indexicon_TVcard%2526deepLinkEnable%253Dfalse%2526requestUrl%253Dhttps%25253A%25252F%25252Fm.jr.airstarfinance.net%25252Fmp%25252Factivity%25252FvideoActivity%25253Ffrom%25253Dmipay_indexicon_TVcard%252526_noDarkMode%25253Dtrue%252526_transparentNaviBar%25253Dtrue%252526cUserId%25253Dusyxgr5xjumiQLUoAKTOgvi858Q%252526_statusBarHeight%25253D137&sid=jrairstar&_group=DEFAULT&_snsNone=true&_loginType=ticket'
    headers = {
        'user-agent': 'Mozilla/5.0 (Linux; U; Android 14; zh-CN; M2012K11AC Build/UKQ1.230804.001) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/100.0.4896.127 Mobile Safari/537.36 XiaoMi/MiuiBrowser/4.3',
        'cookie': f'passToken={pass_token}; userId={user_id};'
    }
    try:
        session = requests.Session()
        session.get(url=login_url, headers=headers, verify=False, timeout=10)
        cookies = session.cookies.get_dict()
        if 'cUserId' in cookies and 'serviceToken' in cookies:
            return f"cUserId={cookies.get('cUserId')};jrairstar_serviceToken={cookies.get('serviceToken')}"
    except:
        pass
    return None
def format_days(days):
    """格式化天数显示（保留一位小数）"""
    # 直接显示天数，不转换为分钟
    return f"{days:.1f}天"
def mask_user_id(user_id):
    """格式化用户ID显示，只显示前三位和后三位，中间用星号代替"""
    if len(user_id) <= 6:
        # 如果ID长度小于等于6，全部显示星号
        return '*' * len(user_id)
    # 显示前3位 + 6个星号 + 后3位
    return user_id[:3] + '*' * 6 + user_id[-3:]

def generate_notification(account_id, rnl_instance):
    """生成格式化的通知消息"""
    current_date = datetime.now().strftime("%Y-%m-%d")
    
    msg = f"""
【账号信息】
✨ 账号ID：{mask_user_id(account_id)}
📊 当前兑换视频天数：{format_days(rnl_instance.total_days)}

📅 {current_date} 任务记录
{"-"*40}"""
    
    # 显示今日记录
    if rnl_instance.today_records:
        for record in rnl_instance.today_records:
            record_time = record["createTime"]
            days = int(record["value"]) / 100
            msg += f"""
⏰ {record_time}
🎁 领到视频会员，+{days:.2f}天"""
    else:
        msg += """
ℹ️ 今日暂无任务记录"""
    
    # 显示错误信息
    if rnl_instance.error_info:
        msg += f"""
⚠️ 执行异常：{rnl_instance.error_info}"""
    
    msg += f"""
{"="*40}"""
    
    return msg
def main():
    # 环境变量检测
    env_value = os.getenv(ENV_NAME)
    if not env_value:
        print(f"❌ 环境变量 {ENV_NAME} 未设置")
        print("请在青龙面板中添加环境变量，格式：passToken1&userId1@passToken2&userId2")
        sys.exit(1)
    
    # 解析账号信息
    accounts = []
    account_strs = env_value.split('@')
    for acc_str in account_strs:
        if '&' not in acc_str:
            print(f"⚠️ 账号格式错误: {acc_str}，跳过")
            continue
        parts = acc_str.split('&', 1)
        if len(parts) != 2:
            print(f"⚠️ 账号格式错误: {acc_str}，跳过")
            continue
        pass_token, user_id = parts
        accounts.append({
            'passToken': pass_token.strip(),
            'userId': user_id.strip()
        })
    
    if not accounts:
        print("❌ 未找到有效账号信息")
        sys.exit(1)
    
    print(f"✅ 找到 {len(accounts)} 个账号")
    print(f"⏱️ 目标兑换天数: {TARGET_DAYS}天")
    print(f"🔌 自动兑换功能: {'已开启' if AUTO_EXCHANGE_SWITCH else '已关闭'}")
    if AUTO_EXCHANGE_SWITCH:
        print(f"📱 兑换会员类型: {EXCHANGE_TYPE}")
        print(f"🎯 兑换条件: 总天数≥7天且从未兑换过")
    print("=" * 60)
    
    # 获取兑换手机号环境变量
    exchange_phones = []
    exchange_phones_str = os.getenv("EXCHANGE_PHONES", "")
    if exchange_phones_str:
        exchange_phones = exchange_phones_str.split('@')
        print(f"📱 找到 {len(exchange_phones)} 个兑换手机号")
    else:
        print("⚠️ 未设置兑换手机号环境变量 EXCHANGE_PHONES")
    
    # 构建完整通知消息
    full_notification = "📺【小米钱包任务执行结果】\n"
    
    # 执行每个账号的任务
    valid_count = 0
    exchange_count = 0
    for idx, account in enumerate(accounts):
        user_id = account.get('userId', '未知')
        masked_id = mask_user_id(user_id)  # 获取脱敏后的用户ID
        print(f"\n▶️ 开始账号 {idx+1}/{len(accounts)} (ID: {masked_id})")
        
        # 获取 cookies
        start_time = time.time()
        cookies = get_xiaomi_cookies(
            account.get('passToken', ''), 
            account.get('userId', '')
        )
        
        if not cookies:
            print("❌ 无效账号 - 登录失败")
            # 创建一个临时的RNL实例用于生成通知
            rnl = RNL(None)
            rnl.current_user_id = user_id
            rnl.error_info = "登录失败，无法获取Cookie"
            # 生成当前账号的通知消息并添加到完整通知中
            account_notification = generate_notification(user_id, rnl)
            full_notification += account_notification
            continue
        
        # 执行任务
        try:
            rnl = RNL(cookies)
            rnl.current_user_id = user_id  # 设置当前用户ID
            is_valid, result = rnl.run_tasks()
            
            if not is_valid:
                print("❌ 无效账号 - 无法获取任务")
                rnl.error_info = result  # 将错误信息存储到error_info中
                # 生成当前账号的通知消息并添加到完整通知中
                account_notification = generate_notification(user_id, rnl)
                full_notification += account_notification
                continue
                
            # 有效账号计数
            valid_count += 1
            
            # 输出结果
            elapsed = time.time() - start_time
            print(f"✅ 账号有效 - 任务完成")
            print(f"⏱️ 耗时: {elapsed:.1f}秒")
            print(f"💎 当前总天数: {format_days(result['total_days'])}")
            print(f"📈 今日总收益: {format_days(result['today_gain'])}")  # 直接显示小数形式的天数
            
            # 生成当前账号的通知消息并添加到完整通知中
            account_notification = generate_notification(user_id, rnl)
            full_notification += account_notification
            
            if result['gain_this_run'] > 0:
                print(f"🎁 本次获得: {format_days(result['gain_this_run'])}")
                
                # 计算预估天数
                if result['estimated_days'] > 0:
                    print(f"⏳ 预估兑换: 约 {result['estimated_days']:.1f} 天后可兑换会员")
                else:
                    print("🎉 恭喜！已达成兑换目标")
            else:
                print("ℹ️ 今日已无任务可完成")
            
            # 进度条
            progress = min(100, result['total_days'] / TARGET_DAYS * 100)
            print(f"\n📊 进度: [{('=' * int(progress//5)).ljust(20)}] {progress:.1f}%")
            print(f"🎯 目标: {TARGET_DAYS}天 | 剩余: {max(0, TARGET_DAYS - result['total_days']):.1f}天")
            
            # 显示兑换历史状态
            if result['has_exchanged_before']:
                print("ℹ️ 该账号曾经兑换过会员")
            else:
                print("ℹ️ 该账号从未兑换过会员")
            
            # ================ 自动兑换功能 ================
            if AUTO_EXCHANGE_SWITCH:
                # 获取当前时间（UTC+8）
                beijing_time = datetime.utcnow() + timedelta(hours=8)
                current_hour = beijing_time.hour
                
                # 检查兑换条件：
                # 1. 总天数≥7天
                # 2. 从未兑换过
                # 3. 当前时间是10点
                if (result['total_days'] >= 7 and 
                    not result['has_exchanged_before'] and 
                    current_hour == 10):
                    
                    # 获取手机号
                    phone = ""
                    if idx < len(exchange_phones) and exchange_phones[idx]:
                        phone = exchange_phones[idx].strip()
                        print(f"⏰ 检测到10点，满足兑换条件（≥7天且首次兑换），开始兑换{EXCHANGE_TYPE}会员到手机: {phone}")
                        
                        # 执行兑换
                        if rnl.exchange_member(phone):
                            exchange_count += 1
                            print(f"🎉 {EXCHANGE_TYPE}会员兑换成功！")
                        else:
                            print("⚠️ 兑换失败，请检查日志")
                    else:
                        print(f"⚠️ 未找到对应的兑换手机号，无法兑换{EXCHANGE_TYPE}会员")
                else:
                    # 显示不兑换的原因
                    reasons = []
                    if result['total_days'] < 7:
                        reasons.append(f"总天数不足7天（当前{result['total_days']:.1f}天）")
                    if result['has_exchanged_before']:
                        reasons.append("该账号已兑换过会员")
                    if current_hour != 10:
                        reasons.append(f"当前时间 {beijing_time.strftime('%H:%M')} 非10点")
                    
                    if reasons:
                        print(f"ℹ️ 不满足兑换条件: {'，'.join(reasons)}")
            # ===========================================
            
        except Exception as e:
            print(f"⚠️ 执行异常: {str(e)}")
            # 创建一个临时的RNL实例用于生成通知
            if 'rnl' not in locals():
                rnl = RNL(None)
                rnl.current_user_id = user_id
            rnl.error_info = f"执行异常: {str(e)}"
            # 生成当前账号的通知消息并添加到完整通知中
            account_notification = generate_notification(user_id, rnl)
            full_notification += account_notification
        
        print(f"🔚 账号 {masked_id} 处理完成")
        print("-" * 50)
        time.sleep(ACCOUNT_INTERVAL)
    
    # 添加汇总信息到通知
    full_notification += f"""
📊 执行汇总：
✅ 有效账号数：{valid_count}/{len(accounts)}
🎁 成功兑换会员：{exchange_count}个
⏰ 执行时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""

    # 最终统计
    print("\n" + "=" * 60)
    print(f"✅ 任务完成 - 有效账号: {valid_count}/{len(accounts)}")
    print(f"🎁 成功兑换会员: {exchange_count}个")
    print(f"⏰ 执行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    # 发送通知
    if NOTIFY_AVAILABLE:
        try:
            print("\n📢 正在发送通知...")
            notify.send("小米钱包任务推送", full_notification)
            print("✅ 通知发送成功")
        except Exception as e:
            print(f"❌ 通知发送失败: {str(e)}")
    else:
        print("\n📄 完整通知内容:")
        print(full_notification)
if __name__ == "__main__":
    main()