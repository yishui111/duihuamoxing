// 模拟 loader.js 的 fetch 包装（含 clone 修复），验证：
// 1) 包装后 Open WebUI 的 res.json() 不再报 "body stream already read"
// 2) 流式响应也能被正常消费
// 用法:
//   node tests\loader_fetch_test.mjs
// 环境变量:
//   OWUI_URL      默认 http://localhost:8088
//   OWUI_EMAIL / OWUI_PASSWORD   Open WebUI 登录账号（以环境变量传入，不提供则跳过登录与对话用例）
const BASE = process.env.OWUI_URL || 'http://localhost:8088';

// ---------- 复刻 loader.js 第一个 IIFE 的包装（修复后版本） ----------
function makeChatWrap(nativeFetch) {
  function isChatRequest(url, method) {
    if (method !== 'POST' || typeof url !== 'string') return false;
    if (url.indexOf('/api/chat/completions') !== -1) return true;
    if (url.indexOf('/api/chat/') !== -1) return true;
    if (url.length >= 9 && url.slice(-9) === '/api/chat') return true;
    return false;
  }
  return function (input, init) {
    const url = typeof input === 'string' ? input : (input && input.url) || '';
    const method = (init && init.method) || (input && input.method) || 'GET';
    const promise = nativeFetch.apply(this, arguments);
    if (isChatRequest(url, method)) {
      const timer = setTimeout(() => console.log('[wrap] 10s 无数据 -> 显示提示条（未触发才算正常）'), 10000);
      let done = false;
      promise.then(function (res) {
        if (!res || !res.body || typeof res.body.getReader !== 'function') {
          clearTimeout(timer); return;
        }
        let clone;
        try { clone = res.clone(); } catch (e) { clearTimeout(timer); return; }
        if (!clone.body || typeof clone.body.getReader !== 'function') { clearTimeout(timer); return; }
        const reader = clone.body.getReader();
        const pump = function () {
          reader.read().then(function (r) {
            if (!done) { clearTimeout(timer); done = true; }
            if (r.done) return;
            pump();
          }).catch(function () { clearTimeout(timer); });
        };
        pump();
      }).catch(function () { clearTimeout(timer); });
    }
    return promise;
  };
}

async function main() {
  const email = process.env.OWUI_EMAIL;
  const passwd = process.env.OWUI_PASSWORD;
  if (!email || !passwd) {
    console.log('未提供 OWUI_EMAIL / OWUI_PASSWORD，跳过登录与对话测试（需先按 DEPLOY.md 完成部署并创建账号）。');
    return;
  }
  // 登录拿令牌
  const cred = { email: email };
  cred['password'] = passwd;
  const login = await fetch(`${BASE}/api/v1/auths/signin`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(cred),
  });
  const loginData = await login.json();
  const jwt = loginData.token;
  console.log('token 获取:', jwt ? 'OK' : 'FAIL');
  if (!jwt) throw new Error('登录失败: ' + JSON.stringify(loginData).slice(0, 200));

  // 应用包装
  const origFetch = global.fetch.bind(globalThis);
  global.fetch = makeChatWrap(origFetch);

  // 测试 1: 非流式 chat/completions -> res.json()
  console.log('\n[测试1] 非流式 chat/completions 后调用 res.json() ...');
  const r1 = await fetch(`${BASE}/api/chat/completions`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${jwt}` },
    body: JSON.stringify({ model: 'qwen2.5:7b', messages: [{ role: 'user', content: '你好' }], stream: false }),
  });
  const d1 = await r1.json(); // 之前这里会报 body stream already read
  console.log('[测试1] res.json() 正常, choices:', d1.choices ? d1.choices.length : 0, ', 回复:', (d1.choices && d1.choices[0] && d1.choices[0].message && d1.choices[0].message.content || '').slice(0, 30));

  // 测试 2: 流式 chat/completions -> 读 body 流
  console.log('\n[测试2] 流式 chat/completions 读取响应流 ...');
  const r2 = await fetch(`${BASE}/api/chat/completions`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${jwt}` },
    body: JSON.stringify({ model: 'qwen2.5:7b', messages: [{ role: 'user', content: '用三个字回答' }], stream: true }),
  });
  let chunks = 0, text = '';
  const reader = r2.body.getReader();
  const decoder = new TextDecoder();
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    chunks++;
    text += decoder.decode(value, { stream: true });
  }
  console.log('[测试2] 流式读取正常, chunks:', chunks, ', 首片段:', text.slice(0, 60).replace(/\n/g, ' '));

  console.log('\n===== 全部通过：clone 修复后 res.json() 与流式读取都正常 =====');
}

main().catch((e) => { console.error('测试失败:', e.message); process.exit(1); });
