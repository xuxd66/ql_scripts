#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""

联通账号密码登录脚本
通过账号密码登录，输出账号对应的信息到UNICOM_ACCOUNTS（自动化添加）

【原作者信息】
yaohuo：新人
ID: 12996

【修改】
yaohuo：来姑娘坐我鞭上
ID: 38445

【青龙环境变量配置说明】
1. 账号密码配置（二选一即可）：
   - 变量名：UNICOM_ACCOUNTS_OLD
     格式：手机号1#密码1@手机号2#密码2（多个账号用@分隔）
     示例：13012345678#abc123456@13187654321#def654321
   - 变量名：UNICOM_ACCOUNTS_PWD
     格式：手机号#密码（单个账号）
     示例：13012345678#abc123456

【脚本内配置说明】
- OUTPUT_TYPE：1 → 存储格式：手机号#ecs_token；
               2 → 存储格式：手机号#token_online#appid
               
"""

import os
import json
import time
import random
import base64
import requests
import hashlib
from datetime import datetime
from sys import stdout
# 关键：将Crypto导入移到顶部，解决RSA未定义问题
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_v1_5

# ====================== 脚本内配置项（核心修改）======================
# 配置输出类型：1 = 账号#ecs_token；2 = 账号#token_online#appid
OUTPUT_TYPE = 2  # 可直接修改这里的数字切换格式

def print_now(msg):
    print(msg)
    stdout.flush()

#-----------------------------------------
# 变量获取
#-----------------------------------------
def get_env_value(name):
    """获取环境变量值"""
    value = os.environ.get(name)
    if value:
        return value
    return None

# =====================================================================
# RSA 加密类（适配账号密码登录）
# =====================================================================
class RSAEncrypt:
    def __init__(self):
        self.public_key = """-----BEGIN PUBLIC KEY-----
MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQDc+CZK9bBA9IU+gZUOc6FUGu7y
O9WpTNB0PzmgFBh96Mg1WrovD1oqZ+eIF4LjvxKXGOdI79JRdve9NPhQo07+uqGQ
gE4imwNnRx7PFtCRryiIEcUoavuNtuRVoBAm6qdB0SrctgaqGfLgKvZHOnwTjyNq
jBUxzMeQlEC2czEMSwIDAQAB
-----END PUBLIC KEY-----"""
        
        self.max_block_size = 117
    
    def encrypt(self, plaintext, is_password=False):
        """RSA加密"""
        try:
            if is_password:
                plaintext = plaintext + "000000"
                print_now(f"🔑 密码处理：添加后缀000000，原始内容：{plaintext[:-6]}，处理后：{plaintext}")
            
            raw = plaintext.encode('utf-8')
            pubkey = RSA.import_key(self.public_key)
            cipher = PKCS1_v1_5.new(pubkey)
            
            result = []
            print_now(f"🔐 开始RSA分块加密，内容长度：{len(raw)}，最大块大小：{self.max_block_size}")
            for i in range(0, len(raw), self.max_block_size):
                block = raw[i:i + self.max_block_size]
                encrypted_block = cipher.encrypt(block)
                result.append(encrypted_block)
                print_now(f"   加密块 {i//self.max_block_size + 1}：长度 {len(block)} → {len(encrypted_block)}")
            
            encrypted = b"".join(result)
            b64_encrypted = base64.b64encode(encrypted).decode('utf-8')
            print_now(f"✅ RSA加密完成，加密后内容（前50位）：{b64_encrypted[:50]}...")
            return b64_encrypted, None
            
        except Exception as e:
            error_msg = f"RSA加密失败：{str(e)}"
            print_now(f"❌ {error_msg}")
            return "", error_msg

# =====================================================================
# 联通账号密码登录类
# =====================================================================
class UnicomPwdLogin:
    def __init__(self, phone, password):
        self.phone = phone
        self.password = password
        self.token_online = ""
        self.ecs_token = ""
        self.appid = ""
        self.device_id = ""
        self.error_msg = ""
        
        print_now(f"\n📱 初始化账号 {phone} 设备信息...")
        self.init_device_info()
        self.rsa = RSAEncrypt()
        print_now(f"✅ 设备信息初始化完成：")
        print_now(f"   Device ID：{self.device_id}")
        print_now(f"   AppID（前50位）：{self.appid[:50]}...")
    
    def init_device_info(self):
        """初始化设备信息"""
        self.appid = (
            f"{random.randint(0,9)}f{random.randint(0,9)}af"
            f"{random.randint(0,9)}{random.randint(0,9)}ad"
            f"{random.randint(0,9)}912d306b5053abf90c7ebbb695887bc"
            "870ae0706d573c348539c26c5c0a878641fcc0d3e90acb9be1e6ef858a"
            "59af546f3c826988332376b7d18c8ea2398ee3a9c3db947e2471d32a49612"
        )
        self.device_id = hashlib.md5(self.phone.encode()).hexdigest()
    
    def build_headers(self):
        """构建请求头"""
        app_version = "iphone_c@12.0200"
        device_os = "26.2"
        
        headers = {
            "Host": "m.client.10010.com",
            "Accept-Encoding": "gzip, deflate, br",
            "Content-Type": "application/x-www-form-urlencoded",
            "Connection": "keep-alive",
            "Accept": "*/*",
            "User-Agent": f"ChinaUnicom4.x/12.2 (com.chinaunicom.mobilebusiness; build:44; iOS {device_os}) Alamofire/4.7.3 unicom{{version:{app_version}}}",
            "Accept-Language": "zh-CN,zh-Hans;q=0.9",
        }
        return headers
    
    def build_payload(self):
        """构建请求参数"""
        print_now(f"\n📝 构建登录请求参数...")
        encrypted_mobile, mobile_error = self.rsa.encrypt(self.phone, is_password=False)
        if mobile_error:
            self.error_msg = mobile_error
            return None
        
        encrypted_password, pwd_error = self.rsa.encrypt(self.password, is_password=True)
        if pwd_error:
            self.error_msg = pwd_error
            return None
        
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        payload = {
            "voipToken": "citc-default-token-do-not-push",
            "deviceBrand": "iPhone",
            "simOperator": "--,%E4%B8%AD%E5%9B%BD%E7%A7%BB%E5%8A%A8,--,--,--",
            "deviceId": self.device_id,
            "netWay": "wifi",
            "deviceCode": self.device_id,
            "deviceOS": "26.2",
            "uniqueIdentifier": self.device_id,
            "latitude": "",
            "version": "iphone_c@12.0200",
            "pip": "10.98.155.187",
            "isFirstInstall": "1",
            "remark4": "",
            "keyVersion": "2",
            "longitude": "",
            "simCount": "1",
            "mobile": encrypted_mobile,
            "isRemberPwd": "false",
            "appId": self.appid,
            "reqtime": timestamp,
            "deviceModel": "iPhone18,1",
            "password": encrypted_password
        }
        print_now(f"✅ 请求参数构建完成，包含 {len(payload)} 个参数")
        return payload
    
    def login(self):
        """执行登录"""
        print_now(f"\n🚀 开始账号 {self.phone} 登录请求...")
        payload = self.build_payload()
        if not payload:
            return {
                "status": "failed",
                "msg": self.error_msg,
                "ecs_token": "",
                "token_online": "",
                "appid": "",
                "phone": self.phone
            }
        
        url = "https://m.client.10010.com/mobileService/login.htm"
        headers = self.build_headers()
        
        try:
            print_now(f"🌐 发送POST请求到：{url}")
            print_now(f"⌛ 设置超时时间：15秒")
            response = requests.post(
                url,
                data=payload,
                headers=headers,
                timeout=15
            )
            print_now(f"✅ 请求响应状态码：{response.status_code}")
            
            result = response.json()
            code = str(result.get("code", ""))
            
            if code in ["0", "0000"]:
                self.token_online = result.get("token_online", "")
                self.ecs_token = result.get("ecs_token", "")
                
                if self.token_online:
                    print_now(f"\n🎉 账号 {self.phone} 登录成功！")
                    print_now(f"   ecs_token（前50位）：{self.ecs_token[:50]}...")
                    print_now(f"   token_online（前50位）：{self.token_online[:50]}...")
                    print_now(f"   AppID：{self.appid[:50]}...")
                    return {
                        "status": "success",
                        "msg": "登录成功",
                        "ecs_token": self.ecs_token,
                        "token_online": self.token_online,
                        "appid": self.appid,
                        "phone": self.phone
                    }
                else:
                    self.error_msg = "登录成功但未获取到token_online"
                    print_now(f"\n⚠ 账号 {self.phone} {self.error_msg}")
                    return {
                        "status": "failed",
                        "msg": self.error_msg,
                        "ecs_token": "",
                        "token_online": "",
                        "appid": "",
                        "phone": self.phone
                    }
            
            elif code == "2":
                self.error_msg = "密码错误！请检查您的登录专用密码。"
                print_now(f"\n❌ 账号 {self.phone} {self.error_msg}")
                return {
                    "status": "failed",
                    "msg": self.error_msg,
                    "ecs_token": "",
                    "token_online": "",
                    "appid": "",
                    "phone": self.phone
                }
            
            elif code == "11":
                self.error_msg = "未设置登录专用密码！建议前往联通APP设置或重置登录专用密码。"
                print_now(f"\n❌ 账号 {self.phone} {self.error_msg}")
                return {
                    "status": "failed",
                    "msg": self.error_msg,
                    "ecs_token": "",
                    "token_online": "",
                    "appid": "",
                    "phone": self.phone
                }
            
            elif code == "ECS99999":
                self.error_msg = "触发安全风控 (ECS99999)，建议手动打开联通APP登录一次以解除风控。"
                print_now(f"\n🛡️ 账号 {self.phone} {self.error_msg}")
                return {
                    "status": "failed",
                    "msg": self.error_msg,
                    "ecs_token": "",
                    "token_online": "",
                    "appid": "",
                    "phone": self.phone
                }
            
            else:
                self.error_msg = f"登录失败: {result.get('desc', '未知错误')} (Code: {code})"
                print_now(f"\n❌ 账号 {self.phone} {self.error_msg}")
                return {
                    "status": "failed",
                    "msg": self.error_msg,
                    "ecs_token": "",
                    "token_online": "",
                    "appid": "",
                    "phone": self.phone
                }
                
        except Exception as e:
            self.error_msg = f"登录请求失败：{str(e)}"
            print_now(f"\n❌ 账号 {self.phone} {self.error_msg}")
            return {
                "status": "failed",
                "msg": self.error_msg,
                "ecs_token": "",
                "token_online": "",
                "appid": "",
                "phone": self.phone
            }

# =====================================================================
# 环境变量操作工具（适配青龙原生QLAPI）
# =====================================================================
def set_env_value(name, value, remarks=""):
    """更新环境变量"""
    res = QLAPI.getEnvs({"searchValue": name})
    for env in res.get("data", []):
        if env.get("name") == name:
            env["value"] = value
            env["remarks"] = remarks
            QLAPI.updateEnv({"env": env})
            tempget = get_env_valueBool(name)
            print_now(f"\n✅ 修改环境变量成功：{name}")
            return True
    return False

def get_env_valueBool(name):
    """检查环境变量是否存在"""
    res = QLAPI.getEnvs({"searchValue": name})
    return len(res.get("data", [])) > 0

def add_env_value(name, value, remarks=""):
    """新增环境变量"""
    QLAPI.createEnv({
        "envs": [
            {
                "name": name,
                "value": value,
                "remarks": remarks
            }
        ]
    })
    tempget = get_env_valueBool(name)
    print_now(f"\n✅ 新增环境变量成功：{name}")

def isAddEnvOrSet(name, value, remarks):
    """新增或更新环境变量"""
    print_now(f"\n📝 环境变量操作：")
    print_now(f"   变量名：{name}")
    print_now(f"   变量值（前100位）：{value[:100]}..." if len(value) > 100 else f"   变量值：{value}")
    print_now(f"   变量描述：{remarks}")
    if get_env_valueBool(name):
        set_env_value(name, value, remarks)
    else:
        add_env_value(name, value, remarks)
    return True

# =====================================================================
# 主程序
# =====================================================================
def parse_accounts():
    """解析账号密码配置"""
    accounts = []
    
    accounts_str = get_env_value("UNICOM_ACCOUNTS_OLD")
    if not accounts_str:
        accounts_str = get_env_value("UNICOM_ACCOUNTS_PWD")
    
    if not accounts_str:
        print_now("❌ 未找到账号密码配置")
        print_now("💡 请在青龙环境变量中设置:")
        print_now("   UNICOM_ACCOUNTS_OLD = 手机号1#密码1@手机号2#密码2")
        print_now("   或")
        print_now("   UNICOM_ACCOUNTS_PWD = 手机号#密码")
        return accounts
    
    print_now(f"\n📋 开始解析账号密码配置，原始配置：{accounts_str}")
    account_list = accounts_str.split('@')
    print_now(f"🔢 分割出 {len(account_list)} 个账号项，开始验证格式...")
    
    for idx, item in enumerate(account_list):
        item = item.strip()
        if not item:
            print_now(f"⚠ 第 {idx+1} 个账号项为空，跳过")
            continue
        
        if '#' in item:
            parts = item.split('#')
            if len(parts) >= 2:
                phone = parts[0].strip()
                password = parts[1].strip()
                
                if phone and phone.isdigit() and len(phone) == 11:
                    accounts.append({
                        "phone": phone,
                        "password": password
                    })
                    print_now(f"✅ 第 {idx+1} 个账号项验证通过：{phone}")
                else:
                    print_now(f"⚠ 第 {idx+1} 个账号项手机号无效：{phone}，跳过")
            else:
                print_now(f"⚠ 第 {idx+1} 个账号项格式错误（缺少#）：{item}，跳过")
        else:
            print_now(f"⚠ 第 {idx+1} 个账号项格式错误（无#）：{item}，跳过")
    
    print_now(f"\n✅ 账号解析完成，共获取 {len(accounts)} 个有效账号")
    return accounts

def check_dependencies():
    """检查依赖（保留该函数，用于验证包是否安装）"""
    print_now("🔍 开始检查脚本依赖包...")
    try:
        # 验证包存在即可，无需重复导入
        import Crypto
        print_now("✅ 依赖包检查通过：pycryptodome 已安装")
        return True
    except ImportError:
        print_now("❌ 缺少依赖包：pycryptodome")
        print_now("📦 安装命令: pip3 install pycryptodome")
        return False

def main():
    print_now("🚀 联通账号密码登录脚本启动（支持脚本内配置输出格式版本）")
    print_now(f"📅 当前时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print_now(f"⚙️ 当前输出配置类型：{OUTPUT_TYPE}（1=账号#ecs_token，2=账号#token_online#appid）")
    print_now("=" * 60)
    
    if not check_dependencies():
        return
    
    print_now("\n🔧 开始解析青龙环境变量中的账号密码配置...")
    accounts = parse_accounts()
    if not accounts:
        print_now("\n🚫 无有效账号，脚本终止执行")
        return
    
    print_now(f"\n📱 本次需处理 {len(accounts)} 个账号，开始逐个处理...")
    print_now("=" * 60)
    
    account_results = []
    # 新增：统一存储最终要写入环境变量的内容
    unicom_accounts_list = []
    
    success_count = 0
    fail_count = 0
    for idx, account in enumerate(accounts):
        phone = account["phone"]
        password = account["password"]
        
        print_now("\n" + "="*60)
        print_now(f"▶ 处理账号 {idx+1}/{len(accounts)}: {phone}")
        print_now("="*60)
        
        try:
            login = UnicomPwdLogin(phone, password)
            login_result = login.login()
            account_results.append(login_result)
            
            if login_result["status"] == "success":
                success_count += 1
                # 根据配置类型添加对应格式的内容
                if OUTPUT_TYPE == 1:
                    unicom_accounts_list.append(f"{phone}#{login_result['ecs_token']}")
                elif OUTPUT_TYPE == 2:
                    unicom_accounts_list.append(f"{phone}#{login_result['token_online']}#{login_result['appid']}")
            else:
                fail_count += 1
                
        except Exception as e:
            error_msg = f"执行异常：{str(e)}"
            fail_count += 1
            error_result = {
                "status": "failed",
                "msg": error_msg,
                "ecs_token": "",
                "token_online": "",
                "appid": "",
                "phone": phone
            }
            account_results.append(error_result)
            print_now(f"\n❌ 账号 {phone} {error_msg}")
        
        if idx < len(accounts) - 1:
            wait_time = random.randint(3, 7)
            print_now(f"\n⏳ 等待 {wait_time} 秒后处理下一个账号...")
            time.sleep(wait_time)
    
    # 核心修改：将对应格式的结果拼接后写入UNICOM_ACCOUNTS
    if unicom_accounts_list:
        unicom_accounts_value = "\n".join(unicom_accounts_list)
        # 根据配置类型设置备注
        if OUTPUT_TYPE == 1:
            remarks = "联通：手机号#ecs_token"
        else:
            remarks = "联通：手机号#token_online#appid"
        isAddEnvOrSet("UNICOM_ACCOUNTS", unicom_accounts_value, remarks)
    
    # 执行结果汇总
    print_now("\n" + "="*60)
    print_now("📊 执行结果汇总")
    print_now("="*60)
    print_now(f"📱 总账号数: {len(accounts)}")
    print_now(f"✅ 成功登录: {success_count}")
    print_now(f"❌ 登录失败: {fail_count}")
    
    # 账号信息展示（保留两种格式的展示）
    print_now("\n" + "="*60)
    print_now("📋 账号关键信息汇总")
    print_now("="*60)
    print_now("1. 账号#ecs_token 格式：")
    for res in account_results:
        phone = res["phone"]
        if res["status"] == "success" and res["ecs_token"]:
            print_now(f"   {phone}#{res['ecs_token']}")
        else:
            print_now(f"   {phone}#失败（原因：{res['msg']}）")
    
    print_now("\n2. 账号#token_online#appid 格式：")
    for res in account_results:
        phone = res["phone"]
        if res["status"] == "success" and res["token_online"] and res["appid"]:
            print_now(f"   {phone}#{res['token_online']}#{res['appid']}")
        else:
            print_now(f"   {phone}#失败（原因：{res['msg']}）")
    print_now("\n🎉 无需复制 全程自动化")
    print_now("\n🎉 脚本执行完成,请到环境变量中查看！")

if __name__ == "__main__":
    main()