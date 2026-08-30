/*
 * 知了快看脚本
 * 环境变量：zy
 * 格式：uid@oaid@androidId@deviceId@zqkey@zqkey_id@app_device_id@sm_device_id@union_id
 *
 * 例：
 * zy=uid@oaid@androidId@deviceId@zqkey@zqkey_id@app_device_id@sm_device_id@union_id
 *
 * 需要真实 SDK 产生的新 media_extra：
 * ZY_MEDIA_EXTRA='{"media_app_id":"...",...}'
 *
 * 默认只执行一次，避免重复提交：ZY_LOOP=1 才持续执行。
 * ZY_DRY_RUN=1 只构造请求，不访问服务器。
 */
'use strict';

const https = require('https');
const crypto = require('crypto');
const zlib = require('zlib');
const { spawnSync } = require('child_process');

const HOST = 'lemon-api.52leho.com';
const APP_NAME = 'new_liao_view';
const APP_PKG = 'new.liao.view';
const APP_VERSION = process.env.ZY_APP_VERSION || '1.7.3';
const VERSION_CODE = process.env.ZY_VERSION_CODE || '43';
const INNER_VERSION = process.env.ZY_INNER_VERSION || '202608071042';
const CHANNEL = process.env.ZY_CHANNEL || 'M1031';

const DEVICE_BRAND = process.env.ZY_DEVICE_BRAND || 'Redmi';
const DEVICE_MODEL = process.env.ZY_DEVICE_MODEL || '25102RKBEC';
const OS_VERSION = process.env.ZY_OS_VERSION || 'BP2A.250605.031.A3';
const OS_API = process.env.ZY_OS_API || '36';
const RESOLUTION = process.env.ZY_RESOLUTION || '1200x2416';
const CARRIER = process.env.ZY_CARRIER || '中国移动';
const STORAGE = process.env.ZY_STORAGE || '229.87';
const MEMORY = process.env.ZY_MEMORY || '10';
const NETWORK_TYPE = process.env.ZY_NETWORK_TYPE || 'UNKNOWN';
const DEVICE_PLATFORM = 'android';
const ACCESS = process.env.ZY_ACCESS || 'wlan';
const VERSION2_KEY = 'jdvylqchJZrfw0o2DgAbsmCGUapF1YChc';
const VERSION6_KEY = 'zWpfzystJLrfw7o3SgGlMmGGPupK2YLhB';
const SIGN_FRAGMENT = '-DMUWDwjdUAJLwaHPWZF2GsrixncrL9S8VQI';
const LOOP = process.env.ZY_LOOP === '1';
const DRY_RUN = process.env.ZY_DRY_RUN === '1';
const DELAY_MIN = numberEnv('ZY_DELAY_MIN', 30000, 1000, 3600000);
const DELAY_MAX = numberEnv('ZY_DELAY_MAX', 45000, DELAY_MIN, 3600000);
let stopping = false;

function numberEnv(name, fallback, min, max) {
  const raw = process.env[name];
  if (raw === undefined || raw === '') return fallback;
  const n = Number(raw);
  if (!Number.isFinite(n) || n < min || n > max) {
    throw new Error(`${name} 必须在 ${min}~${max} 范围内`);
  }
  return n;
}

function parseAccounts() {
  const raw = process.env.zy || '';
  if (!raw.trim()) throw new Error('未配置 zy，格式：uid@oaid@androidId@deviceId@zqkey@zqkey_id@app_device_id@sm_device_id@union_id');
  return raw.split(/\r?\n/).map(x => x.trim()).filter(Boolean).map((row, index) => {
    const a = row.split('@');
    if (a.length < 9 || a.slice(0, 9).some(x => !x)) {
      throw new Error(`zy 第${index + 1}行格式错误，需要 uid@oaid@androidId@deviceId@zqkey@zqkey_id@app_device_id@sm_device_id@union_id`);
    }
    return { uid: a[0], oaid: a[1], androidid: a[2], deviceId: a[3], zqkey: a[4], zqkey_id: a[5], appDeviceId: a[6], smDeviceId: a[7], unionId: a[8] };
  });
}

function enc(v) { return encodeURIComponent(String(v)); }
function md5(v) { return crypto.createHash('md5').update(v).digest('hex'); }
function randChar() { return '0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'[crypto.randomInt(62)]; }
function randDelay() { return Math.floor(DELAY_MIN + Math.random() * (DELAY_MAX - DELAY_MIN + 1)); }
function sleep(ms) { return new Promise(resolve => setTimeout(resolve, ms)); }
function sortedKeys(obj) { return Object.keys(obj).filter(k => obj[k] !== undefined && obj[k] !== '').sort(); }

// App's URL form serializer: values are URL encoded, key order is insertion order.
function formText(obj, sorted = false) {
  const keys = sorted ? sortedKeys(obj) : Object.keys(obj).filter(k => obj[k] !== undefined && obj[k] !== '');
  return keys.map(k => `${k}=${enc(obj[k])}`).join('&');
}

// p is an inner signed copy. The app sorts the source fields, then URL-encodes twice.
function makeP(base) {
  const keys = sortedKeys(base);
  const raw = keys.map(k => `${k}=${base[k]}`).join('');
  const signed = {};
  keys.forEach(k => { signed[k] = base[k]; });
  signed.sign = raw + VERSION2_KEY;
  return wrapDes(formText(signed));
}

function wrapDes(plain) {
  const c = randChar();
  const trim = SIGN_FRAGMENT.slice(0, SIGN_FRAGMENT.length - (c.charCodeAt(0) % 10));
  const key = Buffer.from(trim.slice(0, 8), 'ascii');
  const digest8 = crypto.createHash('md5').update(trim).digest().subarray(0, 8);
  const ivText = digest8.toString('base64url') + '=';
  const iv = Buffer.from(ivText.slice(0, 8), 'ascii');
  const pad = 8 - (Buffer.byteLength(plain) % 8);
  const padded = Buffer.concat([Buffer.from(plain), Buffer.alloc(pad, pad)]);
  const cipher = desCbc(key, iv, padded, false);
  return c + ivText + cipher.toString('base64url');
}

function desCbc(key, iv, data, decrypt) {
  // Node 17+ disables single-DES in OpenSSL's default provider. Use the
  // legacy provider through stdin so no plaintext is put on argv/process list.
  const args = ['enc', '-des-cbc', '-provider', 'legacy', '-K', key.toString('hex'), '-iv', iv.toString('hex'), '-nopad'];
  if (decrypt) args.push('-d');
  const r = spawnSync('openssl', args, { input: data, maxBuffer: 1024 * 1024 });
  if (r.error || r.status !== 0) throw new Error(`DES 加密组件不可用：${(r.stderr || r.error || '').toString().trim()}`);
  return r.stdout;
}

function baseParams(a, extra) {
  const now = process.env.ZY_REQUEST_TIME || Math.floor(Date.now() / 1000).toString();
  return {
    access: ACCESS, account: a.uid, androidid: a.androidid,
    'app-version': APP_VERSION, app_device_id: a.appDeviceId,
    app_name: APP_NAME, app_pkg: APP_PKG, app_version: APP_VERSION,
    carrier: CARRIER, channel: CHANNEL, dev_mode: '0',
    device_brand: DEVICE_BRAND, device_id: a.deviceId,
    device_model: DEVICE_MODEL, device_platform: DEVICE_PLATFORM,
    device_type: 'android', dpi: '3.0', inner_version: INNER_VERSION,
    is_debug: '0', language: 'zh-CN', memory: MEMORY, mi: '1',
    mobile_type: '1', network_type: NETWORK_TYPE, oaid: a.oaid,
    openudid: a.androidid, os_api: OS_API, os_version: OS_VERSION,
    request_time: now, resolution: RESOLUTION, rom_version: OS_VERSION,
    sim: '1', sm_device_id: a.smDeviceId, storage: STORAGE, uid: a.uid,
 union_id: a.unionId, user_cert: '0', version_code: VERSION_CODE,
    zqkey: a.zqkey, zqkey_id: a.zqkey_id,
    s_ad: wrapDes(a.androidid),
    ...extra
  };
}

function makeSignedBase(a, extra) {
  const base = baseParams(a, extra);
  const keys = sortedKeys(base);
  const raw = keys.map(k => `${k}=${base[k]}`).join('');
  return { ...base, sign: md5(raw + VERSION2_KEY) };
}

function makeRewardBody(a) {
  const media = process.env.ZY_MEDIA_EXTRA;
  if (!media) throw new Error('缺少 ZY_MEDIA_EXTRA；必须填入真实 SDK 新产生的 media_extra，禁止重放旧抓包');
  let mediaObj;
  try { mediaObj = JSON.parse(media); } catch { throw new Error('ZY_MEDIA_EXTRA 不是合法 JSON'); }
  const base = baseParams(a, {
    action: process.env.ZY_ACTION || 'read_withdraw', index: '0', video_id: '0',
    media_extra: JSON.stringify(mediaObj)
  });
  const inner = makeP(base);
  return formText({ zqkd_param: wrapDes(formText({ ...base, p: inner }, true)) });
}

function makeTaskBody(a, type) {
  const base = makeSignedBase(a, { type: String(type) });
  return formText(base);
}

function makeUserQuery(a) {
  const base = makeSignedBase(a, { phone_sim: '1' });
  return formText(base);
}

function request(method, path, body, query) {
  return new Promise((resolve, reject) => {
    const target = query ? `${path}?${query}` : path;
    const req = https.request({ hostname: HOST, method, path: target, headers: {
      'device-platform': 'android', 'app-pkg': APP_PKG, 'User-Agent': 'android',
      'Content-Type': 'application/x-www-form-urlencoded',
      ...(body !== null ? { 'Content-Length': Buffer.byteLength(body) } : {})
    }, timeout: 20000 }, res => {
      const chunks = [];
      res.on('data', x => chunks.push(x));
      res.on('end', () => {
        const text = Buffer.concat(chunks).toString('utf8').trim();
        try { resolve({ status: res.statusCode, text, json: decryptResponse(text) }); }
        catch (e) { reject(new Error(`响应解密失败：${e.message}`)); }
      });
    });
    req.on('timeout', () => req.destroy(new Error('请求超时')));
    req.on('error', reject);
    if (body !== null) req.write(body);
    req.end();
  });
}

function decryptResponse(text) {
  const raw = Buffer.from(text, 'base64');
  const c = crypto.createDecipheriv('aes-128-ecb', Buffer.from(SIGN_FRAGMENT.slice(0, 16), 'ascii'), null);
  const out = Buffer.concat([c.update(raw), c.final()]);
  return JSON.parse(out.toString('utf8'));
}

function assertSuccess(r, label) {
  if (!r || r.status !== 200) throw new Error(`${label} HTTP ${r && r.status}`);
  if (!r.json || r.json.success !== true) throw new Error(`${label}：${r.json && r.json.message || '业务失败'}`);
  return r.json;
}

function logReward(json) {
  const item = json && json.items || {};
  if (item.score === undefined || item.score === null) throw new Error('响应没有 items.score，不能判定奖励');
  console.log(`恭喜获得${item.score}积分`);
  if (item.total_score !== undefined) console.log(`当前累计积分：${item.total_score}`);
  if (item.red_packet !== undefined && Number(item.red_packet) > 0) console.log(`红包奖励：${item.red_packet}`);
}

async function runAccount(a, index) {
  console.log(`知了快看启动（账号${index + 1}）`);

  do {
    const rewardBody = makeRewardBody(a);
    if (DRY_RUN) {
      console.log(`DRY_RUN：已构造 toGetReward 请求，body=${Buffer.byteLength(rewardBody)}字节`);
      return;
    }
    const reward = assertSuccess(await request('POST', '/v5/CommonReward/toGetReward.json', rewardBody), '奖励接口');
    logReward(reward);
    if (!LOOP) return;
    await sleep(randDelay());
  } while (!stopping);
}

async function main() {
  const accounts = parseAccounts();
  await Promise.all(accounts.map(runAccount));
}

process.on('SIGINT', () => { stopping = true; });
process.on('SIGTERM', () => { stopping = true; });
if (require.main === module) {
  main().catch(e => { console.error(`失败：${e.message}`); process.exitCode = 1; });
}

module.exports = { formText, makeP, makeSignedBase, makeRewardBody, wrapDes, decryptResponse };
