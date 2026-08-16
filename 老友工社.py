'''
#注册链接
http://www.laoyou.video/h5/reg.html?invite_code=8Y46CV
# 使用说明:
# 变量 LYGS_USERINFO 格式: 手机号&密码&设备ID (多个账号用换行或@分隔)
# 示例: 150456789222&111111&8b23522229098f8cae
# 注:设备id可直接随机生成(生成地址:https://uat.lzltool.com/Tools/RandomHex)
# 依赖:requests
'''
import datetime
import json
import logging
import os
import random
import time
import requests
from concurrent.futures import ThreadPoolExecutor

INVITE_URL = "http://www.laoyou.video/h5/reg.html?invite_code=8Y46CV"

logging.basicConfig(level=logging.INFO,
   format='%(asctime)s %(message)s',
   datefmt='%H:%M:%S'
)

def print_banner():
    print(f"""
老友工社自动任务脚本

注册链接: {INVITE_URL}
""")



def get_userinfo():
    userinfo_str = os.getenv('LYGS_USERINFO', '')
    if not userinfo_str:
        logging.error("❌ 未找到环境变量 LYGS_USERINFO")
        logging.error("❌ 请在青龙面板环境变量中配置账号信息")
        return []
    
    userinfo_list = []
    if '\n' in userinfo_str:
        userinfo_list = [line.strip() for line in userinfo_str.split('\n') if line.strip()]
    elif '@' in userinfo_str:
        userinfo_list = [item.strip() for item in userinfo_str.split('@') if item.strip()]
    else:
        userinfo_list = [userinfo_str.strip()]
    
    valid_users = []
    for user in userinfo_list:
        if user.count('&') >= 2:
            valid_users.append(user)
        else:
            logging.warning(f"⚠️ 账号格式错误，已跳过: {user}")
    
    if not valid_users:
        logging.error("❌ 没有有效的账号信息")
        return []
    
    logging.info(f"✅ 共加载 {len(valid_users)} 个账号")
    return valid_users

MAX_CONCURRENT_TASKS = 1
lygs_headers = {
    'User-Agent': "okhttp/4.10.0",
    'Connection': "Keep-Alive",
    'Accept': "application/json",
    'Accept-Encoding': "gzip",
    'os': "android",
    'Version-Code': "4",
    'Client-Version': "1.0.3",
}

def void_follow(nickname,headers,tsk):
    try:
        url = "https://www.laoyou.video/api/v2/video/recommends"
        headers['datetime'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        params = {'page': "5",'type': "0"}
        resp = requests.get(url, params=params, headers=headers).json()
        for video in resp:
            if tsk['finish_num'] >= tsk['completed_num']:
                logging.info(f"✅ {nickname}>>{tsk['name']} 已完成")
                return
            url = "https://www.laoyou.video/api/v2/follow"
            headers['datetime'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
            params = {'id': f"{video.get('user_id')}"}
            resp = requests.post(url,params=params, headers=headers).json()
            tsk['finish_num'] = tsk['finish_num'] + 1
            logging.info(f"   ├─ 关注用户: {video.get('id')}")
            wait_time = random.randint(2, 5)
            logging.info(f"   ├─ 等待 {wait_time} 秒后继续...")
            time.sleep(wait_time)
        void_follow(nickname,headers,tsk)
    except Exception:
        logging.error(f"❌ {nickname}>>关注任务异常")   

def voide_time(nickname,headers,tsk):
    try:
        if tsk['finish_num'] >= tsk['completed_num']:
            logging.info(f"✅ {nickname}>>{tsk['name']} 已完成")
            return
        logging.info(f"⏱️ {nickname}>>{tsk['name']}")
        url = "https://www.laoyou.video/api/v2/video/watchtime"
        headers['datetime'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        payload = {'time': "300"}
        response = requests.post(url, data=payload, headers=headers)
        logging.info(f"   ├─ 观看时长: 5分钟")
        time.sleep(2)
        payload = {'time': "600"}
        response = requests.post(url, data=payload, headers=headers)
        logging.info(f"   ├─ 观看时长: 10分钟")
        time.sleep(2)
        payload = {'time': "1200"}
        response = requests.post(url, data=payload, headers=headers)
        logging.info(f"   ├─ 观看时长: 20分钟")
        time.sleep(2)
    except Exception:
        logging.error(f"❌ {nickname}>>观看时长任务异常")   

def voide_share(nickname,headers,tsk):
    try:
        logging.info(f"🔄 {nickname}>>{tsk['name']}")
        url = "https://www.laoyou.video/api/v2/video/recommends"
        headers['datetime'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        params = {'page': "1",'type': "0"}
        resp = requests.get(url, params=params, headers=headers).json()
        for video in resp:
            if tsk['finish_num'] >= tsk['completed_num']:
                logging.info(f"✅ {nickname}>>{tsk['name']} 已完成")
                return
            url = "https://www.laoyou.video/api/v2/video/share"
            headers['datetime'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
            params = {'video_id': video.get("id")}
            resp = requests.get(url,params=params, headers=headers).json()
            tsk['finish_num'] = tsk['finish_num'] + 1
            logging.info(f"   ├─ 转发视频: {video.get('id')}")
        voide_share(nickname,headers,tsk)
    except Exception:
        logging.error(f"❌ {nickname}>>转发任务异常")   

def voide_collect(nickname,headers,tsk):
    try:
        logging.info(f"⭐ {nickname}>>{tsk['name']}")
        url = "https://www.laoyou.video/api/v2/video/recommends"
        headers['datetime'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        params = {'page': "1",'type': "0"}
        resp = requests.get(url, params=params, headers=headers).json()
        for video in resp:
            if tsk['finish_num'] >= tsk['completed_num']:
                logging.info(f"✅ {nickname}>>{tsk['name']} 已完成")
                return
            url = "https://www.laoyou.video/api/v2/video/collect"
            headers['datetime'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
            params = {'video_id': video.get("id")}
            resp = requests.get(url,params=params, headers=headers).json()
            tsk['finish_num'] = tsk['finish_num'] + 1
            logging.info(f"   ├─ 收藏视频: {video.get('id')}")
            wait_time = random.randint(2, 5)
            logging.info(f"   ├─ 等待 {wait_time} 秒后继续...")
            time.sleep(wait_time)
        voide_collect(nickname,headers,tsk)
    except Exception:
        logging.error(f"❌ {nickname}>>收藏任务异常")   

def voide_comment(nickname,headers,tsk):
    try:
        logging.info(f"💬 {nickname}>>{tsk['name']}")
        url = "https://www.laoyou.video/api/v2/user"
        headers['datetime'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        resp = requests.get(url, headers=headers).json()
        id = resp.get('id')
        name = resp.get('name')
        avatar = resp.get('avatar')
        url = "https://www.laoyou.video/api/v2/video/recommends"
        headers['datetime'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        params = {'page': "6",'type': "0"}
        resp = requests.get(url, params=params, headers=headers).json()
        for video in resp:
            if tsk['finish_num'] >= tsk['completed_num']:
                logging.info(f"✅ {nickname}>>{tsk['name']} 已完成")
                return
            url = "https://www.laoyou.video/api/v2/video/store-comment"
            headers['datetime'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
            payload = {
                'body': "666",
                'pid': "0",
                'video_id': video.get("id"),
                'at_user': "",
                'target_user': video.get("user_id"),
                'cid': "0",
                'reply_user': json.dumps({"user_avatar": avatar,"user_id": id,"user_name": name}, ensure_ascii=False),
                'type': "1",
                'voice': "",
                'time': ""
            }
            resp = requests.post(url, data=payload, headers=headers).json()
            tsk['finish_num'] = tsk['finish_num'] + 1
            logging.info(f"   ├─ 评论视频: {video.get('id')}")
            wait_time = random.randint(3, 6)
            logging.info(f"   ├─ 等待 {wait_time} 秒后继续...")
            time.sleep(wait_time)
        voide_comment(nickname,headers,tsk)
    except Exception:
        logging.error(f"❌ {nickname}>>评论任务异常")   

def voide_like(nickname,headers,tsk):
    try:
        logging.info(f"👍 {nickname}>>{tsk['name']}")
        url = "https://www.laoyou.video/api/v2/video/recommends"
        headers['datetime'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        params = {'page': "6",'type': "0"}
        resp = requests.get(url, params=params, headers=headers).json()
        for video in resp:
            if tsk['finish_num'] >= tsk['completed_num']:
                logging.info(f"✅ {nickname}>>{tsk['name']} 已完成")
                return
            url = f"https://www.laoyou.video/api/v2/video/like/{video.get('id')}"
            headers['datetime'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
            resp = requests.get(url, headers=headers).json()
            tsk['finish_num'] = tsk['finish_num'] + 1
            logging.info(f"   ├─ 点赞视频: {video.get('id')}")
            wait_time = random.randint(2, 5)
            logging.info(f"   ├─ 等待 {wait_time} 秒后继续...")
            time.sleep(wait_time)
        voide_like(nickname,headers,tsk)
    except Exception:
        logging.error(f"❌ {nickname}>>点赞任务异常")    

def watck_ads(phone,headers,tsk,uid):
    pass

def watck_videos(nickname,headers,tsk):
    try:
        logging.info(f"📺 {nickname}>>{tsk['name']}")
        url = "https://www.laoyou.video/api/v2/video/recommends"
        headers['datetime'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        params = {'page': "6",'type': "0"}
        resp = requests.get(url, params=params, headers=headers).json()
        for video in resp:
            if tsk['finish_num'] >= tsk['completed_num']:
                logging.info(f"✅ {nickname}>>{tsk['name']} 已完成")
                return
            logging.info(f"   ├─ 观看视频: {video.get('name')}")
            url = "https://www.laoyou.video/api/v2/video/watchvideo"
            headers['datetime'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]  
            resp = requests.post(url, headers=headers).json()
            tsk['finish_num'] = tsk['finish_num'] + 1
            wait_time = random.randint(15, 30)
            logging.info(f"   ├─ 等待 {wait_time} 秒后继续...")
            time.sleep(wait_time)
        watck_videos(nickname,headers,tsk)
    except Exception:
        logging.error(f"❌ {nickname}>>刷视频任务异常")    

def work_task(userinfo):
    try:
        config = userinfo.split("&")
        phone = config[0]
        password = config[1]
        deviceId = config[2]
        
        logging.info(f"🔐 {phone}>>开始登录...")
        
        url = "https://www.laoyou.video/api/v2/auth/login"
        payload = {'login': phone,'type': "2",'verifiable_code': "",'password': password}
        headers = lygs_headers.copy()
        headers['datetime'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        headers['deviceId'] = deviceId
        resp = requests.post(url, data=payload, headers=headers).json()
        
        if 'user_id' not in resp:
            logging.error(f"❌ {phone}>>登录失败，响应中无user_id")
            return
        
        user_id = resp['user_id']
        headers['Authorization'] = f"Bearer {resp['token']}"
        
        url = "https://www.laoyou.video/api/v2/user"
        headers['datetime'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        user_info = requests.get(url, headers=headers).json()
        nickname = user_info.get('name', phone)
        
        logging.info(f"✅ {nickname}>>登录成功，用户ID: {user_id}")
        
        url = "https://www.laoyou.video/api/v2/sign/add"
        headers['datetime'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        resp = requests.post(url, data=payload, headers=headers).json()
        result = resp.get("day")
        if result is None:
           logging.info(f"📅 {nickname}>>{resp.get('message')}")
        else:
            logging.info(f"📅 {nickname}>>{resp.get('day')}")
        
        logging.info(f"📋 {nickname}>>获取任务列表...")
        
        task_list = []
        url = "https://www.laoyou.video/api/v2/mission/new-num-point"
        headers['datetime'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        resp = requests.get(url, headers=headers).json()
        task_list = []
        
        logging.info(f"📊 {nickname}>>基础任务:")
        for tsk in resp['basic']:
            logging.info(f"   ├─ {tsk['name']}: {tsk['finish_num']}/{tsk['completed_num']}")
            task_list.append({
                "name": tsk.get("name"),
                "finish_num": tsk.get("finish_num"),
                "completed_num": tsk.get("completed_num")
            })
        
        logging.info(f"📊 {nickname}>>互动任务:")
        for tsk in resp['interact']:
            task_list.append({
                "name": tsk.get("name"),
                "finish_num": tsk.get("finish_num"),
                "completed_num": tsk.get("completed_num")
            })
            logging.info(f"   ├─ {tsk['name']}: {tsk['finish_num']}/{tsk['completed_num']}")

        logging.info(f"📊 {nickname}>>进阶任务:")
        for tsk in resp['advanced']:
            task_list.append({
                "name": tsk.get("name"),
                "finish_num": tsk.get("is_finish"),
                "completed_num": tsk.get("completed_num")
            })
            logging.info(f"   ├─ {tsk['name']}: {tsk['is_finish']}/{tsk['completed_num']}")
        
        logging.info(f"📊 {nickname}>>社交任务:")
        for tsk in resp['social']:
            task_list.append({
                "name": tsk.get("name"),
                "finish_num": tsk.get("finish_num"),
                "completed_num": tsk.get("completed_num")
            })
            logging.info(f"   ├─ {tsk['name']}: {tsk['finish_num']}/{tsk['completed_num']}")
        
        logging.info(f"🚀 {nickname}>>开始执行任务...")
        
        watck_videos(nickname,headers,task_list[0])
        watck_ads(nickname,headers,task_list[1],user_id)
        voide_like(nickname,headers,task_list[2])
        voide_comment(nickname,headers,task_list[3])
        voide_collect(nickname,headers,task_list[4])
        voide_share(nickname,headers,task_list[5])
        voide_time(nickname,headers,task_list[9])
        void_follow(nickname,headers,task_list[12])
        
        logging.info(f"🎉 {nickname}>>所有任务执行完成！")
    except Exception as e:
        logging.error(f"❌ {nickname}>>执行失败: {str(e)}")
        import traceback
        logging.error(f"❌ 错误详情: {traceback.format_exc()}")
        return

if __name__ == '__main__':
    print_banner()
    userinfo = get_userinfo()
    if userinfo:
        with ThreadPoolExecutor(max_workers=MAX_CONCURRENT_TASKS) as executor:
            list(executor.map(work_task, userinfo))
    print(f"\n注册链接: {INVITE_URL}")
