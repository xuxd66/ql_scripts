# -*- coding: utf-8 -*-
"""
=========================================
  UC极速版 · 自动刷视频赚元宝(单文件版)
  配套:signhook-module(Xposed 模块,内嵌进 UC APK)
=========================================

环境变量:

1) UC_ACCOUNTS   填 token(多账号换行)
   格式: 备注#kps=xxx&ut=xxx&ds=xxx&mt=xxx&de=xxx&dn=xxx&ni=xxx&lb=xxx&wf=xxx&ch=xxx&ve=xxx&sn=xxx&mi=xxx&bd=xxx
   最少: 备注#kps=xxx&ut=xxx

2) UC_SIGN_RPC   填签名 RPC 地址(由 signhook-module 提供)
   - 模拟器: 默认 http://127.0.0.1:17890 (配合 adb forward tcp:17890 tcp:17890)
   - 真机局域网: http://手机IP:17890

从环境变量读 token,持续刷视频到各任务日上限。
停止: 创建 STOP_VIDEO_FARM.txt 或任务全满/失效。
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
CLAIM_INTERVAL = 7.0

VIDEO_TIDS: List[Tuple[str, int]] = [
    ("1789725", 9671),
    ("39823", 9671),
    ("1795864", 9671),
    ("1795863", 9655),
    ("1792321", 9671),
    ("1795844", 9671),
    ("1794063", 9806),
]

UA = (
    "Mozilla/5.0 (Linux; U; Android 16; zh-CN; V2426A Build/BQ2A.250705.001) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/100.0.4896.58 "
    "UCBrowser/18.9.4.1458 Mobile Safari/537.36"
)

TOKEN_KEYS = (
    "kps", "ut", "st", "uid", "ds", "mt", "de", "dn", "ni", "lb", "wf",
    "ch", "ve", "sn", "mi", "bd", "fr", "pr", "nn", "pc", "od", "oc",
)


def log(msg: str, level: str = "信息") -> None:
    print(f"[{time.strftime('%H:%M:%S')}][{level}] {msg}", flush=True)


def notify(title: str, content: str) -> None:
    try:
        from notify import send  # type: ignore
        send(title, content)
    except Exception:
        pass


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
                    out[str(k)] = str(v)
                return out
        except Exception:
            pass
    sep = "&" if "&" in blob else (";" if ";" in blob else "\n")
    for part in blob.split(sep):
        part = part.strip()
        if not part or "=" not in part:
            continue
        k, v = part.split("=", 1)
        k = k.strip()
        if k:
            out[k] = v.strip()
    return out


def parse_accounts(raw: str) -> List[Dict[str, Any]]:
    """解析 UC_ACCOUNTS 环境变量。格式: 备注#kps=..&ut=.. (换行多账号)"""
    accounts: List[Dict[str, Any]] = []
    for line in (raw or "").splitlines():
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        if "#" not in s:
            log(f"账号行缺少 # 分隔符: {s[:40]}…", "警告")
            continue
        label, _, token_str = s.partition("#")
        label = label.strip()
        token_str = token_str.strip()
        kv = _parse_kv_blob(token_str)
        tok: Dict[str, Any] = {}
        for k in TOKEN_KEYS:
            v = kv.get(k)
            if v:
                tok[k] = v
        if not tok.get("kps"):
            for alt in ("X-U-KPS-WG", "X_U_KPS_WG", "KPS"):
                if kv.get(alt):
                    tok["kps"] = kv[alt]
                    break
        user = label or f"acc{len(accounts)+1}"
        if not tok.get("kps"):
            log(f"账号行缺少 kps: {line[:40]}…", "警告")
            continue
        if not tok.get("ut"):
            log(f"账号行缺少 ut: {label}", "警告")
        accounts.append({
            "label": label or user,
            "user": user,
            "token": tok,
        })
    return accounts


# ---------------------------------------------------------------------------
# SignRPC 客户端 — 对接 signhook-module 的 HTTP server
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
            time.sleep(12 + i * 10)
        raise RuntimeError(f"加签失败: {last}")


# ---------------------------------------------------------------------------
# UC API 客户端
# ---------------------------------------------------------------------------
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

    def list_video_tasks(self) -> List[Dict[str, Any]]:
        q = self.qbase()
        q.update({
            "__t": str(int(time.time() * 1000)),
            "entry": "toolbar",
            "evSub": "uclite_fuli_index",
            "codes": "uc_piggy_task_nest,uc_piggy_limit_time,uc_piggy_xssvideo_fuli",
            "requestId": str(uuid.uuid4()),
            "fve": FVE,
            "activeUser": "1",
            "prioritySize": "1",
        })
        r = self.s.get(
            f"{HOST_CORAL2}/uclite/queryByMultiResource",
            params=q, headers=self.headers(), timeout=25,
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
                    out.append({
                        "id": str(t.get("id")),
                        "name": t.get("name"),
                        "dayTimes": t.get("dayTimes"),
                        "publishId": t.get("publishId") or 9671,
                        "amount": (ri[0] or {}).get("amount"),
                    })
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

    def claim_video(self, tid: str, publish_id: int) -> Dict[str, Any]:
        """优先 coral2 POST /uclite/trigger,再回退 coral-task GET。"""
        def _do_coral2(rid: str, sign: str) -> Dict[str, Any]:
            body = {
                "kps": self.kps, "appId": APP_ID_H5, "moduleCode": MODULE_TASK,
                "useUtCompleteTask": False, "publishId": int(publish_id),
                "fve": FVE, "tid": int(tid), "type": "complete", "value": 1,
                "requestId": rid, "sign": sign, "salt": FARM_SALT,
            }
            r = self.s.post(
                f"{HOST_CORAL2}/uclite/trigger",
                params=self.qbase(), json=body, headers=self.headers(), timeout=30,
            )
            try:
                return r.json()
            except Exception:
                return {"raw": r.text[:200]}

        def _do_coral_task(rid: str, sign: str) -> Dict[str, Any]:
            params = {
                "appId": APP_ID_TASK, "moduleCode": MODULE_TASK,
                "value": "1", "type": "complete", "kps": self.kps,
                "requestId": rid, "salt": FARM_SALT, "sign": sign,
                "tid": str(tid), "_ch": "native",
                "uc_param_str": "utpcsnnnvebipfdnprfrcgch",
                "ve": self.tok.get("ve") or "18.9.4.1458",
                "fr": "android", "ut": self.ut, "entry": "toolbar",
                "from": "", "pr": "UCLite", "ch": self.tok.get("ch") or "",
            }
            r = self.s.get(
                f"{HOST_CORAL_TASK}/task/trigger",
                params=params, headers={"User-Agent": UA, "X-U-KPS-WG": self.kps},
                timeout=30,
            )
            try:
                return r.json()
            except Exception:
                return {"raw": r.text[:200]}

        rid = str(uuid.uuid4())
        try:
            sign = self.farm_sign(tid, rid)
        except Exception as e:
            return {"tid": tid, "ok": False, "error": f"加签失败: {e}"}
        j = _do_coral2(rid, sign)
        path = "coral2"
        prz = self.prize(j if isinstance(j, dict) else {})
        good = bool(j.get("success") and j.get("code") == "OK" and isinstance(prz, int) and prz > 0)

        if not good:
            rid2 = str(uuid.uuid4())
            try:
                sign2 = self.farm_sign(tid, rid2)
            except Exception as e:
                if j.get("success") and j.get("code") == "OK":
                    cur = (j.get("data") or {}).get("curTask") or {}
                    return {"tid": tid, "ok": True, "code": j.get("code"),
                            "msg": j.get("msg"), "prize": prz,
                            "dayTimes": cur.get("dayTimes"), "path": path}
                return {"tid": tid, "ok": False, "code": j.get("code"),
                        "msg": j.get("msg"), "error": f"回退加签失败: {e}"}
            j2 = _do_coral_task(rid2, sign2)
            p2 = self.prize(j2 if isinstance(j2, dict) else {})
            if j2.get("success") and j2.get("code") == "OK" and isinstance(p2, int) and p2 > 0:
                j, path, prz = j2, "coral-task", p2
            elif (not (j.get("success") and j.get("code") == "OK")) and j2.get("success") and j2.get("code") == "OK":
                j, path, prz = j2, "coral-task", p2
            elif not (j.get("success") and j.get("code") == "OK"):
                return {"tid": tid, "ok": False, "code": j.get("code") or j2.get("code"),
                        "msg": j.get("msg") or j2.get("msg"),
                        "fallback_code": j2.get("code"), "path": path}

        cur = (j.get("data") or {}).get("curTask") or {}
        prize = self.prize(j)
        ok = bool(j.get("success") and j.get("code") == "OK")
        return {"tid": tid, "ok": ok, "code": j.get("code"), "msg": j.get("msg"),
                "prize": prize, "dayTimes": cur.get("dayTimes"), "path": path}


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


# ---------------------------------------------------------------------------
# 单账号刷视频主循环
# ---------------------------------------------------------------------------
def run_one_account(account: Any, rpc: str) -> Dict[str, Any]:
    if isinstance(account, dict):
        user = str(account.get("user") or account.get("label") or "acc")
        preset_token = dict(account.get("token") or {})
        label = str(account.get("label") or user)
    else:
        user, preset_token, label = str(account), {}, str(account)

    log("=" * 48)
    log(f"账号 {label} 开始")
    log("=" * 48)

    if not preset_token.get("kps"):
        raise RuntimeError(
            f"账号 {label} 环境变量缺少 kps。请在 UC_ACCOUNTS 配置: 备注#kps=xxx&ut=xxx&ds=..."
        )
    tok = dict(preset_token)
    tok.setdefault("user", user)
    if not tok.get("ut"):
        raise RuntimeError(f"账号 {label} 环境变量缺少 ut(UC_ACCOUNTS 需 kps+ut)")

    log(
        f"已从环境变量加载 token kps={str(tok.get('kps'))[:18]}… "
        f"ut=有 设备字段={sum(1 for k in ('ds','mt','de','dn','ni','lb','wf') if tok.get(k))}",
        "成功",
    )

    client = Client(tok, rpc)
    if not client.ut:
        raise RuntimeError("token 缺少 ut,无法加签。请在 UC_ACCOUNTS 补 ut=...")

    res: Dict[str, Any] = {
        "user": user, "claims": [], "time": time.strftime("%Y-%m-%d %H:%M:%S"),
        "balance_before": None,
    }
    log("开始刷视频(持续模式,不查余额、无轮数)")

    tasks = client.list_video_tasks()
    log(f"视频任务 {len(tasks)} 个")

    progress: Dict[str, int] = {}
    target: Dict[str, int] = {}
    full: Set[str] = set()
    dead: Set[str] = set()
    miss: Dict[str, int] = {}
    empty: Dict[str, int] = {}
    got_prize: Set[str] = set()

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
        if tid and dp > 0 and dt > 0 and dp >= dt:
            progress[tid] = dp
            full.add(tid)
            log(f"启动跳过已满任务 tid={tid} {dp}/{dt}", "信息")
        log(f"  {tid} {t.get('name')} 日={day} 奖={t.get('amount')}")

    cands = video_cands(tasks)
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
            if tid in progress and tid in target and progress[tid] > 0 and progress[tid] >= target[tid]:
                full.add(tid)
                log(f"任务 {tid} 达上限 {progress[tid]}/{target[tid]},后续不跑", "成功")
                continue

            item = client.claim_video(tid, pub)
            if item.get("ok") and not (isinstance(item.get("prize"), int) and item.get("prize") > 0):
                try:
                    for t2 in client.list_video_tasks():
                        if str(t2.get("id")) == str(tid):
                            day2 = t2.get("dayTimes") if isinstance(t2.get("dayTimes"), dict) else {}
                            if day2.get("progress") is not None:
                                item.setdefault("dayTimes", {})
                                if not isinstance(item.get("dayTimes"), dict):
                                    item["dayTimes"] = {}
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
                    got_prize.add(tid)
                    empty[tid] = 0
                    miss[tid] = 0
                    ok_n += 1
                    round_ok += 1
                    prize_sum += int(pr)
                    round_prize += int(pr)
                    if dp is not None:
                        progress[tid] = dp
                    log(f"成功 任务{tid} 奖={pr} 进度={progress.get(tid)}/{target.get(tid)} 累计奖~{prize_sum}", "成功")
                    if tid in progress and tid in target and progress[tid] > 0 and progress[tid] >= target[tid]:
                        full.add(tid)
                        log(f"任务 {tid} 已满 {progress[tid]}/{target[tid]},停止该任务", "成功")
                else:
                    empty[tid] = empty.get(tid, 0) + 1
                    if dp is not None and dt is not None and dp > 0 and dt > 0 and dp >= dt:
                        progress[tid] = dp
                        full.add(tid)
                        log(f"任务 {tid} 无奖且进度已满 {dp}/{dt},停止该任务", "信息")
                    else:
                        log(f"空响应 任务{tid} 奖=None 返回进度={dp} 本地={progress.get(tid)} 连续空={empty[tid]}", "警告")
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
                                        log(f"列表确认任务 {tid} 已满 {p2}/{t2},停止", "成功")
                                    else:
                                        log(f"列表确认任务 {tid} 未满 progress={p2}/{t2},冷却后继续", "信息")
                                        time.sleep(6)
                                        empty[tid] = 0
                                else:
                                    miss[tid] = miss.get(tid, 0) + 1
                                    if miss[tid] >= 2:
                                        dead.add(tid)
                                        log(f"任务 {tid} 列表不存在,移出", "警告")
                            except Exception as e:
                                log(f"确认任务上限失败: {e}", "警告")
                                time.sleep(5)
                                empty[tid] = 1
            else:
                log(f"失败 任务{tid} code={code} {item.get('msg') or item.get('error')}", "警告")
                if code in ("TASK_DAY_LIMIT", "DAY_LIMIT", "TIMES_LIMIT"):
                    full.add(tid)
                    log(f"任务 {tid} 服务端日限,停止该任务", "成功")
                elif code in ("TASK_NOT_FOUND", "ILLEGAL_TYPE"):
                    miss[tid] = miss.get(tid, 0) + 1
                    if miss[tid] >= 1:
                        dead.add(tid)
                        log(f"任务 {tid} 连续 {code},移出", "警告")
                    else:
                        time.sleep(2)
                else:
                    wait_s = min(12, 2 + empty.get(tid, 0) + miss.get(tid, 0))
                    log(f"任务 {tid} 软失败,冷却 {wait_s}s", "警告")
                    time.sleep(wait_s)

            # 空奖退避:连续空响应时拉长间隔,降低风控触发
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
                log(f"任务{tid} 连续空奖{_empty_n}次,冷却 {_sleep:.0f}s(疑似风控/严格完成窗口)", "警告")
            time.sleep(_sleep)

        alive = [t for t, _ in cands if t not in full and t not in dead]
        log(f"批次完成: 本批奖+{round_prize} 成功{round_ok} 待刷{alive} 已满{sorted(full)} 失效{sorted(dead)}")

        if not alive:
            res["stop_reason"] = "各视频任务均已达上限或失效"
            log("无待刷任务,结束", "成功")
            break

        if round_prize <= 0 and round_ok <= 0:
            no_gain_rounds += 1
        else:
            no_gain_rounds = 0
        if no_gain_rounds >= 200:
            res["stop_reason"] = "长时间无收益"
            log("长时间无收益,结束", "警告")
            break

        time.sleep(2.0)

    res.update({
        "balance_after": None, "delta": None,
        "ok_count": ok_n, "prize_sum": prize_sum, "rounds": tick,
        "full": sorted(full), "dead": sorted(dead),
        "progress": progress, "target": target,
        "ended": time.strftime("%Y-%m-%d %H:%M:%S"),
    })
    log(
        f"账号结束: 有效成功{ok_n} 累计奖~{prize_sum} "
        f"已满任务{sorted(full)} {res.get('stop_reason')}",
        "成功",
    )
    return res


# ---------------------------------------------------------------------------
# 青龙环境兜底
# ---------------------------------------------------------------------------
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
    log("UC极速版 · 单文件版 · 无限刷视频")
    ensure_ql_env()
    raw = (os.environ.get("UC_ACCOUNTS") or "").strip()
    if not raw:
        log("请配置环境变量 UC_ACCOUNTS(备注#kps=..&ut=.. 换行多账号)", "错误")
        return 2

    accounts = parse_accounts(raw)
    if not accounts:
        log("UC_ACCOUNTS 解析为空", "错误")
        return 2

    rpc = (os.environ.get("UC_SIGN_RPC") or "").strip() or SIGN_RPC_DEFAULT
    if not (os.environ.get("UC_SIGN_RPC") or "").strip():
        log(f"未设 UC_SIGN_RPC,使用默认 {rpc}", "警告")
    if not SignRPC(rpc).ok():
        log(f"SignRPC 不可用: {rpc}", "错误")
        log("请确认 UC APK 已用 LSPatch 集成 signhook 模块,且 UC 已启动", "错误")
        log("模拟器: adb forward tcp:17890 tcp:17890", "信息")
        log("真机: UC_SIGN_RPC=http://手机局域网IP:17890", "信息")
        return 2
    log(f"SignRPC 正常 {rpc}", "成功")
    log(f"共 {len(accounts)} 个账号", "信息")
    for a in accounts:
        if not (a.get("token") or {}).get("kps"):
            log(f"账号 {a.get('label')} 未解析到 kps,请检查 UC_ACCOUNTS 格式", "错误")
            return 2
        if not (a.get("token") or {}).get("ut"):
            log(f"账号 {a.get('label')} 未解析到 ut,请检查 UC_ACCOUNTS 格式", "错误")
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
