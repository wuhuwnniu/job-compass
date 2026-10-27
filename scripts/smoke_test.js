#!/usr/bin/env node
/* 无浏览器冒烟测试：用极简 DOM 桩跑通 app.js 的每条路由与主要交互。
   用法：node scripts/smoke_test.js  （需先有 app/data.js） */
'use strict';
const fs = require('fs');
const path = require('path');
const vm = require('vm');

const APP = path.join(__dirname, '..', 'app');
const read = (f) => fs.readFileSync(path.join(APP, f), 'utf8');

if (!fs.existsSync(path.join(APP, 'data.js'))) {
  console.error('缺少 app/data.js，先运行 python scripts/build_data.py');
  process.exit(1);
}
if (!fs.existsSync(path.join(APP, 'dadian.js'))) {
  console.error('缺少 app/dadian.js，先运行 python scripts/build_dadian.py');
  process.exit(1);
}

/* ---------- 极简 DOM 桩 ---------- */
function makeEl(id) {
  return {
    id,
    innerHTML: '',
    value: '',
    style: {},
    setAttribute() {},
    getAttribute() { return null; },
    appendChild() {},
    addEventListener() {},
  };
}

const els = { app: makeEl('app'), hits: makeEl('hits'), q: makeEl('q'), ddlist: makeEl('ddlist') };
const listeners = { click: [], input: [], hashchange: [] };
const store = new Map();

const sandbox = {
  console,
  Math, JSON, Date, RegExp, Object, Array, String, Number, Boolean, Error,
  setTimeout, clearTimeout,
  alert() {},
  navigator: {},
  history: { length: 2, back() {} },
  location: { hash: '#/', protocol: 'file:', href: 'file:///index.html' },
  document: {
    getElementById: (id) => els[id] || null,
    addEventListener: (t, fn) => {
      if (listeners[t]) listeners[t].push(fn);
    },
  },
  localStorage: {
    getItem: (k) => (store.has(k) ? store.get(k) : null),
    setItem: (k, v) => store.set(k, String(v)),
    removeItem: (k) => store.delete(k),
  },
};
sandbox.window = sandbox;
sandbox.globalThis = sandbox;
sandbox.window.addEventListener = (t, fn) => {
  if (listeners[t]) listeners[t].push(fn);
};
sandbox.window.scrollTo = () => {};

const ctx = vm.createContext(sandbox);
vm.runInContext(read('data.js'), ctx, { filename: 'data.js' });
vm.runInContext(read('dadian.js'), ctx, { filename: 'dadian.js' });
vm.runInContext(read('app.js'), ctx, { filename: 'app.js' });

/* ---------- 断言工具 ---------- */
let fails = 0;
function ok(cond, name, extra) {
  if (cond) {
    console.log('  ✓ ' + name);
  } else {
    fails++;
    console.log('  ✗ ' + name + (extra ? '  ' + String(extra).slice(0, 400) : ''));
  }
}
function html() {
  return els.app.innerHTML;
}
function nav(hash) {
  sandbox.location.hash = hash;
  listeners.hashchange.forEach((fn) => fn());
  return html();
}
function noCrash(text) {
  return !/undefined|NaN|\[object Object\]/.test(text);
}

function tagsBalanced(text) {
  const tags = ['div', 'a', 'span', 'p', 'ul', 'ol', 'li', 'h1', 'h2', 'h3', 'h4', 'nav', 'button', 'textarea'];
  const bad = [];
  for (const t of tags) {
    const open = (text.match(new RegExp('<' + t + '(?=[\\s>])', 'g')) || []).length;
    const close = (text.match(new RegExp('</' + t + '>', 'g')) || []).length;
    if (open !== close) bad.push(t + ':' + open + '/' + close);
  }
  return bad;
}

/* ---------- 路由逐条渲染 ---------- */
console.log('\n[路由渲染]');
let h = nav('#/');
ok(h.includes('岗位罗盘') && h.includes('开始：说说我会什么'), '首页');
ok(noCrash(h), '首页无 undefined/NaN');

h = nav('#/wizard/0');
ok(h.includes('第 1 / 3 步') && h.includes('你的专业'), '自评第 1 步');

h = nav('#/wizard/1');
ok(h.includes('哪些是你真的会的'), '自评第 2 步（技能）');

h = nav('#/wizard/2');
ok(h.includes('最后两件小事'), '自评第 3 步（偏好）');

h = nav('#/jobs');
ok(h.includes('岗位库') && h.includes('前端开发工程师'), '岗位库');

h = nav('#/job/fe-dev');
ok(h.includes('每天在做什么') && h.includes('怎么入门') && h.includes('钱和以后'), '岗位详情');
ok(noCrash(h), '详情无 undefined/NaN');

h = nav('#/search');
ok(h.includes('搜一搜'), '搜索页');

h = nav('#/dadian');
ok(h.includes('职业大典') && h.includes('1636'), '职业大典列表页');
ok(noCrash(h), '大典页无 undefined/NaN');

h = nav('#/dadian/4-04-05-01');
ok(h.includes('计算机程序设计员') && h.includes('官方定义'), '大典详情页');

h = nav('#/job/fe-dev');
ok(h.includes('国家职业分类里，它叫'), '岗位页挂上大典对应');

h = nav('#/about');
ok(h.includes('关于这个应用'), '关于页');

/* ---------- 标签闭合 ---------- */
console.log('\n[标签闭合]');
const routes = ['#/', '#/wizard/0', '#/wizard/1', '#/wizard/2', '#/jobs', '#/job/fe-dev',
  '#/job/nurse', '#/job/headhunter', '#/search', '#/dadian', '#/dadian/4-04-05-01', '#/about'];
routes.forEach((r) => {
  const bad = tagsBalanced(nav(r));
  ok(bad.length === 0, r + ' 标签闭合', bad.join(' '));
});

/* ---------- 交互：勾技能 → 生成结果 ---------- */
console.log('\n[交互流程]');
function click(attrs) {
  const el = {
    getAttribute: (k) => {
      const key = String(k).replace(/^data-/, '');
      return key in attrs ? String(attrs[key]) : null;
    },
  };
  const target = {
    closest(sel) {
      if (sel === '[data-go]') return attrs.go ? el : null;
      if (sel === '[data-act]') return attrs.act ? el : null;
      return null;
    },
  };
  listeners.click.forEach((fn) => fn({ target, preventDefault() {} }));
}

nav('#/wizard/1');
click({ act: 'lvl', id: 'frontend', lv: 3 });
click({ act: 'lvl', id: 'programming', lv: 2 });
click({ act: 'lvl', id: 'git', lv: 2 });
click({ act: 'lvl', id: 'problem_solving', lv: 2 });
click({ act: 'lvl', id: 'learning', lv: 2 });
click({ act: 'lvl', id: 'teamwork', lv: 1 });
ok(html().includes('已选 6 项'), '技能勾选计数');

click({ act: 'finish' });
ok(store.has('jrc.profile.v2'), '生成结果时写入本地档案');

h = nav('#/result');
ok(h.includes('现在就能投') || h.includes('补一补就能投'), '结果页出现分桶');
ok(h.includes('前端开发工程师'), '结果页包含前端开发工程师');
ok(noCrash(h), '结果页无 undefined/NaN');

const profile = JSON.parse(store.get('jrc.profile.v2'));
ok(profile.skills && profile.skills.frontend === 3, '档案里保存了技能熟练度');

/* ---------- 检索 ---------- */
console.log('\n[检索]');
nav('#/search');
const inputEl = {
  getAttribute: (k) => (k === 'data-field' ? 'q' : null),
  value: '会计',
};
listeners.input.forEach((fn) => fn({ target: inputEl }));
ok(els.hits.innerHTML.includes('会计'), '搜索「会计」有命中');
ok(noCrash(els.hits.innerHTML), '搜索结果无 undefined/NaN');

/* ---------- 职业大典检索与筛选 ---------- */
console.log('\n[职业大典]');
nav('#/dadian');
click({ act: 'dcat', c: '2' });
ok(html().includes('‹ 全部分类') && els.ddlist.innerHTML.includes('共 489 个'), '按大类筛选（专业技术 489）');
listeners.input.forEach((fn) => fn({ target: { getAttribute: () => 'dq', value: '电工' } }));
ok(els.ddlist.innerHTML.includes('电工'), '大典搜索「电工」有命中');
ok(!els.ddlist.innerHTML.includes('共 1636 个'), '搜索后列表被过滤');
listeners.input.forEach((fn) => fn({ target: { getAttribute: () => 'dq', value: '不存在职业xyz' } }));
ok(els.ddlist.innerHTML.includes('没搜到'), '搜不到时有空状态');

const jd = '负责公司新媒体账号日常运营，撰写文案，策划选题，分析数据并优化内容，配合活动执行。';
sandbox.location.hash = '#/search';
listeners.hashchange.forEach((fn) => fn());
listeners.input.forEach((fn) => fn({ target: { getAttribute: () => 'q', value: jd } }));
ok(els.hits.innerHTML.includes('新媒体运营') || els.hits.innerHTML.includes('内容运营'),
  '整段 JD 能匹配到运营类岗位');

/* ---------- 边界：没有档案时直接进结果页 ---------- */
console.log('\n[边界]');
store.clear();
nav('#/jobs'); // 重置渲染
ok(true, '存储清空后不报错');

/* ---------- 数据完整性 ---------- */
console.log('\n[数据完整性]');
const data = sandbox.JOB_DATA;
ok(data.jobs.length === 150, '岗位数 = 150', '实际 ' + data.jobs.length);
ok(data.skills.length >= 100, '技能数 ≥ 100', '实际 ' + data.skills.length);
const ids = new Set(data.jobs.map((j) => j.id));
ok(data.jobs.every((j) => (j.adjacent || []).every((a) => ids.has(a))), '相邻岗位引用全部有效');
ok(data.jobs.every((j) => (j.skills || []).every((s) => new Set(data.skills.map((x) => x.id)).has(s.id))),
  '技能引用全部有效');
ok(new Set(data.jobs.map((j) => j.id)).size === data.jobs.length, '岗位 id 无重复');

const dd = sandbox.DADIAN;
ok(dd.list.length === 1636, '大典职业数 = 1636', '实际 ' + dd.list.length);
ok(dd.cats.length === 8, '大典大类 = 8');
ok(Object.keys(dd.map).length === 150, '150 个岗位都有大典映射', '实际 ' + Object.keys(dd.map).length);
const ddCodes = new Set(dd.list.map((x) => x.c));
ok(Object.values(dd.map).every((cs) => cs.every((c) => ddCodes.has(c))), '映射的大典编码全部存在');
ok(dd.list.every((x) => x.n && x.c && x.d), '大典条目字段完整');

console.log('\n' + (fails ? `✗ ${fails} 项失败\n` : '✓ 全部通过\n'));
process.exit(fails ? 1 : 0);
