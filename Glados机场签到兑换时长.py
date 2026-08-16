import requests
import time
from datetime import datetime
import json
# https://glados.space/landing/5386X-76FBK-0FJAE-SV71V 网站首页该机场采用邀请注册制 邀请码 5386X-76FBK-0FJAE-SV71V 新用户注册 双方可获得15天免费会员时长

# 该脚本实现自动化签到 每签到100积分可自动兑换15天免费会员时长

class GLaDOSAutoCheckin:
    def __init__(self, cookies, authorization):
        """
        初始化 GLaDOS 自动签到类
        :param cookies: 登录态 Cookie 字典（含 __stripe_mid、koa:sess、koa:sess.sig）
        :param authorization: 请求头中的 Authorization 标识（从浏览器请求中获取）
        """
        self.base_url = "https://glados.rocks"
        self.checkin_url = f"{self.base_url}/api/user/checkin"  # 签到接口
        self.console_url = f"{self.base_url}/console"          # 控制台页面（验证登录）
        
        # 初始化会话（自动保持 Cookie）
        self.session = requests.Session()
        
        # 模拟浏览器请求头（关键：需包含 Authorization 和 Content-Type）
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36 Edg/139.0.0.0",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
            "Content-Type": "application/json;charset=UTF-8",  # 签到请求为 JSON 格式
            "Authorization": authorization,                    # 关键标识，不可缺少
            "Origin": self.base_url,
            "Sec-Fetch-Site": "same-origin",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Dest": "empty",
            "Sec-Ch-Ua": "\"Not;A=Brand\";v=\"99\", \"Microsoft Edge\";v=\"139\", \"Chromium\";v=\"139\"",
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": "\"Windows\""
        }
        
        # 设置会话头和 Cookie
        self.session.headers.update(self.headers)
        self.session.cookies.update(cookies)

    def test_login_status(self):
        """
        测试登录状态：访问控制台页面，判断 Cookie 是否有效
        :return: 登录状态（True=有效，False=无效）
        """
        try:
            # 禁止重定向：未登录时会重定向到登录页（状态码 302）
            response = self.session.get(self.console_url, allow_redirects=False, timeout=10)
            
            if response.status_code == 200:
                print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] ✅ Cookie 有效，登录状态正常")
                return True
            elif response.status_code == 302:
                print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] ❌ Cookie 无效或已过期，需重新获取")
                return False
            else:
                print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] ⚠️  登录状态未知，响应码：{response.status_code}")
                return False
        except requests.exceptions.RequestException as e:
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] ❌ 测试登录失败：{str(e)}")
            return False

    def auto_checkin(self):
        """
        执行自动签到：发送 POST 请求到签到接口，解析响应结果
        :return: 签到结果（True=成功，False=失败/重复）
        """
        # 先验证登录状态，再执行签到
        if not self.test_login_status():
            return False
        
        # 签到请求参数（固定为 {"token": "glados.one"}，从浏览器请求中获取）
        checkin_data = json.dumps({"token": "glados.one"})
        
        try:
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 🚀 开始执行签到...")
            response = self.session.post(
                url=self.checkin_url,
                data=checkin_data,  # 注意：此处用 data 而非 json（需手动序列化 JSON）
                timeout=15
            )
            
            # 解析 JSON 响应（处理可能的编码问题）
            response.encoding = "utf-8"
            result = response.json()
            
            # 根据响应判断签到结果（参考你提供的响应格式）
            if response.status_code == 200:
                code = result.get("code")
                message = result.get("message", "未知信息")
                points = result.get("points", 0)
                # 提取最新余额（从 list 中取第一条记录的 balance）
                latest_balance = result.get("list", [{}])[0].get("balance", "未知")
                
                # 场景1：重复签到（code=1，message 含 "Repeats"）
                if code == 1 and "Repeats" in message:
                    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] ⚠️  签到结果：{message}")
                    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 💰 当前积分余额：{latest_balance}")
                    return False
                
                # 场景2：签到成功（code=0 或 message 含 "Success"，需根据实际成功响应调整）
                elif code == 0 or "Success" in message:
                    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] ✅ 签到成功！")
                    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 🎁 本次获得积分：{points}")
                    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 💰 当前积分余额：{latest_balance}")
                    return True
                
                # 场景3：其他情况（如账号异常）
                else:
                    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] ❌ 签到失败：{message}（code={code}）")
                    return False
            
            else:
                print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] ❌ 签到接口响应异常，状态码：{response.status_code}")
                return False
        
        except json.JSONDecodeError:
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] ❌ 解析签到响应失败：响应不是合法 JSON")
            return False
        except requests.exceptions.RequestException as e:
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] ❌ 签到请求失败：{str(e)}")
            return False

if __name__ == "__main__":
    # -------------------------- 请替换为你的个人信息 --------------------------
    # 1. Cookie 从浏览器开发者工具（F12）→ Network → 找到 checkin 请求 → Headers → Cookie 中提取
    USER_COOKIES = {
        #"__stripe_mid": "",  # 替换为你的 __stripe_mid
        "koa:sess": "eyJ1c2VySWQiOjY1MTMzMywiX2V4cGlyZSI6MTc4NzE4NTI1OTAxMiwiX21heEFnZSI6MjU5MjAwMDAwMDB9",  # 替换为你的 koa:sess
        "koa:sess.sig": "vwdwGCXNkQm7VlBtZO9JaPadpKc"  # 替换为你的 koa:sess.sig
    }
    
    # 2. Authorization 从浏览器 checkin 请求的 Headers 中提取（替换为你的标识）如果没有 请先点击签到 会出现这个抓包
    USER_AUTHORIZATION = "69439953663700993447647920417177-915-412"
    # --------------------------------------------------------------------------
    
    # 创建签到实例并执行签到
    glados_checker = GLaDOSAutoCheckin(
        cookies=USER_COOKIES,
        authorization=USER_AUTHORIZATION
    )
    
    # 执行签到
    glados_checker.auto_checkin()
    
    # 可选：添加延迟，防止快速请求被拦截
    time.sleep(2)