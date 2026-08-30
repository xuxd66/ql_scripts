# -*- coding: utf-8 -*-
"""
知了快看 —— 青龙单文件版 —— 算法与脚本合一, 可直接丢进青龙定时任务
================================================================================
【功能】自动刷视频观看时长 + 纯脚本领取「刷视频领金币」(task_score_optimize) 与「刷视频领现金」(read_withdraw) 待领收益(均非广告类, 无需 media_verify)
【依赖】仅 pycryptodome (pip install pycryptodome), 其余全为标准库; 不依赖任何外部文件/APK
【凭据】三种模式(任选其一, 推荐方式1):
    ▶ 方式1(最简): 只需UID, 环境变量 ZHIKAN_ACCOUNT 或命令行 --account:
        示例: ZHIKAN_ACCOUNT="54475743"  或  python3 xxx.py --account 54475743 66677788
        无需抓包, session 由服务端自动下发, 脚本自动捕获。
    ▶ 方式2(推荐): 抓包拿到请求体里的 zqkd_param 整串, 直接设为环境变量 ZHILIAO_PARAM, 脚本自动解密取参(uid/union_id/zqkey/zqkey_id/s_ad/设备指纹全自动):
        示例: ZHILIAO_PARAM="EsBz4arTkukU=094bDP238NM0IRDBjryYjdKTDeWZynsrRHhW9pF3itm-8-By4FYP-..."
    ▶ 多账号(方式2扩展): 多个 zqkd_param 整串用 & 分隔即可, 脚本逐个运行, 账号之间随机等待 30-60s:
        示例: ZHILIAO_PARAM="串1&串2&串3"
    ▶ 方式3(手工): 环境变量 ZHILIAO, 多个参数用 # 分隔, 每个参数为 key=value:
        示例: ZHILIAO="uid=54475743#session=你的PHPSESSID#union_id=xxx#zqkey=xxx#zqkey_id=xxx#s_ad=xxx#minutes=40"
        支持 key: uid / session(PHPSESSID, 可选) / union_id / user_cert / zqkey / zqkey_id /
                 s_ad / oaid / openudid / androidid / device_id / sm_device_id / app_device_id /
                 ssp_uid / minutes(默认30) / media_extra(frida捕获, 广告翻倍用) / media_verify
        未提供的 key 自动用内置默认值; 旧版 ZQKD_* 多变量已废弃(仍静默兼容, 建议统一)。
    ✅ session(PHPSESSID) 无需手动配置: 它由服务端在响应(Set-Cookie 头)自动下发,
       脚本首次请求后自动从响应捕获并保存, 后续请求自动带上。仅想复用固定会话时才在
       ZHILIAO 里写 session=xxx(可选, 一般不用配)。。
【用法】青龙添加任务:  python3 xxx.py
        UID直登:  python3 xxx.py --account 54475743
        多账号:    python3 xxx.py --account 54475743 66677788
        (时长可调: 命令后加 --minutes 40, 或 ZHILIAO 里写 minutes=40)
【通知】QYWX_AM: 企业微信应用通知，格式: corpid,corpsecret,touser,agentid（可选）
【密钥说明】DES/AES 密钥由 APK 签名证书 SPKI 派生; 该证书固定, 已预算为常量 SPKI_B64 硬编码,
           故本文件不再读取 base.apk。所有签名/加解密均经原 HAR 字节级闭环验证。
"""
from __future__ import annotations
import os, sys, time, random, json, argparse, hashlib, hmac, base64, struct, gzip, string
import urllib.request, urllib.error, urllib.parse
from typing import Any, Dict, Optional

# ==================== 企业微信通知 ====================

def _qywx_request(url, data=None, method="GET"):
    """用 urllib 发送 HTTP 请求(与脚本风格一致)"""
    req = urllib.request.Request(url, method=method)
    if data is not None:
        req.add_header("Content-Type", "application/json")
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        req.data = body
    resp = urllib.request.urlopen(req, timeout=10)
    return json.loads(resp.read().decode("utf-8"))


def get_qywx_token(corpid, corpsecret):
    """获取企业微信 access_token"""
    url = f"https://qyapi.weixin.qq.com/cgi-bin/gettoken?corpid={corpid}&corpsecret={corpsecret}"
    try:
        data = _qywx_request(url)
        if data.get("errcode") == 0:
            return data.get("access_token")
    except Exception:
        pass
    return None


def send_qywx_msg(content):
    """通过企业微信应用发送文本消息

    环境变量 QYWX_AM 格式: corpid,corpsecret,touser,agentid
      - corpid:     企业ID
      - corpsecret: 应用密钥
      - touser:     接收消息的用户ID，多个用 | 分隔，@all 表示全部
      - agentid:    应用AgentId
    """
    qywx_am = os.environ.get("QYWX_AM", "").strip()
    if not qywx_am:
        return False

    parts = qywx_am.split(",")
    if len(parts) < 4:
        print("[通知] QYWX_AM 格式错误，应为: corpid,corpsecret,touser,agentid")
        return False

    corpid, corpsecret, touser, agentid = parts[0], parts[1], parts[2], parts[3]

    token = get_qywx_token(corpid, corpsecret)
    if not token:
        print("[通知] 获取企业微信 access_token 失败")
        return False

    url = f"https://qyapi.weixin.qq.com/cgi-bin/message/send?access_token={token}"
    payload = {
        "touser": touser,
        "msgtype": "text",
        "agentid": int(agentid),
        "text": {"content": content},
    }
    try:
        data = _qywx_request(url, data=payload, method="POST")
        if data.get("errcode") == 0:
            print("[通知] 企业微信消息发送成功")
            return True
        else:
            print(f"[通知] 企业微信消息发送失败: {data}")
            return False
    except Exception as e:
        print(f"[通知] 企业微信消息发送异常: {e}")
        return False

# ============================================================
# 运行参数 (老韩集中调参区, 放最前方便改)
# ============================================================
# 刷时长有两套完全不同的接口(实测抓包逐条确认):
#   - scoreTime(type=1, time=秒): 推进「看视频赚金币」(readScore) 进度, 响应只给金币, 不碰领现金
#   - readTime (type=2, time=秒): 推进「刷视频领现金」(readWithdraw) 进度, 才是老韩要的
BRUSH_SUBMIT_SECONDS = 60    # scoreTime(type=1) 每次上报秒数(看视频赚金币用, 与抓包一致)
BRUSH_INTERVAL       = 8   # 每轮上报的真实间隔(秒, 休眠用); 调小=刷得快但像机器人
READTIME_SECONDS     = 300  # readTime(type=2) 每次上报秒数(刷视频领现金用, 与真实抓包 time=300 一致=5分钟)
DEFAULT_MINUTES      = 30   # 单次刷视频默认时长(分钟), 可用 ZHILIAO 里 minutes= 覆盖

# ----- slot_price(ecpm) 随机范围配置(老韩调参区, 放最前) -----
# 领奖请求 media_extra 里的 slot_price = ecpm, 在以下区间随机生成(单位: 元, 保留1位小数, 与抓包格式一致)。
# 抓包实测参考范围: 367.71 ~ 3990.7; 可按需放宽/收紧。
SLOT_PRICE_MIN = 20000.0
SLOT_PRICE_MAX = 39999.9

# 任务结束提现目标金额(元): 红包/奖励领完后按此金额提现(bonusWithdraw), 老韩可调
WITHDRAW_TARGET = 1.5

# ----- 提现后保活(解决微信不到账问题) -----
# 提现后模拟app启动流程并轮询余额, 等待微信回调到账
KEEPALIVE_DURATION = 300   # 提现后保活总时长(秒), 默认5分钟; 可通过环境变量 KEEPALIVE_DURATION 覆盖
KEEPALIVE_INTERVAL = 20    # 每轮间隔(秒), 包含启动序列执行时间

def random_slot_price():
    """在 [SLOT_PRICE_MIN, SLOT_PRICE_MAX] 区间随机生成 ecpm(单位: 元, 保留1位小数)。"""
    return f"{round(random.uniform(SLOT_PRICE_MIN, SLOT_PRICE_MAX), 1)}"
# ============================================================

# pycryptodome 依赖检测
try:
    from Crypto.Cipher import DES, AES
    from Crypto.Util.Padding import pad, unpad
except Exception as _e:
    sys.stderr.write(
        "\n[错误] 缺少 pycryptodome: %s\n青龙请先在依赖管理里添加 pycryptodome, "
        "或执行: pip install pycryptodome\n" % _e
    )
    sys.exit(1)


# ============================================================
# 一、加解密算法 (原 zqkd_crypto.py, 已内联; SPKI 预计算硬编码)
# ============================================================

# APK 签名证书 SPKI 的 base64urlsafe (固定常量, 原由 base.apk 解析得到, 此处直接固化)
SPKI_B64 = ("MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA1E_mX-gaRQSNkmvPplyoSaa2k019s5jvfkw940Tf"
            "_gmjmxDQPyqJOePqK9gvA4lM0tdU5vGCCcQB6PgdgfIyhzs20kJzWSHtNJ0TvcM4f269UGVpZ0Ju8ErIy_ST"
            "6bFJLKLZzLewcttJUPwfvbeMtlKzDXa74zRkQqHS9MGZ4inKaFFILtOwFtJYHRzYRU5ctUP790FcxevpFK-q1"
            "5AXS3kRARqLmPUeh_BQUSqOZwMsMtMWyz56-c6ZBsLWKFGehfVjfZcAGVjeZ3nsEesXQf8J3xFFgULu9sj0Ou"
            "YgjolaRTdO9RJ-DMUWDwjdUAJLwaHPWZF2GsrixncrL9S8VQIDAQAB")

# 原生密钥 (libencrypt.so 反汇编提取, 与 jrkd 同源)
VERSION2_KEY = "jdvylqchJZrfw0o2DgAbsmCGUapF1YChc"
VERSION6_KEY = "zWpfzystJLrfw7o3SgGlMmGGPupK2YLhB"
VERSION15_KEY = ("AAAAB3NzaC1yc2EAAAADAQABAAABAQC1WAth281wjZj5XhGU9Iza5EXzOy5U/AKgGxF14svnCEWrTH6i"
                 "3lZd+lMTFLvTakGI5l1RJmutFRku6CvDVCEc7dJURVWsrgQTFNBuu0t5WOkoUY0zNa05pejDmBC4w4Msc"
                 "H2OexCrKfHNEYi/FpjBJv1bwjU0luxt/cvsjBjlthgY47I4KNy+T953CpBiYQmkSJZUBzsN2Zz+jEA+CvL"
                 "EK9BPHBlKcz0GupalgnHHSnS/JoUz8+RTjZr1O2sjSyrcg0LL+vWeCnJN07Uv4jJaTDqc6Ig1Mw+TJrrsAR"
                 "xoA+Frc66Qo7GFxACimuJ1LeCc9iFlMzZNZly3JxYAR019")

_RND = string.digits + string.ascii_letters  # 0-9 a-z A-Z


def _udp(v: Any) -> str:
    """对齐 Java URLEncoder.encode: UTF-8 字节; 字母数字与 -_.~ 不变, 空格->'+', 其余 %XX。"""
    bs = str(v).encode("utf-8")
    out = []
    for b in bs:
        if (48 <= b <= 57) or (65 <= b <= 90) or (97 <= b <= 122) or b in (45, 46, 95, 126):
            out.append(chr(b))
        elif b == 0x20:
            out.append("+")
        else:
            out.append("%%%02X" % b)
    return "".join(out)


def uzw(c: str) -> str:
    """复现 uc.uzw: 由固定 SPKI_B64 派生串(长度 36 - ord(c)%10)。"""
    b64 = SPKI_B64
    s = b64[9:]
    s = s[:len(s) - 5]
    s = s[len(s) - 36:]
    s = s[:len(s) - (ord(c) % 10)]
    return s


def des_key_for(cFtr: str) -> bytes:
    return uzw(cFtr).encode("utf-8")[:8]


def aes_key() -> bytes:
    return uzw("a").encode("utf-8")[:16]


def _jenc(v: Any) -> str:
    bs = str(v).encode("utf-8")
    out = []
    for b in bs:
        if (48 <= b <= 57) or (65 <= b <= 90) or (97 <= b <= 122) or b in (45, 46, 95, 126):
            out.append(chr(b))
        elif b == 0x20:
            out.append("+")
        else:
            out.append("%%%02X" % b)
    return "".join(out)


def _enc_params_str(params: Dict[str, Any]) -> str:
    return "&".join("%s=%s" % (k, _jenc(v)) for k, v in params.items())


def _ar_aor(key: str, params_str: str) -> str:
    """ar.aor(key, params): 返回 str3(12) + base64(DES-CBC(params))"""
    md5k = hashlib.md5(key.encode("utf-8")).digest()[:8]
    str3 = base64.urlsafe_b64encode(md5k).decode()
    iv = str3[:8].encode("utf-8")
    des_key = key.encode("utf-8")[:8]
    ct = DES.new(des_key, DES.MODE_CBC, iv).encrypt(pad(params_str.encode("utf-8"), 8))
    return str3 + base64.urlsafe_b64encode(ct).decode()


def _mou_aor(c: str, inner: str) -> str:
    """mou.aor: c + inner + (i 个随机尾字符), i=(ord(c)%10)%3"""
    i = (ord(c) % 10) % 3
    tail = "".join(random.choice(_RND) for _ in range(i))
    return c + inner + tail


def _encrypt_str(plaintext: str) -> str:
    """og(str): 任意明文串 -> zqkd_param (单层加密)。"""
    cFtr = random.choice(_RND)
    key = uzw(cFtr)
    inner = _ar_aor(key, plaintext)
    return _mou_aor(cFtr, inner)


def build_param(params: Dict[str, Any], extra: Optional[Dict[str, Any]] = None) -> str:
    p = dict(params)
    if extra:
        p.update(extra)
    params_str = _enc_params_str(p)
    return _encrypt_str(params_str)


def build_ssp_q(params: Dict[str, Any]) -> str:
    """SSP 广告信封 q (tbc-svc /v1/qm/ad/list)"""
    cFtr = random.choice(_RND)
    key = uzw(cFtr)
    return _mou_aor(cFtr, _ar_aor(key, _enc_params_str(params)))


# ===== 签名 =====
def sign_sorted_md5(params: Dict[str, Any], tail: str = VERSION2_KEY) -> str:
    S = "".join("%s=%s" % (k, params[k]) for k in sorted(params)
                if k != "sign" and params[k] != "")
    return hashlib.md5((S + tail).encode("utf-8")).hexdigest()


def token_sorted_md5(params: Dict[str, Any], tail: str = VERSION6_KEY) -> str:
    S = "".join("%s=%s" % (k, params[k]) for k in sorted(params)
                if k != "token" and params[k] != "")
    return hashlib.md5((S + tail).encode("utf-8")).hexdigest()


def make_jwt(claims: Dict[str, Any], key: str = VERSION15_KEY) -> str:
    header = base64.urlsafe_b64encode(
        json.dumps({"typ": "JWT", "alg": "HS512"}, separators=(",", ":")).encode()
    ).rstrip(b"=").decode()
    payload = base64.urlsafe_b64encode(
        json.dumps({k: _udp(v) for k, v in sorted(claims.items()) if v != ""},
                   separators=(",", ":")).encode()
    ).rstrip(b"=").decode()
    signing_input = "%s.%s" % (header, payload)
    sig = hmac.new(key.encode("utf-8"), signing_input.encode("utf-8"),
                   hashlib.sha512).digest()
    sig_b64 = base64.urlsafe_b64encode(sig).rstrip(b"=").decode()
    return "%s.%s" % (signing_input, sig_b64)


def build_signed_single_md5(params, extra=None) -> str:
    p = dict(params)
    if extra:
        p.update(extra)
    p["sign"] = sign_sorted_md5(p)
    return build_param(p)


def build_signed_single_token(params, extra=None) -> str:
    p = dict(params)
    if extra:
        p.update(extra)
    p["token"] = token_sorted_md5(p)
    return build_param(p)


def build_signed_single_jwt(params, extra=None) -> str:
    p = dict(params)
    if extra:
        p.update(extra)
    p["token"] = make_jwt(p)
    return build_param(p)


def build_signed_double_plain(device, business=None) -> str:
    full = dict(device)
    if business:
        full.update(business)
    full.pop("sign", None)
    full.pop("token", None)
    S = "".join("%s=%s" % (k, full[k]) for k in sorted(full) if full[k] != "")
    sign = S + VERSION2_KEY
    linked = {k: _udp(full[k]) for k in full}
    linked["sign"] = sign
    p_plaintext = "&".join("%s=%s" % (k, _udp(v)) for k, v in linked.items())
    p_value = _encrypt_str(p_plaintext)
    outer = dict(device)
    if business:
        outer.update(business)
    outer["p"] = p_value
    return build_param(outer)


# ===== 解密 =====
def dec_param(val: str) -> Dict[str, str]:
    cFtr = val[0]
    rest = val[1:]
    i = (ord(cFtr) % 10) % 3
    if i:
        rest = rest[:-i]
    str3 = rest[:12]
    body = rest[12:]
    iv = str3[:8].encode("utf-8")
    des_key = uzw(cFtr).encode("utf-8")[:8]
    raw = base64.urlsafe_b64decode(body)
    plain = unpad(DES.new(des_key, DES.MODE_CBC, iv).decrypt(raw), 8).decode("utf-8", "replace")
    out = {}
    for seg in plain.split("&"):
        if not seg:
            continue
        k, _, v = seg.partition("=")
        out[k] = v
    return out


def dec_resp(text: str) -> dict:
    text = text.strip()
    if text.startswith("{"):
        try:
            return json.loads(text)
        except Exception:
            pass
    raw = base64.b64decode(text)
    plain = unpad(AES.new(aes_key(), AES.MODE_ECB).decrypt(raw), 16).decode("utf-8", "replace")
    return json.loads(plain)


class StaticProvider:
    """sign_mode: none/md5/token/jwt/double —— 与原 zqkd_crypto.StaticProvider 一致。"""
    def encrypt(self, params, extra=None, need_sign=False, sign_mode="none"):
        if not need_sign:
            return build_param(params, extra)
        if sign_mode == "md5":
            return build_signed_single_md5(params, extra)
        if sign_mode == "token":
            return build_signed_single_token(params, extra)
        if sign_mode == "jwt":
            return build_signed_single_jwt(params, extra)
        if sign_mode == "double":
            return build_signed_double_plain(params, extra)
        raise ValueError("unknown sign_mode: %r" % sign_mode)

    def decrypt(self, zqkd_param):
        return dec_param(zqkd_param)

    def decrypt_resp(self, text):
        return dec_resp(text)


# ============================================================
# 二、基础配置 / 凭据 (全部走环境变量, 适配青龙依赖管理)
# ============================================================
LEMON = "https://lemon-api.52leho.com"
TBC = "https://tbc-svc.52leho.com"
APP_PKG = "new.liao.view"
UA = "android"
AD_UA = "okhttp/3.12.2"
MEDIA_APP_ID = "sspJA8HT1eIS373e"

DEVICE = {
    "app_name": "new_liao_view",
    "app_pkg": "new.liao.view",
    "app_version": "1.7.5",
    "app-version": "1.7.5",
    "appid": "wxdb76b366c1f1b2e4",
    "version_code": "45",
    "inner_version": "202608191646",
    "channel": "c1002",
    "device_brand": "Xiaomi",
    "device_model": "24053PY09C",
    "device_platform": "android",
    "device_type": "2",
    "os_version": "UKQ1.240116.001 release-keys",
    "os_api": "34",
    "resolution": "1236x2474",
    "dpi": "3.0",
    "memory": "11",
    "storage": "227.02",
    "language": "zh-CN",
    "carrier": "中国电信",
    "network_type": "WIFI",
    "access": "WIFI",
    "mobile_type": "1",
    "mi": "1",
    "is_debug": "0",
    "dev_mode": "0",
    "sim": "1",
    "rom_version": "UKQ1.240116.001 release-keys",
}
# 设备字段出厂默认副本(切换账号前重置用, 避免上账号设备信息残留)
DEVICE_DEFAULT = dict(DEVICE)

# ============================================================
# 凭据: 单变量 ZHILIAO (参数之间用 # 分隔, 每个参数为 key=value)
#  示例: ZHILIAO="uid=54475743#session=xxxx#union_id=yyy#zqkey=zzz#zqkey_id=aaa#s_ad=bbb#minutes=40"
#  支持 key: uid, session, union_id, user_cert, zqkey, zqkey_id, s_ad,
#           oaid, openudid, androidid, device_id, sm_device_id, app_device_id,
#           ssp_uid, minutes, media_extra(广告翻倍需 frida 捕获的 JSON)
#  未提供的 key 用下方默认值; 多账号只需改 uid/session 等真实值。
# ============================================================
def _parse_zhiliao_env():
    raw = (os.environ.get("ZHILIAO") or "").strip()
    kv = {}
    if raw:
        for _seg in raw.split("#"):
            _seg = _seg.strip()
            if not _seg or "=" not in _seg:
                continue
            _k, _v = _seg.split("=", 1)
            kv[_k.strip()] = _v.strip()
    return kv


_ENV = _parse_zhiliao_env()


def _cfg(name, default):
    """优先取 ZHILIAO 单变量里的 key; 旧版 ZQKD_* 多变量作为静默回退(已废弃, 建议统一用 ZHILIAO)。"""
    if name in _ENV and _ENV[name] != "":
        return _ENV[name]
    _old = os.environ.get("ZQKD_" + name.upper())
    if _old is not None and _old != "":
        return _old
    return default


UID = _cfg("uid", "")
SESSION = _cfg("session", "")
UNION_ID = _cfg("union_id", "")
USER_CERT = _cfg("user_cert", "0")
ZQKEY = _cfg("zqkey", "")
ZQKEY_ID = _cfg("zqkey_id", "")
S_AD = _cfg("s_ad", "")
OAID = _cfg("oaid", "")
OPENUDID = _cfg("openudid", "")
ANDROIDID = _cfg("androidid", "")
DEVICE_ID = _cfg("device_id", "")
SM_DEVICE_ID = _cfg("sm_device_id", "")
APP_DEVICE_ID = _cfg("app_device_id", "")
SSP_USER_ID = _cfg("ssp_uid", "64879461")
MEDIA_EXTRA_RAW = _ENV.get("media_extra")
MEDIA_VERIFY_RAW = _ENV.get("media_verify")  # 刷短剧领现金领奖的 media_verify(抓包112字节base64), 没配则留空, 老韩后续填抓包值
MINUTES_ENV = _ENV.get("minutes", os.environ.get("ZQKD_MINUTES", str(DEFAULT_MINUTES)))

# media_extra: 仅广告翻倍路径需要(由 frida 实时捕获)。青龙纯脚本主模式不依赖。
MEDIA_EXTRA_MAX_AGE = int(_ENV.get("me_max_age", os.environ.get("ZQKD_ME_MAX_AGE", "120")))

# ============================================================
# 凭据增强: ZHILIAO_PARAM 整串(zqkd_param)自动解密取参  ← 老韩需求
#   只需把抓包里请求体的 zqkd_param 整串设为环境变量 ZHILIAO_PARAM, 脚本自己解密拿参跑。
#   多账号: 多个 zqkd_param 整串用 & 分隔 (如 ZHILIAO_PARAM="串1&串2&串3"), 脚本逐个跑, 账号间随机等 30-60s。
#   覆盖优先级: ZHILIAO_PARAM(整串解密) > ZHILIAO(# 模式) > 内置默认值
#   注: zqkd_param 不含 PHPSESSID(session); 若服务端要求, 仍在 ZHILIAO 里补 session=xxx(两变量可同时设)
# ============================================================
def apply_param(raw):
    """用单个账号的 zqkd_param 整串(raw) 解密并【全量】填充全局凭据 + 重建 AUTH。
    多账号时每个账号跑之前调用一次即可(自动重置上账号的 UID/设备/session 等状态)。
    解析出的参数全部用解析值, 仅未解析到的 key 保留 ZHILIAO/# 模式或内置默认值。"""
    global UID, SESSION, UNION_ID, USER_CERT, ZQKEY, ZQKEY_ID, S_AD, OAID, OPENUDID, ANDROIDID, DEVICE_ID, SM_DEVICE_ID, APP_DEVICE_ID, SSP_USER_ID, AUTH
    # 1) 先把全部全局凭据重置回默认(来自 ZHILIAO/# 模式或内置), 防止上账号残留
    UID = _cfg("uid", "")
    SESSION = _cfg("session", "")
    UNION_ID = _cfg("union_id", "")
    USER_CERT = _cfg("user_cert", "0")
    ZQKEY = _cfg("zqkey", "")
    ZQKEY_ID = _cfg("zqkey_id", "")
    S_AD = _cfg("s_ad", "")
    OAID = _cfg("oaid", "")
    OPENUDID = _cfg("openudid", "")
    ANDROIDID = _cfg("androidid", "")
    DEVICE_ID = _cfg("device_id", "")
    SM_DEVICE_ID = _cfg("sm_device_id", "")
    APP_DEVICE_ID = _cfg("app_device_id", "")
    SSP_USER_ID = _cfg("ssp_uid", "64879461")
    DEVICE.clear()
    DEVICE.update(DEVICE_DEFAULT)
    # 2) 解密整串, 全量覆盖解析出的字段
    #    加密前客户端对参数值做过 URLEncoder 编码, 解密出的 value 是编码态(如 device_model=Mi+10、
    #    carrier=%E4%B8%AD...、s_ad 里的 %3D), 必须先 unquote_plus 还原成原始值再赋值, 否则脚本会二次编码
    #    导致与真实抓包不一致、甚至破坏 zqkey(base64 的 +/= 被编码)。
    _pd = dec_param(raw)
    for _k, _v in _pd.items():
        if _k in DEVICE:
            DEVICE[_k] = urllib.parse.unquote_plus(_v)
    if _pd.get("device_id"): DEVICE_ID = urllib.parse.unquote_plus(_pd["device_id"])
    if _pd.get("openudid"): OPENUDID = urllib.parse.unquote_plus(_pd["openudid"])
    if _pd.get("oaid"): OAID = urllib.parse.unquote_plus(_pd["oaid"])
    if _pd.get("androidid"): ANDROIDID = urllib.parse.unquote_plus(_pd["androidid"])
    if _pd.get("sm_device_id"): SM_DEVICE_ID = urllib.parse.unquote_plus(_pd["sm_device_id"])
    if _pd.get("app_device_id"): APP_DEVICE_ID = urllib.parse.unquote_plus(_pd["app_device_id"])
    if _pd.get("uid"): UID = urllib.parse.unquote_plus(_pd["uid"])
    if _pd.get("account") and not UID: UID = urllib.parse.unquote_plus(_pd["account"])
    if _pd.get("union_id"): UNION_ID = urllib.parse.unquote_plus(_pd["union_id"])
    if _pd.get("user_cert"): USER_CERT = urllib.parse.unquote_plus(_pd["user_cert"])
    if _pd.get("zqkey"): ZQKEY = urllib.parse.unquote_plus(_pd["zqkey"])
    if _pd.get("zqkey_id"): ZQKEY_ID = urllib.parse.unquote_plus(_pd["zqkey_id"])
    if _pd.get("s_ad"): S_AD = urllib.parse.unquote_plus(_pd["s_ad"])   # zqkd_param 里 s_ad 是 URL 编码(%3D=), 需解码
    # 3) 重建 AUTH(引用最新全局值)
    AUTH = {
        "uid": UID, "account": UID,
        "union_id": UNION_ID, "user_cert": USER_CERT,
        "zqkey": ZQKEY, "zqkey_id": ZQKEY_ID, "s_ad": S_AD,
        "oaid": OAID, "openudid": OPENUDID, "androidid": ANDROIDID,
        "device_id": DEVICE_ID, "sm_device_id": SM_DEVICE_ID, "app_device_id": APP_DEVICE_ID,
    }
    # 4) 调试: 打印覆盖情况
    _ACCT_KEYS = ("uid", "account", "union_id", "user_cert", "zqkey", "zqkey_id", "s_ad",
                  "oaid", "openudid", "androidid", "device_id", "sm_device_id", "app_device_id")
    _used_dev = sum(1 for _k in _pd if _k in DEVICE)
    _used_acct = sum(1 for _k in _pd if _k in _ACCT_KEYS)
    print(f"[凭据] 已自动解密取参: "
          f"uid={UID}")

# 模块级: 若配了 ZHILIAO_PARAM 且为单账号(无 &), 立即填充全局(保持向后兼容, 使 main 的 if not UID 检查可用)
_PARAM_RAW = (os.environ.get("ZHILIAO_PARAM") or "").strip()
if _PARAM_RAW and "&" not in _PARAM_RAW:
    try:
        apply_param(_PARAM_RAW)
    except Exception as _e:
        print(f"[警告] ZHILIAO_PARAM 解密失败: {_e} (回退 ZHILIAO/# 模式或默认值)")

AUTH = {
    "uid": UID, "account": UID,
    "union_id": UNION_ID, "user_cert": USER_CERT,
    "zqkey": ZQKEY, "zqkey_id": ZQKEY_ID, "s_ad": S_AD,
    "oaid": OAID, "openudid": OPENUDID, "androidid": ANDROIDID,
    "device_id": DEVICE_ID, "sm_device_id": SM_DEVICE_ID, "app_device_id": APP_DEVICE_ID,
}

# 任务业务字段 + sign_mode (原 task_config.json 已内联)
TASK = {
    "common": {},
    "scoreTime": {"sign_mode": "md5", "params": {"type": "1", "time": str(BRUSH_SUBMIT_SECONDS)}},
    "rewardView": {"sign_mode": "md5", "params": {"rid": ""}},
    "readTime": {"sign_mode": "md5", "params": {"type": "2", "time": str(READTIME_SECONDS)}},
    "readScore": {"sign_mode": "md5", "params": {}},
    "readWithdraw": {"sign_mode": "md5", "params": {"type": "2"}},
    "userinfo": {"sign_mode": "md5", "params": {}, "method": "GET"},
    "userdata": {"sign_mode": "md5", "params": {}, "method": "GET"},
    "bonusWithdraw": {"sign_mode": "jwt", "params": {"type": "61"}},
    # 红包余额专属提现(与 bonusWithdraw 不同池子): getPaymentList 查 red 余额与档位, redWithdraw 提现
    "getPaymentList": {"sign_mode": "jwt", "params": {}},
    "redWithdraw": {"sign_mode": "jwt", "params": {"type": "__DYNAMIC__", "score": "__DYNAMIC__"}},
    "adConversion": {"sign_mode": "md5", "params": {"extra": "[]", "is_install": "0"}},
    "rewardVideoCrv": {"sign_mode": "md5", "params": {}},
    "csjCpa": {"sign_mode": "md5", "params": {}},
    "ylhCpa": {"sign_mode": "md5", "params": {}},
    "getTaskList": {"sign_mode": "jwt", "params": {"install_alipay": "1"}},
    "machine": {"sign_mode": "md5", "params": {}},
    "biTf": {"sign_mode": "none", "params": {}},
    "BiCollect": {"sign_mode": "double", "params": {}},
    "exchange": {"sign_mode": "double", "params": {}},
    "getFeedBrowseTaskList": {"sign_mode": "double", "params": {}},
    "adlickstart": {"sign_mode": "double", "params": {"task_id": "__DYNAMIC__"}},
    "adlickend": {"sign_mode": "double", "params": {"task_id": "__DYNAMIC__", "task_click": "0", "task_click_num": "0"}},
    "bannerstatus": {"sign_mode": "double", "params": {"task_id": "__DYNAMIC__", "page_click": "3", "page_slide": "9", "page_stay": "101"}},
    "readRewardClaim": {"sign_mode": "double", "params": {"action": "task_score_optimize", "param": "", "video_id": "0", "media_extra": "", "extra": ""}},
    "readWithdrawClaim": {"sign_mode": "double", "params": {"action": "read_withdraw", "param": "", "video_id": "0", "media_extra": "__DYNAMIC__", "extra": ""},
        "media_extra_template": {"media_app_id": "sspJA8HT1eIS373e", "media_scene_id": "010", "media_slot_id": "20120118", "media_verify": "__DYNAMIC__", "position_id": "1032", "slot_platform": "BQT", "slot_price": "__RANDOM_SLOT_PRICE__", "slot_type": "RewardVideo", "tactics_mold": "bidding"}},
    "toGetReward": {"sign_mode": "double", "params": {"action": "bonus_video_ad_award", "param": "1", "video_id": "0", "media_extra": "__DYNAMIC__"},
        "media_extra_template": {"media_app_id": "sspJA8HT1eIS373e", "media_replace_score": 0, "media_scene_id": "47", "media_slot_id": "986301995", "media_verify": "__DYNAMIC__", "params_action_type": "DEEPLINK", "params_app_name": "淘宝", "params_app_package": "com.taobao.taobao", "params_slot_type": "RewardVideo", "params_storage": {}, "position_id": "1032", "slot_platform": "CSJ", "slot_price": "367.71", "slot_type": "RewardVideo", "tactics_mold": "bidding"}},
    "openRedEnvelopeCash": {"sign_mode": "md5", "params": {}},
    "claimRedEnvelope": {"sign_mode": "md5", "params": {"index": "__DYNAMIC__", "media_extra": "__DYNAMIC__"},
        "media_extra_template": {"media_app_id": "sspJA8HT1eIS373e", "media_replace_score": 0, "media_scene_id": "010", "media_slot_id": "20120118", "media_verify": "__DYNAMIC__", "params_action_type": "DOWNLOAD", "params_app_name": "\u767e\u5ea6", "params_app_package": "com.baidu.searchbox", "params_slot_type": "RewardVideo", "params_storage": {}, "position_id": "1032", "slot_platform": "BQT", "slot_price": "__RANDOM_SLOT_PRICE__", "slot_type": "RewardVideo", "tactics_mold": "bidding"}},
    "adlist": {"params": {}},
    # 启动序列新端点(抓包4.har: 手动进app到账流程)
    "getBonusPaymentList": {"sign_mode": "jwt", "params": {}},
    "configInfo": {"sign_mode": "none", "params": {}, "method": "GET"},
    "configAudit": {"sign_mode": "jwt", "params": {}},
    "configDid": {"sign_mode": "jwt", "params": {}},
    "countStart": {"sign_mode": "md5", "params": {}},
    "getinfo": {"sign_mode": "none", "params": {}, "method": "GET"},
    "mediaConfig": {"sign_mode": "none", "params": {}, "method": "GET"},
    "appUpdate": {"sign_mode": "jwt", "params": {}},
}


# ============================================================
# 三、HTTP 通用层
# ============================================================
_idx = [0]
def _next_index():
    _idx[0] += 1
    return str(_idx[0])


# ============================================================
# session 自动获取: PHPSESSID 由服务端在响应(Set-Cookie 头)下发,
# 脚本首次请求后自动捕获并保存, 后续请求自动带上 —— 无需手动配置
# (环境变量 session= 仍可预填以复用旧会话, 但非必需)
# ============================================================
def _capture_session_cookie(resp):
    """从响应的 Set-Cookie 头自动提取 PHPSESSID 并写入全局 SESSION, 实现 session 自动获取。"""
    global SESSION
    try:
        cookies = resp.headers.get_all("Set-Cookie") or []
    except Exception:
        cookies = []
    if not cookies:
        single = resp.headers.get("Set-Cookie")
        if single:
            cookies = [single]
    for c in cookies:
        head = c.split(";")[0].strip()
        if head.lower().startswith("phpsessid="):
            val = head[len("PHPSESSID="):]
            if val and val != SESSION:
                SESSION = val
                print(f"[session] 已自动更新 PHPSESSID")
            return


# 响应体里可能回传的 session 字段名(兜底, 大多数情况 session 在 Set-Cookie 头)
_SESS_BODY_KEYS = ("PHPSESSID", "phpsessid", "session", "sessid", "sess_id")
def _update_session_from_resp_obj(obj):
    """兜底: 若解密响应体里也回传了 session 字段, 同步更新全局 SESSION。"""
    global SESSION
    if not isinstance(obj, dict):
        return
    candidates = []
    items = obj.get("items")
    if isinstance(items, dict):
        candidates.append(items)
    candidates.append(obj)
    for c in candidates:
        for k in _SESS_BODY_KEYS:
            v = c.get(k)
            if v and isinstance(v, str) and len(v) >= 8 and v != SESSION:
                SESSION = v
                print(f"[session] 已自动获取PHPSESSID")
                return


def _http(path, base, task_key, provider, runtime_extra=None, plain=False):
    cfg = TASK.get(task_key, {})
    sign_mode = cfg.get("sign_mode", "none")
    params = dict(TASK.get("common", {}))
    params.update(cfg.get("params", {}))
    if runtime_extra:
        params.update(runtime_extra)

    common = dict(DEVICE)
    common.update(AUTH)
    common["request_time"] = str(int(time.time()))
    if sign_mode == "md5":
        common["device_type"] = "2"
        common["channel_code"] = "c1002"
    else:
        common["device_type"] = "android"
    if sign_mode == "double":
        common["index"] = _next_index()
    if task_key == "getFeedBrowseTaskList":
        common["support_wechat"] = "0"
    if not common.get("uid"):
        common.pop("uid", None)
        common.pop("account", None)

    zq = provider.encrypt(common, extra=params, need_sign=(sign_mode != "none"), sign_mode=sign_mode)
    url = base + path
    data = ("zqkd_param=" + urllib.parse.quote(zq, safe="")).encode("utf-8")
    headers = {
        "User-Agent": UA,
        "device-platform": "android",
        "app-pkg": APP_PKG,
        "Accept-Encoding": "gzip",
        "Content-Type": "application/x-www-form-urlencoded",
    }
    if SESSION:
        headers["Cookie"] = f"PHPSESSID={SESSION}"
    req = urllib.request.Request(url, data=data, method="POST")
    for k, v in headers.items():
        req.add_header(k, v)
    try:
        resp = urllib.request.urlopen(req, timeout=30)
        raw = resp.read()
        if resp.headers.get("Content-Encoding") == "gzip":
            raw = gzip.decompress(raw)
        text = raw.decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return {"success": False, "http": e.code, "raw": e.read().decode("utf-8", "replace")[:200]}
    _capture_session_cookie(resp)
    if plain:
        try:
            return json.loads(text)
        except Exception:
            return {"success": False, "error": "json_fail", "raw": text[:200]}
    r = provider.decrypt_resp(text)
    _update_session_from_resp_obj(r)
    return r


def _http_get(path, base, task_key, provider, runtime_extra=None):
    """GET 变体: zqkd_param 放在 URL query 里(适用于 userinfo/userdata 等 @GET 接口)。"""
    cfg = TASK.get(task_key, {})
    sign_mode = cfg.get("sign_mode", "none")
    params = dict(TASK.get("common", {}))
    params.update(cfg.get("params", {}))
    if runtime_extra:
        params.update(runtime_extra)
    common = dict(DEVICE)
    common.update(AUTH)
    common["request_time"] = str(int(time.time()))
    if sign_mode == "md5":
        common["device_type"] = "2"
        common["channel_code"] = "c1002"
    else:
        common["device_type"] = "android"
    if not common.get("uid"):
        common.pop("uid", None)
        common.pop("account", None)
    zq = provider.encrypt(common, extra=params, need_sign=(sign_mode != "none"), sign_mode=sign_mode)
    url = base + path + "?zqkd_param=" + urllib.parse.quote(zq, safe="")
    headers = {
        "User-Agent": UA,
        "device-platform": "android",
        "app-pkg": APP_PKG,
        "Accept-Encoding": "gzip",
    }
    if SESSION:
        headers["Cookie"] = f"PHPSESSID={SESSION}"
    req = urllib.request.Request(url, method="GET")
    for k, v in headers.items():
        req.add_header(k, v)
    try:
        resp = urllib.request.urlopen(req, timeout=30)
        raw = resp.read()
        if resp.headers.get("Content-Encoding") == "gzip":
            raw = gzip.decompress(raw)
        text = raw.decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return {"success": False, "http": e.code, "raw": e.read().decode("utf-8", "replace")[:200]}
    _capture_session_cookie(resp)
    r = provider.decrypt_resp(text)
    _update_session_from_resp_obj(r)
    return r


def _brief(r):
    if not isinstance(r, dict):
        return str(r)[:80]
    code = r.get("code") or r.get("error_code")
    msg = r.get("message", "")
    if code in (0, "0") or msg in ("执行成功", "success"):
        return "成功"
    if code == 10001 or "参数" in str(msg):
        return "参数错误"
    if code == 10002 or "登录" in str(msg) or "session" in str(msg).lower():
        return "登录失效"
    if "message" in r:
        return f"{msg}" if msg else f"错误码{code}"
    if "items" in r and isinstance(r["items"], dict):
        keys = list(r["items"].keys())[:4]
        return "数据:" + ",".join(keys)
    return json.dumps(r, ensure_ascii=False)[:80]


def _to_float(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


# ============================================================
# 四、广告检测 (SSP 明文) —— 仅广告翻倍路径使用
# ============================================================
def _ssp_params():
    sm_md5 = hashlib.md5(SM_DEVICE_ID.encode("utf-8")).hexdigest()
    partner_extra = json.dumps({
        "inner_version": DEVICE["inner_version"], "app_version": DEVICE["app_version"],
        "partner_sm_device_id_md5": sm_md5, "partner_device_id": DEVICE_ID,
        "app_device_id": APP_DEVICE_ID, "oaid": OAID,
    }, separators=(",", ":"))
    media_extra = json.dumps({
        "multiuser_mode": False, "proxy_mode": False, "battery_anomaly_mode": False,
        "connection_proxy_mode": False, "adb_mode": False, "vpn_mode": False,
        "automation_tool_mode": False, "root_mode": False, "mock_location_mode": False,
        "hook_mode": 0, "accessibility_mode": False, "usb_connected_mode": False,
        "emulator_mode": False, "develop_mode": False,
    }, separators=(",", ":"))
    return {
        "device_android_id": ANDROIDID, "device_brand": DEVICE["device_brand"], "device_dpi": "480",
        "device_language": DEVICE["language"], "device_model": DEVICE["device_model"],
        "device_oaid": OAID, "device_orientation": "Portrait",
        "device_screen": DEVICE["resolution"].replace("x", "*"), "device_time": str(int(time.time())),
        "media_app_id": MEDIA_APP_ID, "media_extra_params": media_extra,
        "media_sdk_mode": "Release", "media_sdk_time": "2026-08-19 02:52", "media_sdk_version": "2.1.6.2",
        "media_user_id": SSP_USER_ID, "partner_channel": DEVICE["channel"],
        "partner_extra_params": partner_extra, "partner_launch_user": "1",
        "partner_package_name": APP_PKG, "partner_user_id": UID, "partner_version_name": DEVICE["app_version"],
        "system_api": DEVICE["os_api"], "system_display": DEVICE["os_version"], "system_type": "1",
        "system_version": "14", "position_id": "1032", "tactics_index": "-1",
    }


def detect_ad():
    q = build_ssp_q(_ssp_params())
    body = f"media_app_id={MEDIA_APP_ID}&q={urllib.parse.quote(q, safe='')}"
    url = TBC + "/v1/qm/ad/list"
    headers = {"User-Agent": AD_UA, "device-platform": "android",
               "Content-Type": "application/x-www-form-urlencoded", "Accept-Encoding": "gzip"}
    if SESSION:
        headers["Cookie"] = f"PHPSESSID={SESSION}"
    req = urllib.request.Request(url, data=body.encode("utf-8"), method="POST")
    for k, v in headers.items():
        req.add_header(k, v)
    try:
        resp = urllib.request.urlopen(req, timeout=30)
        raw = resp.read()
        if resp.headers.get("Content-Encoding") == "gzip":
            raw = gzip.decompress(raw)
        r = json.loads(raw.decode("utf-8", "replace"))
    except Exception as e:
        print(f"  [广告] ad/list 异常: {e}")
        return None
    if r.get("code") not in (200, "200") or not r.get("data"):
        return None
    return r.get("data")


def _load_captured_media_extra():
    raw = MEDIA_EXTRA_RAW
    if raw:
        try:
            obj = json.loads(raw)
            me = obj.get("media_extra", obj) if isinstance(obj, dict) else obj
            return json.dumps(me, ensure_ascii=False, separators=(",", ":"))
        except Exception:
            return raw
    return None


def build_media_extra(ad_data):
    captured = _load_captured_media_extra()
    if captured:
        return captured
    tmpl = TASK.get("toGetReward", {}).get("media_extra_template", {})
    me = dict(tmpl)
    me["media_verify"] = ad_data.get("position_config_verify", me.get("media_verify", ""))
    if ad_data.get("position_id"):
        me["position_id"] = str(ad_data["position_id"])
    me["slot_price"] = random_slot_price()  # ecpm 随机化
    return json.dumps(me, ensure_ascii=False, separators=(",", ":"))


def build_read_withdraw_media_extra():
    """构造「刷视频领现金」(read_withdraw) 领奖 media_extra: slot_price 随机, media_verify 取 ZHILIAO 配置(抓包112字节base64)。"""
    tmpl = TASK.get("readWithdrawClaim", {}).get("media_extra_template", {})
    me = dict(tmpl)
    me["slot_price"] = random_slot_price()
    me["media_verify"] = MEDIA_VERIFY_RAW or me.get("media_verify", "")
    return json.dumps(me, ensure_ascii=False, separators=(",", ":"))


def build_claim_media_extra(ad_data):
    """构造「开红包领现金」claimRedEnvelope 的 media_extra: slot_price 随机, media_verify 取 ZHILIAO 配置(抓包重放)或 detect_ad 返回。"""
    tmpl = TASK.get("claimRedEnvelope", {}).get("media_extra_template", {})
    me = dict(tmpl)
    me["media_verify"] = MEDIA_VERIFY_RAW or (ad_data or {}).get("position_config_verify", me.get("media_verify", ""))
    me["slot_price"] = random_slot_price()
    return json.dumps(me, ensure_ascii=False, separators=(",", ":"))


# ============================================================
# 五、任务实现 (Bot)
# ============================================================
class Bot:
    def __init__(self, provider):
        self.p = provider
        self.total_seconds = 0
        self.username = ""  # 微信昵称, 提现用; 第一轮从 userinfo 获取
        # 本次运行统计
        self.stats = {
            "cash_gained": 0.0,       # 刷视频领现金收入(元)
            "red_gained": 0.0,        # 红包收入(元)
            "withdraw_amount": 0.0,   # 提现金额(元)
            "withdraw_ok": False,     # 提现是否成功
            "bonus_withdraw": 0.0,    # 小金库提现金额(元)
            "bonus_withdraw_ok": False,
            "red_withdraw": 0.0,      # 红包余额提现金额(元)
            "red_withdraw_ok": False,
        }

    def score_time_once(self):
        return _http("/v18/feed/scoreTime.json", LEMON, "scoreTime", self.p)

    def read_time_once(self):
        # 推进「刷视频领现金」(readWithdraw) 真实进度, 参数 type=2 time=<秒>(实测抓包 time=300)
        return _http("/v18/feed/readTime.json", LEMON, "readTime", self.p)

    def reward_view_once(self):
        return _http("/v18/feed/rewardView.json", LEMON, "rewardView", self.p)

    def machine_once(self):
        return _http("/v15/config/machine.json", LEMON, "machine", self.p)

    def bi_tf_once(self):
        return _http("/v18/bi/tf.json", LEMON, "biTf", self.p)

    def bi_collect_once(self):
        return _http("/v18/Bi/collect.json", LEMON, "BiCollect", self.p)

    def exchange_once(self):
        return _http("/v17/TaskScoreOptimize/exchange.json", LEMON, "exchange", self.p)

    def get_bonus_payment_list(self):
        return _http("/v17/UserRed/getBonusPaymentList.json", LEMON, "getBonusPaymentList", self.p)

    def config_info_once(self):
        return _http_get("/v15/config/info.json", LEMON, "configInfo", self.p)

    def config_audit_once(self):
        return _http("/v15/config/audit.json", LEMON, "configAudit", self.p)

    def config_did_once(self):
        return _http("/v15/config/did.json", LEMON, "configDid", self.p)

    def count_start_once(self):
        return _http("/v6/count/start.json", LEMON, "countStart", self.p)

    def getinfo_once(self):
        return _http_get("/v3/user/getinfo.json", LEMON, "getinfo", self.p)

    def media_config_once(self):
        return _http_get("/v15/config/media_config.json", LEMON, "mediaConfig", self.p)

    def app_update_once(self):
        return _http("/V17/Menu/appUpdate.json", LEMON, "appUpdate", self.p)

    def read_score_once(self):
        return _http("/v18/task/readScore.json", LEMON, "readScore", self.p)

    def read_withdraw_once(self):
        return _http("/v18/task/readWithdraw.json", LEMON, "readWithdraw", self.p)

    def get_task_list(self):
        return _http("/v17/TaskScoreOptimize/getTaskList.json", LEMON, "getTaskList", self.p)

    def csj_cpa_once(self):
        return _http("/v18/task/csjCpa.json", LEMON, "csjCpa", self.p)

    def ad_conversion_once(self):
        return _http("/v18/task/adConversion.json", LEMON, "adConversion", self.p)

    def reward_video_crv_once(self):
        return _http("/v18/task/rewardVideoCrv.json", LEMON, "rewardVideoCrv", self.p)

    def claim_read_reward(self, max_rounds=8):
        """循环领取 readScore 中 status=1 的待领档位(非广告类, 纯脚本, 无需 media_verify)。"""
        gained = 0
        for i in range(max_rounds):
            r = _http("/v18/task/readScore.json", LEMON, "readScore", self.p, {"type": "2"})
            items = (r.get("items") or {})
            lst = items.get("list") or []
            claimable = [t for t in lst if str(t.get("status")) == "1"]
            if not claimable:
                break
            sra = items.get("send_reward_action") or {"reward_action": "look_video_article_get_score"}
            if isinstance(sra, str):
                sra = {"reward_action": sra}
            param = json.dumps(sra, ensure_ascii=False, separators=(",", ":"))
            cfg = dict(TASK.get("readRewardClaim", {}))
            cfg_params = dict(cfg.get("params", {}))
            cfg_params["param"] = param
            cfg["params"] = cfg_params
            TASK["readRewardClaim"] = cfg
            g = _http("/v5/CommonReward/toGetReward.json", LEMON, "readRewardClaim", self.p)
            g_items = (g.get("items") or {})
            sc = g_items.get("score")
            if g.get("success") or g.get("error_code") in (0, "0"):
                try:
                    gained += int(float(sc))
                except (TypeError, ValueError):
                    pass
                print(f"  [领金币] 第{i+1}次 +{sc} (累计 {gained})")
            else:
                print(f"  [领金币] 第{i+1}次领取失败: {g.get('message')}")
                break
        if gained:
            print(f"[领金币] 本轮共领 {gained} 金币")
        return gained

    # ---------- 刷视频领现金(福利页/刷短剧领现金) 完整链路 ----------

    def query_cash_task(self):
        """查询「刷视频领现金」任务进度(readWithdraw)。
        返回: {milestones, claimable(list), top_value, top_reached(bool), all_done(bool), title, raw}
        milestones 每项: {score, value(累计秒), status(0未达/1可领/2已领), title}
        """
        r = _http("/v18/task/readWithdraw.json", LEMON, "readWithdraw", self.p, {"type": "2"})
        items = (r.get("items") or {})
        lst = items.get("list") or []
        milestones = []
        for m in lst:
            try:
                val = int(m.get("value", 0))
            except (TypeError, ValueError):
                val = 0
            try:
                st = int(m.get("status", 0))
            except (TypeError, ValueError):
                st = 0
            milestones.append({"score": m.get("score"), "value": val, "status": st, "title": m.get("title", "")})
        if not milestones:
            return {"milestones": [], "claimable": [], "top_value": 0, "top_reached": False,
                    "all_done": False, "title": items.get("title", ""), "raw": r}
        top_value = max(m["value"] for m in milestones)
        top_reached = any(m["value"] == top_value and m["status"] != 0 for m in milestones)
        all_done = not any(m["status"] == 0 for m in milestones)  # 无未达成里程碑 = 任务结束
        claimable = [m for m in milestones if m["status"] == 1]
        return {"milestones": milestones, "claimable": claimable, "top_value": top_value,
                "top_reached": top_reached, "all_done": all_done, "title": items.get("title", "")}

    def get_userinfo(self):
        r = _http_get("/v3/user/userinfo.json", LEMON, "userinfo", self.p)
        items = (r.get("items") or {})
        # 小金库余额 = mini_balance(随刷视频领现金增长, 提现来源);
        #   cash_balance(11.46 恒定) 是累计冻结值, money(2.39) 是金币钱包, 均非小金库
        return {"nickname": items.get("nickname", ""),
                "treasury": _to_float(items.get("mini_balance")), "raw": r}

    def get_userdata(self):
        r = _http_get("/v15/user/userdata.json", LEMON, "userdata", self.p)
        items = (r.get("items") or {})
        # 小金库余额 = mini(与 mini_balance 同值); money 是金币钱包, cash_balance 是累计, 均不用于提现
        return {"treasury": _to_float(items.get("mini")), "raw": r}

    def get_cash_balance(self):
        """小金库余额(随刷视频领现金增长, 提现来源):
           userdata.mini 优先, 回退 userinfo.mini_balance。返回 (treasury, None)。
           注意: cash_balance(11.46) 是累计冻结值, money(2.39) 是金币钱包, 二者均非小金库。"""
        try:
            d = self.get_userdata()
            if d["treasury"] is not None:
                return d["treasury"], None
        except Exception:
            pass
        try:
            u = self.get_userinfo()
            return u["treasury"], None
        except Exception:
            return None, None

    def withdraw_cash(self, amount_yuan, username):
        """提现(bonusWithdraw): score=金额(单位分), type=61, username=微信昵称, token=JWT(设备字段)。"""
        try:
            cents = int(round(float(amount_yuan) * 100))
        except (TypeError, ValueError):
            print(f"  [提现] 金额 {amount_yuan} 无效, 跳过")
            return False
        if cents <= 0:
            print(f"  [提现] 金额 {amount_yuan} 无效, 跳过")
            return False
        common = dict(DEVICE)
        common.update(AUTH)
        common["request_time"] = str(int(time.time()))
        token = make_jwt({k: common[k] for k in common})  # JWT 仅设备字段(与抓包一致)
        business = {"score": str(cents), "type": "61", "username": username, "token": token}
        allp = dict(common)
        allp.update(business)
        zq = build_param(allp)
        url = LEMON + "/v17/UserRed/bonusWithdraw.json"
        data = ("zqkd_param=" + urllib.parse.quote(zq, safe="")).encode("utf-8")
        headers = {"User-Agent": UA, "device-platform": "android", "app-pkg": APP_PKG,
                   "Accept-Encoding": "gzip", "Content-Type": "application/x-www-form-urlencoded"}
        if SESSION:
            headers["Cookie"] = f"PHPSESSID={SESSION}"
        req = urllib.request.Request(url, data=data, method="POST")
        for k, v in headers.items():
            req.add_header(k, v)
        try:
            resp = urllib.request.urlopen(req, timeout=30)
            raw = resp.read()
            if resp.headers.get("Content-Encoding") == "gzip":
                raw = gzip.decompress(raw)
            text = raw.decode("utf-8", "replace")
        except urllib.error.HTTPError as e:
            print(f"  [提现] HTTP {e.code}: {e.read().decode('utf-8','replace')[:200]}")
            return False
        _capture_session_cookie(resp)
        r = self.p.decrypt_resp(text)
        items = (r.get("items") or {})
        if r.get("success") or r.get("error_code") in (0, "0"):
            print(f"  [提现] 成功: {amount_yuan}元 → 微信 (单号{items.get('order_id', '')})")
            self.stats["withdraw_amount"] += float(amount_yuan)
            self.stats["withdraw_ok"] = True
            self.stats["bonus_withdraw"] += float(amount_yuan)
            self.stats["bonus_withdraw_ok"] = True
            return True
        print(f"  [提现] 失败: {_brief(r)}")
        return False

    def get_red_payment_list(self):
        """查红包余额与提现档位: /v17/UserRed/getPaymentList.json (jwt)。
        返回 items: red(红包余额, 元), red_payment=[{type,score,money,status}], draw_money(已提)。
        抓包实证: red=2.05 时 red_payment 含 type41/score150/money1.5; redWithdraw(type=41,score=150) 提1.5成功。
        注: 该接口运行时偶发 10001 参数错误, 失败时静默返回 {} (red_withdraw 用 TIERS 兜底下仍可读档提现, 不打印吓人日志)。"""
        r = _http("/v17/UserRed/getPaymentList.json", LEMON, "getPaymentList", self.p, {})
        if r.get("success") or r.get("error_code") in (0, "0"):
            return (r.get("items") or {})
        return {}

    def red_withdraw(self, amount_yuan):
        """红包余额提现(专属接口 redWithdraw, 非 bonusWithdraw):
        先查 getPaymentList 展示红包余额与档位(失败时静默降级, 不影响提现);
        选档优先 red_payment 精确匹配, 否则用抓包实证固定档位兜底; redWithdraw(type,score) 提现。
        抓包实证 type41/score150 => 提1.5元(已实机成功 order=64846136)。"""
        items = self.get_red_payment_list()
        bal = items.get("red")
        try:
            bal_f = float(bal)
        except (TypeError, ValueError):
            bal_f = None
        # getPaymentList 失败时, 用小金库余额兜底判断(红包子池余额通常 <= 小金库)
        if bal_f is None:
            try:
                fallback_bal, _ = self.get_cash_balance()
                if fallback_bal is not None:
                    bal_f = fallback_bal
                    print(f"  [提现] getPaymentList未返回, 用小金库余额{fallback_bal}元兜底")
            except Exception:
                pass
        red_pay = items.get("red_payment") or []
        if bal is not None:
            print(f"\n[提现] 红包余额={bal}元, 目标提现={amount_yuan}元")
        else:
            print(f"\n[提现] 红包余额查询未返回(沿用抓包档位), 目标提现={amount_yuan}元")
        # 抓包实证红包提现档位(2026-08-25): money(元) -> (type, score)
        #   实测 red_payment=[type40/0.3元, type41/1.5元, type42/10元]; redWithdraw(41,150) 提1.5成功
        TIERS = {0.3: ("40", "30"), 1.5: ("41", "150"), 10.0: ("42", "1000")}
        # 选档位: 1) red_payment 精确匹配 2) 抓包固定档位兜底(绕过 getPaymentList 失败时仍可读档)
        target = None
        for p in red_pay:
            try:
                if abs(float(p.get("money")) - float(amount_yuan)) < 1e-6:
                    target = p
                    break
            except (TypeError, ValueError):
                continue
        if not target:
            best = min(TIERS.keys(), key=lambda x: abs(x - float(amount_yuan)))
            if abs(best - float(amount_yuan)) < 1e-6:
                t, s = TIERS[best]
                target = {"type": t, "score": s, "money": best}
        if not target:
            print(f"  [提现] 未找到金额={amount_yuan}元的红包提现档位; 可用: "
                  f"{[ (p.get('money'), p.get('type')) for p in red_pay ]}")
            return False
        typ = str(target.get("type"))
        score = str(target.get("score"))
        amt = target.get("money")
        if bal_f is not None and bal_f + 1e-9 < float(amt):
            print(f"  [提现] 红包余额不足 {bal_f}元 < {amt}元, 跳过")
            return False
        print(f"  [提现] 选档 type={typ}/score={score} (抓包实证)")
        # 构造请求(仿 withdraw_cash 的 JWT 写法, token 含业务参数以贴近抓包)
        common = dict(DEVICE)
        common.update(AUTH)
        common["request_time"] = str(int(time.time()))
        business = {"type": typ, "score": score, "username": self.username or ""}
        allp = dict(common)
        allp.update(business)
        token = make_jwt({k: allp[k] for k in allp})
        allp["token"] = token
        zq = build_param(allp)
        url = LEMON + "/v17/UserRed/redWithdraw.json"
        data = ("zqkd_param=" + urllib.parse.quote(zq, safe="")).encode("utf-8")
        headers = {"User-Agent": UA, "device-platform": "android", "app-pkg": APP_PKG,
                   "Accept-Encoding": "gzip", "Content-Type": "application/x-www-form-urlencoded"}
        if SESSION:
            headers["Cookie"] = f"PHPSESSID={SESSION}"
        req = urllib.request.Request(url, data=data, method="POST")
        for k, v in headers.items():
            req.add_header(k, v)
        try:
            resp = urllib.request.urlopen(req, timeout=30)
            raw = resp.read()
            if resp.headers.get("Content-Encoding") == "gzip":
                raw = gzip.decompress(raw)
            text = raw.decode("utf-8", "replace")
        except urllib.error.HTTPError as e:
            print(f"  [提现] HTTP {e.code}: {e.read().decode('utf-8','replace')[:200]}")
            return False
        _capture_session_cookie(resp)
        r = self.p.decrypt_resp(text)
        items_r = (r.get("items") or {})
        if r.get("success") or r.get("error_code") in (0, "0"):
            print(f"  [提现] 红包提现成功: {amt}元 → 微信 (单号{items_r.get('order_id', '')})")
            self.stats["withdraw_amount"] += float(amt)
            self.stats["withdraw_ok"] = True
            self.stats["red_withdraw"] += float(amt)
            self.stats["red_withdraw_ok"] = True
            return True
        print(f"  [提现] 红包提现失败: {_brief(r)}")
        return False

    def maybe_withdraw(self, task_ended=False):
        """按老韩规则提现:
           - 平时: 小金库余额 >= 0.8 元 -> 提现(全额)
           - 任务结束且余额 > 0.1 元 -> 即使不足 0.8 也提现
        """
        bal, _ = self.get_cash_balance()
        if bal is None:
            print("  [提现] 查不到余额, 跳过")
            return False
        if task_ended:
            if bal > 0.1:
                print(f"  [提现] 任务结束, 余额 {bal}元 > 0.1, 触发提现")
                return self.withdraw_cash(bal, self.username)
            print(f"  [提现] 任务结束, 余额 {bal}元 <= 0.1, 不提")
            return False
        if bal >= 0.8:
            print(f"  [提现] 余额 {bal}元 >= 0.8, 触发提现")
            return self.withdraw_cash(bal, self.username)
        print(f"  [提现] 余额 {bal}元 < 0.8, 暂不提(继续领)")
        return False

    def maybe_withdraw_target(self, target=WITHDRAW_TARGET):
        """任务结束按目标金额提现: 走红包余额专属提现接口 redWithdraw(非 bonusWithdraw)。"""
        return self.red_withdraw(target)

    def claim_all_cash_stages(self):
        """循环领取「刷视频领现金」全部可领阶段奖励(共 12 个里程碑)。
        每领一个就检查小金库余额, >= 0.8 元立即提现。
        遇到限速(如"不要着急嘛")随机等待 15-20s 后重试, 不卡在第一次失败。
        返回领取总额(元)。
        """
        gained = 0.0
        attempts = 0
        MAX_ATTEMPTS = 60  # 防止极端情况下死循环
        rate_keys = ("不要着急", "着急", "频繁", "太快", "过快", "稍后", "稍等", "稍候",
                     "请稍", "retry", "limit", "操作过快", "too frequent", "rate")
        while attempts < MAX_ATTEMPTS:
            attempts += 1
            info = self.query_cash_task()
            claimable = info.get("claimable") or []
            if not claimable:
                left = sum(1 for m in info["milestones"] if m["status"] == 0)
                print(f"  [领现金] 无可领阶段(待达成 {left} 个)")
                break
            g = _http("/v5/CommonReward/toGetReward.json", LEMON, "readWithdrawClaim", self.p,
                      {"media_extra": build_read_withdraw_media_extra()})
            g_items = (g.get("items") or {})
            sc = g_items.get("score")
            if g.get("success") or g.get("error_code") in (0, "0"):
                try:
                    amt = float(sc)
                except (TypeError, ValueError):
                    amt = 0.0
                gained += amt
                print(f"  [领现金] +{sc}元 (累计 {gained:.2f}元)")
                self.maybe_withdraw(task_ended=False)  # 每领一个查余额
                continue  # 继续领下一个可领阶段
            msg = str(g.get("message", ""))
            # 限速类 -> 等待重试(同一阶段)
            if any(k in msg for k in rate_keys):
                wait = random.uniform(15, 20)
                print(f"  [领现金] 随机等待 {wait:.0f}s")
                time.sleep(wait)
                continue
            # 硬失败(需 media_verify / 已领 / 参数错) -> 停止
            print(f"  [领现金] 失败: {msg}")
            if "验证" in msg or "广告" in msg or "media" in msg.lower():
                print(f"  [领现金] 疑似需 media_verify, 纯脚本不可领该阶段, 停止本轮")
            break
        if gained:
            print(f"[领现金] 本轮共领 {gained:.2f} 元")
        self.stats["cash_gained"] = gained
        return gained

    def brush_until_stages_full(self, cap_minutes=DEFAULT_MINUTES):
        """刷视频时长, 直到「刷视频领现金」(readWithdraw) 的 12 个阶段全部达到
        「待领(status=1)或 已领(status=2)」(即无 status=0 未达成阶段) 即停止刷时长。
        不再用固定 minutes 当目标 —— 以服务端阶段进度为准, 没满 12 就继续刷。
        安全机制: 可达阶段数连续 3 轮不变(疑似服务端封顶) 或达 max_rounds 上限则转领取。
        关键: 必须用 readTime(type=2) 上报, scoreTime(type=1) 只给金币不推进领现金进度。
        """
        total = 12
        n = 0
        last_reachable = -1
        stable = 0
        # cap_minutes 仅作为安全上限(轮数), 默认内部上限 80 轮
        try:
            cap_rounds = max(10, int(cap_minutes) * 60 // max(READTIME_SECONDS, 1)) if cap_minutes else 80
        except Exception:
            cap_rounds = 80
        print(f"[刷视频] 目标: 刷到「刷视频领现金」12 阶段全部可领/已领才停; "
              f"每 {BRUSH_INTERVAL}s 上报 {READTIME_SECONDS}s (上限 {cap_rounds} 轮)")
        while n < cap_rounds:
            r = self.read_time_once()
            ok = r.get("success") or r.get("code") in (0, "0", 200) or "data" in r or "items" in r
            n += 1
            if n % 2 == 0 or not ok:
                info = self.query_cash_task()
                milestones = info.get("milestones") or []
                reachable = sum(1 for m in milestones if m["status"] in (1, 2))  # 待领+已领
                claim_n = len(info.get("claimable") or [])
                top = info.get("top_value", 0)
                print(f"  第{n}轮 | {_brief(r)} | 进度{reachable}/{total} 可领{claim_n}个 下阶段{top}s")
                if reachable >= total:
                    print(f"[刷视频] 12 阶段已全部可领/已领, 停止刷时长")
                    break
                if reachable == last_reachable:
                    stable += 1
                    if stable >= 3:
                        print(f"[刷视频] 进度已稳定于 {reachable} 阶段(疑似封顶), 转领取")
                        break
                else:
                    stable = 0
                    last_reachable = reachable
            else:
                print(f"  第{n}轮 {_brief(r)}")
            if not ok:
                print("  ⚠ 上报失败, 可能已过期")
            time.sleep(BRUSH_INTERVAL)
        print(f"[刷视频] 刷时长结束, 共上报 {n} 轮")

    # ---------- 开红包领现金 完整链路 ----------
    def open_red_envelope(self):
        """开红包领现金: POST /v18/task/openRedEnvelopeCash.json (md5 签名, 无业务参数, 自动开下一个待开红包)。"""
        return _http("/v18/task/openRedEnvelopeCash.json", LEMON, "openRedEnvelopeCash", self.p)

    def claim_red_envelope(self, index, media_extra):
        """看完广告后上报解锁第 index 个红包: POST /v18/task/claimRedEnvelope.json (md5, index+media_extra)。"""
        c = _http("/v18/task/claimRedEnvelope.json", LEMON, "claimRedEnvelope", self.p,
                  {"index": str(index), "media_extra": media_extra})
        print(f"  [红包广告] 第{index}个 → {_brief(c)}")
        return c

    def _parse_red(self, r):
        """解析 openRedEnvelopeCash 响应 -> {list:[{index,status,money,video}], money, total_money, next_time}"""
        if not isinstance(r, dict):
            return None
        items = r.get("items") or {}
        lst = items.get("list") or []
        out = []
        for m in lst:
            try:
                idx = int(m.get("index", 0))
            except (TypeError, ValueError):
                idx = 0
            try:
                st = int(m.get("status", 0))
            except (TypeError, ValueError):
                st = 0
            try:
                vid = int(m.get("video", 0))
            except (TypeError, ValueError):
                vid = 0
            out.append({"index": idx, "status": st, "money": _to_float(m.get("money")), "video": vid})
        return {"list": out, "money": _to_float(items.get("money")),
                "total_money": _to_float(items.get("total_money")),
                "next_time": _to_float(items.get("next_time"))}

    def _watch_one_ad_for_red(self):
        """为红包看一个广告(toGetReward 上报看完); media_verify 取 ZHILIAO 配置重放或 detect_ad 返回。"""
        try:
            ad = detect_ad()
        except Exception:
            ad = None
        me = build_claim_media_extra(ad)
        g = _http("/v5/CommonReward/toGetReward.json", LEMON, "toGetReward", self.p, {"media_extra": me})
        
        if isinstance(g, dict) and str(g.get("error_code", "0")) != "0":
            print(f"  [红包广告] 广告奖励上报成功")
        return g

    def run_red_envelope(self):
        """开红包领现金主流程(状态机, 动态适配红包数量):
        每个红包都必须调 claimRedEnvelope(index) 才会发放/解锁(抓包证实 video=0 的 index1 也走 claim, 非 openRedEnvelopeCash 自动开)。
        video=0 的无需看广告, 直接 claim; video>0 的需先看对应数量广告再 claim; 每次 claim 后 openRedEnvelopeCash 查询确认。
        全部开完后 maybe_withdraw 提现。
        依赖 media_verify: 优先环境变量 media_verify(抓包重放), 否则 detect_ad 返回(position_config_verify)。
        返回红包总收入(元)。"""
        print("\n========== 开红包领现金任务 ==========")
        
        r = self.open_red_envelope()
        guard = 0
        MAX_GUARD = 50
        total_money = 0.0
        while guard < MAX_GUARD:
            guard += 1
            info = self._parse_red(r)
            if info is None or not info["list"]:
                print("[红包] 响应异常或无红包列表, 停止")
                break
            opened = [x for x in info["list"] if x["status"] == 2]
            pending = [x for x in info["list"] if x["status"] == 1]
            total_money = info.get("total_money") or 0.0
            print(f"[红包] 进度: 已开 {len(opened)}/{len(info['list'])} 待开 {len(pending)} "
                  f"累计 {total_money}元 本次 {info.get('money')}元")
            if not pending:
                print("[红包] 全部红包已开完")
                break
            i = pending[0]          # 下一个待开(序号最小)
            idx, v = i["index"], i["video"]
            if v == 0:
                # 抓包证实: video=0 的红包(如 index1)也必须 claimRedEnvelope(index) 才发放,
                # 并非 openRedEnvelopeCash 自动开; 故无需看广告, 直接 claim 解锁。
                print(f"[红包] 第 {idx} 个无需看广告, 直接领取(claim 解锁)")
            else:
                # 需看 v 个广告 -> 上报奖励 -> 再 claim 解锁
                print(f"[红包] 第 {idx} 个需看 {v} 个广告, 开始观看...")
                for k in range(v):
                    self._watch_one_ad_for_red()
                    time.sleep(random.uniform(3, 8))
            # 关键: video=0 与 video>0 统一走 claimRedEnvelope(index) 解锁/发放
            try:
                ad = detect_ad()
            except Exception:
                ad = None
            me = build_claim_media_extra(ad)
            self.claim_red_envelope(idx, me)
            r = self.open_red_envelope()
            time.sleep(random.uniform(5, 12))
        # 红包任务结束: 按目标金额提现红包余额(redWithdraw, 非 mini/bonusWithdraw)
        self.red_withdraw(WITHDRAW_TARGET)
        print("[红包] 任务结束")
        self.stats["red_gained"] = total_money
        return total_money

    def get_feed_browse_task_list(self):
        r = _http("/v5/Nameless/getFeedBrowseTaskList.json", LEMON, "getFeedBrowseTaskList", self.p)
        items = (r.get("items") or {}).get("list") or []
        return items[0] if items else None

    def watch_ad(self, task, ad):
        task_id = task.get("banner_id") or task.get("id") or task.get("task_id")
        if not task_id:
            print("  [广告] 无任务号, 跳过")
            return
        print(f"  [广告] 任务{task_id} 开始观看")
        s = _http("/v5/nameless/adlickstart.json", LEMON, "adlickstart", self.p, {"task_id": str(task_id)})
        print(f"    广告开始 → {_brief(s)}")
        stop = int(os.environ.get("ZQKD_AD_WATCH", "100"))
        try:
            rule = (s.get("items") or {}).get("rule") or []
            if rule:
                stop = int(rule[0].get("stop_time", stop))
        except Exception:
            pass
        half = max(3, stop // 2)
        print(f"    观看 {stop}s (中途心跳) ...")
        time.sleep(half)
        try:
            _http("/v5/nameless/bannerstatus.json", LEMON, "bannerstatus", self.p,
                  {"task_id": str(task_id), "page_click": "3", "page_slide": "9", "page_stay": str(half)})
        except Exception:
            pass
        time.sleep(stop - half + 3)
        ad2 = detect_ad()
        if ad2:
            ad = ad2
        me = build_media_extra(ad)
        g = _http("/v5/CommonReward/toGetReward.json", LEMON, "toGetReward", self.p, {"media_extra": me})
        print(f"    领取奖励 → {_brief(g)}")
        # 抓包: toGetReward 后调用 rewardVideoCrv(激励视频转化上报, entry285/529/926)
        try:
            self.reward_video_crv_once()
        except Exception:
            pass
        e = _http("/v5/nameless/adlickend.json", LEMON, "adlickend", self.p,
                  {"task_id": str(task_id), "task_click": "0", "task_click_num": "0"})
        print(f"    广告完成 → {_brief(e)}")
        # 抓包: adlickend 后调用 csjCpa(穿山甲CPA上报, entry1056)
        try:
            self.csj_cpa_once()
        except Exception:
            pass

    def keepalive_after_withdraw(self, duration=None, interval=None):
        """提现后保活: 按抓包4.har完整模拟app启动流程, 等待微信到账。
        关键端点: getBonusPaymentList(查奖金提现列表, 触发到账)。"""
        dur = duration or int(os.environ.get("KEEPALIVE_DURATION", str(KEEPALIVE_DURATION)))
        ivl = interval or KEEPALIVE_INTERVAL
        if dur <= 0:
            return

        try:
            before_bal, _ = self.get_cash_balance()
        except Exception:
            before_bal = None

        print(f"\n[保活] 提现后模拟app完整启动流程 (最长 {dur}s)...")
        end = time.time() + dur
        round_n = 0
        arrived = False

        while time.time() < end:
            round_n += 1
            # === 阶段1: 启动初始化 (抓包 08:13:47) ===
            try: self.config_info_once()
            except Exception: pass
            try: self.getinfo_once()
            except Exception: pass
            try: self.config_audit_once()
            except Exception: pass
            try: self.media_config_once()
            except Exception: pass
            try: self.config_did_once()
            except Exception: pass
            try: self.count_start_once()
            except Exception: pass

            time.sleep(random.uniform(1, 3))

            # === 阶段2: 主流程加载 (抓包 08:13:53) ===
            try: self.get_bonus_payment_list()
            except Exception: pass
            try: self.get_task_list()
            except Exception: pass
            try: self.machine_once()
            except Exception: pass
            try: self.read_score_once()
            except Exception: pass
            try:
                self._http_get("/v3/user/userinfo.json", LEMON, "userinfo", self.p)
            except Exception: pass
            try: self.app_update_once()
            except Exception: pass
            try: self.read_withdraw_once()
            except Exception: pass
            try: self.bi_collect_once()
            except Exception: pass

            time.sleep(random.uniform(2, 4))

            # === 阶段3: 数据加载 (抓包 08:13:59) ===
            try: self.get_feed_browse_task_list()
            except Exception: pass
            try:
                self._http_get("/v15/user/userdata.json", LEMON, "userdata", self.p)
            except Exception: pass

            time.sleep(random.uniform(1, 2))

            # === 阶段4: ★ 关键! 查奖金提现列表 (抓包 08:14:02) ===
            try:
                r = self.get_bonus_payment_list()
                print(f"  [保活] 第{round_n}轮 查提现列表 → {_brief(r)}")
            except Exception as e:
                print(f"  [保活] 第{round_n}轮 查提现列表异常: {e}")

            # 查余额对比
            try:
                bal, _ = self.get_cash_balance()
                if bal is not None:
                    if before_bal is not None and bal < before_bal:
                        print(f"  [保活] ★ 余额 {before_bal}→{bal}元, 已到账!")
                        arrived = True
                        break
                    print(f"  [保活] 余额 {bal}元 (提现前 {before_bal}元)")
            except Exception:
                pass

            remaining = max(0, int(end - time.time()))
            if remaining <= 0:
                break
            time.sleep(min(ivl, remaining))

        if arrived:
            print("[保活] 已到账, 保活结束")
        else:
            print(f"[保活] 等待{dur}秒超时, 保活结束")

    def ad_loop(self, stop_event=None):
        lo, hi = 25, 60
        while True:
            if stop_event and stop_event():
                break
            ad = detect_ad()
            if ad:
                task = self.get_feed_browse_task_list()
                if task:
                    self.watch_ad(task, ad)
                else:
                    print("  [广告] 检测到广告但无浏览任务可领")
            else:
                print("  [广告] 当前无广告")
            time.sleep(random.uniform(lo, hi))


# ============================================================
# 六、入口
# ============================================================
def _split_accounts():
    """把 ZHILIAO_PARAM 按 & 分割成多个账号的 zqkd_param 整串。
    zqkd_param 串本身是 base64urlsafe 编码(字符集 [A-Za-z0-9-_], 不含 &), 故 & 可作安全分隔符。
    返回 list[str]; 空列表表示未配 ZHILIAO_PARAM(走 ZHILIAO/# 单账号模式)。"""
    raw = (os.environ.get("ZHILIAO_PARAM") or "").strip()
    if not raw:
        return []
    return [p.strip() for p in raw.split("&") if p.strip()]


def _split_uid_accounts():
    """从环境变量 ZHIKAN_ACCOUNT 或命令行解析 UID 列表。
    支持空格、逗号、换行分隔。
    返回 list[str]; 空列表表示未配 UID 登录模式。"""
    raw = (os.environ.get("ZHIKAN_ACCOUNT") or "").strip()
    if not raw:
        return []
    return [a.strip() for a in raw.replace(",", " ").replace("\n", " ").split() if a.strip()]


def _apply_uid(uid_str):
    """UID 直登模式: 只传 UID, 其余用内置默认值, session 由服务端自动下发。"""
    global UID, SESSION, UNION_ID, USER_CERT, ZQKEY, ZQKEY_ID, S_AD
    global OAID, OPENUDID, ANDROIDID, DEVICE_ID, SM_DEVICE_ID, APP_DEVICE_ID, SSP_USER_ID, AUTH
    UID = uid_str.strip()
    SESSION = ""
    UNION_ID = ""
    USER_CERT = "0"
    ZQKEY = ""
    ZQKEY_ID = ""
    S_AD = ""
    OAID = ""
    OPENUDID = ""
    ANDROIDID = ""
    DEVICE_ID = ""
    SM_DEVICE_ID = ""
    APP_DEVICE_ID = ""
    SSP_USER_ID = "64879461"
    DEVICE.clear()
    DEVICE.update(DEVICE_DEFAULT)
    AUTH = {
        "uid": UID, "account": UID,
        "union_id": UNION_ID, "user_cert": USER_CERT,
        "zqkey": ZQKEY, "zqkey_id": ZQKEY_ID, "s_ad": S_AD,
        "oaid": OAID, "openudid": OPENUDID, "androidid": ANDROIDID,
        "device_id": DEVICE_ID, "sm_device_id": SM_DEVICE_ID, "app_device_id": APP_DEVICE_ID,
    }
    print(f"[凭据] UID直登模式: uid={UID} (session将在首次请求后自动获取)")


def run_single_account(bot, args):
    """单账号完整流程: 取昵称 -> 刷到12阶段填满 -> 领取(+限速重试) -> 判定 -> 收尾提现。"""
    # 完整启动初始化(抓包4.har: 手动进app到账流程)
    try: bot.config_info_once()
    except Exception: pass
    try: bot.getinfo_once()
    except Exception: pass
    try: bot.config_audit_once()
    except Exception: pass
    try: bot.media_config_once()
    except Exception: pass
    try: bot.config_did_once()
    except Exception: pass
    try: bot.count_start_once()
    except Exception: pass
    try: bot.bi_tf_once()
    except Exception: pass
    try: bot.bi_collect_once()
    except Exception: pass

    # 先取微信昵称(提现 username 用)
    nickname = ""
    try:
        ui = bot.get_userinfo()
        bot.username = ui.get("nickname") or ""
        nickname = bot.username
        print(f"[信息] 微信昵称={bot.username} 小金库余额={ui.get('treasury')}元")
    except Exception as ex:
        print(f"[警告] 取昵称失败: {ex} (提现可能需手动补 username)")

    # machine(config 检查, 抓包 entry229: getTaskList 后立即调用)
    try:
        bot.machine_once()
    except Exception:
        pass

    # 主流程: 刷到 12 阶段填满 -> 领取(带限速重试) -> 未满继续刷, 封顶则收尾提现
    last_claimed = -1
    last_reachable = -1
    stuck = 0
    for cycle in range(12):
        # 抓包: getTaskList 后立即调用 machine(config) + exchange(金币兑换)
        try:
            bot.get_task_list()
        except Exception:
            pass
        try:
            bot.machine_once()
        except Exception:
            pass
        # 抓包: machine 后调用 adConversion(广告转化上报, entry230/512/824/1064/1265/1397)
        try:
            bot.ad_conversion_once()
        except Exception:
            pass
        try:
            bot.exchange_once()
        except Exception:
            pass
        # 抓包: exchange 后紧跟 BiCollect(事件上报, entry521/525/533/534)
        try:
            bot.bi_collect_once()
        except Exception:
            pass

        # 阶段1: 刷视频时长, 直到 12 阶段全部可领/已领 或 安全封顶
        bot.brush_until_stages_full(args.minutes)

        # 阶段2: 领取全部可领阶段(限速时随机等 15-20s 重试)
        print(f"\n[阶段2] 第{cycle+1}轮 领取阶段奖励...")
        bot.claim_all_cash_stages()

        # 阶段3: 判定是否填满
        info = bot.query_cash_task()
        claimed = sum(1 for m in info["milestones"] if m["status"] == 2)
        reachable = sum(1 for m in info["milestones"] if m["status"] in (1, 2))
        print(f"[进度] 第{cycle+1}轮: 已领={claimed}/12 当前可领={len(info['claimable'])} 可达={reachable}/12")
        if info.get("all_done") or claimed >= 12:
            print("[进度] 12 阶段全部领取完成")
            break
        # 连续两轮无新增 -> 服务端可能封顶/需真广告, 停止循环
        if claimed == last_claimed and reachable == last_reachable:
            stuck += 1
            if stuck >= 2:
                print("[进度] 连续无新增, 停止")
                break
        else:
            stuck = 0
        last_claimed, last_reachable = claimed, reachable

    # 收尾: 任务结束且余额>0.1 提现; 否则按平时规则(>=0.8 提)
    info = bot.query_cash_task()
    claimed_final = sum(1 for m in info["milestones"] if m["status"] == 2)
    all_done = info.get("all_done") or claimed_final >= 12
    print(f"\n[阶段3] 任务结束判定: all_done={all_done} 已领={claimed_final}/12")
    bot.maybe_withdraw(task_ended=all_done)

    # 开红包领现金任务(默认执行; 依赖 media_verify 重放; --no-red 可跳过)
    if not getattr(args, "no_red", False):
        try:
            bot.run_red_envelope()
        except Exception as _e:
            print(f"[红包] 任务异常: {_e}")

    # 提现后保活: 仅在实际提现成功时触发, 模拟app在线等待微信支付回调
    if bot.stats["withdraw_ok"]:
        bot.keepalive_after_withdraw()
    else:
        print("[info] 未发生提现, 跳过保活")

    print("[done] 账号任务结束")

    # 查询最终余额并发送通知
    try:
        bal, _ = bot.get_cash_balance()
        bal_str = f"{bal}元" if bal is not None else "未知"
    except Exception:
        bal_str = "未知"

    total_income = bot.stats["cash_gained"] + bot.stats["red_gained"]
    withdraw_info = f"提现: {bot.stats['withdraw_amount']}元" if bot.stats["withdraw_ok"] else "未提现"
    bonus_info = f"小金库提现: {bot.stats['bonus_withdraw']}元" if bot.stats["bonus_withdraw_ok"] else ""
    red_info = f"红包提现: {bot.stats['red_withdraw']}元" if bot.stats["red_withdraw_ok"] else ""
    withdraw_detail = " | ".join(filter(None, [withdraw_info, bonus_info, red_info]))

    notify_msg = (
        f"【知了快看任务完成】\n"
        f"账号: {nickname} (uid={UID})\n"
        f"刷视频领现金: {bot.stats['cash_gained']:.2f}元\n"
        f"红包收入: {bot.stats['red_gained']:.2f}元\n"
        f"今日总收入: {total_income:.2f}元\n"
        f"{withdraw_detail}\n"
        f"小金库余额: {bal_str}"
    )
    send_qywx_msg(notify_msg)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--minutes", type=int, default=int(MINUTES_ENV))
    ap.add_argument("--ad", action="store_true", help="同时跑广告翻倍(需 ZHILIAO 里写 media_extra=frida捕获值)")
    ap.add_argument("--only-brush", action="store_true")
    ap.add_argument("--no-red", action="store_true", help="跳过开红包领现金任务(默认会跑, 需配 media_verify 重放)")
    ap.add_argument("--account", "-a", nargs="+", default=None, help="UID直登: 只传账号UID即可运行, 无需抓包")
    args = ap.parse_args()

    provider = StaticProvider()

    # ===== 优先级1: --account 命令行参数 (UID直登) =====
    uid_accounts = args.account or []
    if not uid_accounts:
        env_uid = (os.environ.get("ZHIKAN_ACCOUNT") or "").strip()
        if env_uid:
            uid_accounts = [a.strip() for a in env_uid.replace(",", " ").replace("\n", " ").split() if a.strip()]

    if uid_accounts:
        # ===== UID 直登模式: 只需UID, 无需抓包zqkd_param =====
        total = len(uid_accounts)
        print(f"[启动] UID直登模式 | {total} 个账号 | 每账号 {args.minutes} 分钟")
        print(f"账号列表: {', '.join(uid_accounts)}")
        for idx, uid in enumerate(uid_accounts):
            try:
                _apply_uid(uid)
            except Exception as _e:
                print(f"[错误] 第{idx+1}个账号UID设置失败: {_e}, 跳过")
                continue
            bot = Bot(provider)
            print(f"\n========== 账号 {idx+1}/{total}  uid={UID} (UID直登) ==========")
            run_single_account(bot, args)
            if idx < total - 1:
                wait = random.uniform(30, 60)
                print(f"\n[间隔] 下一账号前随机等待 {wait:.0f}s ...")
                time.sleep(wait)
    else:
        accounts = _split_accounts()
        if accounts:
            # ===== 优先级2: ZHILIAO_PARAM 多账号模式 =====
            total = len(accounts)
            print(f"[启动] 检测到 {total} 个账号，逐个运行, 账号间随机等待 30-60s")
            for idx, raw in enumerate(accounts):
                try:
                    apply_param(raw)
                except Exception as _e:
                    print(f"[错误] 第{idx+1}个账号 zqkd_param 解密失败: {_e}, 跳过该账号")
                    continue
                bot = Bot(provider)
                print(f"\n========== 账号 {idx+1}/{total}  uid={UID} ==========")
                run_single_account(bot, args)
                if idx < total - 1:
                    wait = random.uniform(30, 60)
                    print(f"\n[间隔] 下一账号前随机等待 {wait:.0f}s (30-60s) ...")
                    time.sleep(wait)
        else:
            # ===== 优先级3: 单账号模式 =====
            if not UID:
                print("[错误] 未解析到 uid。三种方式任选其一:")
                print("        方式1(最简): ZHIKAN_ACCOUNT=\"你的UID\" 或 --account 你的UID")
                print("        方式2(推荐): ZHILIAO_PARAM=\"抓包的 zqkd_param 整串\"")
                print("        方式3: ZHILIAO=\"uid=54475743#session=你的PHPSESSID\"")
                send_qywx_msg("【知了快看执行失败】\n未配置 uid，请检查环境变量")
                sys.exit(1)
            print(f"[启动] uid={UID} 模式=刷视频领现金(纯脚本) + 金币 + 自动提现")
            bot = Bot(provider)
            run_single_account(bot, args)

    print("\n[done] 全部账号任务结束")

    # 发送企业微信通知
    total = len(uid_accounts) if uid_accounts else (len(accounts) if accounts else 1)
    notify_msg = f"【知了快看全部完成】\n共 {total} 个账号任务执行完毕"
    send_qywx_msg(notify_msg)


if __name__ == "__main__":
    main()
