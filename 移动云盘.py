#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
移动云盘自动签到 v5.0.3

包含以下功能:
1. 每日自动签到 (签到/抽奖/摇一摇/新版云朵领取)
2. 多账号并发支持 (环境变量 & 分隔)
3. 云朵中心新版任务自动处理 (上传/分享/AI相机/月任务补传等)
4. 临时文件智能清理与详细日志推送

更新说明:

### 20260420
v5.0.3:
- 适配新版签到链路，修复旧接口报错。
- 接入云朵中心新版任务。
- 新增 AI 相机、上传清理、分享文件每日自动化与月上传补传能力。
- 优化启动与任务日志输出。

### 20251227
v5.0.2:
- 🐛 日志修复：修复控制台日志重复输出问题，精简本地显示。
- 📊 总结优化：优化运行总结显示，通知推送保持完整详情。

v5.0.1:
- 🚀 架构升级：优化推送版逻辑，正式支持多账号并发处理。

配置说明:
变量名: ydyp
赋值方式:
1. 抓包 authTokenRefresh.do 请求头 Authorization 值。
2. 填入青龙环境变量，格式：Authorization值#手机号 (多账号用 & 分隔)。

⚠️ 依赖安装:
pip3 install requests

定时规则建议 (Cron):
0 0 8,16,20 * * * (每日早中晚执行)

Author: YaoHuo8648
Email: zheyizzf@188.com
Update: 2026.04.20
"""

import base64
import hashlib
import json
import os
import random
import re
import time
import uuid
from datetime import datetime, timezone, timedelta
from os import path
from urllib.parse import unquote

import requests

SCRIPT_VERSION = '5.0.3'

ua = 'Mozilla/5.0 (Linux; Android 11; M2012K10C Build/RP1A.200720.011; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/90.0.4430.210 Mobile Safari/537.36 MCloudApp/10.0.1'
market_ua = 'Mozilla/5.0 (Linux; Android 10; MI 8 Build/QKQ1.190828.002; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/143.0.7499.146 Mobile Safari/537.36 MCloudApp/12.5.4 AppLanguage/zh-CN'
cloud_file_dummy_content = b'0'
cloud_file_dummy_hash = hashlib.sha256(cloud_file_dummy_content).hexdigest()

err_accounts = ''  # 异常账号
all_logs = ''      # 所有用户的详细运行日志 (原 err_message)
user_amount = ''   # 用户云朵·数量
GLOBAL_DEBUG = False


def print_startup_info(account_count):
    print(f"移动云盘自动签到 v{SCRIPT_VERSION}")
    print(f"移动云盘共获取到{account_count}个账号")


# 发送通知
def load_send():
    cur_path = path.abspath(path.dirname(__file__))
    notify_file = cur_path + "/notify.py"

    if path.exists(notify_file):
        try:
            from notify import send  # 导入模块的send为notify_send
            print("加载通知服务成功！")
            return send  # 返回导入的函数
        except ImportError:
            print("加载通知服务失败~")
    else:
        print("加载通知服务失败~")

    return False  # 返回False表示未成功加载通知服务


class YP:
    def __init__(self, cookie):
        try:
            self.notebook_id = None
            self.note_token = None
            self.note_auth = None
            self.click_num = 15  # 定义抽奖次数和摇一摇戳一戳次数
            self.draw = 1  # 抽奖次数，首次免费
            self.client_version = '12.5.4'
            self.market_base_url = 'https://m.mcloud.139.com'
            self.market_source_id = '1097'
            self.sso_token = None
            self.user_domain_id = ''
            self.market_headers = {}
            self.market_cookies = {}
            self.session = requests.Session()
            self.user_log_lines = []

            self.timestamp = str(int(round(time.time() * 1000)))
            self.cookies = {'sensors_stay_time': self.timestamp}

            parts = cookie.split("#")
            if len(parts) < 2:
                raise ValueError(f"⚠️ 变量值格式错误: {cookie}")

            self.Authorization = parts[0]
            self.account = parts[1]
            
            # 【修改点1】手机号脱敏处理，保留前3后4
            if len(self.account) >= 11:
                self.encrypt_account = self.account[:3] + "****" + self.account[-4:]
            else:
                self.encrypt_account = self.account # 账号长度不足时不处理
                
            self.fruit_url = 'https://happy.mail.10086.cn/jsp/cn/garden/'

            self.jwtHeaders = {
                'User-Agent': ua,
                'Accept': '*/*',
                'Host': 'caiyun.feixin.10086.cn:7071',
            }
            self.treeHeaders = {
                'Host': 'happy.mail.10086.cn',
                'Accept': 'application/json, text/plain, */*',
                'User-Agent': ua,
                'Referer': 'https://happy.mail.10086.cn/jsp/cn/garden/wap/index.html?sourceid=1003',
                'Cookie': '',
            }

        except Exception as e:
            print(f"{e}")
            self.Authorization = None  # 标记为无效账号

    # 【修改点2】自定义日志函数：同时打印到控制台并记录到推送列表
    def log(self, content):
        print(content)
        self.user_log_lines.append(content)

    # 捕获异常
    @staticmethod
    def catch_errors(func):
        def wrapper(self, *args, **kwargs):
            try:
                return func(self, *args, **kwargs)
            except Exception as e:
                # 记录详细错误到日志
                err_str = f"错误: {str(e)}"
                print(err_str)
                self.user_log_lines.append(err_str)
            return None

        return wrapper

    @catch_errors
    def run(self):
        if self.jwt():
            self.signin_status()
            self.click()
            # 任务
            self.get_tasklist(url = 'sign_in_3', app_type = 'cloud_app')
            #print(f'\n☁️ 云朵大作战')
            #self.cloud_game()
            self.log(f'\n📰 公众号任务')
            self.wxsign()
            self.shake()
            self.surplus_num()
            self.log(f'\n🔥 热门任务')
            self.backup_cloud()
            self.open_send()
            self.log(f'\n📧 139邮箱任务')
            self.get_tasklist(url = 'newsign_139mail', app_type = 'email_app')
            self.receive()
            
            # 【修改点3】运行结束后，将当前用户的日志汇总到全局变量
            global all_logs
            user_log_str = "\n".join(self.user_log_lines)
            all_logs += f"用户【{self.encrypt_account}】日志:\n{user_log_str}\n\n"
            
        else:
            global err_accounts
            # 失效账号
            err_accounts += f'{self.encrypt_account}\n'

    @catch_errors
    def send_request(self, url, headers=None, cookies=None, data=None, params=None, method='GET', debug=None,
                     retries=5):

        debug = debug if debug is not None else GLOBAL_DEBUG

        request_headers = dict(headers or {})
        request_cookies = dict(cookies or {})
        request_args = {'json': data} if isinstance(data, dict) else {'data': data}

        for attempt in range(retries):
            try:
                response = self.session.request(method, url, params = params, headers = request_headers or None,
                                                cookies = request_cookies or None, **request_args)
                response.raise_for_status()
                if debug:
                    print(f'\n【{url}】响应数据:\n{response.text}')
                return response
            except (requests.RequestException, ConnectionError, TimeoutError) as e:
                print(f"请求异常: {e}")
                if attempt >= retries - 1:
                    print("达到最大重试次数。")
                    return None
                time.sleep(1)

    def request_json(self, url, headers=None, cookies=None, data=None, params=None, method='GET', debug=None,
                     retries=5):
        response = self.send_request(url, headers = headers, cookies = cookies, data = data, params = params,
                                     method = method, debug = debug, retries = retries)
        if response is None:
            return None
        try:
            return response.json()
        except ValueError as e:
            self.log(f'响应解析失败: {e}')
            return None

    @staticmethod
    def get_today_sign_state(result):
        today_sign_in = result.get('todaySignIn')
        if isinstance(today_sign_in, bool):
            return today_sign_in
        for day in result.get('cal') or []:
            if day.get('t'):
                return bool(day.get('s'))
        return None

    @staticmethod
    def extract_user_domain_id(jwt_token):
        try:
            payload = jwt_token.split('.')[1]
            payload += '=' * (-len(payload) % 4)
            data = json.loads(base64.urlsafe_b64decode(payload).decode())
            sub = data.get('sub', '')
            if isinstance(sub, str):
                sub = json.loads(sub)
            return sub.get('userDomainId', '')
        except (IndexError, KeyError, TypeError, ValueError, json.JSONDecodeError):
            return ''

    def build_market_context(self, jwt_token):
        self.user_domain_id = self.extract_user_domain_id(jwt_token)
        self.market_headers = {
            'User-Agent': market_ua,
            'Accept': '*/*',
            'jwtToken': jwt_token,
            'X-Requested-With': 'com.chinamobile.mcloud',
            'Referer': self.build_market_page_url(),
        }
        self.market_cookies = {'jwtToken': jwt_token}
        if self.user_domain_id:
            self.market_cookies['userDomainId'] = self.user_domain_id

    def build_market_page_url(self, source_id=None):
        current_source_id = source_id or self.market_source_id
        return f'{self.market_base_url}/portal/mobilecloud/index.html?path=newsignin&sourceid={current_source_id}&enableShare=1&token={self.sso_token or ""}&targetSourceId=001005'

    def build_market_headers(self, extra_headers=None, referer=None):
        headers = dict(self.market_headers)
        headers['Referer'] = referer or headers.get('Referer') or self.build_market_page_url()
        if extra_headers:
            headers.update(extra_headers)
        return headers

    def build_receive_headers(self, source_id=None):
        headers = self.build_market_headers({
            'showLoading': 'true',
            'appVersion': f'{self.client_version}.0',
            'activityId': 'sign_in_3',
        }, referer = self.build_market_page_url(source_id))
        thumb_cookie_name = next((name for name in self.session.cookies.keys() if name.startswith('.thumbcache_')), '')
        if thumb_cookie_name:
            headers['deviceId'] = unquote(self.session.cookies.get(thumb_cookie_name, ''))
        return headers

    def request_market_json(self, url, params=None, data=None, method='GET', debug=None, retries=5, headers=None,
                            cookies=None):
        request_cookies = dict(self.market_cookies)
        if cookies:
            request_cookies.update(cookies)
        return self.request_json(url, headers = self.build_market_headers(headers), cookies = request_cookies,
                                 data = data, params = params, method = method, debug = debug, retries = retries)

    def post_signin_journaling(self, keyword, source_id=None):
        current_source_id = source_id or self.market_source_id
        payload = f'module=uservisit&optkeyword={keyword}&sourceid={current_source_id}&marketName=sign_in_3'
        response = self.send_request(f'{self.market_base_url}/ycloud/visitlog/journaling',
                                     headers = self.build_market_headers(
                                         {'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8'},
                                         referer = self.build_market_page_url(current_source_id)
                                     ),
                                     cookies = self.market_cookies, data = payload, method = 'POST', retries = 1)
        return response is not None

    def prepare_signin_center_session(self, for_receive=False, source_id=None):
        current_source_id = source_id or self.market_source_id
        page_url = self.build_market_page_url(current_source_id)
        self.send_request(page_url, headers = self.build_market_headers(referer = page_url),
                          cookies = self.market_cookies, retries = 1)
        for keyword in (
            'newsignin_index_pv',
            'newsignin_index_client',
            'newsignin_index_app_client',
            'newsignin_index_cookie_login',
            'newsignin_index_cookie',
            'newsignin_index_app_cookie_login',
        ):
            self.post_signin_journaling(keyword, current_source_id)
        if for_receive:
            self.post_signin_journaling('newsignin_index_receive_type', current_source_id)
        return True

    def click_task(self, task_id, key='task'):
        return self.request_market_json(f'{self.market_base_url}/market/signin/task/click?key={key}&id={task_id}')

    def get_notice_status(self):
        send_data = self.request_json('https://caiyun.feixin.10086.cn/market/msgPushOn/task/status',
                                      headers = self.jwtHeaders) or {}
        if send_data.get('code') != 0:
            return {}
        return send_data.get('result', {}) or {}

    def format_notice_task_log(self, task_name, notice_status):
        if not notice_status:
            return f'-需手动完成: {task_name}'
        push_on = int(notice_status.get('pushOn') or 0)
        first_status = int(notice_status.get('firstTaskStatus') or 0)
        second_status = int(notice_status.get('secondTaskStatus') or 0)
        on_duration = int(notice_status.get('onDuaration') or 0)
        total = int(notice_status.get('total') or 31)
        if push_on != 1:
            return f'-需手动完成: {task_name} (通知未开启)'
        if second_status == 3:
            return f'-已完成: {task_name}'
        if first_status != 3:
            return f'-待领取: {task_name} (首日奖励可领取)'
        if second_status == 2:
            return f'-待领取: {task_name} (已开启{on_duration}/{total}天)'
        return f'-进行中: {task_name} (已开启{on_duration}/{total}天)'

    def build_cloud_file_headers(self):
        return {
            'x-yun-op-type': '1',
            'x-yun-sub-op-type': '100',
            'x-yun-api-version': 'v1',
            'x-yun-client-info': '6|127.0.0.1|1|12.1.0|realme|RMX5060|BCFF2BBA6881DD8E4971803C63DDB5E4|02-00-00-00-00-00|android 15|1264X2592|zh||||032|0|',
            'x-yun-app-channel': '10000023',
            'Authorization': self.Authorization,
            'Content-Type': 'application/json; charset=UTF-8',
            'User-Agent': 'okhttp/4.12.0',
            'Host': 'personal-kd-njs.yun.139.com',
            'Connection': 'Keep-Alive'
        }

    def build_share_headers(self):
        return {
            'Authorization': self.Authorization,
            'x-yun-api-version': 'v1',
            'x-yun-app-channel': '10000023',
            'x-yun-client-info': f'||9|{self.client_version}|Chrome|143.0.7499.146|codextestshare||Windows 10||zh-CN|||Q2hyb21l||',
            'x-yun-module-type': '100',
            'x-yun-svc-type': '1',
            'x-SvcType': '1',
            'x-yun-channel-source': '10000023',
            'x-huawei-channelSrc': '10000023',
            'Content-Type': 'application/json;charset=UTF-8',
            'CMS-DEVICE': 'default',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36',
            'Referer': 'https://yun.139.com/shareweb/',
            'Origin': 'https://yun.139.com',
        }

    def create_cloud_file(self, prefix):
        beijing_tz = timezone(timedelta(hours=8))
        now = datetime.now(beijing_tz)
        file_size = len(cloud_file_dummy_content)
        file_name = f"{prefix}{now.strftime('%Y%m%d_%H%M%S')}.txt"
        payload = {
            "contentHash": cloud_file_dummy_hash,
            "contentHashAlgorithm": "SHA256",
            "contentType": "application/oct-stream",
            "fileRenameMode": "force_rename",
            "localCreatedAt": now.isoformat(timespec='milliseconds'),
            "name": file_name,
            "parallelUpload": True,
            "parentFileId": "/",
            "partInfos": [{
                "end": file_size,
                "partNumber": 1,
                "partSize": file_size,
                "start": 0
            }],
            "size": file_size,
            "type": "file"
        }
        response = self.send_request('https://personal-kd-njs.yun.139.com/hcy/file/create',
                                     headers = self.build_cloud_file_headers(), data = payload, method = 'POST')
        if not response or response.status_code != 200:
            return None
        try:
            res_json = response.json()
        except ValueError:
            return None
        if not res_json.get("success"):
            return None
        data = res_json.get("data", {})
        return {
            "fileId": data.get("fileId"),
            "fileName": data.get("fileName", file_name),
        }

    def list_cloud_root_files(self):
        items = []
        page_cursor = ''
        while True:
            response = self.request_json('https://personal-kd-njs.yun.139.com/hcy/file/list',
                                         headers = self.build_cloud_file_headers(),
                                         data = {
                                             'imageThumbnailStyleList': ['Small', 'Large'],
                                             'orderBy': 'updated_at',
                                             'orderDirection': 'DESC',
                                             'pageInfo': {'pageCursor': page_cursor, 'pageSize': 100},
                                             'parentFileId': '/',
                                         },
                                         method = 'POST')
            if not response:
                return items
            if not response.get('success'):
                self.log(f"获取云盘文件列表失败: {response.get('message', '未知错误')}")
                return items
            data = response.get('data', {})
            items.extend(data.get('items', []))
            page_cursor = data.get('nextPageCursor') or ''
            if not page_cursor:
                return items

    @staticmethod
    def is_cleanup_upload_file(item):
        if item.get('type') != 'file' or item.get('parentFileId') != '/':
            return False
        name = item.get('name', '')
        if not (name.endswith('.txt') and (name.startswith('auto_upload_') or name.startswith('auto_share_'))):
            return False
        size = item.get('size')
        content_hash = item.get('contentHash')
        return size in (0, 1, None) or content_hash == cloud_file_dummy_hash

    def trash_cloud_files(self, file_ids):
        if not file_ids:
            return True
        response = self.request_json('https://personal-kd-njs.yun.139.com/hcy/recyclebin/batchTrash',
                                     headers = self.build_cloud_file_headers(),
                                     data = {'fileIds': file_ids},
                                     method = 'POST')
        if not response:
            self.log('清理上传文件失败: 接口无响应')
            return False
        if response.get('success'):
            return True
        self.log(f"清理上传文件失败: {response.get('message', '未知错误')}")
        return False

    def cleanup_uploaded_files(self, current_file=None):
        file_ids = []
        if current_file and current_file.get('fileId'):
            file_ids.append(current_file['fileId'])
        for item in self.list_cloud_root_files():
            if self.is_cleanup_upload_file(item):
                file_ids.append(item.get('fileId'))
        seen = set()
        unique_file_ids = []
        for file_id in file_ids:
            if not file_id or file_id in seen:
                continue
            seen.add(file_id)
            unique_file_ids.append(file_id)
        if not unique_file_ids:
            return True
        if self.trash_cloud_files(unique_file_ids):
            self.log(f'-已清理上传文件: {len(unique_file_ids)}个')
            return True
        return False

    def complete_share_file_task(self, task):
        share_file = self.create_cloud_file('auto_share_')
        if not share_file:
            self.log('分享文件失败: 创建临时文件失败')
            return None
        try:
            response = self.request_json('https://yun.139.com/orchestration/personalCloud-rebuild/outlink/v1.0/getOutLink',
                                         headers = self.build_share_headers(),
                                         data = {
                                             'getOutLinkReq': {
                                                 'subLinkType': 0,
                                                 'encrypt': 0,
                                                 'coIDLst': [share_file.get('fileId')],
                                                 'caIDLst': [],
                                                 'pubType': 1,
                                                 'dedicatedName': share_file.get('fileName', ''),
                                                 'periodUnit': 1,
                                                 'viewerLst': [],
                                                 'extInfo': {'isWatermark': 0, 'shareChannel': '3001'},
                                                 'commonAccountInfo': {'account': self.account, 'accountType': 1},
                                             }
                                         },
                                         method = 'POST', retries = 1)
        finally:
            self.trash_cloud_files([share_file.get('fileId')])
        result = response.get('data', {}).get('result', {}) if response else {}
        if not response or not response.get('success') or result.get('resultCode') != '0':
            msg = result.get('resultDesc') or response.get('message', '未知错误') if response else '接口无响应'
            self.log(f'分享文件失败: {msg}')
            return None
        return self.query_cloud_task(task.get('id', 434), 'month') or task

    def build_ai_headers(self, use_client_info=False):
        headers = {
            'Connection': 'keep-alive',
            'sec-ch-ua-platform': '"Android"',
            'Authorization': self.Authorization,
            'x-yun-api-version': 'v1',
            'x-yun-tid': str(uuid.uuid4()),
            'sec-ch-ua': '"Android WebView";v="143", "Chromium";v="143", "Not A(Brand";v="24"',
            'sec-ch-ua-mobile': '?1',
            'X-Requested-With': 'com.chinamobile.mcloud',
            'Origin': 'https://frontend.mcloud.139.com',
            'Referer': 'https://frontend.mcloud.139.com/',
            'User-Agent': f'Mozilla/5.0 (Linux; Android 10; MI 8 Build/QKQ1.190828.002; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/143.0.7499.146 Mobile Safari/537.36 MCloudApp/{self.client_version} tid/{uuid.uuid4()}',
            'Content-Type': 'application/json',
            'Sec-Fetch-Site': 'same-site',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Dest': 'empty',
            'Accept-Encoding': 'gzip, deflate, br, zstd',
            'Accept-Language': 'zh,zh-CN;q=0.9,en-US;q=0.8,en;q=0.7',
        }
        if use_client_info:
            headers['Accept'] = 'text/event-stream'
            headers['x-yun-client-info'] = f'4||1|{self.client_version}||MI 8|{uuid.uuid4().hex.upper()}||android 10|||||'
            headers['x-yun-app-channel'] = '101'
            return headers
        headers['Accept'] = '*/*'
        headers['x-DeviceInfo'] = f'||36|{self.client_version}||MI 8|{uuid.uuid4()}||android 10|||||'
        return headers

    def get_ai_camera_sample_base64(self):
        sample_path = path.join(path.abspath(path.dirname(__file__)), 'assets', 'ai_camera_sample.jpg')
        if not path.exists(sample_path):
            return ''
        with open(sample_path, 'rb') as file:
            return f"data:image/jpg;base64,{base64.b64encode(file.read()).decode()}"

    @staticmethod
    def is_ai_chat_success(text):
        payloads = []
        for line in (text or '').splitlines():
            if line.startswith('data:'):
                payloads.append(line[5:].strip())
        if not payloads and text:
            payloads.append(text.strip())
        for payload in payloads:
            if not payload or payload == '[DONE]':
                continue
            try:
                data = json.loads(payload)
            except ValueError:
                continue
            if data.get('success') or data.get('code') == '0000':
                return True
        return False

    def complete_ai_camera_task(self):
        if not self.user_domain_id:
            self.log('AI相机任务失败: 缺少用户信息')
            return False
        image_data = self.get_ai_camera_sample_base64()
        if not image_data:
            self.log('AI相机任务失败: 缺少样图')
            return False
        recognize_payload = json.dumps({
            'channelId': '101',
            'userId': self.user_domain_id,
            'recognizeType': '1',
            'base64': image_data,
            'sendType': '2',
            'imageExt': 'jpg',
            'uploadToCloud': True,
            'timeout': 30000,
        }, ensure_ascii = False, separators = (',', ':'))
        recognize_data = self.request_json('https://ai.yun.139.com/api/image/aiRecognize',
                                           headers = self.build_ai_headers(),
                                           data = recognize_payload,
                                           method = 'POST')
        if not recognize_data:
            self.log('AI相机识图失败: 接口无响应')
            return False
        if not recognize_data.get('success'):
            self.log(f"AI相机识图失败: {recognize_data.get('message', '未知错误')}")
            return False
        recognize_result = recognize_data.get('data') or {}
        file_id = recognize_result.get('fileId')
        if not file_id:
            self.log('AI相机识图失败: 缺少文件ID')
            return False
        task_id = str(recognize_result.get('taskId') or int(time.time() * 1000))
        file_name = f'{int(task_id) + 1}.jpeg' if task_id.isdigit() else f'{task_id}.jpeg'
        input_time = datetime.now(timezone(timedelta(hours = 8))).isoformat(timespec = 'milliseconds')
        chat_payload = json.dumps({
            'userId': self.user_domain_id,
            'sessionId': '',
            'applicationType': 'chat',
            'applicationId': '',
            'sourceChannel': '101',
            'dialogueInput': {
                'dialogue': '？',
                'prompt': '',
                'inputTime': input_time,
                'enableForceLlm': False,
                'enableForceNetworkSearch': True,
                'enableModelThinking': False,
                'enableAllNetworkSearch': False,
                'enableKnowledgeAndNetworkSearch': False,
                'enableRegenerate': False,
                'versionInfo': {'h5Version': '2.7.6'},
                'extInfo': '{}',
                'sortInfo': {},
                'toolSetting': {'imageToolSetting': {'enableLlmDescribe': True}},
                'attachment': {
                    'attachmentTypeList': [3],
                    'fileList': [{'fileId': file_id, 'name': file_name}],
                },
            },
        }, ensure_ascii = False, separators = (',', ':'))
        chat_response = self.send_request('https://ai.yun.139.com/api/outer/assistant/chat/v2/add',
                                          headers = self.build_ai_headers(use_client_info = True),
                                          data = chat_payload,
                                          method = 'POST')
        if not chat_response:
            self.log('AI相机对话失败: 接口无响应')
            return False
        if self.is_ai_chat_success(chat_response.text):
            return True
        try:
            chat_data = chat_response.json()
        except ValueError:
            chat_data = None
        if chat_data and (chat_data.get('success') or chat_data.get('code') == '0000'):
            return True
        if chat_data:
            self.log(f"AI相机对话失败: {chat_data.get('message') or chat_data.get('msg', '未知错误')}")
            return False
        self.log('AI相机对话失败: 响应解析失败')
        return False

    @staticmethod
    def get_task_progress(task):
        progress_parts = []
        currstep = task.get('currstep', 0)
        process = task.get('process', 0)
        if currstep:
            progress_parts.append(f'阶段{currstep}')
        if process:
            progress_parts.append(f'进度{process}')
        if not progress_parts:
            return ''
        return f" ({'，'.join(progress_parts)})"

    @staticmethod
    def strip_task_name(task):
        return re.sub(r'<[^>]+>', '', task.get('name', ''))

    @staticmethod
    def get_task_step_types(task):
        return set(task.get('stepTypeSet') or [])

    def get_task_click_keys(self, task):
        task_id = task.get('id')
        currstep = task.get('currstep', 0)
        step_types = self.get_task_step_types(task)
        if task_id == 409:
            if currstep > 0:
                return ['task2']
            return ['task', 'task2']
        if 'click' in step_types and currstep == 0:
            return ['task']
        return []

    def get_cloud_task_groups(self):
        return [
            ('cloudEmail', '\n📮 联动任务'),
            ('time', '\n✨ 新版热门任务'),
            ('day', '\n📆 云盘每日任务'),
            ('month', '\n📆 云盘每月任务'),
        ]

    def query_cloud_task(self, task_id, group='time'):
        return_data = self.request_market_json(f'{self.market_base_url}/market/signin/task/taskListV2', params = {
            'marketname': 'sign_in_3',
            'clientVersion': self.client_version,
            'group': group,
        })
        if not return_data or return_data.get('code') != 0:
            return None
        for task in return_data.get('result', {}).get(group, []):
            if task.get('id') == task_id:
                return task
        return None

    def complete_monthly_upload_task(self, task):
        target_count = 100
        current_process = int(task.get('process') or 0)
        for attempt in range(3):
            remaining = max(0, target_count - current_process)
            if remaining == 0:
                return True
            if attempt == 0:
                self.log(f'-开始补上传进度: 当前{current_process}/{target_count}，还需{remaining}次')
            else:
                self.log(f'-继续补上传进度: 当前{current_process}/{target_count}，还需{remaining}次')
            for _ in range(remaining):
                self.updata_file()
            refreshed_task = self.query_cloud_task(task.get('id', 522), 'time')
            if not refreshed_task:
                return False
            refreshed_process = int(refreshed_task.get('process') or 0)
            if refreshed_task.get('state') == 'FINISH' or refreshed_process >= target_count:
                return True
            if refreshed_process <= current_process:
                self.log(f'-月上传任务进度: {refreshed_process}/{target_count}')
                return False
            current_process = refreshed_process
        self.log(f'-月上传任务进度: {current_process}/{target_count}')
        return False

    def get_cloud_tasklist_v2(self):
        for group, title in self.get_cloud_task_groups():
            return_data = self.request_market_json(f'{self.market_base_url}/market/signin/task/taskListV2', params = {
                'marketname': 'sign_in_3',
                'clientVersion': self.client_version,
                'group': group,
            })
            if not return_data:
                self.log(f'获取任务列表失败: {group}')
                continue
            if return_data.get('code') != 0:
                self.log(f"获取任务列表失败: {group} {return_data.get('msg', '未知错误')}")
                continue
            tasks = return_data.get('result', {}).get(group, [])
            if not tasks:
                continue
            self.log(title)
            for task in tasks:
                self.handle_cloud_v2_task(group, task)
        self.cleanup_uploaded_files()

    def handle_cloud_v2_task(self, group, task):
        task_id = task.get('id')
        task_name = self.strip_task_name(task)
        task_status = task.get('state', '')
        if task_status == 'FINISH':
            print(f'-已完成: {task_name}')
            return
        if group == 'day' and task_id == 106:
            self.log(f'-去完成: {task_name}')
            self.do_task(task_id, task_type = 'day', app_type = 'cloud_app')
            return
        if task_id == 522:
            self.log(f'-去完成: {task_name}')
            if self.complete_monthly_upload_task(task):
                self.log(f'-已完成: {task_name}')
                return
            refreshed_task = self.query_cloud_task(task_id, group) or task
            self.log(f'-需手动完成: {task_name}{self.get_task_progress(refreshed_task)}')
            return
        if task_id == 434:
            self.log(f'-去完成: {task_name}')
            refreshed_task = self.complete_share_file_task(task)
            if refreshed_task:
                refreshed_name = self.strip_task_name(refreshed_task)
                if refreshed_task.get('state') == 'FINISH':
                    self.log(f'-已完成: {refreshed_name}')
                    return
                self.log(f'-分享成功: {refreshed_name}{self.get_task_progress(refreshed_task)}')
                return
            self.log(f'-需手动完成: {task_name}{self.get_task_progress(task)}')
            return
        if task_id == 406:
            self.log(self.format_notice_task_log(task_name, self.get_notice_status()))
            return
        task_keys = self.get_task_click_keys(task)
        if task_keys:
            self.log(f'-去完成: {task_name}')
            for task_key in task_keys:
                click_data = self.click_task(task_id, task_key)
                if click_data and click_data.get('code') == 0:
                    continue
                msg = click_data.get('msg', '未知错误') if click_data else '接口无响应'
                self.log(f'-任务登记失败: {task_name} {msg}')
                return
            if task_id == 585 and self.complete_ai_camera_task():
                self.log(f'-已完成: {task_name}')
                return
            self.log(f'-已登记任务: {task_name}')
            return
        self.log(f'-需手动完成: {task_name}{self.get_task_progress(task)}')

    # 随机延迟默认1-1.5s
    def sleep(self, min_delay=1, max_delay=1.5):
        delay = random.uniform(min_delay, max_delay)
        time.sleep(delay)

    # 刷新令牌
    def sso(self):
        sso_url = 'https://orches.yun.139.com/orchestration/auth-rebuild/token/v1.0/querySpecToken'
        sso_headers = {
            'Authorization': self.Authorization,
            'User-Agent': ua,
            'Content-Type': 'application/json',
            'Accept': '*/*',
            'Host': 'orches.yun.139.com'
        }
        sso_payload = {"account": self.account, "toSourceId": "001005"}
        sso_data = self.request_json(sso_url, headers = sso_headers, data = sso_payload, method = 'POST')
        if not sso_data:
            self.log('刷新Token失败: 接口无响应')
            return None

        if sso_data['success']:
            refresh_token = sso_data['data']['token']
            self.sso_token = refresh_token
            return refresh_token
        else:
            self.log(f"刷新Token失败: {sso_data.get('message', '未知错误')}")
            return None

    # jwt
    def jwt(self):
        # 获取jwttoken
        token = self.sso()
        if token is not None:

            jwt_url = f"https://caiyun.feixin.10086.cn:7071/portal/auth/tyrzLogin.action?ssoToken={token}"
            jwt_data = self.request_json(jwt_url, headers = self.jwtHeaders, method = 'POST')
            if not jwt_data:
                self.log('JWT获取失败: 接口无响应')
                return False
            if jwt_data['code'] != 0:
                self.log(f"JWT获取失败: {jwt_data['msg']}")
                return False
            jwt_token = jwt_data['result']['token']
            self.jwtHeaders['jwtToken'] = jwt_token
            self.cookies['jwtToken'] = jwt_token
            self.build_market_context(jwt_token)
            return True
        else:
            self.log('-ck可能失效了')
            return False

    # 签到查询
    @catch_errors
    def signin_status(self):
        self.sleep()
        check_url = f'{self.market_base_url}/market/signin/page/infoV3'
        check_data = self.request_market_json(check_url, params = {'client': 'app'})
        if not check_data:
            self.log('查询签到失败: 接口无响应')
            return
        if check_data.get('code') != 0:
            self.log(f"查询签到失败: {check_data.get('msg', '未知错误')}")
            return
        if self.get_today_sign_state(check_data.get('result', {})):
            self.log('✅已签到')
            return
        signin_data = self.request_market_json(f'{self.market_base_url}/market/signin/page/startSignIn',
                                               params = {'client': 'app'})
        if not signin_data:
            self.log('签到失败: 接口无响应')
            return
        if signin_data.get('code') == 0 and self.get_today_sign_state(signin_data.get('result', {})):
            self.log('✅签到成功')
            return
        latest_data = self.request_market_json(check_url, params = {'client': 'app'})
        if latest_data and latest_data.get('code') == 0 and self.get_today_sign_state(latest_data.get('result', {})):
            self.log('✅签到成功')
            return
        self.log(f"签到失败: {signin_data.get('msg', '未知错误')}")

    # 戳一下
    def click(self):
        successful_click = 0  # 获得次数

        try:
            for _ in range(self.click_num):
                return_data = self.click_task(319) or {}
                time.sleep(0.2)

                if 'result' in return_data:
                    self.log(f'✅戳一戳: {return_data["result"]}')
                    successful_click += 1

            if successful_click == 0:
                print(f'❌戳一戳: 未获得 x {self.click_num}') # 失败的不记入通知，避免刷屏
        except Exception as e:
            print(f'错误信息:{e}')

    # 刷新笔记token
    @catch_errors
    def refresh_notetoken(self):
        note_url = 'http://mnote.caiyun.feixin.10086.cn/noteServer/api/authTokenRefresh.do'
        note_payload = {
            "authToken": self.auth_token,
            "userPhone": self.account
        }
        note_headers = {
            'X-Tingyun-Id': 'p35OnrDoP8k;c=2;r=1122634489;u=43ee994e8c3a6057970124db00b2442c::8B3D3F05462B6E4C',
            'Charset': 'UTF-8',
            'Connection': 'Keep-Alive',
            'User-Agent': 'mobile',
            'APP_CP': 'android',
            'CP_VERSION': '3.2.0',
            'x-huawei-channelsrc': '10001400',
            'Host': 'mnote.caiyun.feixin.10086.cn',
            'Content-Type': 'application/json; charset=UTF-8',
            'Accept-Encoding': 'gzip'
        }

        try:
            response = self.send_request(note_url, headers = note_headers, data = note_payload, method = "POST")
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            print('出错了:', e)
            return

        self.note_token = response.headers.get('NOTE_TOKEN')
        self.note_auth = response.headers.get('APP_AUTH')

    # 任务列表
    def get_tasklist(self, url, app_type):
        if url == 'sign_in_3' and app_type == 'cloud_app':
            self.get_cloud_tasklist_v2()
            return
        url = f'https://caiyun.feixin.10086.cn/market/signin/task/taskList?marketname={url}'
        return_data = self.send_request(url, headers = self.jwtHeaders, cookies = self.cookies).json()
        self.sleep()
        # 任务列表
        task_list = return_data.get('result', {})

        try:
            for task_type, tasks in task_list.items():
                if task_type in ["new", "hidden", "hiddenabc"]:
                    continue
                if app_type == 'cloud_app':
                    if task_type == "month":
                        self.log('\n📆 云盘每月任务')
                        for month in tasks:
                            task_id = month.get('id')
                            if task_id in [110, 113, 417, 409]:
                                continue
                            task_name = re.sub(r'<[^>]+>', '', month.get('name', ''))
                            task_status = month.get('state', '')

                            if task_status == 'FINISH':
                                print(f'-已完成: {task_name}') # 已完成的任务不刷屏推送到TG，只Print
                                continue
                            self.log(f'-去完成: {task_name}')
                            self.do_task(task_id, task_type = 'month', app_type = 'cloud_app')
                            time.sleep(2)
                    elif task_type == "day":
                        self.log('\n📆 云盘每日任务')
                        for day in tasks:
                            task_id = day.get('id')
                            if task_id == 404:
                                continue
                            task_name = re.sub(r'<[^>]+>', '', day.get('name', ''))
                            task_status = day.get('state', '')

                            if task_status == 'FINISH':
                                print(f'-已完成: {task_name}')
                                continue
                            self.log(f'-去完成: {task_name}')
                            self.do_task(task_id, task_type = 'day', app_type = 'cloud_app')
                elif app_type == 'email_app':
                    if task_type == "month":
                        self.log('\n📆 139邮箱每月任务')
                        for month in tasks:
                            task_id = month.get('id')
                            task_name = re.sub(r'<[^>]+>', '', month.get('name', ''))
                            task_status = month.get('state', '')
                            if task_id in [1004, 1005, 1015, 1020]:
                                continue

                            if task_status == 'FINISH':
                                print(f'-已完成: {task_name}')
                                continue
                            self.log(f'-去完成: {task_name}')
                            self.do_task(task_id, task_type = 'month', app_type = 'email_app')
                            time.sleep(2)
        except Exception as e:
            self.log(f'获取任务列表错误:{e}')

    # 做任务
    @catch_errors
    def do_task(self, task_id, task_type, app_type):
        self.sleep()
        if app_type == 'cloud_app':
            self.click_task(task_id)
        else:
            task_url = f'https://caiyun.feixin.10086.cn/market/signin/task/click?key=task&id={task_id}'
            self.send_request(task_url, headers = self.jwtHeaders, cookies = self.cookies)

        if app_type == 'cloud_app':
            if task_type == 'day':
                if task_id == 106:
                    self.log('-开始上传文件，默认0kb')
                    self.updata_file()
                elif task_id == 107:
                    self.refresh_notetoken()
                    print('-获取默认笔记id')
                    note_url = 'http://mnote.caiyun.feixin.10086.cn/noteServer/api/syncNotebookV3.do'
                    headers = {
                        'X-Tingyun-Id': 'p35OnrDoP8k;c=2;r=1122634489;u=43ee994e8c3a6057970124db00b2442c::8B3D3F05462B6E4C',
                        'Charset': 'UTF-8',
                        'Connection': 'Keep-Alive',
                        'User-Agent': 'mobile',
                        'APP_CP': 'android',
                        'CP_VERSION': '3.2.0',
                        'x-huawei-channelsrc': '10001400',
                        'APP_NUMBER': self.account,
                        'APP_AUTH': self.note_auth,
                        'NOTE_TOKEN': self.note_token,
                        'Host': 'mnote.caiyun.feixin.10086.cn',
                        'Content-Type': 'application/json; charset=UTF-8',
                        'Accept': '*/*'
                    }
                    payload = {
                        "addNotebooks": [],
                        "delNotebooks": [],
                        "notebookRefs": [],
                        "updateNotebooks": []
                    }
                    return_data = self.send_request(url = note_url, headers = headers, data = payload,
                                                    method = 'POST').json()
                    if return_data is None:
                        return print('出错了')
                    self.notebook_id = return_data['notebooks'][0]['notebookId']
                    print('开始创建笔记')
                    self.create_note(headers)
            elif task_type == 'month':
                pass
        elif app_type == 'email_app':
            if task_type == 'month':
                pass

    # 上传文件 (已修复)
    @catch_errors
    def updata_file(self):
        upload_info = self.create_cloud_file('auto_upload_')
        if not upload_info:
            self.log('-上传失败: 接口无响应')
            return
        self.log(f"-上传文件成功，文件名: {upload_info.get('fileName', '')}")
        self.cleanup_uploaded_files(upload_info)

    # 创建笔记
    def create_note(self, headers):
        note_id = self.get_note_id(32)
        createtime = str(int(round(time.time() * 1000)))
        time.sleep(3)
        updatetime = str(int(round(time.time() * 1000)))
        note_url = 'http://mnote.caiyun.feixin.10086.cn/noteServer/api/createNote.do'
        payload = {
            "archived": 0,
            "attachmentdir": note_id,
            "attachmentdirid": "",
            "attachments": [],
            "audioInfo": {
                "audioDuration": 0,
                "audioSize": 0,
                "audioStatus": 0
            },
            "contentid": "",
            "contents": [{
                "contentid": 0,
                "data": "<font size=\"3\">000000</font>",
                "noteId": note_id,
                "sortOrder": 0,
                "type": "RICHTEXT"
            }],
            "cp": "",
            "createtime": createtime,
            "description": "android",
            "expands": {
                "noteType": 0
            },
            "latlng": "",
            "location": "",
            "noteid": note_id,
            "notestatus": 0,
            "remindtime": "",
            "remindtype": 1,
            "revision": "1",
            "sharecount": "0",
            "sharestatus": "0",
            "system": "mobile",
            "tags": [{
                "id": self.notebook_id,
                "orderIndex": "0",
                "text": "默认笔记本"
            }],
            "title": "00000",
            "topmost": "0",
            "updatetime": updatetime,
            "userphone": self.account,
            "version": "1.00",
            "visitTime": ""
        }
        create_note_data = self.send_request(note_url, headers = headers, data = payload, method = "POST")
        if create_note_data.status_code == 200:
            self.log('-创建笔记成功')
        else:
            self.log('-创建失败')

    # 笔记id
    def get_note_id(self, length):
        characters = '19f3a063d67e4694ca63a4227ec9a94a19088404f9a28084e3e486b928039a299bf756ebc77aa4f6bfa250308ec6a8be8b63b5271a00350d136d117b8a72f39c5bd15cdfd350cba4271dc797f15412d9f269e666aea5039f5049d00739b320bb9e8585a008b52c1cbd86970cae9476446f3e41871de8d9f6112db94b05e5dc7ea0a942a9daf145ac8e487d3d5cba7cea145680efc64794d43dd15c5062b81e1cda7bf278b9bc4e1b8955846e6bc4b6a61c28f831f81b2270289e5a8a677c3141ddc9868129060c0c3b5ef507fbd46c004f6de346332ef7f05c0094215eae1217ee7c13c8dca6d174cfb49c716dd42903bb4b02d823b5f1ff93c3f88768251b56cc'
        note_id = ''.join(random.choice(characters) for _ in range(length))
        return note_id

    # 公众号签到
    @catch_errors
    def wxsign(self):
        self.sleep()
        url = 'https://caiyun.feixin.10086.cn/market/playoffic/followSignInfo?isWx=true'
        return_data = self.send_request(url, headers = self.jwtHeaders, cookies = self.cookies).json()

        if return_data['msg'] != 'success':
            return self.log(return_data['msg'])
        if not return_data['result'].get('todaySignIn'):
            return self.log('❌签到失败,可能未绑定公众号')
        return self.log('✅公众号签到成功')

    # 摇一摇
    def shake(self):
        url = "https://caiyun.feixin.10086.cn:7071/market/shake-server/shake/shakeIt?flag=1"
        successful_shakes = 0  # 记录成功摇中的次数

        try:
            for _ in range(self.click_num):
                return_data = self.send_request(url = url, cookies = self.cookies, headers = self.jwtHeaders,
                                                method = 'POST').json()
                time.sleep(1)
                shake_prize_config = return_data["result"].get("shakePrizeconfig")

                if shake_prize_config:
                    self.log(f"🎉摇一摇获得: {shake_prize_config['name']}")
                    successful_shakes += 1
        except Exception as e:
            print(f'错误信息: {e}')
        if successful_shakes == 0:
            print(f'❌未摇中 x {self.click_num}') # 失败不通知

    # 查询剩余抽奖次数
    @catch_errors
    def surplus_num(self):
        self.sleep()
        draw_info_url = 'https://caiyun.feixin.10086.cn/market/playoffic/drawInfo'
        draw_url = "https://caiyun.feixin.10086.cn/market/playoffic/draw"

        draw_info_data = self.send_request(draw_info_url, headers = self.jwtHeaders).json()

        if draw_info_data.get('msg') == 'success':
            remain_num = draw_info_data['result'].get('surplusNumber', 0)
            self.log(f'剩余抽奖次数{remain_num}')
            if remain_num > 50 - self.draw:
                for _ in range(self.draw):
                    self.sleep()
                    draw_data = self.send_request(url = draw_url, headers = self.jwtHeaders).json()

                    if draw_data.get("code") == 0:
                        prize_name = draw_data["result"].get("prizeName", "")
                        self.log("✅抽奖成功，获得:" + prize_name)
                    else:
                        print("❌抽奖失败")
            else:
                pass
        else:
            self.log(f"抽奖查询失败: {draw_info_data.get('msg')}")

    # 做任务
    @catch_errors
    def do_fruit_task(self, task_name, task_id, water_num):
        self.log(f'-去完成: {task_name}')
        do_task_url = f'{self.fruit_url}task/doTask.do?taskId={task_id}'
        do_task_data = self.send_request(do_task_url, headers = self.treeHeaders).json()

        if do_task_data.get('success'):
            get_water_url = f'{self.fruit_url}task/givenWater.do?taskId={task_id}'
            get_water_data = self.send_request(get_water_url, headers = self.treeHeaders).json()

            if get_water_data.get('success'):
                self.log(f'-已完成任务获得水滴: {water_num}')
            else:
                self.log(f'❌领取失败: {get_water_data.get("msg", "")}')
        else:
            self.log(f'❌参与任务失败: {do_task_data.get("msg", "")}')

    # 云朵大作战
    @catch_errors
    def cloud_game(self):
        game_info_url = 'https://caiyun.feixin.10086.cn/market/signin/hecheng1T/info?op=info'
        bigin_url = 'https://caiyun.feixin.10086.cn/market/signin/hecheng1T/beinvite'
        end_url = 'https://caiyun.feixin.10086.cn/market/signin/hecheng1T/finish?flag=true'

        game_info_data = self.send_request(game_info_url, headers = self.jwtHeaders, cookies = self.cookies).json()
        if game_info_data and game_info_data.get('code', -1) == 0:
            currnum = game_info_data.get('result', {}).get('info', {}).get('curr', 0)
            count = game_info_data.get('result', {}).get('history', {}).get('0', {}).get('count', '')
            rank = game_info_data.get('result', {}).get('history', {}).get('0', {}).get('rank', '')

            self.log(f'今日剩余游戏次数: {currnum} 合成次数: {count}')

            for _ in range(currnum):
                self.send_request(bigin_url, headers = self.jwtHeaders, cookies = self.cookies).json()
                print('-开始游戏,等待10-15秒完成游戏')
                time.sleep(random.randint(10, 15))
                end_data = self.send_request(end_url, headers = self.jwtHeaders, cookies = self.cookies).json()
                if end_data and end_data.get('code', -1) == 0:
                    self.log('游戏成功')
        else:
            print("-获取游戏信息失败")

    # 领取云朵
    @catch_errors
    def receive(self):
        prize_url = f"https://caiyun.feixin.10086.cn/market/prizeApi/checkPrize/getUserPrizeLogPage?currPage=1&pageSize=15&_={self.timestamp}"
        info_data = self.request_market_json(f'{self.market_base_url}/market/signin/page/infoV3',
                                             params = {'client': 'app'})
        if not info_data:
            self.log('查询云朵失败: 接口无响应')
            return
        if info_data.get('code') != 0:
            self.log(f"查询云朵失败: {info_data.get('msg', '未知错误')}")
            return
        info_result = info_data.get('result', {})
        pending_amount = info_result.get('toReceive', 0)
        total_amount = info_result.get('total', '')
        if pending_amount:
            self.prepare_signin_center_session(for_receive = True)
            receive_data = self.request_market_json(f'{self.market_base_url}/market/signin/page/receiveV2',
                                                    params = {'client': 'app'},
                                                    headers = self.build_receive_headers())
            if not receive_data:
                self.log('领取云朵失败: 接口无响应')
                self.log(f'-当前待领取:{pending_amount}云朵')
            elif receive_data.get('code') == 0:
                receive_result = receive_data.get('result', {})
                self.log(f'-领取云朵:{receive_result.get("receive", pending_amount)}云朵')
                total_amount = receive_result.get('total', total_amount)
            else:
                latest_info_data = self.request_market_json(f'{self.market_base_url}/market/signin/page/infoV3',
                                                            params = {'client': 'app'})
                latest_result = latest_info_data.get('result', {}) if latest_info_data and latest_info_data.get('code') == 0 else {}
                latest_pending = latest_result.get('toReceive', pending_amount)
                latest_total = latest_result.get('total', total_amount)
                pending_delta = pending_amount - latest_pending if isinstance(pending_amount, int) and isinstance(latest_pending, int) else 0
                total_delta = latest_total - total_amount if isinstance(total_amount, int) and isinstance(latest_total, int) else 0
                claimed_amount = total_delta or pending_delta or (pending_amount if latest_pending == 0 else 0)
                if claimed_amount > 0:
                    self.log(f'-领取云朵:{claimed_amount}云朵')
                    total_amount = latest_total
                else:
                    self.log(f"领取云朵失败: {receive_data.get('msg', '未知错误')}")
                    self.log(f'-当前待领取:{pending_amount}云朵')
        else:
            self.log('-当前待领取:0云朵')
        self.sleep()
        prize_data = self.request_json(prize_url, headers = self.jwtHeaders, cookies = self.cookies) or {}
        result = prize_data.get('result', {}).get('result') or []
        rewards = ''
        for value in result:
            prizeName = value.get('prizeName')
            flag = value.get('flag')
            if flag == 1:
                rewards += f'待领取奖品: {prizeName}\n'
        self.log(f'-当前云朵数量:{total_amount}云朵')
        if rewards:
            self.log(rewards)
        global user_amount
        user_amount += f'用户【{self.encrypt_account}】:{total_amount}云朵\n'

    # 备份云朵
    @catch_errors
    def backup_cloud(self):
        backup_url = 'https://caiyun.feixin.10086.cn/market/backupgift/info'
        backup_data = self.send_request(backup_url, headers = self.jwtHeaders).json()
        state = backup_data.get('result', {}).get('state', '')
        if state == -1:
            self.log('本月未备份,暂无连续备份奖励')

        elif state == 0:
            self.log('-领取本月连续备份奖励')
            cur_url = 'https://caiyun.feixin.10086.cn/market/backupgift/receive'
            cur_data = self.send_request(cur_url, headers = self.jwtHeaders).json()
            self.log(f'-获得云朵数量:{cur_data.get("result").get("result")}')

        elif state == 1:
            print('-已领取本月连续备份奖励')
        self.sleep()
        expend_url = 'https://caiyun.feixin.10086.cn/market/signin/page/taskExpansion'  # 每月膨胀云朵
        expend_data = self.send_request(expend_url, headers = self.jwtHeaders, cookies = self.cookies).json()

        curMonthBackup = expend_data.get('result', {}).get('curMonthBackup', '')  # 本月备份
        preMonthBackup = expend_data.get('result', {}).get('preMonthBackup', '')  # 上月备份
        curMonthBackupTaskAccept = expend_data.get('result', {}).get('curMonthBackupTaskAccept', '')  # 本月是否领取
        nextMonthTaskRecordCount = expend_data.get('result', {}).get('nextMonthTaskRecordCount', '')  # 下月备份云朵
        acceptDate = expend_data.get('result', {}).get('acceptDate', '')  # 月份

        if curMonthBackup:
            self.log(f'- 本月已备份，下月可领取膨胀云朵: {nextMonthTaskRecordCount}')
        else:
            self.log('- 本月还未备份，下月暂无膨胀云朵')

        if preMonthBackup:
            if curMonthBackupTaskAccept:
                print('- 上月已备份，膨胀云朵已领取')
            else:
                # 领取
                receive_url = f'https://caiyun.feixin.10086.cn/market/signin/page/receiveTaskExpansion?acceptDate={acceptDate}'
                receive_data = self.send_request(receive_url, headers = self.jwtHeaders,
                                                 cookies = self.cookies).json()
                if receive_data.get("code") != 0:
                    self.log(f'-领取失败:{receive_data.get("msg")}')
                else:
                    cloudCount = receive_data.get('result', {}).get('cloudCount', '')
                    self.log(f'- 膨胀云朵领取成功: {cloudCount}朵')
        else:
            print('-上月未备份，本月无膨胀云朵领取')

    # 通知云朵
    @catch_errors
    def open_send(self):
        notice_status = self.get_notice_status()
        if not notice_status:
            self.log('获取通知任务状态失败')
            return

        pushOn = notice_status.get('pushOn', '')
        firstTaskStatus = notice_status.get('firstTaskStatus', '')
        secondTaskStatus = notice_status.get('secondTaskStatus', '')
        onDuaration = notice_status.get('onDuaration', '')

        if pushOn == 1:
            reward_url = 'https://caiyun.feixin.10086.cn/market/msgPushOn/task/obtain'

            if firstTaskStatus == 3:
                print('- 任务1奖励已领取')
            else:
                # 领取任务1
                self.log('- 领取任务1奖励')
                reward1_data = self.send_request(reward_url, headers = self.jwtHeaders, data = {"type": 1},
                                                 method = "POST").json()
                self.log(reward1_data.get('result', {}).get('description', ''))

            if secondTaskStatus == 2:
                # 领取任务2
                self.log('- 领取任务2奖励')
                reward2_data = self.send_request(reward_url, headers = self.jwtHeaders, data = {"type": 2},
                                                 method = "POST").json()
                self.log(reward2_data.get('result', {}).get('description', ''))

            self.log(f'- 通知已开启天数: {onDuaration}, 满31天可领取奖励')
        else:
            self.log('- 通知权限未开启')


if __name__ == "__main__":
    env_name = 'ydyp'
    token = os.getenv(env_name)
    if not token:
        print(f'⛔️未获取到ck变量：请检查变量 {env_name} 是否填写')
        exit(0)

    cookies = re.split(r'[&]', token)
    print_startup_info(len(cookies))

    for i, account_info in enumerate(cookies, start=1):
        print(f"\n======== ▷ 第 {i} 个账号 ◁ ========")
        yp_instance = YP(account_info)
    
        if not yp_instance.Authorization:  # 跳过无效账号
            print(f"⛔️ 账号 {i} 无效，跳过执行")
            continue
    
        yp_instance.run()
        print("\n准备进行下一个账号")
        time.sleep(random.randint(1, 3))


    # 构建推送消息
    # 结构: 失效账号 -> 任务详情(过程日志) -> 云朵汇总
    msg = ""
    if err_accounts:
        msg += f"失效账号:\n{err_accounts}\n"
    
    msg += f"任务详情:\n{all_logs}\n"
    msg += f"云朵汇总:\n{user_amount}"
    
    # 【修改点4】优化控制台输出：删除重复的详细日志，只保留简要汇总，推送保持完整
    print("\n================ 运行总结 ================")
    if err_accounts:
        print(f"❌ 失效账号:\n{err_accounts}")
    if user_amount:
        print(f"☁️ 云朵汇总:\n{user_amount}")
    
    # 替换特殊字符以防止推送报错
    msg = msg.replace('-', ' ').replace('.', ' ').replace('!', '！').replace('(', '（').replace(')', '）')
    msg = msg.replace('_', ' ').replace('=', ' ').replace('~', ' ').replace('{', ' ').replace('}', ' ').replace('|', ' ')
        
    # 在load_send中获取导入的send函数
    send = load_send()

    # 判断send是否可用再进行调用
    if send:
        send('中国移动云盘任务信息', msg)
