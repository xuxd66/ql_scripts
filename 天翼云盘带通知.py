import os
import re
import rsa
import time
import random
import base64
import requests
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter
from datetime import datetime, timedelta, timezone

try:
    import env
    # windows 本地测试
except ImportError:
    pass

# 添加：开始随机延迟（0-1800秒）
random_delay = random.randint(0, 1800)
print(f"随机延迟 {random_delay} 秒 ({random_delay//60}分{random_delay%60}秒)后开始签到...")
time.sleep(random_delay)
print("开始执行签到任务...\n")

# 导入青龙面板的通知模块
try:
    from notify import send
    QL_NOTIFY = True
except ImportError:
    QL_NOTIFY = False
    print("未找到青龙面板的notify模块，将只会打印结果")

# ... 保持原有代码不变 ...

class TG:
    def __init__(self, token, chat_id, retry=2, timeout=5):
        # 检测是否为空
        if not token or not chat_id:
            raise ValueError("Token and chat_id cannot be empty")

        self.token = token
        self.chat_id = chat_id
        self.retry = retry
        self.timeout = timeout
        self.base = f"https://api.telegram.org/bot{token}"

    # 基础请求函数（带自动重试）
    def _post(self, method, data=None, files=None):
        url = f"{self.base}/{method}"
        for i in range(self.retry + 1):
            try:
                resp = requests.post(url, data=data, files=files, timeout=self.timeout)
                return resp.json()
            except Exception as e:
                if i == self.retry:
                    print(f"Telegram API 请求失败,{e}")
                    return {"ok": False, "error": str(e)}
                print(f"{e}\nTelegram API 请求失败，正在第 {i + 1} 次重试...")
                time.sleep(1)
        return None

    # 发文字
    def send_text(self, text, parse_mode=None):
        data = {
            "chat_id": self.chat_id,
            "text": text
        }
        if parse_mode:
            data["parse_mode"] = parse_mode
        return self._post("sendMessage", data=data)

    def send_markdown(self, text):
        return self.send_text(text, "Markdown")


class Ecloud:
    globals()["UA"] = 'Mozilla/5.0'
    globals()["MODEL"] = "SM-G930K"
    BI_RM = list("0123456789abcdefghijklmnopqrstuvwxyz")
    B64MAP = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"
    Referer = "https://m.cloud.189.cn/zhuanti/2016/sign/index.jsp"  # https://m.cloud.189.cn/zt/2024/grow-guide/index.html#/

    def __init__(self, username, password):
        self.username = username
        self.password = password

    @staticmethod
    def retry_request(method, session, url, **kwargs):
        max_retries = 3
        delay = 3
        for attempt in range(1, max_retries + 1):
            try:
                resp = session.request(method, url, **kwargs)
                resp.raise_for_status()
                return resp
            except Exception as e:
                print(f"[第 {attempt} 次请求失败] {method} {url} → {e}")
                if attempt < max_retries:
                    time.sleep(delay)
                    delay += 2
                else:
                    raise
        return None

    @staticmethod
    def init_session_with_retry():
        sess = requests.Session()
        retries = Retry(total=3, backoff_factor=0.5, status_forcelist=[500, 502, 503, 504],
                        allowed_methods=["GET", "POST"])
        adapter = HTTPAdapter(max_retries=retries)
        sess.mount("http://", adapter)
        sess.mount("https://", adapter)
        return sess

    def int2char(self, a):
        return self.BI_RM[a]

    def b64tohex(self, a):
        d, e, c = "", 0, 0
        for ch in a:
            if ch != "=":
                v = self.B64MAP.index(ch)
                if e == 0:
                    e = 1
                    d += self.int2char(v >> 2)
                    c = v & 3
                elif e == 1:
                    e = 2
                    d += self.int2char((c << 2) | (v >> 4))
                    c = v & 15
                elif e == 2:
                    e = 3
                    d += self.int2char(c)
                    d += self.int2char(v >> 2)
                    c = v & 3
                else:
                    e = 0
                    d += self.int2char((c << 2) | (v >> 4))
                    d += self.int2char(v & 15)
        if e == 1:
            d += self.int2char(c << 2)
        return d

    def rsa_encode(self, pubkey_str, text):
        rsa_key = f"-----BEGIN PUBLIC KEY-----\n{pubkey_str}\n-----END PUBLIC KEY-----"
        pubkey = rsa.PublicKey.load_pkcs1_openssl_pem(rsa_key.encode())
        encrypted = rsa.encrypt(text.encode(), pubkey)
        return self.b64tohex(base64.b64encode(encrypted).decode())

    def login_flow(self):
        session = self.init_session_with_retry()
        base_headers = {
            'User-Agent': UA or "Mozilla 5.0",
            'Accept-Encoding': 'gzip, deflate'
        }
        token_url = f"https://m.cloud.189.cn/udb/udb_login.jsp?pageId=1&pageKey=default&clientType=wap&redirectURL={self.Referer}"
        r = self.retry_request("GET", session, token_url, headers=base_headers, timeout=10)
        m = re.search(r"https?://[^\s'\"]+", r.text)
        if not m:
            raise Exception("登录跳转 URL 获取失败")
        redirect = m.group()
        r = self.retry_request("GET", session, redirect, headers=base_headers, timeout=10)
        m2 = re.search(r"<a id=\"j-tab-login-link\"[^>]*href=\"([^\"]+)\"", r.text)
        if not m2:
            raise Exception("登录页面链接解析失败")
        href = m2.group(1)
        r = self.retry_request("GET", session, href, headers=base_headers, timeout=10)

        ct = re.findall(r"captchaToken' value='(.+?)'", r.text)[0]
        lt = re.findall(r'lt = "(.+?)"', r.text)[0]
        ret = re.findall(r"returnUrl= '(.+?)'", r.text)[0]
        pid = re.findall(r'paramId = "(.+?)"', r.text)[0]
        pubkey = re.findall(r'j_rsaKey" value="(\S+)"', r.text, re.M)[0]
        session.headers.update({"lt": lt})

        user_enc = self.rsa_encode(pubkey, self.username)
        pwd_enc = self.rsa_encode(pubkey, self.password)

        login_api = "https://open.e.189.cn/api/logbox/oauth2/loginSubmit.do"
        data = {
            "appKey": "cloud",
            "accountType": "01",
            "userName": f"{{RSA}}{user_enc}",
            "password": f"{{RSA}}{pwd_enc}",
            "validateCode": "",
            "captchaToken": ct,
            "returnUrl": ret,
            "mailSuffix": "@189.cn",
            "paramId": pid
        }
        login_headers = {
            'User-Agent': UA or "Mozilla 5.0",
            'Referer': 'https://open.e.189.cn/',
            'Accept-Encoding': 'gzip, deflate'
        }
        r = self.retry_request("POST", session, login_api, data=data, headers=login_headers, timeout=10)
        msg = r.json().get("msg", "无消息")
        print("登录响应：", msg)
        redirect_to = r.json().get("toUrl")
        if not redirect_to:
            raise Exception("登录跳转 URL 获取失败")
        self.retry_request("GET", session, redirect_to, headers=base_headers, timeout=10)
        return session

    def single_checkin(self):
        try:
            sess = self.login_flow()
        except Exception as e:
            print("登录重试结束仍失败：", e)
            push = ' 错误，请查看运行日志！'
            return push

        base_headers = {
            'User-Agent': UA or "Mozilla 5.0",
            'Referer': f"{self.Referer}",
            'Host':'m.cloud.189.cn',
            'Accept-Encoding': 'gzip, deflate'
        }
        rand = str(int(time.time() * 1000))
        sign_url = f'https://api.cloud.189.cn/mkt/userSign.action?rand={rand}&clientType=TELEANDROID&version=10.3.11&model={MODEL}'

        results = []
        try:
            r = self.retry_request("GET", sess, sign_url, headers=base_headers, timeout=10)
            j = r.json()
            bonus = j.get('netdiskBonus', 0)
            if j.get('isSign') == "false":
                msg = f" 未签到，获得 {bonus}M 空间"
            else:
                msg = f" 已签到，获得 {bonus}M 空间"
            print(msg)
            results.append(msg)
        except Exception as e:
            print("签到失败：", e)
            push = ' 错误，请查看运行日志！'
            return push

        # tasks = [
        # ("TASK_SIGNIN", "ACT_SIGNIN", ""),
        # ("TASK_SIGNIN_PHOTOS", "ACT_SIGNIN", ""),
        # ("TASK_2022_FLDFS_KJ", "ACT_SIGNIN", "链接3")
        # ]
        # for task, act, label in tasks:
        # try:
        # detail_url = (f'https://m.cloud.189.cn/v2/drawPrizeMarketDetails.action'
        # f'?taskId={task}&activityId={act}')
        # r = self.retry_request("GET", sess, detail_url, headers=base_headers, timeout=10)
        # data = r.json()
        # if 'description' in data:
        # desc = data['description']
        # out = (f"{label}抽奖获得{desc}" if label else f"抽奖获得{desc}")
        # print(out)
        # results.append(out)
        # except Exception as e:
        # print(f"{label}抽奖失败：", e)

        print("天翼云盘签到结果：")
        push = "\n".join(results)
        return push

def mphone(phone):
    if phone and len(phone) > 7:
        masked_phone = f"{phone[:3]}{'*' * 4}{phone[-4:]}"
        return masked_phone
    return phone

def send_ql_notification(content, title=""):
    """发送通知到青龙面板"""
    if QL_NOTIFY:
        try:
            # 青龙面板的send函数通常需要content参数
            # 尝试不同的参数传递方式
            import inspect
            sig = inspect.signature(send)
            params = list(sig.parameters.keys())
            
            if len(params) >= 2:
                # 如果函数需要2个或以上参数，通常第一个是标题，第二个是内容
                send(title, content)
            elif 'content' in params:
                # 如果函数有content参数
                send(content=content)
            elif 'title' in params:
                # 如果函数有title参数
                send(title=title)
            elif len(params) == 1:
                # 如果函数只有一个参数，直接传递内容
                send(content)
            else:
                # 默认方式
                send(content)
            
            print("已发送青龙面板通知")
        except Exception as e:
            print(f"发送青龙面板通知失败: {e}")
            print(f"通知内容: {content[:100]}...")
    else:
        print(f"【{title}】\n{content}")

def main():
    msg = ""
    if (a := os.getenv("ACCOUNTS")) is None:
        error_msg = "未设置 ACCOUNTS 环境变量"
        print(error_msg)
        send_ql_notification(error_msg, "天翼云盘签到失败")
        return
    
    # 读取系统变量以 \n 或 && 分割变量
    accounts = re.split('\n|&&', a)
    print("检测到共：", len(accounts), "天翼云盘账号\n")
    
    # main
    all_results = []
    i = 0
    while i < len(accounts):
        try:
            account_info = accounts[i].replace(" ", "").split(";")
            if len(account_info) < 2:
                print(f"第{i+1}个账号格式错误，跳过")
                i += 1
                continue
                
            username, password = account_info[0], account_info[1]
            
            if not username or not password:
                print(f"第{i+1}个账号的用户名或密码为空，跳过")
                i += 1
                continue
                
            print(f"\n开始处理第{i+1}个账号: {mphone(username)}")
            ecloud = Ecloud(username, password)
            result = ecloud.single_checkin()
            
            account_result = f"第{i+1}个账号 ({mphone(username)}):\n{result}"
            all_results.append(account_result)
            print(account_result)
            
        except Exception as e:
            error_msg = f"第{i+1}个账号签到失败：{e}"
            print(error_msg)
            all_results.append(error_msg)
        
        i += 1
        # 账号间延迟，避免请求过快
        if i < len(accounts):
            time.sleep(2)
    
    # 汇总所有结果
    if all_results:
        final_msg = "\n".join(all_results)
        print(f"\n{'='*30}\n签到完成！\n{'='*30}")
        print(final_msg)
        
        # 发送通知
        success_count = sum(1 for r in all_results if "错误" not in r and "失败" not in r)
        total_count = len(all_results)
        title = f"天翼云盘签到结果 ({success_count}/{total_count} 成功)"
        send_ql_notification(final_msg, title)
    else:
        error_msg = "没有有效的账号进行处理"
        print(error_msg)
        send_ql_notification(error_msg, "天翼云盘签到失败")

if __name__ == "__main__":
    print("开始执行天翼云盘签到脚本...")
    main()