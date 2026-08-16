# -*- coding: utf-8 -*-
"""
=========================================
        作者：JOH 小丑 呆呆 
        售后1群QQ：716677130
        售后1群QQ：991774923
        购买公益接口作者Q1:1934103887
        购买公益接口作者Q2:12567501
        购买公益接口作者Q3:2661320550
=========================================

UC浏览器极速版 - 开源只学习交流觉得可以联系上面的信息购买接口

环境变量:

1) UC_ACCOUNTS   填 token（多账号换行）
   备注#kps=xxx&ut=xxx&ds=xxx&mt=xxx&de=xxx&dn=xxx&ni=xxx&lb=xxx&wf=xxx&ch=xxx&ve=xxx&sn=xxx&mi=xxx&bd=xxx
   最少: 备注#kps=xxx&ut=xxx

2) UC_SIGN_RPC   填签名接口地址
   例: http://111.128.173.91:18888

从环境变量读 token，持续刷视频到各任务日上限。
停止: STOP_VIDEO_FARM.txt 或任务全满/失效。
"""
from __future__ import annotations

import json
import os
import sys
import time
import uuid
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

try:
    import requests
    from requests.packages.urllib3.exceptions import InsecureRequestWarning  # type: ignore

    requests.packages.urllib3.disable_warnings(InsecureRequestWarning)  # type: ignore
except ImportError:
    os.system(f"{sys.executable} -m pip install requests -q")
    import requests
    from requests.packages.urllib3.exceptions import InsecureRequestWarning  # type: ignore

    requests.packages.urllib3.disable_warnings(InsecureRequestWarning)  # type: ignore

HERE = Path(__file__).resolve().parent
TOKENS_PATH = HERE / "live_tokens.json"
RESULT_PATH = HERE / "uc_lite_main_result.json"
STOP_PATH = HERE / "STOP_VIDEO_FARM.txt"

HOST_CORAL2 = "https://coral2.uc.cn"
HOST_CORAL_TASK = "https://coral-task.uc.cn"
FARM_SALT = "sy5th908xb9bmgiz2ssy0cykzezkq1jf"
MODULE_TASK = "8ee46ec7f90543a290e8667c02c0ecb2"
MODULE_YB = "6a7acf9bf37c4c49b515c369fa4a46b4"
MODULE_LIST = (
    f"{MODULE_YB},9c524f8bb1524b14840d15c5cec38133,"
    "5ecbf1ebc8554065a824064fd71c3dfb,61fc17c6e1884a90b57738c9973439a3,"
    "1748d580510246a59262b97f20145ba4"
)
APP_ID_H5 = "_dft_uclite_piggy"
APP_ID_TASK = "uclite_piggy_task"
FVE = "3.9.46"
SIGN_RPC_DEFAULT = "http://127.0.0.1:17890"
CLAIM_INTERVAL = 7.0  # EMPTY_BACKOFF enabled

VIDEO_TIDS: List[Tuple[str, int]] = [
    # 主视频（已可 coral-task）
    ("1789725", 9671),
    ("39823", 9671),
    ("1795864", 9671),
    # 高级/限时视频（手机成功走 coral2）
    ("1795863", 9655),   # 看视频轻松赚元宝
    ("1792321", 9671),
    ("1795844", 9671),
    # 宝箱兜底（抓包有 120 奖，target=30）
    ("1794063", 9806),
]

UA = (
    "Mozilla/5.0 (Linux; U; Android 16; zh-CN; V2426A Build/BQ2A.250705.001) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/100.0.4896.58 "
    "UCBrowser/18.9.4.1458 Mobile Safari/537.36"
)


def log(msg: str, level: str = "信息") -> None:
    print(f"[{time.strftime('%H:%M:%S')}][{level}] {msg}", flush=True)


def notify(title: str, content: str) -> None:
    try:
        from notify import send  # type: ignore

        send(title, content)
    except Exception:
        pass



TOKEN_KEYS = (
    "kps", "ut", "st", "uid", "ds", "mt", "de", "dn", "ni", "lb", "wf",
    "ch", "ve", "sn", "mi", "bd", "fr", "pr", "nn", "pc", "od", "oc",
)


def _parse_kv_blob(blob: str) -> Dict[str, str]:
    """parse a=b&c=d or a=b;c=d or JSON-ish key values."""
    blob = (blob or "").strip()
    out: Dict[str, str] = {}
    if not blob:
        return out
    if blob.startswith("{") and blob.endswith("}"):
        try:
            j = json.loads(blob)
            if isinstance(j, dict):
                for k, v in j.items():
                    if v is None or isinstance(v, (dict, list)):
                        continue
                    out[str(k)] = str(v)
                return out
        except Exception:
            pass
    # normalize separators
    s = blob.replace(";", "&").replace(",", "&").replace("\n", "&")
    # if pure kps without key
    if "=" not in s and len(s) > 20:
        out["kps"] = s
        return out
    for part in s.split("&"):
        part = part.strip()
        if not part or "=" not in part:
            continue
        k, v = part.split("=", 1)
        k = k.strip()
        v = v.strip().strip('"').strip("'")
        if k:
            out[k] = v
    return out


def parse_accounts(raw: str) -> List[Dict[str, Any]]:
    """
    多账号换行。每行:
      备注#kps=...&ut=...&ds=...
      手机号
      手机号#密码
    返回: [{label,user,password,token}]
    """
    raw = (raw or "").strip()
    if not raw:
        return []
    lines: List[str] = []
    for chunk in raw.replace("\r", "\n").split("\n"):
        chunk = chunk.strip()
        if not chunk or chunk.startswith("//") or chunk.startswith("# "):
            continue
        # also allow old & multi on one line without kps=
        if "&" in chunk and "kps=" not in chunk.lower() and re.fullmatch(r"[\d&#|@:\s]+", chunk):
            for p in chunk.split("&"):
                p = p.strip()
                if p:
                    lines.append(p)
        else:
            lines.append(chunk)

    accounts: List[Dict[str, Any]] = []
    for line in lines:
        label = ""
        body = line
        if "#" in line:
            # 备注#payload  —— 但 payload 里也可能有 #，只切第一个
            a, b = line.split("#", 1)
            # 若 a 是 11 位手机且 b 不含 =，当密码
            if re.fullmatch(r"\d{11}", a.strip()) and "=" not in b and "kps" not in b.lower():
                accounts.append({
                    "label": a.strip(),
                    "user": a.strip(),
                    "password": b.strip(),
                    "token": {},
                })
                continue
            label = a.strip() or "acc"
            body = b.strip()
        else:
            body = line.strip()
            label = body[:16]

        kv = _parse_kv_blob(body)
        # 不再支持仅手机号（不读 live_tokens 文件）

        tok = {k: kv[k] for k in TOKEN_KEYS if kv.get(k)}
        # also accept X-U-KPS-WG
        if not tok.get("kps"):
            for alt in ("X-U-KPS-WG", "X_U_KPS_WG", "KPS"):
                if kv.get(alt):
                    tok["kps"] = kv[alt]
                    break
        user = str(kv.get("user") or kv.get("phone") or label or "").strip()
        if re.fullmatch(r"\d{11}", label):
            user = label
        if not user:
            user = label or f"acc{len(accounts)+1}"
        if not tok.get("kps"):
            log(f"账号行缺少 kps（需 备注#kps=..&ut=..）: {line[:40]}…", "警告")
            continue
        if not tok.get("ut"):
            log(f"账号行缺少 ut（领奖加签需要）: {label}", "警告")
        accounts.append({
            "label": label or user,
            "user": user,
            "password": "",
            "token": tok,
        })
    return accounts


# ---------------------------------------------------------------------------
# 登录
# ---------------------------------------------------------------------------
def make_kps(st: str, uid: str, rpc: str) -> Dict[str, Any]:
    try:
        j = requests.post(
            rpc.rstrip("/") + "/make_kps",
            json={"token": st, "uid": uid, "nickname": ""},
            timeout=120,
        ).json()
    except Exception as e:
        return {"error": str(e)}
    out: Dict[str, Any] = {}
    if j.get("ok") and j.get("kps"):
        out["kps"] = j["kps"]
        if j.get("ut"):
            out["ut"] = j["ut"]
    else:
        out["error"] = j.get("error") or j
    return out



def login_by_password(user: str, password: str, rpc: str) -> Dict[str, Any]:
    log(f"账密登录: {user[:3]}****{user[-4:] if len(user) >= 7 else user}")
    # 优先：宿主机 SignRPC 的 /pwd_login（容器无 playwright）
    auth: Dict[str, Any] = {}
    try:
        r = requests.post(
            rpc.rstrip("/") + "/pwd_login",
            json={"phone": user, "password": password},
            timeout=180,
        )
        j = r.json()
        if j.get("ok") and isinstance(j.get("auth"), dict):
            auth = dict(j["auth"])
            log("宿主机 SignRPC 账密登录完成", "成功")
        else:
            log(f"SignRPC /pwd_login 返回: {j.get('error') or j}", "警告")
    except Exception as e:
        log(f"SignRPC /pwd_login 调用失败: {e}", "警告")

    # 回退：容器内本地 playwright（一般没有）
    if not auth.get("kps") and not (auth.get("st") and auth.get("uid")):
        os.environ["UC_USER"] = user
        os.environ["UC_PASS"] = password
        os.environ["UC_SIGN_RPC"] = rpc
        sys.path.insert(0, str(HERE))
        try:
            import uc_pwd_playwright as login_mod  # type: ignore
            code = login_mod.main()
            for name in ("login_result.json", "pwd_playwright_result.json", "live_tokens.json"):
                p = HERE / name
                if not p.is_file():
                    continue
                try:
                    data = json.loads(p.read_text(encoding="utf-8-sig"))
                except Exception:
                    continue
                if name == "live_tokens.json":
                    for k in ("kps", "ut", "st", "uid", "ds", "mt", "de", "dn", "ni", "lb", "wf", "ch", "ve"):
                        if data.get(k):
                            auth[k] = data[k]
                else:
                    a = data.get("auth") or {}
                    for k in ("kps", "ut", "st", "uid"):
                        if a.get(k):
                            auth[k] = a[k]
            log(f"本地 playwright 登录 exit={code}", "信息")
        except Exception as e:
            log(f"本地 playwright 不可用: {e}", "警告")

    if not auth.get("kps") and auth.get("st") and auth.get("uid"):
        log("make_kps…")
        mk = make_kps(str(auth["st"]), str(auth["uid"]), rpc)
        auth.update(mk)

    if not auth.get("kps"):
        raise RuntimeError(
            "登录未拿到 kps。请先双击桌面「启动_UC_SignRPC_17890.bat」，"
            "保持 MuMu+UC 打开，并确认宿主机已装 playwright"
        )

    if not auth.get("ut") and TOKENS_PATH.is_file():
        try:
            old = json.loads(TOKENS_PATH.read_text(encoding="utf-8-sig"))
            old_user = str(old.get("user") or old.get("phone") or "")
            same_user = (not user) or (not old_user) or (user in old_user or old_user in user)
            same_uid = str(old.get("uid") or "") == str(auth.get("uid") or "")
            if same_user and same_uid and old.get("ut"):
                auth["ut"] = old["ut"]
        except Exception:
            pass

    if not auth.get("ut"):
        log("无 ut，部分加签可能失败", "警告")

    merged: Dict[str, Any] = {}
    if TOKENS_PATH.is_file():
        try:
            merged = json.loads(TOKENS_PATH.read_text(encoding="utf-8-sig"))
        except Exception:
            merged = {}

    # 同 uid 时保留设备侧字段（ut/ds/mt/...），账密登录通常只返回 st/uid/kps
    device_keys = (
        "ut", "ds", "mt", "de", "dn", "ni", "lb", "wf", "ch", "ve",
        "sn", "mi", "bd", "fr", "pr",
    )
    same_uid = str(merged.get("uid") or "") == str(auth.get("uid") or "")
    if not same_uid:
        # 尝试从 outputs 历史样本补设备参数（仅同 uid）
        for cand in [
            HERE / "httpcanary_1006_tokens.json",
            Path(r"C:/Users/Administrator/Documents/Codex/2026-07-15/new-chat-3/outputs/live_tokens.json"),
            Path(r"C:/Users/Administrator/Documents/Codex/2026-07-15/new-chat-3/outputs/httpcanary_1006_tokens.json"),
        ]:
            if not cand.is_file():
                continue
            try:
                old = json.loads(cand.read_text(encoding="utf-8-sig"))
            except Exception:
                continue
            if str(old.get("uid") or "") == str(auth.get("uid") or ""):
                for k in device_keys:
                    if old.get(k) and not auth.get(k):
                        auth[k] = old[k]
                log(f"已从历史样本补设备参数: {cand.name}", "信息")
                break
    else:
        for k in device_keys:
            if merged.get(k) and not auth.get(k):
                auth[k] = merged[k]

    for k, v in auth.items():
        if v:
            merged[k] = v
    # 若仍无 ut，再扫一次历史
    if not merged.get("ut"):
        for cand in [
            HERE / "httpcanary_1006_tokens.json",
            Path(r"C:/Users/Administrator/Documents/Codex/2026-07-15/new-chat-3/outputs/live_tokens.json"),
            Path(r"C:/Users/Administrator/Documents/Codex/2026-07-15/new-chat-3/outputs/httpcanary_1006_tokens.json"),
        ]:
            if not cand.is_file():
                continue
            try:
                old = json.loads(cand.read_text(encoding="utf-8-sig"))
            except Exception:
                continue
            if str(old.get("uid") or "") == str(merged.get("uid") or "") and old.get("ut"):
                merged["ut"] = old["ut"]
                for k in device_keys:
                    if old.get(k) and not merged.get(k):
                        merged[k] = old[k]
                log(f"已补 ut 自 {cand.name}", "信息")
                break

    merged["source"] = "UC_ACCOUNTS"
    merged["user"] = user
    merged["time"] = time.strftime("%Y-%m-%dT%H:%M:%S")
    TOKENS_PATH.write_text(json.dumps(merged, ensure_ascii=False, indent=2), encoding="utf-8")
    try:
        (HERE / f"live_tokens_{user}.json").write_text(json.dumps(merged, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        pass
    log(f"登录成功 kps={str(merged.get('kps'))[:18]}… ut={'有' if merged.get('ut') else '无'}", "成功")
    return merged

# ---------------------------------------------------------------------------
# 客户端
# ---------------------------------------------------------------------------
class SignRPC:
    def __init__(self, base: str) -> None:
        self.base = base.rstrip("/")
        self.s = requests.Session()
        self.s.trust_env = False

    def ok(self) -> bool:
        try:
            return bool(self.s.get(self.base + "/", timeout=5).json().get("ok"))
        except Exception:
            return False

    def farm_sign(self, plain: str) -> str:
        last = None
        for i in range(2):
            try:
                j = self.s.post(
                    self.base + "/farm_sign",
                    json={"plain": plain, "salt": "", "op": "farm_sign"},
                    timeout=70,
                ).json()
            except Exception as e:
                last = str(e)
                log(f"加签异常 重试{i+1}: {e}", "警告")
                time.sleep(8 + i * 8)
                continue
            if j.get("ok") and j.get("sign"):
                return str(j["sign"])
            last = j.get("error") or j
            log(f"加签失败 重试{i+1}: {last}", "警告")
            # 失败后长冷却，避免连环注入把 UC 打成 err:108
            time.sleep(12 + i * 10)
        raise RuntimeError(f"加签失败: {last}")




class Client:
    def __init__(self, tok: Dict[str, Any], rpc_url: str) -> None:
        self.tok = tok
        self.kps = tok["kps"]
        self.ut = tok.get("ut") or ""
        self.rpc = SignRPC(rpc_url)
        self.s = requests.Session()
        self.s.trust_env = False

    def headers(self) -> Dict[str, str]:
        return {
            "User-Agent": UA,
            "Accept": "application/json",
            "Origin": "https://broccoli.uc.cn",
            "Referer": "https://broccoli.uc.cn/",
            "X-U-KPS-WG": self.kps,
            "Content-Type": "application/json;charset=UTF-8",
        }

    def qbase(self) -> Dict[str, str]:
        t = self.tok
        return {
            "uc_param_str": "dsdnfrpfbivessbtbmnilauputogpintnwmtsvcppcprsnnnchmicgodmekplobdmicgodcadebcaaoclbwf",
            "kps": self.kps,
            "ut": self.ut,
            "fr": "android",
            "pr": "UCLite",
            "ve": t.get("ve") or "18.9.4.1458",
            "ch": t.get("ch") or "",
            "ds": t.get("ds") or "",
            "mt": t.get("mt") or "",
            "de": t.get("de") or "",
            "dn": t.get("dn") or "",
            "ni": t.get("ni") or "",
            "lb": t.get("lb") or "",
            "wf": t.get("wf") or "",
            "sn": t.get("sn") or "",
            "mi": t.get("mi") or "",
            "bd": t.get("bd") or "",
            "appId": APP_ID_H5,
        }

    def balance(self) -> Optional[int]:
        q = self.qbase()
        q["__t"] = str(int(time.time() * 1000))
        q["moduleCodeList"] = MODULE_LIST
        q["publishId"] = "9655"
        r = self.s.get(
            f"{HOST_CORAL2}/currency/v1/ucliteHomepage",
            params=q,
            headers=self.headers(),
            timeout=25,
        )
        j = r.json() if r.text.startswith("{") else {}
        bi = ((j.get("data") or {}).get("balanceInfo") or {})
        return (bi.get(MODULE_YB) or {}).get("balance")

    def list_video_tasks(self) -> List[Dict[str, Any]]:
        q = self.qbase()
        q.update(
            {
                "__t": str(int(time.time() * 1000)),
                "entry": "toolbar",
                "evSub": "uclite_fuli_index",
                "codes": "uc_piggy_task_nest,uc_piggy_limit_time,uc_piggy_xssvideo_fuli",
                "requestId": str(uuid.uuid4()),
                "fve": FVE,
                "activeUser": "1",
                "prioritySize": "1",
            }
        )
        r = self.s.get(
            f"{HOST_CORAL2}/uclite/queryByMultiResource",
            params=q,
            headers=self.headers(),
            timeout=25,
        )
        j = r.json() if r.text.startswith("{") else {}
        out = []
        for _, block in (j.get("data") or {}).items():
            if not isinstance(block, dict):
                continue
            for t in block.get("taskList") or []:
                ev = str(t.get("event") or "")
                name = str(t.get("name") or "")
                gc = str(t.get("groupCode") or "")
                if ev == "video_ad_new" or "视频" in name or gc in ("video", "video_advanced"):
                    ri = t.get("rewardItems") or [{}]
                    out.append(
                        {
                            "id": str(t.get("id")),
                            "name": t.get("name"),
                            "dayTimes": t.get("dayTimes"),
                            "publishId": t.get("publishId") or 9671,
                            "amount": (ri[0] or {}).get("amount"),
                        }
                    )
        return out

    def farm_sign(self, tid: str, rid: str) -> str:
        plain = f"{self.ut}{tid}complete1{rid}{FARM_SALT}"
        return self.rpc.farm_sign(plain)

    @staticmethod
    def prize(j: Dict[str, Any]) -> Optional[int]:
        data = j.get("data") or {}
        pr = data.get("prizes") or []
        if pr:
            try:
                amt = (pr[0].get("rewardItem") or pr[0]).get("amount")
                if amt is not None:
                    return int(amt)
            except Exception:
                pass
        # some payloads put amount on curTask/rewardItems
        cur = data.get("curTask") or {}
        for ri in cur.get("rewardItems") or []:
            try:
                if ri.get("amount") is not None:
                    return int(ri.get("amount"))
            except Exception:
                pass
        if data.get("amount") is not None:
            try:
                return int(data.get("amount"))
            except Exception:
                pass
        return None

        try:
            return (pr[0].get("rewardItem") or pr[0]).get("amount")
        except Exception:
            return None

    def claim_video(self, tid: str, publish_id: int) -> Dict[str, Any]:
        """优先手机成功路径 coral2 POST /uclite/trigger，再回退 coral-task GET。"""
        def _do_coral2(rid: str, sign: str) -> Dict[str, Any]:
            body = {
                "kps": self.kps,
                "appId": APP_ID_H5,
                "moduleCode": MODULE_TASK,
                "useUtCompleteTask": False,
                "publishId": int(publish_id),
                "fve": FVE,
                "tid": int(tid),
                "type": "complete",
                "value": 1,
                "requestId": rid,
                "sign": sign,
                "salt": FARM_SALT,
            }
            r = self.s.post(
                f"{HOST_CORAL2}/uclite/trigger",
                params=self.qbase(),
                json=body,
                headers=self.headers(),
                timeout=30,
            )
            try:
                return r.json()
            except Exception:
                return {"raw": r.text[:200]}

        def _do_coral_task(rid: str, sign: str) -> Dict[str, Any]:
            params = {
                "appId": APP_ID_TASK,
                "moduleCode": MODULE_TASK,
                "value": "1",
                "type": "complete",
                "kps": self.kps,
                "requestId": rid,
                "salt": FARM_SALT,
                "sign": sign,
                "tid": str(tid),
                "_ch": "native",
                "uc_param_str": "utpcsnnnvebipfdnprfrcgch",
                "ve": self.tok.get("ve") or "18.9.4.1458",
                "fr": "android",
                "ut": self.ut,
                "entry": "toolbar",
                "from": "",
                "pr": "UCLite",
                "ch": self.tok.get("ch") or "",
            }
            r = self.s.get(
                f"{HOST_CORAL_TASK}/task/trigger",
                params=params,
                headers={"User-Agent": UA, "X-U-KPS-WG": self.kps},
                timeout=30,
            )
            try:
                return r.json()
            except Exception:
                return {"raw": r.text[:200]}

        # 1) coral2 first (抓包 1008 手机成功路径)
        rid = str(uuid.uuid4())
        try:
            sign = self.farm_sign(tid, rid)
        except Exception as e:
            return {"tid": tid, "ok": False, "error": f"加签失败: {e}"}
        j = _do_coral2(rid, sign)
        path = "coral2"
        prz = self.prize(j if isinstance(j, dict) else {})
        good = bool(j.get("success") and j.get("code") == "OK" and isinstance(prz, int) and prz > 0)

        # 2) coral2 OK 但无奖 / 失败 → 再试 coral-task
        if not good:
            rid2 = str(uuid.uuid4())
            try:
                sign2 = self.farm_sign(tid, rid2)
            except Exception as e:
                # 若 coral2 已是 OK 无奖，仍返回 coral2 结果
                if j.get("success") and j.get("code") == "OK":
                    cur = (j.get("data") or {}).get("curTask") or {}
                    return {
                        "tid": tid,
                        "ok": True,
                        "code": j.get("code"),
                        "msg": j.get("msg"),
                        "prize": prz,
                        "dayTimes": cur.get("dayTimes"),
                        "path": path,
                    }
                return {"tid": tid, "ok": False, "code": j.get("code"), "msg": j.get("msg"), "error": f"回退加签失败: {e}"}
            j2 = _do_coral_task(rid2, sign2)
            p2 = self.prize(j2 if isinstance(j2, dict) else {})
            if j2.get("success") and j2.get("code") == "OK" and isinstance(p2, int) and p2 > 0:
                j, path, prz = j2, "coral-task", p2
            elif (not (j.get("success") and j.get("code") == "OK")) and j2.get("success") and j2.get("code") == "OK":
                j, path, prz = j2, "coral-task", p2
            elif not (j.get("success") and j.get("code") == "OK"):
                return {
                    "tid": tid,
                    "ok": False,
                    "code": j.get("code") or j2.get("code"),
                    "msg": j.get("msg") or j2.get("msg"),
                    "fallback_code": j2.get("code"),
                    "path": path,
                }

        cur = (j.get("data") or {}).get("curTask") or {}
        prize = self.prize(j)
        ok = bool(j.get("success") and j.get("code") == "OK")
        return {
            "tid": tid,
            "ok": ok,
            "code": j.get("code"),
            "msg": j.get("msg"),
            "prize": prize,
            "dayTimes": cur.get("dayTimes"),
            "path": path,
        }


def video_cands(api_tasks: List[Dict[str, Any]]) -> List[Tuple[str, int]]:
    m: Dict[str, int] = {t: p for t, p in VIDEO_TIDS}
    for t in api_tasks:
        tid = str(t.get("id") or "")
        if tid:
            try:
                m[tid] = int(t.get("publishId") or m.get(tid) or 9671)
            except Exception:
                m[tid] = m.get(tid) or 9671
    return list(m.items())






def try_cached_tokens(user: str, rpc: str) -> Optional[Dict[str, Any]]:
    """优先复用本机 live_tokens，但必须匹配当前手机号，禁止串号。"""
    cands = [
        HERE / f"live_tokens_{str(user or '').strip()}.json",
        HERE / "live_tokens.json",
        HERE / "pwd_playwright_result.json",
        HERE / "login_result.json",
    ]
    phone = str(user or "").strip()
    for cand in cands:
        if not cand.is_file():
            continue
        try:
            data = json.loads(cand.read_text(encoding="utf-8-sig"))
        except Exception:
            continue
        auth = data.get("auth") if isinstance(data.get("auth"), dict) else data
        if not isinstance(auth, dict):
            continue
        if not (auth.get("kps") and (auth.get("ut") or auth.get("st"))):
            continue
        u = str(auth.get("user") or auth.get("phone") or data.get("user") or data.get("phone") or "").strip()
        # 严格：有手机号就必须一致；无手机号字段的旧缓存直接丢弃，避免串号
        if phone:
            if not u:
                log(f"跳过无手机号缓存 {cand.name}，避免串号", "警告")
                continue
            if phone not in u and u not in phone:
                log(f"跳过其他账号缓存 {cand.name} user={u[:3]}****", "信息")
                continue
        try:
            client = Client(auth, rpc)
            yb = client.balance()
            tasks = []
            try:
                tasks = client.list_video_tasks() or []
            except Exception:
                tasks = []
            if yb is not None or tasks:
                log(f"复用本地 token 成功 账号={phone[:3]}**** 元宝={yb} 任务数={len(tasks)} 来源={cand.name}", "成功")
                auth = dict(auth)
                auth["user"] = phone
                TOKENS_PATH.write_text(json.dumps(auth, ensure_ascii=False, indent=2), encoding="utf-8")
                per = HERE / f"live_tokens_{phone}.json"
                try:
                    per.write_text(json.dumps(auth, ensure_ascii=False, indent=2), encoding="utf-8")
                except Exception:
                    pass
                return auth
            log(f"本地 token 无效({cand.name}) balance=None tasks=0，尝试下一个", "警告")
        except Exception as e:
            log(f"本地 token 校验失败 {cand.name}: {e}", "警告")
    return None


def run_one_account(account: Any, rpc: str) -> Dict[str, Any]:
    """只使用环境变量里的抓包 token；持续刷；不查余额。"""
    if isinstance(account, dict):
        user = str(account.get("user") or account.get("label") or "acc")
        password = str(account.get("password") or "")
        preset_token = dict(account.get("token") or {})
        label = str(account.get("label") or user)
    elif isinstance(account, (tuple, list)) and len(account) >= 2:
        user, password = str(account[0]), str(account[1])
        preset_token, label = {}, user
    else:
        user, password, preset_token, label = str(account), "", {}, str(account)

    log("=" * 48)
    log(f"账号 {label} 开始")
    log("=" * 48)

    tok: Optional[Dict[str, Any]] = None
    if preset_token.get("kps"):
        tok = dict(preset_token)
        tok.setdefault("user", user)
        tok.setdefault("phone", user)
        if not tok.get("ut"):
            raise RuntimeError(f"账号 {label} 环境变量缺少 ut（UC_ACCOUNTS 需 kps+ut）")
        log(
            f"已从环境变量加载 token kps={str(tok.get('kps'))[:18]}… "
            f"ut=有 设备字段={sum(1 for k in ('ds','mt','de','dn','ni','lb','wf') if tok.get(k))}",
            "成功",
        )
    else:
        # 默认禁止读 live_tokens；仅 UC_ALLOW_TOKEN_FILE=1 时兜底
        allow_file = (os.environ.get("UC_ALLOW_TOKEN_FILE") or "").strip() in ("1", "true", "yes", "Y")
        if allow_file:
            tok = try_cached_tokens(user, rpc)
        if not tok and password:
            log("环境变量无 kps，尝试账密登录（不推荐）", "警告")
            tok = login_by_password(user, password, rpc)
        if not tok:
            raise RuntimeError(
                f"账号 {label} 未从环境变量拿到 token。"
                f"请在 UC_ACCOUNTS 配置: 备注#kps=xxx&ut=xxx&ds=..."
            )

    client = Client(tok, rpc)
    if not client.ut:
        raise RuntimeError("环境变量 token 缺少 ut，无法加签。请在 UC_ACCOUNTS 补 ut=...")

    res: Dict[str, Any] = {
        "user": user,
        "claims": [],
        "time": time.strftime("%Y-%m-%d %H:%M:%S"),
    }
    yb0 = None
    res["balance_before"] = None
    log("开始刷视频（持续模式，不查余额、无轮数）")

    tasks = client.list_video_tasks()
    log(f"视频任务 {len(tasks)} 个")

    # per-task state
    progress: Dict[str, int] = {}   # 仅在有奖时更新（可信）
    target: Dict[str, int] = {}
    full: Set[str] = set()          # 该任务已达自身上限，本轮不再跑
    dead: Set[str] = set()          # 确认不存在
    miss: Dict[str, int] = {}       # TASK_NOT_FOUND 计数
    empty: Dict[str, int] = {}      # 连续无奖计数
    got_prize: Set[str] = set()     # 本运行曾真正领过奖

    for t in tasks:
        tid = str(t.get("id") or "")
        day = t.get("dayTimes") if isinstance(t.get("dayTimes"), dict) else {}
        try:
            dp = int(day.get("progress")) if day.get("progress") is not None else -1
        except Exception:
            dp = -1
        try:
            dt = int(day.get("target")) if day.get("target") is not None else -1
        except Exception:
            dt = -1
        if tid and dt > 0:
            target[tid] = dt
        # 启动：列表 progress>0 且 >=target 才跳过；0/x 不可信
        if tid and dp > 0 and dt > 0 and dp >= dt:
            progress[tid] = dp
            full.add(tid)
            log(f"启动跳过已满任务 tid={tid} {dp}/{dt}", "信息")
        log(f"  {tid} {t.get('name')} 日={day} 奖={t.get('amount')}")

    cands = video_cands(tasks)
    # 只跑还没 full 的
    active = [(tid, pub) for tid, pub in cands if tid not in full and tid not in dead]
    if not active:
        active = list(cands)

    ok_n = prize_sum = 0
    tick = 0
    no_gain_rounds = 0

    while True:
        if STOP_PATH.exists():
            res["stop_reason"] = "停止文件"
            log("检测到停止文件", "信息")
            break

        # 当前可跑列表：每个任务独立判断；优先已有真实进度/已领过奖的 tid
        active = [(tid, pub) for tid, pub in cands if tid not in full and tid not in dead]
        if not active:
            res["stop_reason"] = "各视频任务均已达上限或失效"
            log(f"全部任务完成 full={sorted(full)} dead={sorted(dead)}", "成功")
            break
        def _rank(item):
            tid, _pub = item
            sc = 0
            if tid in got_prize:
                sc += 1000
            if progress.get(tid, 0) > 0:
                sc += 100 + int(progress.get(tid) or 0)
            sc -= int(miss.get(tid, 0)) * 50
            sc -= int(empty.get(tid, 0)) * 5
            return -sc
        active = sorted(active, key=_rank)


        tick += 1
        if tick == 1 or tick % 20 == 0:
            log(f"持续刷 进度点#{tick} 待刷{[t for t,_ in active]}")
        round_prize = 0
        round_ok = 0

        for tid, pub in active:
            if STOP_PATH.exists():
                break
            if tid in full or tid in dead:
                continue

            # 该任务本地已达自身上限 -> 不再跑
            if tid in progress and tid in target and progress[tid] > 0 and progress[tid] >= target[tid]:
                full.add(tid)
                log(f"任务 {tid} 达上限 {progress[tid]}/{target[tid]}，后续不跑", "成功")
                continue

            item = client.claim_video(tid, pub)
            # 服务端有时 OK 但空奖/脏 progress=0：用列表回查真实进度
            if item.get("ok") and not (isinstance(item.get("prize"), int) and item.get("prize") > 0):
                try:
                    for t2 in client.list_video_tasks():
                        if str(t2.get("id")) == str(tid):
                            day2 = t2.get("dayTimes") if isinstance(t2.get("dayTimes"), dict) else {}
                            if day2.get("progress") is not None:
                                item.setdefault("dayTimes", {})
                                if not isinstance(item.get("dayTimes"), dict):
                                    item["dayTimes"] = {}
                                # only overwrite if list progress > 0
                                if int(day2.get("progress") or 0) > 0:
                                    item["dayTimes"]["progress"] = int(day2.get("progress"))
                                    item["dayTimes"]["target"] = int(day2.get("target") or item["dayTimes"].get("target") or 0)
                                    item["_listed"] = True
                            break
                except Exception as _e:
                    log(f"列表回查真实进度失败: {_e}", "警告")
            item["tick"] = tick
            res["claims"].append(item)

            code = str(item.get("code") or "")
            pr = item.get("prize")
            day = item.get("dayTimes") if isinstance(item.get("dayTimes"), dict) else {}
            try:
                dp = int(day["progress"]) if day.get("progress") is not None else None
            except Exception:
                dp = None
            try:
                dt = int(day["target"]) if day.get("target") is not None else target.get(tid)
            except Exception:
                dt = target.get(tid)
            if dt is not None and dt > 0:
                target[tid] = dt

            if item.get("ok"):
                real = isinstance(pr, int) and pr > 0
                if real:
                    # 有奖：完全信任服务端进度（含跨天从0重新计）
                    got_prize.add(tid)
                    empty[tid] = 0
                    miss[tid] = 0
                    ok_n += 1
                    round_ok += 1
                    prize_sum += int(pr)
                    round_prize += int(pr)
                    if dp is not None:
                        progress[tid] = dp
                    log(
                        f"成功 任务{tid} 奖={pr} 进度={progress.get(tid)}/{target.get(tid)} "
                        f"累计奖~{prize_sum}",
                        "成功",
                    )
                    if (
                        tid in progress
                        and tid in target
                        and progress[tid] > 0
                        and progress[tid] >= target[tid]
                    ):
                        full.add(tid)
                        log(f"任务 {tid} 已满 {progress[tid]}/{target[tid]}，停止该任务", "成功")
                else:
                    # 无奖 OK：可能已满，也可能崩溃脏数据
                    empty[tid] = empty.get(tid, 0) + 1
                    # 仅当返回 progress>0 且 >=target 认定该任务满
                    if dp is not None and dt is not None and dp > 0 and dt > 0 and dp >= dt:
                        progress[tid] = dp
                        full.add(tid)
                        log(f"任务 {tid} 无奖且进度已满 {dp}/{dt}，停止该任务", "信息")
                    else:
                        log(
                            f"空响应 任务{tid} 奖=None 返回进度={dp} 本地={progress.get(tid)} "
                            f"连续空={empty[tid]}",
                            "警告",
                        )
                        # 连续多次无奖：查列表确认该任务是否真满，不要靠脏 progress=0
                        if empty[tid] >= 3:
                            try:
                                lst = client.list_video_tasks()
                                hit = None
                                for t in lst:
                                    if str(t.get("id") or "") == tid:
                                        hit = t
                                        break
                                if hit:
                                    d2 = hit.get("dayTimes") if isinstance(hit.get("dayTimes"), dict) else {}
                                    try:
                                        p2 = int(d2.get("progress")) if d2.get("progress") is not None else None
                                        t2 = int(d2.get("target")) if d2.get("target") is not None else None
                                    except Exception:
                                        p2 = t2 = None
                                    if p2 is not None and t2 is not None and p2 > 0 and p2 >= t2:
                                        progress[tid] = p2
                                        target[tid] = t2
                                        full.add(tid)
                                        log(f"列表确认任务 {tid} 已满 {p2}/{t2}，停止", "成功")
                                    else:
                                        log(f"列表确认任务 {tid} 未满 progress={p2}/{t2}，冷却后继续", "信息")
                                        time.sleep(6)
                                        empty[tid] = 0
                                else:
                                    # 列表没有该任务，累计 miss
                                    miss[tid] = miss.get(tid, 0) + 1
                                    if miss[tid] >= 2:
                                        dead.add(tid)
                                        log(f"任务 {tid} 列表不存在，移出", "警告")
                            except Exception as e:
                                log(f"确认任务上限失败: {e}", "警告")
                                time.sleep(5)
                                empty[tid] = 1
            else:
                log(f"失败 任务{tid} code={code} {item.get('msg') or item.get('error')}", "警告")
                if code in ("TASK_DAY_LIMIT", "DAY_LIMIT", "TIMES_LIMIT"):
                    full.add(tid)
                    log(f"任务 {tid} 服务端日限，停止该任务", "成功")
                elif code in ("TASK_NOT_FOUND", "ILLEGAL_TYPE"):
                    miss[tid] = miss.get(tid, 0) + 1
                    if miss[tid] >= 1:
                        dead.add(tid)
                        log(f"任务 {tid} 连续 {code}，移出", "警告")
                    else:
                        time.sleep(2)
                else:
                    # 加签超时等：冷却，不改 full
                    wait_s = min(12, 2 + empty.get(tid, 0) + miss.get(tid, 0))
                    log(f"任务 {tid} 软失败，冷却 {wait_s}s", "警告")
                    time.sleep(wait_s)

            # 每任务间隔，降低 UC 注入频率
            # 空奖退避：连续空响应时拉长间隔，降低风控触发
            _empty_n = int(empty.get(tid, 0) or 0) if "empty" in dir() or True else 0
            try:
                _empty_n = int(empty.get(tid, 0) or 0)
            except Exception:
                _empty_n = 0
            _sleep = CLAIM_INTERVAL
            if _empty_n >= 2:
                _sleep = max(_sleep, 12.0)
            if _empty_n >= 3:
                _sleep = max(_sleep, 30.0)
            if _empty_n >= 5:
                _sleep = max(_sleep, 60.0)
            if _empty_n >= 8:
                _sleep = max(_sleep, 120.0)
            if _empty_n >= 12:
                _sleep = max(_sleep, 180.0)
            if _empty_n >= 3:
                log(f"任务{tid} 连续空奖{_empty_n}次，冷却 {_sleep:.0f}s（疑似风控/严格完成窗口）", "警告")
            time.sleep(_sleep)

        alive = [t for t, _ in cands if t not in full and t not in dead]
        log(
            f"批次完成: 本批奖+{round_prize} 成功{round_ok} "
            f"待刷{alive} 已满{sorted(full)} 失效{sorted(dead)}"
        )

        if not alive:
            res["stop_reason"] = "各视频任务均已达上限或失效"
            log("无待刷任务，结束", "成功")
            break

        if round_prize <= 0 and round_ok <= 0:
            no_gain_rounds += 1
        else:
            no_gain_rounds = 0

        # 仅当长时间完全无收益才停；不因脏数据停
        if no_gain_rounds >= 200:
            res["stop_reason"] = "长时间无收益"
            log("长时间无收益，结束", "警告")
            break

        # 轮间休息，给 UC 喘口气
        time.sleep(2.0)
    yb1 = None
    res.update(
        {
            "balance_after": None,
            "delta": None,
            "ok_count": ok_n,
            "prize_sum": prize_sum,
            "rounds": tick,
            "full": sorted(full),
            "dead": sorted(dead),
            "progress": progress,
            "target": target,
            "ended": time.strftime("%Y-%m-%d %H:%M:%S"),
        }
    )
    log(
        f"账号结束: 元宝 {yb0}→{yb1} 变化{res['delta']} 有效成功{ok_n} 累计奖~{prize_sum} "
        f"已满任务{sorted(full)} {res.get('stop_reason')}",
        "成功",
    )
    return res



def ensure_ql_env() -> None:
    """Qinglong may not inject envs into python; load from preload/db fallback."""
    if (os.environ.get("UC_ACCOUNTS") or "").strip():
        return

    def _apply_from_env_py(path: Path) -> bool:
        try:
            code = path.read_text(encoding="utf-8", errors="ignore")
            g = {"os": os}
            exec(compile(code, str(path), "exec"), g, g)
            return bool((os.environ.get("UC_ACCOUNTS") or "").strip())
        except Exception as e:
            log(f"load {path} failed: {e}", "警告")
            return False

    def _apply_from_env_sh(path: Path) -> bool:
        try:
            for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
                s = line.strip()
                if not s.startswith("export "):
                    continue
                body = s[7:]
                if "=" not in body:
                    continue
                k, v = body.split("=", 1)
                k = k.strip()
                v = v.strip()
                if len(v) >= 2 and v[0] == v[-1] and v[0] in "\"'":
                    v = v[1:-1]
                if k:
                    os.environ.setdefault(k, v)
            return bool((os.environ.get("UC_ACCOUNTS") or "").strip())
        except Exception as e:
            log(f"load {path} failed: {e}", "警告")
            return False

    for py in [
        Path("/ql/shell/preload/env.py"),
        Path(os.environ.get("QL_DIR", "/ql")) / "shell" / "preload" / "env.py",
    ]:
        if py.is_file() and _apply_from_env_py(py):
            log("已从 env.py 兜底加载 UC_ACCOUNTS", "信息")
            return

    for sh in [
        Path("/ql/shell/preload/env.sh"),
        Path(os.environ.get("QL_DIR", "/ql")) / "shell" / "preload" / "env.sh",
    ]:
        if sh.is_file() and _apply_from_env_sh(sh):
            log("已从 env.sh 兜底加载 UC_ACCOUNTS", "信息")
            return

    db = Path("/ql/data/db/database.sqlite")
    if db.is_file():
        try:
            import sqlite3
            con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
            for name in ("UC_ACCOUNTS", "UC_SIGN_RPC"):
                row = con.execute(
                    "SELECT value FROM Envs WHERE name=? AND status=0 ORDER BY id DESC LIMIT 1",
                    (name,),
                ).fetchone()
                if row and row[0] and not (os.environ.get(name) or "").strip():
                    os.environ[name] = str(row[0])
            con.close()
            if (os.environ.get("UC_ACCOUNTS") or "").strip():
                log("已从 database.sqlite 兜底加载 UC_ACCOUNTS", "信息")
                return
        except Exception as e:
            log(f"sqlite fallback failed: {e}", "警告")


def main() -> int:
    log("UC极速版 · 青龙单变量 · 无限刷视频（不领宝箱）")
    ensure_ql_env()
    raw = (os.environ.get("UC_ACCOUNTS") or "").strip()
    # 兼容误写成 UC_USER#UC_PASS 两个变量时的拼接提示
    if not raw:
        u = (os.environ.get("UC_USER") or os.environ.get("UC_PHONE") or "").strip()
        p = (os.environ.get("UC_PASS") or "").strip()
        if u and p:
            raw = f"{u}#{p}"
            log("未设 UC_ACCOUNTS，已兼容 UC_USER+UC_PASS", "警告")
        else:
            log("请配置环境变量 UC_ACCOUNTS（备注#kps=..&ut=.. 换行多账号）", "错误")
            log("多账号: 号1#密1&号2#密2", "信息")
            return 2

    accounts = parse_accounts(raw)
    if not accounts:
        log("UC_ACCOUNTS 解析为空", "错误")
        return 2

    rpc = (os.environ.get("UC_SIGN_RPC") or "").strip() or SIGN_RPC_DEFAULT
    if not (os.environ.get("UC_SIGN_RPC") or "").strip():
        log(f"未设 UC_SIGN_RPC，使用默认 {rpc}", "警告")
    if not SignRPC(rpc).ok():
        log(f"SignRPC 不可用: {rpc}", "错误")
        log("请在跑模拟器的机器上: 打开 UC极速版 → python uc_mumu_sign_rpc.py", "错误")
        log("青龙在 Docker 时把 UC_SIGN_RPC 设为宿主机 IP:17890（可选第二变量）", "信息")
        return 2
    log(f"SignRPC 正常 {rpc}", "成功")
    log(f"共 {len(accounts)} 个账号", "信息")
    for a in accounts:
        if not (a.get("token") or {}).get("kps"):
            log(f"账号 {a.get('label')} 未解析到 kps，请检查 UC_ACCOUNTS 格式", "错误")
            return 2
        if not (a.get("token") or {}).get("ut"):
            log(f"账号 {a.get('label')} 未解析到 ut，请检查 UC_ACCOUNTS 格式", "错误")
            return 2

    log("UC极速刷视频 · token + 加签机", "信息")

    if STOP_PATH.exists():
        try:
            STOP_PATH.unlink()
        except Exception:
            pass

    all_res: Dict[str, Any] = {
        "time": time.strftime("%Y-%m-%d %H:%M:%S"),
        "accounts": [],
    }
    for acc in accounts:
        try:
            one = run_one_account(acc, rpc)
            all_res["accounts"].append(one)
        except Exception as e:
            lab = acc.get("label") if isinstance(acc, dict) else str(acc)
            log(f"账号 {lab} 失败: {e}", "错误")
            all_res["accounts"].append({"user": lab, "error": str(e)})

    RESULT_PATH.write_text(json.dumps(all_res, ensure_ascii=False, indent=2), encoding="utf-8")
    log(f"全部完成 → {RESULT_PATH.name}")

    lines = []
    for a in all_res["accounts"]:
        if a.get("error"):
            lines.append(f"{a.get('user','?')}: 失败 {a['error']}")
        else:
            lines.append(f"{a.get('user','?')}: 成功{a.get('ok_count')} 累计奖~{a.get('prize_sum')} {a.get('stop_reason') or ''}")
    notify("UC刷视频", "\n".join(lines) or "无结果")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        log("中断", "警告")
        raise SystemExit(130)
