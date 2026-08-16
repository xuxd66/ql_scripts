import requests
import time
import os
import random
from requests.exceptions import RequestException

# ==============================================================================
# 【环境变量QH配置说明（无token，隐藏wid展示）】
# 1. 格式：
#    - 单账号：直接填写wid（例：123456）
#    - 多账号：支持两种分隔方式，可混合使用
#      - &分隔：123&456&789
#      - 换行分隔：每个wid单独占一行（Windows/Linux换行符均兼容）
# 2. 关键：脚本仅内部使用wid登录，所有输出不显示wid；UA由脚本自动随机生成（小程序ID固定）
'''
不用抓包，直接登录小程序。
个人中心---用户设置---用户编号就是需要的wid信息
'''
# ==============================================================================

# -------------------------- 【配置+工具函数（隐藏wid输出）】--------------------------
def generate_random_ua():
    """生成随机UA（基于iPhone微信小程序模板，小程序ID wx532ecb3bdaaf92f9固定不变）"""
    # iPhone OS版本与对应Mobile版本映射（可按需扩展）
    os_mobile_map = [
        ("15_8_3", "15E148"),
        ("16_2_0", "16F203"),
        ("16_5_1", "16H62"),
        ("17_0_3", "17A5844a"),
        ("17_1_1", "17B100"),
        ("17_2_0", "17C304"),
        ("17_3_1", "17D50"),
        ("17_4_1", "17E262")
    ]
    # 随机选择OS与Mobile版本
    os_version, mobile_version = random.choice(os_mobile_map)
    # 随机生成微信版本（8.0.50 ~ 8.0.75范围）
    wechat_version = f"8.0.{random.randint(50, 75)}"
    # 拼接UA字符串
    return (
        f"Mozilla/5.0 (iPhone; CPU iPhone OS {os_version} like Mac OS X) "
        "AppleWebKit/605.1.15 (KHTML, like Gecko) "
        f"Mobile/{mobile_version} MicroMessenger/{wechat_version} "
        "NetType/WIFI Language/zh_CN miniProgram/wx532ecb3bdaaf92f9"
    )

def parse_qh_env():
    """解析QH环境变量（支持&和换行分隔多账号，自动生成UA）"""
    qh_env = os.getenv("QH", "")
    if not qh_env:
        print("❌ 错误：未检测到环境变量QH，请按配置说明设置！")
        return None
    
    # 统一分隔符：将所有换行符（\r\n、\n）替换为&，再拆分账号
    unified_env = qh_env.replace("\r\n", "&").replace("\n", "&")
    account_str_list = unified_env.split("&")
    
    accounts = []
    for idx, account_str in enumerate(account_str_list, 1):
        wid = account_str.strip()
        # 过滤空内容（避免多余分隔符导致的无效项）
        if not wid:
            print(f"⚠️  检测到第{idx}个无效项（空内容），已跳过")
            continue
        
        # 为当前账号生成随机UA
        ua = generate_random_ua()
        print(f"ℹ️  账号{idx}：自动生成UA（前70字符）：{ua[:70]}...")
        
        accounts.append({
            "index": idx, 
            "wid": wid, 
            "token": "", 
            "ua": ua,
            "user_data": {}, 
            "land_data": []
        })
    
    if not accounts:
        print("❌ 没有可用账号（所有项格式错误或为空），脚本终止")
        return None
    return accounts

def get_account_headers(account):
    """生成账号请求头（使用自动生成的UA，无wid相关输出）"""
    return {
        "Authorization": account["token"],
        "User-Agent": account["ua"],
        "Origin": "https://h5.zhumanito.cn",
        "Referer": "https://h5.zhumanito.cn/",
        "Accept-Language": "zh-CN,zh-Hans;q=0.9",
        "Accept-Encoding": "gzip, deflate, br"
    }
def mask_wid(wid):
    """对wid进行脱敏处理，显示前4位和后4位，中间用****替代"""
    if len(wid) <= 8:
        return wid  # 如果wid长度小于等于8，直接返回原wid
    return f"{wid[:4]}****{wid[-4:]}"

def login_account(account):
    """账号自动登录（隐藏wid显示，登录后更新token和用户数据）"""
    login_url = "https://api.zhumanito.cn/api/login"
    headers = get_account_headers(account)
    # 补充登录请求的Content-Type
    headers["Content-Type"] = "application/json;charset=utf-8"
    payload = {"wid": account["wid"]}  # 内部使用wid，不打印
    
    try:
        print(f"🔐 账号{account['index']}：发起登录请求（wid脱敏：{mask_wid(account['wid'])}）")

        response = requests.post(login_url, headers=headers, json=payload, timeout=20)
        response.raise_for_status()  # 触发HTTP错误（如404、500）
        res = response.json()
        
        if res.get("code") != 200:
            print(f"❌ 账号{account['index']}：登录失败，原因：{res.get('msg', '未知错误')}")
            return False
        
        # 更新账号的token、用户数据、土地数据
        account["token"] = res["data"]["token"]
        account["user_data"] = res["data"]["user"]
        account["land_data"] = res["data"].get("land", [])
        
        # 打印登录成功信息（不含wid）
        print(f"✅ 账号{account['index']}：登录成功！")
        print(f"  📌 当前资源：💧{account['user_data']['water_num']}，☀️{account['user_data']['sun_num']}")
        if account["land_data"]:
            print(f"  🌱 土地状态：共{len(account['land_data'])}块，生长阶段{account['land_data'][0]['seed_stage']}")
        return True
    
    except RequestException as e:
        print(f"❌ 账号{account['index']}：登录异常，原因：{str(e)}")
        return False

def get_user_status(account):
    """获取账号当前资源（水、阳光），无wid输出"""
    if not account.get("user_data"):
        print(f"⚠️  账号{account['index']}：未获取到用户数据，返回默认资源值0")
        return 0, 0
    water = account["user_data"].get("water_num", 0)
    sun = account["user_data"].get("sun_num", 0)
    return water, sun

# -------------------------- 【任务+浇水函数（无wid输出）】--------------------------
def get_unfinished_tasks(headers, account_idx):
    """获取账号未完成任务列表（无wid相关输出）"""
    task_url = "https://api.zhumanito.cn/api/task?"
    try:
        response = requests.get(task_url, headers=headers, timeout=20)
        response.raise_for_status()
        task_data = response.json()
        
        if task_data.get("code") != 200:
            print(f"❌ 账号{account_idx}：获取任务列表失败，原因：{task_data.get('msg', '未知错误')}")
            return []
        
        # 筛选未完成任务（status=0）
        unfinished_tasks = [t for t in task_data["data"]["task"] if t["status"] == 0]
        # 打印所有任务状态
        print("=" * 40)
        print(f"📋 账号{account_idx} - 所有任务状态：")
        for task in task_data["data"]["task"]:
            status_text = "✅ 已完成" if task["status"] == 1 else "❌ 未完成"
            print(f"  任务{task['id']}：{task['content']} | 奖励：💧{task['water_num']} ☀️{task['sun_num']} | {status_text}")
        print("=" * 40)
        return unfinished_tasks
    
    except RequestException as e:
        print(f"❌ 账号{account_idx}：获取任务异常，原因：{str(e)}")
        return []

def complete_task_1(headers, account_idx, account):
    """执行【每日签到】任务（任务ID=1，完成后更新用户资源）"""
    complete_url = "https://api.zhumanito.cn/api/task/complete"
    try:
        print(f"\n🔄 账号{account_idx}：开始执行【每日签到】任务（ID=1）")
        # 复制请求头并补充Content-Type
        task_headers = headers.copy()
        task_headers["Content-Type"] = "application/x-www-form-urlencoded;charset=utf-8"
        
        # 提交任务完成请求
        response = requests.post(complete_url, headers=task_headers, data="task_id=1&", timeout=20)
        response.raise_for_status()
        res = response.json()
        
        if res.get("code") != 200:
            print(f"❌ 账号{account_idx}：【每日签到】失败，原因：{res.get('msg', '未知错误')}")
            return False
        
        # 更新账号的用户数据（资源变化）
        if res.get("data", {}).get("user"):
            account["user_data"] = res["data"]["user"]
        
        print(f"✅ 账号{account_idx}：【每日签到】任务完成！")
        return True
    
    except RequestException as e:
        print(f"❌ 账号{account_idx}：【每日签到】异常，原因：{str(e)}")
        return False

def complete_task_2(headers, account_idx, account, task):
    """执行【浏览指定页面】任务（任务ID=2，需先访问链接再提交）"""
    # 检查任务是否包含目标链接
    task_url = task.get("url")
    if not task_url:
        print(f"\n❌ 账号{account_idx}：【浏览指定页面】任务缺少目标链接，已跳过")
        return False
    
    try:
        print(f"\n🔄 账号{account_idx}：开始执行【浏览指定页面】任务（ID=2）")
        print(f"🌐 正在访问目标链接（前60字符）：{task_url[:60]}...")
        
        # 访问目标页面（模拟浏览）
        browse_response = requests.get(task_url, headers=headers, timeout=25)
        browse_response.raise_for_status()
        time.sleep(3)  # 模拟实际浏览延迟
        print(f"✅ 账号{account_idx}：目标页面浏览完成")
        
        # 提交任务完成请求
        complete_url = "https://api.zhumanito.cn/api/task/complete"
        submit_headers = headers.copy()
        submit_headers["Content-Type"] = "application/x-www-form-urlencoded;charset=utf-8"
        submit_data = f"task_id={task['id']}&"
        
        submit_response = requests.post(complete_url, headers=submit_headers, data=submit_data, timeout=20)
        submit_response.raise_for_status()
        res = submit_response.json()
        
        if res.get("code") != 200:
            print(f"❌ 账号{account_idx}：【浏览指定页面】提交失败，原因：{res.get('msg', '未知错误')}")
            return False
        
        # 更新账号用户数据
        if res.get("data", {}).get("user"):
            account["user_data"] = res["data"]["user"]
        
        print(f"✅ 账号{account_idx}：【浏览指定页面】任务完成！")
        return True
    
    except RequestException as e:
        print(f"❌ 账号{account_idx}：【浏览指定页面】异常，原因：{str(e)}")
        return False

def complete_watering(headers, account_idx, account):
    """执行浇水操作（带重试机制，浇水后更新资源和土地状态）"""
    water_url = "https://api.zhumanito.cn/api/water"
    # 配置请求重试策略（应对临时网络错误）
    retry_strategy = requests.adapters.HTTPAdapter(
        max_retries=requests.packages.urllib3.util.retry.Retry(
            total=2,  # 总重试次数
            backoff_factor=3,  # 重试间隔（1s, 3s, 9s...）
            allowed_methods=["POST"],  # 仅对POST请求重试
            status_forcelist=[429, 500, 502, 503, 504]  # 需要重试的HTTP状态码
        )
    )
    session = requests.Session()
    session.mount("https://", retry_strategy)
    
    try:
        print("=" * 40)
        print(f"💧 账号{account_idx}：开始执行浇水操作")
        # 复制请求头并补充Content-Type
        water_headers = headers.copy()
        water_headers["Content-Type"] = "application/x-www-form-urlencoded;charset=utf-8"
        
        # 发送浇水请求
        response = session.post(water_url, headers=water_headers, data=b"", timeout=(25, 30))
        response.raise_for_status()
        res = response.json()
        
        # 处理能量不足的特殊情况
        if res.get("code") == 10006 and "能量值不足" in res.get("msg", ""):
            print(f"⚠️  账号{account_idx}：浇水失败，原因：{res['msg']}")
            return False
        
        if res.get("code") != 200:
            print(f"❌ 账号{account_idx}：浇水失败，原因：{res.get('msg', '未知错误')}")
            return False
        
        # 更新账号的用户数据和土地数据
        account["user_data"] = res["data"]["user"]
        account["land_data"] = res["data"].get("land", [])
        
        # 打印浇水结果
        current_water, current_sun = get_user_status(account)
        land_count = len(account["land_data"])
        print(f"✅ 账号{account_idx}：浇水成功！")
        print(f"📊 剩余资源：💧{current_water}，☀️{current_sun}")
        if land_count > 0:
            print(f"🌱 土地状态：共{land_count}块，生长阶段{account['land_data'][0]['seed_stage']}")
        print("=" * 40)
        return True
    
    except RequestException as e:
        print(f"❌ 账号{account_idx}：浇水异常，原因：{str(e)}")
        return False

# -------------------------- 【主流程（无wid输出）】--------------------------
def auto_multi_account():
    """多账号自动处理主流程：登录→任务→浇水"""
    print("🚀 【茄皇多账号自动化脚本】已启动\n")
    print("🚀 欢迎加入qq群：https://qm.qq.com/q/RfI2JT5AmO\n")
    # 解析环境变量获取账号列表
    accounts = parse_qh_env()
    if not accounts:
        return
    
    # 逐个处理账号
    for account in accounts:
        account_idx = account["index"]
        total_accounts = len(accounts)
        # 打印账号处理分隔符
        print(f"\n" + "=" * 50)
        print(f"📌 正在处理账号 {account_idx}/{total_accounts}")
        print("=" * 50)
        
        # 1. 账号登录
        login_success = login_account(account)
        if not login_success:
            print(f"❌ 账号{account_idx}：登录失败，跳过后续所有操作")
            continue
        
        # 2. 获取请求头（登录后token已更新）
        account_headers = get_account_headers(account)
        
        # 3. 获取并处理未完成任务
        unfinished_tasks = get_unfinished_tasks(account_headers, account_idx)
        if unfinished_tasks:
            for task in unfinished_tasks:
                # 匹配任务类型并执行
                if task["id"] == 1 and task["content"] == "每日签到":
                    complete_task_1(account_headers, account_idx, account)
                elif task["id"] == 2 and task["content"] == "浏览指定页面":
                    complete_task_2(account_headers, account_idx, account, task)
                else:
                    print(f"\n⚠️  账号{account_idx}：发现未知任务（ID：{task['id']}，内容：{task['content']}），已跳过")
            # 打印任务处理后的资源
            task_water, task_sun = get_user_status(account)
            print(f"\n🎉 账号{account_idx}：所有可处理任务已完成")
            print(f"📊 任务后资源：💧{task_water}，☀️{task_sun}")
        else:
            print(f"\n🎉 账号{account_idx}：无未完成任务或无法获取任务列表")
            no_task_water, no_task_sun = get_user_status(account)
            print(f"📊 当前资源：💧{no_task_water}，☀️{no_task_sun}")
        
        # 4. 循环浇水（资源满足：水≥20且阳光≥20）
        print(f"\n🔄 账号{account_idx}：进入循环浇水逻辑（触发条件：💧≥20 且 ☀️≥20）")
        while True:
            current_water, current_sun = get_user_status(account)
            if current_water >= 20 and current_sun >= 20:
                print(f"\n📌 账号{account_idx}：资源满足（💧{current_water}，☀️{current_sun}），执行浇水")
                water_success = complete_watering(account_headers, account_idx, account)
                if not water_success:
                    print(f"🔚 账号{account_idx}：浇水失败，退出浇水循环")
                    break
                time.sleep(2)  # 浇水间隔，避免请求过于频繁
            else:
                print(f"\n🔚 账号{account_idx}：资源不足（💧{current_water}，☀️{current_sun}），停止浇水")
                break
        
        # 单个账号处理完成
        print(f"\n✅ 账号{account_idx}/{total_accounts}：所有操作处理完毕")
        # 非最后一个账号，添加延迟避免并发
        if account_idx < total_accounts:
            delay_time = 5
            print(f"⏳ 账号间延迟{delay_time}秒，准备处理下一个账号...\n")
            time.sleep(delay_time)
    
    # 所有账号处理完成
    print("\n" + "=" * 50)
    print("🎯 所有账号已全部处理完成！脚本执行结束")
    print("=" * 50)

# 脚本入口
if __name__ == "__main__":
    auto_multi_account()