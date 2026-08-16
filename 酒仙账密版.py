#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""

酒仙app/微信小程序签到脚本V1.1


操作步骤：

打开上方链接

截图保存二维码

微信扫码参与活动

点击"立即领取"获得1000积分！！


！！！请勿在0-1点之间运行！！！
定时规则：（每天上午9点10分运行）
10 9 * * *



脚本特色
· 自动完成每日签到 + 3个浏览任务
· 支持多账号批量运行
· 同时支持账号密码登录和Token登录
· 支持PushPlus微信推送通知
· 平均每日可获得约100金币


配置说明：

方式一：账号密码登录（多用户换行分割）
变量名：jiuxian
格式：
手机号#密码
13800138000#123456
13900139000#abcdef

注意：如使用账号密码登录，请先在App中修改为自定义密码





方式二：Token登录（抓包微信小程序）
变量名：JX_TOKENS
获取方式：
抓包域名：https://newappuser.jiuxian.com/

在请求参数中查找token值

格式：
token1
token2
token3


推送通知（可选）
变量名：PUSHPLUS_TOKEN
在 PushPlus官网 获取Token，用于接收运行结果推送



每日任务清单：
· 每日签到 [正常] - 10-70金币，连续签到奖励更高
· 浏览任务1 [正常] - 20金币，自动完成
· 浏览任务2 [正常] - 20金币，自动完成
· 浏览任务3 [正常] - 20金币，自动完成
· 分享任务 [待完善] - 100金币，需要手动完成

收益估算：
· 基础收益：每日约70-120金币
· 连续签到：每周额外奖励
· 月累计：约3000金币

积分兑换

兑换内容：
· 多种实物商品


积分规则：
· 有效期：当年积分次年年底失效
· 清空机制：注意及时使用

#####################################################################
本脚本采用三层架构设计，请下载以下3个文件并放在同一文件夹中：

├── jiuxian_config.py     # 配置层 - 管理应用配置、API接口和设备信息
├── jiuxian账密版.py      # 业务逻辑层 - 主要的业务逻辑和任务执行流程
└── token_manager.py      # 数据持久层 - 负责Token数据的存储和管理

使用步骤：

将三个文件下载到同一文件夹

配置环境变量（jiuxian 或 JX_TOKENS）

运行主程序：task jiuxian账密版.py



####################################################################



-----------------------------------------------------------

免责声明

· 本脚本仅供学习交流使用，不得用于商业用途
· 使用者应对自己的行为负责，脚本作者不承担任何法律责任
· 请合理使用脚本，遵守相关平台规则
· 禁止将脚本用于任何违法违纪行为
· 如遇平台规则变更，请及时停止使用
· 下载或使用即代表同意以上声明

使用建议

· 建议设置合理的执行频率，避免对服务器造成压力
· 妥善保管账号信息，注意账号安全
· 关注平台规则变化，及时调整使用方式
· 如发现异常，请立即停止使用

风险提示

· 使用自动化脚本可能存在账号风险
· 请根据自身情况谨慎使用
· 如不确定是否合规，建议手动操作
------------------------------------------------------------
"""
import os
import json
import time
import random
import requests
from typing import Dict, List, Optional, Tuple
import urllib3
from jiuxian_config import JiuxianConfig
from token_manager import TokenManager

# 禁用SSL警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class Jiuxian:
    def __init__(self, username: str = None, password: str = None, token: str = None):
        self.username = username
        self.password = password
        self.token = token
        self.uid = None
        self.nickname = None
        self.task_token = None
        self.session = requests.Session()
        self.session.verify = False
        self.token_manager = TokenManager(JiuxianConfig.TOKEN_FILE)
        
    def get_phone_tail(self, phone: str = None) -> str:
        """获取手机尾号（脱敏处理）"""
        if not phone:
            phone = self.username or ""
        if phone and len(phone) >= 4:
            return f"******{phone[-4:]}"
        return "****"
        
    def load_saved_token(self) -> bool:
        """加载已保存的Token"""
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
        """保存当前Token信息"""
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
        """使用账号密码登录"""
        try:
            if not self.username or not self.password:
                print("❌ 缺少账号或密码")
                return False
                
            login_data = JiuxianConfig.DEVICE_INFO.copy()
            login_data.update({
                "appKey": JiuxianConfig.APP_KEY,
                "userName": self.username,
                "passWord": self.password
            })
            
            response = self.session.post(
                JiuxianConfig.LOGIN_URL,
                data=login_data,
                headers=JiuxianConfig.HEADERS,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get("success") == "1":
                    user_info = result["result"]["userInfo"]
                    self.token = user_info["token"]
                    self.uid = user_info["uid"]
                    self.nickname = user_info["nickName"]
                    
                    # 保存新的Token
                    self.save_current_token()
                    phone_tail = self.get_phone_tail()
                    print(f"✅ 密码登录成功: {self.nickname} ({phone_tail})")
                    return True
                else:
                    phone_tail = self.get_phone_tail()
                    print(f"❌ 密码登录失败 ({phone_tail}): {result.get('errMsg', '未知错误')}")
                    # 登录失败时删除无效Token
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
    
    def login_with_token(self) -> bool:
        """使用Token登录"""
        try:
            if not self.token:
                print("❌ 未提供Token")
                return False
                
            # 直接使用提供的Token，验证其有效性
            phone_tail = self.get_phone_tail()
            print(f"🔑 使用提供的Token登录 ({phone_tail})...")
            return self.check_token_valid()
            
        except Exception as e:
            phone_tail = self.get_phone_tail()
            print(f"❌ Token登录异常 ({phone_tail}): {str(e)}")
            return False
    
    def check_token_valid(self) -> bool:
        """检查当前Token是否有效"""
        if not self.token:
            return False
            
        try:
            # 通过获取会员信息来验证Token有效性
            member_info = self.get_member_info()
            if member_info:
                # 如果获取到了会员信息，说明Token有效
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
        """智能登录：优先使用Token，失败时使用密码登录"""
        # 如果有直接提供的Token，优先使用
        if self.token:
            phone_tail = self.get_phone_tail()
            print(f"🔄 尝试使用提供的Token登录 ({phone_tail})...")
            if self.login_with_token():
                return True
            else:
                print("❌ 提供的Token无效，尝试其他登录方式...")
        
        # 1. 尝试加载已保存的Token（需要用户名）
        if self.username and self.load_saved_token():
            # 2. 验证Token是否仍然有效
            if self.check_token_valid():
                phone_tail = self.get_phone_tail()
                print(f"✅ Token登录成功: {self.nickname} ({phone_tail})")
                return True
            else:
                phone_tail = self.get_phone_tail()
                print(f"🔄 保存的Token已过期 ({phone_tail})，尝试密码登录...")
                # Token无效，清除并重新登录
                self.token_manager.delete_token(self.username)
        
        # 3. 使用密码登录（需要用户名和密码）
        if self.username and self.password:
            password_login_success = self.login_with_password()
            if password_login_success:
                # 密码登录成功后立即获取会员信息来设置taskToken
                self.get_member_info()
                return True
        
        phone_tail = self.get_phone_tail()
        print(f"❌ 所有登录方式都失败了 ({phone_tail})")
        return False
    
    def get_member_info(self) -> Optional[Dict]:
        """获取会员信息（包含任务列表和taskToken）"""
        if not self.token:
            phone_tail = self.get_phone_tail()
            print(f"❌ 请先登录 ({phone_tail})")
            return None
            
        try:
            params = JiuxianConfig.DEVICE_INFO.copy()
            params["token"] = self.token
            params["appKey"] = JiuxianConfig.APP_KEY
            
            response = self.session.get(
                JiuxianConfig.MEMBER_INFO_URL,
                params=params,
                headers=JiuxianConfig.HEADERS,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get("success") == "1":
                    member_data = result["result"]
                    # 保存taskToken到实例变量中
                    task_channel = member_data.get("taskChannel", {})
                    self.task_token = task_channel.get("taskToken", "")
                    if self.task_token:
                        phone_tail = self.get_phone_tail()
                        print(f"🔑 获取到taskToken ({phone_tail}): {self.task_token}")
                    else:
                        phone_tail = self.get_phone_tail()
                        print(f"⚠️ 未获取到taskToken ({phone_tail})")
                    return member_data
                else:
                    # Token可能已过期
                    if result.get("errCode") in ["TOKEN_EXPIRED", "INVALID_TOKEN"]:
                        phone_tail = self.get_phone_tail()
                        print(f"❌ Token已过期 ({phone_tail})")
                        if self.username:
                            self.token_manager.delete_token(self.username)
                    return None
            else:
                phone_tail = self.get_phone_tail()
                print(f"❌ 获取会员信息请求失败 ({phone_tail}): HTTP {response.status_code}")
                return None
                
        except Exception as e:
            phone_tail = self.get_phone_tail()
            print(f"❌ 获取会员信息异常 ({phone_tail}): {str(e)}")
            return None
    
    def check_in(self) -> Tuple[bool, str]:
        """每日签到"""
        try:
            if not self.token:
                return False, "未登录"
                
            params = JiuxianConfig.DEVICE_INFO.copy()
            params["token"] = self.token
            params["appKey"] = JiuxianConfig.APP_KEY
            
            response = self.session.get(
                JiuxianConfig.SIGN_URL,
                params=params,
                headers=JiuxianConfig.HEADERS,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get("success") == "1":
                    sign_data = result["result"]
                    sign_days = sign_data.get("signDays", 0)
                    received_golds = sign_data.get("receivedGoldNums", 0)
                    will_get_golds = sign_data.get("willGetGolds", 0)
                    
                    message = f"签到成功！连续签到{sign_days}天，获得{received_golds}金币"
                    if will_get_golds > 0:
                        message += f"，明日可获得{will_get_golds}金币"
                    
                    phone_tail = self.get_phone_tail()
                    print(f"✅ {message} ({phone_tail})")
                    return True, message
                else:
                    error_msg = result.get('errMsg', '未知错误')
                    phone_tail = self.get_phone_tail()
                    print(f"❌ 签到失败 ({phone_tail}): {error_msg}")
                    return False, error_msg
            else:
                error_msg = f"签到请求失败: HTTP {response.status_code}"
                phone_tail = self.get_phone_tail()
                print(f"❌ {error_msg} ({phone_tail})")
                return False, error_msg
                
        except Exception as e:
            error_msg = f"签到异常: {str(e)}"
            phone_tail = self.get_phone_tail()
            print(f"❌ {error_msg} ({phone_tail})")
            return False, error_msg
    
    def complete_browse_task(self, task: Dict) -> bool:
        """完成浏览任务"""
        try:
            if not self.task_token:
                phone_tail = self.get_phone_tail()
                print(f"❌ 未获取到taskToken ({phone_tail})，无法完成任务")
                return False
                
            task_id = task["id"]
            task_name = task["taskName"]
            task_url = task["url"]
            count_down = task.get("countDown", 15)
            
            phone_tail = self.get_phone_tail()
            print(f"🔄 开始浏览任务 ({phone_tail}): {task_name}, 需要浏览 {count_down} 秒")

            # 设置浏览页面的请求头
            browse_headers = {
                "User-Agent": "Mozilla/5.0 (Linux; Android 14; M2011K2C Build/UKQ1.230804.001; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/139.0.7258.158 Mobile Safari/537.36 jiuxianApp/9.2.13 from/ANDROID suptwebp/1 netEnv/wifi oadzApp lati/null long/null shopId/ areaId/500",
                "Cookie": f"token={self.token}",
                "Referer": "https://shop.jiuxian.com/",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
                "Accept-Language": "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7"
            }

            print("📱 访问任务页面开始计时...")
            
            # 1. 访问任务页面开始计时
            browse_response = self.session.get(task_url, headers=browse_headers, timeout=30)
            if browse_response.status_code != 200:
                phone_tail = self.get_phone_tail()
                print(f"❌ 任务页面访问失败 ({phone_tail}): HTTP {browse_response.status_code}")
                return False
            
            print("✅ 任务页面访问成功，开始计时...")
            
            # 2. 等待浏览时间
            wait_time = count_down + 5
            print(f"⏰ 等待浏览计时 {wait_time} 秒...")
            time.sleep(wait_time)
            
            print("✅ 浏览完成，提交任务完成状态...")
            
            # 3. 提交任务完成状态
            complete_success = self.submit_task_completion(task_id, task_url)
            if not complete_success:
                return False
            
            print("✅ 任务完成状态提交成功")
            
            # 4. 领取金币奖励
            print("💰 领取任务奖励...")
            return self.receive_reward(task_id, task_name)
            
        except Exception as e:
            phone_tail = self.get_phone_tail()
            print(f"❌ 浏览任务异常 ({phone_tail}): {str(e)}")
            import traceback
            print(f"详细错误: {traceback.format_exc()}")
            return False
    
    def complete_share_task(self, task: Dict) -> bool:
        """完成分享任务"""
        try:
            if not self.task_token:
                phone_tail = self.get_phone_tail()
                print(f"❌ 未获取到taskToken ({phone_tail})，无法完成任务")
                return False
                
            task_id = task["id"]
            task_name = task["taskName"]
            task_url = task["url"]
            
            phone_tail = self.get_phone_tail()
            print(f"🔄 开始分享任务 ({phone_tail}): {task_name}")

            # 设置请求头
            headers = {
                "User-Agent": "Mozilla/5.0 (Linux; Android 14; M2011K2C Build/UKQ1.230804.001; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/139.0.7258.158 Mobile Safari/537.36 jiuxianApp/9.2.13 from/ANDROID suptwebp/1 netEnv/wifi oadzApp lati/null long/null shopId/ areaId/500",
                "Cookie": f"token={self.token}",
                "Referer": "https://shop.jiuxian.com/"
            }

            print("📱 访问分享页面...")
            # 1. 访问分享页面
            response = self.session.get(task_url, headers=headers, timeout=30)
            if response.status_code != 200:
                phone_tail = self.get_phone_tail()
                print(f"❌ 分享页面访问失败 ({phone_tail}): HTTP {response.status_code}")
                return False
            
            print("✅ 分享页面访问成功")
            
            # 2. 调用分享上报接口
            print("📤 上报分享行为...")
            share_success = self.report_share(task_url)
            if not share_success:
                print("❌ 分享上报失败")
                return False
            
            print("✅ 分享上报成功")
            
            # 3. 提交任务完成状态
            print("✅ 提交任务完成状态...")
            complete_success = self.submit_task_completion(task_id, task_url)
            if not complete_success:
                return False
            
            # 4. 领取金币奖励
            print("💰 领取任务奖励...")
            return self.receive_reward(task_id, task_name)
            
        except Exception as e:
            phone_tail = self.get_phone_tail()
            print(f"❌ 分享任务异常 ({phone_tail}): {str(e)}")
            return False
    
    def report_share(self, task_url: str) -> bool:
        """上报分享行为（修复编码问题）"""
        try:
            boundary = "d38dd6cb-be16-4e1c-91ec-44369961499f"
            headers = {
                "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 14; M2011K2C Build/UKQ1.230804.001)",
                "Content-Type": f"multipart/form-data; boundary={boundary}",
                "Host": "log.umsns.com"
            }
            
            # 使用字典构建表单数据
            form_fields = {
                "de": "M2011K2C",
                "u_sharetype": "native",
                "opid": "9",
                "sdkv": "7.1.6",
                "title": "酒仙网",
                "mac": "no mac",
                "dt": str(int(time.time() * 1000)),
                "uid": "a90fd0967241099b5242c9a2ea2b97efod",
                "sn": "",
                "pcv": "3.0",
                "os": "Android",
                "ek": "-1",
                "os_version": "14",
                "en": "Wi-Fi",
                "ak": "51ff1ac356240b6fb20a2156",
                "url": task_url,
                "ct": "酒等你来，发现一个超级好的活动，赶快买买买！",
                "ftype": "0",
                "imei": "a7204ced77696f16",
                "sns": '{"qq":""}',
                "furl": "http://m.jiuxian.com/mobile/android/update/picture/icon_launcher_new.png",
                "to": '{"qq":""}',
                "android_id": "2185ce8ea28df6ab",
                "tp": "1",
                "dc": "com.umeng.share"
            }
            
            # 自动生成multipart格式，使用UTF-8编码
            form_data = ""
            for name, value in form_fields.items():
                form_data += f"""--{boundary}
Content-Disposition: form-data; name="{name}"
Content-Type: text/plain; charset=UTF-8

{value}
"""
            form_data += f"--{boundary}--"
            
            # 显式使用UTF-8编码
            response = self.session.post(
                JiuxianConfig.SHARE_REPORT_URL, 
                data=form_data.encode('utf-8'),
                headers=headers, 
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get("st") == 200:
                    return True
            print(f"❌ 分享上报失败: {response.text}")
            return False
            
        except Exception as e:
            print(f"❌ 分享上报异常: {str(e)}")
            return False
    
    def submit_task_completion(self, task_id: int, task_url: str) -> bool:
        """提交任务完成状态（浏览和分享任务共用）"""
        try:
            headers = {
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
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get("code") == 1:
                    return True
                else:
                    phone_tail = self.get_phone_tail()
                    print(f"❌ 任务完成提交失败 ({phone_tail}): {result.get('msg', '未知错误')}")
            else:
                phone_tail = self.get_phone_tail()
                print(f"❌ 任务完成提交请求失败 ({phone_tail}): HTTP {response.status_code}")
            return False
            
        except Exception as e:
            phone_tail = self.get_phone_tail()
            print(f"❌ 任务完成提交异常 ({phone_tail}): {str(e)}")
            return False
    
    def receive_reward(self, task_id: int, task_name: str) -> bool:
        """领取任务奖励"""
        try:
            params = JiuxianConfig.DEVICE_INFO.copy()
            params["token"] = self.token
            params["appKey"] = JiuxianConfig.APP_KEY
            params["taskId"] = str(task_id)
            
            response = self.session.get(
                JiuxianConfig.RECEIVE_REWARD_URL,
                params=params,
                headers=JiuxianConfig.HEADERS,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get("success") == "1":
                    reward_data = result["result"]
                    gold_num = reward_data.get("goldNum", 0)
                    phone_tail = self.get_phone_tail()
                    print(f"🎉 任务 '{task_name}' 完成 ({phone_tail})，获得 {gold_num} 金币")
                    return True
                else:
                    phone_tail = self.get_phone_tail()
                    print(f"❌ 领取奖励失败 ({phone_tail}): {result.get('errMsg', '未知错误')}")
                    return False
            else:
                phone_tail = self.get_phone_tail()
                print(f"❌ 领取奖励请求失败 ({phone_tail}): HTTP {response.status_code}")
                return False
                
        except Exception as e:
            phone_tail = self.get_phone_tail()
            print(f"❌ 领取奖励异常 ({phone_tail}): {str(e)}")
            return False
    
    def run_all_tasks(self) -> Dict:
        """执行所有任务"""
        result = {
            "username": self.username,
            "phone_tail": self.get_phone_tail(),
            "nickname": self.nickname,
            "login_success": False,
            "login_type": "unknown",
            "check_in": {"success": False, "message": ""},
            "tasks": [],
            "member_info": {},
            "today_gold": 0,  # 今日获得金币
            "total_gold": 0   # 总金币数
        }
        
        # 智能登录
        login_success = self.smart_login()
        if login_success:
            result["login_success"] = True
            result["nickname"] = self.nickname
            if self.token and not self.username:
                result["login_type"] = "direct_token"
            else:
                result["login_type"] = "token" if hasattr(self, 'token') and self.token else "password"
        else:
            result["login_success"] = False
            return result
        
        # 获取会员信息（只获取一次！）
        member_info = self.get_member_info()
        if not member_info:
            return result
        
        result["member_info"] = {
            "gold_money": member_info.get("goldMoney", 0),
            "is_sign_today": member_info.get("isSignTody", False),
            "sign_days": member_info.get("signDays", 0),
            "user_rank": member_info.get("userRank", "")
        }
        result["total_gold"] = member_info.get("goldMoney", 0)
        
        # 确保taskToken已正确设置
        if not self.task_token:
            phone_tail = self.get_phone_tail()
            print(f"❌ 未获取到taskToken ({phone_tail})，无法执行任务")
            return result
        
        print(f"🔑 使用taskToken: {self.task_token}")
        
        # 处理签到（只有在未签到时才执行）
        if not member_info.get("isSignTody"):
            print("📅 执行签到...")
            check_in_success, check_in_msg = self.check_in()
            result["check_in"] = {"success": check_in_success, "message": check_in_msg}
            # 如果签到成功，从消息中提取金币数
            if check_in_success and "获得" in check_in_msg:
                try:
                    gold_str = check_in_msg.split("获得")[1].split("金币")[0]
                    result["today_gold"] += int(gold_str)
                except:
                    pass
            time.sleep(random.randint(2, 4))
        else:
            result["check_in"] = {"success": True, "message": "今日已签到"}
            print("📅 今日已签到，跳过签到")
        
        # 处理任务
        task_channel = member_info.get("taskChannel", {})
        task_list = task_channel.get("taskList", [])
        
        for task in task_list:
            task_result = {
                "id": task["id"],
                "name": task["taskName"],
                "type": task["taskType"],
                "state": task["state"],
                "gold_num": task.get("goldNum", 0),
                "completed": False
            }
            
            # state: 0-未完成, 1-已完成未领取, 2-已完成已领取
            if task["state"] == 0:  # 未完成的任务
                if task["taskType"] == 1:  # 浏览任务
                    task_result["completed"] = self.complete_browse_task(task)
                elif task["taskType"] == 2:  # 分享任务
                    task_result["completed"] = self.complete_share_task(task)
                
                # 如果任务完成，累加金币
                if task_result["completed"]:
                    result["today_gold"] += task_result["gold_num"]
            
            result["tasks"].append(task_result)
            
            # 任务间短暂间隔
            time.sleep(random.randint(2, 4))
        
        return result

def send_pushplus_notification(token: str, title: str, content: str) -> bool:
    """发送PushPlus推送通知"""
    try:
        if not token:
            print("❌ PushPlus Token未设置，跳过推送")
            return False
            
        url = "https://www.pushplus.plus/send"
        data = {
            "token": token,
            "title": title,
            "content": content,
            "template": "markdown"
        }
        
        response = requests.post(url, json=data, timeout=30)
        if response.status_code == 200:
            result = response.json()
            if result.get("code") == 200:
                print("✅ PushPlus推送发送成功")
                return True
            else:
                print(f"❌ PushPlus推送失败: {result.get('msg', '未知错误')}")
                return False
        else:
            print(f"❌ PushPlus推送请求失败: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ PushPlus推送异常: {str(e)}")
        return False

def generate_markdown_report(all_results: List[Dict]) -> str:
    """生成Markdown格式的报告"""
    # 统计信息
    total_users = len(all_results)
    success_login_count = sum(1 for r in all_results if r["login_success"])
    success_checkin_count = sum(1 for r in all_results if r.get("check_in", {}).get("success", False))
    total_today_gold = sum(r.get("today_gold", 0) for r in all_results)
    total_gold = sum(r.get("total_gold", 0) for r in all_results)
    
    # 构建Markdown内容
    content = f"""# 🍷 酒仙网任务执行报告

## 📊 统计概览

| 项目 | 数值 |
|------|------|
| 👥 用户总数 | {total_users} |
| ✅ 登录成功 | {success_login_count} |
| 📅 签到成功 | {success_checkin_count} |
| 🎯 今日获得金币 | {total_today_gold} |
| 💰 总金币数 | {total_gold} |

## 👤 用户详情

| 手机尾号 | 签到状态 | 任务状态 | 今日金币 | 总金币 |
|----------|----------|----------|----------|--------|
"""
    
    # 添加每个用户的详情
    for result in all_results:
        phone_tail = result.get("phone_tail", "****")
        nickname = result.get("nickname", "未知用户")
        
        # 签到状态
        check_in = result.get("check_in", {})
        if check_in.get("success"):
            sign_status = "✅ 成功"
        else:
            sign_status = "❌ 失败"
        
        # 任务状态
        tasks = result.get("tasks", [])
        completed_tasks = sum(1 for t in tasks if t.get("completed", False))
        total_tasks = len(tasks)
        task_status = f"{completed_tasks}/{total_tasks}"
        
        # 金币信息
        today_gold = result.get("today_gold", 0)
        total_gold_user = result.get("total_gold", 0)
        
        content += f"| {phone_tail} ({nickname}) | {sign_status} | {task_status} | {today_gold} | {total_gold_user} |\n"
    
    # 添加执行时间
    exec_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    content += f"\n---\n**🕐 执行时间**: {exec_time}\n"
    
    return content

def main():
    """主函数"""
    # 获取环境变量
    accounts_str = os.getenv("jiuxian", "")
    tokens_str = os.getenv("JX_TOKENS", "")
    pushplus_token = os.getenv("PUSHPLUS_TOKEN", "")
    
    if not accounts_str and not tokens_str:
        print("❌ 未找到账号配置，请检查环境变量 jiuxian 或 JX_TOKENS")
        return
    
    all_accounts = []
    
    # 解析账号密码
    if accounts_str:
        for line in accounts_str.strip().split('\n'):
            if '#' in line:
                username, password = line.split('#', 1)
                all_accounts.append(("account", username.strip(), password.strip()))
    
    # 解析Token
    if tokens_str:
        for line in tokens_str.strip().split('\n'):
            token = line.strip()
            if token:
                all_accounts.append(("token", None, token))
    
    if not all_accounts:
        print("❌ 未找到有效的账号配置")
        return
    
    print(f"🔍 找到 {len(all_accounts)} 个账号配置，开始执行任务...")
    
    all_results = []
    
    # 遍历所有账号执行任务
    for i, (account_type, username, credential) in enumerate(all_accounts, 1):
        print(f"\n{'='*50}")
        phone_tail = "****" if not username else f"******{username[-4:]}" if len(username) >= 4 else "****"
        print(f"🔄 开始处理账号 {i}: {phone_tail}")
        
        if account_type == "account":
            jiuxian = Jiuxian(username=username, password=credential)
        else:
            jiuxian = Jiuxian(token=credential)
            
        result = jiuxian.run_all_tasks()
        all_results.append(result)
        
        print(f"✅ 账号 {i} 处理完成")
        time.sleep(random.randint(3, 5))  # 账号间间隔
    
    # 生成简单报告
    print("\n" + "="*50)
    print("📋 任务执行完成报告:")
    success_count = sum(1 for r in all_results if r["login_success"])
    print(f"✅ 成功执行: {success_count}/{len(all_accounts)} 个账号")
    
    for i, result in enumerate(all_results, 1):
        if result["login_success"]:
            completed_tasks = sum(1 for t in result["tasks"] if t["completed"])
            total_tasks = len(result["tasks"])
            login_type = result.get('login_type', 'unknown')
            phone_tail = result.get('phone_tail', '****')
            print(f"账号 {i}: {result['nickname']} ({phone_tail}) - 完成任务: {completed_tasks}/{total_tasks}")

    # 发送PushPlus推送
    if pushplus_token:
        print("\n📤 正在发送PushPlus推送通知...")
        markdown_content = generate_markdown_report(all_results)
        title = f"🍷 酒仙网任务报告 - {success_count}/{len(all_accounts)}成功"
        send_pushplus_notification(pushplus_token, title, markdown_content)
    else:
        print("\n⚠️ 未设置PUSHPLUS_TOKEN环境变量，跳过推送")

if __name__ == "__main__":
    main()