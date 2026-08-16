import os
import time
import requests
import urllib3
from datetime import datetime
from typing import Optional, Dict, Any, Union, List

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class RnlRequest:
    def __init__(self, cookies: Union[str, dict]):
        self.session = requests.Session()
        self._base_headers = {
            'Host': 'm.jr.airstarfinance.net',
            'Connection': 'keep-alive',
            'Accept': 'application/json, text/plain, */*',
            'Cache-Control': 'no-cache',
            'User-Agent': 'Mozilla/5.0 (Linux; U; Android 14; zh-CN; M2012K11AC Build/UKQ1.230804.001; AppBundle/com.mipay.wallet; AppVersionName/6.96.0.5453.2620; AppVersionCode/20577622; MiuiVersion/stable-V816.0.13.0.UMNCNXM; DeviceId/alioth; NetworkType/WIFI; mix_version; WebViewVersion/118.0.0.0) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Mobile Safari/537.36 XiaoMi/MiuiBrowser/4.3',
            'X-Requested-With': 'com.mipay.wallet',
            'Sec-Fetch-Site': 'same-origin',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Dest': 'empty',
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7'
        }
        self.update_cookies(cookies)

    def request(
        self,
        method: str,
        url: str,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Union[Dict[str, Any], str, bytes]] = None,
        json: Optional[Dict[str, Any]] = None,** kwargs
    ) -> Optional[Dict[str, Any]]:
        headers = {**self._base_headers, **kwargs.pop('headers', {})}
        try:
            resp = self.session.request(
                verify=False,
                method=method.upper(),
                url=url,
                params=params,
                data=data,
                json=json,
                headers=headers,** kwargs
            )
            resp.raise_for_status()
            return resp.json()
        except requests.RequestException as e:
            print(f"[Request Error] {e}")
        except ValueError as e:
            print(f"[JSON Parse Error] {e}")
        return None

    def update_cookies(self, cookies: Union[str, dict]) -> None:
        if cookies:
            if isinstance(cookies, str):
                dict_cookies = self._parse_cookies(cookies)
            else:
                dict_cookies = cookies
            self.session.cookies.update(dict_cookies)
            self._base_headers['Cookie'] = self.dict_cookie_to_string(dict_cookies)

    @staticmethod
    def _parse_cookies(cookies_str: str) -> Dict[str, str]:
        return dict(
            item.strip().split('=', 1)
            for item in cookies_str.split(';')
            if '=' in item
        )

    @staticmethod
    def dict_cookie_to_string(cookie_dict):
        cookie_list = []
        for key, value in cookie_dict.items():
            cookie_list.append(f"{key}={value}")
        return "; ".join(cookie_list)

    def get(self, url: str, params: Optional[Dict[str, Any]] = None, **kwargs) -> Optional[Dict[str, Any]]:
        return self.request('GET', url, params=params,** kwargs)

    def post(self, url: str, data: Optional[Union[Dict[str, Any], str, bytes]] = None,
             json: Optional[Dict[str, Any]] = None, **kwargs) -> Optional[Dict[str, Any]]:
        return self.request('POST', url, data=data, json=json,** kwargs)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.session.close()


class RNL:
    def __init__(self, c):
        self.options = {
            "task_list": True,
            "complete_task": True,
            "receive_award": True,
            "task_item": True,
            "UserJoin": True,
        }
        self.activity_code = '2211-videoWelfare'
        self.rr = RnlRequest(c)
        self.TASK_COMPLETED_CODE = 10016  # 当日任务已完成的错误码
        self.AFTER_COMPLETE_DELAY = 5  # 完成任务后到领取奖励前的延迟时间（秒）

    def queryUserJoinListAndQueryUserGoldRichSum(self) -> tuple[bool, str]:
        """仅查询用户总天数和当日记录（不用于判断任务状态）"""
        try:
            user_extra = "%7B%22platformType%22:1,%22com.miui.video%22:%22v2023091090(MiVideo-ROM)%22,%22com.mipay.wallet%22:%226.96.0.5453.2620%22%7D"
            
            # 获取总天数
            total_url = (
                f"https://m.jr.airstarfinance.net/mp/api/generalActivity/queryUserGoldRichSum"
                f"?app=com.mipay.wallet&deviceType=2&system=1&visitEnvironment=2"
                f"&userExtra={user_extra}&activityCode={self.activity_code}"
            )
            total_res = self.rr.get(total_url)
            if not total_res or total_res['code'] != 0:
                print(f'获取兑换视频天数失败：{total_res}')
                return False, "未知"
            total_days = f"{int(total_res['value']) / 100:.2f}天"

            # 查询当日记录（仅展示用）
            join_list_url = (
                f"https://m.jr.airstarfinance.net/mp/api/generalActivity/queryUserJoinList"
                f"?userExtra={user_extra}&activityCode={self.activity_code}"
                f"&pageNum=1&pageSize=20"
            )
            response = self.rr.get(join_list_url)
            if not response or response['code'] != 0:
                print(f'查询任务完成记录失败：{response}')
                return True, total_days  # 记录查询失败不影响主流程

            # 打印当日记录
            history_list = response['value']['data']
            current_date = datetime.now().strftime("%Y-%m-%d")
            print(f"\n【当前用户兑换视频总天数】：{total_days}")
            print(f"------------ {current_date} 当日任务记录 ------------")
            has_today_record = False
            for record in history_list:
                record_time = record['createTime']
                if record_time.startswith(current_date):
                    days = int(record['value']) / 100
                    print(f"• {record_time} 领取视频会员 +{days:.2f}天")
                    has_today_record = True
            if not has_today_record:
                print(f"• 暂无{current_date}任务记录")
            
            return True, total_days
        except Exception as e:
            print(f'获取任务记录失败：{e}')
            return False, "未知"

    def complete_task(self) -> Optional[Union[int, str]]:
        """
        执行【应用试用任务】请求
        返回值说明：
        - int: 成功时返回userTaskId
        - "completed": 当code=10016时（当日任务已完成）
        - None: 其他错误
        """
        try:
            complete_url = (
                f"https://m.jr.airstarfinance.net/mp/api/generalActivity/completeTask"
                f"?activityCode={self.activity_code}&app=com.mipay.wallet"
                f"&oaid=8c45c5802867e923"
                f"&regId=KWkK5VsKXiIbAH8Rf6kgU6tpDPyNWgXY8YCM1mQtt5nd7i1%2F4BqzPq0uY7OlIEOd"
                f"&versionCode=20577622&versionName=6.96.0.5453.2620"
                f"&isNfcPhone=true&channel=mipay_indexicon_TVcard2test"
                f"&deviceType=2&system=1&visitEnvironment=2"
                f"&userExtra=%7B%22platformType%22:1,%22com.miui.video%22:%22v2023091090(MiVideo-ROM)%22,%22com.mipay.wallet%22:%226.96.0.5453.2620%22%7D"
                f"&taskCode=NEW_USER_CAMPAIGN&browsTaskId=&browsClickUrlId=1306285"
                f"&adInfoId=&triggerId="
            )
            print("\n正在执行【应用试用任务】请求...")
            response = self.rr.get(complete_url, headers={'X-Request-ID': self._generate_request_id()})
            if not response:
                print("完成任务请求无响应")
                return None
            
            # 核心判断：如果返回code=10016，标记为当日已完成
            if response['code'] == self.TASK_COMPLETED_CODE:
                error_msg = response.get('error', '当日任务已完成')
                print(f"完成任务返回状态：{error_msg}（code={response['code']}）")
                return "completed"  # 特殊标记表示当日已完成
            
            # 其他错误码
            if response['code'] != 0:
                error_msg = response.get('error', '未知错误')
                print(f"完成任务失败：{error_msg}（code={response['code']}）")
                return None
            
            # 成功执行
            user_task_id = response['value']
            print(f"完成任务成功！获取userTaskId：{user_task_id}")
            return user_task_id
        except Exception as e:
            print(f'完成任务异常：{e}')
            return None

    def receive_award(self, user_task_id: int) -> None:
        """执行【领取奖励】请求"""
        try:
            receive_url = (
                f"https://m.jr.airstarfinance.net/mp/api/generalActivity/luckDraw"
                f"?imei=&device=alioth"
                f"&appLimit=%7B%22com.qiyi.video%22:false,%22com.youku.phone%22:false,%22com.tencent.qqlive%22:false,%22com.hunantv.imgo.activity%22:false,%22com.cmcc.cmvideo%22:false,%22com.sankuai.meituan%22:false,%22com.anjuke.android.app%22:false,%22com.tal.abctimelibrary%22:false,%22com.lianjia.beike%22:false,%22com.kmxs.reader%22:false,%22com.jd.jrapp%22:false,%22com.smile.gifmaker%22:true,%22com.kuaishou.nebula%22:false%7D"
                f"&activityCode={self.activity_code}&userTaskId={user_task_id}"
                f"&app=com.mipay.wallet&oaid=8c45c5802867e923"
                f"&regId=L522i5qLZR9%2Bs25kEqPBJYbbHqUS4LrpuTsgl9kdsbcyU7tjWmx1BewlRNSSZaOT"
                f"&versionCode=20577622&versionName=6.96.0.5453.2620"
                f"&isNfcPhone=true&channel=mipay_indexicon_TVcard2test"
                f"&deviceType=2&system=1&visitEnvironment=2"
                f"&userExtra=%7B%22platformType%22:1,%22com.miui.video%22:%22v2023091090(MiVideo-ROM)%22,%22com.mipay.wallet%22:%226.96.0.5453.2620%22%7D"
            )
            print(f"\n正在执行【领取奖励】请求（userTaskId={user_task_id}）...")
            response = self.rr.get(
                receive_url, 
                headers={
                    'X-Request-ID': self._generate_request_id(),
                    'sec-ch-ua': '"Chromium";v="118", "Android WebView";v="118", "Not=A?Brand";v="99"'
                }
            )
            if not response:
                print("领取奖励请求无响应")
                return
            
            if response['code'] != 0:
                print(f"领取奖励失败：{response['error']}（code={response['code']}）")
                return
            
            prize_info = response['value']['prizeInfo']
            print(f"领取奖励成功！")
            print(f"奖励详情：{prize_info['prizeName']}（{prize_info['prizeDesc']}）")
            print(f"奖励数量：{prize_info['amount']} | 发放时间：{prize_info['createTime']}")
        except Exception as e:
            print(f'领取奖励异常：{e}')

    @staticmethod
    def _generate_request_id() -> str:
        """生成随机X-Request-ID"""
        import uuid
        return str(uuid.uuid4())

    def main(self) -> bool:
        """主逻辑：先查询状态（展示用）→ 执行完成任务 → 根据返回code判断是否继续"""
        print("="*50)
        # 1. 查询用户状态（仅展示，不用于判断任务状态）
        query_success, total_days = self.queryUserJoinListAndQueryUserGoldRichSum()
        if not query_success:
            print("初始状态查询失败，尝试继续执行任务...")
        
        # 2. 执行完成任务（核心判断逻辑）
        print(f"\n开始执行【完成任务】操作...")
        time.sleep(13)  # 模拟操作延迟
        result = self.complete_task()
        
        # 3. 根据返回结果处理
        if result == "completed":
            # 明确code=10016，当日任务已完成
            print(f"✅ 检测到code={self.TASK_COMPLETED_CODE}，当日任务已完成，无需继续操作")
            print("="*50)
            return True
        
        if isinstance(result, int):
            # 任务成功完成，延迟指定时间后领取奖励
            print(f"\n等待{self.AFTER_COMPLETE_DELAY}秒后领取奖励...")
            time.sleep(self.AFTER_COMPLETE_DELAY)  # 关键修改：将此处延迟改为5秒
            self.receive_award(result)
            
            # 最终查询更新状态
            time.sleep(2)
            print("\n" + "="*50)
            print("【任务执行后更新状态】")
            self.queryUserJoinListAndQueryUserGoldRichSum()
            print("="*50)
            return True
        
        # 其他错误情况
        print("❌ 任务执行失败，终止流程")
        print("="*50)
        return False


def get_xiaomi_cookies(pass_token, user_id) -> Optional[str]:
    """获取小米账号Cookie"""
    session = requests.Session()
    login_url = (
        "https://account.xiaomi.com/pass/serviceLogin?callback=https%3A%2F%2Fapi.jr.airstarfinance.net%2Fsts%3Fsign%3D1dbHuyAmee0NAZ2xsRw5vhdVQQ8%253D%26followup%3Dhttps%253A%252F%252Fm.jr.airstarfinance.net%252Fmp%252Fapi%252Flogin%253Ffrom%253Dmipay_indexicon_TVcard%2526deepLinkEnable%253Dfalse%2526requestUrl%253Dhttps%25253A%25252F%25252Fm.jr.airstarfinance.net%25252Fmp%25252Factivity%25252FvideoActivity%25253Ffrom%25253Dmipay_indexicon_TVcard%252526_noDarkMode%25253Dtrue%252526_transparentNaviBar%25253Dtrue%252526cUserId%25253Dusyxgr5xjumiQLUoAKTOgvi858Q%252526_statusBarHeight%25253D137&sid=jrairstar&_group=DEFAULT&_snsNone=true&_loginType=ticket"
    )
    headers = {
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36 Edg/135.0.0.0',
        'cookie': f'passToken={pass_token}; userId={user_id};'
    }

    try:
        session.get(url=login_url, headers=headers, verify=False, timeout=15)
        cookies = session.cookies.get_dict()
        if 'cUserId' in cookies and 'serviceToken' in cookies:
            return (
                f"cUserId={cookies['cUserId']}; "
                f"jrairstar_serviceToken={cookies['serviceToken']}; "
                f"sajssdk_2015_cross_new_user=1; "
                f"jrairstar_slh=aSVmYnIUbBUDsNJyMZEVo0aPF/A=; "
                f"jrairstar_ph=XR+3vTjVZVW95TtjfCvpcw==; "
                f"sensorsdata2015jssdkcross=%7B%22distinct_id%22%3A%22{cookies['cUserId']}%22%2C%22first_id%22%3A%221990ca2cac36de-038290424cd5ca4-710f241b-343089-1990ca2cac44ff%22%2C%22props%22%3A%7B%22%24latest_traffic_source_type%22%3A%22%E7%9B%B4%E6%8E%A5%E6%B5%81%E9%87%8F%22%2C%22%24latest_search_keyword%22%3A%22%E6%9C%AA%E5%8F%96%E5%88%B0%E5%80%BC_%E7%9B%B4%E6%8E%A5%E6%89%93%E5%BC%80%22%2C%22%24latest_referrer%22%3A%22%22%7D%2C%22identities%22%3A%22eyIkaWRlbnRpdHlfbG9naW5faWQiOiJ{cookies['cUserId']}IiwiJGlkZW50aXR5X2Nvb2tlaV9pZCI6IjE5OTBjYTJjYWMzNmRlLTAzODI5MDQyNGNkNWNhNC03MTBmMjQxYi0zNDMwODktMTk5MGNhMmNhYzQ0ZmYifQ%3D%3D%22%2C%22history_login_id%22%3A%7B%22name%22%3A%22%24identity_login_id%22%2C%22value%22%3A%22{cookies['cUserId']}%22%7D%2C%22%24device_id%22%3A%221990ca2cac36de-038290424cd5ca4-710f241b-343089-1990ca2cac44ff%22%7D"
            )
        else:
            print(f"Cookie缺失关键字段：cUserId={cookies.get('cUserId')}, serviceToken={cookies.get('serviceToken')}")
            return None
    except Exception as e:
        print(f"获取Cookie失败: {str(e)}")
        return None


if __name__ == "__main__":
    ORIGINAL_COOKIES = [
        {   # 账号1
            'passToken': 'xxxx',
            'userId': 'xxxxx'
        },
        {   # 账号2
            'passToken': 'xxxx',
            'userId': 'xxxx'
        }
    ]

    # 1. 批量获取有效Cookie
    cookie_list = []
    for idx, account in enumerate(ORIGINAL_COOKIES, 1):
        print(f"\n【账号{idx}】正在处理 userId={account['userId']}")
        new_cookie = get_xiaomi_cookies(account['passToken'], account['userId'])
        if new_cookie:
            cookie_list.append((account['userId'], new_cookie))
            print(f"【账号{idx}】Cookie获取成功")
        else:
            print(f"【账号{idx}】⚠️ Cookie获取失败，请检查passToken有效性")

    # 2. 批量执行任务
    print(f"\n\n【批量执行开始】共获取到 {len(cookie_list)} 个有效账号")
    for idx, (user_id, cookie) in enumerate(cookie_list, 1):
        print(f"\n\n" + "="*60)
        print(f"【正在执行账号{idx}】userId={user_id}")
        print("="*60)
        try:
            rnl = RNL(cookie)
            success = rnl.main()
            print(f"【账号{idx}】执行结果：{'成功' if success else '失败'}")
        except Exception as e:
            print(f"【账号{idx}】执行异常：{str(e)}")
        time.sleep(5)  # 账号间延迟，避免反爬
    
    print(f"\n\n【批量执行结束】所有账号处理完成")
