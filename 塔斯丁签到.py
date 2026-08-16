#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
塔斯丁
author：Rex
createTime: 2025.12.4
email: 2375560790@qq.com
q群：621124138
blog: https://www.leishennb.icu/
每日签到
微信小程序 塔斯丁，抓包获取user-token
填写青龙环境变量 TA_S_TIENTECH， 格式如下： 备注#user_token，多账号换行
cron：0 1 7 * * *
"""
import os
import sys
from os import path
import random
import time
from typing import Optional, Dict, Any, Union, Tuple, List

import requests
import urllib3
from loguru import logger
from requests import Response
import subprocess
from functools import partial
subprocess.Popen = partial(subprocess.Popen, encoding='utf-8')
script_dir = path.dirname(path.abspath(__file__))

# logger.add('app.log', rotation='10 MB', retention=5)

# ------------------------ 模块加载区 --------------------------
# 1. 获取当前脚本的绝对路径
current_script = os.path.abspath(__file__)
# 2. 定位根目录（根据实际结构调整层级）
# 假设脚本在根目录的子目录（如 src/）中，根目录是当前脚本目录的上层目录
root_dir = os.path.dirname(os.path.dirname(current_script))
# 3. 将根目录添加到模块搜索路径（确保只添加一次）
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)  # 插入到最前面，优先搜索根目录
try:
    from RnlProxy import RnlProxy
except:
    RnlProxy = None
    logger.error('未检测到 RnlProxy.py 模块，使用默认ip')
try:
    from rnl_push import rnl_push
except:
    try:
        import notify
        if hasattr(notify, 'send'):
            notify.sendNotify = notify.send
        rnl_push = notify
    except:
        rnl_push = None
        logger.error('未检测到 rnl_push.py、notify.py 模块，不进行消息推送')
# ------------------------ 模块加载区 --------------------------

class Utils:
    @staticmethod
    def r_sleep(s=1, e=None):
        """
        随机休眠函数，支持更灵活的参数设置

        参数:
            s: 休眠时间下限（秒），默认为1
            e: 休眠时间上限（秒），默认为 s+1

        用法:
            r_sleep()       # 随机休眠1-2秒
            r_sleep(3)      # 随机休眠3-4秒
            r_sleep(2, 5)   # 随机休眠2-5秒
        """
        # 如果只传入一个参数，则 e 默认为 s+1
        if e is None:
            e = s + 1

        # 确保下限不大于上限
        if s > e:
            s, e = e, s  # 自动交换顺序，避免错误

        # 生成随机休眠时间并休眠
        sleep_time = random.randint(s, e)
        time.sleep(sleep_time)
        return sleep_time  # 可选：返回实际休眠时间


    @staticmethod
    def dict_cookie_to_string(cookie_dict):
        """
        将字典形式的 cookie 转换为字符串
        :param cookie_dict: 包含 cookie 信息的字典
        :return: 转换后的 cookie 字符串
        """
        cookie_list = []
        for key, value in cookie_dict.items():
            cookie_list.append(f"{key}={value}")
        return "; ".join(cookie_list)

    @staticmethod
    def string_cookie_to_dict(cookie_str):
        """
        将 Cookie 字符串转换为字典
        :param cookie_str: 格式为 "key1=value1; key2=value2" 的 Cookie 字符串
        :return: 转换后的字典，格式为 {key1: value1, key2: value2}
        """
        cookie_dict = {}
        # 处理空字符串情况
        if not cookie_str:
            return cookie_dict

        # 按分号分隔 Cookie 键值对（处理可能的空格，如 "key=val; key2=val2"）
        cookie_pairs = [pair.strip() for pair in cookie_str.split(';') if pair.strip()]

        for pair in cookie_pairs:
            # 按第一个等号分割（兼容值中包含等号的情况，如 "token=abc=123"）
            key_value = pair.split('=', 1)
            if len(key_value) == 2:
                key, value = key_value
                cookie_dict[key.strip()] = value.strip()
            else:
                # 处理异常格式（如仅有 key 无 value，如 "isLogin"）
                cookie_dict[key_value[0].strip()] = ""

        return cookie_dict


class RnlRequest:
    def __init__(self, proxies=None, cookies=None, headers=None):
        """ 20251012 """
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        self.session = requests.session()
        self.session.trust_env = False
        self.session.verify = False
        self.last_response: Optional[Response] = None  # 存储最近一次响应

        if proxies:
            self.session.proxies.update(proxies)

        # 基础请求头，默认带常见浏览器UA
        self._base_headers = headers or {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36',
        }

        self.update_cookies(cookies)

    @property
    def status_code(self) -> Optional[int]:
        """快捷获取状态码（同requests.Response.status_code）"""
        return self.last_response.status_code if self.last_response else None

    @property
    def ok(self) -> bool:
        """判断请求是否成功（状态码2xx），同requests.Response.ok"""
        return 200 <= self.status_code < 300 if self.status_code else False

    @property
    def json(self) -> Any:
        """快捷获取JSON数据（自动处理解析异常）"""
        if not self.last_response:
            return None
        try:
            return self.last_response.json()
        except (ValueError, TypeError):
            return None  # 解析失败返回None

    @property
    def text(self) -> Optional[str]:
        """快捷获取文本内容"""
        return self.last_response.text if self.last_response else None

    @property
    def content(self) -> Optional[bytes]:
        """快捷获取二进制内容"""
        return self.last_response.content if self.last_response else None

    @property
    def headers(self) -> Optional[Dict[str, str]]:
        """快捷获取响应头"""
        return dict(self.last_response.headers) if self.last_response else None


    def update_cookies(self, cookies: Union[str, dict, None]) -> None:
        """更新Cookie（支持字符串/字典）"""
        if not cookies:
            return
        if isinstance(cookies, str):
            cookies = dict(
                item.strip().split('=', 1)
                for item in cookies.split(';')
                if '=' in item.strip()
            )
        elif not isinstance(cookies, dict):
            return
        self.session.cookies.update(cookies)

    def get_cookies(self) -> Dict[str, str]:
        """获取当前会话的Cookie（字典形式）"""
        return self.session.cookies.get_dict()

    def update_headers(self, headers: Dict[str, str]) -> None:
        """更新基础请求头（会与原有头合并，新值覆盖旧值）"""
        self._base_headers.update(headers)

    def raise_for_status(self) -> None:
        """若请求失败（非2xx），主动抛出异常（同requests.Response.raise_for_status）"""
        if self.last_response:
            self.last_response.raise_for_status()

    def request(
            self,
            method: str,
            url: str,
            params: Optional[Union[Dict[str, Any], bytes]] = None,
            data: Optional[Union[Dict[str, Any], str, bytes, List[Tuple[str, Any]]]] = None,
            json: Optional[Any] = None,
            headers: Optional[Dict[str, str]] = None,
            cookies: Optional[Union[Dict[str, str]]] = None,
            files: Optional[Union[Dict[str, Any], List[Tuple[str, Any]]]] = None,
            auth: Optional[Union[Tuple[str, str]]] = None,
            timeout: Optional[Union[float, Tuple[float, float]]] = None,
            allow_redirects: bool = True,
            proxies: Optional[Dict[str, str]] = None,
            hooks: Optional[Dict[str, Any]] = None,
            stream: Optional[bool] = None,
            verify: Optional[Union[bool, str]] = None,
            cert: Optional[Union[str, Tuple[str, str]]] = None, **kwargs
    ) -> Optional[Response]:
        """发送请求，参数与原生requests保持一致"""
        self.last_response = None
        # 合并基础头和请求头（请求头优先级更高）
        request_headers = {**self._base_headers, **(headers or {})}

        try:
            resp = self.session.request(
                method=method.upper(),
                url=url,
                params=params,
                data=data,
                json=json,
                headers=request_headers,
                cookies=cookies,
                files=files,
                auth=auth,
                timeout=timeout,
                allow_redirects=allow_redirects,
                proxies=proxies,
                hooks=hooks,
                stream=stream,
                verify=verify if verify is not None else self.session.verify,
                cert=cert,
                **kwargs
            )
            self.last_response = resp
            return resp
        except requests.RequestException as e:
            if hasattr(e, 'response') and e.response:
                self.last_response = e.response
                return e.response
            return None

    def get(
            self,
            url: str,
            params: Optional[Union[Dict[str, Any], bytes]] = None,
            data: Optional[Union[Dict[str, Any], str, bytes, List[Tuple[str, Any]]]] = None,
            json: Optional[Any] = None,
            headers: Optional[Dict[str, str]] = None,
            cookies: Optional[Union[Dict[str, str]]] = None,
            files: Optional[Union[Dict[str, Any], List[Tuple[str, Any]]]] = None,
            auth: Optional[Union[Tuple[str, str]]] = None,
            timeout: Optional[Union[float, Tuple[float, float]]] = None,
            allow_redirects: bool = True,
            proxies: Optional[Dict[str, str]] = None,
            hooks: Optional[Dict[str, Any]] = None,
            stream: Optional[bool] = None,
            verify: Optional[Union[bool, str]] = None,
            cert: Optional[Union[str, Tuple[str, str]]] = None, **kwargs
    ) -> Optional[Response]:
        return self.request(
            method='GET',
            url=url,
            params=params,
            data=data,
            json=json,
            headers=headers,
            cookies=cookies,
            files=files,
            auth=auth,
            timeout=timeout,
            allow_redirects=allow_redirects,
            proxies=proxies,
            hooks=hooks,
            stream=stream,
            verify=verify,
            cert=cert,
            **kwargs
        )

    def post(
            self,
            url: str,
            data: Optional[Union[Dict[str, Any], str, bytes, List[Tuple[str, Any]]]] = None,
            json: Optional[Any] = None,
            params: Optional[Union[Dict[str, Any], bytes]] = None,
            headers: Optional[Dict[str, str]] = None,
            cookies: Optional[Union[Dict[str, str]]] = None,
            files: Optional[Union[Dict[str, Any], List[Tuple[str, Any]]]] = None,
            auth: Optional[Union[Tuple[str, str]]] = None,
            timeout: Optional[Union[float, Tuple[float, float]]] = None,
            allow_redirects: bool = True,
            proxies: Optional[Dict[str, str]] = None,
            hooks: Optional[Dict[str, Any]] = None,
            stream: Optional[bool] = None,
            verify: Optional[Union[bool, str]] = None,
            cert: Optional[Union[str, Tuple[str, str]]] = None, **kwargs
    ) -> Optional[Response]:
        return self.request(
            method='POST',
            url=url,
            params=params,
            data=data,
            json=json,
            headers=headers,
            cookies=cookies,
            files=files,
            auth=auth,
            timeout=timeout,
            allow_redirects=allow_redirects,
            proxies=proxies,
            hooks=hooks,
            stream=stream,
            verify=verify,
            cert=cert,
            **kwargs
        )

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.session.close()


class RNL:
    def __init__(self, user_token, proxies=None):
        self.userAgent = 'Mozilla/5.0 (Linux; Android 14; 23117RK66C Build/UKQ1.230804.001; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/142.0.7444.172 Mobile Safari/537.36 XWEB/1420045 MMWEBSDK/20240404 MMWEBID/3531 MicroMessenger/8.0.49.2600(0x2800313D) WeChat/arm64 Weixin Android Tablet NetType/WIFI Language/zh_CN ABI/arm64 MiniProgramEnv/android'
        self.user_token = user_token
        self.rr = RnlRequest(proxies=proxies, headers={'User-Agent': self.userAgent, 'user-token': self.user_token})

    # 获取用户信息
    def getMemberDetail(self):
        headers = {
            'Host': 'sss-web.tastientech.com',
            'Connection': 'keep-alive',
            'charset': 'utf-8',
            'channel': '1',
            'content-type': 'application/json',
            'version': '3.50.0',
            'Referer': 'https://servicewechat.com/wx557473f23153a429/482/page-frame.html',
        }
        try:
            # 发送GET请求
            response = self.rr.get(
                url='https://sss-web.tastientech.com/api/intelligence/member/getMemberDetail/sign',
                headers=headers,
                timeout=10
            )
            # 检查请求是否成功（状态码200）
            response.raise_for_status()
            # 解析JSON响应
            response_data = response.json()
            # 提取phone参数（逐层判断，避免KeyError）
            result = response_data.get('result', {})
            phone = result.get('phone')
            return phone
        except Exception as e:
            print(f"提取phone参数时发生未知错误: {e}")
            return None

    def sign(self, memberPhone):
        headers = {
            'Host': 'sss-web.tastientech.com',
            'Connection': 'keep-alive',
            # 'Content-Length': '78',
            'charset': 'utf-8',
            'channel': '1',
            'content-type': 'application/json',
            # 'Accept-Encoding': 'gzip,compress,br,deflate',
            'version': '3.49.2',
            'gray-shop-id': '18207',
            'Referer': 'https://servicewechat.com/wx557473f23153a429/481/page-frame.html',
        }
        json_data = {
            'activityId': 66,
            'memberName': '',
            'memberPhone': memberPhone,
        }
        response = self.rr.post('https://sss-web.tastientech.com/api/sign/member/signV2/sign', headers=headers,
                                 json=json_data)
        json = response.json()
        if json['code'] == 200:
            rewardInfoList = json.get('result', {}).get('rewardInfoList', [])
            if len(rewardInfoList) > 0:
                rewardInfo = rewardInfoList[0]
                logger.success(f"签到成功：{rewardInfo['rewardName']}")
                return True, f"签到成功：{rewardInfo['rewardName']}"
        else:
            logger.error(f"签到失败：{json['msg']}")
            return False, f"签到失败：{json['msg']}"

    # 获取积分
    def myPoint(self):
        headers = {
            'Host': 'sss-web.tastientech.com',
            'Connection': 'keep-alive',
            # 'Content-Length': '2',
            'charset': 'utf-8',
            'channel': '1',
            # Already added when you pass json=
            # 'content-type': 'application/json',
            # 'Accept-Encoding': 'gzip,compress,br,deflate',
            'version': '3.50.0',
            'Referer': 'https://servicewechat.com/wx557473f23153a429/482/page-frame.html',
        }
        json_data = {}
        response = self.rr.post('https://sss-web.tastientech.com/api/wx/point/myPoint', headers=headers,
                                 json=json_data)
        json = response.json()
        if json['code'] == 200:
            return json.get('result', {}).get('point')
        return None

    def main(self):
        phone = self.getMemberDetail()
        if not phone:
            print("响应中未找到phone参数")
            return None
        is_sign, msg = self.sign(memberPhone=phone)

        point = self.myPoint()
        logger.info(f'当前积分：{point}')
        return is_sign, msg

def read_users_from_env():
    """从环境变量读取用户信息，一行一个用户"""
    users_env = os.getenv('TA_S_TIENTECH', '')
    users = []

    # 按行分割用户信息
    for line in users_env.strip().split('\n'):
        if line.strip():
            # 按分隔符分割备注、token
            parts = line.replace('#', ',').replace(' ', ',').split(',')
            if len(parts) >= 2:
                user_info = {
                    'username': parts[0].strip(),
                    'user_token': parts[1].strip(),
                }
                users.append(user_info)

    return users


if __name__ == "__main__":
    """主函数"""
    users = read_users_from_env()
    if not users:
        print("未配置用户信息，请设置 TA_S_TIENTECH 环境变量")
        exit()

    print(f"共读取到 {len(users)} 个用户")
    print('等待30-600s...')
    # Utils.r_sleep(30, 600)

    # 代理
    rnlProxy = None
    if RnlProxy:
        rnlProxy = RnlProxy()

    for i, user in enumerate(users, 1):
        username = user['username']
        print(f"\n正在为第 {i} 个用户 {username} 签到...")

        proxies = None
        if rnlProxy:
            proxies = rnlProxy.get_valid_proxy()

        success, msg = RNL(user_token=user['user_token'], proxies=proxies).main()
        if rnl_push:
            rnl_push.sendNotify('塔斯丁', msg)
