import os
import re
import json
import base64
import requests
import hashlib
import time
import random
import string
import urllib.parse
from datetime import datetime
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
import binascii

try:
    import notify
    NOTIFY_AVAILABLE = True
except ImportError:
    NOTIFY_AVAILABLE = False

PHONE_V = "13119345616"
phone_vs = os.environ.get('PHONE_V', PHONE_V)
if not phone_vs:
    print("请设置 PHONE_V 环境变量，格式：手机号1@手机号2 或 手机号1&手机号2")
    exit(1)

WOREAD_UA = "Mozilla/5.0 (Linux; Android 11; Redmi Note 10 Pro Build/RP1A.201005.004; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/92.0.4515.159 Mobile Safari/537.36"
WOREAD_KEY = "woreadst^&*12345"

AITING_BASE_URL = "https://pcc.woread.com.cn"
AITING_SIGN_KEY_APPKEY = "7ZxQ9rT3wE5sB2dF"
AITING_SIGN_KEY_API = "woread!@#qwe1234"
AITING_SIGN_KEY_REQUERTID = "46iCw24ewAZbNkK6"
AITING_CLIENT_KEY = "1"
AITING_AES_KEY = "j2K81755sxV12wFx"
AITING_AES_IV = "16-Bytes--String"
ADDREADTIME_AES_KEY = "UNS#READDAY39COM"

def log_time():
    now = datetime.now()
    return now.strftime("%H:%M:%S.%f")[:-3]


def log(msg, level="INFO"):
    timestamp = log_time()

    prefix_map = {
        "INFO": "ℹ",
        "SUCCESS": "✓",
        "ERROR": "✗",
        "WARNING": "⚠"
    }
    prefix = prefix_map.get(level, "•")

    print(f"[{timestamp}] {prefix} {msg}")

def generate_random_imei():
    tac = ''.join(random.choice(string.digits) for _ in range(8))
    snr = ''.join(random.choice(string.digits) for _ in range(6))
    imei_without_check = tac + snr

    def calculate_luhn(number):
        digits = [int(d) for d in number]
        for i in range(len(digits) - 1, -1, -2):
            digits[i] *= 2
            if digits[i] > 9:
                digits[i] -= 9
        total = sum(digits)
        check_digit = (10 - (total % 10)) % 10
        return str(check_digit)

    check_digit = calculate_luhn(imei_without_check)
    imei = imei_without_check + check_digit

    return imei

def get_aes_phone(data, key):
    iv_str = "gnirtS--setyB-61"[::-1]
    iv = iv_str.encode('utf-8')[:16]
    key_bytes = key.encode('utf-8')[:16]

    cipher = AES.new(key_bytes, AES.MODE_CBC, iv)
    padded_data = pad(data.encode('utf-8'), AES.block_size)
    encrypted = cipher.encrypt(padded_data)
    hex_str = binascii.hexlify(encrypted).decode('utf-8')
    return base64.b64encode(hex_str.encode('utf-8')).decode('utf-8')


def get_aes(data, key=""):
    iv_str = "gnirtS--setyB-61"[::-1]
    iv = iv_str.encode('utf-8')[:16]
    key_bytes = key.encode('utf-8')[:16]

    json_string = json.dumps(data, separators=(',', ':'))

    cipher = AES.new(key_bytes, AES.MODE_CBC, iv)
    padded_data = pad(json_string.encode('utf-8'), AES.block_size)
    encrypted = cipher.encrypt(padded_data)
    hex_str = binascii.hexlify(encrypted).decode('utf-8')
    return base64.b64encode(hex_str.encode('utf-8')).decode('utf-8')


def aes_encrypt(data, key, iv):
    key_bytes = key.encode('utf-8')
    iv_bytes = iv.encode('utf-8')

    cipher = AES.new(key_bytes, AES.MODE_CBC, iv_bytes)
    padded_data = pad(data.encode('utf-8'), AES.block_size)
    encrypted = cipher.encrypt(padded_data)
    hex_str = binascii.hexlify(encrypted).decode('utf-8').upper()
    return base64.b64encode(hex_str.encode('utf-8')).decode('utf-8')


def woread_login(phone):
    e = {
        "data": {"phone": get_aes_phone(phone, WOREAD_KEY)}
    }

    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")[:14]
    data_to_encrypt = {**e["data"], "timestamp": timestamp}
    result = get_aes(data_to_encrypt, WOREAD_KEY)
    data = json.dumps({"sign": result})

    headers = {
        "User-Agent": WOREAD_UA,
        "Accept": "application/json, text/plain, */*",
        "accesstoken": "ODZERTZCMjA1NTg1MTFFNDNFMThDRDYw",
        "Content-Type": "application/json;charset=UTF-8",
        "Origin": "https://10010.woread.com.cn",
        "Referer": "https://10010.woread.com.cn/ng_woread/",
    }

    try:
        response = requests.post(
            "https://10010.woread.com.cn/ng_woread_service/rest/account/login",
            headers=headers,
            data=data,
            timeout=10
        )
        response.raise_for_status()

        if not response.text.strip():
            log("联通阅读登录失败: 空响应", "ERROR")
            return None

        body_data = response.json()

        if "data" not in body_data:
            log("联通阅读登录失败", "ERROR")
            return None

        data = body_data["data"]
        required_fields = ["token", "userid", "userindex", "phone", "verifycode"]
        for field in required_fields:
            if field not in data:
                log(f"联通阅读登录失败: 缺少字段 {field}", "ERROR")
                return None

        log("联通阅读登录成功", "SUCCESS")
        return {
            "userid": data["userid"],
            "useraccount": data["phone"],
            "token": data["token"],
            "userindex": data["userindex"],
            "verifycode": data["verifycode"]
        }

    except Exception as e:
        log(f"联通阅读登录失败: {e}", "ERROR")
        return None

def woread_sign_in(userid, token, jwt_token, statisticsinfo):
    url = "https://woread.com.cn/rest/read/usersign/getSignin/3/0"

    timestamp = str(int(time.time() * 1000))
    nonestr = ''.join(random.choices(string.digits, k=6))

    requertid_params = {
        'jwt': jwt_token,
        'nonestr': nonestr,
        'osversion': 'Android12',
        'terminalName': 'Redmi',
        'timestamp': timestamp
    }
    sorted_params = sorted(requertid_params.items())
    sign_str = '&'.join([f"{k}={v}" for k, v in sorted_params])
    sign_str += f"&key={AITING_SIGN_KEY_REQUERTID}"
    requertid = hashlib.md5(sign_str.encode('utf-8')).hexdigest()

    headers = {
        'Content-Type': 'application/json',
        'statisticsinfo': statisticsinfo,
        'requerttime': timestamp,
        'nonestr': nonestr,
        'requertid': requertid,
        'AuthorizationClient': f'Bearer {jwt_token}',
        'User-Agent': 'okhttp/4.9.0'
    }

    params = {
        'userid': userid,
        'token': token
    }

    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)
        result = response.json()
        if result.get('code') == '0000':
            log(f"签到成功: 连续{result.get('continuousDays', 0)}天", "SUCCESS")
        else:
            log(f"签到: {result.get('message', '未知')}")
        return result
    except Exception as e:
        log(f"签到失败: {e}", "ERROR")
        return None


def woread_get_secretkey(userid, token, jwt_token, statisticsinfo):
    timestamp = str(int(time.time() * 1000))
    nonestr = ''.join(random.choices(string.digits, k=6))

    requertid_params = {
        'jwt': jwt_token,
        'nonestr': nonestr,
        'osversion': 'Android12',
        'terminalName': 'Redmi',
        'timestamp': timestamp
    }
    sorted_params = sorted(requertid_params.items())
    sign_str = '&'.join([f"{k}={v}" for k, v in sorted_params])
    sign_str += f"&key={AITING_SIGN_KEY_REQUERTID}"
    requertid = hashlib.md5(sign_str.encode('utf-8')).hexdigest()

    url = f"https://woread.com.cn/rest/read/statistics/getsecretkey/3/{userid}"

    headers = {
        'statisticsinfo': statisticsinfo,
        'requerttime': timestamp,
        'nonestr': nonestr,
        'requertid': requertid,
        'AuthorizationClient': f'Bearer {jwt_token}',
        'Content-Type': 'application/json',
        'User-Agent': 'okhttp/4.9.0'
    }

    params = {
        'token': token
    }

    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)
        result = response.json()
        if result.get('code') == '0000':
            return result.get('message')
        else:
            return None
    except Exception:
        return None


def woread_add_read_time(userid, token, jwt_token, statisticsinfo, readtime=120, secretkey=None):
    stats_dict = {}
    for item in statisticsinfo.split('&'):
        if '=' in item:
            key, value = item.split('=', 1)
            stats_dict[key] = value

    imei = stats_dict.get('eid', '4aL_QwmGakUJQoMlOLni')
    imsi = stats_dict.get('sid', 'cw9_t9ptZYA6YNmdlZ@y')
    channelid = stats_dict.get('channelid', '28015001')
    clientallid = stats_dict.get('clientallid', '000000100000000000058.0.3.1225')
    nettypename = stats_dict.get('nettypename', 'wifi')
    osversion = stats_dict.get('osversion', 'Android12')

    timestamp = str(int(time.time() * 1000))
    nonestr = ''.join(random.choices(string.digits, k=6))

    requertid_params = {
        'jwt': jwt_token,
        'nonestr': nonestr,
        'osversion': osversion,
        'terminalName': 'Redmi',
        'timestamp': timestamp
    }
    sorted_params = sorted(requertid_params.items())
    sign_str = '&'.join([f"{k}={v}" for k, v in sorted_params])
    sign_str += f"&key={AITING_SIGN_KEY_REQUERTID}"
    requertid = hashlib.md5(sign_str.encode('utf-8')).hexdigest()

    if not secretkey:
        secretkey = woread_get_secretkey(userid, token, jwt_token, statisticsinfo)
        if not secretkey:
            return None

    url_data = {
        "userid": userid,
        "counttime": str(readtime * 1000),
        "timestamp": timestamp,
        "secretkey": secretkey,
        "cntindex": "4524960",
        "cnttype": 1,
        "readtype": 1
    }

    url_data_str = json.dumps(url_data, separators=(',', ':'))
    encrypted = aes_encrypt(url_data_str, ADDREADTIME_AES_KEY, AITING_AES_IV)

    now = datetime.now()
    creadertime = now.strftime("%y%m%d%H%M%S")

    import uuid
    random_uuid = str(uuid.uuid4()).replace('-', '')

    body = {
        "activityid": "",
        "cardid": "",
        "catindex": "",
        "channelid": channelid,
        "clientallid": clientallid,
        "creadertime": creadertime,
        "endseno": "",
        "imei": imei,
        "imsi": imsi,
        "isfreeLimt": "0",
        "list": {
            "chapterid": "7",
            "cntindex": "4524960",
            "cnttype": 1,
            "readtime": str(readtime * 1000),
            "readtype": 1
        },
        "list1": [{
            "chapterid": "7",
            "cntindex": "4524960",
            "cnttype": 1,
            "readtime": str(readtime * 1000),
            "readtype": 1
        }],
        "listentimes": str(readtime * 1000),
        "listentype": "",
        "nettypename": nettypename,
        "osversion": osversion,
        "pageindex": "",
        "startseno": "",
        "stattype": "1",
        "uuid": random_uuid
    }

    url = f"https://woread.com.cn/rest/read/statistics/addreadtime/3/{encrypted}"

    headers = {
        'statisticsinfo': statisticsinfo,
        'requerttime': timestamp,
        'nonestr': nonestr,
        'requertid': requertid,
        'AuthorizationClient': f'Bearer {jwt_token}',
        'Content-Type': 'application/json',
        'User-Agent': 'okhttp/4.9.0'
    }

    try:
        response = requests.post(url, json=body, headers=headers, timeout=10)
        result = response.json()
        if result:
            result['secretkey'] = secretkey
        return result
    except Exception:
        return None


def aiting_complete_task(userid, token, jwt_token, statisticsinfo, task_type):
    url = f"{AITING_BASE_URL}/activity/rest/unicom/points/completiontask"

    timestamp = str(int(time.time() * 1000))
    nonestr = ''.join(random.choices(string.digits, k=6))

    requertid_params = {
        'jwt': jwt_token,
        'nonestr': nonestr,
        'osversion': 'Android12',
        'terminalName': 'Redmi',
        'timestamp': timestamp
    }
    sorted_params = sorted(requertid_params.items())
    sign_str = '&'.join([f"{k}={v}" for k, v in sorted_params])
    sign_str += f"&key={AITING_SIGN_KEY_REQUERTID}"
    requertid = hashlib.md5(sign_str.encode('utf-8')).hexdigest()

    sign_params_for_calc = {
        'source': '3',
        'timestamp': timestamp,
        'token': token,
        'type': str(task_type),
        'userid': userid
    }

    sorted_sign_params = sorted(sign_params_for_calc.items())
    sign_str = '&'.join([f"{k}={v}" for k, v in sorted_sign_params])
    sign_str += f"&key={AITING_SIGN_KEY_API}"
    sign = hashlib.md5(sign_str.encode('utf-8')).hexdigest()

    body = {
        'source': 3,
        'timestamp': timestamp,
        'token': token,
        'type': str(task_type),
        'userid': userid,
        'sign': sign
    }

    headers = {
        'statisticsinfo': statisticsinfo,
        'requerttime': timestamp,
        'nonestr': nonestr,
        'requertid': requertid,
        'AuthorizationClient': f'Bearer {jwt_token}',
        'Content-Type': 'application/json; charset=utf-8',
        'User-Agent': 'okhttp/4.9.0'
    }

    try:
        response = requests.post(url, json=body, headers=headers, timeout=10)
        result = response.json()
        return result
    except Exception:
        return None

def jf_get_task_detail(ticket):
    url = "https://m.jf.10010.com/jf-external-application/jftask/taskDetail"

    headers = {
        'ticket': ticket,
        'pageid': 's789081246969976832',
        'user-agent': 'Mozilla/5.0 (Linux; Android 12; Redmi K30 Pro Build/SKQ1.220303.001; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/140.0.7339.51 Mobile Safari/537.36 WoReaderApp/Android',
        'accept': 'application/json, text/plain, */*',
        'clienttype': 'aiting_android',
        'content-type': 'application/json;charset=UTF-8',
        'partnersid': '1706'
    }

    try:
        response = requests.post(url, json={}, headers=headers, timeout=10)
        result = response.json()
        return result
    except Exception:
        return None


def jf_get_user_info(ticket):
    url = "https://m.jf.10010.com/jf-external-application/jftask/userInfo"

    headers = {
        'ticket': ticket,
        'pageid': 's789081246969976832',
        'user-agent': 'Mozilla/5.0 (Linux; Android 12; Redmi K30 Pro Build/SKQ1.220303.001; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/140.0.7339.51 Mobile Safari/537.36 WoReaderApp/Android',
        'accept': 'application/json, text/plain, */*',
        'clienttype': 'aiting_android',
        'content-type': 'application/json;charset=UTF-8',
        'partnersid': '1706'
    }

    try:
        response = requests.post(url, json={}, headers=headers, timeout=10)
        result = response.json()
        return result
    except Exception:
        return None


def jf_to_finish(ticket, task_code):
    url = "https://m.jf.10010.com/jf-external-application/jftask/toFinish"

    headers = {
        'ticket': ticket,
        'pageid': 's789081246969976832',
        'user-agent': 'Mozilla/5.0 (Linux; Android 12; Redmi K30 Pro Build/SKQ1.220303.001; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/140.0.7339.51 Mobile Safari/537.36 WoReaderApp/Android',
        'accept': 'application/json, text/plain, */*',
        'clienttype': 'aiting_android',
        'content-type': 'application/json;charset=UTF-8',
        'partnersid': '1706'
    }

    body = {'taskCode': task_code}

    try:
        response = requests.post(url, json=body, headers=headers, timeout=10)
        result = response.json()
        return result
    except Exception:
        return None


def jf_completion_task(ticket, task_code):
    url = "https://m.jf.10010.com/jf-external-application/jftask/completionTask"

    headers = {
        'ticket': ticket,
        'pageid': 's789081246969976832',
        'user-agent': 'Mozilla/5.0 (Linux; Android 12; Redmi K30 Pro Build/SKQ1.220303.001; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/140.0.7339.51 Mobile Safari/537.36 WoReaderApp/Android',
        'accept': 'application/json, text/plain, */*',
        'clienttype': 'aiting_android',
        'content-type': 'application/json;charset=UTF-8',
        'partnersid': '1706'
    }

    body = {'taskCode': task_code}

    try:
        response = requests.post(url, json=body, headers=headers, timeout=10)

        if response.status_code == 200:
            if not response.text or response.text.strip() == '':
                return {'code': '0000', 'msg': '成功'}

            try:
                result = response.json()
                return result
            except:
                return {'code': '0000', 'msg': response.text}
        else:
            return {'code': str(response.status_code), 'msg': '请求失败'}
    except Exception:
        return None


def jf_pop_up(ticket):
    url = "https://m.jf.10010.com/jf-external-application/jftask/popUp"

    headers = {
        'ticket': ticket,
        'pageid': 's789081246969976832',
        'user-agent': 'Mozilla/5.0 (Linux; Android 12; Redmi K30 Pro Build/SKQ1.220303.001; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/140.0.7339.51 Mobile Safari/537.36 WoReaderApp/Android',
        'accept': 'application/json, text/plain, */*',
        'clienttype': 'aiting_android',
        'content-type': 'application/json;charset=UTF-8',
        'partnersid': '1706'
    }

    data = {}

    try:
        response = requests.post(url, headers=headers, json=data, timeout=10)
        return response.json()
    except Exception:
        return None


def woread_new_read_add(userid, token, jwt_token, statisticsinfo, cntindex="5716575"):
    url = f"https://woread.com.cn/rest/read/new/newreadadd/3/{userid}/{token}"

    timestamp = str(int(time.time() * 1000))
    nonestr = ''.join(random.choices(string.digits, k=6))

    requertid_params = {
        'jwt': jwt_token,
        'nonestr': nonestr,
        'osversion': 'Android12',
        'terminalName': 'Redmi',
        'timestamp': timestamp
    }
    sorted_params = sorted(requertid_params.items())
    sign_str = '&'.join([f"{k}={v}" for k, v in sorted_params])
    sign_str += f"&key={AITING_SIGN_KEY_REQUERTID}"
    requertid = hashlib.md5(sign_str.encode('utf-8')).hexdigest()

    headers = {
        'Content-Type': 'application/json',
        'statisticsinfo': statisticsinfo,
        'requerttime': timestamp,
        'nonestr': nonestr,
        'requertid': requertid,
        'AuthorizationClient': f'Bearer {jwt_token}',
        'User-Agent': 'Redmi K30 Pro'
    }

    params = {
        'isfreeLimt': '0',
        'isgray': 'true'
    }

    body = {
        "source": 3,
        "cntindex": cntindex,
        "chapterallindex": "100136247350",
        "chapterflag": "1",
        "productpkgindex": "0",
        "offset": 0,
        "beginchapter": "11",
        "maxchapterseno": "1841",
        "paragraphindex": 0,
        "wordindex": 0,
        "charindex": 513,
        "readtype": 3
    }

    try:
        response = requests.post(url, params=params, json=body, headers=headers, timeout=10)
        result = response.json()
        return result
    except Exception:
        return None

def calculate_passcode(timestamp, phone, clientkey):
    raw_str = timestamp + phone + clientkey
    return hashlib.md5(raw_str.encode('utf-8')).hexdigest()


def calculate_clientconfirm(userid, imei):
    plaintext = "android" + userid + imei
    iv = AITING_AES_IV.encode('utf-8')
    key = AITING_AES_KEY.encode('utf-8')

    cipher = AES.new(key, AES.MODE_CBC, iv)
    ciphertext = cipher.encrypt(pad(plaintext.encode('utf-8'), AES.block_size))
    hex_str = ciphertext.hex().upper()
    return base64.b64encode(hex_str.encode('utf-8')).decode('utf-8')


def generate_sid():
    chars = string.ascii_letters + string.digits + '_@'
    return ''.join(random.choice(chars) for _ in range(20))


def generate_eid():
    chars = string.ascii_letters + string.digits + '_'
    return ''.join(random.choice(chars) for _ in range(20))


def generate_woid(imei):
    random_6 = ''.join(random.choice(string.digits) for _ in range(6))
    imei_8 = imei[:8] if len(imei) >= 8 else imei.ljust(8, '0')
    random_4 = ''.join(random.choice(string.digits) for _ in range(4))
    random_2 = ''.join(random.choice(string.digits) for _ in range(2))
    return f"WOA{random_6}{imei_8}LOT{random_4}LV{random_2}"


def generate_timestamp():
    return str(int(time.time() * 1000))


def generate_nonce():
    return str(random.randint(100000, 999999))


def md5_sign(text):
    return hashlib.md5(text.encode('utf-8')).hexdigest()


def generate_sign(params, key):
    sorted_params = sorted(params.items())
    sign_str = '&'.join([f"{k}={v}" for k, v in sorted_params])
    sign_str += f"&key={key}"
    return md5_sign(sign_str)


def build_statisticsinfo(userid, useraccount, imei, clientconfirm):
    versionname = '8.0.2'
    params = {
        'channelid': '28015001',
        'sid': generate_sid(),
        'eid': generate_eid(),
        'osversion': 'Android12',
        'clientallid': f"00000010000000000005{versionname}.1225",
        'display': '2400_1080',
        'ip': '192.168.3.24',
        'nettypename': 'wifi',
        'version': '802',
        'versionname': versionname,
        'terminalName': 'Redmi',
        'terminalType': 'Redmi_K30_Pro',
        'udid': 'null',
        'woid': generate_woid(imei),
        'useraccount': useraccount,
        'userid': userid,
        'clientconfirm': clientconfirm
    }
    return '&'.join([f"{k}={v}" for k, v in params.items()])


def get_jwt_token(statisticsinfo):
    url = f"{AITING_BASE_URL}/oauth/client/appkey"

    sign_params = {
        'clientSource': '3',
        'clientId': 'android',
        'source': '3',
        'timestamp': generate_timestamp()
    }

    sign = generate_sign(sign_params, AITING_SIGN_KEY_APPKEY)

    client_id_b64 = base64.b64encode(
        "395DEDE9C1D6FE11B7C9C0D82B353E74".encode('utf-8')
    ).decode('utf-8')

    params = {
        'clientSource': '3',
        'clientId': client_id_b64,
        'source': '3',
        'timestamp': sign_params['timestamp'],
        'sign': sign
    }

    headers = {'Skip-Authorization-Check': 'true'}
    if statisticsinfo:
        headers['statisticsinfo'] = statisticsinfo

    response = requests.post(url, json=params, headers=headers, timeout=10)

    if response.status_code == 200:
        result = response.json()
        if result.get('code') == '0000' and 'key' in result:
            return result['key']
    return None


def aiting_user_login(phone, useraccount, jwt_token, statisticsinfo):
    timestamp = time.strftime("%Y%m%d%H%M%S")

    passcode = calculate_passcode(timestamp, phone, AITING_CLIENT_KEY)

    url = f"{AITING_BASE_URL}/mainrest/rest/read/user/ulogin//3/{useraccount}/1/1/0"
    params_list = [
        'networktype=3',
        'ua=Redmi+K30+Pro',
        'isencode=true',
        'clientversion=8.0.2',
        'versionname=Android_1_1080x2356',
        'channelid=28015001',
        'userlabelisencode=1',
        'validatecode=',
        'sid=',
        f'timestamp={timestamp}',
        f'passcode={passcode}'
    ]
    full_url = f"{url}?{'&'.join(params_list)}"

    headers = {'Content-Type': 'application/json'}
    if statisticsinfo:
        headers['statisticsinfo'] = statisticsinfo

    requerttime = generate_timestamp()
    nonestr = generate_nonce()
    sign_params = {
        'jwt': jwt_token,
        'nonestr': nonestr,
        'osversion': 'Android12',
        'terminalName': 'Redmi',
        'timestamp': requerttime
    }
    sorted_params = sorted(sign_params.items())
    sign_str = '&'.join([f"{k}={v}" for k, v in sorted_params])
    sign_str += f"&key={AITING_SIGN_KEY_REQUERTID}"
    requertid = md5_sign(sign_str)

    headers.update({
        'requerttime': requerttime,
        'nonestr': nonestr,
        'requertid': requertid,
        'AuthorizationClient': f'Bearer {jwt_token}',
        'User-Agent': 'okhttp/4.9.0'
    })

    try:
        response = requests.get(full_url, headers=headers, timeout=10)

        if response.status_code == 200:
            result = response.json()

            if result.get('code') == '0000' and 'message' in result:
                message = result['message']
                if isinstance(message, dict):
                    user_token = None
                    userid = None

                    if 'token' in message:
                        user_token = message['token']
                    elif 'accountinfo' in message and 'token' in message['accountinfo']:
                        user_token = message['accountinfo']['token']

                    if 'accountinfo' in message:
                        userid = message['accountinfo'].get('userid')
                    elif 'userid' in message:
                        userid = message['userid']

                    if user_token and userid:
                        log("联通爱听登录成功", "SUCCESS")
                        return {"token": user_token, "userid": userid}

        log("联通爱听登录失败", "ERROR")
        return None

    except Exception as e:
        log(f"联通爱听登录失败: {e}", "ERROR")
        return None


def get_read_profile(user_token, userid, jwt_token, statisticsinfo):
    url = f"{AITING_BASE_URL}/pcc/rest/sns/profile/readprofile/7"

    params = {
        'userid': userid,
        'token': user_token,
        'encryptflag': '1'
    }

    requerttime = generate_timestamp()
    nonestr = generate_nonce()

    requertid_params = {
        'jwt': jwt_token,
        'nonestr': nonestr,
        'osversion': 'Android12',
        'terminalName': 'Redmi',
        'timestamp': requerttime
    }
    sorted_params = sorted(requertid_params.items())
    sign_str = '&'.join([f"{k}={v}" for k, v in sorted_params])
    sign_str += f"&key={AITING_SIGN_KEY_REQUERTID}"
    requertid = md5_sign(sign_str)

    headers = {
        'User-Agent': 'okhttp/4.9.0',
        'Connection': 'Keep-Alive',
        'Accept-Encoding': 'gzip',
        'Content-Type': 'application/json',
        'requerttime': requerttime,
        'nonestr': nonestr,
        'requertid': requertid,
        'AuthorizationClient': f'Bearer {jwt_token}'
    }

    if statisticsinfo:
        headers['statisticsinfo'] = statisticsinfo

    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)

        if response.status_code == 200:
            result = response.json()
            return result

        return None

    except Exception:
        return None


def get_info_ticket(user_token, userid, jwt_token, statisticsinfo):
    url = f"{AITING_BASE_URL}/activity/rest/unicom/points/getInfoTicket"

    timestamp = generate_timestamp()

    sign_params = {
        'timestamp': timestamp,
        'token': user_token,
        'userid': userid
    }

    sign = generate_sign(sign_params, AITING_SIGN_KEY_API)

    body = {
        'sign': sign,
        'timestamp': timestamp,
        'token': user_token,
        'userid': userid
    }

    requerttime = timestamp
    nonestr = generate_nonce()

    requertid_params = {
        'jwt': jwt_token,
        'nonestr': nonestr,
        'osversion': 'Android12',
        'terminalName': 'Redmi',
        'timestamp': requerttime
    }
    sorted_params = sorted(requertid_params.items())
    sign_str = '&'.join([f"{k}={v}" for k, v in sorted_params])
    sign_str += f"&key={AITING_SIGN_KEY_REQUERTID}"
    requertid = md5_sign(sign_str)

    headers = {
        'AuthorizationClient': f'Bearer {jwt_token}',
        'requerttime': requerttime,
        'nonestr': nonestr,
        'requertid': requertid
    }

    if statisticsinfo:
        headers['statisticsinfo'] = statisticsinfo

    try:
        response = requests.post(url, json=body, headers=headers, timeout=10)

        if response.status_code == 200:
            result = response.json()
            return result

        return None

    except Exception:
        return None

def process_single_phone(phone, imei=None):
    if imei is None:
        imei = generate_random_imei()

    score_stats = {
        'initial_score': 0,
        'final_score': 0,
        'earned_today': 0,
        'tasks_completed': []
    }

    log(f"开始处理手机号: {phone}")

    try:
        woread_data = woread_login(phone)
        if not woread_data:
            return None

        userid = woread_data["userid"]
        woread_token = woread_data["token"]

        temp_useraccount = phone
        clientconfirm = calculate_clientconfirm(userid, imei)
        statisticsinfo = build_statisticsinfo(userid, temp_useraccount, imei, clientconfirm)

        jwt_token = get_jwt_token(statisticsinfo)
        if not jwt_token:
            return None

        profile_data = get_read_profile(woread_token, userid, jwt_token, statisticsinfo)
        if not profile_data:
            return None

        if profile_data.get("code") != "0000":
            return None

        message = profile_data.get("message", {})
        real_useraccount = message.get("mobile")

        if not real_useraccount:
            return None

        clientconfirm = calculate_clientconfirm(userid, imei)
        statisticsinfo = build_statisticsinfo(userid, real_useraccount, imei, clientconfirm)

        aiting_login_data = aiting_user_login(phone, real_useraccount, jwt_token, statisticsinfo)
        if not aiting_login_data:
            return None

        aiting_token = aiting_login_data["token"]
        aiting_userid = aiting_login_data["userid"]

        ticket_data = get_info_ticket(aiting_token, aiting_userid, jwt_token, statisticsinfo)
        if not ticket_data:
            return None

        woread_sign_in(userid, woread_token, jwt_token, statisticsinfo)

        if ticket_data and ticket_data.get('code') == '0000':
            message_url = ticket_data.get('message', '')

            parsed_url = urllib.parse.urlparse(message_url)
            query_params = urllib.parse.parse_qs(parsed_url.query)
            ticket_str = query_params.get('ticket', [''])[0]

            if not ticket_str:
                return None

            user_info = jf_get_user_info(ticket_str)
            if user_info and user_info.get('code') == '0000':
                data = user_info.get('data', {})
                score_stats['initial_score'] = data.get('todayEarnScore', 0)
                score_stats['available_score'] = data.get('availableScore', 0)
                log(f"当前积分: 今日已获得 {score_stats['initial_score']} 积分, 可用 {score_stats['available_score']} 积分")

            task_detail = jf_get_task_detail(ticket_str)
            if task_detail and task_detail.get('code') == '0000':
                task_list = task_detail.get('data', {}).get('taskDetail', {}).get('taskList', [])

                unfinished_tasks = []
                for task in task_list:
                    task_name = task.get('taskName', '')
                    finish = task.get('finish', 0)
                    task_code = task.get('taskCode', '')
                    score = task.get('score', 0)
                    finish_count = task.get('finishCount', 0)
                    need_count = task.get('needCount', 1)

                    if finish == 0:
                        unfinished_tasks.append({
                            'code': task_code,
                            'name': task_name,
                            'score': score,
                            'finish_count': finish_count,
                            'need_count': need_count
                        })

                aiting_complete_task(userid, woread_token, jwt_token, statisticsinfo, task_type=2)
                time.sleep(1)

                aiting_complete_task(userid, woread_token, jwt_token, statisticsinfo, task_type=4)
                time.sleep(1)

                if unfinished_tasks:

                    notification_task = None
                    other_tasks = []

                    for task in unfinished_tasks:
                        task_name = task['name']
                        if '通知' in task_name:
                            notification_task = task
                        elif '邀请' not in task_name:
                            other_tasks.append(task)

                    for task in other_tasks:
                        task_name = task['name']
                        task_code = task['code']
                        finish_count = task.get('finish_count', 0)
                        need_count = task.get('need_count', 1)

                        if ('听读看' in task_name or '阅读' in task_name) and '邀请' not in task_name:
                            log(f"执行阅读任务: {task_name}")
                            result = jf_to_finish(ticket_str, task_code)
                            time.sleep(2)

                            log("阅读中...")
                            woread_new_read_add(userid, woread_token, jwt_token, statisticsinfo)
                            time.sleep(120)
                            woread_add_read_time(userid, woread_token, jwt_token, statisticsinfo, readtime=120)
                            time.sleep(2)

                            result = jf_pop_up(ticket_str)
                            if result and result.get('code') == '0000':
                                data = result.get('data', {})
                                score = data.get('score', '')
                                if score:
                                    log(f"第1次完成: {score}", "SUCCESS")
                                else:
                                    time.sleep(2)
                                    list_result = jf_get_task_detail(ticket_str)
                                    if list_result and list_result.get('code') == '0000':
                                        time.sleep(2)
                                        jf_pop_up(ticket_str)
                            else:
                                msg = result.get('msg', '未知错误') if result else '请求失败'

                                if '登录' in msg:
                                    ticket_result = get_info_ticket(aiting_token, aiting_userid, jwt_token, statisticsinfo)
                                    if ticket_result and ticket_result.get('code') == '0000':
                                        message_url = ticket_result.get('message', '')
                                        parsed_url = urllib.parse.urlparse(message_url)
                                        query_params = urllib.parse.parse_qs(parsed_url.query)
                                        new_ticket = query_params.get('ticket', [''])[0]

                                        if new_ticket:
                                            ticket_str = new_ticket

                                            result = jf_to_finish(ticket_str, task_code)
                                            if not (result and result.get('code') == '0000'):
                                                continue
                                            time.sleep(2)

                                            woread_new_read_add(userid, woread_token, jwt_token, statisticsinfo)
                                            time.sleep(10)
                                            woread_add_read_time(userid, woread_token, jwt_token, statisticsinfo, readtime=10)
                                            time.sleep(2)

                                            jf_pop_up(ticket_str)

                            time.sleep(2)

                            log("执行第2次阅读")
                            result = jf_to_finish(ticket_str, task_code)
                            if result and result.get('code') == '0000':
                                pass
                            else:
                                msg = result.get('msg', '未知错误') if result else '请求失败'

                                if '登录' in msg:
                                    ticket_result = get_info_ticket(aiting_token, aiting_userid, jwt_token, statisticsinfo)
                                    if ticket_result and ticket_result.get('code') == '0000':
                                        message_url = ticket_result.get('message', '')
                                        parsed_url = urllib.parse.urlparse(message_url)
                                        query_params = urllib.parse.parse_qs(parsed_url.query)
                                        new_ticket = query_params.get('ticket', [''])[0]

                                        if new_ticket:
                                            ticket_str = new_ticket

                                            result = jf_to_finish(ticket_str, task_code)
                                            if not (result and result.get('code') == '0000'):
                                                continue
                                        else:
                                            continue
                                    else:
                                        continue
                            time.sleep(2)

                            log("阅读中...")
                            woread_new_read_add(userid, woread_token, jwt_token, statisticsinfo)
                            time.sleep(120)
                            woread_add_read_time(userid, woread_token, jwt_token, statisticsinfo, readtime=120)
                            time.sleep(2)

                            result = jf_pop_up(ticket_str)
                            if result and result.get('code') == '0000':
                                data = result.get('data', {})
                                score = data.get('score', '')
                                if score:
                                    log(f"第2次完成: {score}", "SUCCESS")
                                else:
                                    time.sleep(2)
                                    list_result = jf_get_task_detail(ticket_str)
                                    if list_result and list_result.get('code') == '0000':
                                        time.sleep(2)
                                        jf_pop_up(ticket_str)
                            else:
                                msg = result.get('msg', '未知错误') if result else '请求失败'

                                if '登录' in msg:
                                    ticket_result = get_info_ticket(aiting_token, aiting_userid, jwt_token, statisticsinfo)
                                    if ticket_result and ticket_result.get('code') == '0000':
                                        message_url = ticket_result.get('message', '')
                                        parsed_url = urllib.parse.urlparse(message_url)
                                        query_params = urllib.parse.parse_qs(parsed_url.query)
                                        new_ticket = query_params.get('ticket', [''])[0]

                                        if new_ticket:
                                            ticket_str = new_ticket

                                            result = jf_to_finish(ticket_str, task_code)
                                            if not (result and result.get('code') == '0000'):
                                                continue
                                            time.sleep(2)

                                            woread_new_read_add(userid, woread_token, jwt_token, statisticsinfo)
                                            time.sleep(10)
                                            woread_add_read_time(userid, woread_token, jwt_token, statisticsinfo, readtime=10)
                                            time.sleep(2)

                                            jf_pop_up(ticket_str)
                        else:
                            remaining = need_count - finish_count
                            log(f"执行任务: {task_name} (剩余{remaining}次)")

                            for i in range(remaining):
                                new_ticket_result = get_info_ticket(woread_token, userid, jwt_token, statisticsinfo)
                                if new_ticket_result and new_ticket_result.get('code') == '0000':
                                    message_url = new_ticket_result.get('message', '')
                                    parsed_url = urllib.parse.urlparse(message_url)
                                    query_params = urllib.parse.parse_qs(parsed_url.query)
                                    new_ticket_str = query_params.get('ticket', [''])[0]

                                    if new_ticket_str:
                                        ticket_str = new_ticket_str
                                time.sleep(1)

                                jf_to_finish(ticket_str, task_code)
                                time.sleep(1)

                                aiting_complete_task(userid, woread_token, jwt_token, statisticsinfo, task_type=4)
                                time.sleep(2)

                                result = jf_pop_up(ticket_str)
                                if result and result.get('code') == '0000':
                                    data = result.get('data', {})
                                    score = data.get('score', '')
                                    if score:
                                        log(f"{task_name} 第{i+1}次完成: {score}", "SUCCESS")

                                if i < remaining - 1:
                                    time.sleep(1)

                        time.sleep(1)

                    if notification_task:
                        task_code = notification_task['code']
                        task_name = notification_task.get('name', '通知任务')
                        log(f"执行任务: {task_name}")

                        new_ticket_result = get_info_ticket(aiting_token, aiting_userid, jwt_token, statisticsinfo)
                        if new_ticket_result and new_ticket_result.get('code') == '0000':
                            message_url = new_ticket_result.get('message', '')
                            parsed_url = urllib.parse.urlparse(message_url)
                            query_params = urllib.parse.parse_qs(parsed_url.query)
                            new_ticket_str = query_params.get('ticket', [''])[0]

                            if new_ticket_str:
                                ticket_str = new_ticket_str

                        time.sleep(1)

                        jf_to_finish(ticket_str, task_code)

                        time.sleep(1)

                        aiting_complete_task(aiting_userid, aiting_token, jwt_token, statisticsinfo, task_type=2)

                        time.sleep(2)

                        result = jf_pop_up(ticket_str)
                        if result and result.get('code') == '0000':
                            data = result.get('data', {})
                            score = data.get('score', '')
                            if score:
                                log(f"{task_name} 完成: {score}", "SUCCESS")

                        time.sleep(1)

                        task_detail = jf_get_task_detail(ticket_str)
                        if task_detail and task_detail.get('code') == '0000':
                            task_list = task_detail.get('data', {}).get('taskDetail', {}).get('taskList', [])

                            for task in task_list:
                                if task.get('taskCode') == task_code:
                                    finish = task.get('finish', 0)

                                    if finish == 1:
                                        time.sleep(1)
                                        jf_pop_up(ticket_str)
                                    break

                        time.sleep(1)

        time.sleep(10)
        check_ticket_data = get_info_ticket(woread_token, userid, jwt_token, statisticsinfo)
        if check_ticket_data and check_ticket_data.get('code') == '0000':
            message_url = check_ticket_data.get('message', '')
            parsed_url = urllib.parse.urlparse(message_url)
            query_params = urllib.parse.parse_qs(parsed_url.query)
            check_ticket_str = query_params.get('ticket', [''])[0]

            if check_ticket_str:
                check_task_detail = jf_get_task_detail(check_ticket_str)
                if check_task_detail and check_task_detail.get('code') == '0000':
                    task_list = check_task_detail.get('data', {}).get('taskDetail', {}).get('taskList', [])

                    remaining_tasks = []
                    for task in task_list:
                        task_name = task.get('taskName', '')
                        finish = task.get('finish', 0)
                        task_code = task.get('taskCode', '')

                        if finish == 0 and '邀请' not in task_name:
                            remaining_tasks.append({
                                'name': task_name,
                                'code': task_code
                            })

                    if remaining_tasks:
                        for task in remaining_tasks:
                            task_code = task['code']

                            new_ticket_result = get_info_ticket(woread_token, userid, jwt_token, statisticsinfo)
                            if new_ticket_result and new_ticket_result.get('code') == '0000':
                                message_url = new_ticket_result.get('message', '')
                                parsed_url = urllib.parse.urlparse(message_url)
                                query_params = urllib.parse.parse_qs(parsed_url.query)
                                new_ticket_str = query_params.get('ticket', [''])[0]

                                if new_ticket_str:
                                    check_ticket_str = new_ticket_str
                            time.sleep(1)

                            jf_to_finish(check_ticket_str, task_code)
                            time.sleep(1)

                            aiting_complete_task(userid, woread_token, jwt_token, statisticsinfo, task_type=4)
                            time.sleep(2)

                            jf_pop_up(check_ticket_str)

                            time.sleep(1)
        latest_ticket_data = get_info_ticket(woread_token, userid, jwt_token, statisticsinfo)
        if latest_ticket_data and latest_ticket_data.get('code') == '0000':
            message_url = latest_ticket_data.get('message', '')
            parsed_url = urllib.parse.urlparse(message_url)
            query_params = urllib.parse.parse_qs(parsed_url.query)
            latest_ticket_str = query_params.get('ticket', [''])[0]

            if latest_ticket_str:
                final_user_info = jf_get_user_info(latest_ticket_str)
                if final_user_info and final_user_info.get('code') == '0000':
                    data = final_user_info.get('data', {})
                    score_stats['final_score'] = data.get('todayEarnScore', 0)
                    score_stats['earned_today'] = score_stats['final_score'] - score_stats['initial_score']

                    log(f"手机号: {data.get('phone', 'N/A')}")
                    log(f"今日总获得积分: {score_stats['final_score']}")
                    log(f"本次运行获得: {score_stats['earned_today']} 积分", "SUCCESS")
                    log(f"可用积分: {data.get('availableScore', 0)}")
                    log(f"累计获得积分: {data.get('allEarnScore', 0)}")

                    if score_stats['earned_today'] > 0:
                        notify_msg = f"联通爱听任务完成\n手机号: {phone}\n本次获得: {score_stats['earned_today']} 积分\n今日总计: {score_stats['final_score']} 积分"
                        if NOTIFY_AVAILABLE:
                            try:
                                notify.send("联通爱听", notify_msg)
                                log("通知发送成功", "SUCCESS")
                            except Exception as notify_err:
                                log(f"通知发送失败: {notify_err}", "WARNING")
                        else:
                            print(f"\n  📢 通知内容:\n{notify_msg}")
                else:
                    log(f"获取积分信息失败: {final_user_info.get('msg', '未知错误') if final_user_info else '请求失败'}", "ERROR")
            else:
                log("无法提取ticket", "ERROR")
        else:
            log(f"获取ticket失败: {latest_ticket_data.get('msg', '未知错误') if latest_ticket_data else '请求失败'}", "ERROR")

        return {
            "profile": profile_data,
            "ticket": ticket_data,
            "score_stats": score_stats
        }

    except Exception:
        return None


def main():
    """主函数"""
    phone_list = re.split(r'[@&\n]', phone_vs)
    phone_list = [p.strip() for p in phone_list if p.strip()]

    results = {}

    for idx, phone in enumerate(phone_list, 1):
        log(f"第 {idx}/{len(phone_list)} 个账号")

        result = process_single_phone(phone)
        results[phone] = result

        if idx < len(phone_list):
            time.sleep(2)

    success_count = sum(1 for r in results.values() if r is not None)
    fail_count = len(results) - success_count

    log(f"总计: {len(results)} 个账号, 成功: {success_count} 个, 失败: {fail_count} 个")

    for phone, result in results.items():
        if result is not None:
            log(f"✓ {phone}", "SUCCESS")
        else:
            log(f"✗ {phone}", "ERROR")


if __name__ == "__main__":
    main()

