"""
🎯 Bing Rewards 自动化脚本 - 多账号支持版-v1.0
变量名：bing_ck  多账号换行 
如果执行的发现积分不增长，且脚本上显示的积分跟实际不符，很有可能不是同一个账号的cookie，建议重新抓取。

cron: 10 0-20 * * *
"""
import requests
import random
import re
import time
import json
import os
from datetime import datetime, date
from urllib.parse import urlparse, parse_qs
import threading

# 尝试导入notify，失败则使用本地打印替代
try:
    import notify
except ImportError:
    class Notify:
        def send(self, title, content):
            print("\n--- [通知] ---")
            print(f"标题: {title}")
            print(f"内容:\n{content}")
            print("-------------------------------")
    notify = Notify()

def print_log(title: str, msg: str, account_index: int = None):
    """打印带时间戳的日志，支持账号编号前缀"""
    now = datetime.now().strftime("%H:%M:%S")
    if account_index is not None:
        title = f"账号{account_index} - {title}"
    print(f"{now} [{title}]: {msg or ''}")

# 从环境变量获取cookie，支持多行（一行一个）
def get_cookies(account_index=None):
    """从环境变量获取cookie，支持多行（一行一个）"""
    env_cookies = os.getenv("bing_ck")
    if env_cookies:
        # 分割多行cookie，去除空行和空白字符
        cookies_list = [ck.strip() for ck in env_cookies.strip().split("\n") if ck.strip()]
        return cookies_list
    else:
        print_log("配置错误", "未配置 bing_ck 环境变量，无法执行任务", account_index)
        return []

# 获取cookie列表
cookies_list = get_cookies()
if not cookies_list:
    print_log("启动错误", "没有可用的cookie，程序退出", None)
    exit(1)

print_log("初始化", f"检测到 {len(cookies_list)} 个账号，即将开始...", None)

# 浏览器通用头部（将在运行时根据当前cookie动态设置）
BROWSER_HEADERS = {
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36 Edg/137.0.0.0",
    "accept-language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
    "referer": "https://rewards.bing.com/"
}

# 新增：热搜词API及默认词库
HOT_WORDS_APIS = [
    ("https://dailyapi.eray.cc/", ["weibo", "douyin", "baidu", "toutiao", "thepaper", "qq-news", "netease-news", "zhihu"]),
    ("https://hot.baiwumm.com/api/", ["weibo", "douyin", "baidu", "toutiao", "thepaper", "qq", "netease", "zhihu"]),
    ("https://cnxiaobai.com/DailyHotApi/", ["weibo", "douyin", "baidu", "toutiao", "thepaper", "qq-news", "netease-news", "zhihu"]),
    ("https://hotapi.zhusun.top/", ["weibo", "douyin", "baidu", "toutiao", "thepaper", "qq-news", "netease-news", "zhihu"]),
    ("https://api-hot.imsyy.top/", ["weibo", "douyin", "baidu", "toutiao", "thepaper", "qq-news", "netease-news", "zhihu"]),
    ("https://hotapi.nntool.cc/", ["weibo", "douyin", "baidu", "toutiao", "thepaper", "qq-news", "netease-news", "zhihu"]),
]
DEFAULT_HOT_WORDS = [
    "盛年不重来，一日难再晨", "千里之行，始于足下", "少年易学老难成，一寸光阴不可轻", "敏而好学，不耻下问", "海内存知已，天涯若比邻", "三人行，必有我师焉",
    "莫愁前路无知已，天下谁人不识君", "人生贵相知，何用金与钱", "天生我材必有用", "海纳百川有容乃大；壁立千仞无欲则刚", "穷则独善其身，达则兼济天下", "读书破万卷，下笔如有神",
    "学而不思则罔，思而不学则殆", "一年之计在于春，一日之计在于晨", "莫等闲，白了少年头，空悲切", "少壮不努力，老大徒伤悲", "一寸光阴一寸金，寸金难买寸光阴", "近朱者赤，近墨者黑",
    "吾生也有涯，而知也无涯", "纸上得来终觉浅，绝知此事要躬行", "学无止境", "己所不欲，勿施于人", "天将降大任于斯人也", "鞠躬尽瘁，死而后已", "书到用时方恨少", "天下兴亡，匹夫有责",
    "人无远虑，必有近忧", "为中华之崛起而读书", "一日无书，百事荒废", "岂能尽如人意，但求无愧我心"
]

# 只保留推送相关的 load_used_words 和 save_used_words
USED_WORDS_FILE = "Bing_Rewards_Cache.json"
used_words_lock = threading.Lock()

def load_used_words():
    if not os.path.exists(USED_WORDS_FILE):
        return {}
    try:
        with open(USED_WORDS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def save_used_words(data):
    today = date.today().isoformat()
    keys_to_keep = []
    for k in data:
        date_part = None
        if '_' in k:
            date_part = k.split('_')[-1]
        elif k.startswith('push_'):
            date_part = k.replace('push_', '')
        if date_part and date_part >= today:
            keys_to_keep.append(k)
    new_data = {k: data[k] for k in keys_to_keep}
    with open(USED_WORDS_FILE, "w", encoding="utf-8") as f:
        json.dump(new_data, f, ensure_ascii=False, indent=2)

# fetch_hot_words 和 get_next_hot_word 只做热搜词的获取和随机，不再写入/读取used_words文件

def fetch_hot_words(max_count=30):
    """base_url和sources都随机顺序，依次全部尝试，只要有一个source成功获取热搜词就立即返回，全部失败用默认词库"""
    apis_shuffled = HOT_WORDS_APIS[:]
    random.shuffle(apis_shuffled)
    for base_url, sources in apis_shuffled:
        sources_shuffled = sources[:]
        random.shuffle(sources_shuffled)
        for source in sources_shuffled:
            api_url = base_url + source
            try:
                resp = requests.get(api_url, timeout=10)
                if resp.status_code == 200:
                    data = resp.json()
                    if isinstance(data, dict) and 'data' in data and data['data']:
                        all_titles = [item.get('title') for item in data['data'] if item.get('title')]
                        if all_titles:
                            print_log("热搜词", f"成功获取热搜词 {len(all_titles)} 条，来源: {api_url}")
                            random.shuffle(all_titles)  # 打乱顺序
                            return all_titles[:max_count]
            except Exception:
                pass
    print_log("热搜词", "全部热搜API失效，使用默认搜索词。")
    default_words = DEFAULT_HOT_WORDS[:max_count]
    random.shuffle(default_words)
    return default_words

hot_words = fetch_hot_words()

def get_next_hot_word(account_index=None, email=None):
    """每次随机返回一个热搜词"""
    return random.choice(hot_words) if hot_words else random.choice(DEFAULT_HOT_WORDS)

def get_rewards_points(cookies, account_index=None):
    """查询当前积分和账号信息"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Linux; Android 9; OPPO R11 Plus Build/PKQ1.190414.001; ) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/74.0.3729.136 Mobile Safari/537.36 BingSapphire/31.4.2110003555',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3',
        'Accept-Language': 'zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7',
        'Accept-Encoding': 'gzip, deflate',
        'Cache-Control': 'max-age=0',
        'Upgrade-Insecure-Requests': '1',
        'X-Search-Location': 'lat=19.3516,long=110.1012,re=-1.0000,disp=%20',
        'Sapphire-OSVersion': '9',
        'Sapphire-Configuration': 'Production',
        'Sapphire-APIVersion': '114',
        'Sapphire-Market': 'zh-CN',
        'X-Search-ClientId': '2E2936301F8D6BFD3225203D1E5F6A0D',
        'Sapphire-DeviceType': 'OPPO R11 Plus',
        'X-Requested-With': 'com.microsoft.bing',
        'Cookie': cookies
    }

    url = 'https://rewards.bing.com/'
    params = {
        'ssp': '1',
        'safesearch': 'moderate',
        'setlang': 'zh-hans',
        'cc': 'CN',
        'ensearch': '0',
        'PC': 'SANSAAND'
    }

    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        
        content = response.text
        
        # 提取积分
        points_pattern = r'"availablePoints":(\d+)'
        points_match = re.search(points_pattern, content)
        
        # 提取邮箱账号
        email_pattern = r'email:\s*"([^"]+)"'
        email_match = re.search(email_pattern, content)
        
        available_points = None
        email = None
        
        if points_match:
            available_points = int(points_match.group(1))
            # print_log("积分查询", f"当前积分: {available_points}")
        else:
            print_log("积分查询", "未找到 availablePoints 值", account_index)
            
        if email_match:
            email = email_match.group(1)
            # print_log("账号信息", f"账号: {email}")
        else:
            print_log("账号信息", "未找到 email 值", account_index)
            
        return {
            'points': available_points,
            'email': email
        }
            
    except requests.exceptions.RequestException as e:
        print_log("积分查询", f"请求失败: {e}", account_index)
        return None
    except Exception as e:
        print_log("积分查询", f"发生错误: {e}", account_index)
        return None

def bing_search_pc(cookies, account_index=None, email=None):
    # 使用热搜词
    q = get_next_hot_word(account_index, email)
    #print_log("搜索关键词", f"本次搜索词: {q}", account_index)

    url = "https://cn.bing.com/search"
    params = {
        "q": q,
        "qs": "FT",
        "form": "TSASDS"
    }

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36 Edg/137.0.0.0",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "Referer": "https://rewards.bing.com/",
        "Accept-Language": "zh-CN,zh;q=0.9",
        "Cookie": cookies
    }

    try:
        response = requests.get(url, params=params, headers=headers)
        if response.status_code == 200:
            return True
        else:
            return False
    except Exception as e:
        print_log("电脑搜索", f"电脑搜索异常: {e}", account_index)
        return False

def bing_search_mobile(cookies, account_index=None, email=None):
    """执行移动设备搜索，使用热搜词"""
    q = get_next_hot_word(account_index, email)
    #print_log("搜索关键词", f"本次搜索词: {q}", account_index)

    # 模拟真实移动搜索请求的cookie
    enhanced_cookies = cookies
    
    # 移除桌面版特有的cookie字段，这些可能影响移动搜索识别
    import re
    
    # 移除桌面版特有的字段
    desktop_fields_to_remove = [
        r'_HPVN=[^;]+',
        r'_RwBf=[^;]+', 
        r'_U=[^;]+',
        r'USRLOC=[^;]+',
        r'BFBUSR=[^;]+',
        r'_Rwho=[^;]+',
        r'ipv6=[^;]+',
        r'_clck=[^;]+',
        r'_clsk=[^;]+',
        r'webisession=[^;]+',
        r'MicrosoftApplicationsTelemetryDeviceId=[^;]+',
        r'MicrosoftApplicationsTelemetryFirstLaunchTime=[^;]+',
        r'MSPTC=[^;]+',
        r'vdp=[^;]+'
    ]
    
    for pattern in desktop_fields_to_remove:
        enhanced_cookies = re.sub(pattern, '', enhanced_cookies)
    
    # 清理多余的分号和空格
    enhanced_cookies = re.sub(r';;+', ';', enhanced_cookies)
    enhanced_cookies = enhanced_cookies.strip('; ')
    
    # 替换SRCHUSR为简化版本（移除DS和POEX参数）
    if 'SRCHUSR=' in enhanced_cookies:
        enhanced_cookies = re.sub(r'SRCHUSR=[^;]+', 'SRCHUSR=DOB=20250706', enhanced_cookies)
    else:
        enhanced_cookies += '; SRCHUSR=DOB=20250706'
    
    # 确保有SRCHD字段
    if 'SRCHD=' not in enhanced_cookies:
        enhanced_cookies += '; SRCHD=AF=NOFORM'
    
    # 添加或替换SRCHHPGUSR为移动设备版本
    if 'SRCHHPGUSR=' in enhanced_cookies:
        enhanced_cookies = re.sub(r'SRCHHPGUSR=[^;]+', 'SRCHHPGUSR=SRCHLANG=zh-Hans&DM=0&CW=360&CH=493&SCW=360&SCH=493&BRW=MM&BRH=MS&DPR=3.0&UTC=480&PR=3&OR=0&PRVCW=360&PRVCH=493&HV=1751764054&HVE=CfDJ8Inh5QCoSQBNls38F2rbEpSFNIuT7R7A-dN544maOpoSyIiAlvCb43wPmzrMB8xLZeNzPTVPZYSpNz07pdIhrHpXIpf7BsQSxPNmP9esnrCjcj4OTSnzlqIQ0NroSiLt3Awrdp6qCqmkbZUfleTej6Bio11sryZznjdagVAUt5JoBZSzj5SbjYNHGoSgrIu2Ow&PREFCOL=0', enhanced_cookies)
    else:
        enhanced_cookies += '; SRCHHPGUSR=SRCHLANG=zh-Hans&DM=0&CW=360&CH=493&SCW=360&SCH=493&BRW=MM&BRH=MS&DPR=3.0&UTC=480&PR=3&OR=0&PRVCW=360&PRVCH=493&HV=1751764054&HVE=CfDJ8Inh5QCoSQBNls38F2rbEpSFNIuT7R7A-dN544maOpoSyIiAlvCb43wPmzrMB8xLZeNzPTVPZYSpNz07pdIhrHpXIpf7BsQSxPNmP9esnrCjcj4OTSnzlqIQ0NroSiLt3Awrdp6qCqmkbZUfleTej6Bio11sryZznjdagVAUt5JoBZSzj5SbjYNHGoSgrIu2Ow&PREFCOL=0'

    url = "https://cn.bing.com/search"
    params = {
        "q": q,
        "form": "NPII01",
        "filters": "tnTID:\"DSBOS_F29F59C848FA467D96D2F8EEC96FBC7A\" tnVersion:\"8908b7744161474e8812c12c507ece49\" Segment:\"popularnow.carousel\" tnCol:\"39\" tnScenario:\"TrendingTopicsAPI\" tnOrder:\"ef45722b-8213-4953-9c44-57e0dde6ac78\"",
        "ssp": "1",
        "safesearch": "moderate",
        "setlang": "zh-hans",
        "cc": "CN",
        "ensearch": "0",
        "PC": "SANSAAND"
    }

    headers = {
        "host": "cn.bing.com",
        "upgrade-insecure-requests": "1",
        "user-agent": "Mozilla/5.0 (Linux; Android 9; OPPO R11 Plus Build/PKQ1.190414.001; ) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/74.0.3729.136 Mobile Safari/537.36 BingSapphire/31.4.2110003555",
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3",
        "x-search-location": "lat=19.3516,long=110.1012,re=-1.0000,disp=%20",
        "sapphire-osversion": "9",
        "sapphire-configuration": "Production",
        "sapphire-apiversion": "114",
        "sapphire-market": "zh-CN",
        "x-search-clientid": "2E2936301F8D6BFD3225203D1E5F6A0D",
        "sapphire-devicetype": "OPPO R11 Plus",
        "accept-encoding": "gzip, deflate",
        "accept-language": "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7",
        "cookie": enhanced_cookies,
        "x-requested-with": "com.microsoft.bing"
    }

    try:
        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            return True
        else:
            return False
    except Exception as e:
        print_log("移动搜索", f"移动设备搜索异常: {e}", account_index)
        return False



def get_dashboard_data(cookies, account_index=None):
    """统一获取dashboard数据和token"""
    try:
        headers = {
            **BROWSER_HEADERS,
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
            "cookie": cookies
        }
        resp = requests.get("https://rewards.bing.com/", headers=headers, timeout=30)
        resp.raise_for_status()
        
        html_text = resp.text
        token_match = re.search(r'name="__RequestVerificationToken".*?value="([^"]+)"', html_text)
        dashboard_match = re.search(r'var dashboard\s*=\s*(\{.*?\});', html_text, re.DOTALL)
        
        if not token_match:
            print_log('Dashboard错误', "未能获取 __RequestVerificationToken", account_index)
            return None
        
        if not dashboard_match:
            print_log('Dashboard错误', "未能获取 dashboard 数据", account_index)
            return None
        
        token = token_match.group(1)
        dashboard_json = json.loads(dashboard_match.group(1).rstrip().rstrip(';'))
        
        return {
            'dashboard_data': dashboard_json,
            'token': token
        }
    except Exception as e:
        print_log('Dashboard错误', str(e), account_index)
        return None

def complete_daily_set_tasks(cookies, account_index=None):
    """完成每日活动任务"""
    # print_log('每日活动', '--- 开始检查网页端每日活动 ---')
    completed_count = 0
    try:
        # 获取dashboard数据
        dashboard_result = get_dashboard_data(cookies, account_index)
        if not dashboard_result:
            return completed_count
        
        dashboard_data = dashboard_result['dashboard_data']
        token = dashboard_result['token']
        
        # 提取积分信息
        if 'userStatus' in dashboard_data:
            user_status = dashboard_data['userStatus']
            available_points = user_status.get('availablePoints', 0)
            lifetime_points = user_status.get('lifetimePoints', 0)
            # print_log("每日活动", f"? 当前积分: {available_points}, 总积分: {lifetime_points}", account_index)
        
        # 提取每日任务
        today_str = date.today().strftime('%m/%d/%Y')
        daily_tasks = dashboard_data.get('dailySetPromotions', {}).get(today_str, [])
        
        if not daily_tasks:
            print_log("每日活动", "没有找到今日的每日活动任务", account_index)
            return completed_count
        
        # 过滤未完成的任务
        incomplete_tasks = [task for task in daily_tasks if not task.get('complete')]
        
        if not incomplete_tasks:
            # print_log("每日活动", "所有每日活动任务已完成", account_index)
            return completed_count
        
        print_log("每日活动", f"找到 {len(incomplete_tasks)} 个未完成的每日活动任务", account_index)
        
        # 执行任务
        for i, task in enumerate(incomplete_tasks, 1):
            print_log("每日活动", f"执行任务 {i}/{len(incomplete_tasks)}: {task.get('title', '未知任务')}", account_index)
            
            if execute_task(task, token, cookies, account_index):
                completed_count += 1
                print_log("每日活动", f"? 任务完成: {task.get('title', '未知任务')}", account_index)
            else:
                print_log("每日活动", f"? 任务失败: {task.get('title', '未知任务')}", account_index)
            
            # 随机延迟
            time.sleep(random.uniform(2, 4))
        
        print_log("每日活动", f"每日活动执行完成，成功完成 {completed_count} 个任务", account_index)
        
    except Exception as e:
        print_log('每日活动出错', f"异常: {e}", account_index)
    
    return completed_count

def setup_task_headers(cookies):
    """设置任务执行的请求头"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36 Edg/137.0.0.0',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'Accept-Language': 'zh-CN,zh;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br, zstd',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Site': 'same-origin',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-User': '?1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Ch-Ua': '"Microsoft Edge";v="137", "Chromium";v="137", "Not/A)Brand";v="24"',
        'Sec-Ch-Ua-Mobile': '?0',
        'Sec-Ch-Ua-Platform': '"Windows"',
        'Sec-Ch-Ua-Platform-Version': '"19.0.0"',
        'Sec-Ch-Ua-Model': '""',
        'Sec-Ch-Ua-Bitness': '"64"',
        'Sec-Ch-Prefers-Color-Scheme': 'light',
        'Sec-Ms-Gec': '1',
        'Sec-Ms-Gec-Version': '1-137.0.3296.83',
        'Cookie': cookies
    }
    return headers

def setup_api_headers(cookies):
    """设置API请求的请求头"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36 Edg/137.0.0.0',
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'Accept-Language': 'zh-CN,zh;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br, zstd',
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'X-Requested-With': 'XMLHttpRequest',
        'Origin': 'https://rewards.bing.com',
        'Referer': 'https://rewards.bing.com/',
        'Sec-Fetch-Site': 'same-origin',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Ch-Ua': '"Microsoft Edge";v="137", "Chromium";v="137", "Not/A)Brand";v="24"',
        'Sec-Ch-Ua-Mobile': '?0',
        'Sec-Ch-Ua-Platform': '"Windows"',
        'Sec-Ch-Ua-Platform-Version': '"19.0.0"',
        'Sec-Ch-Ua-Model': '""',
        'Sec-Ch-Ua-Bitness': '"64"',
        'Sec-Ch-Prefers-Color-Scheme': 'light',
        'Sec-Ms-Gec': '1',
        'Sec-Ms-Gec-Version': '1-137.0.3296.83',
        'Cookie': cookies
    }
    return headers

def extract_tasks(more_promotions):
    """提取任务"""
    tasks = []
    for promotion in more_promotions:
        complete = promotion.get('complete')
        priority = promotion.get('priority')
        attributes = promotion.get('attributes', {})
        is_unlocked = attributes.get('is_unlocked')
        # 只要complete为False且(priority为0或7，或is_unlocked为True)
        if (complete == False or complete == 'False') and (
            priority == 0 or priority == 7 or is_unlocked is True or is_unlocked == 'True'):
            tasks.append(promotion)
    return tasks

def extract_search_query(destination_url):
    """从URL中提取搜索查询"""
    try:
        parsed_url = urlparse(destination_url)
        query_params = parse_qs(parsed_url.query)
        if 'q' in query_params:
            search_query = query_params['q'][0]
            import urllib.parse
            search_query = urllib.parse.unquote(search_query)
            return search_query
        return None
    except Exception as e:
        print_log("更多活动", f"提取搜索查询失败: {e}", None)
        return None

def report_activity(task, token, cookies, account_index=None):
    """报告任务活动，真正完成任务"""
    if not token:
        return False
    
    try:
        post_url = 'https://rewards.bing.com/api/reportactivity?X-Requested-With=XMLHttpRequest'
        post_headers = setup_api_headers(cookies)
        payload = f"id={task.get('offerId', task.get('name'))}&hash={task.get('hash', '')}&timeZone=480&activityAmount=1&dbs=0&form=&type=&__RequestVerificationToken={token}"
        response = requests.post(post_url, data=payload, headers=post_headers, timeout=15)
        
        if response.status_code == 200:
            try:
                result = response.json()
                if result.get("activity") and result["activity"].get("points", 0) > 0:
                    print_log("更多活动", f"? 获得{result['activity']['points']}积分", account_index)
                    return True
                else:
                    return False
            except json.JSONDecodeError:
                return False
        else:
            return False
    except Exception as e:
        return False

def execute_task(task, token, cookies, account_index=None):
    """执行单个任务"""
    try:
        destination_url = task.get('destinationUrl') or task.get('attributes', {}).get('destination')
        if not destination_url:
            print_log("更多活动", f"? 任务 {task.get('name')} 没有目标URL", account_index)
            return False
        
        # 检查是否为搜索任务
        search_query = extract_search_query(destination_url)
        
        if search_query:
            # 搜索任务
            print_log("更多活动", f"? 执行搜索任务: {task.get('title')}", account_index)
        else:
            # 非搜索任务（如Edge相关任务）
            print_log("更多活动", f"? 执行URL访问任务: {task.get('title')}", account_index)
            
            # 对于Edge相关任务，可能需要特殊处理URL
            if 'microsoftedgewelcome.microsoft.com' in destination_url:
                # 转换为实际的Microsoft URL
                if 'focus=privacy' in destination_url:
                    destination_url = 'https://www.microsoft.com/zh-cn/edge/welcome?exp=e155&form=ML23ZX&focus=privacy&cs=2175697442'
                elif 'focus=performance' in destination_url:
                    destination_url = 'https://www.microsoft.com/zh-cn/edge/welcome?exp=e155&form=ML23ZX&focus=performance&cs=2175697442'
        
        # 设置任务执行请求头
        headers = setup_task_headers(cookies)
        
        # 发送请求
        response = requests.get(
            destination_url, 
            headers=headers, 
            timeout=15,
            allow_redirects=True
        )
        
        if response.status_code == 200:
            print_log("更多活动", f"? 任务执行成功", account_index)
            # 报告活动
            if report_activity(task, token, cookies, account_index):
                return True
            else:
                print_log("更多活动", f"?? 任务执行成功但活动报告失败", account_index)
                return False
        else:
            print_log("更多活动", f"? 任务执行失败，状态码: {response.status_code}", account_index)
            return False
            
    except Exception as e:
        print_log("更多活动", f"? 执行任务时出错: {e}", account_index)
        return False

def complete_more_activities(cookies, account_index=None):
    """完成更多活动任务"""
    # print_log('更多活动', '--- 开始检查更多活动 ---')
    completed_count = 0
    
    try:
        # 获取dashboard数据
        dashboard_result = get_dashboard_data(cookies, account_index)
        if not dashboard_result:
            print_log("更多活动", "无法获取dashboard数据，跳过更多活动\n", account_index)
            return completed_count
        
        dashboard_data = dashboard_result['dashboard_data']
        token = dashboard_result['token']
        
        # 提取积分信息
        if 'userStatus' in dashboard_data:
            user_status = dashboard_data['userStatus']
            available_points = user_status.get('availablePoints', 0)
            lifetime_points = user_status.get('lifetimePoints', 0)
            # print_log("更多活动", f"? 当前积分: {available_points}, 总积分: {lifetime_points}", account_index)
        
        # 提取更多活动任务
        more_promotions = dashboard_data.get('morePromotions', [])
        tasks = extract_tasks(more_promotions)
        
        if not tasks:
            # print_log("更多活动", "没有找到可执行的更多活动任务", account_index)
            return completed_count
        
        print_log("更多活动", f"找到 {len(tasks)} 个可执行的更多活动任务", account_index)
        
        # 执行任务
        for i, task in enumerate(tasks, 1):
            print_log("更多活动", f"执行任务 {i}/{len(tasks)}: {task.get('title', '未知任务')}", account_index)
            
            if execute_task(task, token, cookies, account_index):
                completed_count += 1
            else:
                print_log("更多活动", f"? 任务失败: {task.get('title', '未知任务')}", account_index)
            
            # 随机延迟
            time.sleep(random.uniform(2, 4))
        
        print_log("更多活动", f"更多活动执行完成，成功完成 {completed_count} 个任务\n", account_index)
        
    except Exception as e:
        print_log('更多活动出错', f"异常: {e}\n", account_index)
    
    return completed_count

search_thread_stopped = threading.Event()

def get_search_progress_sum(dashboard_data, search_type):
    user_status = dashboard_data.get('userStatus', {})
    counters = user_status.get('counters', {})
    search_tasks = counters.get(search_type, [])
    return sum(task.get('pointProgress', 0) for task in search_tasks)

def perform_search_tasks(search_type, search_func, cookies, account_index=None):
    check_interval = 4
    print_log(search_type, f"{search_type} - 执行{check_interval}次搜索 ---", account_index)
    count = 0
    dashboard_result = get_dashboard_data(cookies, account_index)
    dashboard_data = dashboard_result['dashboard_data'] if dashboard_result and 'dashboard_data' in dashboard_result else None
    progress_type = 'pcSearch' if '电脑' in search_type else 'mobileSearch'
    last_progress = get_search_progress_sum(dashboard_data, progress_type) if dashboard_data else 0
    for i in range(check_interval):
        count += 1
        if search_func(cookies, account_index):
            delay = random.randint(20, 30)
            print_log(search_type, f"第 {count} 次{search_type}成功，等待 {delay} 秒...", account_index)
            time.sleep(delay)
        else:
            print_log(search_type, f"第 {count} 次{search_type}失败", account_index)
        # 每次都检查进度
        dashboard_result = get_dashboard_data(cookies, account_index)
        dashboard_data = dashboard_result['dashboard_data'] if dashboard_result and 'dashboard_data' in dashboard_result else None
        current_progress = get_search_progress_sum(dashboard_data, progress_type) if dashboard_data else last_progress
        # 第4次搜索完成后输出进度变化
        if count == 4:
            print_log(f"{search_type}", f"已完成{count} 次，进度变化: {last_progress} -> {current_progress}", account_index)
        # 检查任务是否完成
        if progress_type == 'pcSearch':
            if is_pc_search_complete(dashboard_data):
                print_log(f"{search_type}", f"电脑搜索任务已完成", account_index)
                break
        elif progress_type == 'mobileSearch':
            if is_mobile_search_complete(dashboard_data):
                print_log(f"{search_type}", f"移动搜索任务已完成", account_index)
                break
    # 4次后统一中止线程
    if not ((progress_type == 'pcSearch' and is_pc_search_complete(dashboard_data)) or (progress_type == 'mobileSearch' and is_mobile_search_complete(dashboard_data))):
        print_log(f"{search_type}", f"{check_interval}次后任务未完成，停止线程", account_index)
        search_thread_stopped.set()
        raise SystemExit()

def is_pc_search_complete(dashboard_data):
    for task in dashboard_data['userStatus']['counters'].get('pcSearch', []):
        if not task.get('complete', True):
            return False
    return True

def is_mobile_search_complete(dashboard_data):
    for task in dashboard_data['userStatus']['counters'].get('mobileSearch', []):
        if not task.get('complete', True):
            return False
    return True

def get_cached_init_points(email, date_str):
    key = f"init_{email}_{date_str}"
    data = load_used_words()
    entry = data.get(key)
    if entry and str(entry.get("init_points")) != "None":
        return entry["init_points"]
    return None

def set_cached_init_points(email, date_str, points):
    try:
        data = load_used_words()
        key = f"init_{email}_{date_str}"
        if key in data and str(data[key].get("init_points")) != "None":
            return
        data[key] = {
            "init_points": points,
            "datetime": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        save_used_words(data)
    except Exception:
        pass

def format_account_summary(dashboard_data, email, script_start_points, final_points, account_index=None):
    prefix = f"账号{account_index} - " if account_index is not None else "账号: "
    lines = [f"{prefix}{email}"]
    lines.append(f"?积分变化: {script_start_points} -> {final_points} (+{final_points - script_start_points})")
    # 搜索任务
    user_status = dashboard_data.get('userStatus', {})
    counters = user_status.get('counters', {})
    for search_type, label in [("pcSearch", "电脑搜索"), ("mobileSearch", "移动搜索")]:
        search_tasks = counters.get(search_type, [])
        for task in search_tasks:
            title = task.get('title', label)
            progress = f"{task.get('pointProgress', 0)}/{task.get('pointProgressMax', 0)}"
            lines.append(f"?{label}: {progress}")
    # 每日活动
    lines.append("?---------- 每日活动 ----------")
    today_str = date.today().strftime('%m/%d/%Y')
    daily_tasks = dashboard_data.get('dailySetPromotions', {}).get(today_str, [])
    if daily_tasks:
        for task in daily_tasks:
            title = task.get('title', '每日任务')
            complete = '?' if task.get('complete') else '?'
            lines.append(f"{complete}{title}: {'已完成' if task.get('complete') else '未完成'}")
    else:
        lines.append("无每日活动任务")
    # 更多活动
    lines.append("?---------- 更多活动 ----------")
    more_tasks = dashboard_data.get('morePromotions', [])
    if more_tasks:
        for task in more_tasks:
            # 只显示pointProgressMax或activityProgressMax大于0的任务
            ppm = task.get('pointProgressMax', 0) or 0
            if ppm > 0:
                title = task.get('title', '更多任务')
                complete = '?' if task.get('complete') else '?'
                lines.append(f"{complete}{title}: {'已完成' if task.get('complete') else '未完成'}")
    else:
        lines.append("无更多活动任务")
    return '\n'.join(lines)

def single_account_main(cookies, account_index):
    """单个账号的完整任务流程"""
    #print(f"\n{'='*15} [开始处理账号 {account_index}] {'='*15}")
    
    # 1. 查询初始积分和账号信息（重试3次）
    #print_log("账号信息", "---查询账号信息和初始积分 ---", account_index)
    initial_data = None
    for retry in range(3):
        initial_data = get_rewards_points(cookies, account_index)
        if initial_data is not None and initial_data['points'] is not None:
            break
        if retry < 2:  # 前两次失败时重试
            print_log("账号信息", f"第{retry + 1}次获取失败，{3 - retry - 1}秒后重试...", account_index)
            time.sleep(3 - retry - 1)  # 递减延迟：2秒、1秒
    
    if initial_data is None or initial_data['points'] is None:
        print_log("账号信息", "重试3次后仍无法获取初始积分，跳过此账号", account_index)
        return None
    
    email = initial_data.get('email', '未知邮箱')
    today_str = date.today().isoformat()
    # 优先从缓存读取初始积分
    cached_init_points = get_cached_init_points(email, today_str)
    if cached_init_points is not None:
        script_start_points = cached_init_points
    else:
        script_start_points = initial_data['points']
        set_cached_init_points(email, today_str, script_start_points)
    print_log("账号信息", f"账号: {email}, 初始积分: {script_start_points}", account_index)
    
    # 任务前dashboard_data不再用于推送
    dashboard_result = get_dashboard_data(cookies, account_index)
    dashboard_data = dashboard_result['dashboard_data'] if dashboard_result and 'dashboard_data' in dashboard_result else None
    if dashboard_data and not is_pc_search_complete(dashboard_data):
        perform_search_tasks("电脑搜索", lambda c, ai: bing_search_pc(c, ai, email), cookies, account_index)
    else:
        print_log("电脑搜索", "【电脑搜索 - 已完成】", account_index)
    pc_completed_points = get_rewards_points(cookies, account_index)
    mobile_start_points = pc_completed_points['points'] if pc_completed_points else script_start_points
    if dashboard_data and not is_mobile_search_complete(dashboard_data):
        perform_search_tasks("移动搜索", lambda c, ai: bing_search_mobile(c, ai, email), cookies, account_index)
    else:
        print_log("移动搜索", "【移动搜索 - 已完成】", account_index)
    complete_daily_set_tasks(cookies, account_index)
    print_log("每日活动", "【每日活动 - 已完成】", account_index)
    complete_more_activities(cookies, account_index)
    print_log("更多活动", "【更多活动 - 已完成】", account_index)
    final_data = get_rewards_points(cookies, account_index)
    # 重新获取最新dashboard_data用于推送
    dashboard_result = get_dashboard_data(cookies, account_index)
    dashboard_data = dashboard_result['dashboard_data'] if dashboard_result and 'dashboard_data' in dashboard_result else None
    if final_data and final_data['points'] is not None:
        final_points = final_data['points']
        points_earned = final_points - script_start_points
        print_log("脚本完成", f"? 最终积分：{final_points}（+{points_earned}）", account_index)
        if dashboard_data:
            summary = format_account_summary(dashboard_data, email, script_start_points, final_points, account_index)
        else:
            summary = f"账号{account_index} ： {email}\n(未获取到dashboard数据)"
        return summary
    else:
        print_log("脚本完成", "无法获取最终积分", account_index)
        return None

def has_pushed_today():
    today = date.today().isoformat()
    used_words_data = load_used_words()
    return used_words_data.get(f"push_{today}", False)

def mark_pushed_today():
    today = date.today().isoformat()
    used_words_data = load_used_words()
    used_words_data[f"push_{today}"] = True
    save_used_words(used_words_data)

def main():
    """主函数 - 支持多账号并发执行和推送"""
    all_summaries = []
    threads = []
    summaries_lock = threading.Lock()

    def thread_worker(cookies, i):
        try:
            summary = single_account_main(cookies, i)
            if summary:
                with summaries_lock:
                    all_summaries.append(summary)
        except Exception as e:
            print_log(f"账号{i}错误", f"处理账号时发生异常: {e}", i)

    for i, cookies in enumerate(cookies_list, 1):
        t = threading.Thread(target=thread_worker, args=(cookies, i))
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

    # --- 统一推送 ---
    print(f"\n\n{'='*10} [全部任务完成] {'='*10}")
    if search_thread_stopped.is_set():
        print_log("统一推送", "搜索任务未完成，线程被终止，取消推送。", None)
        return
    if has_pushed_today():
        print_log("统一推送", "今天已经推送过，取消本次推送。", None)
        return
    if all_summaries:
        print_log("统一推送", "准备发送所有账号的总结报告...", None)
        try:
            title = f"Microsoft Rewards 任务总结 ({date.today().strftime('%Y-%m-%d')})"
            content = "\n\n".join(all_summaries)
            notify.send(title, content)
            print_log("推送成功", "总结报告已发送。", None)
            mark_pushed_today()
        except Exception as e:
            print_log("推送失败", f"发送总结报告时出错: {e}", None)
    else:
        print_log("统一推送", "没有可供推送的账号信息。", None)

if __name__ == "__main__":
    main() 