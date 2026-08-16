# 脚本来源于网络，所涉及到的 账号安全、数据泄露、设备故障、软件违规封禁、财产损失等问题及法律风险，与脚本库无关！均由使用者自行承担。

# 多账号：每行一个 "手机号@密码"
# export YDY_AUTH=$'188xxxx@pass1\n199xxxx@pass2'
#本就不加密了，求求送个头，注册链接https://h5.yidingyuecheng.com/#/pages/register/index?promoCode=BEI134781
import os
import json
from typing import Dict, Any, Tuple, List, Optional
import requests

BASE = "https://h5.yidingyuecheng.com"
LOGIN_URL = f"{BASE}/api/user/login"
SIGN_URL  = f"{BASE}/api/mission/sign"
INFO_URL  = f"{BASE}/api/user/info"


AUTH_LIST = os.getenv("YDY_AUTH", "").strip()

COMMON_HEADERS = {
    "source": "h5",
    "content-type": "application/json",
    "accept": "*/*",
    "origin": "https://h5.yidingyuecheng.com",
    "referer": "https://h5.yidingyuecheng.com/",
    "x-requested-with": "mark.via",
    "user-agent": (
        "Mozilla/5.0 (Linux; Android 15; PKG110 Build/UKQ1.231108.001) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.6998.135 "
        "Mobile Safari/537.36"
    ),
    "sec-ch-ua-platform": '"Android"',
    "sec-ch-ua": '"Chromium";v="134", "Not:A-Brand";v="24", "Android WebView";v="134"',
    "sec-ch-ua-mobile": "?1",
    "sec-fetch-site": "same-origin",
    "sec-fetch-mode": "cors",
    "sec-fetch-dest": "empty",
    "accept-language": "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7",
    "accept-encoding": "gzip, deflate, br, zstd",
}

def jdump(x: Any) -> str:
    return json.dumps(x, ensure_ascii=False, indent=2)

def mask_token(t: Optional[str]) -> Optional[str]:
    if not t:
        return t
    if len(t) < 12:
        return t
    return t[:6] + "..." + t[-6:]

def parse_accounts(multiline: str) -> List[Tuple[str, str]]:
    if not multiline:
        raise ValueError(
            "未设置环境变量 YDY_AUTH。\n"
            "示例：export YDY_AUTH=$'188xxxx@pass1\\n199xxxx@pass2'"
        )

    accounts: List[Tuple[str, str]] = []
    for raw in multiline.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if "@" not in line:
            raise ValueError(f"账号行格式错误（缺少@）：{line}")
        mobile, pwd = line.split("@", 1)
        mobile, pwd = mobile.strip(), pwd.strip()
        if not mobile or not pwd:
            raise ValueError(f"账号行格式错误（手机号或密码为空）：{line}")
        accounts.append((mobile, pwd))

    if not accounts:
        raise ValueError("YDY_AUTH 中没有可用账号行（空行或被注释）。")
    return accounts

def api_post(session: requests.Session, url: str, payload: Dict[str, Any], timeout: int = 20) -> Dict[str, Any]:
    r = session.post(url, json=payload, timeout=timeout)
    r.raise_for_status()
    try:
        return r.json()
    except Exception as e:
        raise RuntimeError(f"响应不是 JSON：{e}\nraw={r.text[:2000]}")

def login(session: requests.Session, mobile: str, password: str) -> str:
    res = api_post(session, LOGIN_URL, {"mobile": mobile, "password": password})
    if not (res.get("success") is True or res.get("code") == 0):
        raise RuntimeError(f"登录失败：\n{jdump(res)}")
    token = res.get("data")
    if not isinstance(token, str) or not token.strip():
        raise RuntimeError(f"登录未返回 token(data)：\n{jdump(res)}")
    return token

def sign(session: requests.Session, token: str) -> Dict[str, Any]:
    session.headers["token"] = token
    return api_post(session, SIGN_URL, {})

def user_info(session: requests.Session, token: str) -> Dict[str, Any]:
    session.headers["token"] = token
    return api_post(session, INFO_URL, {})

def print_basic_info(info_res: Dict[str, Any]) -> None:
    if not (info_res.get("success") is True or info_res.get("code") == 0):
        print(f"⚠️ 获取用户信息失败：{info_res.get('msg')} code={info_res.get('code')}")
        return
    d = info_res.get("data") or {}
    print(f"ID={d.get('id')}  积分={d.get('point')}  注册时间={d.get('cdate')}")

def run_one_account(mobile: str, password: str) -> None:
    s = requests.Session()
    s.headers.update(COMMON_HEADERS)

    print(f"\n========== 账号 {mobile} ==========")

    print("[1] 登录…")
    token = login(s, mobile, password)
    print(f"[+] 登录成功，token={mask_token(token)}（长度={len(token)}）")

    print("[2] 签到…")
    sign_res = sign(s, token)
    msg, code, ok = sign_res.get("msg"), sign_res.get("code"), sign_res.get("success")
    print(f"[+] 签到结果：success={ok} code={code} msg={msg}")

    print("[3] 获取用户信息…")
    info_res = user_info(s, token)
    print_basic_info(info_res)

def main():
    accounts = parse_accounts(AUTH_LIST)
    for mobile, pwd in accounts:
        try:
            run_one_account(mobile, pwd)
        except Exception as e:
            print(f"❌ 账号 {mobile} 执行失败：{e}")

if __name__ == "__main__":
    main()

