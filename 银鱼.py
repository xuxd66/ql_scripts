#环境变量API_PROXY，值：过检ip:5000
import os
import requests
import json
import time
from requests.exceptions import RequestException

# ========================== 第一部分：CK获取功能 ==========================

# 配置区
LOCAL_PROXY = "http://" + os.getenv("API_PROXY")  # 过检软件API地址
TARGET_APP_ID = "wx5b82dfe3747e533f"  # 目标小程序的APP_ID
LOGIN_URL_TEMPLATE = "https://n05.sentezhenxuan.com/api/v2/routine/silenceAuth?code={wxCode}&spread_spid=1295646&spread_code=0"
CK_FILE = "ikun_yyck.json"  # CK存储文件名

# 请求头
REQUEST_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36 MicroMessenger/7.0.20.1781(0x6700143B) NetType/WIFI MiniProgramEnv/Windows WindowsWechat/WMPF WindowsWechat(0x63090a13) UnifiedPCWindowsWechat(0x6254051a) XWEB/16019",
    "xweb_xhr": "1",
    "Form-type": "routine-zhixiang",
    "Content-Type": "application/json",
    "Referer": "https://servicewechat.com/wx5b82dfe3747e533f/6/page-frame.html",
    "Accept": "*/*",
    "Sec-Fetch-Site": "cross-site",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Dest": "empty",
    "Accept-Encoding": "gzip, deflate, br",
    "Accept-Language": "zh-CN,zh;q=0.9"
}

# 验证CK有效性的请求头
VALIDATE_HEADERS = {
    "Host": "n05.sentezhenxuan.com",
    "Connection": "keep-alive",
    "Cb-lang": "zh-CN",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36 MicroMessenger/7.0.20.1781(0x6700143B) NetType/WIFI MiniProgramEnv/Windows WindowsWechat/WMPF WindowsWechat(0x63090a13) UnifiedPCWindowsWechat(0xf254051a) XWEB/16019",
    "xweb_xhr": "1",
    "Form-type": "routine-zhixiang",
    "Content-Type": "application/json",
    "Accept": "*/*",
    "Sec-Fetch-Site": "cross-site",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Dest": "empty",
    "Referer": "https://servicewechat.com/wx5b82dfe3747e533f/6/page-frame.html",
    "Accept-Encoding": "gzip, deflate, br",
    "Accept-Language": "zh-CN,zh;q=0.9"
}

def get_wx_list():
    """获取微信账户列表"""
    try:
        url = f"{LOCAL_PROXY}/getallwx"
        response = requests.get(url, timeout=10)
        return response.json() if response.status_code == 200 else []
    except Exception as e:
        print(f"获取微信列表失败: {str(e)}")
        return []

def get_wx_code(wxid):
    """获取小程序登录凭证"""
    try:
        url = f"{LOCAL_PROXY}/loginbyapp?Wxid={wxid}&appid={TARGET_APP_ID}"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            return response.json().get("code")
        print(f"获取wxCode失败: HTTP {response.status_code}")
    except Exception as e:
        print(f"wxCode请求异常: {str(e)}")
    return None

def get_ck(wx_code):
    """获取小程序登录凭证(CK)"""
    login_url = LOGIN_URL_TEMPLATE.format(wxCode=wx_code)
    
    try:
        response = requests.get(login_url, headers=REQUEST_HEADERS, timeout=15)
        if response.status_code == 200:
            res_data = response.json()
            token = res_data.get('data', {}).get('token') or res_data.get('token')
            if token:
                return f"Bearer {token}"
            print("Token提取失败! 响应结构:", json.dumps(res_data, indent=2)[:300])
        else:
            print(f"登录失败: HTTP {response.status_code} | 响应: {response.text[:200]}")
    except Exception as e:
        print(f"登录请求异常: {str(e)}")
    return None

def validate_ck(ck):
    """验证CK有效性 - 根据抓包数据更新"""
    url = "https://n05.sentezhenxuan.com/api/user"
    headers = VALIDATE_HEADERS.copy()
    headers["Authori-zation"] = ck
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == 200:
                return True
        return False
    except Exception:
        return False

def load_ck_from_file():
    """从文件加载CK并验证有效性，返回有效CK列表和失效账号列表"""
    valid_results = []
    expired_accounts = []
    
    if not os.path.exists(CK_FILE):
        return valid_results, expired_accounts, set()
    
    try:
        with open(CK_FILE, "r") as f:
            ck_results = json.load(f)
            # 验证CK有效性
            for acc in ck_results:
                if validate_ck(acc["ck"]):
                    valid_results.append(acc)
                else:
                    print(f"❌ CK已失效: {acc['wxname']}")
                    expired_accounts.append(acc)
        
        if valid_results:
            print(f"✅ 从文件加载 {len(valid_results)} 个有效CK")
        if expired_accounts:
            print(f"⚠️ 检测到 {len(expired_accounts)} 个失效CK")
            
        # 返回现有wxid集合用于检测新账号
        existing_wxids = {acc["wxid"] for acc in ck_results}
        return valid_results, expired_accounts, existing_wxids
    except Exception as e:
        print(f"加载CK文件失败: {str(e)}")
        return [], [], set()

def save_ck_to_file(ck_results):
    """保存CK到文件"""
    try:
        with open(CK_FILE, "w") as f:
            json.dump(ck_results, f, indent=2)
        print(f"💾 成功保存 {len(ck_results)} 个CK到 {CK_FILE}")
    except Exception as e:
        print(f"保存CK文件失败: {str(e)}")

def fetch_ck(wx_accounts):
    """
    获取指定微信账号的CK
    :param wx_accounts: 需要获取CK的微信账号列表
    :return: 新获取的CK列表
    """
    if not wx_accounts:
        print("❌ 未提供微信账户列表")
        return []
    
    print(f"✅ 准备获取 {len(wx_accounts)} 个微信账户的CK")
    
    ck_results = []
    for account in wx_accounts:
        wxid = account.get("Wxid")
        wxname = account.get("wxname", "未知账户")
        print(f"\n🔍 处理账户: {wxname}({wxid})")
        
        wx_code = get_wx_code(wxid)
        if not wx_code:
            print("❌ 获取wxCode失败")
            continue
        
        print(f"🔑 获取到wxCode: {wx_code[:8]}****")
        
        ck = get_ck(wx_code)
        if ck:
            print(f"🔐 获取CK成功: {ck[:23]}****")
            ck_results.append({
                "wxid": wxid,
                "wxname": wxname,
                "ck": ck
            })
        else:
            print("❌ 获取CK失败")
    
    if not ck_results:
        print("\n❌ 未获取到有效CK")
        return []
    
    return ck_results

def merge_ck_lists(original_list, new_list):
    """
    合并新旧CK列表
    :param original_list: 原始有效CK列表
    :param new_list: 新获取的CK列表
    :return: 合并后的CK列表
    """
    # 创建wxid到账号的映射
    account_map = {acc["wxid"]: acc for acc in original_list}
    
    # 更新或添加新CK
    for new_acc in new_list:
        account_map[new_acc["wxid"]] = new_acc
    
    return list(account_map.values())

def detect_new_accounts(current_wx_list, existing_wxids):
    """
    检测新的微信账号
    :param current_wx_list: 当前微信账号列表
    :param existing_wxids: 已有CK中的wxid集合
    :return: 新账号列表
    """
    new_accounts = []
    for account in current_wx_list:
        wxid = account.get("Wxid")
        if wxid not in existing_wxids:
            new_accounts.append(account)
    
    return new_accounts

# ========================== 第二部分：银鱼功能 ==========================

class EnvWrapper:
    """环境兼容类"""
    def __init__(self, name):
        self.name = name
    
    def isNode(self):
        """检查是否在Node环境中"""
        return True
    
    def wait(self, ms):
        """等待指定毫秒数"""
        time.sleep(ms / 1000.0)
    
    def get(self, url, headers):
        """发送GET请求"""
        try:
            response = requests.get(url, headers=headers, timeout=15)
            return response.text
        except Exception as e:
            print(f"GET请求失败: {str(e)}")
            return ""
    
    def post(self, url, headers, body):
        """发送POST请求"""
        try:
            response = requests.post(url, headers=headers, data=body, timeout=15)
            return response.text
        except Exception as e:
            print(f"POST请求失败: {str(e)}")
            return ""
    
    def done(self):
        """完成函数（占位）"""
        pass

def safe_json_parse(str_data):
    """安全解析JSON"""
    try:
        return json.loads(str_data)
    except:
        return None

def run_silverfish(ck_results):
    """执行银鱼功能"""
    if not ck_results:
        print("❌ 没有有效的CK可执行银鱼功能")
        return
    
    print("\n" + "="*50)
    print("🚀 开始执行")
    print("="*50)
    
    # 配置参数
    config = {
        "onlyWithdraw": False,   # true = 只提现, false = 先刷视频再提现
        "notify": False,          # 是否发送通知（在Python中暂不实现）
        "delay": 1500,           # 请求间隔时间(毫秒)
        "watchDuration": 80000,  # 模拟观看时长(毫秒)
        "baseVersion": "3.8.9"   # 更新为最新版本号
    }
    
    # 全局统计
    stats = {
        "totalAccounts": 0,
        "processedAccounts": 0,
        "successWithdraw": 0,
        "alreadyWithdraw": 0,
        "failedWithdraw": 0,
        "watchedVideos": 0
    }
    
    # 初始化环境
    env = EnvWrapper("🎬 银鱼质亨")
    
    # 构造账户列表
    accounts = [f"{acc['wxname']}#{acc['ck']}" for acc in ck_results]
    stats["totalAccounts"] = len(accounts)
    
    if not accounts:
        print("❌ 未找到有效的账号信息")
        return
    
    print(f"\n🎉 共找到 {len(accounts)} 个账号")
    
    for i, account in enumerate(accounts):
        account = account.strip()
        if not account: continue
        
        parts = account.split('#')
        remark = parts[0].strip() if len(parts) > 0 else ""
        auth = parts[1].strip() if len(parts) > 1 else ""
        account_name = remark or f"账号 {i + 1}"
        
        print(f"\n📌 ━━━━━━━━━━━━━ 开始处理 {account_name} ━━━━━━━━━━━━━")
        try:
            process_account(env, auth, account_name, config, stats)
            stats["processedAccounts"] += 1
        except Exception as e:
            print(f"❌ 处理账号 {account_name} 时出错: {str(e)}")
        
        # 账号间间隔
        if i < len(accounts) - 1:
            env.wait(2000)
    
    # 生成统计报告
    report = [
        '✅ 所有账号处理完成',
        '📊 统计报告:',
        f'├─ 总账号数: {stats["totalAccounts"]}',
        f'├─ 已处理账号: {stats["processedAccounts"]}',
        f'├─ 成功提现: {stats["successWithdraw"]}',
        f'├─ 今日已提现: {stats["alreadyWithdraw"]}',
        f'├─ 提现失败: {stats["failedWithdraw"]}',
        f'└─ 刷视频数: {stats["watchedVideos"]}'
    ]
    
    print("\n" + "\n".join(report))
    print("\n" + "="*50)
    print("✅ 银鱼执行完毕")
    print("="*50)

def process_account(env, auth, account_name, config, stats):
    """处理单个账号"""
    if config["onlyWithdraw"]:
        print('ℹ️ 只提现模式已启用，跳过刷视频步骤')
        do_withdraw(env, auth, account_name, stats)
    else:
        video_ids = get_video_ids(env, auth, account_name)
        if video_ids:
            print(f'📽️ 获取到 {len(video_ids)} 个视频ID，准备刷视频...')
            watch_videos(env, video_ids, auth, account_name, config, stats)
            stats["watchedVideos"] += len(video_ids)
        else:
            print('⚠️ 无视频可刷，跳过刷视频步骤')
        do_withdraw(env, auth, account_name, stats)

def get_video_ids(env, auth, account_name):
    """获取视频ID列表"""
    url = 'https://n05.sentezhenxuan.com/api/video/list?page=1&limit=10&status=1&source=0&isXn=1'
    headers = get_base_headers(auth)
    
    try:
        print(f'🔍 {account_name} 正在获取视频列表...')
        response = env.get(url, headers)
        data = safe_json_parse(response)
        
        if not data:
            print(f'⚠️ {account_name} 无效的JSON响应')
            return []
        
        if data.get('status') != 200 or not isinstance(data.get('data'), list):
            print(f'⚠️ {account_name} 获取视频列表失败: {data.get("msg", "未知错误")}')
            return []
        
        return [item['id'] for item in data['data'] if isinstance(item.get('id'), int)]
    except Exception as e:
        print(f'⚠️ {account_name} 获取视频列表异常: {str(e)}')
        return []

def watch_videos(env, video_ids, auth, account_name, config, stats):
    """刷视频"""
    total = len(video_ids)
    for i, vid in enumerate(video_ids):
        now = int(time.time() * 1000)
        body = json.dumps({
            "vid": vid,
            "startTime": now - config["watchDuration"],
            "endTime": now,
            "baseVersion": config["baseVersion"],
            "playMode": 0,
        })
        
        url = 'https://n05.sentezhenxuan.com/api/video/videoJob'
        headers = get_base_headers(auth)
        
        try:
            response = env.post(url, headers, body)
            data = safe_json_parse(response)
            
            if data and data.get('status') == 200:
                print(f'🎥 {account_name} 视频 {i + 1}/{total} 刷完 (ID: {vid})')
            else:
                msg = data.get('msg') if data else '无返回数据'
                print(f'⚠️ {account_name} 视频 {i + 1}/{total} 返回异常: {msg}')
        except Exception as e:
            print(f'⚠️ {account_name} 视频 {i + 1}/{total} 请求失败: {str(e)}')
        
        # 请求间间隔
        if i < total - 1:
            env.wait(config["delay"])

def do_withdraw(env, auth, account_name, stats):
    """提现操作"""
    url = 'https://n05.sentezhenxuan.com/api/userTx'
    headers = get_withdraw_headers(auth)
    
    try:
        print(f'💳 {account_name} 正在尝试提现...')
        response = env.get(url, headers)
        data = safe_json_parse(response)
        
        if not data:
            raise Exception('无效的JSON响应')
        
        if data.get('code') == 200 or data.get('status') == 200:
            print(f'💰 {account_name} 提现成功: {data.get("msg", "成功")}')
            stats["successWithdraw"] += 1
        elif '每天只可提现1次' in data.get('msg', ''):
            print(f'💰 {account_name} 今日已提现过')
            stats["alreadyWithdraw"] += 1
        else:
            msg = data.get('msg', '提现失败: 未知错误')
            print(f'❌ {account_name} {msg}')
            stats["failedWithdraw"] += 1
    except Exception as e:
        if '每天只可提现1次' in str(e):
            print(f'💰 {account_name} 今日已提现过')
            stats["alreadyWithdraw"] += 1
        else:
            print(f'❌ {account_name} 提现异常: {str(e)}')
            stats["failedWithdraw"] += 1

def get_base_headers(auth):
    """获取基础headers"""
    return {
        "Accept": "application/json",
        "Accept-Encoding": "gzip, deflate, br",
        "Content-Type": "application/json",
        "Connection": "keep-alive",
        "Referer": "https://servicewechat.com/wx5b82dfe3747e533f/5/page-frame.html",
        "Host": "n05.sentezhenxuan.com",
        "Authori-zation": auth,
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 15_4_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 MicroMessenger/8.0.50 NetType/WIFI Language/zh_CN",
        "Cb-lang": "zh-CN",
        "Form-type": "routine-zhixiang",
        "xweb_xhr": "1"
    }

def get_withdraw_headers(auth):
    """获取提现headers"""
    return {
        "Accept": "application/json",
        "Accept-Language": "zh-CN,zh;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Content-Type": "application/json",
        "Referer": "https://servicewechat.com/wx5b82dfe3747e533f/5/page-frame.html",
        "Host": "n05.sentezhenxuan.com",
        "Authori-zation": auth,
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 15_4_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 MicroMessenger/8.0.50(0x1800323d) NetType/WIFI Language/zh_CN",
        "Cb-lang": "zh-CN",
        "Form-type": "routine-zhixiang",
        "xweb_xhr": "1"
    }

# ========================== 主程序 ==========================

def main():
    print("="*50)
    print("🚀 银鱼")
    print("="*50)
    
    # 第一步：尝试加载已有的CK并验证有效性
    valid_ck_list, expired_accounts, existing_wxids = load_ck_from_file()
    
    # 第二步：获取当前微信账户列表
    print("\n🔄 正在获取当前微信账户列表...")
    current_wx_list = get_wx_list()
    
    if not current_wx_list:
        print("❌ 未获取到微信账户列表")
        return
    
    print(f"✅ 获取到 {len(current_wx_list)} 个微信账户")
    
    # 第三步：检测新账号
    new_accounts = detect_new_accounts(current_wx_list, existing_wxids)
    if new_accounts:
        print(f"🎉 检测到 {len(new_accounts)} 个新账号:")
        for acc in new_accounts:
            print(f"  - {acc.get('wxname', '未知账号')} ({acc.get('Wxid')})")
        
        # 获取新账号的CK
        new_ck_list = fetch_ck(new_accounts)
        if new_ck_list:
            # 合并新账号到有效列表
            merged_ck_list = merge_ck_lists(valid_ck_list, new_ck_list)
            valid_ck_list = merged_ck_list
            print(f"✅ 成功添加 {len(new_ck_list)} 个新账号的CK")
        else:
            print("❌ 未能获取新账号的CK")
    
    # 第四步：更新失效账号
    if expired_accounts:
        print("\n⚠️ 检测到失效CK，开始更新...")
        # 构建需要更新的账号列表（仅限当前存在的账号）
        update_accounts = []
        for expired in expired_accounts:
            # 查找当前微信列表中是否存在此wxid
            for wx_acc in current_wx_list:
                if wx_acc.get("Wxid") == expired["wxid"]:
                    update_accounts.append(wx_acc)
                    break
        
        if update_accounts:
            updated_ck_list = fetch_ck(update_accounts)
            if updated_ck_list:
                # 合并更新后的CK
                merged_ck_list = merge_ck_lists(valid_ck_list, updated_ck_list)
                valid_ck_list = merged_ck_list
                print(f"🔄 成功更新 {len(updated_ck_list)} 个失效账号的CK")
            else:
                print("❌ 未能更新失效账号的CK")
        else:
            print("⚠️ 失效账号已不在当前微信列表中，跳过更新")
    
    # 第五步：保存所有CK到文件
    if valid_ck_list:
        save_ck_to_file(valid_ck_list)
    else:
        # 如果没有有效CK，尝试获取所有账号的CK
        print("\n❌ 没有有效的CK，尝试获取所有账号的CK...")
        all_ck_list = fetch_ck(current_wx_list)
        if all_ck_list:
            save_ck_to_file(all_ck_list)
            valid_ck_list = all_ck_list
        else:
            print("❌ 未能获取任何CK，程序终止")
            return
    
    # 第六步：执行银鱼
    if valid_ck_list:
        run_silverfish(valid_ck_list)
    else:
        print("❌ 没有有效的CK可用，程序终止")

if __name__ == "__main__":
    main()