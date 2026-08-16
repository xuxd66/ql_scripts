/**
先走个邀请链接:http://b6i.cn/2D5Ygp
得6个月会员
 * KuGou H5 签到（多账户版） - 青龙平台兼容 (基于 Cookie + 其他 ENV)
 * * ⚠️ 注意: 
 * 1. 脚本假设青龙环境支持 'axios' 和 'crypto-js' 模块。如果不支持，需要手动安装: 
 * npm install axios crypto-js
 * 2. 账号数据通过以下**多个环境变量**获取：
 * - KUGOU_COOKIE: 酷狗的 Cookie 字符串，多账号用 @ 或 & 分隔。
 * - KUGOU_QUERY_PARAMS: 签到请求中 URL 的查询参数 (query string) 部分，例如 appid=...&clientver=...&mid=...
 * * **************************************************/

const axios = require('axios');
const CryptoJS = require('crypto-js');
// 导入 Node.js 内置的 URL 模块
const { URLSearchParams } = require('url');

const COOKIE_KEY_ENV = 'KUGOU_COOKIE'; // Cookie 环境变量名
const QUERY_KEY_ENV = 'KUGOU_QUERY_PARAMS'; // 必需的查询参数环境变量名
const LOG_PREFIX = '酷狗音乐概念版签到 (青龙版)';
const H5_SECRET = 'NVPh5oo715z5DIWAeQlhMDsWXXQV4hwt'; 

// --- UTILS for QingLong Environment ---

function log(...a){ console.log(...a); }

function notify(title, sub, msg){ 
  log(`\n\n=== ${title} ===`);
  if (sub) log(`--- ${sub} ---`);
  if (msg) log(msg);
  log('=================\n');
}

/**
 * 构造查询字符串
 */
function buildQS(obj){
  const sp = new URLSearchParams();
  Object.keys(obj||{}).forEach(k=> sp.append(k, obj[k]));
  return sp.toString();
}

/**
 * 环境变量中读取 Cookie 并拆分，同时读取必需的 Query Params
 */
function readStore(){
  const cookieStr = process.env[COOKIE_KEY_ENV] || '';
  const queryStr = process.env[QUERY_KEY_ENV] || '';

  if (!cookieStr || !queryStr) {
    log(`${LOG_PREFIX}: ⚠️ 缺少必需的环境变量。请设置 ${COOKIE_KEY_ENV} 和 ${QUERY_KEY_ENV}。`);
    return [];
  }

  // 拆分多账号 Cookie (支持 @ 和 & 分隔)
  const cookies = cookieStr.split(/[@&]\s*/).filter(c => c.trim() !== '');

  // 解析基础查询参数
  const baseQuery = {};
  new URLSearchParams(queryStr).forEach((v, k) => { baseQuery[k] = v; });

  const records = [];

  // 检查必需字段是否在 baseQuery 中
  const must = ['appid', 'clientver', 'mid', 'uuid', 'dfid', 'token', 'userid'];
  const missingInBase = must.filter(k => !baseQuery[k]);

  if (missingInBase.length > 0) {
      log(`❌ 致命错误：KUGOU_QUERY_PARAMS 缺少以下关键参数：${missingInBase.join(', ')}。请检查您的 Query 参数是否完整。`);
      return [];
  }

  // 使用 Set 确保只处理不重复的 userid
  const processedUserIds = new Set();

  for (const cookie of cookies) {
    // 从 baseQuery 继承所有必需参数
    const rec = {
        // 直接使用 baseQuery 中的 userid
        userid: String(baseQuery.userid), 
        query: { ...baseQuery },
        // 构造 headers
        headers: { 'Cookie': cookie }
    };

    // 优化：跳过重复的 userid
    if (processedUserIds.has(rec.userid)) {
        continue;
    }

    // 标记为已处理
    processedUserIds.add(rec.userid);
    records.push(rec);
  }

  return records;
}

/**
 * 封装 axios 请求
 */
async function fetchRemote(options){
  try {
    const response = await axios({
      url: options.url,
      method: options.method || 'GET',
      headers: options.headers,
      timeout: options.timeout || 10000,
      data: options.method === 'POST' ? options.data : undefined,
    });
    // 兼容原脚本返回格式 { response: resp, body }
    return { 
      response: { status: response.status, headers: response.headers }, 
      body: JSON.stringify(response.data) // axios data 是解析后的对象，这里转回字符串模拟 body 
    };
  } catch (err) {
    // 兼容原脚本抛出错误
    throw new Error(err.message || 'Network request failed');
  }
}

// 签名 (直接使用导入的 CryptoJS)
async function calcSignature(queryObj){
  // 检查 CryptoJS 是否加载成功
  if (!CryptoJS || typeof CryptoJS.MD5 !== 'function') {
      throw new Error('CryptoJS 模块未加载或不支持MD5');
  }

  const p = { ...(queryObj||{}) };
  if (!('source_id' in p)) p.source_id = '';
  if ('signature' in p) delete p.signature;
  const useAppKey = !!p.appkey;
  const secret = useAppKey ? String(p.appkey) : H5_SECRET;
  if (useAppKey) delete p.srcappid; 
  const keys = Object.keys(p).sort();
  const joined = keys.map(k => `${k}=${p[k] == null ? '' : String(p[k])}`).join('');
  const raw = secret + joined + secret;

  return CryptoJS.MD5(raw).toString();
}

// --- SIGN IN LOGIC ---

function sanitizeHeadersForScript(headers){
  const out = {};
  Object.keys(headers||{}).forEach(k=>{
    if (!k.startsWith(':') && !k.toLowerCase().includes('content-length')) {
      out[k]=headers[k];
    }
  });
  return out;
}

async function signOne(rec){
  const base = 'https://gateway.kugou.com';
  const path = '/youth/v1/recharge/receive_vip_listen_song';
  const q = { ...(rec.query||{}) };
  q.clienttime = String(Date.now());
  if (!('source_id' in q)) q.source_id = '';

  const useAppKey = !!q.appkey;
  if (useAppKey) delete q.srcappid;

  let signature;
  try {
     signature = await calcSignature(q);
  } catch (error) {
     return { ok: false, code: -1, msg: error.message };
  }

  q.signature = signature;
  const url = `${base}${path}?${buildQS(q)}`; // buildQS 在这里被调用
  const headers = sanitizeHeadersForScript(rec.headers || {});
  const options = { url, method: 'POST', headers };

  let body;
  try {
     const res = await fetchRemote(options);
     body = res.body;
  } catch (error) {
     return { ok: false, code: -2, msg: `网络请求失败: ${error.message}` };
  }

  let ret = {};
  try{ ret = JSON.parse(body || '{}'); }catch{}

  // 响应
  if (ret && Number(ret.status) === 1 && Number(ret.error_code) === 0) {
    return { ok: true, code: 0, msg: '签到成功' };
  }
  if (ret && Number(ret.status) === 0 && Number(ret.error_code) === 131001) {
    return { ok: true, code: 131001, msg: '已签到（今日）' };
  }
  if (ret && Number(ret.error_code) === 20006) {
    return { ok: false, code: 20006, msg: '签名错误(err signature)' , raw: ret };
  }
  return { ok: false, code: ret && ret.error_code, msg: ret && ret.error_msg || '未知返回', raw: ret };
}

async function runSignin(){
  const list = readStore();
  if (!list.length){
    // notify 在 readStore 内部已调用
    return;
  }

  // 检查依赖
  if (!CryptoJS || typeof CryptoJS.MD5 !== 'function'){ 
    notify(LOG_PREFIX, '初始化失败', '❌ CryptoJS 模块未找到或不支持MD5，请检查是否安装: npm install crypto-js'); 
    return; 
  }

  const lines = [];
  let ok = 0, fail = 0;

  for (const rec of list){
    try{
      const r = await signOne(rec);
      if (r.ok){ ok++; lines.push(`✅ ${rec.userid}: ${r.msg}`); }
      else { fail++; lines.push(`❌ ${rec.userid}: ${r.msg}`); }
    }catch(e){
      fail++; lines.push(`❌ ${rec.userid}: ${String(e)}`);
    }
  }

  notify(LOG_PREFIX, `执行完毕 | 成功 ${ok}，失败 ${fail}`, lines.join('\n'));
}

(async () => {
  try{
     await runSignin();
  }catch(e){
    notify(LOG_PREFIX, '执行异常', String(e));
  }
})();

