/*
中国联通 v1.32 + 自动提取Token整合版

包含以下功能:
1. 首页签到 (话费红包/积分)
2. 联通祝福 (各类抽奖)
3. 天天领现金 (每日打卡/立减金)
4. 权益超市 (任务/抽奖/浇水/领奖/全局库存缓存)
5. 安全管家 (日常任务/积分领取)
6. 联通云盘 (签到/抽奖/AI互动)
7. 联通阅读 (新版重构: 自动获取书籍/心跳阅读/8051抽奖/查红包)
8. 沃云手机 (新: 签到/任务/抽奖)
9. 区域专区 (新: 自动识别新疆/河南执行特有任务)
10. 联通爱听 (新: 积分任务/自动签到/阅读挂机/分享任务)


更新说明:

### 20260127
v1.32:
- ⚔️ **话费抢兑 (并发版)**：重构为全并发模式。所有账号同时启动、独立提IP、同时请求。(⚠️注意：此模式仅供开发调试，普通用户请勿开启，否则将跳过日常任务及查询模式)。
- ♻️ **代理机制更新**：新增**智能故障转移**，优先验活旧代理，仅在完全失效时更换新IP，最大化节省资源并确保任务连续性。
- 📝 **明细查询 & 日志优化**：新增 `sign_query_my_prizes` 接口精准查询；**美化抢兑失败日志**，不再输出原始JSON，直接显示中文错误提示 (如: 库存不足/火爆)。

### 20260126
v1.31:
- 🚀 智能查询模式：定点时间(7/20点)全量跑任务；补跑时间(9/15点)仅跑爱听；**其他时间自动进入“仅查询模式”**。只查资产(话费/积分/奖品)，不执行耗时任务，手动运行无负担。
- 🔧 **环境变量控制**：新增 `CHINA_UNICOM_FORCE_TASK` 变量。设置为 `true` 可在非定点时间强制运行全量任务，打破查询模式限制。
- 💰 **查询增强 (Pro)**：新增 **套餐余量查询** (即时查询当月话费余额、实时话费详情)，新增 **话费抢购记录统计** (统计本月在权益超市获得的红包总额)，资产状态更透明。
- ☁️ 云盘优化：适配活动下架情况。保留AI对话互动(积分收益)；**自动屏蔽已失效的抽奖环节**(不查次数/不抽奖)，彻底解决报错飘红问题。
- 🔍 记录增强：新增权益超市抽奖记录、云盘中奖记录查询；补全河南商都签到状态查询。
- 🛡️ 修复与调整：修复“安全管家”任务静默退出问题；云盘积分逻辑回退至旧版(已赚/可用双指标)，数据更完整。

### 20260125
v1.30:
- 🛒 权益超市接口优化：更新请求参数，将 `xbsosjl=xbsosjltrue` 改为 `xbsosjl=xbsosjlsujif&timeVerRan=时间戳`，适配接口变更。

### 20260122
v1.29:
- 🚀 爱听调度优化：支持 **9点/15点** 智能补跑。在此时间段运行脚本，将自动识别并仅执行爱听任务，避开冲突。
- 🔄 逻辑调整：调整爱听专区执行顺序，优先执行签到，再执行积分任务，确保状态同步。
- 🌍 区域优化：新疆/河南专区逻辑微调，提升识别准确率。

### 20260121
v1.28:
- 🆕 新增任务：移植“沃云手机”板块，包含积分签到、任务列表刷新、领取机会及抽奖逻辑。
- 🎵 爱听专区：新增“联通爱听”板块，完美移植Py脚本逻辑，支持积分签到、阅读挂机(自动时长)、分享任务自动完成。
- 🌍 区域特供：新增“区域专区”任务，登录后自动根据归属地判断，执行新疆（每日打卡/客户日秒杀）或河南商都（签到）任务。
- ⚡ 效率提升：权益超市引入“全局库存缓存”机制。首个账号查询若无高价值库存，后续账号将自动跳过查询与抽奖，显著提升多账号运行速度并减少无效请求。
- 🛡️ 安全优化：针对账号密码登录模式，新增动态 `AppId` 生成算法，避免因使用固定 ID 导致的指纹风控。

### 20251231
v1.26:
- 🗑️ 移除失效功能：删除了已下线的“抢50话费券”模块及相关抢购逻辑，精简代码体积。
- ⚡ 流程优化：移除了启动时的“统一预登录”步骤，改为纯串行模式（轮到账号时才获取IP -> 登录 -> 执行），最大化节省代理IP资源，防止因预登录等待导致IP过期。
- 🛡️ 回归日常：脚本现在专注于日常任务（签到、云盘、阅读等），运行更加稳定高效。

### 20251230
v1.25:
- 🔄 抢购策略优化：针对“抢50话费券”模块，移除遇到 `0108` (库存不足) 立即停止的逻辑。
- 🛡️ 捡漏机制：现在即使接口返回无库存，脚本也会坚持跑完循环，应对服务器缓存延迟或短时回流，增加捡漏成功率。
- 📉 频率调整：将单次抢购的最大循环次数从 200 下调至 100 次，在保证抢购强度的同时减少无效请求，降低黑号风险。

配置说明:
1. 账号变量 (chinaUnicomCookie):
   赋值方式有三种:
   a. 填账号密码 (自动获取Token - 推荐):
      export chinaUnicomCookie="18600000000#123456"
   b. 填Token#AppId (免密模式 - 推荐):
      export chinaUnicomCookie="a3e4c1ff2xxxxxxxxx#912d30xxxxxx"
   c. 仅填Token (旧模式):
      export chinaUnicomCookie="a3e4c1ff2xxxxxxxxx"
   (多账号用 & 或 换行 隔开)

2. 代理设置 (可选):
   export UNICOM_PROXY_API="你的品赞JSON提取链接" (⚠️ 必须含 &format=json)
   export UNICOM_PROXY_TYPE="http" (可选 http 或 socks5，默认 http)

3. 青龙应用设置 (可选 - 用于账号密码登录后自动回写Token):
   通常青龙面板会自动注入 Client ID/Secret，无需额外配置。
   若脚本提示“无法获取青龙权限”，请手动设置：
   export QL_CLIENT_ID="你的应用ID"
   export QL_CLIENT_SECRET="你的应用密钥"
   (需在青龙面板 -> 系统设置 -> 应用设置 中新建应用，并给予“环境变量”的读写权限)

4. 特殊功能设置:
   export CHINA_UNICOM_FORCE_TASK="true"  : (可选) 非定点时间强制执行全量任务，忽略查询模式限制。
   export chinaUnicomAiting="false"       : (可选) 禁用爱听任务。设置后，9/15点补跑改为查询模式，7/20点全量任务也跳过爱听。
   export UNICOM_GRAB_MODE="true"         : (⚠️仅供开发调试) 开启话费券抢兑模式 (并发执行，普通用户请勿开启)
   export UNICOM_GRAB_AMOUNT="5"          : (可选) 抢兑面额 (默认5，自动匹配含"5元"或"5话费"的奖品)
   export UNICOM_GRAB_URL="https://..."   : (可选) 自定义抢兑接口地址

⚠️ 依赖安装:
在青龙面板 -> 依赖管理 -> NodeJs 中添加安装:
hpagent
socks-proxy-agent
crypto-js
got
tough-cookie

定时规则建议 (Cron):
0 58 9,17 * * * (新增：话费券抢兑，建议提前2分钟启动，脚本会自动精准等待)
0 7,9,15,20 * * * (推荐：7点/20点跑全套，9点/15点自动跑爱听补救)
其他时间手动运行：自动进入 [仅查询模式]，查资产不跑任务。

const $ = new Env("中国联通");
From：yaohuo28507 (yaohuo8648二改)
*/
const fs = require('fs');
// const { HttpsProxyAgent } = require('hpagent');
const { HttpsProxyAgent, HttpProxyAgent } = require('hpagent');
const { SocksProxyAgent } = require('socks-proxy-agent'); // 新增 Socks5 支持
const crypto = require("crypto"); // 新增：用于账号密码登录的RSA加密
let got;
const appName = createLogger("中国联通"),
  path = require("path"),
  {
    exec: execCommand
  } = require("child_process"),
  cryptoJS = require("crypto-js"),
  {
    CookieJar: cookieJar
  } = require("tough-cookie"),
  chinaUnicom = "chinaUnicom",
  delimiters = ["\n", "&", "@"],
  cookieVars = [chinaUnicom + "Cookie"]; // End of first let block

// 全局代理缓存 (用于普通模式下的IP复用)
let globalSharedProxy = null;

let signDisabled = process.env[chinaUnicom + "Sign"] === "false",
  ltzfDisabled = process.env[chinaUnicom + "Ltzf"] === "false",
  aitingDisabled = process.env[chinaUnicom + "Aiting"] === "false",
  requestTimeout = 10000,
  retryCount = 3,
  projectName = "chinaUnicom",
  retryDelay = 5,
  appVersion = "android@11.0802",
  userAgent = "Dalvik/2.1.0 (Linux; U; Android 10; MI 8 MIUI/20.8.13);unicom{version:android@11.0802}",
  productId = "10000002",
  secretKey = "7k1HcDL8RKvc",
  defaultPassword = "woreadst^&*12345",
  secondProductId = "10000006",
  secondSecretKey = "yQsp9gUqv7qX",
  someConstant = "QzUzOUM2QTQ2MTc4",
  ivString = "16-Bytes--String",
  errorCode = "225",
  errorNumber = "225",
  partyName = "party",
  apiKey = "6-WfVldfFrt3zhjHhe6kzwI-XfG5aMCzRTLI_4K7_a0",
  clientId = "73b138fd-250c-4126-94e2-48cbcc8b9cbe",
  anotherClientId = "7cb46449-3b11-4414-bb49-cbd15525fb88",
  maxRetries = "9",
  minRetries = "1",
  serviceLife = "wocareMBHServiceLife1",
  anotherApiKey = "beea1c7edf7c4989b2d3621c4255132f",
  anotherEncryptionKey = "f4cd4ffeb5554586acf65ba7110534f5",
  numbers = "0123456789",
  letters = "qwertyuiopasdfghjklzxcvbnm",
  uuid = process.env[chinaUnicom + "Uuid"] || appName.randomUuid(),
  someArray = [9, 10, 11, 12, 13],
  delayMs = 1000,
  timeoutMs = 5000,
  client_Id = "1001000003",
  ProductId2 = "100002",
  emptyString = "";

// 已清理旧变量
const maskStr = (str) => {
  try {
    let s = String(str);
    if (s.length === 11) {
      return s.replace(/(\d{3})\d{4}(\d{4})/, '$1****$2');
    }
    return s;
  } catch (e) {
    return str;
  }
};

// ==================== 0. 全局配置常量 (新增) ====================
// 抢兑接口默认 URL (基于 SigninApp/new_convert/prizeList 推断)
// 用户可根据实际抓包结果修改
const UNICOM_GRAB_URL = process.env.UNICOM_GRAB_URL || "https://act.10010.com/SigninApp/convert/prizeConvert";

// Token 缓存文件路径 (同目录下)
const UNICOM_TOKEN_CACHE_PATH = path.join(__dirname, "unicom_token_cache.json");

// 抢兑模式开关 (环境变量控制 或 智能时间判定 9:58/17:58)
// 能够识别 9:58/9:59 和 17:58/17:59 自动进入抢兑模式，无需手动切换变量
const _now = new Date();
const _isGrabTime = (_now.getHours() === 9 || _now.getHours() === 17) && _now.getMinutes() >= 58;
const IS_GRAB_MODE = process.env.UNICOM_GRAB_MODE === "true" || _isGrabTime;
const GRAB_AMOUNT = process.env.UNICOM_GRAB_AMOUNT || "5"; // 默认抢5元
// ===============================================================
const expiration_time = 7,
  appMonth_28_MaxTimes = 5,
  maxDrawTimes = 5;
const activityIds = {
  ttlxj: "TTLXJ20210330",
  card_618: "NZJK618CJHD"
};
const constellationMatchingActivity = {
  name: "星座配对",
  id: 2
};
const turntableActivity = {
  name: "大转盘",
  id: 3
};
const blindBoxActivity = {
  name: "盲盒抽奖",
  id: 4
};
const wocareActivities = [constellationMatchingActivity, turntableActivity, blindBoxActivity];
const card618PrizeMap = {
  ZFGJBXXCY1: "空气",
  GJBNZJK19: "[6]",
  GJBNZJK20: "[1]",
  GJBNZJK21: "[8]",
  GJBNZJK22: "[狂]",
  GJBNZJK23: "[欢]"
};
const card618DrawTypeSuffix = {
  "抽奖": "01",
  "首次进入": "02",
  "卡片合成": "03",
  "瓜分奖励": "04"
};

// RSA 公钥，用于密码登录
const LOGIN_PUB_KEY = `-----BEGIN PUBLIC KEY-----\n${"MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQDc+CZK9bBA9IU+gZUOc6FUGu7yO9WpTNB0PzmgFBh96Mg1WrovD1oqZ+eIF4LjvxKXGOdI79JRdve9NPhQo07+uqGQgE4imwNnRx7PFtCRryiIEcUoavuNtuRVoBAm6qdB0SrctgaqGfLgKvZHOnwTjyNqjBUxzMeQlEC2czEMSwIDAQAB".match(/.{1,64}/g).join('\n')}\n-----END PUBLIC KEY-----`;
// ==================== 爱听专区常量 (新增) ====================
const AITING_BASE_URL = "https://pcc.woread.com.cn";
const AITING_SIGN_KEY_APPKEY = "7ZxQ9rT3wE5sB2dF";
const AITING_SIGN_KEY_API = "woread!@#qwe1234";
const AITING_SIGN_KEY_REQUERTID = "46iCw24ewAZbNkK6";
const AITING_CLIENT_KEY = "1";
const AITING_AES_KEY = "j2K81755sxV12wFx";
const AITING_AES_IV = "16-Bytes--String";
const WOREAD_KEY = "woreadst^&*12345";
const ADDREADTIME_AES_KEY = "UNS#READDAY39COM";
// ==========================================================

function UencryptWithCryptoJS(algorithm, mode, padding, plaintext, key, iv) {
  return cryptoJS[algorithm].encrypt(
    cryptoJS.enc.Utf8.parse(plaintext),
    cryptoJS.enc.Utf8.parse(key),
    {
      mode: cryptoJS.mode[mode],
      padding: cryptoJS.pad[padding],
      iv: cryptoJS.enc.Utf8.parse(iv)
    }
  ).ciphertext.toString(cryptoJS.enc.Hex);
}

function decrypt(cipherMethod, mode, padding, ciphertextHex, key, iv) {
  return cryptoJS[cipherMethod].decrypt({
    ciphertext: cryptoJS.enc.Hex.parse(ciphertextHex)
  }, cryptoJS.enc.Utf8.parse(key), {
    mode: cryptoJS.mode[mode],
    padding: cryptoJS.pad[padding],
    iv: cryptoJS.enc.Utf8.parse(iv)
  }).toString(cryptoJS.enc.Utf8);
}

let processCount = 0;
// ==================== 全局状态变量 (新增) ====================
// 用于权益超市，所有账号共享检测结果，防止重复请求空库存
let globalMarketPoolChecked = false;
let globalMarketHasPrizes = false;
// ==========================================================
let processState = 0;

/**
 * Initializes process monitoring and sets up termination handling.
 */
function initializeProcessMonitoring() {
  processState = 1;
  process.on("SIGTERM", () => {
    processState = 2;
    process.exit(0);
  });

  const scriptName = path.basename(process.argv[1]);
  const excludedCommands = ["bash", "timeout", "grep"];
  let commandList = ["ps afx"];
  commandList.push(`grep ${scriptName}`);
  commandList = commandList.concat(excludedCommands.map(cmd => `grep -v "${cmd} "`));
  commandList.push("wc -l");

  const commandString = commandList.join("|");

  const checkProcessCount = () => {
    execCommand(commandString, (error, stdout, stderr) => {
      if (error || stderr) {
        return;
      }
      processCount = parseInt(stdout.trim(), 10);
    });

    if (processState === 1) {
      setTimeout(checkProcessCount, 2000);
    }
  };

  checkProcessCount();
}

/**
 * Class for managing user services with HTTP request handling and logging.
 */
class UserService {
  constructor() {
    this.index = ++appName.userIdx;
    this.name = "";
    this.valid = false;
    this.notifyLogs = [];

    const retryOptions = {
      limit: 0
    };
    const defaultHeaders = {
      Connection: "keep-alive"
    };
    const httpClientOptions = {
      retry: retryOptions,
      timeout: { request: requestTimeout },
      followRedirect: false,
      headers: defaultHeaders
    };

    this.got = got.extend(httpClientOptions);

    if (processState === 0) {
      initializeProcessMonitoring();
    }
  }

  /**
   * Logs messages with an optional prefix based on user index and name.
   * @param {string} message - The log message.
   * @param {object} options - Additional logging options.
   */
  log(message, options = {}) {
    let logPrefix = "";
    const userCountLength = appName.userCount.toString().length;

    if (this.index) {
      logPrefix += `账号[${appName.padStr(this.index, userCountLength)}]`;
    }
    // 新增一个参数来控制是否显示手机号
    if (this.name && !options.hideName) {
      logPrefix += `[${maskStr(this.name)}]`; // 使用 maskStr 包裹 this.name
    }

    appName.log(logPrefix + message, options);
    // 如果需要通知，将日志添加到用户自己的通知数组中
    if (options.notify) {
      this.notifyLogs.push(logPrefix + message);
    }
  }

  /**
   * Sets a cookie in the cookie jar.
   * @param {string} name - The name of the cookie.
   * @param {string} value - The value of the cookie.
   * @param {string} domain - The domain for the cookie.
   * @param {string} url - The URL for the cookie.
   * @param {object} options - Additional options.
   */
  set_cookie(name, value, domain, url, options = {}) {
    this.cookieJar.setCookieSync(`${name}=${value}; Domain=${domain};`, url);
  }

  /**
   * Makes an HTTP request with retry logic.
   * @param {object} requestOptions - The options for the HTTP request.
   * @returns {Promise<object>} - The result of the HTTP request.
   */
  async request(requestOptions) {
    const networkErrors = ["ECONNRESET", "EADDRINUSE", "ENOTFOUND", "EAI_AGAIN"];
    const timeoutErrors = ["TimeoutError"];
    const protocolErrors = ["EPROTO"];
    const validCodes = [];

    let response = null;
    let attemptCount = 0;
    const requestName = requestOptions.fn || requestOptions.url;

    let validCode = appName.get(requestOptions, "valid_code", validCodes);
    requestOptions.method = requestOptions.method?.toUpperCase() || "GET";

    while (attemptCount < retryCount) {
      try {
        attemptCount++;
        let errorCode = "";
        let errorName = "";
        let error = null;
        // [v12+] 直接从对象中获取 request 超时时间
        const timeout = requestOptions.timeout?.request || this.got.defaults.options.timeout.request || requestTimeout;
        let timeoutOccurred = false;

        await new Promise((resolve) => {
          setTimeout(() => {
            timeoutOccurred = true;
            resolve();
          }, timeout);
          // [v12+] 移除不被支持的自定义属性 (fn, valid_code)
          // 兼容性处理: 如果传入 params, 自动转换为 searchParams
          if (requestOptions.params) {
            requestOptions.searchParams = requestOptions.params;
            delete requestOptions.params;
          }
          const { fn, valid_code, params, ...gotOptions } = requestOptions;

          this.got(gotOptions).then(
            (res) => {
              response = res;
            },
            (err) => {
              error = err;
              response = err.response;
              errorCode = error?.code || "";
              errorName = error?.name || "";
            }
          ).finally(() => resolve());
        });

        if (timeoutOccurred) {
          this.log(`[${requestName}] 请求超时(${timeout / 1000}秒)，重试第${attemptCount}次`);
          if (!IS_GRAB_MODE && typeof this.set_proxy_ip === 'function') { await this.failover_proxy(); }

        } else if (protocolErrors.includes(errorCode)) {
          this.log(`[${requestName}] 请求错误[${errorCode}][${errorName}]`);
          if (error?.message) {
            console.log(error.message);
          }
          break;
        } else if (timeoutErrors.includes(errorName)) {
          this.log(`[${requestName}] 请求错误[${errorCode}][${errorName}]，重试第${attemptCount}次`);
          if (!IS_GRAB_MODE && typeof this.set_proxy_ip === 'function') { await this.failover_proxy(); }

        } else if (networkErrors.includes(errorCode)) {
          this.log(`[${requestName}] 请求错误[${errorCode}][${errorName}]，重试第${attemptCount}次`);
          if (!IS_GRAB_MODE && typeof this.set_proxy_ip === 'function') { await this.failover_proxy(); }

        } else {
          const statusCode = response?.statusCode || "";
          const statusCategory = Math.floor(statusCode / 100);

          if (statusCode) {
            if (statusCategory > 3 && !validCode.includes(statusCode)) {
              this.log(`请求[${requestName}] 返回[${statusCode}]`);
            }
            if (statusCategory <= 4) {
              break;
            }
          } else {
            this.log(`请求[${requestName}] 错误[${errorCode}][${errorName}]: ${error?.message}`);
          }
        }
      } catch (err) {
        if (err.name === "TimeoutError") {
          this.log(`[${requestName}] 请求超时，重试第${attemptCount}次`);
        } else {
          this.log(`[${requestName}] 请求错误(${err.message})，重试第${attemptCount}次`);
        }
        if (!IS_GRAB_MODE && typeof this.set_proxy_ip === 'function') { await this.failover_proxy(); }
      }
    }

    if (response == null) {
      return Promise.resolve({
        statusCode: errorCode || -1,
        headers: null,
        result: null
      });
    }

    let { statusCode, headers, body } = response;
    if (body) {
      try {
        body = JSON.parse(body);
      } catch { }
    }

    const result = {
      statusCode,
      headers,
      result: body
    };

    return Promise.resolve(result);
  }
}

let UserServiceClass = UserService;
try {
  let LocalBasicService = require("./LocalBasic");
  UserServiceClass = LocalBasicService;
} catch { }
// let userServiceInstance = new UserServiceClass(appName);
class CustomUserService extends UserServiceClass {
  constructor(tokenString) {
    super(appName);
    this.cookieString = "";
    this.uuid = process.env[chinaUnicom + "Uuid"] || appName.randomUuid();

    // 初始化登录信息变量
    this.account_mobile = "";
    this.account_password = "";
    this.token_online = "";
    this.appId = ""; // 新增 appId 变量

    // 自动判断是 Token 还是 账号#密码
    // Token 通常较长，账号密码相对较短。这里简单通过 # 判断
    if (tokenString.includes("#") && tokenString.length < 64 && !tokenString.startsWith("a3")) {
      const parts = tokenString.split("#");
      this.account_mobile = parts[0];
      this.account_password = parts[1];
      this.name = this.account_mobile; // 初始显示手机号
      this.log(`识别到账号密码模式，准备自动提取Token: ${maskStr(this.account_mobile)}`);
    } else {
      let deftokenParts = tokenString.split("#");
      this.token_online = deftokenParts[0].trim(); // 加上 trim() 去除可能的首尾空格
      // 【新增】如果存在#appid，则提取并存储
      if (deftokenParts.length > 1 && deftokenParts[1]) {
        this.appId = deftokenParts[1].trim(); // 加上 trim()
        this.log(`识别到 Token#AppId 模式，使用自定义AppId: ${this.appId}`);
      }
    }

    const defaultHeaders = {
      "User-Agent": userAgent
    };
    this.got = this.got.extend({
      headers: defaultHeaders,
      hooks: {
        beforeRequest: [
          (options) => {
            if (this.cookieString) {
              options.headers.cookie = this.cookieString;
            }
          },
        ],
        afterResponse: [
          (response) => {
            const newCookies = response.headers["set-cookie"];
            if (newCookies && Array.isArray(newCookies)) {
              let cookieObj = {};
              if (this.cookieString) {
                this.cookieString.split(";").forEach((pair) => {
                  const parts = pair.split("=");
                  if (parts.length >= 2)
                    cookieObj[parts[0].trim()] = parts.slice(1).join("=").trim();
                });
              }
              newCookies.forEach((str) => {
                const pair = str.split(";")[0];
                const parts = pair.split("=");
                if (parts.length >= 2) {
                  const key = parts[0].trim();
                  const value = parts.slice(1).join("=").trim();
                  cookieObj[key] = value;
                }
              });
              this.cookieString = Object.entries(cookieObj)
                .map(([k, v]) => `${k}=${v}`)
                .join("; ");
            }
            return response;
          },
        ],
      },
    });

    this.unicomTokenId = appName.randomString(32);
    this.tokenId_cookie = "chinaunicom-" + appName.randomString(32, numbers + letters).toUpperCase();
    this.rptId = "";
    this.city = [];
    this.t_flmf_task = 0;
    this.t_woread_draw = 0;
    // 尽管新版阅读已移除这些逻辑，但保留变量初始化以防调用旧代码报错
    this.need_read_rabbit = false;
    this.moonbox_task_record = {};

    this.initialTelephoneAmount = null;
    this.notifyLogs = []; // 为每个用户实例添加独立的通知日志数组
    this.moonbox_notified = [];

    // for security butler
    this.sec_ticket1 = "";
    this.sec_token = "";
    this.sec_ticket = "";
    this.sec_jeaId = "";
    this.sec_oldJFPoints = null;

    this.ttxc_token = "";
    this.ttxc_userId = "";

    // for new woread logic
    this.wr_catid = null;
    this.wr_cardid = null;
    this.wr_cntindex = null;
    this.wr_chapterallindex = null;
    this.wr_chapterid = null;

    this.cookieString = `TOKENID_COOKIE=${this.tokenId_cookie}; UNICOM_TOKENID=${this.unicomTokenId}; sdkuuid=${this.unicomTokenId}`;
  }
  // ==================== 1. Token 缓存读写 (新增) ====================
  // 读取本地缓存 Token
  loadTokenFromCache() {
    try {
      if (!this.account_mobile) return false; // [修复] 必须有手机号才能读缓存
      if (!fs.existsSync(UNICOM_TOKEN_CACHE_PATH)) return false;
      const data = fs.readFileSync(UNICOM_TOKEN_CACHE_PATH, 'utf8');
      const cache = JSON.parse(data);
      // 根据账号(手机号)查找
      const userCache = cache[this.account_mobile];

      if (userCache && userCache.token_online) {
        // 简单校验有效期 (例如 12小时)
        const now = Date.now();
        if (now - userCache.timestamp < 12 * 60 * 60 * 1000) {
          this.token_online = userCache.token_online;
          this.appId = userCache.appId || this.appId;
          this.cookieString = userCache.cookieString || this.cookieString;
          // 复用 cookieJar 需要反序列化 (tough-cookie比较复杂, 这里主要复用关键字符串)
          // 这里的策略是：复用 token_online 最重要
          this.log(`♻️ [缓存复用] 成功加载本地 Token (${userCache.time})`);
          return true;
        }
      }
    } catch (e) {
      // console.log("读取缓存失败", e.message);
    }
    return false;
  }

  // 保存 Token 到本地缓存
  saveTokenToCache() {
    try {
      if (!this.account_mobile) return; // [修复] 必须有手机号才能存缓存

      let cache = {};
      if (fs.existsSync(UNICOM_TOKEN_CACHE_PATH)) {
        try {
          cache = JSON.parse(fs.readFileSync(UNICOM_TOKEN_CACHE_PATH, 'utf8'));
        } catch { }
      }

      const now = Date.now();
      cache[this.account_mobile] = {
        token_online: this.token_online,
        appId: this.appId,
        cookieString: this.cookieString,
        timestamp: now,
        time: appName.time('yyyy-MM-dd hh:mm:ss', now)
      };

      fs.writeFileSync(UNICOM_TOKEN_CACHE_PATH, JSON.stringify(cache, null, 2));
      this.log(`💾 [缓存保存] Token 已写入本地文件`);
    } catch (e) {
      this.log(`❌ 保存缓存失败: ${e.message}`);
    }
  }

  // ==================== 2. 抢兑核心逻辑 (新增) ====================
  async sign_grabCoupon() {
    this.log(`⚔️ [抢兑阶段] 正在检查目标: ${GRAB_AMOUNT}元 话费券...`);

    // 1. 获取奖品列表及其 ID (动态查找)
    let candidates = []; // [新增] 收集所有符合条件的场次

    try {
      const listConfig = {
        fn: "sign_grab_list",
        method: "post",
        url: "https://act.10010.com/SigninApp/new_convert/prizeList",
        headers: { "Origin": "https://img.client.10010.com" }
      };
      let { result: listRes } = await this.request(listConfig);

      if (listRes && listRes.status === "0000") {
        const details = listRes.data?.datails || {};
        const tabItems = details.tabItems || [];

        this.log(`📋 [调试] 共获取到 ${tabItems.length} 个场次数据`);

        for (const tab of tabItems) {
          const products = tab.timeLimitQuanListData || [];
          let roundTimeStr = tab.time || "";  // 例如 "10:00"

          // 尝试解析场次时间
          let roundDate = null;
          if (roundTimeStr) {
            // 构造完整的日期字符串，确保是当天
            let now = new Date();
            let dateStr = appName.time('yyyy/MM/dd', now); // 2026/01/28
            let fullTimeStr = `${dateStr} ${roundTimeStr}`;

            // 如果 roundTimeStr 只有 "10:00"，转为 "2026/01/28 10:00:00"
            if (roundTimeStr.indexOf(":") > 0 && roundTimeStr.length <= 8) {
              roundDate = new Date(fullTimeStr);
            } else {
              // 尝试直接解析
              roundDate = new Date(roundTimeStr);
            }

            // 如果解析失败 (Invalid Date)，再试一次简单的
            if (isNaN(roundDate.getTime()) && roundTimeStr.includes(":")) {
              let [h, m] = roundTimeStr.split(":").map(Number);
              roundDate = new Date();
              roundDate.setHours(h, m, 0, 0);
            }
          }

          this.log(`   🔸 扫描场次: [${roundTimeStr}] (${roundDate ? appName.time('yyyy-MM-dd hh:mm:ss', roundDate) : '解析失败'}) -包含 ${products.length} 个商品`);

          for (const item of products) {
            // 匹配名称
            if (item.product_name && (item.product_name.includes(GRAB_AMOUNT + "元") || item.product_name.includes(GRAB_AMOUNT + "话费"))) {
              this.log(`      ✅ 发现目标: ${item.product_name} (ID: ${item.product_id})`);

              candidates.push({
                id: item.product_id,
                name: item.product_name,
                typeCode: item.type_code,
                timeStr: roundTimeStr,
                startTime: roundDate,
                itemData: item
              });
            }
          }
        }
      }
    } catch (e) {
      this.log(`❌ 获取奖品列表失败: ${e.message}`);
    }

    // [逻辑变更] 智能选择最佳场次
    let targetPrizeId = null;
    let targetPrizeName = "";
    let targetTypeCode = "";

    if (candidates.length === 0) {
      this.log(`⚠️ 未在任何场次中匹配到名为 "${GRAB_AMOUNT}元" 的奖品。`);
      return;
    }

    // 排序逻辑:
    // 1. 优先找 "还未开始" 的 (startTime > now)，按时间正序 (最近的将来)
    // 2. 其次找 "刚刚开始" 的 (now >= startTime && now < startTime + 10min), 视为“正在抢”
    // 3. 最后找 "已过去" 的 (now > startTime + 10min), 可能是捡漏，或者用户只是在测试

    // 为了稳健，我们计算每个 candidate 距离当前时间的 diff (startTime - now)
    // diff > 0: 将来
    // diff < 0: 过去
    // 我们希望 diff 最小的正数 (即将开始)，或者是 最大的负数但是绝对值很小 (刚刚开始)

    const now = Date.now();

    // 给 candidates 评分
    // 状态: 0=完美(即将开始或刚开始10分钟内), 1=太早, 2=太晚(已结束)
    candidates.forEach(c => {
      if (!c.startTime) {
        c.score = 999;
        c.diff = 999999999;
        return;
      }
      c.diff = c.startTime.getTime() - now;

      // 刚刚开始 20分钟内 (放宽一点) 都算 "正在进行" (score -100 极高优先级)
      if (c.diff <= 0 && c.diff > -20 * 60 * 1000) {
        c.score = -100 + Math.abs(c.diff); // 越接近当前时间越小
      }
      // 即将开始 (score = diff, 正数)
      else if (c.diff > 0) {
        c.score = c.diff;
      }
      // 已经过去很久 (score = 99999xxxxx)
      else {
        c.score = 1000000000 + Math.abs(c.diff);
      }
    });

    // 按 score 排序 (小到大)
    candidates.sort((a, b) => a.score - b.score);

    // 选中第一个
    const best = candidates[0];
    targetPrizeId = best.id;
    targetPrizeName = best.name;
    targetTypeCode = best.typeCode;
    this.grabTargetTime = best.startTime;

    this.log(`🎯 最终锁定场次: [${best.timeStr}] ${best.name} (开始时间: ${this.grabTargetTime ? appName.time('yyyy-MM-dd hh:mm:ss', this.grabTargetTime) : 'N/A'})`);
    this.log(`   (共发现 ${candidates.length} 个匹配项，已自动优选最佳场次)`);


    // 2. 精确等待 (Wait Until Time)
    if (this.grabTargetTime) {
      const now = Date.now();
      const targetTs = this.grabTargetTime.getTime();
      // 提前 500ms 唤醒，给网络请求留出余量
      const wakeUpTs = targetTs - 500;
      const waitMs = wakeUpTs - now;

      this.log(`🕒 [时间同步] 当前: ${appName.time('hh:mm:ss.S', now)} | 目标: ${appName.time('hh:mm:ss.S', targetTs)} | 需等待: ${waitMs}ms`);

      if (waitMs > 0) {
        this.log(`⏳ [倒计时] 距离场次开始还有 ${Math.ceil(waitMs / 1000)} 秒，脚本将休眠等待...`);
        this.log(`⏰ 预计唤醒时间: ${appName.time('yyyy-MM-dd hh:mm:ss.S', wakeUpTs)}`);
        await appName.wait(waitMs);
        this.log(`⏰ 唤醒成功！准备抢兑！`);
      } else {
        this.log(`⚡ 当前时间已超过或接近场次时间 (diff: ${waitMs}ms)，直接抢兑！`);
      }
    } else {
      this.log(`⚠️ 未能解析到准确场次时间，直接抢兑！`);
    }

    // 3. 执行抢兑 (死循环或单次 视需求)
    // 抢兑通常是瞬时的，尝试 5 次
    for (let i = 1; i <= 5; i++) {
      this.log(`🔥 [第${i}次冲击] 发起兑换请求...`);
      try {
        const formData = {
          product_id: targetPrizeId, // 修正字段名: product_id
          typeCode: targetTypeCode   // 新增字段: typeCode
        };

        const grabConfig = {
          fn: "sign_grab_submit",
          method: "post",
          url: UNICOM_GRAB_URL, // 抢兑第一步地址
          form: formData,
          headers: { "Origin": "https://img.client.10010.com" }
        };

        // 极速请求第一步: 提交
        let { result: runRes } = await this.request(grabConfig);

        // 只有第一步成功且有 uuid，才进行第二步确认
        if (runRes && runRes.status === "0000" && runRes.data && runRes.data.uuid) {
          const uuid = runRes.data.uuid;
          this.log(`📝 [提交成功] 获取到工单号: ${uuid}，正在查询最终结果...`);

          // 极速请求第二步: 确认结果
          const resultConfig = {
            fn: "sign_grab_result",
            method: "post",
            url: "https://act.10010.com/SigninApp/convert/prizeConvertResult",
            form: { uuid: uuid },
            headers: { "Origin": "https://img.client.10010.com" }
          };

          // let { result: finalRes } = await this.request(resultConfig);
          let { result: finalRes } = await this.request(resultConfig);

          // [美化日志] 不再打印原始JSON，改为提取关键信息
          if (finalRes && finalRes.status === "0000") {
            this.log(`🎉🎉🎉 [抢兑成功] 恭喜！已成功抢到目标奖品！ 🎉🎉🎉`, { notify: true });
            break; // 成功则退出循环
          } else {
            // 解析错误详情
            const status = finalRes?.status || "未知";
            const errCode = finalRes?.data?.errorCode || "";
            const msg = finalRes?.msg || finalRes?.message || "未知原因";
            // 有时候具体的错误原因藏在 rightBtn.name 里 (例如 "兑换规则达到上限")
            const detailMsg = finalRes?.data?.rightBtn?.name || "";

            let logMsg = `💔 [抢兑失败]`;
            if (status !== "0000") logMsg += ` 状态: ${status}`;
            if (errCode) logMsg += ` | 错误码: ${errCode}`;
            if (detailMsg) logMsg += ` | 详情: ${detailMsg}`;
            logMsg += ` | 提示: ${msg}`;

            this.log(logMsg, { notify: true });
          }

        } else {
          this.log(`📝 提交结果: ${runRes?.msg || runRes?.message || JSON.stringify(runRes)}`);
        }
        await appName.wait(200); // 间隔 200ms
      } catch (e) {
        this.log(`❌ 请求异常: ${e.message}`);
      }
    }
  }

  // ==================== 3. 增强：账户明细查询 (签到/抢兑/任务) ====================
  async sign_query_my_prizes() {
    this.log("正在查询账户明细 (抢兑)...");

    const url = "https://act.10010.com/SigninApp/convert/phoneDetails";
    const form = {
      log_type: "1",
      number: "1",
      list_num: ""
    };

    try {
      const { result } = await this.request({
        fn: "sign_query_prizes",
        method: "post",
        url: url,
        form: form,
        headers: { "Origin": "https://img.client.10010.com" }
      });

      if (result && result.status === "0000" && result.data && result.data.detailedBO) {
        const records = result.data.detailedBO;
        if (Array.isArray(records) && records.length > 0) {

          let loggedCount = 0;

          for (const item of records) {
            if (loggedCount >= 5) break;

            const remark = item.remark || "";
            const bussName = item.from_bussname || "";

            // 仅对“兑换”相关的记录进行展示
            if (remark.includes("兑换") || bussName.includes("兑换")) {
              let amount = item.booksNumber || item.books_number || "0";
              if (loggedCount === 0) this.log(`📋 [账户明细] 最近 5 条记录:`, { notify: true });
              this.log(`   🎁 [抢兑] ${item.order_time} | ${remark} (变动:${amount})`, { notify: true });
              loggedCount++;
            }
          }

          if (loggedCount === 0) {
            this.log(`[账户明细] 暂无兑换记录`);
          }
        } else {
          this.log(`[账户明细] 暂无兑换记录`);
        }
      } else {
        this.log(`[账户明细] 暂无兑换记录`);
      }
    } catch (e) {
      this.log(`[账户明细] 查询异常: ${e.message}`);
    }
  }

  // === 这里的代码逻辑改为了读取环境变量 ===
  // === 修改版：支持 JSON 格式 + 账号密码自动认证 ===
  // === 修正版：适配 data.list 结构 ===
  async set_proxy_ip() {
    const maxRetries = 5;
    let currentTry = 0;

    // 默认 http，如果环境变量设置了 UNICOM_PROXY_TYPE="socks5" 则切换
    const proxyType = (process.env.UNICOM_PROXY_TYPE || "http").toLowerCase();

    // ==================== 1. 全局代理复用逻辑 (无限期复用 + 连通性检测) ====================
    // [已禁用] 强制每个账号独立提取IP，避免串行执行时长效性不足导致失效
    /*
    if (!IS_GRAB_MODE && globalSharedProxy) {
      this.log(`♻️ [普通模式] 尝试复用全局代理IP...`);
      // 验活: 轻量级请求检测代理是否有效
      try {
        await this.got.get('https://www.baidu.com', {
          agent: globalSharedProxy,
          timeout: { request: 3000 },
          retry: { limit: 0 }
        });
        // 测试通过
        this.got = this.got.extend({ agent: globalSharedProxy });
        this.log(`✅ [复用成功] 全局代理连通性正常，继续使用`);
        return true;
      } catch (e) {
        this.log(`⚠️ [复用失败] 全局代理已失效 (${e.message})，将重新提取...`);
        globalSharedProxy = null; // 标记失效
      }
    }
    */
    // ==========================================================================

    while (currentTry < maxRetries) {
      currentTry++;
      try {
        const apiUrl = process.env.UNICOM_PROXY_API;
        if (!apiUrl) return false;

        if (currentTry > 1) {
          this.log(`🔄 [第${currentTry}次] 重试获取代理IP (${proxyType})...`);
        } else {
          this.log(`正在获取代理IP (模式: ${proxyType})...`);
        }

        // 请求代理API
        const response = await this.got.get(apiUrl, {
          agent: { http: undefined, https: undefined }, // [v12+] 禁用代理需显式置为 undefined
          timeout: { request: 5000 },
          responseType: 'json'
        });

        const body = response.body;
        let proxyData = null;

        // 智能识别提取到的数据格式
        if (body.data && body.data.list && body.data.list.length > 0) {
          proxyData = body.data.list[0];
        } else if (body.data && Array.isArray(body.data) && body.data.length > 0) {
          proxyData = body.data[0];
        } else if (Array.isArray(body)) {
          proxyData = body[0];
        }

        if (proxyData && proxyData.ip && proxyData.port) {
          const { ip, port } = proxyData;
          // 兼容不同字段名：user/account, pass/password
          const rawUser = proxyData.account || proxyData.user || "";
          const rawPass = proxyData.password || proxyData.pass || "";

          // 【关键优化】对账号密码进行编码，防止特殊字符导致连接失败
          const safeUser = encodeURIComponent(rawUser);
          const safePass = encodeURIComponent(rawPass);

          let proxyUrl = "";
          let newAgent = {};
          let logMsg = "";

          // 根据类型构建代理URL
          if (proxyType === "socks5") {
            if (rawUser && rawPass) {
              proxyUrl = `socks5://${safeUser}:${safePass}@${ip}:${port}`;
              logMsg = `socks5://***:***@${ip}:${port}`;
            } else {
              proxyUrl = `socks5://${ip}:${port}`;
              logMsg = `socks5://${ip}:${port}`;
            }
            // Socks5 代理对象
            // 显式设置超时，防止死等
            const socksAgent = new SocksProxyAgent(proxyUrl, {
              timeout: 5000
            });
            newAgent = { http: socksAgent, https: socksAgent };

          } else {
            // HTTP 代理
            if (rawUser && rawPass) {
              proxyUrl = `http://${safeUser}:${safePass}@${ip}:${port}`;
              logMsg = `http://***:***@${ip}:${port}`;
            } else {
              proxyUrl = `http://${ip}:${port}`;
              logMsg = `http://${ip}:${port}`;
            }
            // HTTP 代理对象
            newAgent = {
              http: new HttpProxyAgent({
                keepAlive: false,
                proxy: proxyUrl
              }),
              https: new HttpsProxyAgent({
                keepAlive: false,
                proxy: proxyUrl,
                rejectUnauthorized: false
              })
            };
          }

          this.log(`🔍 提取成功: ${logMsg}`);

          // 连通性测试 (访问百度，3秒超时)
          try {
            await this.got.get('https://www.baidu.com', {
              agent: newAgent,
              timeout: { request: 3000 },
              retry: { limit: 0 }
            });

            // 测试通过，应用代理
            this.got = this.got.extend({ agent: newAgent });

            // 更新全局缓存 (如果是普通模式)
            if (!IS_GRAB_MODE) {
              globalSharedProxy = newAgent;
            }

            this.log(`✅ 代理连通性测试通过`);
            return true;

          } catch (testErr) {
            // 如果白名单没加好，这里通常会报 407 或 socket hang up
            this.log(`⚠️ 代理测试失败: ${testErr.message} (可能是白名单未生效或IP质量差)`);
          }

        } else {
          const errorMsg = typeof body === 'object' ? JSON.stringify(body) : body;
          this.log(`❌ 提取数据异常: ${errorMsg}`);
        }
      } catch (e) {
        this.log(`❌ 请求代理API异常: ${e.message}`);
      }

      // 失败间隔
      if (currentTry < maxRetries) await appName.wait(2000);
    }

    this.log(`🚫 重试${maxRetries}次均失败，回退至本地IP`);
    return false;
  }

  // [新增] 故障转移方法：当请求连续失败/超时时调用
  async failover_proxy() {
    this.log("⚠️ [故障转移] 检测到网络不稳定，正在检查当前代理是否存活...");

    // 1. 尝试验活当前代理
    try {
      // 注意：这里必须显式指定 retry: 0，否则验活失败又会触发内部重试导致死循环
      await this.got.get('https://www.baidu.com', {
        timeout: { request: 3000 },
        retry: { limit: 0 }
      });
      this.log("✅ [故障转移] 经测试当前IP仍有效，继续复用，暂不提取新IP。");
      await appName.wait(1000);
      return true;
    } catch (e) {
      this.log(`❌ [故障转移]当前代理已失效 (${e.message})，准备更换新IP...`);
    }

    // 2. 验活失败，提取新IP
    await appName.wait(2000);
    return await this.set_proxy_ip();
  }

  // --- RSA 加密辅助函数 (对应原脚本2的功能) ---
  rsa_encrypt(val) {
    const randomStr = Array.from({ length: 6 }, () => Math.floor(Math.random() * 9)).join('');
    const buffer = Buffer.from(String(val) + randomStr);
    return crypto.publicEncrypt({
      key: LOGIN_PUB_KEY,
      padding: crypto.constants.RSA_PKCS1_PADDING
    }, buffer).toString("base64");
  }

  // 移植自 Python 版 _generate_appid，用于生成动态且合规的 appId
  generate_appid() {
    const rnd = () => Math.floor(Math.random() * 10); // 生成 0-9 随机数
    return `${rnd()}f${rnd()}af` +
      `${rnd()}${rnd()}ad` +
      `${rnd()}912d306b5053abf90c7ebbb695887bc` +
      `870ae0706d573c348539c26c5c0a878641fcc0d3e90acb9be1e6ef858a` +
      `59af546f3c826988332376b7d18c8ea2398ee3a9c3db947e2471d32a49612`;
  }

  // --- 使用账号密码登录获取 token_online ---
  async unicom_login() {
    this.log(`正在使用账号 ${maskStr(this.account_mobile)} 进行登录...`);
    // ================= 新增代码 =================
    // 如果没有 appId（即账密模式初始化），则动态生成一个
    // 这样每次登录都像是一个新的合法设备，避免万人一面被风控
    if (!this.appId) {
      this.appId = this.generate_appid();
      this.log(`生成的临时 AppId: ${this.appId.substring(0, 15)}...`);
    }
    // ===========================================
    const now = new Date();
    const pad = (n) => n.toString().padStart(2, '0');
    const reqtime = `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())} ${pad(now.getHours())}:${pad(now.getMinutes())}:${pad(now.getSeconds())}`;

    try {
      const payload = {
        "version": "iphone_c@12.0100",
        "mobile": this.rsa_encrypt(this.account_mobile),
        "reqtime": reqtime,
        "deviceModel": "iPhone17,2",
        "password": this.rsa_encrypt(this.account_password)
      };

      const requestOptions = {
        fn: "unicom_login",
        method: "post",
        url: "https://m.client.10010.com/mobileService/login.htm",
        headers: {
          "User-Agent": `ChinaUnicom4.x/12.0.1 (com.chinaunicom.mobilebusiness; build:120001; iOS 19.2.0) Alamofire/5.9.1 unicom{version:"iphone_c@12.0100"}`
        },
        form: payload
      };

      let response = await this.request(requestOptions);
      let { result: data, statusCode } = response;

      if (data && (data.code === "0" || data.code === "0000")) {
        if (data.token_online) {
          this.token_online = data.token_online;
          this.log(`✅ 登录成功，获取到 token_online`);
          // ============ 插入这里 ============
          // 如果存在 appId，尝试回写变量
          if (this.appId) {
            await this.tryUpdateTokenToQL();
          } else {
            this.log("⚠️ 未获取到 appId，暂不回写环境变量");
          }
          // ================================
          return true;
        } else {
          this.log(`❌ 登录响应中未找到 token_online`);
          return false;
        }
      } else {
        this.log(`❌ 登录失败: ${data ? data.desc : '无响应'} (Code: ${data ? data.code : statusCode})`);
        return false;
      }

    } catch (e) {
      this.log(`❌ 登录过程异常: ${e.message}`);
      return false;
    }
  }

  // ==================== 青龙环境变量回写功能 (移植版) ====================
  async tryUpdateTokenToQL() {
    this.log(`🔄 [自动维护] 正在尝试将 Token 回写至青龙面板...`);

    // 1. 获取青龙应用权限凭证
    // 青龙面板在执行任务时，通常会自动注入这两个环境变量
    const client_id = process.env.QL_CLIENT_ID;
    const client_secret = process.env.QL_CLIENT_SECRET;

    // 如果是老版本青龙或者未注入，尝试读取 auth.json (兼容性处理)
    let authData = {};
    if (!client_id || !client_secret) {
      try {
        const authFile = fs.readFileSync('/ql/data/config/auth.json', 'utf8');
        authData = JSON.parse(authFile);
      } catch (e) {
        try {
          // 尝试旧路径
          const authFileOld = fs.readFileSync('/ql/config/auth.json', 'utf8');
          authData = JSON.parse(authFileOld);
        } catch (err) { }
      }
    }

    const final_id = client_id || authData.token; // 部分版本直接存token
    const final_secret = client_secret;

    // 构造青龙API地址，通常是本机
    const ql_host = "http://127.0.0.1:5600";

    try {
      // 2. 获取青龙 API Token
      let token = "";
      if (client_id && client_secret) {
        const tokenRes = await this.got.get(`${ql_host}/open/auth/token?client_id=${client_id}&client_secret=${client_secret}`, { responseType: 'json' });
        token = tokenRes.body.data.token;
      } else if (authData.token) {
        token = authData.token;
      } else {
        this.log(`⚠️ 无法获取青龙权限，跳过回写 (请确保已创建应用并给予权限)`);
        return;
      }

      // 3. 获取环境变量列表
      const envRes = await this.got.get(`${ql_host}/open/envs?searchValue=chinaUnicomCookie`, {
        headers: { 'Authorization': `Bearer ${token}` },
        responseType: 'json'
      });

      if (envRes.body.data.length > 0) {
        // 找到目标变量（可能有多个，取第一个匹配的）
        let targetEnv = envRes.body.data[0];
        let oldValue = targetEnv.value;

        // 4. 正则替换：匹配 "手机号#任意非分隔符字符"
        // 分隔符通常是 & 或 换行，这里用正则排除法
        const regex = new RegExp(`${this.account_mobile}#[^&@\\n]+`, 'g');

        // 构造新值: Token#AppId
        const newValueStr = `${this.token_online}#${this.appId}`;

        if (oldValue.match(regex)) {
          const newValue = oldValue.replace(regex, newValueStr);

          // 5. 提交更新
          const updateRes = await this.got.put(`${ql_host}/open/envs`, {
            headers: {
              'Authorization': `Bearer ${token}`,
              'Content-Type': 'application/json'
            },
            json: {
              name: "chinaUnicomCookie",
              value: newValue,
              id: targetEnv.id,
              remarks: targetEnv.remarks // 保持备注不变
            },
            responseType: 'json'
          });

          if (updateRes.body.code === 200) {
            this.log(`✅ [自动维护] 环境变量更新成功！下一次将使用 Token 免密登录。`);
          } else {
            this.log(`❌ [自动维护] 更新失败: ${JSON.stringify(updateRes.body)}`);
          }
        } else {
          this.log(`⚠️ [自动维护] 未在环境变量中找到匹配的账号字符串，跳过。`);
        }
      } else {
        this.log(`⚠️ [自动维护] 未找到 chinaUnicomCookie 变量，跳过。`);
      }

    } catch (e) {
      this.log(`❌ [自动维护] 回写过程异常: ${e.message}`);
    }
  }

  get_bizchannelinfo() {
    const bizChannelInfo = {
      bizChannelCode: errorNumber,
      disriBiz: partyName,
      unionSessionId: "",
      stType: "",
      stDesmobile: "",
      source: "",
      rptId: this.rptId,
      ticket: "",
      tongdunTokenId: this.tokenId_cookie,
      xindunTokenId: this.unicomTokenId
    };
    let bizChannelInfoString = JSON.stringify(bizChannelInfo);
    return bizChannelInfoString;
  }

  get_epay_authinfo() {
    const authInfo = {
      mobile: "",
      sessionId: this.sessionId,
      tokenId: this.tokenId,
      userId: ""
    };
    return JSON.stringify(authInfo);
  }

  get_flmf_data(actCode = "welfareCenter") {
    const flmfData = {
      sid: this.flmf_sid,
      actcode: actCode
    };
    return flmfData;
  }

  encode_woread(data, password = defaultPassword) {
    let encryptedData = UencryptWithCryptoJS("AES", "CBC", "Pkcs7", JSON.stringify(data), password, ivString);
    return Buffer.from(encryptedData, "utf-8").toString("base64");
  }
  encode_woread1(data, password = defaultPassword) {
    let encryptedData = UencryptWithCryptoJS("AES", "CBC", "Pkcs7", data, password, ivString);
    return Buffer.from(encryptedData, "utf-8").toString("base64");
  }

  // 新增：单字符串加密，用于模拟Python脚本中的参数加密
  encode_woread_str(text, password = defaultPassword) {
    let encryptedData = UencryptWithCryptoJS("AES", "CBC", "Pkcs7", text, password, ivString);
    return Buffer.from(encryptedData, "utf-8").toString("base64");
  }

  get_woread_param() {
    return {
      timestamp: appName.time("yyyyMMddhhmmss"),
      token: this.woread_token,
      userid: this.woread_userid,
      userId: this.woread_userid,
      userIndex: this.woread_userIndex,
      userAccount: this.mobile,
      verifyCode: this.woread_verifycode
    };
  }
  get_woread_m_param() {
    return {
      timestamp: appName.time("yyyyMMddhhmmss"),
      signtimestamp: Date.now(),
      source: maxRetries,
      token: this.woread_token
    };
  }
  get_ltyp_sign_header(secretKey) {
    const currentTime = Date.now();
    const randomSequence = Math.floor(89999 * Math.random()) + 100000;
    const productId = ProductId2;
    const version = emptyString;
    const signature = cryptoJS.MD5(secretKey + currentTime + randomSequence + productId + version).toString();

    const header = {
      key: secretKey,
      resTime: currentTime,
      reqSeq: randomSequence,
      channel: productId,
      version: version,
      sign: signature
    };

    return header;
  }
  async onLine(options = {}) {
    // 检查是否需要先登录获取Token
    if (!this.token_online && this.account_mobile && this.account_password) {
      let loginSuccess = await this.unicom_login();
      if (!loginSuccess) {
        this.log("⚠️ 账号密码登录失败，无法继续执行 onLine");
        return false;
      }
    }

    let loginSuccess = false;
    // const filePath = path.join(__dirname, 'chinaUnicom_cache.json');

    try {
      const androidVersion = "android@11.0000";
      const deviceId = this.uuid;

      let requestOptions = {
        fn: "onLine",
        method: "post",
        url: "https://m.client.10010.com/mobileService/onLine.htm",
        headers: {
          'User-Agent': `Dalvik/2.1.0 (Linux; U; Android 9; ALN-AL10 Build/PQ3A.190705.11211540);unicom{version:${androidVersion}}`
        },
        // 构造基础表单数据
        form: {
          isFirstInstall: '1',
          netWay: 'Wifi',
          version: androidVersion,
          token_online: this.token_online,
          provinceChanel: 'general',
          deviceModel: 'ALN-AL10',
          step: 'dingshi',
          androidId: '291a7deb1d716b5a',
          reqtime: Date.now(),
          // 如果存在 appId (Token#AppId模式)，则动态追加参数
          ...(this.appId ? { appId: this.appId } : {})
        }
      };

      let response = await this.request(requestOptions);
      let { result: responseData, statusCode: responseStatus } = response;
      let responseCode = appName.get(responseData, "code", responseStatus);

      if (responseCode == 0) {
        loginSuccess = true;
        this.valid = true;
        this.mobile = responseData?.["desmobile"];
        this.name = responseData?.["desmobile"];
        // [修复] Token模式下 account_mobile 初始为空，登录成功后需补全，否则缓存失效
        if (!this.account_mobile && this.mobile) {
          this.account_mobile = this.mobile;
        }

        this.ecs_token = responseData?.["ecs_token"];
        this.city = responseData?.["list"];
        this.log("登录成功");

      } else {
        this.valid = false;
        this.log("登录失败[" + responseCode + "]");
        // 如果是因为Token失效且配置了密码，尝试重新登录（可选优化）
      }
    } catch (error) {
      console.log(error);
      this.log("发生异常：" + error.message);
    } finally {
      return loginSuccess;
    }
  }

  // ============================================
  // 权益超市 NEW LOGIC
  // ============================================

  async get_ticket(ecs_token) {
    this.log("权益超市: 正在获取 ticket...");
    try {
      const requestOptions = {
        fn: "get_ticket",
        method: "get",
        url: "https://m.client.10010.com/mobileService/openPlatform/openPlatLineNew.htm?to_url=https://contact.bol.wo.cn/market",
        headers: {
          'User-Agent': 'Dalvik/2.1.0 (Linux; U; Android 12; leijun Pro Build/SKQ1.22013.001);unicom{version:android@11.0702}',
          'Connection': "Keep-Alive",
          'Accept-Encoding': "gzip",
          'Cookie': `ecs_token=${ecs_token}`
        },
        followRedirect: false // Important: we need to capture the 302 redirect
      };
      const { headers, statusCode } = await this.request(requestOptions);
      if (statusCode === 302 && headers?.location) {
        const locationUrl = new URL(headers.location);
        const ticket = locationUrl.searchParams.get("ticket");
        if (ticket) {
          this.log("权益超市: 获取ticket成功");
          return ticket;
        }
      }
      this.log(`权益超市: 获取ticket失败, status: ${statusCode}`);
      return null;
    } catch (e) {
      this.log(`权益超市: 获取ticket异常: ${e.message}`);
      return null;
    }
  }

  async get_userToken(ticket) {
    this.log("权益超市: 正在获取 userToken...");
    try {
      const requestOptions = {
        fn: "get_userToken",
        method: "post",
        url: `https://backward.bol.wo.cn/prod-api/auth/marketUnicomLogin?ticket=${ticket}`,
        headers: {
          'User-Agent': 'Dalvik/2.1.0 (Linux; U; Android 12; leijun Pro Build/SKQ1.22013.001);unicom{version:android@11.0702}',
          'Connection': "Keep-Alive",
          'Accept-Encoding': "gzip",
        }
      };
      const { result, statusCode } = await this.request(requestOptions);
      if (result?.code === 200) {
        const userToken = result?.data?.token;
        if (userToken) {
          this.log("权益超市: 获取userToken成功");
          return userToken;
        }
      }
      this.log(`权益超市: 获取userToken失败: ${result?.msg || '返回数据异常'}`);
      return null;
    } catch (e) {
      this.log(`权益超市: 获取userToken异常: ${e.message}`);
      return null;
    }
  }

  async get_AllActivityTasks(ecs_token, userToken) {
    this.log("权益超市: 正在获取任务列表...");
    try {
      const requestOptions = {
        fn: "getAllActivityTasks",
        method: "get",
        url: "https://backward.bol.wo.cn/prod-api/promotion/activityTask/getAllActivityTasks?activityId=12",
        headers: {
          'User-Agent': 'Dalvik/2.1.0 (Linux; U; Android 12; leijun Pro Build/SKQ1.22013.001);unicom{version:android@11.0702}',
          'Authorization': `Bearer ${userToken}`,
          'Cookie': `ecs_token=${ecs_token}`
        }
      };
      const { result } = await this.request(requestOptions);
      if (result?.code === 200) {
        const tasks = result?.data?.activityTaskUserDetailVOList || [];
        this.log(`权益超市: 成功获取到 ${tasks.length} 个任务`);
        return tasks;
      }
      this.log(`权益超市: 查询任务列表失败: ${result?.msg || '未知错误'}`);
      return [];
    } catch (e) {
      this.log(`权益超市: 查询任务列表异常: ${e.message}`);
      return [];
    }
  }

  async do_ShareList(shareList, userToken) {
    this.log("权益超市: 开始执行任务...");
    for (const task of shareList) {
      const { name, param1: param, triggerTime, triggeredTime } = task;
      if (name.includes("购买") || name.includes("秒杀")) {
        this.log(`权益超市: 🚫 ${name} [跳过]`);
        continue;
      }
      if (triggeredTime >= triggerTime) {
        this.log(`权益超市: ✅ ${name} [已完成]`);
        continue;
      }

      let url = "";
      if (name.includes("浏览") || name.includes("查看")) {
        url = `https://backward.bol.wo.cn/prod-api/promotion/activityTaskShare/checkView?checkKey=${param}`;
      } else if (name.includes("分享")) {
        url = `https://backward.bol.wo.cn/prod-api/promotion/activityTaskShare/checkShare?checkKey=${param}`;
      }

      if (url) {
        try {
          const requestOptions = {
            fn: `do_task_${name}`,
            method: "post",
            url: url,
            headers: {
              'User-Agent': 'Dalvik/2.1.0 (Linux; U; Android 12; leijun Pro Build/SKQ1.22013.001);unicom{version:android@11.0702}',
              'Authorization': `Bearer ${userToken}`,
            }
          };
          const { result } = await this.request(requestOptions);
          if (result?.code === 200) {
            this.log(`权益超市: ✅ ${name} [执行成功]`);
          } else {
            this.log(`权益超市: ❌ ${name} [执行失败]: ${result?.msg}`);
          }
        } catch (e) {
          this.log(`权益超市: ❌ ${name} [执行异常]: ${e.message}`);
        }
      }
      await appName.wait(2000 + Math.random() * 2000);
    }
  }

  // 优化版：权益超市查询奖品池 (支持全局缓存)
  async get_Raffle(userToken) {
    // 如果全局已经检查过，且判定无奖品，直接返回 false，后续账号不再浪费请求
    if (globalMarketPoolChecked && !globalMarketHasPrizes) {
      this.log("权益超市: ⚡ 依据全局缓存，今日无放水，跳过查询");
      return false;
    }

    this.log("权益超市: 正在查询奖品池...");
    try {
      const requestOptions = {
        fn: "get_Raffle",
        method: "post",
        url: "https://backward.bol.wo.cn/prod-api/promotion/home/raffleActivity/prizeList?id=12",
        headers: {
          'User-Agent': 'Dalvik/2.1.0 (Linux; U; Android 12; leijun Pro Build/SKQ1.22013.001);unicom{version:android@11.0702}',
          'Authorization': `Bearer ${userToken}`
        }
      };
      const { result } = await this.request(requestOptions);

      // 解析奖品逻辑
      if (result?.code === 200 && Array.isArray(result.data)) {
        const keywords = ['月卡', '月会员', '月度', 'VIP月', '一个月', '周卡'];
        const excludeWords = ['5G宽视界', '沃视频']; // 排除不值钱的

        // 筛选出符合关键词、不含排除词、有库存、概率>0 的奖品
        const livePrizes = result.data.filter(prize =>
          keywords.some(kw => prize.name.includes(kw)) &&
          !excludeWords.some(kw => prize.name.includes(kw)) &&
          parseInt(prize.dailyPrizeLimit, 10) > 0 &&
          parseFloat(prize.probability) > 0
        );

        if (livePrizes.length > 0) {
          livePrizes.forEach(item => {
            const name = item.name.trim();
            const daily = item.dailyPrizeLimit;
            const total = item.quantity;
            const prob = (item.probability * 100).toFixed(1);
            this.log(`权益超市: 【${name}】监测到放水 (日库存:${daily}, 总库存:${total}, 概率:${prob}%)`);
          });

          // 更新全局状态：有奖品
          globalMarketHasPrizes = true;
          globalMarketPoolChecked = true;
          return true;
        }
      }

      // 如果代码走到这里，说明没库存
      this.log("权益超市: 📢 未监测到高价值权益放水");

      // 更新全局状态：无奖品
      globalMarketHasPrizes = false;
      globalMarketPoolChecked = true;
      return false;

    } catch (e) {
      this.log(`权益超市: 查询奖品池异常: ${e.message}`);
      return false; // 异常情况下不锁全局，让下一个号再试试
    }
  }

  async get_raffle_count(userToken) {
    this.log("权益超市: 正在查询抽奖次数...");
    try {
      const requestOptions = {
        fn: "get_raffle_count",
        method: "post",
        url: "https://backward.bol.wo.cn/prod-api/promotion/home/raffleActivity/getUserRaffleCountExt?id=12",
        headers: {
          'User-Agent': 'Dalvik/2.1.0 (Linux; U; Android 12; leijun Pro Build/SKQ1.22013.001);unicom{version:android@11.0702}',
          'Authorization': `Bearer ${userToken}`
        }
      };
      const { result } = await this.request(requestOptions);

      let count = 0;
      if (result?.code === 200) {
        // 【关键修复】兼容对象格式，提取 raffleCount
        if (typeof result.data === 'object' && result.data !== null && result.data.raffleCount !== undefined) {
          count = parseInt(result.data.raffleCount) || 0;
        } else {
          // 兼容旧格式直接返回数字
          count = parseInt(result.data) || 0;
        }
      }

      if (count > 0) {
        this.log(`权益超市: ✅ 当前抽奖次数: ${count}`);
        for (let i = 0; i < count; i++) {
          this.log(`权益超市: 🎯 第 ${i + 1} 次抽奖...`);
          const success = await this.get_userRaffle(userToken);
          if (!success) {
            this.log("权益超市: 抽奖失败或遇到验证, 停止后续抽奖");
            break;
          }
          await appName.wait(3000 + Math.random() * 2000);
        }
      } else {
        // 只有当 count 真的为 0 时才打印这个，避免日志刷屏
        this.log(`权益超市: 当前无抽奖次数`);
      }
    } catch (e) {
      this.log(`权益超市: 查询抽奖次数异常: ${e.message}`);
    }
  }

  async get_userRaffle(userToken) {
    try {
      const requestOptions = {
        fn: "get_userRaffle",
        method: "post",
        url: "https://backward.bol.wo.cn/prod-api/promotion/home/raffleActivity/userRaffle?id=12&channel=",
        headers: {
          'User-Agent': 'Dalvik/2.1.0 (Linux; U; Android 12; leijun Pro Build/SKQ1.22013.001);unicom{version:android@11.0702}',
          'Authorization': `Bearer ${userToken}`
        }
      };
      const { result } = await this.request(requestOptions);

      if (result?.code === 200) {
        const data = result.data || {};
        const { lotteryRecordId, prizesName } = data;
        // 兼容各种空消息情况
        let message = data.message || result.msg || "";
        if (message === "null") message = "";

        // 1. 中奖逻辑 (带通知)
        if (prizesName && !prizesName.includes("谢谢参与")) {
          this.log(`权益超市: 🎉 抽奖成功: ${prizesName}`, { notify: true });
          if (lotteryRecordId) {
            this.log(`权益超市:  尝试领取：${prizesName}`);
            await this.get_grantPrize(userToken, lotteryRecordId, prizesName);
          }
          return true;
        }

        // 2. 未中奖逻辑 (全部带通知 { notify: true })

        // 情况A: 被拦截 (库存/风控)
        if (message.includes("预缓存") || message.includes("库存不足")) {
          this.log(`权益超市: 💨 未中奖(库存/风控拦截)`, { notify: true });
        }
        // 情况B: 次数上限
        else if (message.includes("重复参与") || message.includes("次数") || message.includes("24小时")) {
          this.log(`权益超市: 🛑 抽奖失败(今日机会已用完)`, { notify: true });
        }
        // 情况C: 纯空气
        else if (!message) {
          this.log(`权益超市: 💨 未中奖(继续努力)`, { notify: true });
        }
        // 情况D: 其他消息
        else {
          this.log(`权益超市: 💨 未中奖: ${message}`, { notify: true });
        }

        return true;

      } else if (result?.code === 500) {
        // 500错误通常不发通知，除非你需要监控报错
        this.log(`权益超市: 抽奖请求异常 (Code 500): ${result?.msg}`);
        if (result?.msg?.includes("验证")) {
          return await this.get_validateCaptcha(userToken);
        }
        return false;
      } else {
        this.log(`权益超市: 抽奖失败: ${result?.msg || '未知错误'}`);
        return false;
      }
    } catch (e) {
      this.log(`权益超市: 抽奖异常: ${e.message}`);
      return false;
    }
  }

  async get_validateCaptcha(userToken) {
    try {
      const requestOptions = {
        fn: "get_validateCaptcha",
        method: "post",
        url: "https://backward.bol.wo.cn/prod-api/promotion/home/raffleActivity/validateCaptcha?id=12",
        headers: {
          'User-Agent': 'Dalvik/2.1.0 (Linux; U; Android 12; leijun Pro Build/SKQ1.22013.001);unicom{version:android@11.0702}',
          'Authorization': `Bearer ${userToken}`
        }
      };
      const { result } = await this.request(requestOptions);
      if (result?.code === 200) {
        this.log("权益超市: 人机验证成功, 重新抽奖...");
        return await this.get_userRaffle(userToken);
      }
      this.log(`权益超市: 人机验证失败: ${result?.msg}`);
      return false;
    } catch (e) {
      this.log(`权益超市: 人机验证异常: ${e.message}`);
      return false;
    }
  }

  async queryGeneralPrizes(userToken) {
    this.log("权益超市: 正在查询待领取奖品...");
    if (!userToken) {
      this.log("权益超市-查通用奖品: userToken not found, skipping.");
      return;
    }
    // 'this.mobile' is available after a successful onLine.htm call.
    if (!this.mobile) {
      this.log("权益超市-查待领取奖品: 手机号未找到, 跳过.");
      return;
    }

    try {
      const requestBody = {
        "isReceive": "0",
        "receiveStatus": "0",
        "limit": 20,
        "page": 1,
        "mobile": this.mobile,
        "businessSources": ["3", "4", "5", "6", "99"],
        "isPromotion": 1,
        "returnFormatType": 1
      };

      const requestOptions = {
        fn: "queryGeneralPrizes",
        method: "post",
        url: `https://backward.bol.wo.cn/prod-api/market/contactReceive/queryReceiveRecord`,
        headers: {
          'Authorization': `Bearer ${userToken}`,
          'User-Agent': 'Dalvik/2.1.0 (Linux; U; Android 12; leijun Pro Build/SKQ1.22013.001);unicom{version:android@11.0702}',
          'Content-Type': 'application/json'
        },
        json: requestBody
      };

      const { result } = await this.request(requestOptions);

      if (result?.code !== 200) {
        this.log(`权益超市-查待领取奖品: 查询失败: ${result?.msg || '未知错误'}`);
        return;
      }

      const prizes = result.data?.recordObjs || [];
      const now = new Date();

      const claimablePrizes = prizes.filter(prize => {
        if (!prize.receiveEndTime) return false;
        const endTime = new Date(prize.receiveEndTime.replace(/-/g, "/"));
        return endTime > now;
      });

      if (claimablePrizes.length > 0) {
        this.log(`权益超市: 查询到 ${claimablePrizes.length} 个可领取奖品:`, { notify: true });
        for (const prize of claimablePrizes) {
          this.log(`    - ${prize.recordName} (截止: ${prize.receiveEndTime})`);
          if (prize.businessId) {
            await this.grantGeneralPrize(userToken, prize);
            await appName.wait(1500 + Math.random() * 1000);
          } else {
            this.log(`    └─ 缺少 businessId, 无法自动领取.`);
          }
        }
      } else {
        this.log("权益超市: 未发现可领取的奖品。");
      }

    } catch (e) {
      this.log(`权益超市-查待领取奖品: 任务异常: ${e.message}`);
    }
  }


  async query_market_raffle_records(userToken) {
    this.log("权益超市: 正在查询抽奖记录...");
    try {
      const requestOptions = {
        fn: "query_market_raffle_records",
        method: "post",
        url: "https://backward.bol.wo.cn/prod-api/promotion/home/raffleActivity/getMyPrize",
        headers: {
          'User-Agent': "Dalvik/2.1.0 (Linux; U; Android 12; leijun Pro Build/SKQ1.22013.001);unicom{version:android@11.0702}",
          'Content-Type': "application/json",
          'Authorization': `Bearer ${userToken}`,
        },
        json: {
          "id": 12,
          "type": 0,
          "page": 1,
          "limit": 20 // 限制条数，避免日志过长
        }
      };

      const { result } = await this.request(requestOptions);
      if (result?.code === 200) {
        const records = result.data?.list || [];
        if (records.length > 0) {
          this.log(`权益超市: 最近 ${records.length} 条抽奖记录:`, { notify: true });
          for (const item of records) {
            const status = item.status === 1 ? '已领取' : '待领取';
            this.log(`    - [${item.createTime}] ${item.prizesName} (${status})`);
          }
        } else {
          this.log("权益超市: 无近期抽奖记录。");
        }
      } else {
        this.log(`权益超市: 查询抽奖记录失败: ${result?.msg || '未知错误'}`);
      }
    } catch (e) {
      this.log(`权益超市: 查询抽奖记录异常: ${e.message}`);
    }
  }

  async query_phone_recharge_records(userToken) {
    this.log("权益超市: 正在查询本月话费抢购记录...");
    try {
      const requestOptions = {
        fn: "query_phone_recharge_records",
        method: "post",
        url: "https://backward.bol.wo.cn/prod-api/promotion/home/raffleActivity/getMyPrize",
        headers: {
          'User-Agent': "Dalvik/2.1.0 (Linux; U; Android 12; leijun Pro Build/SKQ1.22013.001);unicom{version:android@11.0702}",
          'Content-Type': "application/json",
          'Authorization': `Bearer ${userToken}`,
        },
        json: {
          "id": 12,
          "type": 0,
          "page": 1,
          "limit": 100
        }
      };
      const { result } = await this.request(requestOptions);
      if (result?.code === 200) {
        const list = result.data?.list || [];
        const date = new Date();
        const currentMonth = date.getMonth() + 1;
        const currentYear = date.getFullYear();
        let totalAmount = 0.0;
        let records = [];

        for (const item of list) {
          const createTime = item.createTime || "";
          if (createTime) {
            // Check if record is from current month
            // createTime format example: "2023-05-20 12:00:00"
            const mStr = currentMonth < 10 ? `0${currentMonth}` : `${currentMonth}`;
            const targetStr = `${currentYear}-${mStr}`;

            if (createTime.includes(targetStr)) {
              const name = item.prizesName || "";
              if (["话费", "充值", "缴费", "红包"].some(kw => name.includes(kw))) {
                let amount = 0.0;
                const match = name.match(/(\d+(\.\d+)?)元/);
                if (match) {
                  amount = parseFloat(match[1]);
                }
                records.push({ name, time: createTime, amount });
                totalAmount += amount;
              }
            }
          }
        }
        if (records.length > 0) {
          this.log(`💰 [资产-抢购] 本月权益超市话费累计: ${totalAmount.toFixed(2)}元`, { notify: true });
        } else {
          this.log("权益超市: 本月暂无话费抢购记录");
        }
      }
    } catch (e) {
      this.log(`查询话费抢购记录异常: ${e.message}`);
    }
  }

  async query_cloud_lottery_records(cloudToken, activityId) {
    this.log(`云盘任务: 正在查询活动[${activityId}]中奖记录...`);
    try {
      const requestOptions = {
        fn: "query_cloud_lottery_records",
        method: "get",
        url: "https://panservice.mail.wo.cn/activity/lottery/recordList",
        headers: {
          'User-Agent': "Dalvik/2.1.0 (Linux; U; Android 12; leijun Pro Build/SKQ1.22013.001);unicom{version:android@11.0702}",
          'Accept': "application/json, text/plain, */*",
          'requestTime': Date.now().toString(),
          'clientId': "1001000165",
          'X-YP-Client-Id': "1001000165",
          'source-type': "woapi",
          'X-YP-Access-Token': cloudToken,
          'token': cloudToken,
        },
        searchParams: { 'activityId': activityId }
      };

      const { result } = await this.request(requestOptions);
      if (result?.meta?.code === "200") {
        const records = result.result || [];
        if (records.length > 0) {
          this.log(`云盘任务: 最近 ${records.length} 条中奖记录:`, { notify: true });
          for (const item of records) {
            this.log(`    - [${item.createTime}] ${item.prizeName}`, { notify: true });
          }
        } else {
          this.log("云盘任务: 无近期中奖记录。");
        }
      } else {
        // this.log(`云盘任务: 查询记录失败: ${JSON.stringify(result)}`);
      }
    } catch (e) {
      this.log(`云盘任务: 查询记录异常: ${e.message}`);
    }
  }

  async grantGeneralPrize(userToken, prize) {
    this.log(`权益超市: └─ 尝试领取: ${prize.recordName}`);
    try {
      const requestOptions = {
        fn: "grantGeneralPrize",
        method: "post",
        url: "https://backward.bol.wo.cn/prod-api/promotion/home/raffleActivity/grantPrize",
        headers: {
          'Authorization': `Bearer ${userToken}`,
          'User-Agent': 'Dalvik/2.1.0 (Linux; U; Android 12; leijun Pro Build/SKQ1.22013.001);unicom{version:android@11.0702}',
          'Content-Type': 'application/json'
        },
        json: { "recordId": prize.businessId } // Using businessId as recordId
      };
      const { result } = await this.request(requestOptions);
      if (result?.code === 200) {
        // 【修复】把奖品名字传进来或者简单通知，这里简单加上通知标记
        this.log(`权益超市:    └─ ✅ [领取成功]: ${prize.recordName}`, { notify: true });
      } else {
        this.log(`权益超市:    └─ ❌ [领取失败]: ${result?.msg}`);
      }
    } catch (e) {
      this.log(`权益超市:    └─ 领取通用奖品 ${prize.recordName} 异常: ${e.message}`);
    }
  }

  async get_grantPrize(userToken, lotteryRecordId, prizesName) {
    try {
      const requestOptions = {
        fn: "get_grantPrize",
        method: "post",
        url: "https://backward.bol.wo.cn/prod-api/promotion/home/raffleActivity/grantPrize?activityId=12",
        headers: {
          'User-Agent': 'Dalvik/2.1.0 (Linux; U; Android 12; leijun Pro Build/SKQ1.22013.001);unicom{version:android@11.0702}',
          'Authorization': `Bearer ${userToken}`,
          'Content-Type': 'application/json'
        },
        json: { "recordId": lotteryRecordId }
      };
      const { result } = await this.request(requestOptions);
      if (result?.code === 200) {
        this.log(`权益超市: ✅ ${prizesName} [领取成功]`);
      } else {
        this.log(`权益超市: ❌ ${prizesName} [领取失败]: ${result?.msg}`);
      }
    } catch (e) {
      this.log(`权益超市: 领取奖品异常: ${e.message}`);
    }
  }

  async marketWateringTask(userToken) {
    this.log("权益超市: 浇花任务开始...");
    if (!userToken) {
      this.log("权益超市-浇花: userToken not found, skipping.");
      return;
    }

    try {
      // 1. Get watering status
      const statusOptions = {
        fn: "marketGetWateringStatus",
        method: "get",
        url: `https://backward.bol.wo.cn/prod-api/promotion/activityTask/getMultiCycleProcess?activityId=13`,
        headers: {
          'Authorization': `Bearer ${userToken}`,
          'User-Agent': 'Dalvik/2.1.0 (Linux; U; Android 12; leijun Pro Build/SKQ1.22013.001);unicom{version:android@11.0702}',
        }
      };
      const { result: statusResult } = await this.request(statusOptions);

      if (statusResult?.code !== 200) {
        this.log(`权益超市-浇花: 获取状态失败: ${statusResult?.msg || '未知错误'}`);
        return;
      }

      const { triggeredTime, triggerTime, createDate } = statusResult.data;
      this.log(`权益超市-浇花: 当前进度 ${triggeredTime}/${triggerTime}`, { notify: true });

      // 2. Conditional logic
      if (triggeredTime >= triggerTime) {
        this.log("权益超市-浇花: 🌟 您有鲜花权益待领取! (连续浇花已满) 🌟", { notify: true });
        return;
      }

      // Check if watered today
      const todayStr = new Date(new Date().getTime() + 8 * 3600 * 1000).toISOString().split('T')[0];
      const lastWateredDateStr = createDate ? createDate.split(' ')[0] : '';

      if (todayStr === lastWateredDateStr) {
        this.log(`权益超市-浇花: 今日已浇水 (最后浇水时间: ${createDate})`, { notify: true });
        return;
      }

      this.log("权益超市-浇花: 今日未浇水，执行浇水操作...");

      // 3. Perform watering
      const waterOptions = {
        fn: "marketWatering",
        method: "post",
        url: `https://backward.bol.wo.cn/prod-api/promotion/activityTaskShare/checkWatering?xbsosjl=xbsosjlsujif&timeVerRan=${Date.now()}`,
        headers: {
          'Authorization': `Bearer ${userToken}`,
          'User-Agent': 'Dalvik/2.1.0 (Linux; U; Android 12; leijun Pro Build/SKQ1.22013.001);unicom{version:android@11.0702}',
          'Content-Type': 'application/json'
        },
        json: {}
      };
      const { result: waterResult } = await this.request(waterOptions);

      if (waterResult?.code === 200) {
        this.log("权益超市-浇花: ✅ 浇水成功!", { notify: true });
      } else {
        this.log(`权益超市-浇花: ❌ 浇水失败: ${waterResult?.msg || '未知错误'}`);
      }

    } catch (e) {
      this.log(`权益超市-浇花: 任务异常: ${e.message}`);
    }
  }

  async marketTask(isQueryOnly = false) {
    this.log("============= 权益超市 =============");

    // The main `task` function already calls `await user.onLine()`.
    // So when `marketTask` is called, `this.ecs_token` should be available.
    const ecs_token = this.ecs_token;

    if (!ecs_token) {
      this.log("权益超市: ❌ 未获取到 ecs_token, 跳过任务");
      this.log("============= 权益超市执行完毕 =============");
      return;
    }

    // 1. Get ticket
    const ticket = await this.get_ticket(ecs_token);
    if (!ticket) {
      this.log("============= 权益超市执行完毕 =============");
      return;
    }

    // 2. Get userToken
    const userToken = await this.get_userToken(ticket);
    if (!userToken) {
      this.log("============= 权益超市执行完毕 =============");
      return;
    }

    if (isQueryOnly) {
      this.log("权益超市: [查询模式] 跳过浇花、任务及抽奖，仅查询奖品...");
      // 5. Query and claim prizes
      // await this.get_MyPrize(userToken); // For raffle prizes
      await this.queryGeneralPrizes(userToken); // For general prizes
      // [新增] 查询抽奖记录
      await this.query_market_raffle_records(userToken);
      // [新增] 查询话费抢购记录
      await this.query_phone_recharge_records(userToken);
      this.log("============= 权益超市执行完毕 =============");
      return;
    }

    // New: Execute watering task
    await this.marketWateringTask(userToken);
    await appName.wait(2000);

    // 3. Get and do tasks
    const shareList = await this.get_AllActivityTasks(ecs_token, userToken);
    if (shareList && shareList.length > 0) {
      await this.do_ShareList(shareList, userToken);
    }

    // 4. Check raffle and draw
    const canRaffle = await this.get_Raffle(userToken);
    if (canRaffle) {
      await this.get_raffle_count(userToken);
    }

    // 5. Query and claim prizes
    // await this.get_MyPrize(userToken); // For raffle prizes
    await this.queryGeneralPrizes(userToken); // For general prizes
    await this.query_phone_recharge_records(userToken); // Also query here for full mode

    this.log("============= 权益超市执行完毕 =============");
  }


  async openPlatLineNew(url, options = {}) {
    const defaultResult = {
      ticket: "",
      type: "",
      loc: ""
    };

    let result = defaultResult;

    try {
      const queryParams = {
        to_url: url
      };
      const requestOptions = {
        fn: "openPlatLineNew",
        method: "get",
        url: "https://m.client.10010.com/mobileService/openPlatform/openPlatLineNew.htm",
        searchParams: queryParams
      };

      const { headers, statusCode } = await this.request(requestOptions);

      if (headers?.["location"]) {
        const locationUrl = new URL(headers.location);
        const type = locationUrl.searchParams.get("type") || "02";
        const ticket = locationUrl.searchParams.get("ticket");

        if (!ticket) {
          this.log("获取ticket失败");
        }

        result = {
          loc: headers.location,
          ticket: ticket,
          type: type
        };
      } else {
        this.log(`获取ticket失败[${statusCode}]`);
      }
    } catch (error) {
      console.log(error);
    } finally {
      return result;
    }
  }
  async gettaskip(options = {}) {
    const orderId = appName.randomString(32).toUpperCase();

    try {
      const requestBody = {
        mobile: this.mobile,
        orderId: orderId
      };

      const requestOptions = {
        fn: "gettaskip",
        method: "post",
        url: "https://m.client.10010.com/taskcallback/topstories/gettaskip",
        form: requestBody
      };

      await this.request(requestOptions);
    } catch (error) {
      console.log(error);
    } finally {
      return orderId;
    }
  }
  async draw_28_queryChance(options = {}) {
    try {
      const requestConfig = {
        fn: "draw_28_queryChance",
        method: "post",
        url: "https://m.client.10010.com/AppMonthly/appMonth/queryChance"
      };

      let {
        result: responseResult,
        statusCode: responseStatusCode
      } = await this.request(requestConfig),
        status = appName.get(responseResult, "status", responseStatusCode);

      if (status == "0000") {
        let remainingTimes = parseInt(responseResult?.["data"]?.["allRemainTimes"] || 0),
          drawTimes = Math.min(maxDrawTimes, remainingTimes);

        this.log("28日五折日可以抽奖" + remainingTimes + "次, 去抽" + drawTimes + "次");

        let isFirstAttempt = false;
        while (drawTimes-- > 0) {
          if (isFirstAttempt) {
            await appName.wait(8000);
          }
          isFirstAttempt = true;
          await this.draw_28_lottery();
        }
      } else {
        let errorMessage = responseResult?.["message"] || responseResult?.["msg"] || "";
        this.log("28日五折日查询抽奖次数失败[" + status + "]: " + errorMessage);
      }
    } catch (error) {
      console.log(error);
    }
  }
  async draw_28_lottery(options = {}) {
    try {
      const requestOptions = {
        fn: "draw_28_lottery",
        method: "post",
        url: "https://m.client.10010.com/AppMonthly/appMonth/lottery"
      };

      const { result: responseResult, statusCode: responseStatusCode } = await this.request(requestOptions);
      const status = appName.get(responseResult, "status", responseStatusCode);

      if (status === "0000") {
        const data = responseResult?.["data"];
        const code = appName.get(data, "code", -1);

        if (data?.["uuid"]) {
          await appName.wait(2000);
          await this.draw_28_winningRecord(data.uuid);
        } else {
          const errorMessage = data?.["message"] || data?.["msg"] || "";
          this.log(`28日五折日抽奖失败[${code}]: ${errorMessage}`);
        }
      } else {
        const errorMessage = responseResult?.["message"] || responseResult?.["msg"] || "";
        this.log(`28日五折日抽奖失败[${status}]: ${errorMessage}`);
      }
    } catch (error) {
      console.log(error);
    }
  }
  async draw_28_winningRecord(requestId, options = {}) {
    try {
      const requestPayload = {
        requestId: requestId
      };

      const requestOptions = {
        fn: "draw_28_winningRecord",
        method: "post",
        url: "https://m.client.10010.com/AppMonthly/appMonth/winningRecord",
        form: requestPayload
      };

      const { result, statusCode } = await this.request(requestOptions);
      const status = appName.get(result, "status", statusCode);

      if (status === "0000") {
        const responseData = result?.["data"];
        const resultCode = appName.get(responseData, "code", -1);

        if (resultCode === "0000") {
          const logOptions = {
            notify: true
          };
          this.log("28日五折日抽奖: " + responseData?.["prizeName"]?.replace(/\t/g, ""), logOptions);
        } else {
          const errorMessage = responseData?.["message"] || responseData?.["msg"] || "";
          this.log(`查询28日五折日抽奖结果失败[${resultCode}]: ${errorMessage}`);
        }
      } else {
        const errorMessage = result?.["message"] || result?.["msg"] || "";
        this.log(`查询28日五折日抽奖结果失败[${status}]: ${errorMessage}`);
      }
    } catch (error) {
      console.log(error);
    }
  }

  async ttlxj_authorize(ticket, type, refererUrl, options = {}) {
    try {
      const requestConfig = {
        fn: "ttlxj_authorize",
        method: "post",
        url: "https://epay.10010.com/woauth2/v2/authorize",
        headers: {
          Origin: "https://epay.10010.com",
          Referer: refererUrl
        },
        json: {
          response_type: "rptid",
          client_id: clientId,
          redirect_uri: "https://epay.10010.com/ci-mps-st-web/",
          login_hint: {
            credential_type: "st_ticket",
            credential: ticket,
            st_type: type,
            force_logout: true,
            source: "app_sjyyt"
          },
          device_info: {
            token_id: "chinaunicom-pro-" + Date.now() + "-" + appName.randomString(13),
            trace_id: appName.randomString(32)
          }
        }
      };

      const { result } = await this.request(requestConfig);
      const statusCode = appName.get(result, "status", -1);

      if (statusCode === 200) {
        await this.ttlxj_authCheck(options);
      } else {
        const errorMessage = result?.["message"] || result?.["msg"] || "";
        this.log(`天天领现金获取SESSION失败[${statusCode}]: ${errorMessage}`);
      }
    } catch (error) {
      console.log(error);
    }
  }

  async ttlxj_authCheck(options = {}) {
    try {
      const requestConfig = {
        fn: "ttlxj_authCheck",
        method: "post",
        url: "https://epay.10010.com/ps-pafs-auth-front/v1/auth/check",
        headers: {
          bizchannelinfo: this.get_bizchannelinfo()
        }
      };

      const { result } = await this.request(requestConfig);
      const responseCode = appName.get(result, "code", -1);

      if (responseCode === "0000") {
        const { mobile, sessionId, tokenId, userId } = result?.["data"]?.["authInfo"];
        const authInfo = {
          sessionId,
          tokenId,
          userId
        };
        Object.assign(this, authInfo);

        await this.ttlxj_userDrawInfo(options);
        await this.ttlxj_queryAvailable(options);
      } else {
        if (responseCode === "2101000100") {
          const loginUrl = result?.["data"]?.["woauth_login_url"];
          await this.ttlxj_login(loginUrl);
        } else {
          const errorMessage = result?.["msgInside"] || result?.["msg"] || "";
          this.log(`天天领现金获取tokenId失败[${responseCode}]: ${errorMessage}`);
        }
      }
    } catch (error) {
      console.log(error);
    }
  }

  async ttlxj_login(loginUrl, options = {}) {
    try {
      const fullUrl = `${loginUrl}https://epay.10010.com/ci-mcss-party-web/clockIn/?bizFrom=${errorCode}&bizChannelCode=${errorNumber}`;

      const requestConfig = {
        fn: "ttlxj_login",
        method: "get",
        url: fullUrl
      };

      const { headers, statusCode } = await this.request(requestConfig);

      if (headers?.["location"]) {
        const locationUrl = new URL(headers.location);
        this.rptId = locationUrl.searchParams.get("rptid");
        if (this.rptId) {
          await this.ttlxj_authCheck();
        } else {
          this.log("天天领现金获取rptid失败");
        }
      } else {
        this.log(`天天领现金获取rptid失败[${statusCode}]`);
      }
    } catch (error) {
      console.log(error);
    }
  }

  async ttlxj_userDrawInfo(options = {}) {
    try {
      const requestConfig = {
        fn: "ttlxj_userDrawInfo",
        method: "post",
        url: "https://epay.10010.com/ci-mcss-party-front/v1/ttlxj/userDrawInfo",
        headers: {
          bizchannelinfo: this.get_bizchannelinfo(),
          authinfo: this.get_epay_authinfo()
        }
      };

      const { result } = await this.request(requestConfig);
      const responseCode = appName.get(result, "code", -1);

      if (responseCode === "0000") {
        const dayOfWeek = result?.["data"]?.["dayOfWeek"];
        const drawKey = `day${dayOfWeek}`;
        const hasNotClockedIn = result?.["data"]?.[drawKey] === "1";

        const logOptions = {
          notify: true
        };

        this.log(`天天领现金: 今天${hasNotClockedIn ? "未" : "已"}打卡`, logOptions);

        if (options.isQueryOnly) {
          this.log("天天领现金: [查询模式] 跳过打卡操作");
          return;
        }

        if (hasNotClockedIn) {
          const today = new Date().getDay();
          const drawType = (today % 7 === 0) ? "C" : "B";
          await this.ttlxj_unifyDrawNew(drawType);
        }
      } else {
        const errorMessage = result?.["msg"] || "";
        this.log(`天天领现金: 查询失败[${responseCode}]: ${errorMessage}`);
      }
    } catch (error) {
      console.log(error);
    }
  }

  async ttlxj_unifyDrawNew(drawType, options = {}) {
    try {
      const requestData = {
        drawType: drawType,
        bizFrom: errorCode,
        activityId: "TTLXJ20210330"
      };

      const requestConfig = {
        fn: "ttlxj_unifyDrawNew",
        method: "post",
        url: "https://epay.10010.com/ci-mcss-party-front/v1/ttlxj/unifyDrawNew",
        headers: {
          bizchannelinfo: this.get_bizchannelinfo(),
          authinfo: this.get_epay_authinfo()
        },
        form: requestData
      };

      const { result } = await this.request(requestConfig);
      const responseCode = appName.get(result, "code", -1);

      if (responseCode === "0000" && result?.["data"]?.["returnCode"] === 0) {
        const awardMessage = result?.["data"]?.["awardTipContent"]?.replace(/xx/, result?.["data"]?.["amount"]);
        const logOptions = {
          notify: true
        };
        this.log("天天领现金: 打卡 " + awardMessage, logOptions);
      } else {
        const errorMessage = result?.["data"]?.["returnMsg"] || result?.["msg"] || "";
        this.log(`天天领现金: 打卡失败[${result?.["data"]?.["returnCode"] || responseCode}]: ${errorMessage}`);
      }
    } catch (error) {
      console.log(error);
    }
  }

  async ttlxj_help(options = {}) {
    try {
      const requestBody = {
        bizFrom: errorCode,
        activityId: activityIds.ttlxj,
        uid: apiKey
      };
      let requestConfig = {
        fn: "ttlxj_h",
        method: "post",
        url: "https://epay.10010.com/ci-mcss-party-front/v1/ttlxj/help",
        headers: {
          bizchannelinfo: this.get_bizchannelinfo(),
          authinfo: this.get_epay_authinfo()
        },
        form: requestBody
      };
      await this.request(requestConfig);
    } catch (error) {
      console.log(error);
    }
  }
  async ttlxj_queryAvailable(options = {}) {
    try {
      let requestConfig = {
        fn: "ttlxj_queryAvailable",
        method: "post",
        url: "https://epay.10010.com/ci-mcss-party-front/v1/ttlxj/queryAvailable",
        headers: {
          bizchannelinfo: this.get_bizchannelinfo(),
          authinfo: this.get_epay_authinfo()
        }
      };
      let {
        result: responseResult
      } = await this.request(requestConfig);
      let responseCode = appName.get(responseResult, "code", -1);
      if (responseCode == "0000" && responseResult?.["data"]?.["returnCode"] == 0) {
        let availableAmount = responseResult?.["data"]?.["availableAmount"] || 0;
        let logMessage = `天天领现金: 可用立减金: ${(availableAmount / 100).toFixed(2)}元`;
        let expiringPrizes = [];
        let currentTime = Date.now();
        for (let prize of responseResult?.["data"]?.["prizeList"]?.filter(p => p.status == "A")) {
          let endTimeStr = prize.endTime;
          let endTimeDate = new Date(endTimeStr.slice(0, 4) + "-" + endTimeStr.slice(4, 6) + "-" + endTimeStr.slice(6, 8) + " 00:00:00");
          let endTimeMs = endTimeDate.getTime();
          if (endTimeMs - currentTime < expiration_time * 24 * 60 * 60 * 1000) {
            let formattedDate = appName.time("yyyy-MM-dd", endTimeMs);
            const expiringPrize = {
              timestamp: endTimeMs,
              date: formattedDate,
              amount: prize.amount
            };
            expiringPrizes.push(expiringPrize);
          }
        }
        if (expiringPrizes.length) {
          const defaultPrize = {
            timestamp: 0,
            amount: 0
          };
          let earliestExpiringPrize = defaultPrize;
          let totalExpiringAmount = expiringPrizes.reduce(function (total, currentPrize) {
            if (earliestExpiringPrize.timestamp == 0 || currentPrize.timestamp < earliestExpiringPrize.timestamp) {
              earliestExpiringPrize = currentPrize;
            }
            return total + parseFloat(currentPrize.amount);
          }, 0);
          logMessage += `, ${expiration_time}天内过期立减金: ${totalExpiringAmount.toFixed(2)}元`;
          logMessage += `, 最早过期立减金: ${earliestExpiringPrize.amount}元 -- ${earliestExpiringPrize.date}过期`;
        } else {
          logMessage += `, ${expiration_time}天内没有过期的立减金`;
        }
        this.log(logMessage, { notify: true });
      } else {
        let errorMessage = responseResult?.["data"]?.["returnMsg"] || responseResult?.["msg"] || "";
        this.log("天天领现金: 查询可用立减金失败[" + (responseResult?.["data"]?.["returnCode"] || responseCode) + "]: " + errorMessage);
      }
    } catch (error) {
      console.log(error);
    }
  }

  async epay_28_authCheck(options = {}) {
    try {
      let requestConfig = {
        fn: "epay_28_authCheck",
        method: "post",
        url: "https://epay.10010.com/ps-pafs-auth-front/v1/auth/check",
        headers: {
          bizchannelinfo: this.get_bizchannelinfo()
        }
      };
      let {
        result: responseResult
      } = await this.request(requestConfig);
      let responseCode = appName.get(responseResult, "code", -1);
      if (responseCode == "0000") {
        let {
          mobile: mobile,
          sessionId: sessionId,
          tokenId: tokenId,
          userId: userId
        } = responseResult?.["data"]?.["authInfo"];
        const authInfo = {
          sessionId: sessionId,
          tokenId: tokenId,
          userId: userId
        };
        Object.assign(this, authInfo);
        await this.epay_28_queryUserPage();
      } else {
        if (responseCode == "2101000100") {
          let loginUrl = responseResult?.["data"]?.["woauth_login_url"];
          await this.epay_28_login(loginUrl);
        } else {
          let errorMessage = responseResult?.["msgInside"] || responseResult?.["msg"] || "";
          this.log("联通支付日获取tokenId失败[" + responseCode + "]: " + errorMessage);
        }
      }
    } catch (error) {
      console.log(error);
    }
  }
  async epay_28_login(loginUrl, options = {}) {
    try {
      let templateName = appName.time("yyyyMM") + "28ZFR";
      loginUrl += "https://epay.10010.com/ci-mcss-party-web/rainbow/?templateName=" + templateName + "&bizFrom=225&bizChannelCode=225&channelType=WDQB";
      const requestConfig = {
        fn: "epay_28_login",
        method: "get",
        url: loginUrl
      };
      let {
        headers: headers,
        statusCode: statusCode
      } = await this.request(requestConfig);
      if (headers?.["location"]) {
        let locationUrl = new URL(headers.location);
        this.rptId = locationUrl.searchParams.get("rptid");
        this.rptId ? await this.epay_28_authCheck() : this.log("联通支付日获取rptid失败");
      } else {
        this.log("联通支付日获取rptid失败[" + statusCode + "]");
      }
    } catch (error) {
      console.log(error);
    }
  }
  async epay_28_queryUserPage(options = {}) {
    try {
      let templateName = appName.time("yyyyMM") + "28ZFR";
      const requestBody = {
        templateName: templateName
      };
      let requestConfig = {
        fn: "epay_28_queryUserPage",
        method: "post",
        url: "https://epay.10010.com/ci-mcss-party-front/v1/rainbow/queryUserPage",
        headers: {
          bizchannelinfo: this.get_bizchannelinfo(),
          authinfo: this.get_epay_authinfo()
        },
        form: requestBody
      };
      let {
        result: responseResult
      } = await this.request(requestConfig);
      let responseCode = appName.get(responseResult, "code", -1);
      if (responseCode == "0000" && responseResult?.["data"]?.["returnCode"] == 0) {
        for (let prizeInfo of responseResult?.["data"]?.["prizeList"]?.["rainbowMouldInfos"] || []) {
          prizeInfo?.["rainbowUnitInfos"]?.[0]?.["unitActivityId"] && (await this.epay_28_unifyDraw(prizeInfo.rainbowUnitInfos[0]));
          if (prizeInfo?.["day01DrawParam"]) {
            await this.epay_28_queryMiddleUnit(templateName, prizeInfo.mouldName);
            break;
          }
        }
      } else {
        let errorMessage = responseResult?.["message"] || responseResult?.["msg"] || "";
        this.log("联通支付日进入主页失败[" + responseCode + "]: " + errorMessage);
      }
    } catch (error) {
      console.log(error);
    }
  }
  async epay_28_queryMiddleUnit(activityId, mouldName, options = {}) {
    try {
      const requestBody = {
        activityId: activityId,
        mouldName: mouldName
      };
      let requestConfig = {
        fn: "epay_28_queryMiddleUnit",
        method: "post",
        url: "https://epay.10010.com/ci-mcss-party-front/v1/rainbow/queryMiddleUnit",
        headers: {
          bizchannelinfo: this.get_bizchannelinfo(),
          authinfo: this.get_epay_authinfo()
        },
        form: requestBody
      };
      let {
        result: responseResult
      } = await this.request(requestConfig);
      let responseCode = appName.get(responseResult, "code", -1);
      if (responseCode == "0000") {
        let currentDay = appName.time("dd");
        responseResult?.["data"]?.[currentDay] == "1" ? this.log("联通支付日今日(" + currentDay + "号)已打卡") : await this.epay_28_unifyDrawNew(activityId, mouldName);
      } else {
        let errorMessage = responseResult?.["message"] || responseResult?.["msg"] || "";
        this.log("联通支付日查询打卡失败[" + responseCode + "]: " + errorMessage);
      }
    } catch (error) {
      console.log(error);
    }
  }
  async epay_28_unifyDrawNew(activityId, mouldName, options = {}) {
    try {
      const requestBody = {
        bizFrom: errorCode,
        activityId: activityId,
        mouldName: mouldName
      };
      let requestConfig = {
        fn: "epay_28_unifyDrawNew",
        method: "post",
        url: "https://epay.10010.com/ci-mcss-party-front/v1/rainbow/unifyDrawNew",
        headers: {
          bizchannelinfo: this.get_bizchannelinfo(),
          authinfo: this.get_epay_authinfo()
        },
        form: requestBody
      };
      let {
        result: responseResult
      } = await this.request(requestConfig);
      let responseCode = appName.get(responseResult, "code", -1);
      if (responseCode == "0000" && responseResult?.["data"]?.["returnCode"] == 0) {
        let awardMessage = responseResult?.["data"]?.["awardTipContent"]?.replace(/xx/, responseResult?.["data"]?.["amount"]);
        const notifyOptions = {
          notify: true
        };
        this.log("联通支付日打卡:" + awardMessage, notifyOptions);
      } else {
        let errorMessage = responseResult?.["data"]?.["returnMsg"] || responseResult?.["msg"] || "";
        this.log("联通支付日打卡失败[" + (responseResult?.["data"]?.["returnCode"] || responseCode) + "]: " + errorMessage);
      }
    } catch (error) {
      console.log(error);
    }
  }
  async epay_28_unifyDraw(unitInfo, options = {}) {
    try {
      const requestBody = {
        activityId: unitInfo.unitActivityId,
        isBigActivity: unitInfo.isBigActivity,
        bigActivityId: unitInfo.bigActivityId,
        bizFrom: errorCode
      };
      let requestConfig = {
        fn: "epay_28_unifyDraw",
        method: "post",
        url: "https://epay.10010.com/ci-mcss-party-front/v1/rainbow/unifyDraw",
        headers: {
          bizchannelinfo: this.get_bizchannelinfo(),
          authinfo: this.get_epay_authinfo()
        },
        form: requestBody
      };
      let {
        result: responseResult
      } = await this.request(requestConfig);
      let responseCode = appName.get(responseResult, "code", -1);
      if (responseCode == "0000" && responseResult?.["data"]?.["returnCode"] == 0) {
        const notifyOptions = {
          notify: true
        };
        this.log("联通支付日抽奖: " + (responseResult?.["data"]?.["prizeName"] || ""), notifyOptions);
      } else {
        let errorMessage = responseResult?.["data"]?.["returnMsg"] || responseResult?.["msg"] || "";
        this.log("联通支付日抽奖失败[" + (responseResult?.["data"]?.["returnCode"] || responseCode) + "]: " + errorMessage);
      }
    } catch (error) {
      console.log(error);
    }
  }
  async appMonth_28_bind(shareCode, options = {}) {
    try {
      const requestBody = {
        shareCode: shareCode,
        cl: "WeChat"
      };
      const requestConfig = {
        fn: "appMonth_28_bind",
        method: "post",
        url: "https://activity.10010.com/AppMonthly/appMonth/bind",
        form: requestBody,
        valid_code: [401]
      };
      let {
        result: responseResult
      } = await this.request(requestConfig);
    } catch (error) {
      console.log(error);
    }
  }
  async appMonth_28_queryChance(params = {}) {
    try {
      const requestConfig = {
        fn: "appMonth_28_queryChance",
        method: "post",
        url: "https://activity.10010.com/AppMonthly/appMonth/queryChance"
      };

      let {
        result: response
      } = await this.request(requestConfig),
        status = appName.get(response, "status", -1);

      if (status == "0000") {
        let {
          allRemainTimes: remainingTimes,
          isUnicom: isUnicomUser
        } = response?.["data"];

        if (isUnicomUser) {
          let drawTimes = Math.min(appMonth_28_MaxTimes, remainingTimes);
          this.log("联通支付日可以开宝箱" + remainingTimes + "次, 去抽" + drawTimes + "次");

          while (drawTimes-- > 0) {
            await this.appMonth_28_lottery();
          }
        }
      } else {
        let errorMsg = response?.["msg"] || "";
        this.log("联通支付日查询开宝箱次数失败[" + status + "]: " + errorMsg);
      }
    } catch (error) {
      console.log(error);
    }
  }

  async appMonth_28_lottery(options = {}) {
    try {
      const requestConfig = {
        fn: "appMonth_28_lottery",
        method: "post",
        url: "https://activity.10010.com/AppMonthly/appMonth/lottery"
      };
      let {
        result: responseResult
      } = await this.request(requestConfig),
        status = appName.get(responseResult, "status", -1);
      if (status == "0000") {
        let {
          code: resultCode,
          uuid: uuid
        } = responseResult?.["data"];
        uuid ? await this.appMonth_28_winningRecord(uuid) : this.log("联通支付日开宝箱失败[" + resultCode + "]");
      } else {
        let errorMessage = responseResult?.["msg"] || "";
        this.log("联通支付日开宝箱失败[" + status + "]: " + errorMessage);
      }
    } catch (error) {
      console.log(error);
    }
  }
  async appMonth_28_winningRecord(requestId, options = {}) {
    try {
      const requestBody = {
        requestId: requestId
      };
      const requestConfig = {
        fn: "appMonth_28_winningRecord",
        method: "post",
        url: "https://activity.10010.com/AppMonthly/appMonth/winningRecord",
        form: requestBody
      };
      let {
        result: responseResult
      } = await this.request(requestConfig),
        status = appName.get(responseResult, "status", -1);
      if (status == "0000") {
        let {
          code: resultCode,
          prizeName: prizeName
        } = responseResult?.["data"];
        if (resultCode == "0000") {
          const notifyOptions = {
            notify: true
          };
          this.log("联通支付日开宝箱: " + prizeName, notifyOptions);
        } else {
          let errorMessage = responseResult?.["data"]?.["message"] || "";
          this.log("联通支付日开宝箱[" + resultCode + "]: " + errorMessage);
        }
      } else {
        let errorMessage = responseResult?.["msg"] || "";
        this.log("联通支付日查询中奖奖品错误[" + status + "]: " + errorMessage);
      }
    } catch (error) {
      console.log(error);
    }
  }
  // 签到区相关方法
  async sign_getContinuous(imei, options = {}) {
    try {
      const requestConfig = {
        fn: "sign_getContinuous",
        method: "get",
        url: "https://activity.10010.com/sixPalaceGridTurntableLottery/signin/getContinuous",
        params: {
          taskId: "",
          channel: "wode",
          imei: imei
        }
      };
      let { result: responseResult } = await this.request(requestConfig),
        responseCode = appName.get(responseResult, "code", -1);

      if (responseCode == "0000") {
        let todayIsSignIn = responseResult?.["data"]?.["todayIsSignIn"] || 'n';
        this.log("签到区今天" + (todayIsSignIn == "n" ? "未" : "已") + "签到", { notify: true });
        if (todayIsSignIn == "n") {
          await appName.wait(1000);
          await this.sign_daySign();
        }
      } else {
        this.log("签到区查询签到状态失败[" + responseCode + "]: " + (responseResult?.["desc"] || ""));
      }
    } catch (error) {
      console.log(error);
    }
  }

  async sign_daySign(options = {}) {
    try {
      const requestConfig = {
        fn: "sign_daySign",
        method: "post",
        url: "https://activity.10010.com/sixPalaceGridTurntableLottery/signin/daySign",
        form: {}
      };
      let { result: responseResult } = await this.request(requestConfig),
        responseCode = appName.get(responseResult, "code", -1);

      if (responseCode == "0000") {
        let { statusDesc: statusDesc, redSignMessage: redSignMessage } = responseResult?.["data"];
        let logMessage = "签到区签到成功: ";
        if (statusDesc) logMessage += `[${statusDesc}]`;
        if (redSignMessage) logMessage += `${redSignMessage}`;
        this.log(logMessage);
      } else if (responseCode == "0002" && responseResult?.["desc"] && responseResult["desc"].includes('已经签到')) { // 今日已签到
        this.log("签到区签到成功: 今日已完成签到！");
      } else {
        this.log("签到区签到失败[" + responseCode + "]: " + (responseResult?.["desc"] || ""));
      }
    } catch (error) {
      console.log(error);
    }
  }

  async sign_getTaskReward(taskId, options = {}) {
    try {
      const requestConfig = {
        fn: "sign_getTaskReward",
        method: "get",
        url: "https://activity.10010.com/sixPalaceGridTurntableLottery/task/getTaskReward",
        searchParams: {
          taskId: taskId
        }
      };
      let { result: responseResult } = await this.request(requestConfig);
      let responseCode = appName.get(responseResult, "code", -1);

      if (responseCode == "0000") {
        let data = responseResult?.["data"];
        if (data?.code == '0000') {
          let prizeName = data?.prizeName || '';
          let prizeNameRed = data?.prizeNameRed || '';
          this.log(`签到区-领取奖励: [${prizeName}] ${prizeNameRed}`);
        } else {
          this.log("签到区-领取奖励失败[" + data?.code + "]: " + (responseResult?.["desc"] || data?.desc || ""));
        }
      } else {
        this.log("签到区-领取奖励失败[" + responseCode + "]: " + (responseResult?.["desc"] || ""));
      }
    } catch (error) {
      console.log(error);
    }
  }

  async sign_getTelephone(options = {}) {
    try {
      const requestConfig = {
        fn: "sign_getTelephone",
        method: "post",
        url: "https://act.10010.com/SigninApp/convert/getTelephone",
        form: {}
      };
      let { result: responseResult } = await this.request(requestConfig);
      let status = appName.get(responseResult, "status", -1);

      if (status == "0000" && responseResult.data) {
        const currentAmount = parseFloat(responseResult.data.telephone) || 0;

        if (options.isInitial) {
          this.initialTelephoneAmount = currentAmount;
          this.log(`签到区-话费红包: 运行前总额 ${this.initialTelephoneAmount.toFixed(2)}元`, { notify: true });
          return;
        }

        if (this.initialTelephoneAmount !== null) {
          const increase = currentAmount - this.initialTelephoneAmount;
          this.log(`签到区-话费红包: 本次运行增加 ${increase.toFixed(2)}元`, { notify: true });
        }

        let totalMessage = `签到区-话费红包: 总额 ${currentAmount.toFixed(2)}元`;
        if (parseFloat(responseResult.data.needexpNumber) > 0) {
          totalMessage += `，其中 ${responseResult.data.needexpNumber}元 将于 ${responseResult.data.month}月底到期`;
        }
        this.log(totalMessage, { notify: true });

      } else {
        this.log(`签到区查询话费红包失败[${status}]: ${responseResult?.msg || ""}`);
      }
    } catch (error) {
      this.log(`签到区查询话费红包异常: ${error.message}`);
    }
  }

  async sign_getTaskList(options = {}) {
    try {
      const requestConfig = {
        fn: "sign_getTaskList",
        method: "get",
        url: "https://activity.10010.com/sixPalaceGridTurntableLottery/task/taskList",
        searchParams: { type: 2 },
        headers: { "Referer": "https://img.client.10010.com/" }
      };

      // 【修改 1】：将 30 改为 3 或 5 (减少尝试次数)
      for (let i = 0; i < 3; i++) {
        let { result: responseResult } = await this.request(requestConfig);
        let responseCode = appName.get(responseResult, "code", -1);
        // 如果遇到火爆(0329)或系统繁忙，直接跳出循环，不再浪费时间
        if (responseCode == "0329" || (responseResult?.desc && responseResult.desc.includes("火爆"))) {
          this.log("签到区: 系统繁忙(0329)，停止后续尝试");
          break;
        }

        if (responseCode != "0000") {
          this.log("签到区-任务中心: 获取任务列表失败[" + responseCode + "]: " + (responseResult?.desc || ""));
          return;
        }

        if (i === 0) {
          this.log("签到区-任务中心: 获取任务列表成功");
        }

        const allTasks = [
          ...(responseResult.data.tagList || []).flatMap(tag => tag.taskDTOList || []),
          ...(responseResult.data.taskList || [])
        ].filter(Boolean);

        if (allTasks.length === 0) {
          if (i === 0) this.log("签到区-任务中心: 当前无任何任务。");
          break; // Exit loop if no tasks
        }

        // Priority 1: Execute actionable tasks (taskState: 1 and taskType: 5).
        const doTask = allTasks.find(task => task.taskState === "1" && task.taskType === "5");
        if (doTask) {
          this.log(`签到区-任务中心: 开始执行任务 [${doTask.taskName}]`);
          await this.sign_doTaskFromList(doTask);
          await appName.wait(3000);
          continue; // Re-fetch task list, as the completed task might now be claimable.
        }

        // Priority 2: Claim rewards for completed tasks (taskState: 0).
        const claimTask = allTasks.find(task => task.taskState === "0");
        if (claimTask) {
          this.log(`签到区-任务中心: 发现可领取奖励的任务 [${claimTask.taskName}]`);
          await this.sign_getTaskReward(claimTask.id);
          await appName.wait(2000);
          continue; // Re-fetch task list to get the next state.
        }

        // If we are here, no claimable or actionable tasks were found in this iteration.
        if (i === 0) {
          this.log("签到区-任务中心: 没有可执行或可领取的任务。");
        } else {
          this.log("签到区-任务中心: 所有任务处理完毕。");
        }
        break; // Exit the loop
      }

    } catch (error) {
      console.log(error);
      this.log("签到区-任务中心: 获取任务列表时发生异常: " + error.message);
    }
  }

  async sign_doTaskFromList(task, options = {}) {
    try {
      // this.log(`签到区-任务中心: 开始执行任务 [${task.taskName}]`);

      if (task.url && task.url !== "1" && task.url.startsWith("http")) {
        await this.request({
          fn: "sign_doTaskFromList_visit",
          method: "get",
          url: task.url,
          headers: {
            "Referer": "https://img.client.10010.com/"
          }
        });
        this.log(`签到区-任务中心: 浏览页面 [${task.taskName}]`);
        await appName.wait(5000 + Math.random() * 2000);
      }

      const orderId = await this.gettaskip();

      const requestConfig = {
        fn: "sign_doTaskFromList_complete",
        method: "get",
        url: "https://activity.10010.com/sixPalaceGridTurntableLottery/task/completeTask",
        searchParams: {
          taskId: task.id,
          orderId: orderId,
          systemCode: "QDQD"
        }
      };

      let { result: responseResult } = await this.request(requestConfig);
      let responseCode = appName.get(responseResult, "code", -1);

      if (responseCode == "0000") {
        this.log(`签到区-任务中心: ✅ 任务 [${task.taskName}] 已完成`);
      } else {
        this.log(`签到区-任务中心: ❌ 任务 [${task.taskName}] 完成失败[${responseCode}]: ${responseResult.desc || '未知错误'}`);
      }

    } catch (error) {
      console.log(error);
      this.log(`签到区-任务中心: 执行任务 [${task.taskName}] 时发生异常: ${error.message}`);
    }
  }

  async flmf_login(loginUrl, options = {}) {
    try {
      const requestConfig = {
        fn: "flmf_login",
        method: "get",
        url: loginUrl
      };
      let {
        headers: headers,
        statusCode: statusCode
      } = await this.request(requestConfig);
      if (headers?.["location"]) {
        let locationUrl = new URL(headers.location);
        this.flmf_sid = locationUrl.searchParams.get("sid");
        this.flmf_sid ? (await this.flmf_signInInit(), await this.flmf_taskList(), await this.flmf_scanTask()) : this.log("福利魔方获取sid失败");
      } else {
        this.log("福利魔方获取sid失败[" + statusCode + "]");
      }
    } catch (error) {
      console.log(error);
    }
  }
  async flmf_signInInit(options = {}) {
    try {
      let requestConfig = {
        fn: "flmf_signInInit",
        method: "post",
        url: "https://weixin.linktech.hk/lv-apiaccess/welfareCenter/signInInit",
        form: this.get_flmf_data()
      };
      let {
        result: responseResult
      } = await this.request(requestConfig);
      let resultCode = appName.get(responseResult, "resultCode", -1);
      if (resultCode == "0000") {
        this.log("福利魔方今天" + (responseResult?.["data"]?.["isSigned"] ? "已" : "未") + "签到, 已连续签到" + responseResult?.["data"]?.["consecutiveDays"] + "天");
        if (!responseResult?.["data"]?.["isSigned"]) {
          await this.flmf_signIn();
        }
      } else {
        let errorMessage = responseResult?.["resultMsg"] || "";
        this.log("福利魔方查询签到失败[" + resultCode + "]: " + errorMessage);
      }
    } catch (error) {
      console.log(error);
    }
  }
  async flmf_signIn(options = {}) {
    try {
      let requestConfig = {
        fn: "flmf_signIn",
        method: "post",
        url: "https://weixin.linktech.hk/lv-apiaccess/welfareCenter/signIn",
        form: this.get_flmf_data()
      };
      let {
        result: responseResult
      } = await this.request(requestConfig);
      let resultCode = appName.get(responseResult, "resultCode", -1);
      if (resultCode == "0000") {
        this.log("福利魔方签到成功");
      } else {
        let errorMessage = responseResult?.["resultMsg"] || "";
        this.log("福利魔方签到失败[" + resultCode + "]: " + errorMessage);
      }
    } catch (error) {
      console.log(error);
    }
  }
  async flmf_taskList(options = {}) {
    try {
      let requestConfig = {
        fn: "flmf_taskList",
        method: "post",
        url: "https://weixin.linktech.hk/lv-apiaccess/welfareCenter/taskList",
        form: this.get_flmf_data()
      };
      let {
        result: responseResult
      } = await this.request(requestConfig);
      let resultCode = appName.get(responseResult, "resultCode", -1);
      if (resultCode == "0000") {
        for (let taskGroup of responseResult?.["data"]?.["taskInfoList"]) {
          for (let task of taskGroup.taskInfoList.filter(t => !t.done)) {
            for (let i = task.hascount; i < task.count; i++) {
              await this.flmf_gogLance(task.id);
            }
          }
        }
      } else {
        let errorMessage = responseResult?.["resultMsg"] || "";
        this.log("福利魔方查询任务失败[" + resultCode + "]: " + errorMessage);
      }
    } catch (error) {
      console.log(error);
    }
  }
  async flmf_scanTask() {
    for (let taskId of someArray) {
      await this.flmf_gogLance(taskId);
    }
  }
  async flmf_gogLance(taskId, options = {}) {
    try {
      let requestConfig = {
        fn: "flmf_gogLance",
        method: "post",
        url: "https://weixin.linktech.hk/lv-apiaccess/welfareCenter/gogLance",
        form: {
          taskId: taskId,
          ...this.get_flmf_data()
        }
      };
      let {
        result: responseResult
      } = await this.request(requestConfig);
      await appName.wait_gap_interval(this.t_flmf_task, delayMs);
      let resultCode = appName.get(responseResult, "resultCode", -1);
      this.t_flmf_task = Date.now();
      if (resultCode == "0000") {
        this.log("完成任务[" + taskId + "]成功");
      } else {
        let errorMessage = responseResult?.["resultMsg"] || "";
        this.log("完成任务[" + taskId + "]失败[" + resultCode + "]: " + errorMessage);
      }
    } catch (error) {
      console.log(error);
    }
  }

  // ============================================
  // 联通阅读 NEW LOGIC START (移植自Python脚本)
  // ============================================

  // 1. 设备预登录 (获取accesstoken)
  async woread_auth(options = {}) {
    let authSuccess = false;
    try {
      // Python: timestamp = round(time() * 1000)
      let timestamp = Date.now();
      // Python: md5(f'100000027k1HcDL8RKvc{timestamp}')
      let signStr = productId + secretKey + timestamp;
      let md5Hash = cryptoJS.MD5(signStr).toString();

      // Python: crypt_text = f'{{"timestamp":"{self.date}"}}'
      // self.date format: %Y%m%d%H%M%S
      let dateStr = appName.time("yyyyMMddhhmmss");
      let cryptTextObj = { timestamp: dateStr };

      // encrypt using AES (key="woreadst^&*12345")
      let encodedSign = this.encode_woread(cryptTextObj);

      const requestOptions = {
        fn: "woread_auth",
        method: "post",
        url: `https://10010.woread.com.cn/ng_woread_service/rest/app/auth/${productId}/${timestamp}/${md5Hash}`,
        json: { sign: encodedSign }
      };

      let { result: responseData } = await this.request(requestOptions);
      let responseCode = appName.get(responseData, "code", -1);

      if (responseCode == "0000") {
        authSuccess = true;
        this.woread_accesstoken = responseData?.["data"]?.["accesstoken"];
        // 设置Header中的accesstoken
        this.got = this.got.extend({ headers: { accesstoken: this.woread_accesstoken } });
        // this.log("阅读专区: 设备认证成功");
      } else {
        let errorMessage = responseData?.["message"] || "";
        this.log("阅读专区: 设备认证失败[" + responseCode + "]: " + errorMessage);
      }
    } catch (error) {
      console.log(error);
      this.log("阅读专区: 设备认证异常：" + error.message);
    } finally {
      return authSuccess;
    }
  }

  // 2. 账号登录 (使用token_online)
  async woread_login(options = {}) {
    let loginSuccess = false;
    try {
      // 1. 确保设备认证已完成
      if (!this.woread_accesstoken) {
        if (!await this.woread_auth()) return false;
      }

      // 2. 构造加密参数
      if (!this.token_online) {
        this.log("阅读专区: 缺少 token_online，无法进行新版登录");
        return false;
      }

      let token_enc = this.encode_woread_str(this.token_online);
      // 使用当前手机号，如果没获取到则用默认占位符
      let phone_str = this.mobile || "13800000000";
      let phone_enc = this.encode_woread_str(phone_str);
      let timestamp = appName.time("yyyyMMddhhmmss");

      // 构造内层JSON字符串: crypt_text
      let innerJson = JSON.stringify({
        tokenOnline: token_enc,
        phone: phone_enc,
        timestamp: timestamp
      });

      // 3. 对内层JSON再次加密生成sign
      let encodedSign = this.encode_woread_str(innerJson);

      const requestOptions = {
        fn: "woread_login",
        method: "post",
        url: "https://10010.woread.com.cn/ng_woread_service/rest/account/login",
        json: { sign: encodedSign }
      };

      let { result: responseData } = await this.request(requestOptions);
      let responseCode = appName.get(responseData, "code", -1);

      if (responseCode === "0000") {
        loginSuccess = true;
        let { userid, userindex, token, verifycode, phone } = responseData?.["data"];
        this.woread_token = token;
        this.woread_verifycode = verifycode;
        this.woread_userid = userid;
        this.woread_userindex = userindex;

        // 如果返回了真实手机号，更新它
        if (phone) {
          this.mobile = phone;
          this.name = phone; // Update display name
        }

        this.log(`阅读专区: 登录成功`);
      } else {
        let errorMessage = responseData?.["message"] || responseData?.["msg"] || "未知错误";
        this.log(`阅读专区: 登录失败[${responseCode}]: ${errorMessage}`);
      }
    } catch (error) {
      console.log(error);
      this.log("阅读专区: 登录异常：" + error.message);
    } finally {
      return loginSuccess;
    }
  }

  // 3. 获取书籍信息
  async woread_get_book_info() {
    try {
      // 1. 获取推荐位信息得到 cntindex
      let url1 = "https://10010.woread.com.cn/ng_woread_service/rest/basics/recommposdetail/14856";
      let { result: res1 } = await this.request({ fn: "woread_book", method: "get", url: url1 });

      if (res1?.code === '0000') {
        this.wr_catid = res1.data.booklist.message[0].catindex;
        this.wr_cardid = res1.data.bindinfo[0].recommposiindex;
        this.wr_cntindex = res1.data.booklist.message[0].cntindex;
      } else {
        this.log("阅读专区: 获取书籍列表失败");
        return false;
      }

      // 2. 获取章节信息得到 chapterallindex
      if (!this.wr_cntindex) return false;

      let param = {
        curPage: 1, limit: 30, index: this.wr_cntindex, sort: 0, finishFlag: 1,
        ...this.get_woread_param()
      };
      let sign = this.encode_woread(param);

      let url2 = "https://10010.woread.com.cn/ng_woread_service/rest/cnt/chalist";
      let { result: res2 } = await this.request({
        fn: "woread_chap", method: "post", url: url2, json: { sign }
      });

      if (res2?.list && res2.list.length > 0) {
        this.wr_chapterallindex = res2.list[0].charptercontent[0].chapterallindex;
        this.wr_chapterid = res2.list[0].charptercontent[0].chapterid;
        return true;
      }
      return false;

    } catch (e) {
      this.log("阅读专区: 获取书籍信息异常");
      return false;
    }
  }

  // 4. 阅读模拟 (日志修正版)
  async woread_read_process() {
    if (!await this.woread_get_book_info()) {
      this.log("阅读专区: 无法获取书籍信息，跳过阅读");
      return;
    }

    // 循环1次
    let loopCount = 1;

    for (let i = 0; i < loopCount; i++) {
      try {
        // 4.1 发送阅读心跳 wordsDetail
        let param = {
          chapterAllIndex: this.wr_chapterallindex,
          cntIndex: this.wr_cntindex,
          cntTypeFlag: "1",
          ...this.get_woread_param()
        };
        let sign = this.encode_woread(param);

        // 仅仅发送心跳，不判断结果，直接进行下一步
        await this.request({
          fn: "woread_heartbeat",
          method: "post",
          url: `https://10010.woread.com.cn/ng_woread_service/rest/cnt/wordsDetail?catid=${this.wr_catid}&cardid=${this.wr_cardid}&cntindex=${this.wr_cntindex}&chapterallindex=${this.wr_chapterallindex}&chapterseno=1`,
          json: { sign }
        });

        // 4.2 增加阅读时长 addReadTime
        let addParam = {
          readTime: "2",
          cntIndex: this.wr_cntindex,
          cntType: "1",
          catid: "0",
          pageIndex: "",
          cardid: this.wr_cardid,
          cntindex: this.wr_cntindex,
          cnttype: "1",
          chapterallindex: this.wr_chapterallindex,
          chapterseno: "1",
          channelid: "",
          chapterid: this.wr_chapterid,
          readtype: 1,
          isend: "0",
          ...this.get_woread_param()
        };
        let addSign = this.encode_woread(addParam);

        let { result: addRes } = await this.request({
          fn: "woread_addTime",
          method: "post",
          url: "https://10010.woread.com.cn/ng_woread_service/rest/history/addReadTime",
          json: { sign: addSign }
        });

        let addResObj = addRes;
        if (typeof addRes === 'string') {
          try { addResObj = JSON.parse(addRes); } catch (e) { }
        }

        // ==========================================
        // 【重点修改】日志显示逻辑
        // ==========================================
        if (addResObj?.code === '0000') {
          this.log(`阅读专区: 模拟阅读成功`);
        } else if (addResObj?.code === '9999' || (addResObj?.message && addResObj.message.includes("不存在阅读记录"))) {
          // 只要捕获到 9999，不管 JSON 长啥样，统一显示下面这句话
          this.log(`阅读专区: 模拟阅读失败 (需手动在APP打开任意一本书以初始化记录)`);
        } else {
          let errMsg = addResObj?.msg || addResObj?.message || JSON.stringify(addRes);
          this.log(`阅读专区: 模拟阅读失败: ${errMsg}`);
        }

        await appName.wait(2000);

      } catch (e) {
        console.log(e);
        this.log(`阅读专区: 阅读过程异常: ${e.message}`);
      }
    }
  }

  // 5. 新版抽奖 (修改版：全通知)
  async woread_draw_new() {
    try {
      let param = {
        activeindex: "8051",
        ...this.get_woread_param()
      };
      let sign = this.encode_woread(param);

      let { result: res } = await this.request({
        fn: "woread_draw",
        method: "post",
        url: "https://10010.woread.com.cn/ng_woread_service/rest/basics/doDraw",
        json: { sign }
      });

      if (res?.code === '0000') {
        // 成功中奖 -> 推送通知
        let prize = res.data?.prizedesc || res.data?.prizeName || "未知奖品";
        this.log(`阅读专区: 抽奖成功: ${prize}`, { notify: true });
      } else {
        // 失败/次数限制/未中奖 -> 推送通知
        // 这里的 errMsg 会包含 "用户参与该活动总次数已经超过限制" 等信息
        let errMsg = res?.msg || res?.message || JSON.stringify(res);
        this.log(`阅读专区: 抽奖失败: ${errMsg}`, { notify: true });
      }
    } catch (e) {
      // 异常情况也建议推送
      this.log(`阅读专区: 抽奖异常: ${e.message}`, { notify: true });
    }
  }

  async woread_queryTicketAccount(options = {}) {
    try {
      let requestParams = this.get_woread_param(),
        encodedSign = this.encode_woread(requestParams);
      const signData = {
        sign: encodedSign
      };
      const requestOptions = {
        fn: "woread_queryTicketAccount",
        method: "post",
        url: "https://10010.woread.com.cn/ng_woread_service/rest/phone/vouchers/queryTicketAccount",
        json: signData
      };
      let {
        result: responseData
      } = await this.request(requestOptions),
        responseCode = appName.get(responseData, "code", -1);
      if (responseCode == "0000") {
        let balance = (responseData?.["data"]?.["usableNum"] / 100).toFixed(2);
        const notifyOptions = {
          notify: true
        };
        this.log("阅读区话费红包余额: " + balance, notifyOptions);
      } else {
        let errorMessage = responseData?.["message"] || "";
        this.log("查询阅读区话费红包余额失败[" + responseCode + "]: " + errorMessage);
      }
    } catch (error) {
      console.log(error);
    }
  }

  // ============================================
  // 联通阅读 NEW LOGIC END
  // ============================================

  async act_517_userAccount(options = {}) {
    try {
      const requestOptions = {
        fn: "act_517_userAccount",
        method: "get",
        url: "https://activity.10010.com/2024517charges/lottery/userAccount"
      };
      {
        let {
          result: responseResult,
          statusCode: responseStatus
        } = await this.request(appName.copy(requestOptions));
        let responseCode = appName.get(responseResult, "code", responseStatus);
        if (responseCode == "0000") {
          await this.act_517_taskList();
        } else {
          let errorMessage = responseResult?.["message"] || responseResult?.["msg"] || "";
          this.log("517活动进入主页失败[" + responseCode + "]: " + errorMessage);
          return;
        }
      }
      {
        let {
          result: responseResult,
          statusCode: responseStatus
        } = await this.request(appName.copy(requestOptions));
        let responseCode = appName.get(responseResult, "code", responseStatus);
        if (responseCode == "0000") {
          let {
            chances: chances
          } = responseResult?.["data"];
          this.log("517活动可以抽奖" + chances + "次");
          let isFirstDraw = false;
          while (chances-- > 0) {
            if (isFirstDraw) {
              await appName.wait(3000);
            }
            isFirstDraw = true;
            await this.act_517_lottery();
          }
        } else {
          let errorMessage = responseResult?.["message"] || responseResult?.["msg"] || "";
          this.log("517活动查询抽奖次数失败[" + responseCode + "]: " + errorMessage);
        }
      }
      {
        let {
          result: responseResult,
          statusCode: responseStatus
        } = await this.request(appName.copy(requestOptions));
        let responseCode = appName.get(responseResult, "code", responseStatus);
        if (responseCode == "0000") {
          let {
            amount: amount,
            targetAmount: targetAmount
          } = responseResult?.["data"];
          const notifyOptions = {
            notify: true
          };
          this.log("517活动现金进度: " + amount + "/" + targetAmount, notifyOptions);
        } else {
          let errorMessage = responseResult?.["message"] || responseResult?.["msg"] || "";
          this.log("517活动查询进度失败[" + responseCode + "]: " + errorMessage);
        }
      }
    } catch (error) {
      console.log(error);
    }
  }
  async act_517_bind(shareCode, options = {}) {
    try {
      const requestOptions = {
        fn: "act_517_bind",
        method: "post",
        url: "https://activity.10010.com/2024517charges/openWindows/bind",
        json: {},
        valid_code: [401]
      };
      requestOptions.json.shareCode = shareCode;
      requestOptions.json.channel = "countersign";
      let {
        result: responseResult
      } = await this.request(requestOptions);
    } catch (error) {
      console.log(error);
    }
  }
  async act_517_lottery(options = {}) {
    try {
      const requestOptions = {
        fn: "act_517_lottery",
        method: "get",
        url: "https://activity.10010.com/2024517charges/lottery/lottery"
      };
      let {
        result: responseResult,
        statusCode: responseStatus
      } = await this.request(requestOptions);
      let responseCode = appName.get(responseResult, "code", responseStatus);
      if (responseCode == "0000") {
        responseResult?.["data"]?.["uuid"] ? (await appName.wait(2000), await this.act_517_winningRecord(responseResult.data.uuid)) : this.log("517活动抽奖失败, 没有返回uuid");
      } else {
        let errorMessage = responseResult?.["message"] || responseResult?.["msg"] || "";
        this.log("517活动抽奖失败[" + responseCode + "]: " + errorMessage);
      }
    } catch (error) {
      console.log(error);
    }
  }
  async act_517_winningRecord(requestId, options = {}) {
    try {
      const searchParams = {
        requestId: requestId
      };
      const requestOptions = {
        fn: "act_517_winningRecord",
        method: "get",
        url: "https://activity.10010.com/2024517charges/lottery/winningRecord",
        searchParams: searchParams
      };
      let {
        result: responseResult,
        statusCode: responseStatus
      } = await this.request(requestOptions);
      let responseCode = appName.get(responseResult, "code", responseStatus);
      if (responseCode == "0000") {
        if (responseResult?.["data"]?.["isWin"] === "1") {
          let {
            prizeAmount: prizeAmount,
            prizeList: prizeList,
            afterAmount: afterAmount,
            targetAmount: targetAmount,
            showAmount = "0"
          } = responseResult?.["data"],
            prizeNames = (prizeList || []).filter(p => p.prizeName).map(p => p.prizeName).join(", ") || "";
          const notifyOptions = {
            notify: true
          };
          if (prizeNames) {
            this.log("517活动抽奖: " + prizeNames, notifyOptions);
          }
          if (showAmount === "1") {
            this.log("517活动抽奖现金进度: +" + prizeAmount + " (" + afterAmount + "/" + targetAmount + ")");
          }
        } else {
          this.log("517活动抽奖: 空气");
        }
      } else {
        let errorMessage = responseResult?.["message"] || responseResult?.["msg"] || "";
        this.log("查询517活动抽奖结果失败[" + responseCode + "]: " + errorMessage);
      }
    } catch (error) {
      console.log(error);
    }
  }
  async act_517_taskList(options = {}) {
    try {
      const requestOptions = {
        fn: "act_517_taskList",
        method: "get",
        url: "https://activity.10010.com/2024517charges/dotask/taskList"
      };
      let {
        result: responseResult,
        statusCode: responseStatus
      } = await this.request(requestOptions);
      let responseCode = appName.get(responseResult, "code", responseStatus);
      if (responseCode == "0000") {
        let taskList = responseResult?.["data"]?.["taskList"] || [];
        for (let task of taskList) {
          let {
            completeNum = 0,
            maxNum: maxNum,
            isComplete: isComplete,
            taskType: taskType
          } = task;
          if (isComplete) {
            continue;
          }
          if (taskType == "5") {
            continue;
          }
          completeNum = parseInt(completeNum);
          maxNum = parseInt(maxNum);
          for (let i = completeNum; i < maxNum; i++) {
            await this.act_517_completeTask(task);
          }
        }
      } else {
        let errorMessage = responseResult?.["message"] || responseResult?.["msg"] || "";
        this.log("查询517活动抽奖结果失败[" + responseCode + "]: " + errorMessage);
      }
    } catch (error) {
      console.log(error);
    }
  }
  async act_517_completeTask(task, options = {}) {
    try {
      let taskTitle = task.title;
      const searchParams = {
        taskId: task.taskId
      };
      const requestOptions = {
        fn: "act_517_completeTask",
        method: "get",
        url: "https://activity.10010.com/2024517charges/dotask/completeTask",
        searchParams: searchParams
      };
      let {
        result: responseResult,
        statusCode: responseStatus
      } = await this.request(requestOptions);
      let responseCode = appName.get(responseResult, "code", responseStatus);
      if (responseCode == "0000") {
        if (responseResult?.["data"]) {
          let {
            num: num,
            title: title
          } = responseResult.data;
          this.log("完成任务[" + title + "]成功: " + num + "次抽奖机会");
        } else {
          this.log("完成任务[" + taskTitle + "]失败没有获得抽奖机会");
        }
      } else {
        let errorMessage = responseResult?.["message"] || responseResult?.["msg"] || "";
        this.log("完成任务[" + taskTitle + "]失败[" + responseCode + "]: " + errorMessage);
      }
    } catch (error) {
      console.log(error);
    }
  }

  get_wocare_body(apiCode, requestData = {}) {
    const timestamp = appName.time("yyyyMMddhhmmssS"),
      encodedContent = Buffer.from(JSON.stringify(requestData)).toString("base64");
    let body = {
      version: minRetries,
      apiCode: apiCode,
      channelId: anotherApiKey,
      transactionId: timestamp + appName.randomString(6, numbers),
      timeStamp: timestamp,
      messageContent: encodedContent
    },
      paramsArray = [];
    Object.keys(body).sort().forEach(key => {
      paramsArray.push(key + "=" + body[key]);
    });
    paramsArray.push("sign=" + anotherEncryptionKey);
    body.sign = cryptoJS.MD5(paramsArray.join("&")).toString();
    return body;
  }
  async wocare_api(apiCode, requestData = {}) {
    let body = this.get_wocare_body(apiCode, requestData);
    const requestOptions = {
      fn: "wocare_" + apiCode,
      method: "post",
      url: "https://wocare.unisk.cn/api/v1/" + apiCode,
      form: body
    };
    let response = await this.request(requestOptions);
    if (response?.["result"]?.["messageContent"]) {
      try {
        let decodedContent = JSON.parse(Buffer.from(response.result.messageContent, "base64").toString());
        response.result.data = decodedContent?.["data"] || decodedContent;
        if (decodedContent?.["resultMsg"]) {
          response.result.resultMsg = decodedContent.resultMsg;
        }
      } catch (error) {
        this.log("联通祝福: 解析返回失败:");
        console.log(error);
      }
    }
    return response;
  }
  async wocare_getToken(ticket, options = {}) {
    let isSuccess = false;
    try {
      let requestOptions = {
        fn: "wocare_getToken",
        method: "get",
        url: "https://wocare.unisk.cn/mbh/getToken",
        searchParams: {
          channelType: serviceLife,
          type: "02",
          ticket: ticket,
          version: appVersion,
          timestamp: appName.time("yyyyMMddhhmmssS"),
          desmobile: this.mobile,
          num: 0,
          postage: appName.randomString(32),
          homePage: "home",
          duanlianjieabc: "qAz2m",
          userNumber: this.mobile
        }
      },
        {
          headers: headers,
          statusCode: statusCode
        } = await this.request(requestOptions);
      if (statusCode == 302) {
        if (headers?.["location"]) {
          let locationUrl = new URL(headers.location),
            sid = locationUrl.searchParams.get("sid");
          sid ? (this.wocare_sid = sid, isSuccess = await this.wocare_loginmbh()) : this.log("联通祝福: 没有获取到sid");
        } else {
          this.log("联通祝福: 没有获取到location");
        }
      } else {
        this.log("联通祝福: 获取sid失败[" + statusCode + "]");
      }
    } catch (error) {
      console.log(error);
    } finally {
      return isSuccess;
    }
  }
  async wocare_loginmbh(options = {}) {
    let isSuccess = false;
    try {
      let apiCode = "loginmbh";
      const requestData = {
        sid: this.wocare_sid,
        channelType: serviceLife,
        apiCode: apiCode
      };
      let {
        result: responseResult,
        statusCode: responseStatus
      } = await this.wocare_api(apiCode, requestData);
      let resultCode = appName.get(responseResult, "resultCode", responseStatus);
      if (resultCode == "0000") {
        isSuccess = true;
        let {
          token: token
        } = responseResult?.["data"];
        this.wocare_token = token;
      } else {
        let errorMessage = responseResult?.["resultMsg"] || responseResult?.["resultDesc"] || "";
        this.log("联通祝福: 登录失败[" + resultCode + "]: " + errorMessage);
      }
    } catch (error) {
      console.log(error);
    } finally {
      return isSuccess;
    }
  }
  async wocare_getSpecificityBanner(options = {}) {
    try {
      let apiCode = "getSpecificityBanner";
      const requestData = {
        token: this.wocare_token,
        apiCode: apiCode
      };
      let {
        result: responseResult,
        statusCode: responseStatus
      } = await this.wocare_api(apiCode, requestData);
      let resultCode = appName.get(responseResult, "resultCode", responseStatus);
      if (resultCode == "0000") {
        let bannerList = responseResult?.["data"] || [];
        for (let banner of bannerList.filter(b => b.activityStatus === "0" && b.isDeleted === "0")) {
          await this.wocare_getDrawTask(banner);
          await this.wocare_loadInit(banner);
        }
      } else {
        let errorMessage = responseResult?.["resultMsg"] || responseResult?.["resultDesc"] || "";
        this.log("联通祝福: 进入活动失败[" + resultCode + "]: " + errorMessage);
      }
    } catch (error) {
      console.log(error);
    }
  }
  async wocare_loadInit(activity, options = {}) {
    try {
      let apiCode = "loadInit";
      const requestData = {
        token: this.wocare_token,
        channelType: serviceLife,
        type: activity.id,
        apiCode: apiCode
      };
      let {
        result: responseResult,
        statusCode: responseStatus
      } = await this.wocare_api(apiCode, requestData);
      let resultCode = appName.get(responseResult, "resultCode", responseStatus);
      if (resultCode == "0000") {
        let responseData = responseResult?.["data"],
          activeModuleGroupId = responseData?.["zActiveModuleGroupId"],
          drawCount = 0;
        switch (activity.id) {
          case 2:
            {
              let isPartake = responseData?.["data"]?.["isPartake"] || 0;
              !isPartake && (drawCount = 1);
              break;
            }
          case 3:
            {
              drawCount = parseInt(responseData?.["raffleCountValue"] || 0);
              break;
            }
          case 4:
            {
              drawCount = parseInt(responseData?.["mhRaffleCountValue"] || 0);
              break;
            }
        }
        while (drawCount-- > 0) {
          await appName.wait(5000);
          await this.wocare_luckDraw(activity, activeModuleGroupId);
        }
      } else {
        let errorMessage = responseResult?.["resultMsg"] || responseResult?.["resultDesc"] || "";
        this.log("联通祝福: [" + activity.name + "]查询活动失败[" + resultCode + "]: " + errorMessage);
      }
    } catch (error) {
      console.log(error);
    }
  }
  async wocare_getDrawTask(activity, options = {}) {
    try {
      let apiCode = "getDrawTask";
      const requestData = {
        token: this.wocare_token,
        channelType: serviceLife,
        type: activity.id,
        apiCode: apiCode
      };
      let {
        result: responseResult,
        statusCode: responseStatus
      } = await this.wocare_api(apiCode, requestData);
      let resultCode = appName.get(responseResult, "resultCode", responseStatus);
      if (resultCode == "0000") {
        let taskList = responseResult?.["data"]?.["taskList"] || [];
        for (let task of taskList.filter(t => t.taskStatus == 0)) {
          await this.wocare_completeTask(activity, task);
        }
      } else {
        let errorMessage = responseResult?.["resultMsg"] || responseResult?.["resultDesc"] || "";
        this.log("联通祝福: [" + activity.name + "]查询任务失败[" + resultCode + "]: " + errorMessage);
      }
    } catch (error) {
      console.log(error);
    }
  }
  async wocare_completeTask(activity, task, taskStep = "1", options = {}) {
    try {
      let taskTitle = task.title,
        action = taskStep == "1" ? "领取任务" : "完成任务",
        apiCode = "completeTask";
      const requestData = {
        token: this.wocare_token,
        channelType: serviceLife,
        task: task.id,
        taskStep: taskStep,
        type: activity.id,
        apiCode: apiCode
      };
      let {
        result: responseResult,
        statusCode: responseStatus
      } = await this.wocare_api(apiCode, requestData);
      let resultCode = appName.get(responseResult, "resultCode", responseStatus);
      if (resultCode == "0000") {
        this.log("联通祝福: " + action + "[" + taskTitle + "]成功");
        taskStep == "1" && (await this.wocare_completeTask(activity, task, "4"));
      } else {
        let errorMessage = responseResult?.["resultMsg"] || responseResult?.["resultDesc"] || "";
        this.log("联通祝福: [" + activity.name + "]" + action + "[" + taskTitle + "]失败[" + resultCode + "]: " + errorMessage);
      }
    } catch (error) {
      console.log(error);
    }
  }
  async wocare_luckDraw(activity, activeModuleGroupId, options = {}) {
    try {
      let apiCode = "luckDraw";
      const requestData = {
        token: this.wocare_token,
        channelType: serviceLife,
        zActiveModuleGroupId: activeModuleGroupId,
        type: activity.id,
        apiCode: apiCode
      };
      let {
        result: responseResult,
        statusCode: responseStatus
      } = await this.wocare_api(apiCode, requestData);
      let resultCode = appName.get(responseResult, "resultCode", responseStatus);
      if (resultCode == "0000") {
        let drawResultCode = appName.get(responseResult?.["data"], "resultCode", -1);
        if (drawResultCode == "0000") {
          let {
            prizeName: prizeName,
            prizeDesc: prizeDesc
          } = responseResult?.["data"]?.["data"]?.["prize"];
          this.log("联通祝福: [" + activity.name + "]抽奖: " + prizeName + "[" + prizeDesc + "]");
        } else {
          let errorMessage = responseResult?.["resultMsg"] || responseResult?.["resultDesc"] || "";
          this.log("联通祝福: [" + activity.name + "]抽奖失败[" + drawResultCode + "]: " + errorMessage);
        }
      } else {
        let errorMessage = responseResult?.["resultMsg"] || responseResult?.["resultDesc"] || "";
        this.log("联通祝福: [" + activity.name + "]抽奖错误[" + resultCode + "]: " + errorMessage);
      }
    } catch (error) {
      console.log(error);
    }
  }
  async card_618_authCheck(options = {}) {
    try {
      let requestConfig = {
        fn: "card_618_authCheck",
        method: "post",
        url: "https://epay.10010.com/ps-pafs-auth-front/v1/auth/check",
        headers: {
          bizchannelinfo: this.get_bizchannelinfo()
        }
      };
      let {
        result: responseResult
      } = await this.request(requestConfig);
      let responseCode = appName.get(responseResult, "code", -1);
      if (responseCode == "0000") {
        let {
          mobile: mobile,
          sessionId: sessionId,
          tokenId: tokenId,
          userId: userId
        } = responseResult?.["data"]?.["authInfo"];
        const authInfo = {
          sessionId: sessionId,
          tokenId: tokenId,
          userId: userId
        };
        Object.assign(this, authInfo);
        await this.card_618_queryUserCardInfo();
      } else {
        if (responseCode == "2101000100") {
          let loginUrl = responseResult?.["data"]?.["woauth_login_url"];
          await this.card_618_login(loginUrl);
        } else {
          let errorMessage = responseResult?.["msgInside"] || responseResult?.["msg"] || "";
          this.log("618集卡获取tokenId失败[" + responseCode + "]: " + errorMessage);
        }
      }
    } catch (error) {
      console.log(error);
    }
  }
  async card_618_login(loginUrl, options = {}) {
    try {
      let templateName = appName.time("yyyyMM") + "28ZFR";
      loginUrl += "https://epay.10010.com/ci-mcss-party-web/rainbow/?templateName=" + templateName + "&bizFrom=225&bizChannelCode=225&channelType=WDQB";
      const requestOptions = {
        fn: "card_618_login",
        method: "get",
        url: "https://epay.10010.com/woauth2/login",
        searchParams: {}
      };
      requestOptions.searchParams.response_type = "web_token";
      requestOptions.searchParams.source = "app_sjyyt";
      requestOptions.searchParams.union_session_id = "";
      requestOptions.searchParams.device_digest_token_id = this.tokenId_cookie;
      requestOptions.searchParams.target_client_id = anotherClientId;
      requestOptions.searchParams.position = null;
      requestOptions.searchParams.redirect_url = "https://epay.10010.com/ci-mcss-party-web/cardSelection/?activityId=NZJK618CJHD";
      requestOptions.searchParams.bizFrom = errorCode;
      requestOptions.searchParams.bizChannelCode = errorNumber;
      requestOptions.searchParams.channelType = "WDQB";
      let {
        headers: headers,
        statusCode: statusCode
      } = await this.request(requestOptions);
      if (headers?.["location"]) {
        let locationUrl = new URL(headers.location);
        this.rptId = locationUrl.searchParams.get("rptid");
        this.rptId ? await this.card_618_authCheck() : this.log("618集卡获取rptid失败");
      } else {
        this.log("618集卡获取rptid失败[" + statusCode + "]");
      }
    } catch (error) {
      console.log(error);
    }
  }
  async card_618_queryUserCardInfo(options = {}) {
    try {
      const requestBody = {
        activityId: "NZJK618CJHD"
      };
      let requestConfig = {
        fn: "card_618_queryUserCardInfo",
        method: "post",
        url: "https://epay.10010.com/ci-mcss-party-front/v1/mouldCard/queryUserCardInfo",
        headers: {
          bizchannelinfo: this.get_bizchannelinfo(),
          authinfo: this.get_epay_authinfo()
        },
        form: requestBody
      };
      let {
        result: responseResult
      } = await this.request(requestConfig);
      let responseCode = appName.get(responseResult, "code", -1);
      if (responseCode == "0000" && responseResult?.["data"]?.["returnCode"] == 0) {
        let {
          userRemain = 0,
          isFirst = true
        } = responseResult?.["data"];
        if (isFirst) {
          await this.card_618_unifyDraw("首次进入");
        }
        this.log("618集卡可以抽奖" + userRemain + "次");
        while (userRemain-- > 0) {
          await this.card_618_unifyDraw("抽奖");
        }
      } else {
        let errorMessage = responseResult?.["message"] || responseResult?.["msg"] || "";
        this.log("618集卡进入主页失败[" + responseCode + "]: " + errorMessage);
      }
    } catch (error) {
      console.log(error);
    }
  }
  async card_618_unifyDraw(drawType, options = {}) {
    try {
      let requestConfig = {
        fn: "card_618_unifyDraw",
        method: "post",
        url: "https://epay.10010.com/ci-mcss-party-front/v1/mouldCard/unifyDraw",
        headers: {
          bizchannelinfo: this.get_bizchannelinfo(),
          authinfo: this.get_epay_authinfo()
        },
        form: {
          bigActivityId: activityIds.card_618,
          activityId: activityIds.card_618 + card618DrawTypeSuffix[drawType],
          bizFrom: errorCode
        }
      };
      let {
        result: responseResult
      } = await this.request(requestConfig);
      let responseCode = appName.get(responseResult, "code", -1);
      if (responseCode == "0000" && responseResult?.["data"]?.["returnCode"] == 0) {
        let prizeId = responseResult?.["data"]?.["prizeId"] || "空气",
          prizeName = card618PrizeMap[prizeId] || prizeId;
        const notifyOptions = {
          notify: true
        };
        this.log("618集卡[" + drawType + "]: " + prizeName, notifyOptions);
      } else {
        let errorMessage = responseResult?.["data"]?.["returnMsg"] || responseResult?.["msg"] || "";
        this.log("618集卡[" + drawType + "]失败[" + (responseResult?.["data"]?.["returnCode"] || responseCode) + "]: " + errorMessage);
      }
    } catch (error) {
      console.log(error);
    }
  }


  async getTicketByNative_sec() {
    let requestOptions = {
      "fn": "getTicketByNative_sec",
      "url": `https://m.client.10010.com/edop_ng/getTicketByNative?token=${this.ecs_token}&appId=edop_unicom_3a6cc75a`,
      "headers": {
        "Cookie": `PvSessionId=${appName.time("yyyyMMddhhmmss")}${this.unicomTokenId};c_mobile=${this.mobile}; c_version=iphone_c@11.0800; city=036|${this.city?.[0]?.cityCode || ''}|90063345|-99;devicedId=${this.unicomTokenId}; ecs_token=${this.ecs_token};t3_token=`,
        "Accept": "*",
        "Connection": "keep-alive",
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept-Encoding": "gzip;q=1.0, compress;q=0.5",
        "Host": "m.client.10010.com",
        "User-Agent": "ChinaUnicom4.x/12.3.1 (com.chinaunicom.mobilebusiness; build:77; iOS 16.6.0) Alamofire/4.7.3 unicom{version:iphone_c@12.0301}",
        "Accept-Language": "zh-Hans-CN;q=1.0"
      }
    };
    let { result } = await this.request(requestOptions);
    this.sec_ticket1 = result ? result.ticket : null;
    if (!this.sec_ticket1) {
      this.log(`安全管家: getTicketByNative_sec 失败 - ${JSON.stringify(result)}`);
    }
  }

  async getAuthToken_sec() {
    if (!this.sec_ticket1) {
      this.log("安全管家 getAuthToken_sec 缺少 ticket1，跳过");
      return;
    }
    let requestOptions = {
      "fn": "getAuthToken_sec",
      "url": "https://uca.wo116114.com/api/v1/auth/ticket?product_line=uasp&entry_point=h5&entry_point_id=edop_unicom_3a6cc75a",
      "method": "post",
      "headers": {
        "User-Agent": "ChinaUnicom4.x/12.3.1 (com.chinaunicom.mobilebusiness; build:77; iOS 16.6.0) Alamofire/4.7.3 unicom{version:iphone_c@12.0301}",
        "Accept": "*",
        "Accept-Encoding": "gzip;q=1.0, compress;q=0.5",
        "Content-Type": "application/json",
        "Accept-Language": "zh-Hans-CN;q=1.0",
        "clientType": "uasp_unicom_applet"
      },
      "json": { "productId": "", "type": 1, "ticket": this.sec_ticket1 }
    };
    let { result } = await this.request(requestOptions);
    if (result && result.data) {
      this.sec_token = result.data.access_token;
    } else {
      this.log(`安全管家: getAuthToken_sec 失败 - ${JSON.stringify(result)}`);
    }
  }

  async getTicketForJF_sec() {
    if (!this.sec_token) {
      this.log("安全管家 getTicketForJF_sec 缺少 token，跳过");
      return;
    }
    let requestOptions = {
      "fn": "getTicketForJF_sec_1",
      "method": "post",
      "url": "https://uca.wo116114.com/api/v1/auth/getTicket?product_line=uasp&entry_point=h5&entry_point_id=edop_unicom_3a6cc75a",
      "headers": {
        "User-Agent": "ChinaUnicom4.x/12.3.1 (com.chinaunicom.mobilebusiness; build:77; iOS 16.6.0) Alamofire/4.7.3 unicom{version:iphone_c@12.0301}",
        "Content-Type": "application/json",
        "auth-sa-token": this.sec_token,
        "clientType": "uasp_unicom_applet"
      },
      "json": { "productId": "91311616", "phone": this.mobile }
    };

    let { result } = await this.request(requestOptions);
    if (result && result.data) {
      this.sec_ticket = result.data.ticket;
    } else {
      this.log("安全管家获取积分票据失败");
      return;
    }

    let queryOptions = {
      "fn": "getTicketForJF_sec_2",
      "method": "post",
      "url": "https://m.jf.10010.com/jf-external-application/page/query",
      "headers": {
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 unicom{version:iphone_c@12.0301};ltst;OSVersion/16.6",
        "partnersid": "1702",
        "ticket": decodeURIComponent(this.sec_ticket),
        "Cookie": `_jea_id=${this.sec_jeaId}`,
        "clienttype": "uasp_unicom_applet",
      },
      "json": { "activityId": "s747395186896173056", "partnersId": "1702" }
    };

    let { headers } = await this.request(queryOptions);
    const setCookieHeader = headers?.["set-cookie"];
    if (setCookieHeader) {
      const cookies = Array.isArray(setCookieHeader) ? setCookieHeader : [setCookieHeader];
      const jeaCookie = cookies.find(cookie => cookie && cookie.startsWith("_jea_id="));
      if (jeaCookie) {
        const newJeaId = jeaCookie.split(";")[0].split("=")[1];
        if (newJeaId) {
          this.sec_jeaId = newJeaId;
          this.log("安全管家: 更新 jeaId: " + this.sec_jeaId);
        }
      }
    }
  }

  async operateBlacklist_sec(phoneNumber, type) {
    const typeName = type === 0 ? "添加" : "删除";
    this.log(`安全管家: 正在执行${typeName}黑名单号码: ${phoneNumber}`);

    let requestOptions = {
      "fn": `operateBlacklist_sec_${typeName}`,
      "method": "post",
      "url": "https://uca.wo116114.com/sjgj/woAssistant/umm/configs/v1/config?product_line=uasp&entry_point=h5&entry_point_id=wxdefbc1986dc757a6",
      "headers": {
        "User-Agent": "ChinaUnicom4.x/12.3.1 (com.chinaunicom.mobilebusiness; build:77; iOS 16.6.0) Alamofire/4.7.3 unicom{version:iphone_c@12.0301}",
        "auth-sa-token": this.sec_token,
        "clientType": "uasp_unicom_applet",
        "token": this.sec_token,
        "Cookie": `devicedId=${this.unicomTokenId}`
      },
      "json": {
        "productId": "91015539",
        "type": 1,
        "operationType": type,
        ...(type === 0 ? { "blacklistSource": 0 } : {}),
        "contents": [{ "content": phoneNumber, "contentTag": "", "nickname": null, "configTime": null }]
      }
    };

    let { result } = await this.request(requestOptions);
    return result;
  }

  async addToBlacklist_sec() {
    const phoneNumberToOperate = "13088888888";
    let response = await this.operateBlacklist_sec(phoneNumberToOperate, 0);

    // 检查多种成功条件: code 为 '0000' 或 0, 或者 msg 为 '成功'
    if (response && (response.code === '0000' || response.code === 0 || response.msg === '成功')) {
      this.log(`安全管家: ✅ 添加黑名单成功。`);
      return;
    }

    const isDuplicateError = response && response.msg && response.msg.includes("号码已存在");

    if (isDuplicateError) {
      this.log(`安全管家: ⚠️ 检测到号码 ${phoneNumberToOperate} 已存在，执行先删除后添加流程。`);
      let delResponse = await this.operateBlacklist_sec(phoneNumberToOperate, 1);

      // 检查删除操作的多种成功/可接受条件
      const isDelSuccess = delResponse && (delResponse.code === '0000' || delResponse.code === 0 || (delResponse.msg && (delResponse.msg.includes("成功") || delResponse.msg.includes("不在黑名单"))));

      if (isDelSuccess) {
        this.log(`安全管家: ✅ 删除旧记录成功，等待 2 秒后重新添加...`);
        await appName.wait(2000);
        let retryResponse = await this.operateBlacklist_sec(phoneNumberToOperate, 0);

        // 重新检查添加操作的多种成功条件
        if (retryResponse && (retryResponse.code === '0000' || retryResponse.code === 0 || retryResponse.msg === '成功')) {
          this.log(`安全管家: ✅ 重新添加黑名单成功。`);
        } else {
          this.log(`安全管家: ❌ 重新添加失败: ${retryResponse ? retryResponse.msg : '无响应'}`);
        }
      } else {
        this.log(`安全管家: ❌ 删除旧记录失败，无法继续添加。`);
      }
    } else {
      // 其他未知的失败情况
      this.log(`安全管家: ❌ 添加黑名单失败: ${response ? response.msg : '无响应'}`);
    }
  }

  async markPhoneNumber_sec() {
    let requestOptions = {
      "fn": "markPhoneNumber_sec",
      "method": "post",
      "url": "https://uca.wo116114.com/sjgj/unicomAssistant/uasp/configs/v1/addressBook/saveTagPhone?product_line=uasp&entry_point=h5&entry_point_id=wxdefbc1986dc757a6",
      "headers": {
        "User-Agent": "ChinaUnicom4.x/12.3.1 (com.chinaunicom.mobilebusiness; build:77; iOS 16.6.0) Alamofire/4.7.3 unicom{version:iphone_c@12.0301}",
        "auth-sa-token": this.sec_token,
        "clientType": "uasp_unicom_applet"
      },
      "json": { "tagPhoneNo": "13088330789", "tagIds": [26], "status": 0, "productId": "91311616" }
    };
    await this.request(requestOptions);
    this.log("安全管家: 执行号码标记。");
  }

  async syncAddressBook_sec() {
    let requestOptions = {
      "fn": "syncAddressBook_sec",
      "method": "post",
      "url": "https://uca.wo116114.com/sjgj/unicomAssistant/uasp/configs/v1/addressBookBatchConfig?product_line=uasp&entry_point=h5&entry_point_id=edop_unicom_3a6cc75a",
      "headers": {
        "User-Agent": "ChinaUnicom4.x/12.3.1 (com.chinaunicom.mobilebusiness; build:77; iOS 16.6.0) Alamofire/4.7.3 unicom{version:iphone_c@12.0301}",
        "auth-sa-token": this.sec_token,
        "clientType": "uasp_unicom_applet"
      },
      "json": { "addressBookDTOList": [{ "addressBookPhoneNo": "13088888888", "addressBookName": "水水" }], "productId": "91311616", "opType": "1" }
    };
    await this.request(requestOptions);
    this.log("安全管家: 执行同步通讯录。");
  }

  async setInterceptionRules_sec() {
    let requestOptions = {
      "fn": "setInterceptionRules_sec",
      "method": "post",
      "url": "https://uca.wo116114.com/sjgj/woAssistant/umm/configs/v1/config?product_line=uasp&entry_point=h5&entry_point_id=wxdefbc1986dc757a6",
      "headers": {
        "User-Agent": "ChinaUnicom4.x/12.3.1 (com.chinaunicom.mobilebusiness; build:77; iOS 16.6.0) Alamofire/4.7.3 unicom{version:iphone_c@12.0301}",
        "auth-sa-token": this.sec_token,
        "clientType": "uasp_unicom_applet"
      },
      "json": { "contents": [{ "name": "rings-once", "contentTag": "8", "contentName": "响一声", "content": "0", "icon": "alerting" }], "operationType": 0, "type": 3, "productId": "91311616" }
    };
    await this.request(requestOptions);
    this.log("安全管家: 执行设置拦截规则。");
  }

  async viewWeeklyStatus_sec() {
    let requestOptions = {
      "fn": "viewWeeklyStatus_sec",
      "method": "post",
      "url": "https://uca.wo116114.com/sjgj/unicomAssistant/uasp/configs/v1/weeklySwitchStatus?product_line=uasp&entry_point=h5&entry_point_id=wxdefbc1986dc757a6",
      "headers": { "auth-sa-token": this.sec_token, "clientType": "uasp_unicom_applet" },
      "json": { "productId": "91311616" }
    };
    await this.request(requestOptions);
  }

  async queryKeyData_sec() {
    let requestOptions = {
      "fn": "queryKeyData_sec",
      "method": "post",
      "url": "https://uca.wo116114.com/sjgj/unicomAssistant/uasp/report/v1/queryKeyData?product_line=uasp&entry_point=h5&entry_point_id=wxdefbc1986dc757a6",
      "headers": { "auth-sa-token": this.sec_token, "clientType": "uasp_unicom_applet" },
      "json": { "productId": "91311616" }
    };
    await this.request(requestOptions);
  }

  async viewWeeklySummary_sec() {
    let requestOptions = {
      "fn": "viewWeeklySummary_sec",
      "method": "post",
      "url": "https://uca.wo116114.com/sjgj/unicomAssistant/uasp/report/v1/weeklySummary?product_line=uasp&entry_point=h5&entry_point_id=wxdefbc1986dc757a6",
      "headers": { "auth-sa-token": this.sec_token, "clientType": "uasp_unicom_applet" },
      "json": { "productId": "91311616" }
    };
    await this.request(requestOptions);
    this.log("安全管家: 执行查看周报。");
  }

  async receivePoints_sec(taskCode) {
    let requestOptions = {
      "fn": "receivePoints_sec",
      "method": "post",
      "url": "https://m.jf.10010.com/jf-external-application/jftask/receive",
      "headers": {
        "ticket": decodeURIComponent(this.sec_ticket),
        "Cookie": `_jea_id=${this.sec_jeaId}`,
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 unicom{version:iphone_c@12.0301};ltst;OSVersion/16.6",
        "partnersid": "1702",
        "clienttype": "uasp_unicom_applet",
      },
      "json": { "taskCode": taskCode }
    };
    let { result } = await this.request(requestOptions);
    if (result && result.data && result.data.score) {
      this.log(`安全管家: ✅ 领取积分成功: +${result.data.score} (${result.msg})`, { notify: true });
    } else if (result) {
      this.log(`安全管家: ❌ 领取积分失败: ${result.msg}`);
    } else {
      this.log("安全管家: ❌ 领取积分API无响应");
    }
  }

  async finishTask_sec(taskCode, taskName) {
    let requestOptions = {
      "fn": `finishTask_sec_${taskName}`,
      "method": "post",
      "url": "https://m.jf.10010.com/jf-external-application/jftask/toFinish",
      "headers": {
        "ticket": decodeURIComponent(this.sec_ticket),
        "Cookie": `_jea_id=${this.sec_jeaId}`,
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 unicom{version:iphone_c@12.0301};ltst;OSVersion/16.6",
        "partnersid": "1702",
        "clienttype": "uasp_unicom_applet",
      },
      "json": { "taskCode": taskCode }
    };
    await this.request(requestOptions);
    this.log(`安全管家: 开启任务 [${taskName}]`);

    switch (taskName) {
      case "联通助理-添加黑名单":
        await this.addToBlacklist_sec();
        break;
      case "联通助理-号码标记":
        await this.markPhoneNumber_sec();
        break;
      case "联通助理-同步通讯录":
        await this.syncAddressBook_sec();
        break;
      case "联通助理-骚扰拦截设置":
        await this.setInterceptionRules_sec();
        break;
      case "联通助理-查看周报":
        await this.viewWeeklyStatus_sec();
        await this.queryKeyData_sec();
        await this.viewWeeklySummary_sec();
        break;
      default:
        // No action needed as filtering is done upstream
        break;
    }
  }

  async signIn_sec(taskCode) {
    let requestOptions = {
      "fn": "signIn_sec",
      "method": "post",
      "url": "https://m.jf.10010.com/jf-external-application/jftask/sign",
      "headers": {
        "ticket": decodeURIComponent(this.sec_ticket),
        "Cookie": `_jea_id=${this.sec_jeaId}`,
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 unicom{version:iphone_c@12.0301};ltst;OSVersion/16.6",
        "partnersid": "1702",
        "clienttype": "uasp_unicom_applet",
      },
      "json": { "taskCode": taskCode }
    };
    let { result } = await this.request(requestOptions);
    this.log(`安全管家: 完成签到: ${result?.msg || '状态未知'}`);
  }

  async executeAllTasks_sec() {
    let requestOptions = {
      "fn": "executeAllTasks_sec",
      "method": "post",
      "url": "https://m.jf.10010.com/jf-external-application/jftask/taskDetail",
      "headers": {
        "ticket": decodeURIComponent(this.sec_ticket),
        "Cookie": `_jea_id=${this.sec_jeaId}`,
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 unicom{version:iphone_c@12.0301};ltst;OSVersion/16.6",
        "partnersid": "1702",
        "clienttype": "uasp_unicom_applet",
      },
      "json": {}
    };

    let { result } = await this.request(requestOptions);
    if (!result || !result.data || !result.data.taskDetail) {
      this.log("安全管家: 查询任务列表失败或响应格式错误。");
      return;
    }

    const taskList = result.data.taskDetail.taskList;
    const executableTaskNames = [
      "联通助理-添加黑名单",
      "联通助理-号码标记",
      "联通助理-同步通讯录",
      "联通助理-骚扰拦截设置",
      "联通助理-查看周报"
    ];

    const executableTasks = [];
    const skippedTasks = [];

    for (const task of taskList) {
      const isKnownExecutable = executableTaskNames.includes(task.taskName) || task.taskName.includes("签到");
      if (isKnownExecutable) {
        executableTasks.push(task);
      } else {
        skippedTasks.push(task);
      }
    }

    const unfinishedSkipped = skippedTasks.filter(t => t.finishCount !== t.needCount);
    if (unfinishedSkipped.length > 0) {
      const skippedTaskNames = unfinishedSkipped.map(t => `[${t.taskName}]`).join(', ');
      this.log(`安全管家: 跳过: ${skippedTaskNames}`);
    }

    for (const task of executableTasks) {
      const { taskCode, taskName, finishCount, needCount, finishText } = task;
      this.log(`安全管家: [${taskName}]: ${finishCount}/${needCount} - ${finishText}`);

      if (finishCount !== needCount) {
        const remainingCount = needCount - finishCount;
        this.log(`安全管家: 任务未完成，需要再执行 ${remainingCount} 次`);

        for (let i = 0; i < remainingCount; i++) {
          await appName.wait(3000);
          try {
            if (taskName.includes("签到")) {
              await this.signIn_sec(taskCode);
            } else {
              await this.finishTask_sec(taskCode, taskName);
            }

            if (!taskName.includes("签到")) {
              await appName.wait(10000);
              await this.receivePoints_sec(taskCode);
            } else {
              await this.receivePoints_sec(taskCode);
              break;
            }
          } catch (error) {
            this.log(`安全管家: 执行 ${taskCode} 时出错: ${error.message}`);
            break;
          }
        }
      } else if (finishText === "待领取") {
        try {
          await appName.wait(3000);
          await this.receivePoints_sec(taskCode);
        } catch (error) {
          this.log(`安全管家: 领取 ${taskCode} 奖励时出错: ${error.message}`);
        }
      } else {
        this.log(`安全管家: [${taskName}] 任务已完成且奖励已领取`);
      }
      this.log("安全管家: ---------------------");
    }
  }

  async getUserInfo_sec() {
    let requestOptions = {
      "fn": "getUserInfo_sec",
      "method": "post",
      "url": "https://m.jf.10010.com/jf-external-application/jftask/userInfo",
      "headers": {
        "ticket": decodeURIComponent(this.sec_ticket),
        "Cookie": `_jea_id=${this.sec_jeaId}`,
        "User-Agent": "Mozilla/5.0 (Linux; Android 9; ONEPLUS A5000 Build/PKQ1.180716.001; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/138.0.7204.179 Mobile Safari/537.36; unicom{version:android@11.0000,desmobile:0};devicetype{deviceBrand:OnePlus,deviceModel:ONEPLUS A5000}",
        "partnersid": "1702",
        "clienttype": "uasp_unicom_applet",
      },
      "json": {}
    };

    let { result } = await this.request(requestOptions);
    if (!result || result.code !== '0000' || !result.data || result.data.availableScore === undefined) {
      this.log(`安全管家: 查询积分失败或响应格式错误。错误信息: ${result ? result.msg : '无响应'}`);
      return;
    }

    const currentPoints = parseInt(result.data.availableScore, 10);
    const todayPoints = result.data.todayEarnScore;

    if (this.sec_oldJFPoints === null) {
      this.sec_oldJFPoints = currentPoints;
      this.log(`安全管家: 运行前积分：${currentPoints} (今日已赚 ${todayPoints})`);
    } else {
      if (isNaN(currentPoints) || isNaN(this.sec_oldJFPoints)) {
        this.log(`安全管家: 警告：积分值无法转换为数字进行计算。`);
        this.log(`安全管家: 运行后可用积分: ${result.data.availableScore}`, { notify: true });
      } else {
        const pointsGained = currentPoints - this.sec_oldJFPoints;
        this.log(`安全管家: 运行后积分${currentPoints}，本次运行获得${pointsGained}`, { notify: true });
      }
    }
  }

  // ============================================
  // 新增模块 1: 沃云手机 (全国通用)
  // 移植自 Python 版 wostore_cloud_task
  // ============================================

  async wostore_cloud_task() {
    this.log("============= 沃云手机 =============");
    if (!this.mobile || !this.ecs_token) {
      this.log("沃云手机: 缺少 mobile 或 ecs_token，跳过");
      return;
    }

    // 1. 获取入口 Ticket
    const targetUrl = "https://h5forphone.wostore.cn/cloudPhone/dialogCloudPhone.html?channel_id=ST-Zujian001-gs&cp_id=91002997";
    const ticketInfo = await this.openPlatLineNew(targetUrl);
    if (!ticketInfo.ticket) {
      this.log("沃云手机: 获取入口 Ticket 失败");
      return;
    }

    // 2. 登录流程 (双重 Token 获取)
    const tokens = await this.wostore_cloud_login(ticketInfo.ticket);

    // 【修改点】增加 else 日志
    if (!tokens) {
      this.log("沃云手机: 登录失败，跳过后续任务");
      return;
    }

    const { user_token } = tokens;

    // 3. 积分签到
    await this.wostore_cloud_sign(user_token);

    // 4. 刷新任务列表 (触发同步)
    await appName.wait(2000);
    await this.wostore_cloud_task_list(user_token);

    // 5. 领取抽奖次数 (taskCode: 2508-01)
    await appName.wait(1000);
    await this.wostore_cloud_get_chance(user_token, "2508-01");

    // 6. 执行抽奖
    await appName.wait(2000);
    await this.wostore_cloud_draw(user_token);
  }

  async wostore_cloud_login(ticket) {
    try {
      // Step 1: 换取第一个 Token
      const url1 = "https://member.zlhz.wostore.cn/wcy_member/yunPhone/h5Awake/businessHall";
      const body1 = {
        "cpId": "91002997", "channelId": "ST-Zujian001-gs", "ticket": ticket,
        "env": "prod", "transId": "S2ndpage1235+开福袋！+F1+CJDD00D0001+iphone_c@12.0801", "qkActId": null
      };
      const res1 = await this.request({
        fn: "wostore_login_1", method: "post", url: url1, json: body1,
        headers: { "Origin": "https://h5forphone.wostore.cn" }
      });

      if (res1.result?.code !== "0") {
        this.log(`沃云手机: 登录第一步失败 - ${res1.result?.msg || JSON.stringify(res1.result)}`);
        return null;
      }

      // 从 URL 中提取 token
      const redirectUrl = res1.result.data?.url || "";

      // 【关键修改】修复正则: /token=([^&]+)/ 
      // 含义：提取 token= 后面所有“非&符号”的内容，直到遇到&或字符串结束
      const match = redirectUrl.match(/token=([^&]+)/);

      if (!match) {
        if (redirectUrl.includes("protocol") || redirectUrl.includes("sign")) {
          this.log(`沃云手机: 未开通业务 (检测到协议签署跳转)，跳过`);
        } else {
          this.log(`沃云手机: 无法提取 Token, 跳转URL: ${redirectUrl}`);
        }
        return null;
      }
      const firstToken = match[1];

      // Step 2: 换取 user_token
      await appName.wait(1000);
      const url2 = "https://uphone.wostore.cn/h5api/activity-service/user/login";
      const body2 = {
        "identityType": "cloudPhoneLogin", "code": firstToken, "channelId": "ST-Zujian001-gs",
        "activityId": "Lottery_251201", "device": "device"
      };
      const res2 = await this.request({
        fn: "wostore_login_2", method: "post", url: url2, json: body2,
        headers: { "Origin": "https://uphone.wostore.cn", "X-USR-TOKEN": firstToken }
      });

      if (res2.result?.code === 200) {
        return { firstToken, user_token: res2.result.data.user_token };
      } else {
        this.log(`沃云手机: 登录第二步失败 - ${res2.result?.msg || JSON.stringify(res2.result)}`);
        return null;
      }
    } catch (e) {
      this.log(`沃云手机: 登录异常 ${e.message}`);
      return null;
    }
  }

  async wostore_cloud_sign(userToken) {
    try {
      const res = await this.request({
        fn: "wostore_sign", method: "post",
        url: "https://uphone.wostore.cn/h5api/activity-service/points/v1/sign",
        json: { "activityCode": "Points_Sign_2507" },
        headers: { "X-USR-TOKEN": userToken, "Origin": "https://uphone.wostore.cn" }
      });
      if (res.result?.code === 200) {
        this.log(`沃云手机: 积分签到成功`);
      }
    } catch (e) { }
  }

  async wostore_cloud_task_list(userToken) {
    try {
      await this.request({
        fn: "wostore_list", method: "post",
        url: "https://uphone.wostore.cn/h5api/activity-service/user/task/list",
        json: { "activityCode": "Lottery_251201" },
        headers: { "X-USR-TOKEN": userToken }
      });
    } catch (e) { }
  }

  async wostore_cloud_get_chance(userToken, taskCode) {
    try {
      await this.request({
        fn: "wostore_chance", method: "post",
        url: "https://uphone.wostore.cn/h5api/activity-service/user/task/raffle/get",
        json: { "activityCode": "Lottery_251201", "taskCode": taskCode },
        headers: { "X-USR-TOKEN": userToken }
      });
    } catch (e) { }
  }

  async wostore_cloud_draw(userToken) {
    try {
      const res = await this.request({
        fn: "wostore_draw", method: "post",
        url: "https://uphone.wostore.cn/h5api/activity-service/lottery",
        json: { "activityCode": "Lottery_251201" },
        headers: { "X-USR-TOKEN": userToken }
      });
      if (res.result?.code === 200) {
        const prize = res.result.prizeName || "未中奖";
        this.log(`沃云手机: 抽奖结果 - ${prize}`, { notify: true });
      } else {
        this.log(`沃云手机: 抽奖失败 - ${res.result?.msg || JSON.stringify(res.result)}`);
      }
    } catch (e) {
      this.log(`沃云手机: 抽奖异常 ${e.message}`);
    }
  }

  // ============================================
  // 新增模块 2: 区域任务 (自动判断)
  // 新疆专区 & 河南商都
  // ============================================

  async regional_task(isQueryOnly = false) {
    // 通过 onLine 接口获取到的 province 字段判断
    // 注意：this.city 是 onLine 接口返回的 list 数组，通常包含省份信息
    // 这里的逻辑需要依赖 onLine 登录成功后返回的 list 数据
    let isXinjiang = false;
    let isHenan = false;

    // 尝试解析省份
    if (this.city && Array.isArray(this.city) && this.city.length > 0) {
      const proName = this.city[0].proName || "";
      if (proName.includes("新疆")) isXinjiang = true;
      if (proName.includes("河南")) isHenan = true;
    }

    if (isQueryOnly) {
      this.log("============= 区域专区 (查询模式) =============");
      if (isXinjiang) {
        this.log("新疆专区: [查询模式] 跳过每日打卡 (无查询接口)");
      }
      if (isHenan) {
        // 仅查询河南签到状态
        const isSigned = await this.shangdu_get_sign_status();
        if (isSigned === true) {
          this.log(`河南商都: [状态查询] 今日已签到`);
        } else if (isSigned === false) {
          this.log(`河南商都: [状态查询] 今日未签到`);
        } else {
          this.log(`河南商都: [状态查询] 查询失败`);
        }
      }
      return;
    }

    if (isXinjiang) {
      this.log("============= 新疆专区 =============");
      await this.xj_task_main();
    }

    if (isHenan) {
      this.log("============= 河南商都 =============");
      await this.shangdu_task_main();
    }
  }

  // --- 新疆逻辑 ---
  async xj_task_main() {
    const ticketInfo = await this.openPlatLineNew("https://zy100.xj169.com/touchpoint/openapi/jumpHandRoom1G?source=155&type=02");
    if (!ticketInfo.ticket) return;

    const token = await this.xj_get_token(ticketInfo.ticket);
    if (token) {
      await this.xj_do_draw(token, "Jan2026Act"); // 注意：Python脚本里是 Jan2026Act，如果失效需检查月份
      // 客户日逻辑 (每月19-25号)
      const day = new Date().getDate();
      if (day >= 19 && day <= 25) {
        await this.xj_usersday_task(token);
      }
    }
  }

  async xj_get_token(ticket) {
    try {
      const res = await this.request({
        fn: "xj_token", method: "post",
        url: "https://zy100.xj169.com/touchpoint/openapi/getTokenAndCity",
        form: { ticket },
        headers: { "Referer": `https://zy100.xj169.com/touchpoint/openapi/jumpHandRoom1G?source=155&type=02&ticket=${ticket}` }
      });
      if (res.result?.code === 0) return res.result.data?.token;
      return null;
    } catch (e) { return null; }
  }

  async xj_do_draw(token, actId) {
    try {
      const res = await this.request({
        fn: "xj_draw", method: "post",
        url: `https://zy100.xj169.com/touchpoint/openapi/marchAct/draw_${actId}`,
        form: { "activityId": `daka${actId}`, "prizeId": "" }, // 注意 activityId 拼接
        headers: { "userToken": token }
      });
      const msg = res.result?.msg || res.result?.data || "失败";
      this.log(`新疆专区: 每日打卡 - ${msg}`, { notify: true });
    } catch (e) { }
  }

  async xj_usersday_task(token) {
    // 简化版：仅尝试秒杀 20元话费券，时间判断交给用户定时任务
    const res = await this.request({
      fn: "xj_userday", method: "post",
      url: "https://zy100.xj169.com/touchpoint/openapi/marchAct/draw_UsersDay2025Act",
      form: { "activityId": "usersDay2025Act", "prizeId": "hfq_twenty" },
      headers: { "userToken": token }
    });
    const msg = res.result?.msg || res.result?.data || "失败";
    this.log(`新疆客户日: 秒杀结果 - ${msg}`, { notify: true });
  }

  // --- 河南商都逻辑 ---

  // Helper: 查询河南商都签到状态
  async shangdu_get_sign_status() {
    try {
      const res = await this.request({
        method: "post",
        url: "https://app.shangdu.com/monthlyBenefit/v1/signIn/queryCumulativeSignAxis",
        json: {},
        headers: {
          "Origin": "https://app.shangdu.com",
          "Referer": "https://app.shangdu.com/monthlyBenefit/index.html",
          "edop_flag": "0",
          "Content-Type": "application/json"
        }
      });
      if (res.result?.code === "0000") {
        // todaySignFlag: '1' = 已签到, '0' = 未签到
        return res.result.data?.todaySignFlag === "1";
      }
      return null;
    } catch (e) {
      return null;
    }
  }

  // Helper: 河南商都签到重试
  async shangdu_sign_retry() {
    try {
      const resSign = await this.request({
        method: "post",
        url: "https://app.shangdu.com/monthlyBenefit/v1/signIn/userSignIn",
        json: {},
        headers: {
          "Origin": "https://app.shangdu.com",
          "Referer": "https://app.shangdu.com/monthlyBenefit/index.html",
          "edop_flag": "0",
          "X-Requested-With": "XMLHttpRequest",
          "Content-Type": "application/json"
        }
      });

      const code = resSign.result?.code;
      const data = resSign.result?.data || {};

      if (code === "0000") {
        const prize = data.prizeResp?.prizeName;
        if (prize) {
          this.log(`河南商都: 签到成功(重试) - 获得 ${prize}`, { notify: true });
        } else {
          this.log(`河南商都: 签到成功(重试)`);
        }
      } else if (code === "0019") {
        this.log(`河南商都: 重试仍返回重复签到，请检查`);
      } else {
        this.log(`河南商都: 签到重试失败 - ${resSign.result?.msg || "未知错误"}`);
      }
    } catch (e) {
      this.log(`河南商都: 签到重试异常: ${e}`);
    }
  }
  async shangdu_task_main() {
    if (!this.ecs_token) return;

    // 1. Get Ticket
    const res = await this.request({
      fn: "shangdu_ticket", method: "get",
      url: "https://m.client.10010.com/edop_ng/getTicketByNative?appId=edop_unicom_4b80047a&token=" + this.ecs_token
    });
    const ticket = res.result?.ticket;
    if (!ticket) {
      this.log("河南商都: 获取Ticket失败");
      return;
    }

    // 2. Login (激活 Session)
    // 补全 Origin 和 Accept，模拟 Python 逻辑
    const resLogin = await this.request({
      fn: "shangdu_login", method: "get",
      url: `https://app.shangdu.com/monthlyBenefit/v1/common/config?ticket=${ticket}`,
      headers: {
        "Origin": "https://app.shangdu.com",
        "Referer": "https://app.shangdu.com/monthlyBenefit/index.html",
        "edop_flag": "0",
        "Accept": "application/json, text/plain, */*"
      }
    });

    // 注意：Python 脚本这里并不强制要求 code=0000 才能继续，但通常需要这一步来 Set-Cookie
    if (resLogin.result?.code !== "0000") {
      this.log(`河南商都: 登录激活可能有误 (${resLogin.result?.msg})，尝试继续签到...`);
    }

    await appName.wait(1500);

    // 3. Sign In (签到)
    // 【关键修复】补全 X-Requested-With 和 Origin
    const resSign = await this.request({
      fn: "shangdu_sign", method: "post",
      url: "https://app.shangdu.com/monthlyBenefit/v1/signIn/userSignIn",
      json: {},
      headers: {
        "Origin": "https://app.shangdu.com",
        "Referer": "https://app.shangdu.com/monthlyBenefit/index.html",
        "edop_flag": "0",
        "X-Requested-With": "XMLHttpRequest", // 必须加上这个
        "Content-Type": "application/json"
      }
    });

    const code = resSign.result?.code;
    const data = resSign.result?.data || {};

    if (code === "0000") {
      // 判断 signFlag: "1" 代表本次签到成功，"0" 代表已签到或无奖励
      // 但有时 data.value == "0001" 代表 Cookie 失效
      if (data.value === "0001") {
        this.log(`河南商都: 签到失败 - Cookie无效`);
      } else {
        const prize = data.prizeResp?.prizeName || "已签到";
        this.log(`河南商都: 签到结果 - ${prize}`, { notify: true });
      }
    } else if (code === "0019") {
      // 服务端返回重复签到，查询实际状态确认 (移植自 Python)
      await appName.wait(1000);
      const isSigned = await this.shangdu_get_sign_status();

      if (isSigned === true) {
        this.log(`河南商都: 今日已签到 (状态确认)`);
      } else if (isSigned === false) {
        // 状态显示未签到，但返回重复签到，尝试重试一次
        this.log(`河南商都: 服务端异常(返回重复签到但实际未签)，尝试重试...`);
        await appName.wait(2000);
        await this.shangdu_sign_retry();
      } else {
        this.log(`河南商都: 今日已签到 (0019 - 状态查询失败)`);
      }
    } else {
      this.log(`河南商都: 签到失败 - ${code} : ${resSign.result?.msg || resSign.result?.desc}`);
    }
  }

  // 联通云盘任务
  async ltyp_task(isQueryOnly = false) {
    try {
      this.log("============= 联通云盘任务 =============");
      this.cloudDisk = {}; // Reset state for this run
      this.cloudDiskUrls = {
        'onLine': "https://m.client.10010.com/mobileService/onLine.htm",
        'getTicketByNative': "https://m.client.10010.com/edop_ng/getTicketByNative",
        'userticket': "https://panservice.mail.wo.cn/api-user/api/user/ticket",
        'ltypDispatcher': "https://panservice.mail.wo.cn/wohome/dispatcher",
        'query': "https://m.jf.10010.com/jf-external-application/page/query",
        'taskDetail': "https://m.jf.10010.com/jf-external-application/jftask/taskDetail",
        'dosign': "https://m.jf.10010.com/jf-external-application/jftask/sign",
        'doUpload': "https://b.smartont.net/openapi/transfer/quickTransfer",
        'doPopUp': "https://m.jf.10010.com/jf-external-application/jftask/popUp",
        'toFinish': "https://m.jf.10010.com/jf-external-application/jftask/toFinish",
        'lottery': "https://panservice.mail.wo.cn/activity/lottery",
        'activityList': "https://panservice.mail.wo.cn/activity/v1/activityList",
        'userInfo': "https://m.jf.10010.com/jf-external-application/jftask/userInfo",
        'ai_query': "https://panservice.mail.wo.cn/wohome/ai/assistant/query",
        'lottery_times': "https://panservice.mail.wo.cn/activity/lottery/lottery-times",
      };

      if (!this.ecs_token || !this.mobile) {
        this.log("云盘任务: 缺少 ecs_token 或 mobile，跳过。");
        return;
      }

      const ticket = await this.getTicketByNative_cloud();
      if (!ticket) {
        this.log("云盘任务: 获取ticket失败，跳过。");
        return;
      }

      const token = await this.get_ltypDispatcher_cloud(ticket);
      if (!token) {
        this.log("云盘任务: 获取token失败，跳过。");
        return;
      }

      await appName.wait(500);
      await this.get_userInfo_cloud(); // Initial points

      if (isQueryOnly) {
        this.log("云盘任务: [查询模式] 跳过任务及抽奖，仅查询权益...");

        // 同样使用开关控制，避免报错
        const enableLottery = false;

        if (enableLottery) {
          let times = await this.check_lottery_times_cloud(); // 查询抽奖次数
        } else {
          this.log("云盘任务: [查询模式] 抽奖活动已下架，跳过查次数。");
        }

        // [新增] 查询中奖记录
        // 使用 Base64 后的活动ID "MjI=" (即 "22")
        await this.query_cloud_lottery_records(token, "MjI=");
        return;
      }

      await appName.wait(500);
      await this.get_taskDetail_cloud();

      // [UPDATE] 活动抽奖已下架，仅保留AI对话互动(可能仍有积分)，不查次数不抽奖
      const got_chance = await this.do_ai_query_for_lottery_cloud();

      // 设置为 false 以暂时停用抽奖逻辑，但保留代码结构
      const enableLottery = false;

      if (enableLottery && got_chance) {
        await appName.wait(5000);
        let times = await this.check_lottery_times_cloud();
        if (times > 0) {
          for (let i = 0; i < times; i++) {
            this.log(`云盘第 ${i + 1}/${times} 次执行抽奖...`);
            await this.get_ltyplottery_cloud('MjI=');
            await appName.wait(5000);
          }
        }
      } else {
        this.log("云盘任务: 抽奖活动已下架，跳过后续步骤(仅AI互动)。");
      }

      await appName.wait(500);
      await this.get_userInfo_cloud(); // Final points

    } catch (e) {
      this.log(`云盘任务: 出现错误: ${e.message}`);
      console.log(e);
    }
  }

  encrypt_data_cloud(data, key, iv = "wNSOYIB1k1DjY5lA") {
    if (typeof data === 'object') {
      data = JSON.stringify(data);
    }
    const keyHex = cryptoJS.enc.Utf8.parse(key.slice(0, 16));
    const ivHex = cryptoJS.enc.Utf8.parse(iv);
    const encrypted = cryptoJS.AES.encrypt(data, keyHex, {
      iv: ivHex,
      mode: cryptoJS.mode.CBC,
      padding: cryptoJS.pad.Pkcs7
    });
    return encrypted.toString();
  }

  async getTicketByNative_cloud() {
    let requestOptions = {
      fn: "getTicketByNative_cloud",
      method: 'get',
      url: `${this.cloudDiskUrls.getTicketByNative}?appId=edop_unicom_d67b3e30&token=${this.ecs_token}`,
      headers: {
        'User-Agent': "Dalvik/2.1.0 (Linux; U; Android 12; leijun Pro Build/SKQ1.22013.001);unicom{version:android@11.0702}",
        'Connection': "Keep-Alive",
        'Accept-Encoding': "gzip",
      }
    };
    let { result } = await this.request(requestOptions);
    if (result?.ticket) {
      this.cloudDisk.ticket = result.ticket;
      return result.ticket;
    }
    return null;
  }

  async get_ltypDispatcher_cloud(ticket) {
    const timestamp = Date.now().toString();
    const result = Math.floor(Math.random() * (199999 - 123456 + 1)) + 123456;
    const string_to_hash = "HandheldHallAutoLoginV2" + timestamp + result + "wohome";
    const md5Hash = cryptoJS.MD5(string_to_hash).toString();

    const payload = {
      "header": {
        "key": "HandheldHallAutoLoginV2",
        "resTime": timestamp,
        "reqSeq": result,
        "channel": "wohome",
        "version": "",
        "sign": md5Hash
      },
      "body": {
        "clientId": "1001000003",
        "ticket": ticket
      }
    };

    let requestOptions = {
      fn: "get_ltypDispatcher_cloud",
      method: 'post',
      url: this.cloudDiskUrls.ltypDispatcher,
      json: payload,
      headers: {
        'User-Agent': "Dalvik/2.1.0 (Linux; U; Android 12; leijun Pro Build/SKQ1.22013.001);unicom{version:android@11.0702}"
      }
    };

    let { result: res } = await this.request(requestOptions);
    const token = res?.RSP?.DATA?.token;
    if (token) {
      this.cloudDisk.userToken = token;
      return token;
    }
    this.log(`云盘任务: 获取token失败: ${JSON.stringify(res)}`);
    return null;
  }

  async get_userticket_cloud(is_changer = false) {
    if (!this.cloudDisk.userToken) {
      this.log("云盘任务: 获取userticket失败, userToken未获取");
      return null;
    }

    let headers = {};
    if (is_changer) {
      headers = {
        'User-Agent': "LianTongYunPan/4.0.4 (Android 12)",
        'app-type': "liantongyunpanapp",
        'Client-Id': "1001000035",
        'App-Version': "yp-app/4.0.4",
        'Sys-Version': "Android/12",
        'X-YP-Client-Id': "1001000035",
        'X-YP-Access-Token': this.cloudDisk.userToken,
      };
    } else {
      headers = {
        'User-Agent': "Dalvik/2.1.0 (Linux; U; Android 12; leijun Pro Build/SKQ1.22013.001);unicom{version:android@11.0702}",
        'Content-Type': 'application/json',
        'X-YP-Access-Token': this.cloudDisk.userToken,
        'accesstoken': this.cloudDisk.userToken,
        'token': this.cloudDisk.userToken,
        'clientId': "1001000003",
        'X-YP-Client-Id': "1001000003",
        'source-type': "woapi",
        'app-type': "unicom"
      };
    }

    let requestOptions = {
      fn: "get_userticket_cloud",
      method: 'post',
      url: this.cloudDiskUrls.userticket,
      json: {},
      headers: headers
    };

    let { result: res } = await this.request(requestOptions);
    const ticket = res?.result?.ticket;
    if (ticket) {
      this.cloudDisk.userticket = ticket;
      await appName.wait(1000);
      return ticket;
    }
    this.log(`云盘任务: 获取userticket失败: ${JSON.stringify(res)}`);
    return null;
  }

  async get_userInfo_cloud() {
    if (!await this.get_userticket_cloud(false)) return;

    let { result: res, headers } = await this.cloudRequest('userInfo', {}, false, 'post');

    const setCookieHeader = headers?.["set-cookie"];
    if (setCookieHeader) {
      const cookies = Array.isArray(setCookieHeader) ? setCookieHeader : [setCookieHeader];
      const jeaCookie = cookies.find(cookie => cookie && cookie.startsWith("_jea_id="));
      if (jeaCookie) {
        this.cloudDisk.jeaId = jeaCookie.split(";")[0].split("=")[1];
      }
    }

    if (res?.data?.availableScore) {
      const availableScore = res.data.availableScore;
      const allEarnScore = res.data.allEarnScore;
      if (this.cloudDisk.initial_score === undefined) {
        this.cloudDisk.initial_score = parseInt(allEarnScore, 10);
        this.log(`云盘任务: 运行前 - 已赚积分: ${allEarnScore}, 可用积分: ${availableScore}`);
      } else {
        const earned_this_run = parseInt(allEarnScore, 10) - this.cloudDisk.initial_score;
        this.log(`云盘任务: 运行后 - 已赚: ${allEarnScore}, 可用: ${availableScore}, 本次获得: ${earned_this_run}积分`, { notify: true });
      }
    } else {
      this.log(`云盘任务: 获取用户信息失败: ${JSON.stringify(res)}`);
    }
  }

  async get_taskDetail_cloud() {
    if (!await this.get_userticket_cloud(false)) return;

    let { result: res } = await this.cloudRequest('taskDetail', {}, false, 'post');
    if (res?.data?.taskDetail?.taskList) {
      const taskList = res.data.taskDetail.taskList;
      const taskNameList = ["浏览活动中心", "分享文件", "签到", "与AI通通互动", "打开相册自动备份"];
      for (const task of taskList) {
        await appName.wait(500);
        if (task.finishText === "未完成" && taskNameList.some(name => task.taskName.includes(name))) {
          this.log(`云盘任务: 开始执行 [${task.taskName}]`);
          if (task.taskName.includes("浏览活动中心")) {
            await this.toFinish_cloud(task.taskCode, task.taskName, true);
            await this.activityList_cloud(task.taskCode, task.taskName);
          } else if (task.taskName.includes("分享文件")) {
            await this.toFinish_cloud(task.taskCode, task.taskName, false);
            await this.get_ShareFileDispatcher_cloud(task.taskCode, task.taskName);
          } else if (task.taskName.includes("签到")) {
            await this.toFinish_cloud(task.taskCode, task.taskName, false);
            await this.dosign_cloud(task.taskCode, task.taskName);
          } else if (task.taskName.includes("与AI通通互动")) {
            await this.toFinish_cloud(task.taskCode, task.taskName, false);
            await this.do_ai_interaction_cloud(task.taskCode, task.taskName);
          } else if (task.taskName.includes("打开相册自动备份")) {
            await this.toFinish_cloud(task.taskCode, task.taskName, false);

            // Action to simulate opening the album backup page
            if (!await this.get_userticket_cloud(true)) return;
            const payload = { "bizKey": "activityCenterPipeline", "bizObject": { "pageNo": 1 } };
            let { result: res } = await this.cloudRequest('activityList', payload, true);
            if (res?.meta?.code === 0 || res?.meta?.code === "0") {
              this.log(`云盘任务: ✅ [${task.taskName}] 打开成功`);
              await appName.wait(2000);
            } else {
              this.log(`云盘任务: ❌ [${task.taskName}] 打开失败: ${JSON.stringify(res)}`);
            }
          }
        }
        if (task.finishText === "未完成" && task.taskNameSubtitle && task.taskName.includes("手动上传文件")) {
          this.log(`云盘任务: 开始执行 [${task.taskName}]`);
          await this.toFinish_cloud(task.taskCode, task.taskName, false);
          const subtitle = task.taskNameSubtitle;
          const [current_count_str, target_count_str] = subtitle.replace(/[（）]/g, "").split("/");
          let current_count = parseInt(current_count_str, 10);
          let target_count = parseInt(target_count_str, 10);
          if (current_count < target_count) {
            const remaining_times = target_count - current_count;
            this.log(`云盘任务: [${task.taskName}] 需 ${remaining_times} 次`);
            for (let i = 0; i < remaining_times; i++) {
              if (await this.doUpload_cloud(task.taskCode, task.taskName)) {
                this.log(`云盘任务: [${task.taskName}] 第 ${current_count + i + 1} 次上传完成`);
                await appName.wait(500);
              } else {
                break;
              }
            }
          }
        }
      }
    } else {
      this.log(`云盘任务: 获取任务列表失败: ${JSON.stringify(res)}`);
    }
  }

  async cloudRequest(url_name, payload, is_changer = false, method = 'post') {
    const url = this.cloudDiskUrls[url_name];
    if (!url) {
      this.log(`云盘无效的URL名称: ${url_name}`);
      return { result: null, headers: null };
    }

    let headers = {
      'User-Agent': "Dalvik/2.1.0 (Linux; U; Android 12; leijun Pro Build/SKQ1.22013.001);unicom{version:android@11.0702}",
      'Connection': "Keep-Alive",
      'Accept-Encoding': "gzip",
    };

    if (['dosign', 'userInfo', 'doPopUp', 'toFinish', 'taskDetail'].includes(url_name)) {
      if (!this.cloudDisk.userticket) {
        this.log(`云盘 [${url_name}] userticket 未获取`);
        return { result: null, headers: null };
      }
      headers['ticket'] = this.cloudDisk.userticket;
      headers['content-type'] = "application/json;charset=UTF-8";
      headers['partnersid'] = "1649";
      headers['origin'] = "https://m.jf.10010.com";
      if (this.cloudDisk.jeaId) headers['Cookie'] = `_jea_id=${this.cloudDisk.jeaId}`;

      if (is_changer) {
        headers['clienttype'] = "yunpan_unicom_applet";
        headers['x-requested-with'] = "com.sinovatech.unicom.ui";
        if (url_name === 'toFinish') {
          headers['User-Agent'] = "Mozilla/5.0 (Linux; Android 12; Redmi K30 Pro Build/SKQ1.220303.001; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/131.0.6778.39 Mobile Safari/537.36/woapp LianTongYunPan/4.0.4 (Android 12)";
          headers['clienttype'] = "yunpan_android";
          headers['x-requested-with'] = "com.chinaunicom.bol.cloudapp";
        }
      } else {
        headers['clienttype'] = "yunpan_android";
        headers['x-requested-with'] = "com.sinovatech.unicom.ui";
      }
    } else if (url_name === 'activityList') {
      headers = {
        'User-Agent': "Mozilla/5.0 (Linux; Android 12; Redmi K30 Pro Build/SKQ1.220303.001; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/131.0.6778.39 Mobile Safari/537.36/woapp LianTongYunPan/4.0.4 (Android 12)",
        'Accept': "application/json, text/plain, */*",
        'Accept-Encoding': "gzip, deflate, br, zstd",
        'Content-Type': "application/json",
        'credentials': "include",
        'sec-ch-ua-platform': '"Android"',
        'sec-ch-ua': '"Android WebView";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
        'sec-ch-ua-mobile': "?1",
        'Client-Id': "1001000035",
        'App-Version': "yp-app/4.0.4",
        'Access-Token': this.cloudDisk.userToken,
        'Sys-Version': "android/12",
        'Origin': "https://panservice.mail.wo.cn",
        'X-Requested-With': "com.chinaunicom.bol.cloudapp",
        'Sec-Fetch-Site': "same-origin",
        'Sec-Fetch-Mode': "cors",
        'Sec-Fetch-Dest': "empty",
        'Referer': "https://panservice.mail.wo.cn/h5/mobile/wocloud/activityCenter/home",
        'Accept-Language': "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7"
      };
    } else if (url_name === 'doUpload') {
      headers = {
        'User-Agent': "okhttp-okgo/jeasonlzy LianTongYunPan/4.0.4 (Android 12)", 'client-Id': "1001000035",
        'app-version': "yp-app/4.0.4", 'access-token': this.cloudDisk.userToken, 'Content-Type': "application/json;charset=utf-8"
      };
    } else if (url_name === 'ai_query') {
      const model_id = payload.modelId || 1;
      headers = {
        'accept': 'text/event-stream',
        'X-YP-Access-Token': this.cloudDisk.userToken,
        'X-YP-App-Version': '5.0.12',
        'X-YP-Client-Id': '1001000035',
        'User-Agent': 'Mozilla/5.0 (Linux; Android 9; SM-N9810 Build/PQ3A.190705.11211540; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/91.0.4472.114 Mobile Safari/537.36/woapp LianTongYunPan/5.0.12 (Android 9)',
        'Content-Type': 'application/json',
        'Origin': 'https://panservice.mail.wo.cn',
        'X-Requested-With': 'com.chinaunicom.bol.cloudapp',
        'Referer': `https://panservice.mail.wo.cn/h5/wocloud_ai/?modelType=${model_id}&clientId=1001000035&touchpoint=300300010001&token=${this.cloudDisk.userToken}`,
      };
    } else if (url_name === 'lottery_times') {
      method = 'get';
      payload = { activityId: 'MjI=' };
      headers = {
        'X-YP-Access-Token': this.cloudDisk.userToken, 'source-type': 'woapi', 'clientId': '1001000165',
        'token': this.cloudDisk.userToken, 'X-YP-Client-Id': '1001000165',
      };
    } else if (url_name === 'lottery') {
      const activity_id_b64 = payload.activityId || '';
      const activity_id_b64_encoded = encodeURIComponent(activity_id_b64);
      headers = {
        'User-Agent': 'Mozilla/5.0 (Linux; Android 9; SM-N9810 Build/PQ3A.190705.11211540; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/91.0.4472.114 Mobile Safari/537.36/woapp LianTongYunPan/5.0.12 (Android 9)',
        'Accept': 'application/json, text/plain, */*',
        'Content-Type': 'application/json',
        'X-Requested-With': 'com.chinaunicom.bol.cloudapp',
        'requesttime': Date.now().toString(),
        'clientid': '1001000165',
        'x-yp-client-id': '1001000165',
        'source-type': 'woapi',
        'x-yp-access-token': this.cloudDisk.userToken,
        'token': this.cloudDisk.userToken,
        'origin': 'https://panservice.mail.wo.cn',
        'Referer': `https://panservice.mail.wo.cn/h5/activitymobile/blindBox?activityId=${activity_id_b64_encoded}&touchpoint=300300010001&clientId=1001000035&token=${this.cloudDisk.userToken}`,
      };
    }

    let requestOptions = {
      fn: `cloud_${url_name}`, method: method,
      url: method === 'get' ? `${url}?${new URLSearchParams(payload)}` : url,
      headers: headers,
    };

    if (method === 'post') {
      requestOptions.json = payload;
    }

    if (url_name === 'ai_query') {
      const { result, headers } = await this.request(requestOptions);
      // The raw body is in `result` for text/event-stream. Return it as `body`.
      return { result: null, body: result, headers: headers };
    }

    let { result, headers: resHeaders } = await this.request(requestOptions);
    return { result, headers: resHeaders };
  }

  async dosign_cloud(taskcode, taskName) {
    if (!await this.get_userticket_cloud(false)) return;
    const payload = { "taskCode": taskcode };

    let { result: res } = await this.cloudRequest('dosign', payload, false);

    if (res?.code?.includes('0000') && res?.data?.score) {
      this.log(`云盘任务: ✅ [${taskName}] 完成, 获得积分: ${res.data.score}`, { notify: true });
    } else {
      this.log(`云盘任务: ❌ [${taskName}] 失败: ${JSON.stringify(res)}`);
    }
  }

  async toFinish_cloud(taskcode, taskName, is_changer) {
    if (!await this.get_userticket_cloud(is_changer)) return null;
    const payload = { "taskCode": taskcode };

    let { result: res } = await this.cloudRequest('toFinish', payload, is_changer);

    if (res?.code === "0000") return true;
    this.log(`云盘任务: ❌ [${taskName}] toFinish失败: ${JSON.stringify(res)}`);
    return false;
  }

  async doUpload_cloud(taskcode, taskName) {
    if (!await this.get_userticket_cloud(false)) return;
    const payload = {
      "batchNo": "D94628B6C8593D2C6A4B52D0A5F009F4", "deviceId": "", "directoryId": "0", "familyId": 0,
      "fileModificationTime": 1736861613000, "fileName": "mmexport1736861613242.jpg", "fileSize": "280800",
      "fileType": "1", "height": "1174", "lat": "", "lng": "", "psToken": "",
      "sha256": "9c75f5be16bbb4e17788180dfdf4b1d53ba590cb8f4c629e4b337f5f54565949",
      "spaceType": "0", "width": "986"
    };

    let { result: res } = await this.cloudRequest('doUpload', payload, false);

    if (res?.meta?.code === "0000") {
      await appName.wait(1000);
      return await this.doPopUp_cloud(taskcode, taskName, false);
    }
    this.log(`云盘任务: ❌ [${taskName}] 上传失败: ${JSON.stringify(res)}`);
    return false;
  }

  async activityList_cloud(taskcode, taskName) {
    if (!await this.get_userticket_cloud(true)) return;
    const payload = { "bizKey": "activityCenterPipeline", "bizObject": { "pageNo": 1 } };

    let { result: res } = await this.cloudRequest('activityList', payload, true);

    if (res?.meta?.code === 0 || res?.meta?.code === "0") {
      await appName.wait(2000);
      return await this.doPopUp_cloud(taskcode, taskName, true);
    }
    this.log(`云盘任务: ❌ [${taskName}] 浏览活动失败: ${JSON.stringify(res)}`);
    return false;
  }

  async doPopUp_cloud(taskcode, taskName, is_changer) {
    if (!await this.get_userticket_cloud(is_changer)) return;
    const payload = {};
    await appName.wait(5500);

    let { result: res } = await this.cloudRequest('doPopUp', payload, is_changer);

    if ((res?.meta?.code === "0000" || res?.meta?.code === 0) || (res?.code === "0000" || res?.code === 0)) {
      const score = parseInt(res?.data?.score || "0", 10);
      this.log(`云盘任务: ✅ [${taskName}] 完成, ${score > 0 ? `获得积分: ${score}` : '未获得积分'}`);
      return true;
    }
    this.log(`云盘任务: ❌ [${taskName}] 领取奖励失败: ${JSON.stringify(res)}`);
    return false;
  }

  async get_ShareFileDispatcher_cloud(taskCode, taskName) {
    const timestamp = Date.now().toString();
    const randomSeq = Math.floor(Math.random() * (199999 - 123456 + 1)) + 123456;
    const string_to_hash = "ShareFile" + timestamp + randomSeq + "wohome";
    const md5Hash = cryptoJS.MD5(string_to_hash).toString();

    const data = { "fileIds": "f89417024f2642a399fd33f2beebd7c2", "fileFolderIds": "", "days": 7, "clientId": "1001000003" };
    const encrypted = this.encrypt_data_cloud(data, this.cloudDisk.userToken);

    const payload = {
      "header": { "key": "ShareFile", "resTime": timestamp, "reqSeq": randomSeq, "channel": "wohome", "version": "", "sign": md5Hash },
      "body": { "clientId": "1001000003", "param": JSON.stringify(encrypted), "secret": true }
    };

    const headers = { 'client-id': "1001000174", 'x-yp-client-id': "1001000174" };

    let { result: res } = await this.cloudRequest('ltypDispatcher', payload, false, 'post', headers);

    if (res?.STATUS === "200" || res?.STATUS === 200) {
      await this.doPopUp_cloud(taskCode, taskName, false);
    } else {
      this.log(`云盘任务: ❌ [${taskName}] 分享失败: ${JSON.stringify(res)}`);
    }
  }

  async do_ai_interaction_cloud(taskCode, taskName) {
    this.log("云盘任务: 执行AI通通查询请求...");
    const payload = { "input": "Hi", "platform": 1, "modelId": 0, "tag": 0, "conversationId": "", "knowledgeId": "", "referFileInfo": [] };

    let { body } = await this.cloudRequest('ai_query', payload, false, 'post');

    if (body && body.includes('"finish":1')) {
      this.log("云盘任务: AI通通查询请求成功");
      return await this.doPopUp_cloud(taskCode, taskName, false);
    }
    this.log(`云盘任务: ❌ AI通通查询请求失败: ${body}`);
    return false;
  }

  async do_ai_query_for_lottery_cloud() {
    this.log("云盘任务: DeepSeek对话请求, 以获取抽奖资格...");
    const payload = { "input": "Hi", "platform": 1, "modelId": 1, "tag": 0, "conversationId": "", "knowledgeId": "", "referFileInfo": [] };

    let { body } = await this.cloudRequest('ai_query', payload, false, 'post');

    if (body && body.includes('"finish":1')) {
      this.log("云盘任务: DeepSeek对话请求成功");
      return true;
    } else {
      this.log(`云盘任务: ❌ DeepSeek对话请求失败: ${body}`);
      return false;
    }
  }

  async check_lottery_times_cloud() {
    this.log("云盘任务: 正在查询抽奖次数...");
    let { result: res } = await this.cloudRequest('lottery_times', {}, false, 'get');
    if (res?.meta?.code === "200") {
      const times = parseInt(res.result || "0", 10);
      this.log(`云盘任务: 查询成功，剩余抽奖次数: ${times}`);
      return times;
    }
    this.log(`云盘任务: ❌ 查询抽奖次数失败: ${JSON.stringify(res)}`);
    return 0;
  }

  async get_ltyplottery_cloud(activityId_b64) {
    const payload = {
      "bizKey": "newLottery",
      "activityId": activityId_b64,
      "bizObject": { "lottery": { "activityId": activityId_b64, "type": 3 } }
    };

    let { result: res } = await this.cloudRequest('lottery', payload, false, 'post');
    if (res?.meta?.code === '200' && res?.result?.prizeName) {
      this.log(`云盘任务: ✅ 抽奖获得: ${res.result.prizeName}`, { notify: true });
      return true;
    }
    this.log(`云盘任务: ❌ 抽奖失败: ${JSON.stringify(res)}`);
    return false;
  }


  async query_phone_balance() {
    try {
      this.log("正在查询套餐余量...");
      const url = "https://m.client.10010.com/servicequerybusiness/balancenew/accountBalancenew.htm";
      const headers = {
        'User-Agent': "Dalvik/2.1.0 (Linux; U; Android 12; leijun Pro Build/SKQ1.22013.001);unicom{version:android@11.0702}",
        'Accept': 'application/json, text/plain, */*',
        'Cookie': `ecs_token=${this.ecs_token}`
      };

      const { result } = await this.request({
        fn: 'query_phone_balance',
        method: 'get',
        url: url,
        headers: headers
      });

      if (result && result.code === "0000") {
        // Parse info
        let current_balance = "0.00";
        let real_time_fee = "0.00";
        if (result.curntbalancecust) current_balance = parseFloat(result.curntbalancecust).toFixed(2);
        if (result.realfeecust) real_time_fee = parseFloat(result.realfeecust).toFixed(2);

        this.log(`💰 [资产-话费] 当前余额: ${current_balance}元, 实时话费: ${real_time_fee}元`, { notify: true });

        // Parse package details
        if (result.realTimeFeeSpecialFlagThree && Array.isArray(result.realTimeFeeSpecialFlagThree)) {
          this.log(`    📋 [套餐详情]:`, { notify: true });
          for (let item of result.realTimeFeeSpecialFlagThree) {
            if (item.subItems) {
              for (let sub of item.subItems) {
                if (sub.bill) {
                  let name = sub.bill.integrateitem || "未知项";
                  let fee = sub.bill.realfee || "0.00";
                  this.log(`       - ${name}: ${parseFloat(fee).toFixed(2)}元`, { notify: true });
                }
              }
            }
          }
        }
      } else {
        this.log(`套餐余量查询失败: ${result ? result.desc : "无数据"}`);
      }
    } catch (e) {
      this.log(`套餐余量查询异常: ${e.message}`);
    }
  }

  async sign_task(isQueryOnly = false) {
    // 0. 执行套餐余量查询 (新增)
    await this.query_phone_balance();

    if (isQueryOnly) {
      this.log("首页签到: [查询模式] 仅查询话费/积分...");
    }
    await this.sign_getTelephone({ isInitial: true });

    if (isQueryOnly) {
      this.log("首页签到: [查询模式] 跳过签到及任务列表");
      // [新增] 查询签到兑换记录 (静默查询)
      await this.sign_query_my_prizes();
      return;
    }

    await this.sign_getContinuous();
    await this.sign_getTaskList();
    await this.sign_getTelephone();
  }
  async ttlxj_task(isQueryOnly = false) {
    this.rptId = "";
    let targetUrl = "https://epay.10010.com/ci-mps-st-web/?webViewNavIsHidden=webViewNavIsHidden",
      {
        ticket: ticket,
        type: type,
        loc: location
      } = await this.openPlatLineNew(targetUrl);
    if (!ticket) {
      return;
    }
    await this.ttlxj_authorize(ticket, type, location, { isQueryOnly });
  }
  async epay_28_task() {
    this.rptId = "";
    let currentDay = new Date().getDate();
    if (currentDay >= 26 && currentDay <= 28) {
      await this.epay_28_authCheck();
      if (appMonth_28_share.length) {
        let randomShareCode = appName.randomList(appMonth_28_share);
        await this.appMonth_28_bind(randomShareCode);
      }
      await this.appMonth_28_queryChance();
    }
  }
  async draw_28_task() {
    let currentDay = new Date().getDate();
    currentDay == 28 && (await this.draw_28_queryChance());
  }
  async act_517_task() {
    let startTime = new Date("2024-05-10 00:00:00"),
      endTime = new Date("2024-06-09 00:00:00"),
      currentTime = Date.now();
    if (currentTime > startTime.getTime() && currentTime < endTime.getTime()) {
      if (act_517_share.length) {
        let randomShareCode = appName.randomList(act_517_share);
        await this.act_517_bind(randomShareCode);
      }
      await this.act_517_userAccount();
    }
  }
  async card_618_task() {
    let startTime = new Date("2024-05-31 00:00:00"),
      endTime = new Date("2024-06-21 00:00:00"),
      currentTime = Date.now();
    currentTime > startTime.getTime() && currentTime < endTime.getTime() && (this.rptId = "", await this.card_618_authCheck());
  }
  async flmf_task() {
    if (this.city.filter(cityInfo => cityInfo.proCode == "091").length == 0) {
      return;
    }
    let targetUrl = "https://weixin.linktech.hk/lv-web/handHall/autoLogin?actcode=welfareCenter",
      {
        loc: location
      } = await this.openPlatLineNew(targetUrl);
    if (!location) {
      return;
    }
    await this.flmf_login(location);
  }

  async ltzf_task() {
    let targetUrl = new URL("https://wocare.unisk.cn/mbh/getToken");
    targetUrl.searchParams.append("channelType", serviceLife);
    targetUrl.searchParams.append("homePage", "home");
    targetUrl.searchParams.append("duanlianjieabc", "qAz2m");
    let urlString = targetUrl.toString(),
      {
        ticket: ticket
      } = await this.openPlatLineNew(urlString);
    if (!ticket) {
      return;
    }
    if (!(await this.wocare_getToken(ticket))) {
      return;
    }
    for (let activity of wocareActivities) {
      await this.wocare_getDrawTask(activity);
      await this.wocare_loadInit(activity);
    }
  }

  // 重写后的联通阅读任务入口
  async woread_task(isQueryOnly = false) {
    this.log("============= 联通阅读 =============");

    // 1. 登录 (woread_login 内部已经包含了 woread_auth)
    if (!await this.woread_login()) {
      this.log("阅读专区: 登录失败，跳过任务");
      return;
    }

    // 4. 查询红包余额 (对应 query_red)
    // 无论是全量还是查询模式，都查一下余额
    await this.woread_queryTicketAccount();

    if (isQueryOnly) {
      this.log("阅读专区: [查询模式] 跳过阅读及抽奖...");
      this.log("============= 联通阅读执行完毕 =============");
      return;
    }

    // 2. 执行阅读 (对应 Python 的 read_novel)
    await this.woread_read_process();
    await appName.wait(3000);

    // 3. 抽奖 (对应 Python 的 cj)
    await this.woread_draw_new();
    await appName.wait(3000);

    this.log("============= 联通阅读执行完毕 =============");
  }

  // ============================================
  // 新增模块：联通爱听 (移植自 Python)
  // ============================================
  async aiting_task(isQueryOnly = false) {
    this.log("============= 联通爱听 (积分) =============");

    // 1. 登录 (调用之前写好的 aiting_login_flow)
    const loginSuccess = await this.aiting_login_flow();
    if (!loginSuccess) {
      this.log("爱听专区: 登录失败，跳过任务");
      return;
    }

    // 2. 获取业务 Ticket
    this.aiting_biz_ticket = await this.aiting_get_ticket();
    if (!this.aiting_biz_ticket) {
      this.log("爱听专区: 获取Ticket失败");
      return;
    }

    // --- 积分统计准备 ---
    let startScore = 0;
    const startInfo = await this.jf_get_user_info(this.aiting_biz_ticket);
    if (startInfo?.code === '0000' && startInfo?.data) {
      startScore = parseInt(startInfo.data.todayEarnScore || 0);
      // this.log(`运行前状态: 今日已赚 ${startScore} 积分`);
      const totalScore = parseInt(startInfo.data.availableScore || 0);
      this.log(`💰 [资产] 爱听积分余额: ${totalScore} (今日已赚: ${startScore})`);
    }

    if (isQueryOnly) {
      this.log("爱听专区: [查询模式] 跳过签到及做任务...");
      this.log("============= 联通爱听执行完毕 =============");
      return;
    }

    this.log(`运行前状态: 今日已赚 ${startScore} 积分`); // 只有跑任务才需要显示这个详细日志

    // 3. 补充查签到天数 (优先执行)
    await this.aiting_sign_in();

    // 4. 全力做任务
    await this.aiting_do_tasks();

    // --- 积分统计结算 ---
    const endInfo = await this.jf_get_user_info(this.aiting_biz_ticket);
    if (endInfo?.code === '0000' && endInfo?.data) {
      const endScore = parseInt(endInfo.data.todayEarnScore || 0);
      const totalScore = parseInt(endInfo.data.availableScore || 0);
      const earnedThisRun = endScore - startScore;

      this.log(`\n📊 [统计] 本次运行获得: ${earnedThisRun} 积分`, { notify: true });
      this.log(`💰 [资产] 当前可用余额: ${totalScore} 积分`);
      this.log(`📅 [累计] 今日总计获得: ${endScore} 积分`);
    }

    this.log("============= 联通爱听执行完毕 =============");
  }

  // 旧的挂机任务，已废弃
  async woread_reading_task() { }

  async userLoginTask() {
    // ==================== 智能登录逻辑 ====================
    // 如果是抢兑模式 (IS_GRAB_MODE)：总是强制提取新 IP -> 登录 -> 保存
    // 如果是普通模式 (!IS_GRAB_MODE)：优先复用 Token -> 失败再提取 IP 登录

    // 1. 尝试复用 Token (仅限普通模式)
    if (!IS_GRAB_MODE) {
      if (this.loadTokenFromCache()) {
        // 如果本地有 Token，也需要提取 IP (因为用户要求跑任务必须挂代理)
        // 但我们可以先提取 IP，然后 *跳过* 登录接口，直接验证 Token 是否可用
        await this.set_proxy_ip(); // 提取 IP (IP_B)

        // 验证 Token 有效性 (通过一个简单查询接口，如个人信息)
        if (await this.sign_getContinuous()) { // 借用签到查询接口验证
          this.log(`✅ [Token复用] 旧 Token + 新 IP 验证通过，跳过登录步骤！`);
          this.valid = true;
          return;
        } else {
          this.log(`⚠️ [Token复用] 旧 Token 失效，准备重新执行登录流程...`);
          // 失败后继续向下执行标准的登录流程
        }
      }
    }

    // 2. 标准登录流程 (抢兑模式 或 复用失败)
    // 提取 IP (如果上面没提取过)
    // 注意: set_proxy_ip 内部有防重复机制吗？没有，它是覆盖。没关系。
    await this.set_proxy_ip();

    // 执行登录
    if (await this.onLine()) {
      this.valid = true;
      // 登录成功后，保存 Token
      this.saveTokenToCache();
    } else {
      this.valid = false;
    }
  }

  async userTask() {
    // 修改日志标题，包含手机号
    appName.log(`\n------------------ 账号[${this.index}][${maskStr(this.name)}] ------------------`);
    this.log = (message, options = {}) => super.log(message, { ...options, hideName: true });

    // [新增] 智能调度：9点或15点 -> 仅运行爱听补跑
    const nowHour = new Date().getHours();

    // 定点运行时间 (兼容 Cron 表达式: 7,9,15,20)
    // 如果不在定点时间手动运行，则视为“查询模式”
    // 注意：爱听补跑(9,15) 属于特殊定点，这里我们将其视为“非全量任务”时间
    // 为了逻辑清晰，我们定义：
    //  - 7, 20: 全量跑 (isQueryOnly = false)
    //  - 9, 15: 爱听补跑 (独立逻辑)
    //  - 其他时间: 查询模式 (isQueryOnly = true)

    if (nowHour === 9 || nowHour === 15) {
      if (!aitingDisabled) {
        this.log(`🚀 [智能调度] 检测到当前为 ${nowHour}点，自动切换至 [仅爱听补跑模式(避开冲突)]...`);
        await this.aiting_task(false); // 爱听任务在补跑时是全量执行的
        return;
      } else {
        this.log(`🚫 [智能调度] 检测到 ${nowHour}点，但爱听任务已禁用，改为执行 [仅查询模式]...`);
        // 不 return，让它继续走下面的查询模式逻辑
      }
    }

    const scheduledHours = [7, 20];
    let isQueryOnly = !scheduledHours.includes(nowHour);

    // [新增] 环境变量控制：强制运行任务 (跳过时间限制)
    if (process.env.CHINA_UNICOM_FORCE_TASK === 'true' || process.env.CHINA_UNICOM_FORCE_TASK === '1') {
      isQueryOnly = false;
      this.log(`🚀 [环境变量] 检测到 CHINA_UNICOM_FORCE_TASK，强制执行全量任务...`);
    }

    if (isQueryOnly) {
      this.log(`🔍 [手动模式] 检测到非定点时间(${nowHour}点)，进入 [仅查询模式]...`);
      this.log(`ℹ️ 在此模式下，脚本将只查询资产(话费/积分/奖品)，不执行耗时任务。`);
    } else {
      this.log(`🍵 [定点模式] 检测到定点时间(${nowHour}点)，开始执行全套日常任务...`);
    }

    // 1. 首页签到
    if (!signDisabled) {
      await this.sign_task(isQueryOnly);
    }

    // 2. 天天领现金
    await this.ttlxj_task(isQueryOnly);

    // 3. 联通祝福 (查询模式跳过)
    if (!ltzfDisabled && !isQueryOnly) {
      await this.ltzf_task();
    }

    // 4. 权益超市 (已升级全局缓存)
    await this.marketTask(isQueryOnly);

    // 5. 联通阅读
    await this.woread_task(isQueryOnly);

    // 【新增】在这里插入爱听任务 (可通过环境变量禁用)
    if (!aitingDisabled) {
      await this.aiting_task(isQueryOnly);
    }

    // 6. 安全管家
    await this.securityButlerTask(isQueryOnly);

    // 7. 联通云盘
    await this.ltyp_task(isQueryOnly);

    // 8. [新增] 沃云手机 (查询模式跳过，暂无查询接口)
    if (!isQueryOnly) {
      await this.wostore_cloud_task();
    }

    // 9. [新增] 区域专区 (新疆/河南自动识别)
    await this.regional_task(isQueryOnly);
  }
  // ==================== 爱听专区工具函数 ====================

  // 1. 生成随机 IMEI (带 Luhn 校验)
  generate_random_imei() {
    const tac = Array.from({ length: 8 }, () => Math.floor(Math.random() * 10)).join('');
    const snr = Array.from({ length: 6 }, () => Math.floor(Math.random() * 10)).join('');
    const imeiWithoutCheck = tac + snr;

    // Luhn 算法计算校验位
    const digits = imeiWithoutCheck.split('').map(Number);
    for (let i = digits.length - 1; i >= 0; i -= 2) {
      digits[i] *= 2;
      if (digits[i] > 9) digits[i] -= 9;
    }
    const total = digits.reduce((a, b) => a + b, 0);
    const checkDigit = (10 - (total % 10)) % 10;

    return imeiWithoutCheck + checkDigit;
  }

  // 2. 通用 AES 加密 (修复版)
  aiting_get_aes(data, key) {
    // 【关键修复】Python里有一个 [::-1] 反转操作，所以真实的IV是下面这个
    const ivStr = "16-Bytes--String";
    const keyHex = cryptoJS.enc.Utf8.parse(key.substring(0, 16));
    const ivHex = cryptoJS.enc.Utf8.parse(ivStr.substring(0, 16));

    // Python 的 json.dumps(separators=(',', ':')) 对应 JS 的 JSON.stringify
    // 注意：如果是字符串直接加密，就不 stringify
    const text = typeof data === 'object' ? JSON.stringify(data) : data;

    const encrypted = cryptoJS.AES.encrypt(text, keyHex, {
      iv: ivHex,
      mode: cryptoJS.mode.CBC,
      padding: cryptoJS.pad.Pkcs7
    });

    // 提取 ciphertext 转 Hex，再转 Base64
    const hexStr = encrypted.ciphertext.toString(cryptoJS.enc.Hex); // 小写Hex
    const base64Str = cryptoJS.enc.Base64.stringify(cryptoJS.enc.Utf8.parse(hexStr));

    return base64Str;
  }

  // 3. 另一种 AES 加密 (对应 Python 的 aes_encrypt)
  // Python逻辑：AES加密 -> 转Hex大写 -> 转Base64
  aiting_aes_encrypt(data, key, iv) {
    const keyHex = cryptoJS.enc.Utf8.parse(key);
    const ivHex = cryptoJS.enc.Utf8.parse(iv);

    const text = typeof data === 'object' ? JSON.stringify(data) : data;

    const encrypted = cryptoJS.AES.encrypt(text, keyHex, {
      iv: ivHex,
      mode: cryptoJS.mode.CBC,
      padding: cryptoJS.pad.Pkcs7
    });

    // 区别在这里：Python 转了大写 Hex
    const hexStr = encrypted.ciphertext.toString(cryptoJS.enc.Hex).toUpperCase();
    const base64Str = cryptoJS.enc.Base64.stringify(cryptoJS.enc.Utf8.parse(hexStr));

    return base64Str;
  }

  // 4. MD5 签名 (对应 Python 的 md5_sign)
  aiting_md5(text) {
    return cryptoJS.MD5(text).toString();
  }

  // 5. 参数签名生成 (对应 Python 的 generate_sign)
  aiting_generate_sign(params, key) {
    // 按 key 排序
    const sortedKeys = Object.keys(params).sort();
    const signStr = sortedKeys.map(k => `${k}=${params[k]}`).join('&');
    const finalStr = `${signStr}&key=${key}`;
    return this.aiting_md5(finalStr);
  }

  // 6. 生成时间戳 (13位)
  aiting_timestamp() {
    return Date.now().toString();
  }

  // 7. 生成随机 Nonce
  aiting_nonce() {
    return Math.floor(Math.random() * (999999 - 100000 + 1) + 100000).toString();
  }
  // ==================== 爱听专区：辅助函数 ====================

  aiting_generate_woid(imei) {
    const random6 = appName.randomString(6);
    const imei8 = imei.length >= 8 ? imei.substring(0, 8) : imei.padEnd(8, '0');
    const random4 = appName.randomString(4);
    const random2 = appName.randomString(2);
    return `WOA${random6}${imei8}LOT${random4}LV${random2}`;
  }

  aiting_calculate_clientconfirm(userid, imei) {
    const plaintext = "android" + userid + imei;
    // 使用 Step 1 实现的 aes_encrypt (转大写Hex的那种)
    return this.aiting_aes_encrypt(plaintext, AITING_AES_KEY, AITING_AES_IV);
  }

  aiting_calculate_passcode(timestamp, phone) {
    return this.aiting_md5(timestamp + phone + AITING_CLIENT_KEY);
  }

  aiting_build_statisticsinfo(userid, useraccount, imei, clientconfirm) {
    const params = {
      'channelid': '28015001',
      'sid': appName.randomString(20, "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_@"),
      'eid': appName.randomString(20, "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_"),
      'osversion': 'Android12',
      'clientallid': '000000100000000000058.0.2.1225',
      'display': '2400_1080',
      'ip': '192.168.3.24',
      'nettypename': 'wifi',
      'version': '802',
      'versionname': '8.0.2',
      'terminalName': 'Redmi',
      'terminalType': 'Redmi_K30_Pro',
      'udid': 'null',
      'woid': this.aiting_generate_woid(imei),
      'useraccount': useraccount,
      'userid': userid,
      'clientconfirm': clientconfirm
    };
    return Object.keys(params).map(k => `${k}=${params[k]}`).join('&');
  }

  // ==================== 爱听专区：核心登录 API ====================

  // 1. 沃阅读基础登录
  async aiting_woread_login(phone) {
    // 加密手机号
    const phoneEnc = this.aiting_get_aes(phone, WOREAD_KEY);
    const dataObj = { "phone": phoneEnc };

    // 二次加密 (带时间戳)
    const timestamp = appName.time("yyyyMMddhhmmss");
    const dataToEncrypt = { ...dataObj, "timestamp": timestamp };
    const signResult = this.aiting_get_aes(dataToEncrypt, WOREAD_KEY);

    const url = "https://10010.woread.com.cn/ng_woread_service/rest/account/login";
    const body = { "sign": signResult };

    const { result } = await this.request({
      fn: 'aiting_woread_login',
      method: 'post',
      url: url,
      json: body,
      headers: {
        "User-Agent": "Mozilla/5.0 (Linux; Android 11; Redmi Note 10 Pro) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/92.0.4515.159 Mobile Safari/537.36",
        "accesstoken": "ODZERTZCMjA1NTg1MTFFNDNFMThDRDYw",
        "Content-Type": "application/json;charset=UTF-8",
        "Origin": "https://10010.woread.com.cn",
        "Referer": "https://10010.woread.com.cn/ng_woread/"
      }
    });

    if (result && result.data && result.data.userid) {
      return result.data; // 包含 userid, token, phone 等
    }
    return null;
  }

  // 2. 获取 JWT Token
  async aiting_get_jwt_token(statisticsinfo) {
    const timestamp = this.aiting_timestamp();
    const signParams = {
      'clientSource': '3',
      'clientId': 'android',
      'source': '3',
      'timestamp': timestamp
    };
    const sign = this.aiting_generate_sign(signParams, AITING_SIGN_KEY_APPKEY);

    const clientIdB64 = cryptoJS.enc.Base64.stringify(cryptoJS.enc.Utf8.parse("395DEDE9C1D6FE11B7C9C0D82B353E74"));

    const body = {
      'clientSource': '3',
      'clientId': clientIdB64,
      'source': '3',
      'timestamp': timestamp,
      'sign': sign
    };

    const { result } = await this.request({
      fn: 'aiting_jwt',
      method: 'post',
      url: `${AITING_BASE_URL}/oauth/client/appkey`,
      json: body,
      headers: {
        'Skip-Authorization-Check': 'true',
        'statisticsinfo': statisticsinfo
      }
    });

    if (result && result.code === '0000' && result.key) {
      return result.key;
    }
    return null;
  }
  // 2.5 获取个人资料 (补充步骤)
  async aiting_get_read_profile(userToken, userid, jwtToken, statisticsinfo) {
    const reqTime = this.aiting_timestamp();
    const nonce = this.aiting_nonce();

    const signParams = {
      'jwt': jwtToken,
      'nonestr': nonce,
      'osversion': 'Android12',
      'terminalName': 'Redmi',
      'timestamp': reqTime
    };

    const sortedKeys = Object.keys(signParams).sort();
    const signStr = sortedKeys.map(k => `${k}=${signParams[k]}`).join('&');
    const requertid = this.aiting_md5(`${signStr}&key=${AITING_SIGN_KEY_REQUERTID}`);

    const url = `${AITING_BASE_URL}/pcc/rest/sns/profile/readprofile/7`;

    const { result } = await this.request({
      fn: 'aiting_profile',
      method: 'get',
      url: url,
      searchParams: {
        'userid': userid,
        'token': userToken,
        'encryptflag': '1'
      },
      headers: {
        'User-Agent': 'okhttp/4.9.0',
        'requerttime': reqTime,
        'nonestr': nonce,
        'requertid': requertid,
        'AuthorizationClient': `Bearer ${jwtToken}`,
        'statisticsinfo': statisticsinfo
      }
    });

    if (result && result.code === '0000' && result.message) {
      return result.message; // 包含 mobile 等信息
    }
    return null;
  }
  // 3. 爱听业务登录 (最终登录)
  async aiting_api_login(phone, useraccount, jwt_token, statisticsinfo) {
    const timestamp = appName.time("yyyyMMddhhmmss");
    const passcode = this.aiting_calculate_passcode(timestamp, phone);

    const queryParams = [
      'networktype=3', 'ua=Redmi+K30+Pro', 'isencode=true',
      'clientversion=8.0.2', 'versionname=Android_1_1080x2356',
      'channelid=28015001', 'userlabelisencode=1', 'validatecode=', 'sid=',
      `timestamp=${timestamp}`, `passcode=${passcode}`
    ].join('&');

    const url = `${AITING_BASE_URL}/mainrest/rest/read/user/ulogin//3/${useraccount}/1/1/0?${queryParams}`;

    const reqTime = this.aiting_timestamp();
    const nonce = this.aiting_nonce();

    const signParams = {
      'jwt': jwt_token,
      'nonestr': nonce,
      'osversion': 'Android12',
      'terminalName': 'Redmi',
      'timestamp': reqTime
    };

    // 生成 requertid
    const sortedKeys = Object.keys(signParams).sort();
    const signStr = sortedKeys.map(k => `${k}=${signParams[k]}`).join('&');
    const requertid = this.aiting_md5(`${signStr}&key=${AITING_SIGN_KEY_REQUERTID}`);

    const { result } = await this.request({
      fn: 'aiting_user_login',
      method: 'get',
      url: url,
      headers: {
        'statisticsinfo': statisticsinfo,
        'requerttime': reqTime,
        'nonestr': nonce,
        'requertid': requertid,
        'AuthorizationClient': `Bearer ${jwt_token}`,
        'User-Agent': 'okhttp/4.9.0'
      }
    });

    if (result && result.code === '0000' && result.message) {
      // 提取 token 和 userid
      let token = result.message.token;
      let userid = result.message.userid;
      if (result.message.accountinfo) {
        token = result.message.accountinfo.token || token;
        userid = result.message.accountinfo.userid || userid;
      }
      return { token, userid };
    }
    return null;
  }

  // 4. 完整的登录流程封装
  async aiting_login_flow() {
    this.log("开始爱听登录流程...");
    const phone = this.mobile;
    const imei = this.generate_random_imei();

    // Step A: 沃阅读基础登录 (优化：复用已有Token)
    if (this.woread_token && this.woread_userid) {
      this.log("✅ 检测到已有阅读专区凭证，复用登录...");
      this.aiting_woread_token = this.woread_token;
      this.aiting_base_userid = this.woread_userid;
    } else {
      const woreadData = await this.aiting_woread_login(phone);
      if (!woreadData) { this.log("❌ 沃阅读基础登录失败"); return false; }
      this.aiting_woread_token = woreadData.token;
      this.aiting_base_userid = woreadData.userid;
      this.log("✅ 沃阅读基础登录成功");
    }

    // Step B1: 初次构建 Header 统计信息 (用原始手机号)
    let clientconfirm = this.aiting_calculate_clientconfirm(this.aiting_base_userid, imei);
    let temp_stats = this.aiting_build_statisticsinfo(this.aiting_base_userid, phone, imei, clientconfirm);

    // Step C: 获取 JWT
    this.aiting_jwt = await this.aiting_get_jwt_token(temp_stats);
    if (!this.aiting_jwt) { this.log("❌ 获取 JWT 失败"); return false; }
    this.log("✅ 获取 JWT 成功");

    // ================== 新增步骤 START ==================
    // Step C2: 获取 Profile 以拿到真实的 UserAccount
    const profileMsg = await this.aiting_get_read_profile(this.aiting_woread_token, this.aiting_base_userid, this.aiting_jwt, temp_stats);
    if (!profileMsg || !profileMsg.mobile) {
      this.log("❌ 获取个人资料失败 (无法获取 real_useraccount)");
      return false;
    }
    const real_useraccount = profileMsg.mobile;
    // this.log(`获取到真实 UserAccount: ${real_useraccount}`);

    // Step C3: 重新构建 Header (使用 real_useraccount)
    // 注意：clientconfirm 依赖 userid 和 imei，这两个没变，所以不用重新算
    // 但是 statisticsinfo 必须用 real_useraccount 重新生成
    this.aiting_statisticsinfo = this.aiting_build_statisticsinfo(this.aiting_base_userid, real_useraccount, imei, clientconfirm);
    // ================== 新增步骤 END ====================

    // Step D: 爱听业务登录 (注意参数：第二个参数用 real_useraccount)
    const loginData = await this.aiting_api_login(phone, real_useraccount, this.aiting_jwt, this.aiting_statisticsinfo);
    if (!loginData) { this.log("❌ 爱听业务登录失败"); return false; }

    this.aiting_token = loginData.token;
    this.aiting_userid = loginData.userid;
    this.log(`✅ 爱听业务登录成功! Token已获取`);

    return true;
  }
  // ==================== 爱听专区：业务逻辑 ====================

  // 5. 获取业务 Ticket (通往积分任务的钥匙)
  async aiting_get_ticket() {
    const timestamp = this.aiting_timestamp();

    // 构造内部签名
    const signParams = {
      'timestamp': timestamp,
      'token': this.aiting_token,
      'userid': this.aiting_userid
    };
    const sign = this.aiting_generate_sign(signParams, AITING_SIGN_KEY_API);

    // 构造 RequertId
    const nonce = this.aiting_nonce();
    const headSignParams = {
      'jwt': this.aiting_jwt,
      'nonestr': nonce,
      'osversion': 'Android12',
      'terminalName': 'Redmi',
      'timestamp': timestamp
    };
    const sortedKeys = Object.keys(headSignParams).sort();
    const signStr = sortedKeys.map(k => `${k}=${headSignParams[k]}`).join('&');
    const requertid = this.aiting_md5(`${signStr}&key=${AITING_SIGN_KEY_REQUERTID}`);

    const url = `${AITING_BASE_URL}/activity/rest/unicom/points/getInfoTicket`;

    const { result } = await this.request({
      fn: 'aiting_ticket',
      method: 'post',
      url: url,
      json: {
        'sign': sign,
        'timestamp': timestamp,
        'token': this.aiting_token,
        'userid': this.aiting_userid
      },
      headers: {
        'AuthorizationClient': `Bearer ${this.aiting_jwt}`,
        'requerttime': timestamp,
        'nonestr': nonce,
        'requertid': requertid,
        'statisticsinfo': this.aiting_statisticsinfo
      }
    });

    if (result && result.code === '0000' && result.message) {
      // Ticket 藏在 message 的 URL 参数里，需要提取
      try {
        const ticketUrl = new URL(result.message);
        const ticket = ticketUrl.searchParams.get("ticket");
        if (ticket) return ticket;
      } catch (e) {
        // 备用提取方案
        const match = result.message.match(/ticket=([^&]+)/);
        if (match) return match[1];
      }
    }
    return null;
  }

  // 6. 每日签到 (UA修正 + 调试版)
  async aiting_sign_in() {
    this.log(`准备执行签到...`);

    const timestamp = this.aiting_timestamp();
    const nonce = this.aiting_nonce();

    // 1. 构造 requertid (和Py截图一致)
    const signParams = {
      'jwt': this.aiting_jwt,
      'nonestr': nonce,
      'osversion': 'Android12',
      'terminalName': 'Redmi',
      'timestamp': timestamp
    };
    const sortedKeys = Object.keys(signParams).sort();
    const signStr = sortedKeys.map(k => `${k}=${signParams[k]}`).join('&');
    const requertid = this.aiting_md5(`${signStr}&key=${AITING_SIGN_KEY_REQUERTID}`);

    // 2. 构造 URL (注意路径里的 userid 和 token)
    const url = `https://woread.com.cn/rest/read/usersign/sign/3/${this.aiting_base_userid}/${this.aiting_woread_token}`;

    // 3. 构造 Headers (和Py截图一致，UA用okhttp)
    const headers = {
      'Content-Type': 'application/json',
      'statisticsinfo': this.aiting_statisticsinfo,
      'requerttime': timestamp,
      'nonestr': nonce,
      'requertid': requertid,
      'AuthorizationClient': `Bearer ${this.aiting_jwt}`,
      'User-Agent': 'okhttp/4.9.0'
    };

    // 4. 构造 Params (Py截图里的 params)
    const qs = {
      'isresign': '0',
      'isnewversion': '1',
      'isfreeLimt': '0'
    };

    const { result } = await this.request({
      fn: 'aiting_sign_new',
      method: 'get',
      url: url,
      searchParams: qs,
      headers: headers
    });

    if (result && result.code === '0000') {
      const days = result.continuousDays || 0;
      const msg = result.desc || result.message || "成功";
      this.log(`爱听签到: ✅ ${msg} (连续 ${days} 天)`);
    } else {
      this.log(`爱听签到: ❌ ${result ? (result.desc || result.message) : '请求失败'}`);
    }
  }

  // 7. 查询积分信息
  async jf_get_user_info(ticket) {
    const url = "https://m.jf.10010.com/jf-external-application/jftask/userInfo";
    const { result } = await this.request({
      fn: 'jf_info', method: 'post', url: url,
      json: {},
      headers: this.get_jf_headers(ticket)
    });
    if (result && result.code === '0000' && result.data) {
      const today = result.data.todayEarnScore || 0;
      const total = result.data.availableScore || 0;
      this.log(`积分概览: 今日已赚 ${today}, 当前余额 ${total}`, { notify: true });
    }
  }
  // ==================== 爱听专区：底层请求修正 (UA修复版) ====================

  // 通用请求头生成
  get_jf_headers(ticket) {
    return {
      'ticket': ticket,
      'pageid': 's789081246969976832',
      'clienttype': 'aiting_android',
      'partnersid': '1706',
      'content-type': 'application/json;charset=UTF-8',
      // 【关键修正】必须用 WebView 的 UA，否则领不到奖
      'User-Agent': 'Mozilla/5.0 (Linux; Android 12; Redmi K30 Pro Build/SKQ1.220303.001; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/92.0.4515.159 Mobile Safari/537.36 WoReaderApp/Android',
      'Origin': 'https://m.jf.10010.com',
      'Referer': `https://m.jf.10010.com/jf-external-application/index.html?ticket=${ticket}&pageID=s789081246969976832`
    };
  }

  // 8. 获取任务列表
  async jf_get_task_detail(ticket) {
    const url = "https://m.jf.10010.com/jf-external-application/jftask/taskDetail";
    const { result } = await this.request({
      fn: 'jf_list',
      method: 'post',
      url: url,
      json: {},
      headers: this.get_jf_headers(ticket)
    });
    return result?.data?.taskDetail?.taskList || [];
  }

  // 9. 接任务
  async jf_to_finish(ticket, taskCode) {
    const url = "https://m.jf.10010.com/jf-external-application/jftask/toFinish";
    await this.request({
      fn: 'jf_finish', method: 'post', url: url,
      json: { 'taskCode': taskCode },
      headers: this.get_jf_headers(ticket)
    });
  }

  // 10. 领奖励
  async jf_pop_up(ticket) {
    const url = "https://m.jf.10010.com/jf-external-application/jftask/popUp";
    const { result } = await this.request({
      fn: 'jf_popup', method: 'post', url: url,
      json: {},
      headers: this.get_jf_headers(ticket)
    });
    return result;
  }

  // 11. 辅助任务完成 (通知类任务用)
  async aiting_complete_task_api(type) {
    const timestamp = this.aiting_timestamp();
    const nonce = this.aiting_nonce();

    // Header 签名
    const signParams = { 'jwt': this.aiting_jwt, 'nonestr': nonce, 'osversion': 'Android12', 'terminalName': 'Redmi', 'timestamp': timestamp };
    const signStr = Object.keys(signParams).sort().map(k => `${k}=${signParams[k]}`).join('&');
    const requertid = this.aiting_md5(`${signStr}&key=${AITING_SIGN_KEY_REQUERTID}`);

    // Body 签名
    const bodySignParams = { 'source': '3', 'timestamp': timestamp, 'token': this.aiting_woread_token, 'type': type.toString(), 'userid': this.aiting_base_userid };
    const bodySignStr = Object.keys(bodySignParams).sort().map(k => `${k}=${bodySignParams[k]}`).join('&');
    const sign = this.aiting_md5(`${bodySignStr}&key=${AITING_SIGN_KEY_API}`);

    await this.request({
      fn: 'aiting_comp',
      method: 'post',
      url: `${AITING_BASE_URL}/activity/rest/unicom/points/completiontask`,
      json: { ...bodySignParams, 'sign': sign },
      headers: {
        'AuthorizationClient': `Bearer ${this.aiting_jwt}`, 'requerttime': timestamp, 'nonestr': nonce, 'requertid': requertid, 'statisticsinfo': this.aiting_statisticsinfo
      }
    });
  }

  // 12. 获取阅读密钥 (SecretKey)
  async aiting_get_secretkey() {
    const timestamp = this.aiting_timestamp();
    const nonce = this.aiting_nonce();
    const signParams = { 'jwt': this.aiting_jwt, 'nonestr': nonce, 'osversion': 'Android12', 'terminalName': 'Redmi', 'timestamp': timestamp };
    const signStr = Object.keys(signParams).sort().map(k => `${k}=${signParams[k]}`).join('&');
    const requertid = this.aiting_md5(`${signStr}&key=${AITING_SIGN_KEY_REQUERTID}`);

    const url = `https://woread.com.cn/rest/read/statistics/getsecretkey/3/${this.aiting_base_userid}`;
    const { result } = await this.request({
      fn: 'aiting_sk', method: 'get', url: url,
      searchParams: { 'token': this.aiting_woread_token },
      headers: { 'AuthorizationClient': `Bearer ${this.aiting_jwt}`, 'requerttime': timestamp, 'nonestr': nonce, 'requertid': requertid, 'statisticsinfo': this.aiting_statisticsinfo, 'User-Agent': 'okhttp/4.9.0' }
    });
    return (result && result.code === '0000') ? result.message : null;
  }

  // 13. 模拟阅读 (上报时长) - 修正书籍ID
  async aiting_add_read_time(readTimeSeconds) {
    const secretkey = await this.aiting_get_secretkey();
    if (!secretkey) return;

    const timestamp = this.aiting_timestamp();
    const countTimeStr = (readTimeSeconds * 1000).toString();

    // 统一书籍ID，防止服务端校验失败
    const bookId = "4524960";

    const dataObj = {
      "userid": this.aiting_base_userid,
      "counttime": countTimeStr,
      "timestamp": timestamp,
      "secretkey": secretkey,
      "cntindex": bookId, // 修正
      "cnttype": 1,
      "readtype": 1
    };

    const encrypted = this.aiting_aes_encrypt(dataObj, ADDREADTIME_AES_KEY, AITING_AES_IV);

    const nonce = this.aiting_nonce();
    const signParams = { 'jwt': this.aiting_jwt, 'nonestr': nonce, 'osversion': 'Android12', 'terminalName': 'Redmi', 'timestamp': timestamp };
    const signStr = Object.keys(signParams).sort().map(k => `${k}=${signParams[k]}`).join('&');
    const requertid = this.aiting_md5(`${signStr}&key=${AITING_SIGN_KEY_REQUERTID}`);

    const url = `https://woread.com.cn/rest/read/statistics/addreadtime/3/${encrypted}`;
    const randomUuid = appName.randomUuid().replace(/-/g, '');

    const { result } = await this.request({
      fn: 'aiting_addtime',
      method: 'post',
      url: url,
      json: {
        "channelid": "28015001", "creadertime": appName.time("yyMMddhhmmss"),
        "imei": this.generate_random_imei(),
        "list": { "cntindex": bookId, "cnttype": 1, "readtime": countTimeStr, "readtype": 1 },
        "list1": [{ "cntindex": bookId, "cnttype": 1, "readtime": countTimeStr, "readtype": 1 }],
        "listentimes": countTimeStr, "uuid": randomUuid
      },
      headers: {
        'AuthorizationClient': `Bearer ${this.aiting_jwt}`, 'requerttime': timestamp, 'nonestr': nonce, 'requertid': requertid, 'statisticsinfo': this.aiting_statisticsinfo, 'User-Agent': 'okhttp/4.9.0'
      }
    });
    // 打印上报结果，方便调试
    // if (result) this.log(`上报结果: ${JSON.stringify(result)}`);
  }

  // 14. 模拟阅读 (Start)
  async aiting_new_read_add() {
    const timestamp = this.aiting_timestamp();
    const nonce = this.aiting_nonce();
    const signParams = { 'jwt': this.aiting_jwt, 'nonestr': nonce, 'osversion': 'Android12', 'terminalName': 'Redmi', 'timestamp': timestamp };
    const signStr = Object.keys(signParams).sort().map(k => `${k}=${signParams[k]}`).join('&');
    const requertid = this.aiting_md5(`${signStr}&key=${AITING_SIGN_KEY_REQUERTID}`);

    const url = `https://woread.com.cn/rest/read/new/newreadadd/3/${this.aiting_base_userid}/${this.aiting_woread_token}`;
    await this.request({
      fn: 'aiting_read_start', method: 'post', url: url,
      searchParams: { 'isfreeLimt': '0', 'isgray': 'true' },
      json: { "source": 3, "cntindex": "4524960", "chapterallindex": "100136247350", "readtype": 3 },
      headers: { 'AuthorizationClient': `Bearer ${this.aiting_jwt}`, 'requerttime': timestamp, 'nonestr': nonce, 'requertid': requertid, 'statisticsinfo': this.aiting_statisticsinfo, 'User-Agent': 'Redmi K30 Pro' }
    });
  }
  async aiting_do_tasks() {
    this.log("正在获取任务列表...");
    const taskList = await this.jf_get_task_detail(this.aiting_biz_ticket);

    // 【新增功能】 先展示已完成的任务
    // ============================================
    const doneList = taskList.filter(t => t.finish === 1);
    if (doneList.length > 0) {
      this.log(`已完成任务:`);
      doneList.forEach(t => {
        // 打印格式：  ✅ 任务名 (进度/总数)
        this.log(`  ✅ ${t.taskName} (${t.finishCount}/${t.needCount})`);
      });
      this.log("-".repeat(20)); // 打印个分割线好看点
    }

    // ============================================
    // 筛选待办任务 (finish=0 且 不是邀请任务)
    // ============================================
    const todoList = taskList.filter(t =>
      t.finish === 0 && !t.taskName.includes("邀请")
    );

    if (todoList.length === 0) {
      this.log("爱听任务: ✅ 所有任务已完成");
      return;
    }
    this.log(`爱听任务: 发现 ${todoList.length} 个待办任务`);

    // ============================================
    // A. 阅读/听读任务 (Py逻辑 + 打印小数点)
    // ============================================
    // 【修改点】一定要加上 && !t.taskName.includes("邀请")
    const readTasks = todoList.filter(t =>
      (t.taskName.includes("阅读") || t.taskName.includes("听读")) &&
      !t.taskName.includes("邀请")
    );
    for (const task of readTasks) {
      const remaining = (task.needCount || 1) - (task.finishCount || 0);
      if (remaining <= 0) continue;

      this.log(`执行阅读任务: ${task.taskName} (剩余 ${remaining} 次)`);

      for (let i = 0; i < remaining; i++) {
        await this.jf_to_finish(this.aiting_biz_ticket, task.taskCode); // 接任务

        this.log(`  └─ 第 ${i + 1}/${remaining} 次: 极速提交中(等待5秒)...`);
        await this.aiting_new_read_add();
        // 等待5秒是为了防止请求太快触发WAF，也能保证代理IP不过期
        await appName.wait(5000);
        // 直接告诉服务器：我已经读了120秒了
        await this.aiting_add_read_time(120);
        await appName.wait(2000);

        const res = await this.jf_pop_up(this.aiting_biz_ticket); // 领奖
        if (res?.data?.score) this.log(`  └─ 🎉 获得 ${res.data.score} 积分`, { notify: true });
        await appName.wait(2000);
      }
    }

    // ============================================
    // B. 通知任务 (Type=2)
    // ============================================
    const notifyTask = todoList.find(t => t.taskName.includes("通知"));
    if (notifyTask) {
      this.log(`执行通知任务: ${notifyTask.taskName}`);
      await this.jf_to_finish(this.aiting_biz_ticket, notifyTask.taskCode);
      await appName.wait(1000);
      await this.aiting_complete_task_api(2);
      await appName.wait(2000);
      const res = await this.jf_pop_up(this.aiting_biz_ticket);
      if (res?.data?.score) this.log(`  └─ 获得 ${res.data.score} 积分`, { notify: true });
    }

    // ============================================
    // C. 通用任务 (分享/签到/其他) (Type=4)
    // ============================================
    const otherTasks = todoList.filter(t =>
      !t.taskName.includes("通知") &&
      !t.taskName.includes("阅读") &&
      !t.taskName.includes("听读") &&
      !t.taskName.includes("邀请") &&
      !t.taskName.includes("签到")
    );

    for (const task of otherTasks) {
      const remaining = (task.needCount || 1) - (task.finishCount || 0);
      if (remaining <= 0) continue;

      this.log(`执行通用任务: ${task.taskName} (剩余 ${remaining} 次)`);

      for (let i = 0; i < remaining; i++) {
        await this.jf_to_finish(this.aiting_biz_ticket, task.taskCode);
        await appName.wait(1500);

        await this.aiting_complete_task_api(4); // Py Type=4
        await appName.wait(2000);

        const res = await this.jf_pop_up(this.aiting_biz_ticket);
        if (res?.data?.score) {
          this.log(`  └─ 🎉 第 ${i + 1} 次: 获得 ${res.data.score} 积分`, { notify: true });
        } else {
          this.log(`  └─ 第 ${i + 1} 次: 任务完成`);
        }

        // 修正逻辑：这里原本是 aiting_do_tasks 的结尾
        await appName.wait(1500);
      }
    }
  }

  async securityButlerTask(isQueryOnly = false) {
    this.log("============= 联通安全管家 =============");
    if (!this.ecs_token) {
      this.log("安全管家: 缺少 ecs_token，跳过");
      return;
    }

    try {
      await this.getTicketByNative_sec();
      if (!this.sec_ticket1) return;

      await this.getAuthToken_sec();
      if (!this.sec_token) return;

      await this.getTicketForJF_sec();
      if (!this.sec_ticket) return;

      // 1. 查询积分
      await this.getUserInfo_sec();

      if (isQueryOnly) {
        this.log("安全管家: [查询模式] 跳过任务执行...");
        this.log("============= 安全管家执行完毕 =============");
        return;
      }

      // 2. 执行所有任务
      await this.executeAllTasks_sec();

      // 3. 再次查询积分 (显示增长)
      await this.getUserInfo_sec();

    } catch (e) {
      this.log(`安全管家: 异常: ${e.message}`);
    }
    this.log("============= 安全管家执行完毕 =============");
  }

  async userTestTask() {
    this.log("============= 正在执行爱听调试 (Final) =============");

    // 1. 登录
    const loginSuccess = await this.aiting_login_flow();
    if (!loginSuccess) return;

    // 2. 获取业务 Ticket
    this.aiting_biz_ticket = await this.aiting_get_ticket();
    if (!this.aiting_biz_ticket) return;

    // 3. 签到
    await this.aiting_sign_in();

    // 4. 执行所有任务 (新增)
    await this.aiting_do_tasks();

    // 5. 最后查一次分
    await this.jf_get_user_info(this.aiting_biz_ticket);

    this.log("✅ 调试结束！");
    appName.log("\n------------------ 账号[" + this.index + "] ------------------");
  }
}
!(async () => {
  // 动态加载 got (兼容新版ESM和旧版CommonJS)
  // 性能影响：微秒级，仅在启动时加载一次，运行期间无损耗，请放心
  try {
    got = (await import("got")).default;
  } catch (e) {
    // console.log("ESM加载失败，尝试降级加载...");
    got = require("got");
  }

  // 读取环境变量
  appName.read_env(CustomUserService);

  appName.log("\n------------------------------------");
  appName.log("首页签到设置为: " + (signDisabled ? "不" : "") + "运行");
  appName.log("联通祝福设置为: " + (ltzfDisabled ? "不" : "") + "运行");
  appName.log("------------------------------------\n");

  if (appName.userList.length === 0) {
    appName.log("❌ 未找到有效账号配置，请检查变量 chinaUnicomCookie");
    return;
  }


  // ==========================================
  // 核心逻辑: 串行 or 抢兑
  // ==========================================
  if (IS_GRAB_MODE) {
    appName.log(`\n🚨🚨🚨 [抢兑模式已启动] 🚨🚨🚨`);
    appName.log(`目标: 抢 [${GRAB_AMOUNT}元] 话费券`);
    appName.log(`注意: 将强制执行 [提取IP -> 登录 -> 抢兑] 流程`);
    appName.log(`------------------------------------`);
  } else {
    appName.log(`🚀 开始串行执行日常任务...`);
  }

  if (IS_GRAB_MODE) {
    // ==========================================
    // 抢兑模式: 并发执行 (Concurrent)
    // ==========================================
    appName.log(`🚀 [并发模式] 启动 ${appName.userList.length} 个账号同时抢兑...`);

    // 使用 map 映射为 Promise 数组，同时启动
    const grabTasks = appName.userList.map(async (user) => {
      appName.log(`\n⚔️ 账号[${user.index}] 启动并发抢兑任务...`);
      // 1. 登录 (内部强制提取独立IP)
      await user.userLoginTask();
      // 2. 抢兑
      if (user.valid) {
        await user.sign_grabCoupon();
      } else {
        appName.log(`⚠️ 账号[${user.index}] 登录失败，退出抢兑`);
      }
    });

    // 等待所有抢兑任务完成
    await Promise.all(grabTasks);

  } else {
    // ==========================================
    // 普通模式: 串行执行 (Serial)
    // ==========================================
    for (let user of appName.userList) {
      appName.log(`\n🔄 正在初始化账号[${user.index}]...`);
      await user.userLoginTask();

      if (user.valid) {
        await user.userTask();
        // await user.userTestTask();     // 调试
      } else {
        appName.log(`⚠️ 账号[${user.index}] 登录失败或IP失效，跳过任务`);
      }

      // 账号间休息，避免并发过高或日志错乱
      await appName.wait(2000);
    }
  }

  appName.log(`\n🏁 所有账号任务执行完毕`);

})().catch(error => appName.log(error)).finally(() => appName.exitNow());


function createLogger(UserClass) {
  return new class {
    constructor(name) {
      this.name = name;
      this.startTime = Date.now();
      this.log("[" + this.name + "]开始运行\n", { time: true });
      this.notifyStr = [];
      this.notifyFlag = true;
      this.userIdx = 0;
      this.userList = [];
      this.userCount = 0;
      this.default_timestamp_len = 13;
      this.default_wait_interval = 1000;
      this.default_wait_limit = 3600000;
      this.default_wait_ahead = 0;
    }
    log(message, options = {}) {
      const defaultOptions = { console: true, ...options };
      if (defaultOptions.time) {
        let format = defaultOptions.fmt || "hh:mm:ss";
        message = "[" + this.time(format) + "]" + message;
      }
      if (defaultOptions.notify) {
        this.notifyStr.push(message);
      }
      if (defaultOptions.console) {
        console.log(message);
      }
    }
    get(object, key, defaultValue = "") {
      return object?.hasOwnProperty(key) ? object[key] : defaultValue;
    }
    pop(object, key, defaultValue = "") {
      if (object?.hasOwnProperty(key)) {
        const value = object[key];
        delete object[key];
        return value;
      }
      return defaultValue;
    }
    copy(source) {
      return { ...source };
    }
    read_env(UserClass) {
      const envValues = cookieVars.map(varName => process.env[varName]);
      for (const envValue of envValues.filter(value => !!value)) {
        const delimitersFound = delimiters.filter(delimiter => envValue.includes(delimiter));
        const delimiter = delimitersFound.length > 0 ? delimitersFound[0] : delimiters[0];
        for (const userInfo of envValue.split(delimiter).filter(value => !!value)) {
          this.userList.push(new UserClass(userInfo));
        }
      }
      this.userCount = this.userList.length;
      if (!this.userCount) {
        this.log("未找到变量，请检查变量" + cookieVars.map(varName => "[" + varName + "]").join("或"), { notify: true });
        return false;
      }
      this.log("共找到" + this.userCount + "个账号");
      return true;
    }
    async threads(methodName, context, options = {}) {
      while (context.idx < appName.userList.length) {
        const user = appName.userList[context.idx++];
        if (user.valid) {
          await user[methodName](options);
        }
      }
    }
    async threadTask(methodName, count) {
      const tasks = [];
      const context = { idx: 0 };
      while (count--) {
        tasks.push(this.threads(methodName, context));
      }
      await Promise.all(tasks);
    }
    time(format, date = null) {
      const currentDate = date ? new Date(date) : new Date();
      const timeElements = {
        "M+": currentDate.getMonth() + 1,
        "d+": currentDate.getDate(),
        "h+": currentDate.getHours(),
        "m+": currentDate.getMinutes(),
        "s+": currentDate.getSeconds(),
        "q+": Math.floor((currentDate.getMonth() + 3) / 3),
        S: this.padStr(currentDate.getMilliseconds(), 3)
      };
      if (/(y+)/.test(format)) {
        format = format.replace(RegExp.$1, (currentDate.getFullYear() + "").substr(4 - RegExp.$1.length));
      }
      for (const key in timeElements) {
        if (new RegExp("(" + key + ")").test(format)) {
          format = format.replace(RegExp.$1, RegExp.$1.length === 1 ? timeElements[key] : ("00" + timeElements[key]).substr(("" + timeElements[key]).length));
        }
      }
      return format;
    }
    async showmsg() {
      let notifyBody = "";
      // 遍历所有用户，聚合他们的通知日志
      for (const user of this.userList) {
        if (user.notifyLogs.length > 0) {
          const userHeader = `------------------ 账号[${user.index}][${maskStr(user.name)}] ------------------`;
          // 移除每条日志中的手机号前缀，因为标题中已经包含了
          const userLogs = user.notifyLogs.map(log => log.replace(`[${user.name}]`, '')).join("\n");
          notifyBody += `${userHeader}\n${userLogs}\n`;
        }
      }

      if (this.notifyFlag && notifyBody) {
        try {
          const notify = require("./sendNotify");
          this.log("\n============== 推送 ==============");
          await notify.sendNotify(this.name, notifyBody);
        } catch (e) {
          this.log(`\n❌ 推送通知失败: ${e.message}`);
        }
      }
    }

    padStr(value, length, options = {}) {
      const padding = options.padding || "0";
      const mode = options.mode || "l";
      let strValue = String(value);
      const paddingLength = length > strValue.length ? length - strValue.length : 0;
      const paddingStr = padding.repeat(paddingLength);
      return mode === "r" ? strValue + paddingStr : paddingStr + strValue;
    }
    json2str(json, delimiter, encode = false) {
      return Object.keys(json)
        .sort()
        .map(key => {
          let value = json[key];
          return `${key}=${encode && value ? encodeURIComponent(value) : value}`;
        })
        .join(delimiter);
    }
    str2json(str, decode = false) {
      const json = {};
      str.split("&").forEach(pair => {
        if (pair) {
          const [key, value] = pair.split("=");
          json[key] = decode ? decodeURIComponent(value) : value;
        }
      });
      return json;
    }
    randomPattern(pattern, charset = "abcdef0123456789") {
      return pattern.split("").map(char => {
        if (char === "x") {
          return charset.charAt(Math.floor(Math.random() * charset.length));
        } else if (char === "X") {
          return charset.charAt(Math.floor(Math.random() * charset.length)).toUpperCase();
        }
        return char;
      }).join("");
    }
    randomUuid() {
      return appName.randomPattern("xxxxxxxx-xxxx-4xxx-4xxx-xxxxxxxxxxxx");
    }
    randomString(length, charset = "abcdef0123456789") {
      return Array.from({ length }, () => charset.charAt(Math.floor(Math.random() * charset.length))).join("");
    }
    randomList(list) {
      return list[Math.floor(Math.random() * list.length)];
    }
    wait(ms) {
      return new Promise(resolve => setTimeout(resolve, ms));
    }
    async exitNow() {
      await this.showmsg();
      const endTime = Date.now();
      const duration = (endTime - this.startTime) / 1000;
      this.log("");
      this.log("[" + this.name + "]运行结束，共运行了" + duration + "秒", { time: true });
      process.exit(0);
    }
    normalize_time(time, options = {}) {
      const length = options.len || this.default_timestamp_len;
      time = time.toString();
      while (time.length < length) {
        time += "0";
      }
      return parseInt(time.slice(0, 13));
    }

    async wait_gap_interval(lastWaitTime, interval) {
      const elapsedTime = Date.now() - lastWaitTime;
      if (elapsedTime < interval) {
        await this.wait(interval - elapsedTime);
      }
    }
  }(UserClass);
}