//Sat May 31 2025 09:31:06 GMT+0000 (Coordinated Universal Time)
const $ = new Env("福田e家");
const crypto = require("crypto");
const notify = $.isNode() ? require("./sendNotify") : "";

// 添加缓存相关变量
let accountCache = {};
let cacheFile = "ftej_cache.json";

// 备用发帖文本数组
const backupTexts = [
  "如果觉得没有朋友，就去找喜欢的人表白，对方会提出和你做朋友的。",
  "生活就像一杯茶，不会苦一辈子，但总会苦一阵子。",
  "每一个不曾起舞的日子，都是对生命的辜负。",
  "世界上最远的距离，不是生与死，而是我站在你面前，你却不知道我爱你。",
  "人生如梦，一尊还酹江月。",
  "山重水复疑无路，柳暗花明又一村。",
  "海内存知己，天涯若比邻。",
  "落红不是无情物，化作春泥更护花。",
  "问君能有几多愁，恰似一江春水向东流。",
  "但愿人长久，千里共婵娟。"
];

// 获取随机备用文本
function getRandomBackupText() {
  const randomIndex = Math.floor(Math.random() * backupTexts.length);
  return backupTexts[randomIndex];
}

// 添加缓存管理函数
function loadAccountCache() {
  try {
    if ($.isNode()) {
      const fs = require('fs');
      if (fs.existsSync(cacheFile)) {
        const data = fs.readFileSync(cacheFile, 'utf8');
        accountCache = JSON.parse(data);
        console.log("✅ 账号缓存加载成功");
        return accountCache;
      }
    } else {
      // 非Node.js环境使用$.getdata
      const cacheData = $.getdata('ftej_account_cache');
      if (cacheData) {
        accountCache = JSON.parse(cacheData);
        console.log("✅ 账号缓存加载成功");
        return accountCache;
      }
    }
    console.log("ℹ️ 未找到账号缓存文件");
    return {};
  } catch (e) {
    console.log(`❌ 读取账号缓存失败: ${e}`);
    return {};
  }
}

function saveAccountCache(cache) {
  try {
    if ($.isNode()) {
      const fs = require('fs');
      fs.writeFileSync(cacheFile, JSON.stringify(cache, null, 2), 'utf8');
    } else {
      // 非Node.js环境使用$.setdata
      $.setdata(JSON.stringify(cache), 'ftej_account_cache');
    }
    console.log("✅ 账号信息已缓存");
    return true;
  } catch (e) {
    console.log(`❌ 保存账号缓存失败: ${e}`);
    return false;
  }
}

function getCurrentTime() {
  const now = new Date();
  return now.getFullYear() + '-' + 
         String(now.getMonth() + 1).padStart(2, '0') + '-' + 
         String(now.getDate()).padStart(2, '0') + ' ' + 
         String(now.getHours()).padStart(2, '0') + ':' + 
         String(now.getMinutes()).padStart(2, '0') + ':' + 
         String(now.getSeconds()).padStart(2, '0');
}

// 随机打乱数组函数
function shuffleArray(array) {
  const newArray = [...array];
  for (let i = newArray.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [newArray[i], newArray[j]] = [newArray[j], newArray[i]];
  }
  return newArray;
}

// 获取随机延迟时间（3-8秒）
function getRandomDelay() {
  return Math.floor(Math.random() * 6 + 3) * 1000; // 3000-8000毫秒
}

(() => {
  function q(ad) {
    q = "function" == typeof Symbol && "symbol" == typeof Symbol.iterator ? function (af) {
      return typeof af;
    } : function (af) {
      return af && "function" == typeof Symbol && af.constructor === Symbol && af !== Symbol.prototype ? "symbol" : typeof af;
    };
    return q(ad);
  }
  function z(ad, ae) {
    var ag = "undefined" != typeof Symbol && ad[Symbol.iterator] || ad["@@iterator"];
    if (!ag) {
      if (Array.isArray(ad) || (ag = function (am, an) {
        if (am) {
          if ("string" == typeof am) {
            return B(am, an);
          }
          var ap = {}.toString.call(am).slice(8, -1);
          "Object" === ap && am.constructor && (ap = am.constructor.name);
          return "Map" === ap || "Set" === ap ? Array.from(am) : "Arguments" === ap || /^(?:Ui|I)nt(?:8|16|32)(?:Clamped)?Array$/.test(ap) ? B(am, an) : void 0;
        }
      }(ad)) || ae && ad && "number" == typeof ad.length) {
        ag && (ad = ag);
        var ah = 0,
          ai = function () {};
        return {
          s: ai,
          n: function () {
            var am = {
              done: !0
            };
            return ah >= ad.length ? am : {
              done: !1,
              value: ad[ah++]
            };
          },
          e: function (am) {
            throw am;
          },
          f: ai
        };
      }
      throw new TypeError("Invalid attempt to iterate non-iterable instance.\nIn order to be iterable, non-array objects must have a [Symbol.iterator]() method.");
    }
    var aj,
      ak = !0,
      al = !1;
    return {
      s: function () {
        ag = ag.call(ad);
      },
      n: function () {
        var ao = ag.next();
        ak = ao.done;
        return ao;
      },
      e: function (ao) {
        al = !0;
        aj = ao;
      },
      f: function () {
        try {
          ak || null == ag.return || ag.return();
        } finally {
          if (al) {
            throw aj;
          }
        }
      }
    };
  }
  function B(ad, ae) {
    (null == ae || ae > ad.length) && (ae = ad.length);
    for (var ag = 0, ah = Array(ae); ag < ae; ag++) {
      ah[ag] = ad[ag];
    }
    return ah;
  }
  function D() {
    'use strict';

    D = function () {
      return af;
    };
    var ae,
      af = {},
      ag = Object.prototype,
      ah = ag.hasOwnProperty,
      ai = Object.defineProperty || function (aK, aL, aM) {
        aK[aL] = aM.value;
      },
      aj = "function" == typeof Symbol ? Symbol : {},
      ak = aj.iterator || "@@iterator",
      al = aj.asyncIterator || "@@asyncIterator",
      am = aj.toStringTag || "@@toStringTag";
    function an(aK, aL, aM) {
      var aO = {
        value: aM,
        enumerable: !0,
        configurable: !0,
        writable: !0
      };
      Object.defineProperty(aK, aL, aO);
      return aK[aL];
    }
    try {
      an({}, "");
    } catch (aL) {
      an = function (aM, aN, aO) {
        return aM[aN] = aO;
      };
    }
    function ao(aN, aO, aP, aQ) {
      var aR = aO && aO.prototype instanceof av ? aO : av,
        aS = Object.create(aR.prototype),
        aT = new aI(aQ || []);
      ai(aS, "_invoke", {
        value: aE(aN, aP, aT)
      });
      return aS;
    }
    function ap(aN, aO, aP) {
      try {
        return {
          type: "normal",
          arg: aN.call(aO, aP)
        };
      } catch (aU) {
        var aR = {};
        aR.type = "throw";
        aR.arg = aU;
        return aR;
      }
    }
    af.wrap = ao;
    var aq = "suspendedStart",
      ar = "suspendedYield",
      as = "executing",
      at = "completed",
      au = {};
    function av() {}
    function aw() {}
    function ax() {}
    var ay = {};
    an(ay, ak, function () {
      return this;
    });
    var az = Object.getPrototypeOf,
      aA = az && az(az(aJ([])));
    aA && aA !== ag && ah.call(aA, ak) && (ay = aA);
    ax.prototype = av.prototype = Object.create(ay);
    var aB = ax.prototype;
    function aC(aN) {
      ["next", "throw", "return"].forEach(function (aQ) {
        an(aN, aQ, function (aS) {
          return this._invoke(aQ, aS);
        });
      });
    }
    function aD(aN, aO) {
      function aS(aT, aU, aV, aW) {
        var aY = ap(aN[aT], aN, aU);
        if ("throw" !== aY.type) {
          var aZ = aY.arg,
            b0 = aZ.value;
          return b0 && "object" == q(b0) && ah.call(b0, "__await") ? aO.resolve(b0.__await).then(function (b2) {
            aS("next", b2, aV, aW);
          }, function (b2) {
            aS("throw", b2, aV, aW);
          }) : aO.resolve(b0).then(function (b2) {
            aZ.value = b2;
            aV(aZ);
          }, function (b2) {
            return aS("throw", b2, aV, aW);
          });
        }
        aW(aY.arg);
      }
      var aQ;
      ai(this, "_invoke", {
        value: function (aT, aU) {
          function aW() {
            return new aO(function (aX, aY) {
              aS(aT, aU, aX, aY);
            });
          }
          return aQ = aQ ? aQ.then(aW, aW) : aW();
        }
      });
    }
    function aE(aN, aO, aP) {
      var aR = aq;
      return function (aS, aT) {
        if (aR === as) {
          throw Error("Generator is already running");
        }
        if (aR === at) {
          if ("throw" === aS) {
            throw aT;
          }
          var aV = {};
          aV.value = ae;
          aV.done = !0;
          return aV;
        }
        for (aP.method = aS, aP.arg = aT;;) {
          var aW = aP.delegate;
          if (aW) {
            var aX = aF(aW, aP);
            if (aX) {
              if (aX === au) {
                continue;
              }
              return aX;
            }
          }
          if ("next" === aP.method) {
            aP.sent = aP._sent = aP.arg;
          } else {
            if ("throw" === aP.method) {
              if (aR === aq) {
                throw aR = at, aP.arg;
              }
              aP.dispatchException(aP.arg);
            } else {
              "return" === aP.method && aP.abrupt("return", aP.arg);
            }
          }
          aR = as;
          var aY = ap(aN, aO, aP);
          if ("normal" === aY.type) {
            if (aR = aP.done ? at : ar, aY.arg === au) {
              continue;
            }
            var aZ = {};
            aZ.value = aY.arg;
            aZ.done = aP.done;
            return aZ;
          }
          "throw" === aY.type && (aR = at, aP.method = "throw", aP.arg = aY.arg);
        }
      };
    }
    function aF(aN, aO) {
      var aS = aO.method,
        aT = aN.iterator[aS];
      if (aT === ae) {
        aO.delegate = null;
        "throw" === aS && aN.iterator.return && (aO.method = "return", aO.arg = ae, aF(aN, aO), "throw" === aO.method) || "return" !== aS && (aO.method = "throw", aO.arg = new TypeError("The iterator does not provide a '" + aS + "' method"));
        return au;
      }
      var aU = ap(aT, aN.iterator, aO.arg);
      if ("throw" === aU.type) {
        aO.method = "throw";
        aO.arg = aU.arg;
        aO.delegate = null;
        return au;
      }
      var aV = aU.arg;
      return aV ? aV.done ? (aO[aN.resultName] = aV.value, aO.next = aN.nextLoc, "return" !== aO.method && (aO.method = "next", aO.arg = ae), aO.delegate = null, au) : aV : (aO.method = "throw", aO.arg = new TypeError("iterator result is not an object"), aO.delegate = null, au);
    }
    function aG(aN) {
      var aP = {
        tryLoc: aN[0]
      };
      var aQ = aP;
      1 in aN && (aQ.catchLoc = aN[1]);
      2 in aN && (aQ.finallyLoc = aN[2], aQ.afterLoc = aN[3]);
      this.tryEntries.push(aQ);
    }
    function aH(aN) {
      var aO = aN.completion || {};
      aO.type = "normal";
      delete aO.arg;
      aN.completion = aO;
    }
    function aI(aN) {
      var aO = {
        tryLoc: "root"
      };
      this.tryEntries = [aO];
      aN.forEach(aG, this);
      this.reset(!0);
    }
    function aJ(aN) {
      if (aN || "" === aN) {
        var aP = aN[ak];
        if (aP) {
          return aP.call(aN);
        }
        if ("function" == typeof aN.next) {
          return aN;
        }
        if (!isNaN(aN.length)) {
          var aQ = -1,
            aR = function aT() {
              for (; ++aQ < aN.length;) {
                if (ah.call(aN, aQ)) {
                  aT.value = aN[aQ];
                  aT.done = !1;
                  return aT;
                }
              }
              aT.value = ae;
              aT.done = !0;
              return aT;
            };
          return aR.next = aR;
        }
      }
      throw new TypeError(q(aN) + " is not iterable");
    }
    aw.prototype = ax;
    ai(aB, "constructor", {
      value: ax,
      configurable: !0
    });
    ai(ax, "constructor", {
      value: aw,
      configurable: !0
    });
    aw.displayName = an(ax, am, "GeneratorFunction");
    af.isGeneratorFunction = function (aN) {
      var aO = "function" == typeof aN && aN.constructor;
      return !!aO && (aO === aw || "GeneratorFunction" === (aO.displayName || aO.name));
    };
    af.mark = function (aN) {
      Object.setPrototypeOf ? Object.setPrototypeOf(aN, ax) : (aN.__proto__ = ax, an(aN, am, "GeneratorFunction"));
      aN.prototype = Object.create(aB);
      return aN;
    };
    af.awrap = function (aN) {
      var aP = {
        __await: aN
      };
      return aP;
    };
    aC(aD.prototype);
    an(aD.prototype, al, function () {
      return this;
    });
    af.AsyncIterator = aD;
    af.async = function (aN, aO, aP, aQ, aR) {
      void 0 === aR && (aR = Promise);
      var aT = new aD(ao(aN, aO, aP, aQ), aR);
      return af.isGeneratorFunction(aO) ? aT : aT.next().then(function (aV) {
        return aV.done ? aV.value : aT.next();
      });
    };
    aC(aB);
    an(aB, am, "Generator");
    an(aB, ak, function () {
      return this;
    });
    an(aB, "toString", function () {
      return "[object Generator]";
    });
    af.keys = function (aN) {
      var aP = Object(aN),
        aQ = [];
      for (var aR in aP) aQ.push(aR);
      aQ.reverse();
      return function aT() {
        for (; aQ.length;) {
          var aU = aQ.pop();
          if (aU in aP) {
            aT.value = aU;
            aT.done = !1;
            return aT;
          }
        }
        aT.done = !0;
        return aT;
      };
    };
    af.values = aJ;
    aI.prototype = {
      constructor: aI,
      reset: function (aN) {
        if (this.prev = 0, this.next = 0, this.sent = this._sent = ae, this.done = !1, this.delegate = null, this.method = "next", this.arg = ae, this.tryEntries.forEach(aH), !aN) {
          for (var aO in this) "t" === aO.charAt(0) && ah.call(this, aO) && !isNaN(+aO.slice(1)) && (this[aO] = ae);
        }
      },
      stop: function () {
        this.done = !0;
        var aP = this.tryEntries[0].completion;
        if ("throw" === aP.type) {
          throw aP.arg;
        }
        return this.rval;
      },
      dispatchException: function (aN) {
        if (this.done) {
          throw aN;
        }
        var aO = this;
        function aV(aW, aX) {
          aR.type = "throw";
          aR.arg = aN;
          aO.next = aW;
          aX && (aO.method = "next", aO.arg = ae);
          return !!aX;
        }
        for (var aP = this.tryEntries.length - 1; aP >= 0; --aP) {
          var aQ = this.tryEntries[aP],
            aR = aQ.completion;
          if ("root" === aQ.tryLoc) {
            return aV("end");
          }
          if (aQ.tryLoc <= this.prev) {
            var aS = ah.call(aQ, "catchLoc"),
              aT = ah.call(aQ, "finallyLoc");
            if (aS && aT) {
              if (this.prev < aQ.catchLoc) {
                return aV(aQ.catchLoc, !0);
              }
              if (this.prev < aQ.finallyLoc) {
                return aV(aQ.finallyLoc);
              }
            } else {
              if (aS) {
                if (this.prev < aQ.catchLoc) {
                  return aV(aQ.catchLoc, !0);
                }
              } else {
                if (!aT) {
                  throw Error("try statement without catch or finally");
                }
                if (this.prev < aQ.finallyLoc) {
                  return aV(aQ.finallyLoc);
                }
              }
            }
          }
        }
      },
      abrupt: function (aN, aO) {
        for (var aP = this.tryEntries.length - 1; aP >= 0; --aP) {
          var aQ = this.tryEntries[aP];
          if (aQ.tryLoc <= this.prev && ah.call(aQ, "finallyLoc") && this.prev < aQ.finallyLoc) {
            var aR = aQ;
            break;
          }
        }
        aR && ("break" === aN || "continue" === aN) && aR.tryLoc <= aO && aO <= aR.finallyLoc && (aR = null);
        var aS = aR ? aR.completion : {};
        aS.type = aN;
        aS.arg = aO;
        return aR ? (this.method = "next", this.next = aR.finallyLoc, au) : this.complete(aS);
      },
      complete: function (aN, aO) {
        if ("throw" === aN.type) {
          throw aN.arg;
        }
        "break" === aN.type || "continue" === aN.type ? this.next = aN.arg : "return" === aN.type ? (this.rval = this.arg = aN.arg, this.method = "return", this.next = "end") : "normal" === aN.type && aO && (this.next = aO);
        return au;
      },
      finish: function (aN) {
        for (var aP = this.tryEntries.length - 1; aP >= 0; --aP) {
          var aQ = this.tryEntries[aP];
          if (aQ.finallyLoc === aN) {
            this.complete(aQ.completion, aQ.afterLoc);
            aH(aQ);
            return au;
          }
        }
      },
      catch: function (aN) {
        for (var aO = this.tryEntries.length - 1; aO >= 0; --aO) {
          var aP = this.tryEntries[aO];
          if (aP.tryLoc === aN) {
            var aQ = aP.completion;
            if ("throw" === aQ.type) {
              var aR = aQ.arg;
              aH(aP);
            }
            return aR;
          }
        }
        throw Error("illegal catch attempt");
      },
      delegateYield: function (aN, aO, aP) {
        this.delegate = {
          iterator: aJ(aN),
          resultName: aO,
          nextLoc: aP
        };
        "next" === this.method && (this.arg = ae);
        return au;
      }
    };
    return af;
  }
  function F(ad, ae, af, ag, ah, ai, aj) {
    try {
      var ak = ad[ai](aj),
        al = ak.value;
    } catch (ao) {
      return void af(ao);
    }
    ak.done ? ae(al) : Promise.resolve(al).then(ag, ah);
  }
  function G(ad) {
    return function () {
      var ag = this,
        ah = arguments;
      return new Promise(function (ai, aj) {
        var al = ad.apply(ag, ah);
        function am(ao) {
          F(al, ai, aj, am, an, "next", ao);
        }
        function an(ao) {
          F(al, ai, aj, am, an, "throw", ao);
        }
        am(void 0);
      });
    };
  }
  var H = ($.isNode() ? process.env.Fukuda : $.getdata("Fukuda")) || "",
    J = "",
    K = "",
    M = "",
    Q = "",
    R = "",
    cachedInfo = null; // 添加全局变量声明
  function T() {
    return U.apply(this, arguments);
  }
  function U() {
    U = G(D().mark(function ae() {
      var ag, ah, ai, aj, ak, al, am, an, ao, ap, aq, ar, as, at, au, av, aw, ax, ay, az, aA, aB, aC, aD, aE, aF, aG, aH, aI;
      return D().wrap(function (aJ) {
        for (;;) {
          switch (aJ.prev = aJ.next) {
            case 0:
              if (console.log("作者：@xzxxn777\n频道：https://t.me/xzxxn777\n群组：https://t.me/xzxxn7777\n自用机场推荐：https://xn--diqv0fut7b.com\n"), H) {
                aJ.next = 6;
                break;
              }
              console.log("先去boxjs填写账号密码");
              aJ.next = 5;
              return ab("先去boxjs填写账号密码");
            case 5:
              return aJ.abrupt("return");
            case 6:
              // 加载账号缓存
              accountCache = loadAccountCache();
              ag = H.split("&");
              
              // 随机打乱账号顺序
              ag = shuffleArray(ag);
              console.log("🔀 账号将按随机顺序执行，共".concat(ag.length, "个账号"));
              
              ah = z(ag);
              aJ.prev = 8;
              ah.s();
            case 10:
              if ((ai = ah.n()).done) {
                aJ.next = 148;
                break;
              }
              var aL = {};
              aL.deviceType = 1;
              aj = ai.value;
              aJ.prev = 12;
              J = aj.split("#")[0];
              K = aj.split("#")[1];
              console.log("👤 用户：".concat(J, "开始任务"));
              
              // 检查是否有缓存的登录信息
              cachedInfo = accountCache[J]; // 使用全局变量
              var useCache = false;
              var signed = false;
              
              if (cachedInfo) {
                console.log("🔍 发现账号缓存信息，尝试使用缓存凭证");
                uid = cachedInfo.uid || "";
                memberComplexCode = cachedInfo.memberComplexCode || "";
                memberId = cachedInfo.memberId || "";
                M = cachedInfo.token || "";
              }
              
              console.log("🔍 获取皮卡生活safeKey");
              aJ.next = 19;
              return X("/ehomes-new/pkHome/version/getVersion", aL);
            case 19:
              if (am = aJ.sent, 200 != am.code) {
                aJ.next = 40;
                break;
              }
              Q = am.data.safeKey;
              
              // 如果有缓存信息，先尝试使用缓存凭证签到
              if (cachedInfo) {
                console.log("🔍 使用缓存凭证尝试签到");
                aJ.next = 25;
                return a3("/ehomes-new/pkHome/api/bonus/signActivity2nd", {
                  memberId: memberComplexCode,
                  memberID: memberId,
                  mobile: J,
                  token: "7fe186bb15ff4426ae84f300f05d9c8d",
                  vin: "",
                  safeEnc: Date.now() - Q
                });
              } else {
                console.log("🔍 皮卡生活登录");
                aJ.next = 26;
                return X("/ehomes-new/pkHome/api/user/getLoginMember2nd", {
                  memberId: "",
                  memberID: "",
                  mobile: "",
                  token: "7fe186bb15ff4426ae84f300f05d9c8d",
                  vin: "",
                  safeEnc: Date.now() - Q,
                  name: J,
                  password: K,
                  position: "",
                  deviceId: "",
                  deviceBrand: "",
                  brandName: "",
                  deviceType: "0",
                  versionCode: "21",
                  versionName: "V1.1.16"
                });
              }
            case 25:
              // 处理缓存凭证签到结果
              ao = aJ.sent;
              console.log("🔍 缓存验证响应:", JSON.stringify(ao));
              
              if (ao && (ao.code === 200 || (ao.data && (ao.data.integral || ao.data.msg)))) {
                console.log("✅ 缓存凭证有效");
                if (ao.data && ao.data.integral) {
                  console.log("✅ 签到成功，获得".concat(ao.data.integral, "积分"));
                } else if (ao.data && ao.data.msg) {
                  console.log("ℹ️ 签到结果: ".concat(ao.data.msg));
                } else {
                  console.log("ℹ️ 缓存凭证验证成功");
                }
                useCache = true;
                signed = true;
                aJ.next = 41;
                break;
              } else {
                console.log("❌ 缓存凭证无效或已过期，将进行正常登录");
                console.log("皮卡生活登录");
                aJ.next = 26;
                return X("/ehomes-new/pkHome/api/user/getLoginMember2nd", {
                  memberId: "",
                  memberID: "",
                  mobile: "",
                  token: "7fe186bb15ff4426ae84f300f05d9c8d",
                  vin: "",
                  safeEnc: Date.now() - Q,
                  name: J,
                  password: K,
                  position: "",
                  deviceId: "",
                  deviceBrand: "",
                  brandName: "",
                  deviceType: "0",
                  versionCode: "21",
                  versionName: "V1.1.16"
                });
              }
            case 26:
              if (an = aJ.sent, console.log(null == an ? void 0 : an.msg), 200 != (null == an ? void 0 : an.code)) {
                aJ.next = 38;
                break;
              }
              uid = an.data.uid;
              memberComplexCode = an.data.memberComplexCode;
              memberId = an.data.user.memberNo;
              M = an.data.token;
              
              // 保存登录信息到缓存
              accountCache[J] = {
                uid: uid,
                memberComplexCode: memberComplexCode,
                memberId: memberId,
                token: M,
                updateTime: getCurrentTime()
              };
              saveAccountCache(accountCache);
              console.log("✅ 登录成功并已更新缓存");
              
              // 如果不是使用缓存登录，则进行签到
              if (!signed) {
                console.log("🔑 开始签到");
                aJ.next = 36;
                return a3("/ehomes-new/pkHome/api/bonus/signActivity2nd", {
                  memberId: memberComplexCode,
                  memberID: memberId,
                  mobile: J,
                  token: "7fe186bb15ff4426ae84f300f05d9c8d",
                  vin: "",
                  safeEnc: Date.now() - Q
                });
              } else {
                aJ.next = 38;
                break;
              }
            case 36:
              ao = aJ.sent;
              ao.data.integral ? console.log("✅ 签到成功，获得".concat(ao.data.integral, "积分")) : console.log(ao.data.msg);
            case 38:
              aJ.next = 41;
              break;
            case 40:
              console.log(am.msg);
            case 41:
              console.log("————————————");
              console.log("🔍 获取福田e家safeKey");
              aJ.next = 45;
              return Z("/est/getVersion.action", a8(JSON.stringify({
                limit: {
                  auth: "null",
                  uid: "",
                  userType: "61"
                },
                param: {
                  deviceType: "1",
                  version: "7.5.1",
                  versionCode: "345"
                }
              })));
            case 45:
              if (am = aJ.sent, 0 == am.code) {
                aJ.next = 49;
                break;
              }
              console.log(am.msg);
              return aJ.abrupt("continue", 146);
            case 49:
              Q = JSON.parse(am.data).safeKey;
              console.log("🔑 福田e家登录");
              aJ.next = 54;
              return V("/ehomes-new/homeManager/getLoginMember", {
                password: K,
                version_name: "7.4.9",
                version_auth: "svHgvcBi/9f/MyYFLY3aFQ==",
                device_id: "",
                device_model: "",
                ip: "",
                name: J,
                version_code: "342",
                deviceSystemVersion: "12",
                device_type: "0"
              });
            case 54:
              if (ap = aJ.sent, 200 == ap.code) {
                aJ.next = 58;
                break;
              }
              console.log(ap.msg);
              return aJ.abrupt("continue", 146);
            case 58:
              console.log("✅ 福田e家登录成功");
              uid = ap.data.uid;
              memberComplexCode = ap.data.memberComplexCode;
              memberId = ap.data.memberID;
              
              // 模拟登录中
              console.log("🔄 模拟登录中");
              aJ.next = 64;
              return a1("/ehomes-new/homeManager/api/share/corsToActicity", {
                memberId: memberId,
                userId: uid,
                userType: "61",
                uid: uid,
                mobile: J,
                tel: J,
                phone: J,
                brandName: "",
                seriesName: "",
                token: "ebf76685e48d4e14a9de6fccc76483e3",
                safeEnc: Date.now() - Q,
                businessId: 1,
                activityNumber: "open",
                requestType: "0",
                type: "5",
                userNumber: memberId,
                channel: "1",
                name: "",
                remark: "打开APP"
              });
            case 64:
              if (aq = aJ.sent, 200 == aq.code ? console.log("✅ 模拟登录成功") : console.log("❌ 模拟登录失败：".concat(aq.msg)), console.log("🔑 开始签到"), "未签到" != ap.data.signIn) {
                aJ.next = 74;
                break;
              }
              aJ.next = 70;
              return a1("/ehomes-new/homeManager/api/bonus/signActivity2nd", {
                memberId: memberComplexCode,
                userId: uid,
                userType: "61",
                uid: uid,
                mobile: J,
                tel: J,
                phone: J,
                brandName: "",
                seriesName: "",
                token: "ebf76685e48d4e14a9de6fccc76483e3",
                safeEnc: Date.now() - Q,
                businessId: 1
              });
            case 70:
              as = aJ.sent;
              console.log("✅ 签到成功，获得".concat(null == as || null === (ar = as.data) || void 0 === ar ? void 0 : ar.integral, "积分"));
              aJ.next = 75;
              break;
            case 74:
              console.log(null == ap || null === (at = ap.data) || void 0 === at ? void 0 : at.signIn);
            case 75:
              console.log("————————————");
              console.log("🔍 开始任务");
              aJ.next = 79;
              return a1("/ehomes-new/homeManager/api/Member/getTaskList", {
                memberId: memberId,
                userId: uid,
                userType: "61",
                uid: uid,
                mobile: J,
                tel: J,
                phone: J,
                brandName: "",
                seriesName: "",
                token: "ebf76685e48d4e14a9de6fccc76483e3",
                safeEnc: Date.now() - Q,
                businessId: 1
              });
            case 79:
              au = aJ.sent;
              av = z(au.data);
              aJ.prev = 81;
              av.s();
            case 83:
              if ((aw = av.n()).done) {
                aJ.next = 126;
                break;
              }
              if (ax = aw.value, console.log("📌任务：".concat(ax.ruleName)), "1" != ax.isComplete) {
                aJ.next = 90;
                break;
              }
              console.log("✅ 任务已完成");
              aJ.next = 124;
              break;
            case 90:
              if ("33" != ax.ruleId) {
                aJ.next = 95;
                break;
              }
              aJ.next = 93;
              return V("/ehomes-new/homeManager/api/bonus/addIntegralForShare", {
                safeEnc: Date.now() - Q,
                activity: "",
                tel: J,
                id: ax.ruleId,
                source: "APP",
                memberId: memberComplexCode
              });
            case 93:
              ay = aJ.sent;
              200 == ay.code ? console.log("✅ 分享成功，获得".concat(ay.data.integral, "积分")) : console.log(ay.msg);
            case 95:
              if ("130" != ax.ruleId) {
                aJ.next = 109;
                break;
              }
              aJ.next = 98;
              return a1("/ehomes-new/ehomesCommunity/api/post/recommendPostList", {
                memberId: memberId,
                userId: uid,
                userType: "61",
                uid: uid,
                mobile: J,
                tel: J,
                phone: J,
                brandName: "",
                seriesName: "",
                token: "ebf76685e48d4e14a9de6fccc76483e3",
                safeEnc: Date.now() - Q,
                businessId: 1,
                position: "1",
                pageNumber: "1",
                pageSize: 9
              });
            case 98:
              az = aJ.sent;
              aA = Math.floor(Math.random() * az.data.length);
              aB = az.data[aA].memberId;
              aJ.next = 103;
              return a1("/ehomes-new/ehomesCommunity/api/post/follow2nd", {
                memberId: memberComplexCode,
                userId: uid,
                userType: "61",
                uid: uid,
                mobile: J,
                tel: J,
                phone: J,
                brandName: "",
                seriesName: "",
                token: "ebf76685e48d4e14a9de6fccc76483e3",
                safeEnc: Date.now() - Q,
                businessId: 1,
                behavior: "1",
                memberIdeds: aB,
                navyId: "null"
              });
            case 103:
              aC = aJ.sent;
              200 == aC.code ? console.log("✅ 关注成功") : console.log(aC.msg);
              aJ.next = 107;
              return a1("/ehomes-new/ehomesCommunity/api/post/follow2nd", {
                memberId: memberComplexCode,
                userId: uid,
                userType: "61",
                uid: uid,
                mobile: J,
                tel: J,
                phone: J,
                brandName: "",
                seriesName: "",
                token: "ebf76685e48d4e14a9de6fccc76483e3",
                safeEnc: Date.now() - Q,
                businessId: 1,
                behavior: "2",
                memberIdeds: aB,
                navyId: "null"
              });
            case 107:
              aC = aJ.sent;
              200 == aC.code ? console.log("✅ 取关成功") : console.log(aC.msg);
            case 109:
              if ("125" != ax.ruleId) {
                aJ.next = 124;
                break;
              }
              aJ.next = 112;
              return V("/ehomes-new/ehomesCommunity/api/post/topicList", {
                memberId: memberId,
                userId: uid,
                userType: "61",
                uid: uid,
                mobile: J,
                tel: J,
                phone: J,
                brandName: "",
                seriesName: "",
                token: "ebf76685e48d4e14a9de6fccc76483e3",
                safeEnc: Date.now() - Q,
                businessId: 1
              });
            case 112:
              aD = aJ.sent;
              aE = Math.floor(Math.random() * aD.data.top.length);
              aF = aD.data.top[aE].topicId;
              aJ.next = 117;
              return a5();
            case 117:
              aG = aJ.sent;
              // 更严格的文本验证和处理
              if (!aG || typeof aG !== 'string' || aG.length < 10 || 
                  aG.includes("文件内容解析失败") || 
                  aG.includes("错误") || 
                  aG.includes("失败") ||
                  aG.trim() === "") {
                console.log("⚠️ 获取的文本内容无效，使用随机备用文本");
                aG = getRandomBackupText();
              } else {
                // 清理文本，移除可能的HTML标签和多余空白
                aG = aG.replace(/<[^>]*>/g, '').trim();
                if (aG.length < 10) {
                  console.log("⚠️ 清理后文本过短，使用随机备用文本");
                  aG = getRandomBackupText();
                }
              }
              console.log("✍️ 发帖内容：".concat(aG));
              aJ.next = 122;
              return a1("/ehomes-new/ehomesCommunity/api/post/addJson2nd", {
                memberId: memberComplexCode,
                userId: uid,
                userType: "61",
                uid: uid,
                mobile: J,
                tel: J,
                phone: J,
                brandName: "",
                seriesName: "",
                token: "ebf76685e48d4e14a9de6fccc76483e3",
                safeEnc: Date.now() - Q,
                businessId: 1,
                content: aG,
                postType: 1,
                topicIdList: [aF],
                uploadFlag: 3,
                title: "",
                urlList: []
              });
            case 122:
              aH = aJ.sent;
              200 == aH.code ? console.log("✅ 发帖成功") : console.log(aH.msg);
            case 124:
              aJ.next = 83;
              break;
            case 126:
              aJ.next = 131;
              break;
            case 128:
              aJ.prev = 128;
              aJ.t0 = aJ.catch(81);
              av.e(aJ.t0);
            case 131:
              aJ.prev = 131;
              av.f();
              return aJ.finish(131);
            case 134:
              console.log("————————————");
              aJ.next = 138;
              return a1("/ehomes-new/homeManager/api/Member/findMemberPointsInfo", {
                memberId: memberId,
                userId: uid,
                userType: "61",
                uid: uid,
                mobile: J,
                tel: J,
                phone: J,
                brandName: "",
                seriesName: "",
                token: "ebf76685e48d4e14a9de6fccc76483e3",
                safeEnc: Date.now() - Q,
                businessId: 1
              });
            case 138:
              aI = aJ.sent;
              console.log("🔍 查询当前账号拥有积分: ".concat(null == aI || null === (ak = aI.data) || void 0 === ak ? void 0 : ak.pointValue, "\n---------------------------"));
              R += "👤 用户：".concat(J, " 拥有积分: ").concat(null == aI || null === (al = aI.data) || void 0 === al ? void 0 : al.pointValue, "\n");
              
              // 检查是否还有下一个账号，如果有则添加随机延迟
              var currentIndex = ag.findIndex(function(account) { return account.split("#")[0] === J; });
              if (currentIndex < ag.length - 1) {
                var delayTime = getRandomDelay();
                console.log("⏳ 等待".concat(Math.floor(delayTime / 1000), "秒后处理下一个账号..."));
                aJ.next = 142;
                return new Promise(function(resolve) { setTimeout(resolve, delayTime); });
              } else {
                console.log("🎉 所有账号处理完成！");
                aJ.next = 146;
                break;
              }
            case 142:
              aJ.next = 146;
              break;
            case 143:
              aJ.prev = 143;
              aJ.t1 = aJ.catch(12);
              console.log(aJ.t1);
            case 146:
              aJ.next = 10;
              break;
            case 148:
              aJ.next = 153;
              break;
            case 150:
              aJ.prev = 150;
              aJ.t2 = aJ.catch(8);
              ah.e(aJ.t2);
            case 153:
              aJ.prev = 153;
              ah.f();
              return aJ.finish(153);
            case 156:
              if (!R) {
                aJ.next = 159;
                break;
              }
              aJ.next = 159;
              return ab(R);
            case 159:
            case "end":
              return aJ.stop();
          }
        }
      }, ae, null, [[8, 150, 153, 156], [12, 143], [81, 128, 131, 134]]);
    }));
    return U.apply(this, arguments);
  }
  function V(ad, ae) {
    return W.apply(this, arguments);
  }
  function W() {
    W = G(D().mark(function ae(af, ag) {
      return D().wrap(function (aj) {
        for (;;) {
          switch (aj.prev = aj.next) {
            case 0:
              return aj.abrupt("return", new Promise(function (al) {
                var am = {
                  url: "https://czyl.foton.com.cn".concat(af),
                  headers: {
                    "content-type": "application/json;charset=utf-8",
                    Connection: "Keep-Alive",
                    "user-agent": "okhttp/3.14.9",
                    "Accept-Encoding": "gzip"
                  },
                  body: JSON.stringify(ag)
                };
                $.post(am, function () {
                  var ao = G(D().mark(function ap(aq, ar, as) {
                    return D().wrap(function (at) {
                      for (;;) {
                        switch (at.prev = at.next) {
                          case 0:
                            if (at.prev = 0, !aq) {
                              at.next = 6;
                              break;
                            }
                            console.log("".concat(JSON.stringify(aq)));
                            console.log("".concat($.name, " API请求失败，请检查网路重试"));
                            at.next = 9;
                            break;
                          case 6:
                            at.next = 8;
                            return $.wait(2000);
                          case 8:
                            al(JSON.parse(as));
                          case 9:
                            at.next = 14;
                            break;
                          case 11:
                            at.prev = 11;
                            at.t0 = at.catch(0);
                            $.logErr(at.t0, ar);
                          case 14:
                            at.prev = 14;
                            al();
                            return at.finish(14);
                          case 17:
                          case "end":
                            return at.stop();
                        }
                      }
                    }, ap, null, [[0, 11, 14, 17]]);
                  }));
                  return function (aq, ar, as) {
                    return ao.apply(this, arguments);
                  };
                }());
              }));
            case 1:
            case "end":
              return aj.stop();
          }
        }
      }, ae);
    }));
    return W.apply(this, arguments);
  }
  function X(ad, ae) {
    return Y.apply(this, arguments);
  }
  function Y() {
    Y = G(D().mark(function ae(af, ag) {
      return D().wrap(function (ai) {
        for (;;) {
          switch (ai.prev = ai.next) {
            case 0:
              return ai.abrupt("return", new Promise(function (aj) {
                var al = {
                  url: "https://czyl.foton.com.cn".concat(af),
                  headers: {
                    "content-type": "application/json;charset=utf-8",
                    channel: "1",
                    "Accept-Encoding": "gzip"
                  },
                  body: JSON.stringify(ag)
                };
                $.post(al, function () {
                  var an = G(D().mark(function ao(ap, aq, ar) {
                    return D().wrap(function (at) {
                      for (;;) {
                        switch (at.prev = at.next) {
                          case 0:
                            if (at.prev = 0, !ap) {
                              at.next = 6;
                              break;
                            }
                            console.log("".concat(JSON.stringify(ap)));
                            console.log("".concat($.name, " API请求失败，请检查网路重试"));
                            at.next = 9;
                            break;
                          case 6:
                            at.next = 8;
                            return $.wait(2000);
                          case 8:
                            aj(JSON.parse(ar));
                          case 9:
                            at.next = 14;
                            break;
                          case 11:
                            at.prev = 11;
                            at.t0 = at.catch(0);
                            $.logErr(at.t0, aq);
                          case 14:
                            at.prev = 14;
                            aj();
                            return at.finish(14);
                          case 17:
                          case "end":
                            return at.stop();
                        }
                      }
                    }, ao, null, [[0, 11, 14, 17]]);
                  }));
                  return function (ap, aq, ar) {
                    return an.apply(this, arguments);
                  };
                }());
              }));
            case 1:
            case "end":
              return ai.stop();
          }
        }
      }, ae);
    }));
    return Y.apply(this, arguments);
  }
  function Z(ad, ae) {
    return a0.apply(this, arguments);
  }
  function a0() {
    a0 = G(D().mark(function ae(af, ag) {
      return D().wrap(function (ai) {
        for (;;) {
          switch (ai.prev = ai.next) {
            case 0:
              return ai.abrupt("return", new Promise(function (ak) {
                var am = {
                  url: "https://czyl.foton.com.cn".concat(af),
                  headers: {
                    encrypt: "yes",
                    "Content-Type": "application/x-www-form-urlencoded",
                    Connection: "Keep-Alive",
                    "User-Agent": "okhttp/3.14.9",
                    "Accept-Encoding": "gzip"
                  },
                  body: "jsonParame=".concat(encodeURIComponent(ag))
                };
                $.post(am, function () {
                  var ao = G(D().mark(function ap(aq, ar, as) {
                    return D().wrap(function (at) {
                      for (;;) {
                        switch (at.prev = at.next) {
                          case 0:
                            if (at.prev = 0, !aq) {
                              at.next = 6;
                              break;
                            }
                            console.log("".concat(JSON.stringify(aq)));
                            console.log("".concat($.name, " API请求失败，请检查网路重试"));
                            at.next = 9;
                            break;
                          case 6:
                            at.next = 8;
                            return $.wait(2000);
                          case 8:
                            ak(JSON.parse(a7(as)));
                          case 9:
                            at.next = 14;
                            break;
                          case 11:
                            at.prev = 11;
                            at.t0 = at.catch(0);
                            $.logErr(at.t0, ar);
                          case 14:
                            at.prev = 14;
                            ak();
                            return at.finish(14);
                          case 17:
                          case "end":
                            return at.stop();
                        }
                      }
                    }, ap, null, [[0, 11, 14, 17]]);
                  }));
                  return function (aq, ar, as) {
                    return ao.apply(this, arguments);
                  };
                }());
              }));
            case 1:
            case "end":
              return ai.stop();
          }
        }
      }, ae);
    }));
    return a0.apply(this, arguments);
  }
  function a1(ad, ae) {
    return a2.apply(this, arguments);
  }
  function a2() {
    a2 = G(D().mark(function ae(af, ag) {
      return D().wrap(function (aj) {
        for (;;) {
          switch (aj.prev = aj.next) {
            case 0:
              return aj.abrupt("return", new Promise(function (al) {
                var am = {
                  url: "https://czyl.foton.com.cn".concat(af),
                  headers: {
                    "content-type": "application/json;charset=utf-8",
                    Connection: "Keep-Alive",
                    token: "",
                    "app-key": "7918d2d1a92a02cbc577adb8d570601e72d3b640",
                    "app-token": "58891364f56afa1b6b7dae3e4bbbdfbfde9ef489",
                    "user-agent": "web",
                    "Accept-Encoding": "gzip"
                  },
                  body: JSON.stringify(ag)
                };
                $.post(am, function () {
                  var ao = G(D().mark(function ap(aq, ar, as) {
                    return D().wrap(function (at) {
                      for (;;) {
                        switch (at.prev = at.next) {
                          case 0:
                            if (at.prev = 0, !aq) {
                              at.next = 6;
                              break;
                            }
                            console.log("".concat(JSON.stringify(aq)));
                            console.log("".concat($.name, " API请求失败，请检查网路重试"));
                            at.next = 9;
                            break;
                          case 6:
                            at.next = 8;
                            return $.wait(2000);
                          case 8:
                            al(JSON.parse(as));
                          case 9:
                            at.next = 14;
                            break;
                          case 11:
                            at.prev = 11;
                            at.t0 = at.catch(0);
                            $.logErr(at.t0, ar);
                          case 14:
                            at.prev = 14;
                            al();
                            return at.finish(14);
                          case 17:
                          case "end":
                            return at.stop();
                        }
                      }
                    }, ap, null, [[0, 11, 14, 17]]);
                  }));
                  return function (aq, ar, as) {
                    return ao.apply(this, arguments);
                  };
                }());
              }));
            case 1:
            case "end":
              return aj.stop();
          }
        }
      }, ae);
    }));
    return a2.apply(this, arguments);
  }
  function a3(ad, ae) {
    return a4.apply(this, arguments);
  }
  function a4() {
    a4 = G(D().mark(function ae(af, ag) {
      return D().wrap(function (ai) {
        for (;;) {
          switch (ai.prev = ai.next) {
            case 0:
              return ai.abrupt("return", new Promise(function (ak) {
                var am = {
                  url: "https://czyl.foton.com.cn".concat(af),
                  headers: {
                    "content-type": "application/json;charset=utf-8",
                    channel: "1",
                    token: M,
                    "Accept-Encoding": "gzip"
                  },
                  body: JSON.stringify(ag)
                };
                $.post(am, function () {
                  var an = G(D().mark(function ao(ap, aq, ar) {
                    return D().wrap(function (at) {
                      for (;;) {
                        switch (at.prev = at.next) {
                          case 0:
                            if (at.prev = 0, !ap) {
                              at.next = 6;
                              break;
                            }
                            console.log("".concat(JSON.stringify(ap)));
                            console.log("".concat($.name, " API请求失败，请检查网路重试"));
                            at.next = 9;
                            break;
                          case 6:
                            at.next = 8;
                            return $.wait(2000);
                          case 8:
                            ak(JSON.parse(ar));
                          case 9:
                            at.next = 14;
                            break;
                          case 11:
                            at.prev = 11;
                            at.t0 = at.catch(0);
                            $.logErr(at.t0, aq);
                          case 14:
                            at.prev = 14;
                            ak();
                            return at.finish(14);
                          case 17:
                          case "end":
                            return at.stop();
                        }
                      }
                    }, ao, null, [[0, 11, 14, 17]]);
                  }));
                  return function (ap, aq, ar) {
                    return an.apply(this, arguments);
                  };
                }());
              }));
            case 1:
            case "end":
              return ai.stop();
          }
        }
      }, ae);
    }));
    return a4.apply(this, arguments);
  }
  function a5() {
    return a6.apply(this, arguments);
  }
  function a6() {
    a6 = G(D().mark(function ad() {
      return D().wrap(function (af) {
        for (;;) {
          switch (af.prev = af.next) {
            case 0:
              return af.abrupt("return", new Promise(function (ah) {
                var ai = {
                  url: "https://api.btstu.cn/yan/api.php",
                  headers: {}
                };
                $.get(ai, function () {
                  var ak = G(D().mark(function al(am, an, ao) {
                    return D().wrap(function (ap) {
                      for (;;) {
                        switch (ap.prev = ap.next) {
                          case 0:
                            if (ap.prev = 0, !am) {
                              ap.next = 6;
                              break;
                            }
                            console.log("".concat(JSON.stringify(am)));
                            console.log("".concat($.name, " API请求失败，请检查网路重试"));
                            // 如果API请求失败，返回随机备用文本
                            ah(getRandomBackupText());
                            ap.next = 9;
                            break;
                          case 6:
                            ap.next = 8;
                            return $.wait(2000);
                          case 8:
                            // 检查返回的内容是否有效
                            if (ao && ao.length > 10 && !ao.includes("文件内容解析失败") && !ao.includes("错误")) {
                              ah(ao);
                            } else {
                              console.log("⚠️ API返回内容无效，使用随机备用文本");
                              ah(getRandomBackupText());
                            }
                          case 9:
                            ap.next = 14;
                            break;
                          case 11:
                            ap.prev = 11;
                            ap.t0 = ap.catch(0);
                            $.logErr(ap.t0, an);
                          case 14:
                            ap.prev = 14;
                            // 确保总是有返回值
                            ah(getRandomBackupText());
                            return ap.finish(14);
                          case 17:
                          case "end":
                            return ap.stop();
                        }
                      }
                    }, al, null, [[0, 11, 14, 17]]);
                  }));
                  return function (am, an, ao) {
                    return ak.apply(this, arguments);
                  };
                }());
              }));
            case 1:
            case "end":
              return af.stop();
          }
        }
      }, ad);
    }));
    return a6.apply(this, arguments);
  }
  function a7(ad) {
    var ae = Buffer.from("Zm9udG9uZS10cmFuc0BseDEwMCQjMzY1", "base64"),
      af = Buffer.from("MjAxNjEyMDE=", "base64"),
      ag = crypto.createDecipheriv("des-ede3-cbc", ae, af);
    ag.setAutoPadding(!0);
    var ah = Buffer.from(ad, "base64"),
      ai = ag.update(ah, void 0, "utf8");
    ai += ag.final("utf8");
    return ai;
  }
  function a8(ad) {
    var ae = Buffer.from("Zm9udG9uZS10cmFuc0BseDEwMCQjMzY1", "base64"),
      af = Buffer.from("MjAxNjEyMDE=", "base64"),
      ag = crypto.createCipheriv("des-ede3-cbc", ae, af);
    ag.setAutoPadding(!0);
    var ah = ag.update(ad, "utf8", "base64");
    ah += ag.final("base64");
    return ah;
  }
  function a9() {
    return aa.apply(this, arguments);
  }
  function aa() {
    aa = G(D().mark(function ae() {
      return D().wrap(function (ah) {
        for (;;) {
          switch (ah.prev = ah.next) {
            case 0:
              return ah.abrupt("return", new Promise(function (aj) {
                var ak = {
                  url: "https://fastly.jsdelivr.net/gh/xzxxn777/Surge@main/Utils/Notice.json"
                };
                $.get(ak, function () {
                  var am = G(D().mark(function an(ao, ap, aq) {
                    return D().wrap(function (as) {
                      for (;;) {
                        switch (as.prev = as.next) {
                          case 0:
                            try {
                              ao ? (console.log("".concat(JSON.stringify(ao))), console.log("".concat($.name, " API请求失败，请检查网路重试"))) : console.log(JSON.parse(aq).notice);
                            } catch (at) {
                              $.logErr(at, ap);
                            } finally {
                              aj();
                            }
                          case 1:
                          case "end":
                            return as.stop();
                        }
                      }
                    }, an);
                  }));
                  return function (ao, ap, aq) {
                    return am.apply(this, arguments);
                  };
                }());
              }));
            case 1:
            case "end":
              return ah.stop();
          }
        }
      }, ae);
    }));
    return aa.apply(this, arguments);
  }
  function ab(ad) {
    return ac.apply(this, arguments);
  }
  function ac() {
    ac = G(D().mark(function ad(ae) {
      return D().wrap(function (ah) {
        for (;;) {
          switch (ah.prev = ah.next) {
            case 0:
              if (!$.isNode()) {
                ah.next = 5;
                break;
              }
              ah.next = 3;
              return notify.sendNotify($.name, ae);
            case 3:
              ah.next = 6;
              break;
            case 5:
              $.msg($.name, "", ae);
            case 6:
            case "end":
              return ah.stop();
          }
        }
      }, ad);
    }));
    return ac.apply(this, arguments);
  }
  G(D().mark(function ad() {
    return D().wrap(function (ae) {
      for (;;) {
        switch (ae.prev = ae.next) {
          case 0:
            ae.next = 2;
            return a9();
          case 2:
            ae.next = 4;
            return T();
          case 4:
          case "end":
            return ae.stop();
        }
      }
    }, ad);
  }))().catch(function (ae) {
    $.log(ae);
  }).finally(function () {
    $.done({});
  });
})();
function Env(t, e) {
  class s {
    constructor(t) {
      this.env = t;
    }
    send(t, e = "GET") {
      t = "string" == typeof t ? {
        url: t
      } : t;
      let s = this.get;
      "POST" === e && (s = this.post);
      return new Promise((e, i) => {
        s.call(this, t, (t, s, o) => {
          t ? i(t) : e(s);
        });
      });
    }
    get(t) {
      return this.send.call(this.env, t);
    }
    post(t) {
      return this.send.call(this.env, t, "POST");
    }
  }
  return new class {
    constructor(t, e) {
      this.logLevels = {
        debug: 0,
        info: 1,
        warn: 2,
        error: 3
      };
      this.logLevelPrefixs = {
        debug: "[DEBUG] ",
        info: "[INFO] ",
        warn: "[WARN] ",
        error: "[ERROR] "
      };
      this.logLevel = "info";
      this.name = t;
      this.http = new s(this);
      this.data = null;
      this.dataFile = "box.dat";
      this.logs = [];
      this.isMute = !1;
      this.isNeedRewrite = !1;
      this.logSeparator = "\n";
      this.encoding = "utf-8";
      this.startTime = new Date().getTime();
      Object.assign(this, e);
      this.log("", `🔔${this.name}, 开始!`);
    }
    getEnv() {
      return "undefined" != typeof $environment && $environment["surge-version"] ? "Surge" : "undefined" != typeof $environment && $environment["stash-version"] ? "Stash" : "undefined" != typeof module && module.exports ? "Node.js" : "undefined" != typeof $task ? "Quantumult X" : "undefined" != typeof $loon ? "Loon" : "undefined" != typeof $rocket ? "Shadowrocket" : void 0;
    }
    isNode() {
      return "Node.js" === this.getEnv();
    }
    isQuanX() {
      return "Quantumult X" === this.getEnv();
    }
    isSurge() {
      return "Surge" === this.getEnv();
    }
    isLoon() {
      return "Loon" === this.getEnv();
    }
    isShadowrocket() {
      return "Shadowrocket" === this.getEnv();
    }
    isStash() {
      return "Stash" === this.getEnv();
    }
    toObj(t, e = null) {
      try {
        return JSON.parse(t);
      } catch {
        return e;
      }
    }
    toStr(t, e = null, ...s) {
      try {
        return JSON.stringify(t, ...s);
      } catch {
        return e;
      }
    }
    getjson(t, e) {
      let s = e;
      if (this.getdata(t)) {
        try {
          s = JSON.parse(this.getdata(t));
        } catch {}
      }
      return s;
    }
    setjson(t, e) {
      try {
        return this.setdata(JSON.stringify(t), e);
      } catch {
        return !1;
      }
    }
    getScript(t) {
      return new Promise(e => {
        this.get({
          url: t
        }, (t, s, i) => e(i));
      });
    }
    runScript(t, e) {
      return new Promise(s => {
        let i = this.getdata("@chavy_boxjs_userCfgs.httpapi");
        i = i ? i.replace(/\n/g, "").trim() : i;
        let o = this.getdata("@chavy_boxjs_userCfgs.httpapi_timeout");
        o = o ? 1 * o : 20;
        o = e && e.timeout ? e.timeout : o;
        const [r, a] = i.split("@"),
          n = {
            url: `http://${a}/v1/scripting/evaluate`,
            body: {
              script_text: t,
              mock_type: "cron",
              timeout: o
            },
            headers: {
              "X-Key": r,
              Accept: "*/*"
            },
            timeout: o
          };
        this.post(n, (t, e, i) => s(i));
      }).catch(t => this.logErr(t));
    }
    loaddata() {
      if (!this.isNode()) {
        return {};
      }
      {
        this.fs = this.fs ? this.fs : require("fs");
        this.path = this.path ? this.path : require("path");
        const t = this.path.resolve(this.dataFile),
          e = this.path.resolve(process.cwd(), this.dataFile),
          s = this.fs.existsSync(t),
          i = !s && this.fs.existsSync(e);
        if (!s && !i) {
          return {};
        }
        {
          const i = s ? t : e;
          try {
            return JSON.parse(this.fs.readFileSync(i));
          } catch (t) {
            return {};
          }
        }
      }
    }
    writedata() {
      if (this.isNode()) {
        this.fs = this.fs ? this.fs : require("fs");
        this.path = this.path ? this.path : require("path");
        const t = this.path.resolve(this.dataFile),
          e = this.path.resolve(process.cwd(), this.dataFile),
          s = this.fs.existsSync(t),
          i = !s && this.fs.existsSync(e),
          o = JSON.stringify(this.data);
        s ? this.fs.writeFileSync(t, o) : i ? this.fs.writeFileSync(e, o) : this.fs.writeFileSync(t, o);
      }
    }
    lodash_get(t, e, s) {
      const i = e.replace(/\[(\d+)\]/g, ".$1").split(".");
      let o = t;
      for (const t of i) if (o = Object(o)[t], void 0 === o) {
        return s;
      }
      return o;
    }
    lodash_set(t, e, s) {
      Object(t) !== t || (Array.isArray(e) || (e = e.toString().match(/[^.[\]]+/g) || []), e.slice(0, -1).reduce((t, s, i) => Object(t[s]) === t[s] ? t[s] : t[s] = Math.abs(e[i + 1]) >> 0 == +e[i + 1] ? [] : {}, t)[e[e.length - 1]] = s);
      return t;
    }
    getdata(t) {
      let e = this.getval(t);
      if (/^@/.test(t)) {
        const [, s, i] = /^@(.*?)\.(.*?)$/.exec(t),
          o = s ? this.getval(s) : "";
        if (o) {
          try {
            const t = JSON.parse(o);
            e = t ? this.lodash_get(t, i, "") : e;
          } catch (t) {
            e = "";
          }
        }
      }
      return e;
    }
    setdata(t, e) {
      let s = !1;
      if (/^@/.test(e)) {
        const [, i, o] = /^@(.*?)\.(.*?)$/.exec(e),
          r = this.getval(i),
          a = i ? "null" === r ? null : r || "{}" : "{}";
        try {
          const e = JSON.parse(a);
          this.lodash_set(e, o, t);
          s = this.setval(JSON.stringify(e), i);
        } catch (e) {
          const r = {};
          this.lodash_set(r, o, t);
          s = this.setval(JSON.stringify(r), i);
        }
      } else {
        s = this.setval(t, e);
      }
      return s;
    }
    getval(t) {
      switch (this.getEnv()) {
        case "Surge":
        case "Loon":
        case "Stash":
        case "Shadowrocket":
          return $persistentStore.read(t);
        case "Quantumult X":
          return $prefs.valueForKey(t);
        case "Node.js":
          this.data = this.loaddata();
          return this.data[t];
        default:
          return this.data && this.data[t] || null;
      }
    }
    setval(t, e) {
      switch (this.getEnv()) {
        case "Surge":
        case "Loon":
        case "Stash":
        case "Shadowrocket":
          return $persistentStore.write(t, e);
        case "Quantumult X":
          return $prefs.setValueForKey(t, e);
        case "Node.js":
          this.data = this.loaddata();
          this.data[e] = t;
          this.writedata();
          return !0;
        default:
          return this.data && this.data[e] || null;
      }
    }
    initGotEnv(t) {
      this.got = this.got ? this.got : require("got");
      this.cktough = this.cktough ? this.cktough : require("tough-cookie");
      this.ckjar = this.ckjar ? this.ckjar : new this.cktough.CookieJar();
      t && (t.headers = t.headers ? t.headers : {}, t && (t.headers = t.headers ? t.headers : {}, void 0 === t.headers.cookie && void 0 === t.headers.Cookie && void 0 === t.cookieJar && (t.cookieJar = this.ckjar)));
    }
    get(t, e = () => {}) {
      switch (t.headers && (delete t.headers["Content-Type"], delete t.headers["Content-Length"], delete t.headers["content-type"], delete t.headers["content-length"]), t.params && (t.url += "?" + this.queryStr(t.params)), void 0 === t.followRedirect || t.followRedirect || ((this.isSurge() || this.isLoon()) && (t["auto-redirect"] = !1), this.isQuanX() && (t.opts ? t.opts.redirection = !1 : t.opts = {
        redirection: !1
      })), this.getEnv()) {
        case "Surge":
        case "Loon":
        case "Stash":
        case "Shadowrocket":
        default:
          this.isSurge() && this.isNeedRewrite && (t.headers = t.headers || {}, Object.assign(t.headers, {
            "X-Surge-Skip-Scripting": !1
          }));
          $httpClient.get(t, (t, s, i) => {
            !t && s && (s.body = i, s.statusCode = s.status ? s.status : s.statusCode, s.status = s.statusCode);
            e(t, s, i);
          });
          break;
        case "Quantumult X":
          this.isNeedRewrite && (t.opts = t.opts || {}, Object.assign(t.opts, {
            hints: !1
          }));
          $task.fetch(t).then(t => {
            const {
              statusCode: s,
              statusCode: i,
              headers: o,
              body: r,
              bodyBytes: a
            } = t;
            e(null, {
              status: s,
              statusCode: i,
              headers: o,
              body: r,
              bodyBytes: a
            }, r, a);
          }, t => e(t && t.error || "UndefinedError"));
          break;
        case "Node.js":
          let s = require("iconv-lite");
          this.initGotEnv(t);
          this.got(t).on("redirect", (t, e) => {
            try {
              if (t.headers["set-cookie"]) {
                const s = t.headers["set-cookie"].map(this.cktough.Cookie.parse).toString();
                s && this.ckjar.setCookieSync(s, null);
                e.cookieJar = this.ckjar;
              }
            } catch (t) {
              this.logErr(t);
            }
          }).then(t => {
            const {
                statusCode: i,
                statusCode: o,
                headers: r,
                rawBody: a
              } = t,
              n = s.decode(a, this.encoding);
            e(null, {
              status: i,
              statusCode: o,
              headers: r,
              rawBody: a,
              body: n
            }, n);
          }, t => {
            const {
              message: i,
              response: o
            } = t;
            e(i, o, o && s.decode(o.rawBody, this.encoding));
          });
          break;
      }
    }
    post(t, e = () => {}) {
      const s = t.method ? t.method.toLocaleLowerCase() : "post";
      switch (t.body && t.headers && !t.headers["Content-Type"] && !t.headers["content-type"] && (t.headers["content-type"] = "application/x-www-form-urlencoded"), t.headers && (delete t.headers["Content-Length"], delete t.headers["content-length"]), void 0 === t.followRedirect || t.followRedirect || ((this.isSurge() || this.isLoon()) && (t["auto-redirect"] = !1), this.isQuanX() && (t.opts ? t.opts.redirection = !1 : t.opts = {
        redirection: !1
      })), this.getEnv()) {
        case "Surge":
        case "Loon":
        case "Stash":
        case "Shadowrocket":
        default:
          this.isSurge() && this.isNeedRewrite && (t.headers = t.headers || {}, Object.assign(t.headers, {
            "X-Surge-Skip-Scripting": !1
          }));
          $httpClient[s](t, (t, s, i) => {
            !t && s && (s.body = i, s.statusCode = s.status ? s.status : s.statusCode, s.status = s.statusCode);
            e(t, s, i);
          });
          break;
        case "Quantumult X":
          t.method = s;
          this.isNeedRewrite && (t.opts = t.opts || {}, Object.assign(t.opts, {
            hints: !1
          }));
          $task.fetch(t).then(t => {
            const {
              statusCode: s,
              statusCode: i,
              headers: o,
              body: r,
              bodyBytes: a
            } = t;
            e(null, {
              status: s,
              statusCode: i,
              headers: o,
              body: r,
              bodyBytes: a
            }, r, a);
          }, t => e(t && t.error || "UndefinedError"));
          break;
        case "Node.js":
          let i = require("iconv-lite");
          this.initGotEnv(t);
          const {
            url: o,
            ...r
          } = t;
          this.got[s](o, r).then(t => {
            const {
                statusCode: s,
                statusCode: o,
                headers: r,
                rawBody: a
              } = t,
              n = i.decode(a, this.encoding);
            e(null, {
              status: s,
              statusCode: o,
              headers: r,
              rawBody: a,
              body: n
            }, n);
          }, t => {
            const {
              message: s,
              response: o
            } = t;
            e(s, o, o && i.decode(o.rawBody, this.encoding));
          });
          break;
      }
    }
    time(t, e = null) {
      const s = e ? new Date(e) : new Date();
      let i = {
        "M+": s.getMonth() + 1,
        "d+": s.getDate(),
        "H+": s.getHours(),
        "m+": s.getMinutes(),
        "s+": s.getSeconds(),
        "q+": Math.floor((s.getMonth() + 3) / 3),
        S: s.getMilliseconds()
      };
      /(y+)/.test(t) && (t = t.replace(RegExp.$1, (s.getFullYear() + "").substr(4 - RegExp.$1.length)));
      for (let e in i) new RegExp("(" + e + ")").test(t) && (t = t.replace(RegExp.$1, 1 == RegExp.$1.length ? i[e] : ("00" + i[e]).substr(("" + i[e]).length)));
      return t;
    }
    queryStr(t) {
      let e = "";
      for (const s in t) {
        let i = t[s];
        null != i && "" !== i && ("object" == typeof i && (i = JSON.stringify(i)), e += `${s}=${i}&`);
      }
      e = e.substring(0, e.length - 1);
      return e;
    }
    msg(e = t, s = "", i = "", o = {}) {
      const r = t => {
        const {
          $open: e,
          $copy: s,
          $media: i,
          $mediaMime: o
        } = t;
        switch (typeof t) {
          case void 0:
            return t;
          case "string":
            switch (this.getEnv()) {
              case "Surge":
              case "Stash":
              default:
                return {
                  url: t
                };
              case "Loon":
              case "Shadowrocket":
                return t;
              case "Quantumult X":
                return {
                  "open-url": t
                };
              case "Node.js":
                return;
            }
          case "object":
            switch (this.getEnv()) {
              case "Surge":
              case "Stash":
              case "Shadowrocket":
              default:
                {
                  const r = {};
                  let a = t.openUrl || t.url || t["open-url"] || e;
                  a && Object.assign(r, {
                    action: "open-url",
                    url: a
                  });
                  let n = t["update-pasteboard"] || t.updatePasteboard || s;
                  if (n && Object.assign(r, {
                    action: "clipboard",
                    text: n
                  }), i) {
                    let t, e, s;
                    if (i.startsWith("http")) {
                      t = i;
                    } else {
                      if (i.startsWith("data:")) {
                        const [t] = i.split(";"),
                          [, o] = i.split(",");
                        e = o;
                        s = t.replace("data:", "");
                      } else {
                        e = i;
                        s = (t => {
                          const e = {
                            JVBERi0: "application/pdf",
                            R0lGODdh: "image/gif",
                            R0lGODlh: "image/gif",
                            iVBORw0KGgo: "image/png",
                            "/9j/": "image/jpg"
                          };
                          for (var s in e) if (0 === t.indexOf(s)) {
                            return e[s];
                          }
                          return null;
                        })(i);
                      }
                    }
                    Object.assign(r, {
                      "media-url": t,
                      "media-base64": e,
                      "media-base64-mime": o ?? s
                    });
                  }
                  Object.assign(r, {
                    "auto-dismiss": t["auto-dismiss"],
                    sound: t.sound
                  });
                  return r;
                }
              case "Loon":
                {
                  const s = {};
                  let o = t.openUrl || t.url || t["open-url"] || e;
                  o && Object.assign(s, {
                    openUrl: o
                  });
                  let r = t.mediaUrl || t["media-url"];
                  i?.startsWith("http") && (r = i);
                  r && Object.assign(s, {
                    mediaUrl: r
                  });
                  console.log(JSON.stringify(s));
                  return s;
                }
              case "Quantumult X":
                {
                  const o = {};
                  let r = t["open-url"] || t.url || t.openUrl || e;
                  r && Object.assign(o, {
                    "open-url": r
                  });
                  let a = t["media-url"] || t.mediaUrl;
                  i?.startsWith("http") && (a = i);
                  a && Object.assign(o, {
                    "media-url": a
                  });
                  let n = t["update-pasteboard"] || t.updatePasteboard || s;
                  n && Object.assign(o, {
                    "update-pasteboard": n
                  });
                  console.log(JSON.stringify(o));
                  return o;
                }
              case "Node.js":
                return;
            }
          default:
            return;
        }
      };
      if (!this.isMute) {
        switch (this.getEnv()) {
          case "Surge":
          case "Loon":
          case "Stash":
          case "Shadowrocket":
          default:
            $notification.post(e, s, i, r(o));
            break;
          case "Quantumult X":
            $notify(e, s, i, r(o));
            break;
          case "Node.js":
            break;
        }
      }
      if (!this.isMuteLog) {
        let t = ["", "==============📣系统通知📣=============="];
        t.push(e);
        s && t.push(s);
        i && t.push(i);
        console.log(t.join("\n"));
        this.logs = this.logs.concat(t);
      }
    }
    debug(...t) {
      this.logLevels[this.logLevel] <= this.logLevels.debug && (t.length > 0 && (this.logs = [...this.logs, ...t]), console.log(`${this.logLevelPrefixs.debug}${t.map(t => t ?? String(t)).join(this.logSeparator)}`));
    }
    info(...t) {
      this.logLevels[this.logLevel] <= this.logLevels.info && (t.length > 0 && (this.logs = [...this.logs, ...t]), console.log(`${this.logLevelPrefixs.info}${t.map(t => t ?? String(t)).join(this.logSeparator)}`));
    }
    warn(...t) {
      this.logLevels[this.logLevel] <= this.logLevels.warn && (t.length > 0 && (this.logs = [...this.logs, ...t]), console.log(`${this.logLevelPrefixs.warn}${t.map(t => t ?? String(t)).join(this.logSeparator)}`));
    }
    error(...t) {
      this.logLevels[this.logLevel] <= this.logLevels.error && (t.length > 0 && (this.logs = [...this.logs, ...t]), console.log(`${this.logLevelPrefixs.error}${t.map(t => t ?? String(t)).join(this.logSeparator)}`));
    }
    log(...t) {
      t.length > 0 && (this.logs = [...this.logs, ...t]);
      console.log(t.map(t => t ?? String(t)).join(this.logSeparator));
    }
    logErr(t, e) {
      switch (this.getEnv()) {
        case "Surge":
        case "Loon":
        case "Stash":
        case "Shadowrocket":
        case "Quantumult X":
        default:
          this.log("", `❗️${this.name}, 错误!`, e, t);
          break;
        case "Node.js":
          this.log("", `❗️${this.name}, 错误!`, e, void 0 !== t.message ? t.message : t, t.stack);
          break;
      }
    }
    wait(t) {
      return new Promise(e => setTimeout(e, t));
    }
    done(t = {}) {
      const e = (new Date().getTime() - this.startTime) / 1000;
      switch (this.log("", `🔔${this.name}, 结束! 🕛 ${e} 秒`), this.log(), this.getEnv()) {
        case "Surge":
        case "Loon":
        case "Stash":
        case "Shadowrocket":
        case "Quantumult X":
        default:
          $done(t);
          break;
        case "Node.js":
          process.exit(1);
      }
    }
  }(t, e);
}