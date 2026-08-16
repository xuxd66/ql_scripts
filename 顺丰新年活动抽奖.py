# cron: 11 6,9,12,15,18 * * *
# const $ = new Env("顺丰速运");
import hashlib
import json
import os
import random
import time
import re
from datetime import datetime, timedelta
from sys import exit
import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter
from datetime import datetime
from urllib.parse import unquote
import warnings


requests.packages.urllib3.disable_warnings(InsecureRequestWarning)


IS_DEV = False


one_msg = ""


def Log(cont=""):
    global one_msg
    print(cont)
    if cont:
        one_msg += f"{cont}\n"


inviteId = ["A959FF988C64448198CDEB08FC84844F", "0A5BCEB5EA454B878C34EB01A33AF080"]


def sunquote(sfurl):
    decode = unquote(sfurl)
    if "3A//" in decode:
        decode = unquote(decode)
    return decode


# 禁用SSL警告
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class RUN:
    def __init__(self, info, index):
        global one_msg
        one_msg = ""
        split_info = info.split("@")
        url = split_info[0]
        len_split_info = len(split_info)
        last_info = split_info[len_split_info - 1]
        self.send_UID = None
        if len_split_info > 0 and "UID_" in last_info:
            self.send_UID = last_info
        self.index = index + 1
        Log(f"\n---------开始执行第{self.index}个账号>>>>>")
        self.s = requests.session()
        self.s.verify = False
        # 配置适配器，禁用重试以避免SSL问题
        adapter = HTTPAdapter(max_retries=0)
        self.s.mount('http://', adapter)
        self.s.mount('https://', adapter)
        self.headers = {
            "Host": "mcs-mimp-web.sf-express.com",
            "upgrade-insecure-requests": "1",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.102 Safari/537.36 NetType/WIFI MicroMessenger/7.0.20.1781(0x6700143B) WindowsWechat(0x63090551) XWEB/6945 Flue",
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
            "sec-fetch-site": "none",
            "sec-fetch-mode": "navigate",
            "sec-fetch-user": "?1",
            "sec-fetch-dest": "document",
            "accept-language": "zh-CN,zh",
            "platform": "MINI_PROGRAM",
        }
        self.anniversary_black = False
        self.member_day_black = False
        self.member_day_red_packet_drew_today = False
        self.member_day_red_packet_map = {}
        self.login_res = self.login(url)
        self.today = datetime.now().strftime("%Y-%m-%d")
        # self.answer = APP_INFO.get('ANSWER', []).get(self.today, False)
        self.max_level = 8
        self.packet_threshold = 1 << (self.max_level - 1)
        self.all_logs = []

    def get_deviceId(self, characters="abcdef0123456789"):
        result = ""
        for char in "xxxxxxxx-xxxx-xxxx":
            if char == "x":
                result += random.choice(characters)
            elif char == "X":
                result += random.choice(characters).upper()
            else:
                result += char
        return result

    def login(self, sfsyUrl):
        ress = self.s.get(sfsyUrl, headers=self.headers, verify=False)
        # print(ress.text)
        self.user_id = self.s.cookies.get_dict().get("_login_user_id_", "")
        self.phone = self.s.cookies.get_dict().get("_login_mobile_", "")
        self.mobile = self.phone[:3] + "*" * 4 + self.phone[7:]
        if self.phone != "":
            Log(f"用户:【{self.mobile}】登陆成功")
            return True
        else:
            Log(f"获取用户信息失败")
            return False

    def getSign(self):
        timestamp = str(int(round(time.time() * 1000)))
        token = "wwesldfs29aniversaryvdld29"
        sysCode = "MCS-MIMP-CORE"
        data = f"token={token}&timestamp={timestamp}&sysCode={sysCode}"
        signature = hashlib.md5(data.encode()).hexdigest()
        data = {"sysCode": sysCode, "timestamp": timestamp, "signature": signature}
        self.headers.update(data)
        return data

    def do_request(self, url, data={}, req_type="post"):
        try:
            if req_type.lower() == "get":
                response = self.s.get(url, headers=self.headers, verify=False)
            elif req_type.lower() == "post":
                response = self.s.post(url, headers=self.headers, json=data, verify=False)
            else:
                raise ValueError(f"Invalid request type: {req_type}")

            try:
                res = response.json()
            except json.JSONDecodeError:
                Log(f"JSON 解码失败，响应内容: {response.text}")
                return {"success": False, "errorMessage": "JSON 解码失败"}

            return res
        except requests.exceptions.RequestException as e:
            Log(f"网络请求失败: {e}")
            return {"success": False, "errorMessage": "网络请求失败"}
        except Exception as e:
            Log(f"未知错误: {e}")
            return {"success": False, "errorMessage": "未知错误"}

    
    def yearEnd2025_prize_draw(self, currency="HAPPY"):
        print(f">>>2025年年终活动-执行抽奖 (货币类型: {currency})")
        self.headers["channel"] = "daluapp"
        self.headers["platform"] = "SFAPP"
        self.headers["deviceId"] = self.get_deviceId()
        url = "https://mcs-mimp-web.sf-express.com/mcs-mimp/commonPost/~memberNonactivity~yearEnd2025LotteryService~prizeDraw"
        data = {"currency": currency}
        response = self.do_request(url, data=data)
        if response.get("success") == True:
            obj = response.get("obj", {})
            gift_bag_name = obj.get("giftBagName", "")
            gift_bag_worth = obj.get("giftBagWorth", 0)
            Log(f"> 抽奖成功！获得【{gift_bag_name}】，价值【{gift_bag_worth}】元")
            
            product_list = obj.get("productDTOList", [])
            if product_list:
                Log("> 奖品详情:")
                for product in product_list:
                    product_name = product.get("productName", "")
                    amount = product.get("amount", 0)
                    effective_date = product.get("effectiveDate", "")
                    expiration_date = product.get("expirationDate", "")
                    coupon_name = product.get("couponName", "")
                    denomination = product.get("denomination", "")
                    Log(f"  - {product_name} x{amount}")
                    Log(f"    有效期: {effective_date} 至 {expiration_date}")
                    if coupon_name:
                        Log(f"    优惠券: {coupon_name} (面值: {denomination}元)")
        else:
            error_message = response.get("errorMessage", "无返回")
            print(f'>抽奖失败: {error_message}')

    def yearEnd2025_forward_status(self):
        print(">>>2025年年终活动-获取抽奖资格")
        self.headers["channel"] = "daluapp"
        self.headers["platform"] = "SFAPP"
        self.headers["deviceId"] = self.get_deviceId()
        url = "https://mcs-mimp-web.sf-express.com/mcs-mimp/commonPost/~memberNonactivity~yearEnd2025ForwardService~forwardStatus"
        response = self.do_request(url, data={})
        if response.get("success") == True:
            obj = response.get("obj", {})
            current_level = obj.get("currentLevel", "")
            current_times = obj.get("currentTimes", 0)
            remain_chance = obj.get("remainChance", 0)
            Log(f"> 活动状态: 当前等级【{current_level}】, 当前次数【{current_times}】, 剩余抽奖机会【{remain_chance}】")
            level_list = obj.get("levelList", [])
            if level_list:
                Log("> 等级详情:")
                for level in level_list:
                    currency = level.get("currency", "")
                    total_amount = level.get("totalAmount", 0)
                    balance = level.get("balance", 0)
                    Log(f"  - {currency}: 总量【{total_amount}】, 余额【{balance}】")
                    if balance ==1 :
                        print(f"  - {currency}: 余额为1，可抽奖")
                        self.yearEnd2025_prize_draw(currency)
            
           
                
        else:
            error_message = response.get("errorMessage", "无返回")
            print(f'>获取抽奖资格失败: {error_message}')

  
    def sendMsg(self, help=False):
        if self.send_UID:
            push_res = CHERWIN_TOOLS.wxpusher(self.send_UID, one_msg, APP_NAME, help)
            print(push_res)

    def main(self):
        global one_msg
        wait_time = random.randint(1000, 3000) / 1000.0
        time.sleep(wait_time)  # 等待
        one_msg = ""
        if not self.login_res:
            return False
        
        # 执行签到
        # self.sign()
        # # 执行2025年年终活动-获取抽奖资格
        self.yearEnd2025_forward_status()


def get_quarter_end_date():
    current_year = datetime.now().year
    current_month = datetime.now().month

    if current_month in [1, 2, 3]:
        next_quarter_first_day = datetime(current_year, 4, 1)
    elif current_month in [4, 5, 6]:
        next_quarter_first_day = datetime(current_year, 7, 1)
    elif current_month in [7, 8, 9]:
        next_quarter_first_day = datetime(current_year, 10, 1)
    else:
        next_quarter_first_day = datetime(current_year + 1, 1, 1)
    return next_quarter_first_day


def is_activity_end_date(end_date):
    if isinstance(end_date, datetime):
        end_date = end_date.date()
    elif isinstance(end_date, str):
        end_date = datetime.strptime(end_date, "%Y-%m-%d").date()
    else:
        raise TypeError("end_date must be a string or datetime object")

    return end_date



if __name__ == "__main__":
    APP_NAME = "顺丰速运"
    ENV_NAME = "sfsyUrl"
    CK_NAME = "url"
    local_script_name = os.path.basename(__file__)
    local_version = "2024.06.02"
    token = os.getenv(ENV_NAME)
    tokens = token.split("\n")
    # print(tokens)
    if len(tokens) > 0:
        print(f"\n>>>>>>>>>>共获取到{len(tokens)}个账号<<<<<<<<<<")
        for index, infos in enumerate(tokens):
            run_result = RUN(infos, index).main()
            if not run_result:
                continue
