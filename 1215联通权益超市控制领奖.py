#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""

专业优化版 — 联通权益超市自动任务脚本
Version: 3.0-Pro（精简领奖控制版）

【原作者信息】
yaohuo：新人
ID: 12996

【修改】
yaohuo：来姑娘坐我鞭上
ID: 38445

【青龙环境变量配置说明】
1. 配置方式：设置环境变量：UNICOM_ACCOUNTS
2. 账号格式（支持多账号，每行一个）：
   格式1（推荐）：手机号#ecs_token
     示例：13012345678#abcdef1234567890abcdef1234567890
   格式2：手机号#token_online#appid
     示例：13012345678#xyz1234567890#1234567890abcdef

【领奖功能开关配置（脚本内修改）】
通过下方 AUTO_GRANT_REWARD 变量控制：
1: 开启自动领奖（默认）
2: 关闭自动领奖
"""

import os
import sys
import time
import json
import logging
import requests
from urllib.parse import urlparse, parse_qs
from datetime import datetime
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from pathlib import Path  # 新增（日志目录创建）


# ======================
# 领奖功能开关（脚本内直接配置）
# ======================
AUTO_GRANT_REWARD = 2  # 1=开启自动领奖，2=关闭自动领奖
logging.info(f"自动领奖功能状态: {'开启' if AUTO_GRANT_REWARD == 1 else '关闭'}")


# ======================
# 新增：通知配置（不影响主程序）
# ======================
CONFIG = {
    "log_dir": "./unicom_logs",  # 兼容原日志，新增文件日志
    # 自定义通知配置（非青龙环境使用）
    "custom_notify": {
        "enable": True,        # 是否启用自定义通知
        "type": "dingtalk",    # 支持 dingtalk(钉钉)/wechat(企业微信)/serverchan(Server酱)
        "webhook": "",         # 替换为你的webhook地址
        "secret": ""           # 钉钉/企业微信机器人密钥（可选）
    }
}

# ======================
# 新增：适配青龙通知函数（不影响主程序）
# ======================
try:
    from notify import send as qinglong_send  # 青龙新版
except ImportError:
    try:
        from utils import send as qinglong_send  # 青龙旧版
    except:
        qinglong_send = None  # 非青龙环境


# ======================
# 原作者：日志格式（带毫秒）
# ======================
class MsFormatter(logging.Formatter):
    def formatTime(self, record, datefmt=None):
        dt = datetime.fromtimestamp(record.created)
        s = dt.strftime("%Y-%m-%d %H:%M:%S.%f")
        return s[:-3]


# ======================
# 原作者：基础日志配置 + 新增文件日志（不影响控制台输出）
# ======================
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(message)s')
for h in logging.getLogger().handlers:
    h.setFormatter(MsFormatter('[%(asctime)s] %(message)s'))

# 新增：文件日志（兼容原控制台日志，不影响主程序）
Path(CONFIG["log_dir"]).mkdir(exist_ok=True)
file_handler = logging.FileHandler(
    Path(CONFIG["log_dir"]) / f"unicom_task_{datetime.now().strftime('%Y%m%d')}.log",
    encoding="utf-8"
)
file_handler.setFormatter(MsFormatter('[%(asctime)s] %(message)s'))
logging.getLogger().addHandler(file_handler)


# ======================
# 原作者：共享 Session
# ======================
sess = requests.Session()
adapter = HTTPAdapter(max_retries=Retry(total=3, backoff_factor=0.3))
sess.mount("http://", adapter)
sess.mount("https://", adapter)


# ======================
# 原作者：统一 UA
# ======================
def ua():
    return {
        "User-Agent":
            "Mozilla/5.0 (Linux; Android 10; Redmi K30 Pro Build/QKQ1.191117.002; wv) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/100.0.4896.58 "
            "Mobile Safari/537.36 unicom{version:android@11.0500}",
        "Accept": "*/*",
    }


# ======================
# 新增：自定义通知函数（不影响主程序）
# ======================
def send_custom_notify(title, message):
    """
    自定义通知：支持钉钉/企业微信/Server酱
    """
    if not CONFIG["custom_notify"]["enable"] or not CONFIG["custom_notify"]["webhook"]:
        logging.warning("⚠️ 自定义通知未启用或未配置webhook")
        return

    notify_type = CONFIG["custom_notify"]["type"].lower()
    webhook = CONFIG["custom_notify"]["webhook"]
    secret = CONFIG["custom_notify"]["secret"]

    try:
        if notify_type == "dingtalk":
            # 钉钉机器人（支持加签）
            import hmac
            import hashlib
            import base64
            from urllib.parse import quote_plus
            timestamp = str(round(time.time() * 1000))
            sign = ""
            if secret:
                secret_enc = secret.encode('utf-8')
                string_to_sign = f"{timestamp}\n{secret}"
                string_to_sign_enc = string_to_sign.encode('utf-8')
                hmac_code = hmac.new(secret_enc, string_to_sign_enc, digestmod=hashlib.sha256).digest()
                sign = quote_plus(base64.b64encode(hmac_code))
            url = f"{webhook}&timestamp={timestamp}&sign={sign}" if sign else webhook
            data = {
                "msgtype": "text",
                "text": {"content": f"{title}\n\n{message}"}
            }
            resp = sess.post(url, json=data, timeout=10)
            resp.raise_for_status()
            logging.info("✅ 钉钉自定义通知发送成功")

        elif notify_type == "wechat":
            # 企业微信机器人
            data = {
                "msgtype": "text",
                "text": {"content": f"{title}\n\n{message}"}
            }
            resp = sess.post(webhook, json=data, timeout=10)
            resp.raise_for_status()
            logging.info("✅ 企业微信自定义通知发送成功")

        elif notify_type == "serverchan":
            # Server酱（Turbo版）
            data = {
                "title": title,
                "desp": message
            }
            resp = sess.post(webhook, json=data, timeout=10)
            resp.raise_for_status()
            logging.info("✅ Server酱自定义通知发送成功")

        else:
            logging.error(f"⚠️ 不支持的通知类型：{notify_type}")

    except Exception as e:
        logging.error(f"❌ 自定义通知发送失败：{e}")


# ======================
# 原作者：主类（修复name未定义错误，保留精细化收集）
# ======================
class CUAPI:
    def __init__(self, accounts):
        # 原作者代码完全保留
        self.accounts = accounts
        self.GrantPrize = True
        # 新增：结果收集（不影响原逻辑）
        self.account_results = []  # 收集每个账号的执行结果
        self.prize_summary = {}    # 抽奖结果汇总（备用）

    # ======================
    # 原作者：✨ 重构 do_send（专业版 3.0）
    # 完全保留，无任何修改
    # ======================
    def do_send(self, url, method="GET", headers=None,
                params=None, data=None, timeout=10,
                raw=False, allow_redirects=True):

        try:
            resp = sess.request(
                method=method,
                url=url,
                headers=headers,
                params=params,
                json=None if (data and "token_online" in str(data)) else data,
                data=data if (data and "token_online" in str(data)) else None,
                timeout=timeout,
                allow_redirects=allow_redirects
            )
        except Exception as e:
            logging.error(f"请求失败: {e}")
            return None

        # raw 直接返回响应对象
        if raw:
            return resp

        if resp.status_code == 302:
            return resp

        try:
            return resp.json()
        except:
            logging.error("响应非 JSON 格式")
            return None

    # ======================
    # 原作者：登录 — token_online
    # 完全保留，无任何修改
    # ======================
    def login_with_token_online(self, phone, tok, appid):
        url = "https://m.client.10010.com/mobileService/onLine.htm"

        data = {
            "reqtime": str(int(time.time() * 1000)),
            "netWay": "Wifi",
            "version": "android@11.0000",
            "token_online": tok,
            "appId": appid,
            "deviceModel": "Mi10",
            "step": "welcome",
            "androidId": "e1d2c3b4a5f6"
        }

        resp = self.do_send(url, method="POST", headers=ua(), data=data)
        if resp and resp.get("ecs_token"):
            logging.info(f"{phone} token 登录成功")
            return resp["ecs_token"]

        logging.error(f"{phone} token 登录失败")
        return None

    # ======================
    # 原作者：获取 ticket（核心修复点）
    # 完全保留，无任何修改
    # ======================
    def get_ticket(self, ecs_token):
        """
        使用联通官方 H5 openPlatLine 跳转链路强制获取 ticket
        此链路比 openPlatLineNew 更稳定，token_online 登录也可使用
        """

        url = (
            "https://m.client.10010.com/mobileService/openPlatform/"
            "openPlatLine.htm"
        )

        headers = {
            "User-Agent":
                "Mozilla/5.0 (Linux; Android 10; MI 10) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 "
                "Chrome/108.0.5359.128 Mobile Safari/537.36 "
                "unicom{version:android@11.0500}",
            "X-Requested-With": "com.sinovatech.unicom.ui",
            "Origin": "https://img.client.10010.com",
            "Referer": "https://img.client.10010.com/",
            "Cookie": f"ecs_token={ecs_token}",
        }

        params = {
            "to_url": "https://contact.bol.wo.cn/market",
            "reqtime": str(int(time.time() * 1000)),
            "version": "android@11.0500"
        }

        # 强制获取响应，不自动解析
        resp = self.do_send(
            url, method="GET",
            headers=headers,
            params=params,
            raw=True,
            allow_redirects=False
        )

        if not resp:
            logging.error("❌ ticket 请求失败")
            return None

        # 必须要带 Location 才行
        loc = resp.headers.get("Location")
        if not loc:
            logging.error("❌ 联通拒绝跳转（无 Location）")
            return None

        qs = parse_qs(urlparse(loc).query)
        ticket = qs.get("ticket", [None])[0]

        return ticket

    # ======================
    # 原作者：获取 userToken
    # 完全保留，无任何修改
    # ======================
    def get_userToken(self, ticket):
        url = f"https://backward.bol.wo.cn/prod-api/auth/marketUnicomLogin?ticket={ticket}"
        resp = self.do_send(url, method="POST", headers=ua())
        return resp.get("data", {}).get("token") if resp else None

    # ======================
    # 原作者：获取任务列表
    # 完全保留，无任何修改
    # ======================
    def get_tasks(self, ecs_token, userToken):
        url = (
            "https://backward.bol.wo.cn/prod-api/promotion/activityTask/"
            "getAllActivityTasks?activityId=12"
        )

        headers = ua()
        headers["Authorization"] = f"Bearer {userToken}"
        headers["Cookie"] = f"ecs_token={ecs_token}"

        resp = self.do_send(url, headers=headers)
        if not resp:
            return []

        return resp.get("data", {}).get("activityTaskUserDetailVOList", [])

    # ======================
    # 修复核心错误：name未定义 → 改为task_name + 保留精细化任务记录
    # ======================
    def run_task(self, task, userToken):
        # 原作者逻辑：先获取任务名称（修复name未定义的关键）
        task_name = task.get("name", "未知任务")
        # 新增：记录任务详情
        task_result = {
            "name": task_name,
            "status": "unknown",
            "reason": ""
        }
        
        target = int(task.get("triggerTime", 1))
        done = int(task.get("triggeredTime", 0))

        # 修复：把name改成task_name（原错误根源）
        if "购买" in task_name or "秒杀" in task_name:
            logging.info(f"[跳过复杂任务] {task_name}")
            task_result["status"] = "skip"
            task_result["reason"] = "复杂任务跳过"
            return task_result

        if done >= target:
            logging.info(f"任务已完成：{task_name}")
            task_result["status"] = "done"
            task_result["reason"] = "任务已完成无需执行"
            return task_result

        # 任务类型判断（基于task_name，原逻辑保留）
        if "浏览" in task_name or "查看" in task_name:
            api = "checkView"
        elif "分享" in task_name:
            api = "checkShare"
        else:
            logging.info(f"无法识别任务类型：{task_name}")
            task_result["status"] = "unknown"
            task_result["reason"] = "无法识别任务类型"
            return task_result

        url = f"https://backward.bol.wo.cn/prod-api/promotion/activityTaskShare/{api}?checkKey={task.get('param1')}"
        headers = ua()
        headers["Authorization"] = f"Bearer {userToken}"

        resp = self.do_send(url, method="POST", headers=headers)
        if resp and resp.get("code") == 200:
            logging.info(f"任务完成：{task_name}")
            task_result["status"] = "success"
            task_result["reason"] = "任务执行成功"
        else:
            logging.error(f"任务失败：{task_name}")
            task_result["status"] = "fail"
            task_result["reason"] = f"响应码：{resp.status_code if resp else '请求失败'}"

        return task_result

    # ======================
    # 原作者：检查抽奖池是否放水
    # 完全保留，无任何修改
    # ======================
    def check_raffle(self, userToken):
        url = (
            "https://backward.bol.wo.cn/prod-api/promotion/home/"
            "raffleActivity/prizeList?id=12"
        )

        headers = ua()
        headers["Authorization"] = f"Bearer {userToken}"

        resp = self.do_send(url, method="POST", headers=headers)
        if not resp:
            return False

        # 判断是否有“月卡”、“月会员”等奖品
        prize_list = resp.get("data", [])
        has_live = any(("月" in p.get("name", "")) for p in prize_list)

        return has_live

    # ======================
    # 原作者：抽奖次数获取 + 循环抽奖 + 保留抽奖详情
    # ======================
    def raffle(self, userToken):
        url = (
            "https://backward.bol.wo.cn/prod-api/promotion/home/"
            "raffleActivity/getUserRaffleCount?id=12"
        )

        headers = ua()
        headers["Authorization"] = f"Bearer {userToken}"

        resp = self.do_send(url, method="POST", headers=headers)
        if not resp:
            return 0, []

        count = resp.get("data", 0)
        logging.info(f"当前剩余抽奖次数：{count}")

        raffle_details = []  # 抽奖详情记录
        for _ in range(count):
            prize = self.raffle_once(userToken)
            raffle_details.append(prize)
            time.sleep(1)  # 给接口缓冲时间

        return count, raffle_details

    # ======================
    # 原作者：执行一次抽奖 + 保留奖品详情
    # ======================
    def raffle_once(self, userToken):
        url = (
            "https://backward.bol.wo.cn/prod-api/promotion/home/"
            "raffleActivity/userRaffle?id=12&channel="
        )

        headers = ua()
        headers["Authorization"] = f"Bearer {userToken}"

        resp = self.do_send(url, method="POST", headers=headers)
        if not resp:
            logging.error("抽奖请求失败")
            return "❌ 抽奖请求失败"

        if resp.get("code") != 200:
            logging.error("抽奖失败")
            return f"❌ 抽奖失败（响应码：{resp.get('code')}）"

        data = resp.get("data", {})
        prize = data.get("prizesName")
        msg = data.get("message", "")

        result = f"🎁 {prize or msg}"
        logging.info(f"抽奖结果：{result}")
        return result

    # ======================
    # 原作者：查询待领奖品
    # 完全保留，无任何修改
    # ======================
    def get_pending_prizes(self, userToken):
        url = "https://backward.bol.wo.cn/prod-api/promotion/home/raffleActivity/getMyPrize"

        headers = ua()
        headers["Authorization"] = f"Bearer {userToken}"

        data = {
            "id": 12,
            "type": 0,
            "page": 1,
            "limit": 100
        }

        resp = self.do_send(url, method="POST", headers=headers, data=data)
        if not resp:
            return []

        return resp.get("data", {}).get("list", [])

    # ======================
    # 原作者：自动领奖 + 保留领奖详情
    # ======================
    def grant_prize(self, userToken, recordId, prizeName):
        url = (
            "https://backward.bol.wo.cn/prod-api/promotion/home/"
            "raffleActivity/grantPrize?activityId=12"
        )

        headers = ua()
        headers["Authorization"] = f"Bearer {userToken}"
        headers["Content-Type"] = "application/json"

        resp = self.do_send(url, method="POST", headers=headers, data={"recordId": recordId})
        if resp and resp.get("code") == 200:
            logging.info(f"🎉 奖品领取成功：{prizeName}")
            return f"✅ 领奖成功：{prizeName}"
        else:
            logging.error(f"领奖失败：{prizeName}")
            return f"❌ 领奖失败：{prizeName}（响应码：{resp.get('code') if resp else '请求失败'}）"

    # ======================
    # 单账号完整流程 + 领奖开关控制
    # ======================
    def run_account(self, phone, ecs_token=None, token_online=None, appid=None):
        # 精细化结果记录（不影响原逻辑）
        account_result = {
            "phone": phone,
            "success": False,
            "message": "",
            "task_stats": {"success": 0, "fail": 0, "skip": 0, "done": 0, "unknown": 0},
            "task_details": {
                "success": [], 
                "fail": [],     
                "skip": [],     
                "done": [],     
                "unknown": []   
            },
            "raffle_count": 0,
            "raffle_details": [],
            "grant_details": []
        }

        logging.info(f"\n===== 开始处理账号：{phone} =====")

        try:
            # 登录逻辑（原作者代码完全保留）
            if ecs_token:
                final_token = ecs_token
            else:
                final_token = self.login_with_token_online(phone, token_online, appid)
                if not final_token:
                    account_result["message"] = "token登录失败"
                    self.account_results.append(account_result)
                    return

            # Ticket逻辑（原作者代码完全保留）
            ticket = self.get_ticket(final_token)
            if not ticket:
                logging.error("❌ 获取 ticket 失败")
                account_result["message"] = "获取ticket失败"
                self.account_results.append(account_result)
                return
            logging.info("✔ ticket 获取成功")

            # userToken逻辑（原作者代码完全保留）
            userToken = self.get_userToken(ticket)
            if not userToken:
                logging.error("❌ 获取 userToken 失败")
                account_result["message"] = "获取userToken失败"
                self.account_results.append(account_result)
                return
            logging.info("✔ userToken 获取成功")

            # 任务执行（原逻辑 + 精细化记录）
            tasks = self.get_tasks(final_token, userToken)
            for t in tasks:
                task_res = self.run_task(t, userToken)
                # 更新统计
                if task_res["status"] in account_result["task_stats"]:
                    account_result["task_stats"][task_res["status"]] += 1
                # 更新详情
                if task_res["status"] == "success":
                    account_result["task_details"]["success"].append(task_res["name"])
                elif task_res["status"] == "fail":
                    account_result["task_details"]["fail"].append(f"{task_res['name']}（{task_res['reason']}）")
                elif task_res["status"] == "skip":
                    account_result["task_details"]["skip"].append(f"{task_res['name']}（{task_res['reason']}）")
                elif task_res["status"] == "done":
                    account_result["task_details"]["done"].append(task_res["name"])
                elif task_res["status"] == "unknown":
                    account_result["task_details"]["unknown"].append(f"{task_res['name']}（{task_res['reason']}）")

            # 抽奖逻辑（原作者代码 + 详情记录）
            logging.info("检查抽奖池放水情况...")
            if self.check_raffle(userToken):
                logging.info("✔ 抽奖池已放水，开始抽奖")
                raffle_count, raffle_details = self.raffle(userToken)
                account_result["raffle_count"] = raffle_count
                account_result["raffle_details"] = raffle_details
            else:
                logging.info("❌ 今日未放水，跳过抽奖")
                account_result["raffle_details"] = ["今日未放水，跳过抽奖"]

            # 领奖逻辑（增加开关控制）
            if AUTO_GRANT_REWARD == 1:  # 开启自动领奖
                pending = self.get_pending_prizes(userToken)
                if pending:
                    logging.info(f"发现 {len(pending)} 个待领取奖品，开始领取...")
                    for item in pending:
                        recordId = item.get("id")
                        prizeName = item.get("prizesName")
                        grant_res = self.grant_prize(userToken, recordId, prizeName)
                        account_result["grant_details"].append(grant_res)
                else:
                    logging.info("暂无待领取奖品")
                    account_result["grant_details"] = ["暂无待领取奖品"]
            else:  # 关闭自动领奖
                logging.info("已关闭自动领奖功能，跳过领奖流程")
                account_result["grant_details"] = ["自动领奖功能已关闭"]

            # 标记成功
            account_result["success"] = True
            account_result["message"] = "执行完成"
            logging.info(f"===== 账号 {phone} 处理完成 =====\n")

        except Exception as e:
            account_result["message"] = f"执行异常: {str(e)}"
            logging.error(f"账号 {phone} 执行异常: {e}")
        finally:
            self.account_results.append(account_result)

    # ======================
    # 原作者：主程序入口 + 通知调用（无修改）
    # ======================
    def run(self):
        try:
            for acc in self.accounts:
                parts = acc.split("#")
                phone = parts[0]

                if len(parts) == 2:
                    self.run_account(phone, ecs_token=parts[1])
                elif len(parts) >= 3:
                    self.run_account(phone, token_online=parts[1], appid=parts[2])

                time.sleep(3)  # 原作者代码保留
        except Exception as e:
            logging.error(f"处理账号列表全局异常：{e}")
            self.account_results.append({
                "phone": "全局异常",
                "success": False,
                "message": f"脚本执行异常：{str(e)}",
                "task_stats": {"success": 0, "fail": 0, "skip": 0, "done": 0, "unknown": 0},
                "task_details": {"success": [], "fail": [], "skip": [], "done": [], "unknown": []},
                "raffle_count": 0,
                "raffle_details": [],
                "grant_details": []
            })
        finally:
            logging.info("===== 开始执行通知流程 =====")
            self.send_qinglong_notification()

    # ======================
    # 精细化通知函数（无修改，仅依赖收集的详情）
    # ======================
    def send_qinglong_notification(self):
        """
        精细化通知：任务详情+抽奖详情+领奖详情
        """
        logging.info(f"===== 进入通知函数 ===== | 账号结果数量: {len(self.account_results)}")

        # 兜底处理空结果
        if not self.account_results:
            logging.warning("⚠️ 无任何账号执行结果")
            self.account_results = [{
                "phone": "无有效账号",
                "success": False,
                "message": "未配置UNICOM_ACCOUNTS或配置格式错误",
                "task_stats": {"success": 0, "fail": 0, "skip": 0, "done": 0, "unknown": 0},
                "task_details": {"success": [], "fail": [], "skip": [], "done": [], "unknown": []},
                "raffle_count": 0,
                "raffle_details": [],
                "grant_details": []
            }]

        # 全局统计 + 失败判定
        try:
            success_count = sum(1 for res in self.account_results if res.get('success', False))
            failure_count = len(self.account_results) - success_count
            
            # 失败判定逻辑
            has_fail = False
            if failure_count > 0:
                has_fail = True
            else:
                for res in self.account_results:
                    if res.get('task_stats', {}).get('fail', 0) > 0:
                        has_fail = True
                        break

            # 动态标题
            if has_fail:
                title = "📱 联通权益超市任务通知【含失败】"
            else:
                title = "📱 联通权益超市任务通知【全部成功】"

        except Exception as e:
            logging.error(f"统计全局数据失败: {e}")
            success_count = failure_count = 0
            title = "📱 联通权益超市任务通知【统计异常】"

        # 构建通知内容
        message = []
        try:
            # 全局汇总
            message.append("📊 全局执行汇总")
            message.append(f"✅ 成功账号：{success_count}  |  ❌ 失败账号：{failure_count}")
            message.append("=" * 30)

            # 逐个账号详情
            for index, res in enumerate(self.account_results, 1):
                phone = res.get('phone', '未知手机号')
                status = "✅ 成功" if res.get('success', False) else "❌ 失败"
                msg = res.get('message', '无详情')

                # 账号基础信息
                message.append(f"\n{index}. 📱 手机号：{phone}")
                message.append(f"   📈 执行状态：{status}")
                message.append(f"   💡 执行说明：{msg}")

                # 任务统计 + 详情
                task_stats = res.get('task_stats', {})
                message.append(f"\n   📋 任务统计：")
                message.append(f"   成：{task_stats.get('success',0)} | 败：{task_stats.get('fail',0)} | 跳：{task_stats.get('skip',0)} | 完：{task_stats.get('done',0)} | 未知：{task_stats.get('unknown',0)}")
                
                task_details = res.get('task_details', {})
                if task_details.get('success'):
                    message.append(f"  ✅ 成功任务：{', '.join(task_details['success'])}")
                if task_details.get('fail'):
                    message.append(f"  ❌ 失败任务：{', '.join(task_details['fail'])}")
                if task_details.get('skip'):
                    message.append(f"  ⏭️  跳过任务：{', '.join(task_details['skip'])}")
                if task_details.get('done'):
                    message.append(f"  ✔ 已完成任务：{', '.join(task_details['done'])}")
                if task_details.get('unknown'):
                    message.append(f"  ❓ 未知任务：{', '.join(task_details['unknown'])}")

                # 抽奖详情
                message.append(f"\n   🎰 抽奖详情：")
                raffle_count = res.get('raffle_count', 0)
                raffle_details = res.get('raffle_details', [])
                message.append(f"       抽奖次数：{raffle_count}")
                message.append(f"       抽奖结果：{'; '.join(raffle_details)}")

                # 领奖详情
                message.append(f"   🎁 领奖详情：")
                grant_details = res.get('grant_details', [])
                message.append(f"       {'；'.join(grant_details)}")

                message.append("-" * 30)

            # 执行时间
            message.append(f"\n🕒 执行完成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            message_str = "\n".join(message)
            logging.info(f"精细化通知内容构建完成 | 内容长度：{len(message_str)}")

        except Exception as e:
            message_str = f"⚠️ 通知内容构建失败：{str(e)}\n账号结果：{json.dumps(self.account_results, ensure_ascii=False, indent=2)}"
            logging.error(f"构建通知内容异常: {e}")

        # 优先青龙通知
        notify_success = False
        if qinglong_send and callable(qinglong_send):
            try:
                qinglong_send(title, message_str)
                logging.info("✅ 调用青龙通知函数发送成功")
                notify_success = True
            except Exception as e:
                logging.error(f"⚠️ 青龙通知发送失败：{str(e)}")

        # 自定义通知
        if not notify_success and CONFIG["custom_notify"]["enable"]:
            logging.info("📤 尝试使用自定义通知渠道发送...")
            send_custom_notify(title, message_str)

        # 兜底打印
        if not notify_success and not CONFIG["custom_notify"]["enable"]:
            logging.info("⚠️ 未配置任何通知渠道，以下是精细化通知内容：")
            logging.info(message_str)


# ======================
# 原作者：入口（完全保留，无任何修改）
# ======================
if __name__ == "__main__":
    raw = os.getenv("UNICOM_ACCOUNTS", "").strip()

    if not raw:
        print("❌ 未设置环境变量 UNICOM_ACCOUNTS")
        print("示例：")
        print("  手机号#ecs_token")
        print("  手机号#token_online#appid")
        sys.exit(1)

    accounts = [line for line in raw.splitlines() if line.strip()]
    CUAPI(accounts).run()