/* 岗位罗盘 — 应用主逻辑（无框架、无构建、可离线） */
(function () {
  'use strict';

  var DATA = window.JOB_DATA;
  var app = document.getElementById('app');

  if (!DATA || !DATA.jobs || !DATA.jobs.length) {
    app.innerHTML = '<div class="empty">岗位数据没有加载成功，请确认 data.js 与 index.html 在同一个文件夹。</div>';
    return;
  }

  var SKILLS = DATA.skills.slice();
  var JOBS = DATA.jobs.slice();
  var SKILL = {}; SKILLS.forEach(function (s) { SKILL[s.id] = s; });
  var JOB = {}; JOBS.forEach(function (j) { JOB[j.id] = j; });
  var TRACKS = [];
  JOBS.forEach(function (j) { if (TRACKS.indexOf(j.track) < 0) TRACKS.push(j.track); });
  var CATS = [];
  SKILLS.forEach(function (s) { if (CATS.indexOf(s.cat) < 0) CATS.push(s.cat); });

  /* ---------------- 职业分类大典（外部数据） ---------------- */
  var DD = window.DADIAN || { list: [], map: {}, cats: [] };
  var DD_CODE = {};
  DD.list.forEach(function (x) { DD_CODE[x.c] = x; });
  var DD_JOBS = {};
  Object.keys(DD.map || {}).forEach(function (jid) {
    (DD.map[jid] || []).forEach(function (c) {
      (DD_JOBS[c] = DD_JOBS[c] || []).push(jid);
    });
  });
  var DD_AUTO = {};
  (DD.auto || []).forEach(function (jid) { DD_AUTO[jid] = 1; });
  var DD_TOTAL = DD.list.length;

  var TRACK_ICON = {
    '互联网/软件': '💻', '产品/设计': '🧩', '运营/市场': '📣', '销售/商务': '🤝',
    '职能/财务': '📊', '金融': '🏦', '教育': '🎓', '医疗/健康': '🩺',
    '制造/工程': '⚙️', '传媒/内容': '🎬', '公共服务/其他': '🏛️'
  };

  /* ---------------- 存储 ---------------- */
  var LS = { profile: 'jrc.profile.v2', draft: 'jrc.draft.v2', fav: 'jrc.fav.v2' };

  function load(key, fallback) {
    try { var v = JSON.parse(localStorage.getItem(key)); return v == null ? fallback : v; }
    catch (e) { return fallback; }
  }
  function save(key, val) {
    try { localStorage.setItem(key, JSON.stringify(val)); } catch (e) {}
  }

  var profile = load(LS.profile, null);
  var favs = load(LS.fav, []);
  var draft = load(LS.draft, null) || {
    edu: '本科', status: '应届毕业生', major: '', skills: {},
    mode: '', people: '', hours: 10, certs: ''
  };

  var state = {
    view: 'home', jobId: null, q: '', mode: 'job', track: '全部', step: 0,
    dq: '', dcat: '全部', ddLimit: 40, jobsLimit: 60
  };

  /* ---------------- 小工具 ---------------- */
  function esc(s) {
    return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
    });
  }
  function pct(n) { return Math.max(0, Math.min(100, Math.round(n * 100))); }
  function kRange(a) { return a[0] + '–' + a[1] + 'k'; }
  function go(hash) { location.hash = hash; }
  function back() {
    if (history.length > 1) history.back(); else go('#/');
  }
  function skillName(id) { return SKILL[id] ? SKILL[id].name : id; }

  function ring(p) {
    var r = 19, c = 2 * Math.PI * r, off = c * (1 - p / 100);
    var color = p >= 60 ? '#2F6F63' : (p >= 35 ? '#B4531F' : '#A79C8E');
    return '<div class="ring"><svg width="46" height="46" viewBox="0 0 46 46">' +
      '<circle cx="23" cy="23" r="' + r + '" fill="none" stroke="#EFEAE0" stroke-width="4"/>' +
      '<circle cx="23" cy="23" r="' + r + '" fill="none" stroke="' + color + '" stroke-width="4" stroke-linecap="round" ' +
      'stroke-dasharray="' + c.toFixed(1) + '" stroke-dashoffset="' + off.toFixed(1) + '"/>' +
      '</svg><div class="num">' + p + '<small>%</small></div></div>';
  }

  /* ---------------- 专业 → 技能 推断 ---------------- */
  var MAJOR_RULES = [
    { re: /计算机|软件|信息工程|人工智能|数据科学|网络工程|物联网|信息安全|数字媒体技术/,
      skills: ['programming', 'logic', 'learning', 'git'], tip: '计算机类' },
    { re: /电子|通信|自动化|电气|微电子|光电|仪器/,
      skills: ['programming', 'logic', 'problem_solving'], tip: '电子电气类' },
    { re: /数学|统计|物理|应用数学/,
      skills: ['statistics', 'logic', 'data_analysis', 'programming'], tip: '数理类' },
    { re: /会计|财务|审计|税收|财政/,
      skills: ['accounting', 'excel', 'detail', 'logic'], tip: '财会类' },
    { re: /金融|经济|投资|保险|国贸|国际经济/,
      skills: ['business_sense', 'excel', 'market_research', 'communication'], tip: '经济金融类' },
    { re: /工商管理|市场营销|管理科学|电子商务|人力资源|行政管理|公共管理/,
      skills: ['communication', 'business_sense', 'excel', 'operations'], tip: '管理类' },
    { re: /汉语言|中文|新闻|传播|广告|编辑出版|秘书/,
      skills: ['writing', 'editing', 'content_planning', 'communication'], tip: '中文传播类' },
    { re: /英语|日语|法语|德语|西班牙语|翻译|外语|俄语|朝鲜语/,
      skills: ['foreign_language', 'translation', 'writing'], tip: '外语类' },
    { re: /法学|法律|知识产权|政治学/,
      skills: ['law', 'logic', 'writing'], tip: '法学类' },
    { re: /心理|社会学|社会工作|教育学|学前教育|小学教育|特殊教育/,
      skills: ['psychology', 'empathy', 'communication', 'teaching'], tip: '教育心理类' },
    { re: /视觉传达|环境设计|工业设计|艺术设计|数字媒体艺术|美术|动画|服装设计/,
      skills: ['design_tools', 'creativity', 'ui_design'], tip: '设计类' },
    { re: /机械|车辆|材料|航空|船舶|能源与动力|农业机械/,
      skills: ['cad', '3d_modeling', 'manufacturing'], tip: '机械类' },
    { re: /土木|建筑|工程管理|测绘|给排水|城乡规划/,
      skills: ['cad', '3d_modeling', 'quality'], tip: '土木建筑类' },
    { re: /护理|临床|药学|医学|口腔|中医|公共卫生|康复|检验/,
      skills: ['medical', 'nursing', 'detail', 'empathy'], tip: '医药护理类' },
    { re: /生物|化学|环境|食品|农学|园林|动物/,
      skills: ['detail', 'logic', 'data_analysis'], tip: '生化环材类' },
    { re: /物流|供应链|交通运输|工业工程/,
      skills: ['procurement', 'excel', 'detail', 'problem_solving'], tip: '物流供应链类' },
    { re: /旅游|酒店|会展|体育|休闲/,
      skills: ['service_mind', 'communication', 'event_planning'], tip: '旅游体育类' },
    { re: /音乐|舞蹈|表演|戏剧|播音/,
      skills: ['creativity', 'communication', 'teaching'], tip: '艺术表演类' },
    { re: /历史|哲学|社会学|政治|马克思|国际关系/,
      skills: ['writing', 'logic', 'market_research'], tip: '人文社科类' }
  ];

  function majorMatches(jobMajor, major) {
    if (!major || !jobMajor) return false;
    var a = String(jobMajor), b = String(major);
    if (a === b) return true;
    if (b.length >= 2 && (a.indexOf(b) >= 0 || b.indexOf(a) >= 0)) return true;
    return false;
  }

  function inferSkills(major) {
    var out = {};
    if (!major) return out;
    for (var i = 0; i < MAJOR_RULES.length; i++) {
      if (MAJOR_RULES[i].re.test(major)) {
        MAJOR_RULES[i].skills.forEach(function (id) {
          if (SKILL[id]) out[id] = 1;
        });
        break;
      }
    }
    return out;
  }

  /* ---------------- 打分 ---------------- */
  var PREF_TRACK = {
    office: ['互联网/软件', '产品/设计', '职能/财务', '金融', '传媒/内容', '教育', '制造/工程'],
    field: ['销售/商务', '运营/市场', '公共服务/其他', '医疗/健康'],
    people: ['教育', '医疗/健康', '销售/商务', '运营/市场', '公共服务/其他', '职能/财务'],
    things: ['互联网/软件', '制造/工程', '金融', '产品/设计', '传媒/内容', '职能/财务']
  };

  function jobSkillItems(job, skills) {
    var items = [];
    (job.skills || []).forEach(function (x) {
      var s = SKILL[x.id];
      if (!s) return;
      items.push({ id: x.id, w: x.w || 1, lvl: (skills && skills[x.id]) || 0, def: s });
    });
    return items;
  }

  function scoreJob(job, p) {
    var items = jobSkillItems(job, p.skills);
    var W = 0, got = 0;
    items.forEach(function (it) { W += it.w; got += it.w * (it.lvl / 3); });
    var coverage = W ? got / W : 0;

    var bonus = 0;
    if (p.major && (job.majors || []).some(function (m) { return majorMatches(m, p.major); })) bonus += 0.10;

    if (job.friendly === '高' && (p.status === '应届毕业生' || p.status === '在校生')) bonus += 0.04;
    if (job.friendly === '低' && (p.status === '应届毕业生' || p.status === '在校生')) bonus -= 0.06;

    if (p.mode && PREF_TRACK[p.mode] && PREF_TRACK[p.mode].indexOf(job.track) >= 0) bonus += 0.03;
    if (p.people && PREF_TRACK[p.people] && PREF_TRACK[p.people].indexOf(job.track) >= 0) bonus += 0.03;

    var score = Math.max(0, Math.min(1, coverage + bonus));

    var gaps = items.filter(function (it) { return it.lvl < 2; })
      .sort(function (a, b) { return b.w - a.w; });
    var coreGaps = gaps.filter(function (it) { return it.w >= 2; });
    var have = items.filter(function (it) { return it.lvl > 0; }).length;

    return {
      job: job, score: score, coverage: coverage, items: items,
      gaps: gaps, coreGaps: coreGaps, have: have, total: items.length
    };
  }

  function recommend(p) {
    var all = JOBS.map(function (j) { return scoreJob(j, p); });
    all.sort(function (a, b) { return b.score - a.score; });

    var A = [], B = [], C = [];
    var usedIds = {};

    all.forEach(function (r) {
      if (A.length < 6 && r.score >= 0.55 && r.coreGaps.length <= 2) {
        A.push(r); usedIds[r.job.id] = 1;
      }
    });
    all.forEach(function (r) {
      if (usedIds[r.job.id]) return;
      if (B.length < 8 && r.score >= 0.30) { B.push(r); usedIds[r.job.id] = 1; }
    });

    var topTracks = (A.length ? A : B).slice(0, 3).map(function (r) { return r.job.track; });
    all.forEach(function (r) {
      if (usedIds[r.job.id]) return;
      if (C.length >= 4) return;
      if (r.score >= 0.16 && topTracks.indexOf(r.job.track) < 0) { C.push(r); usedIds[r.job.id] = 1; }
    });

    // 冷启动：一门技能都没勾，就按「应届友好 + 专业对口」先铺一批
    var hasSkills = Object.keys(p.skills || {}).length > 0;
    if (!hasSkills && !A.length && !B.length) {
      all.forEach(function (r) {
        if (B.length >= 8) return;
        if (usedIds[r.job.id]) return;
        if (r.job.friendly === '高' || r.job.friendly === '中') { B.push(r); usedIds[r.job.id] = 1; }
      });
    }

    return { A: A, B: B, C: C, total: all.length, hasSkills: hasSkills };
  }

  /* ---------------- 文档检索（BM25，中文用二元切分） ---------------- */
  function tokenize(text) {
    var out = [], s = String(text).toLowerCase();
    var re = /[a-z0-9+.#]{2,}|[\u4e00-\u9fa5]+/g, m;
    while ((m = re.exec(s))) {
      var t = m[0];
      if (/^[a-z0-9]/.test(t)) { out.push(t); continue; }
      for (var i = 0; i < t.length; i++) {
        out.push(t.charAt(i));
        if (i < t.length - 1) out.push(t.substr(i, 2));
      }
    }
    return out;
  }

  function docText(j) {
    var skills = (j.skills || []).map(function (x) {
      var d = SKILL[x.id]; return d ? d.name + ' ' + d.note : '';
    }).join(' ');
    var learn = (j.learn || []).map(function (s) { return s.stage + ' ' + s.goal + ' ' + (s.items || []).join(' '); }).join(' ');
    return [j.name, j.name, (j.aliases || []).join(' '), j.track, j.tagline,
      (j.daily || []).join(' '), (j.majors || []).join(' '), skills,
      (j.growth || []).join(' '), j.in3to5, learn, j.reality].join(' ');
  }

  var INDEX = null;
  function getIndex() {
    if (INDEX) return INDEX;
    var docs = JOBS.map(function (j) {
      var tokens = tokenize(docText(j));
      return { id: j.id, tokens: tokens, tf: countTokens(tokens), dl: tokens.length };
    });
    var df = {}, N = docs.length, totalDl = 0;
    docs.forEach(function (d) {
      totalDl += d.dl;
      Object.keys(d.tf).forEach(function (t) { df[t] = (df[t] || 0) + 1; });
    });
    INDEX = { docs: docs, df: df, N: N, avgdl: totalDl / Math.max(1, N) };
    return INDEX;
  }
  function countTokens(tokens) {
    var tf = {};
    tokens.forEach(function (t) { tf[t] = (tf[t] || 0) + 1; });
    return tf;
  }

  function searchDocs(query, limit) {
    var idx = getIndex();
    var seen = {}, qTokens = [];
    tokenize(query).forEach(function (t) {
      if (!seen[t]) { seen[t] = 1; qTokens.push(t); }
    });
    if (!qTokens.length) return [];
    var k1 = 1.4, b = 0.72, res = [];
    idx.docs.forEach(function (d) {
      var s = 0;
      qTokens.forEach(function (t) {
        var tf = d.tf[t] || 0;
        if (!tf) return;
        var df = idx.df[t] || 0;
        var idf = Math.log(1 + (idx.N - df + 0.5) / (df + 0.5));
        s += idf * (tf * (k1 + 1)) / (tf + k1 * (1 - b + b * d.dl / idx.avgdl));
      });
      if (s > 0.05) res.push({ id: d.id, score: s, job: JOB[d.id] });
    });
    res.sort(function (a, b2) { return b2.score - a.score; });
    return res.slice(0, limit || 12);
  }

  function highlight(text, q) {
    var t = esc(text);
    var toks = tokenize(q).filter(function (x) { return x.length >= 2; });
    var uniq = [];
    toks.forEach(function (x) { if (uniq.indexOf(x) < 0) uniq.push(x); });
    uniq.sort(function (a, b) { return b.length - a.length; });
    uniq.slice(0, 8).forEach(function (tok) {
      var safe = tok.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
      try { t = t.replace(new RegExp(safe, 'g'), function (m) { return '<mark>' + m + '</mark>'; }); } catch (e) {}
    });
    return t;
  }

  function snippet(job, q) {
    var fields = [
      { label: '日常', text: (job.daily || []).join(' ') },
      { label: '技能', text: (job.skills || []).map(function (x) { return skillName(x.id); }).join('、') },
      { label: '专业', text: (job.majors || []).join('、') },
      { label: '前景', text: job.in3to5 }
    ];
    var best = null, bestHits = 0;
    var toks = tokenize(q).filter(function (x) { return x.length >= 2; });
    fields.forEach(function (f) {
      var hits = 0;
      toks.forEach(function (t) { if (f.text && f.text.indexOf(t) >= 0) hits++; });
      if (hits > bestHits) { bestHits = hits; best = f; }
    });
    if (!best) best = { label: '一句话', text: job.tagline };
    var text = String(best.text || '');
    if (text.length > 110) text = text.slice(0, 110) + '…';
    return { label: best.label, html: highlight(text, q) };
  }

  /* ---------------- 渲染：公共部件 ---------------- */
  function tabbar() {
    var v = state.view;
    var active = (v === 'result' || v === 'wizard' || v === 'home') ? 'rec'
      : (v === 'search' ? 'search' : (v === 'dadian' ? 'dd' : 'jobs'));
    function t(id, icon, label, hash) {
      return '<button class="' + (active === id ? 'on' : '') + '" data-go="' + hash + '">' +
        '<span class="ic">' + icon + '</span>' + label + '</button>';
    }
    return '<nav class="tabbar">' +
      t('rec', '◈', '我的推荐', '#/rec') +
      t('jobs', '▤', '岗位库', '#/jobs') +
      t('dd', '▦', '职业大典', '#/dadian') +
      t('search', '⌕', '搜一搜', '#/search') +
      '</nav>';
  }

  function topbar(title, right, backBtn) {
    return '<div class="topbar">' +
      (backBtn ? '<button class="iconbtn ghost" data-act="back" aria-label="返回">‹</button>' : '') +
      '<h1>' + esc(title) + '</h1>' +
      (right || '') + '</div>';
  }

  function jobCardHtml(r) {
    var j = r.job;
    var p = pct(r.coverage);
    var gapTxt = r.coreGaps.length
      ? '还缺 ' + r.coreGaps.slice(0, 2).map(function (g) { return g.def.name; }).join('、') + (r.coreGaps.length > 2 ? ' 等' : '')
      : '核心技能基本齐了';
    return '<a class="jobcard" href="#/job/' + j.id + '">' +
      '<div class="top"><div style="flex:1;min-width:0">' +
      '<h3>' + esc(j.name) + '</h3>' +
      '<div class="track">' + (TRACK_ICON[j.track] || '') + ' ' + esc(j.track) + '</div>' +
      '</div>' + ring(p) + '</div>' +
      '<div class="tl">' + esc(j.tagline) + '</div>' +
      '<div class="foot">' +
      '<span class="fit">已具备 ' + r.have + '/' + r.total + ' 项</span>' +
      '<span class="gap">' + esc(gapTxt) + '</span>' +
      '</div></a>';
  }

  /* ---------------- 视图：首页 ---------------- */
  function viewHome() {
    var s = '';
    s += '<div class="screen">';
    s += '<div class="hero">';
    s += '<div class="brand"><span class="dot"></span>岗位罗盘</div>';
    s += '<h1>不知道想做什么，<br>那就先看看<em>你能做什么</em>。</h1>';
    s += '<p>招聘网站总要你先填「求职意向」。可如果你连有哪些岗位都不清楚呢？' +
      '这里反过来：你只说<b>专业</b>和<b>已经会的</b>，我告诉你可能适合的岗位、每个岗位要什么本事、你还差什么。</p>';
    s += '<div class="hero-actions">';
    s += '<button class="btn accent" data-go="#/wizard/0">开始：说说我会什么 ›</button>';
    s += '<button class="btn ghost" data-go="#/jobs">先随便逛逛 ' + JOBS.length + ' 个岗位</button>';
    s += '</div>';
    s += '<button class="chip" style="margin-top:10px" data-go="#/dadian">或者翻一翻职业大典：国家标准的 ' + DD_TOTAL + ' 种职业 ›</button>';
    s += '<div class="stat-row">' +
      '<div class="stat"><b>' + JOBS.length + '</b><span>个真实岗位</span></div>' +
      '<div class="stat"><b>' + SKILLS.length + '</b><span>项可勾选技能</span></div>' +
      '<div class="stat"><b>' + TRACKS.length + '</b><span>个行业方向</span></div>' +
      '</div></div>';

    if (profile) {
      s += '<div class="section"><div class="card">' +
        '<div class="section-hd" style="margin-bottom:6px"><h2>上次的结果还在</h2></div>' +
        '<p class="lead">你填的专业是「' + esc(profile.major || '未填') + '」，勾了 ' +
        Object.keys(profile.skills || {}).length + ' 项技能。</p>' +
        '<div class="btn-row" style="margin-top:12px">' +
        '<button class="btn sm" data-go="#/result">看推荐结果</button>' +
        '<button class="btn sm ghost" data-go="#/wizard/0">重新填一次</button>' +
        '</div></div></div>';
    }

    s += '<div class="section"><div class="section-hd"><h2>它是怎么想的</h2></div>';
    s += '<div class="card"><div class="steps">';
    s += '<div class="step"><div class="n">1</div><div><b>先不看你想干什么</b><p>只问你专业、课程、技能、实习和证书 —— 你确定的东西。</p></div></div>';
    s += '<div class="step"><div class="n">2</div><div><b>把技能拆成「岗位要的那几项」</b><p>每个岗位背后是一张技能清单，我算你覆盖了多少、核心项差几项。</p></div></div>';
    s += '<div class="step"><div class="n">3</div><div><b>分成三堆放你面前</b><p>现在就能投的、补一两项就能投的、你压根没想到但门槛不高的。</p></div></div>';
    s += '</div></div></div>';

    s += '<div class="section"><div class="card" style="background:var(--teal-soft);border-color:transparent">' +
      '<p class="lead" style="color:#1f4a42"><b>它不替你选人生。</b> 它做的事是：把「你可能可以去的地方」摊开，' +
      '每个地方标清楚门在哪、要带什么、进去以后是什么日子。剩下的还是你走。</p></div></div>';

    s += '<div class="section" style="padding-bottom:20px"><p class="tiny muted" style="text-align:center">' +
      '薪资与发展为公开信息整理的参考区间，不是官方统计；实际以招聘 JD 为准。</p></div>';
    s += '</div>';
    return s;
  }

  /* ---------------- 视图：自评向导 ---------------- */
  function viewWizard(step) {
    state.step = step;
    var s = '<div class="screen">';
    s += topbar('第 ' + (step + 1) + ' / 3 步', '', true);
    s += '<div class="progress">' +
      '<i class="' + (step >= 0 ? 'on' : '') + '"></i>' +
      '<i class="' + (step >= 1 ? 'on' : '') + '"></i>' +
      '<i class="' + (step >= 2 ? 'on' : '') + '"></i></div>';

    if (step === 0) {
      s += '<h2 style="font-size:21px">先说说你的基本情况</h2>';
      s += '<p class="lead" style="margin-top:6px">不用写求职意向。这些只是帮我把范围缩小一点。</p>';

      s += '<div class="field"><label>你现在的学历</label><div class="chips">';
      ['高中及以下', '专科', '本科', '硕士及以上'].forEach(function (x) {
        s += '<button class="chip' + (draft.edu === x ? ' on' : '') + '" data-act="set" data-k="edu" data-v="' + x + '">' + x + '</button>';
      });
      s += '</div></div>';

      s += '<div class="field"><label>你现在的状态</label><div class="chips">';
      ['在校生', '应届毕业生', '毕业 1–3 年', '待业中'].forEach(function (x) {
        s += '<button class="chip' + (draft.status === x ? ' on' : '') + '" data-act="set" data-k="status" data-v="' + x + '">' + x + '</button>';
      });
      s += '</div></div>';

      s += '<div class="field"><label>你的专业（或大概方向）</label>' +
        '<input class="input" id="major" data-field="major" placeholder="例如：计算机科学与技术 / 会计 / 汉语言文学" value="' + esc(draft.major) + '" list="majorlist" autocomplete="off">' +
        '<datalist id="majorlist">' + majorOptions() + '</datalist>' +
        '<div class="hint">想不到标准名称就填方向，比如「计算机」「会计」「师范」。这会影响我按专业替你预勾的技能。</div></div>';

      s += '<div style="margin-top:24px"><button class="btn accent" data-act="wizard-next">下一步：我学过什么 ›</button></div>';
    }

    if (step === 1) {
      var chosen = Object.keys(draft.skills || {}).length;
      s += '<h2 style="font-size:21px">哪些是你真的会的？</h2>';
      s += '<p class="lead" style="margin-top:6px">点一下选中，再点可以改熟练度。拿不准就往低了选 —— 高估自己，面试第一个问题就会露馅。</p>';
      s += '<div class="card" style="margin-top:14px;padding:12px 14px">' +
        '<b style="font-size:14px">已选 ' + chosen + ' 项</b>' +
        '<div class="tiny muted" style="margin-top:2px">一门都没选也能继续，只是推荐会粗一点。</div>' +
        (draft.major ? '<button class="btn sm ghost" style="margin-top:10px" data-act="infer">按专业「' + esc(draft.major) + '」帮我勾</button>' : '') +
        '</div>';

      var openCat = state.openCat;
      if (openCat === undefined) {
        var sel = Object.keys(draft.skills || {});
        openCat = (sel.length && SKILL[sel[0]]) ? SKILL[sel[0]].cat : CATS[0];
      }

      CATS.forEach(function (cat) {
        var list = SKILLS.filter(function (x) { return x.cat === cat; });
        var n = list.filter(function (x) { return (draft.skills || {})[x.id]; }).length;
        var open = openCat === cat ? ' open' : '';
        s += '<div class="acc' + open + '" style="margin-top:10px">';
        s += '<button class="acc-hd" data-act="acc" data-cat="' + esc(cat) + '"><b>' + esc(cat) + '</b>' +
          '<span class="cnt">' + (n ? n + ' 项' : list.length + ' 项可选') + '</span><span class="arw">⌄</span></button>';
        s += '<div class="acc-bd">';
        list.forEach(function (sk) {
          var lv = (draft.skills || {})[sk.id] || 0;
          s += '<div class="skillpick"><div class="t"><b>' + esc(sk.name) + '</b><span>' + esc(sk.note) + '</span></div>' +
            '<div class="lvls">' +
            ['了解', '会用', '熟练'].map(function (lab, i) {
              return '<button class="' + (lv === i + 1 ? 'on' : '') + '" data-act="lvl" data-id="' + sk.id + '" data-lv="' + (i + 1) + '">' + lab + '</button>';
            }).join('') +
            '</div></div>';
        });
        s += '</div></div>';
      });

      s += '<div class="btn-row" style="margin-top:22px">' +
        '<button class="btn ghost" style="flex:0 0 34%" data-go="#/wizard/0">上一步</button>' +
        '<button class="btn accent" data-go="#/wizard/2">下一步：偏好（可跳过）›</button></div>';
    }

    if (step === 2) {
      s += '<h2 style="font-size:21px">最后两件小事</h2>';
      s += '<p class="lead" style="margin-top:6px">都可以不填，只影响排序的小幅调整。</p>';

      s += '<div class="field"><label>你愿意待在哪工作</label><div class="chips">';
      [['office', '坐办公室'], ['field', '经常在外面跑'], ['any', '都行']].forEach(function (x) {
        s += '<button class="chip' + (draft.mode === x[0] ? ' on' : '') + '" data-act="set" data-k="mode" data-v="' + x[0] + '">' + x[1] + '</button>';
      });
      s += '</div></div>';

      s += '<div class="field"><label>你更愿意跟什么打交道</label><div class="chips">';
      [['people', '跟人'], ['things', '跟数据 / 机器'], ['any', '都行']].forEach(function (x) {
        s += '<button class="chip' + (draft.people === x[0] ? ' on' : '') + '" data-act="set" data-k="people" data-v="' + x[0] + '">' + x[1] + '</button>';
      });
      s += '</div></div>';

      s += '<div class="field"><label>每周能拿出多少时间学新东西</label><div class="chips">';
      [[5, '5 小时以内'], [10, '5–10 小时'], [20, '10 小时以上']].forEach(function (x) {
        s += '<button class="chip' + (draft.hours === x[0] ? ' on' : '') + '" data-act="set" data-k="hours" data-v="' + x[0] + '">' + x[1] + '</button>';
      });
      s += '</div></div>';

      s += '<div class="field"><label>证书、实习、作品（选填）</label>' +
        '<textarea class="input" data-field="certs" placeholder="例如：英语六级 / 有 3 个月新媒体实习 / 自己做过一个记账小程序">' + esc(draft.certs) + '</textarea>' +
        '<div class="hint">这部分暂时只用于你自己对照，不参与打分。</div></div>';

      s += '<div class="btn-row" style="margin-top:24px">' +
        '<button class="btn ghost" style="flex:0 0 34%" data-go="#/wizard/1">上一步</button>' +
        '<button class="btn accent" data-act="finish">生成我的岗位地图 ›</button></div>';
    }

    s += '</div>';
    return s;
  }

  function majorOptions() {
    var set = {};
    JOBS.forEach(function (j) { (j.majors || []).forEach(function (m) { set[m] = 1; }); });
    return Object.keys(set).sort().map(function (m) {
      return '<option value="' + esc(m) + '">';
    }).join('');
  }

  /* ---------------- 视图：推荐结果 ---------------- */
  function viewResult() {
    if (!profile) { go('#/wizard/0'); return ''; }
    var r = recommend(profile);
    var s = '<div class="screen">';
    s += topbar('我的岗位地图', '<button class="iconbtn ghost" data-go="#/wizard/0" aria-label="修改">✎</button>', false);

    var skillCount = Object.keys(profile.skills || {}).length;
    s += '<div class="verdict">' +
      '<div class="k">根据你会的东西</div>' +
      '<h2>' + (r.A.length ? '这些岗位，你现在就能投' : '先补一点，你就够得着了') + '</h2>' +
      '<p>专业「' + esc(profile.major || '未填') + '」· 勾了 ' + skillCount + ' 项技能 · ' +
      '扫了 ' + r.total + ' 个岗位</p></div>';

    if (!skillCount || profile.auto) {
      s += '<div class="card" style="margin-top:12px"><p class="lead">' +
        (profile.auto
          ? '你一门技能都没勾，我先按专业「' + esc(profile.major) + '」替你垫了 ' + skillCount + ' 项基础技能，所以结果会比较粗。'
          : '你还没勾任何技能，下面是按「应届生最容易进」和你的专业排的。') +
        '去确认一下你会什么，准确度会高很多。</p>' +
        '<button class="btn sm ghost" style="margin-top:12px" data-go="#/wizard/1">去勾技能</button></div>';
    }

    function bucket(title, hint, list, alt, emptyMsg) {
      if (!list.length) return '';
      var h = '<div class="bucket' + (alt ? ' alt' : '') + '"><div class="bucket-hd">' +
        '<h3>' + title + '</h3><div class="line"></div><span class="hint">' + hint + '</span></div>';
      list.forEach(function (x) { h += jobCardHtml(x); });
      return h + '</div>';
    }

    s += bucket('① 现在就能投', '核心技能基本齐',
      r.A, false);

    s += bucket(r.hasSkills ? '② 补一补就能投' : '先从这些看起',
      r.hasSkills ? '差 2–4 项，3–6 个月' : '应届生最容易进的',
      r.B, false);

    if (!r.A.length && !r.B.length) {
      s += '<div class="empty">你的技能和现有岗位对得上的不多。试试回上一步多勾几项，或者直接用搜索找岗位。</div>';
    }

    s += bucket('③ 你可能没想到的方向', '换个赛道，门槛没你想的高',
      r.C, true);

    s += '<div class="section"><div class="card">' +
      '<p class="tiny muted">匹配度 = 岗位技能清单里你已具备的权重比例，再按专业对口、应届友好度、你的偏好做小幅调整。' +
      '它不是录用概率，只是「你离这个岗位有多远」的粗略尺子。</p></div></div>';

    s += '<div class="section" style="padding-bottom:8px"><div class="btn-row">' +
      '<button class="btn ghost" data-go="#/jobs">看看全部岗位</button>' +
      '<button class="btn ghost" data-go="#/search">搜一个岗位</button></div></div>';
    s += '</div>';
    return s;
  }

  /* ---------------- 视图：岗位详情 ---------------- */
  function viewJob(id) {
    var j = JOB[id];
    if (!j) { go('#/jobs'); return ''; }

    var scored = profile ? scoreJob(j, profile) : null;
    var s = '<div class="screen">';
    var starred = favs.indexOf(id) >= 0;
    s += topbar('岗位详情',
      '<button class="iconbtn" data-act="fav" data-id="' + id + '" aria-label="收藏">' + (starred ? '★' : '☆') + '</button>', true);

    s += '<div class="detail-hero">' +
      '<div class="track">' + (TRACK_ICON[j.track] || '') + ' ' + esc(j.track) + '</div>' +
      '<h1>' + esc(j.name) + '</h1>' +
      '<div class="tagline">' + esc(j.tagline) + '</div>' +
      '<div class="chips" style="margin-top:10px">' +
      '<span class="chip tag">应届友好度 ' + esc(j.friendly) + '</span>' +
      (j.salary ? '<span class="chip tag">入门 ' + kRange(j.salary.junior) + '</span>' : '') +
      (j.aliases || []).map(function (a) { return '<span class="chip tag">' + esc(a) + '</span>'; }).join('') +
      '</div>' +
      (scored ? '<div class="meter"><div class="bar"><i style="width:' + pct(scored.coverage) + '%"></i></div>' +
        '<b>' + pct(scored.coverage) + '%</b><span>技能覆盖</span></div>' +
        '<div class="tiny muted" style="margin-top:6px">你已具备 ' + scored.have + ' / ' + scored.total + ' 项要求</div>' : '') +
      '</div>';

    /* 日常 */
    s += '<div class="section"><div class="section-hd"><h2>每天在做什么</h2></div><div class="card">' +
      '<ul class="plain daily">' + (j.daily || []).map(function (d) {
        return '<li>' + esc(d) + '</li>';
      }).join('') + '</ul></div></div>';

    /* 技能 */
    s += '<div class="section"><div class="section-hd"><h2>需要会什么</h2>' +
      '<span class="sub">' + (scored ? '缺 ' + scored.coreGaps.length + ' 项核心' : '核心 / 重要 / 加分') + '</span></div><div class="card">';
    (scored ? scored.items.sort(function (a, b) { return b.w - a.w; }) : j.skills.map(function (x) {
      return { id: x.id, w: x.w, lvl: 0, def: SKILL[x.id] };
    })).forEach(function (it) {
      if (!it.def) return;
      var lv = it.lvl || 0;
      var badge = !scored ? ''
        : lv >= 3 ? '<span class="badge have">熟练</span>'
          : lv === 2 ? '<span class="badge have">会用</span>'
            : lv === 1 ? '<span class="badge part">了解</span>'
              : '<span class="badge miss">还不会</span>';
      var wb = it.w === 3 ? '<span class="badge w3">核心</span>' : it.w === 2 ? '<span class="badge w2">重要</span>' : '<span class="badge w1">加分</span>';
      s += '<div class="skillrow"><div class="nm">' + esc(it.def.name) +
        '<span class="why">' + esc(it.def.note) + '</span></div>' + wb + badge + '</div>';
    });
    s += '</div>';

    if (scored && scored.gaps.length) {
      s += '<div class="card" style="margin-top:12px"><b style="font-size:14px">最该补的 ' + Math.min(3, scored.gaps.length) + ' 项</b>' +
        '<div class="tiny muted" style="margin-top:4px">按这个岗位的重要性排的，先补这个性价比最高。</div>' +
        '<div class="chips" style="margin-top:10px">' +
        scored.gaps.slice(0, 3).map(function (g) {
          return '<span class="chip pill-soft">' + esc(g.def.name) + (g.w === 3 ? ' · 核心' : '') + '</span>';
        }).join('') + '</div></div>';
    } else if (!scored) {
      s += '<div class="card" style="margin-top:12px"><b style="font-size:14px">想看你差哪几项？</b>' +
        '<p class="lead" style="margin-top:4px">上面是这个岗位要求的能力。做一次 2 分钟自评，就能标出哪些你已经会、哪些还得补。</p>' +
        '<button class="btn sm accent" style="margin-top:10px" data-go="#/wizard/0">开始自评 ›</button></div>';
    }
    s += '</div>';

    /* 入门路线 */
    s += '<div class="section" id="learn"><div class="section-hd"><h2>怎么入门</h2><span class="sub">按 0–12 个月排</span></div><div class="card">' +
      '<div class="timeline">' + (j.learn || []).map(function (st) {
        return '<div class="tl-item"><h4>' + esc(st.stage) + '</h4>' +
          '<div class="goal">阶段目标：' + esc(st.goal) + '</div>' +
          '<ul>' + (st.items || []).map(function (x) { return '<li>' + esc(x) + '</li>'; }).join('') + '</ul></div>';
      }).join('') + '</div></div></div>';

    /* 前景 */
    s += '<div class="section"><div class="section-hd"><h2>钱和以后</h2></div><div class="card">';
    if (j.salary) {
      s += '<div class="salary">' +
        '<div><div class="lv">入门 / 应届</div><div class="val">' + kRange(j.salary.junior) + '</div></div>' +
        '<div><div class="lv">3–5 年</div><div class="val">' + kRange(j.salary.mid) + '</div></div>' +
        '<div><div class="lv">资深</div><div class="val">' + kRange(j.salary.senior) + '</div></div>' +
        '</div><div class="tiny muted" style="margin-top:8px">' + esc(j.salary.note || '') + '</div>';
    }
    if (j.growth) {
      s += '<div class="hr"></div><b style="font-size:13.5px">往上走的路</b><ul class="plain" style="margin-top:8px">' +
        j.growth.map(function (g) {
          return '<li style="position:relative;padding-left:16px;font-size:14px;color:var(--ink-2);margin-bottom:6px">' +
            '<span style="position:absolute;left:0;top:9px;width:5px;height:5px;border-radius:99px;background:var(--teal)"></span>' + esc(g) + '</li>';
        }).join('') + '</ul>';
    }
    if (j.in3to5) {
      s += '<div class="hr"></div><b style="font-size:13.5px">3–5 年后大概在哪</b><p class="lead" style="margin-top:6px">' + esc(j.in3to5) + '</p>';
    }
    s += '</div></div>';

    /* 真实的一面 */
    if (j.reality) {
      s += '<div class="section"><div class="section-hd"><h2>没人告诉你的部分</h2></div>' +
        '<div class="warnbox">' + esc(j.reality) + '</div></div>';
    }

    /* 相邻岗位 */
    var adj = (j.adjacent || []).filter(function (x) { return JOB[x]; });
    if (adj.length) {
      s += '<div class="section"><div class="section-hd"><h2>以后还能转到</h2></div><div class="adjgrid">' +
        adj.map(function (x) {
          var aj = JOB[x];
          return '<a class="adj" href="#/job/' + x + '"><b>' + esc(aj.name) + '</b><span>' + esc(aj.tagline) + '</span></a>';
        }).join('') + '</div></div>';
    }

    /* 专业 */
    if (j.majors && j.majors.length) {
      s += '<div class="section"><div class="section-hd"><h2>常见对口专业</h2></div><div class="chips">' +
        j.majors.map(function (m) { return '<span class="chip tag">' + esc(m) + '</span>'; }).join('') + '</div>' +
        '<p class="tiny muted" style="margin-top:8px">专业不对口不等于不能投，只是要拿出别的东西证明你会。</p></div>';
    }

    /* 国家职业分类 */
    var ddCodes = (DD.map && DD.map[j.id]) || [];
    var ddItem = ddCodes.length ? DD_CODE[ddCodes[0]] : null;
    if (ddItem) {
      var alt = ddCodes.slice(1).map(function (c) { return DD_CODE[c]; }).filter(Boolean);
      var dp = ddDescParts(ddItem);
      var intro = dp.intro.length > 96 ? dp.intro.slice(0, 96) + '…' : dp.intro;
      s += '<div class="section"><div class="section-hd"><h2>国家职业分类里，它叫</h2></div><div class="card">' +
        '<a href="#/dadian/' + ddItem.c + '" style="display:block;color:inherit;text-decoration:none">' +
        '<b style="font-size:15.5px">' + esc(ddItem.n) + (ddItem.tag ? ' <span class="ddtag' + (ddItem.tag.charAt(0) === 'L' ? ' l' : '') + '">' + ddItem.tag + '</span>' : '') + '</b>' +
        '<div class="tiny muted" style="margin-top:3px">' + ddItem.c + ' · ' + esc(ddItem.big) + ' › ' + esc(ddItem.small) + (DD_AUTO[j.id] ? ' · 自动匹配' : '') + '</div>' +
        '<p class="desc" style="margin-top:8px;font-size:13.5px">' + esc(intro) + '</p>' +
        '<span class="chip sm" style="margin-top:10px">查看大典原文 ›</span>' +
        '</a>' +
        (alt.length ? '<div class="tiny muted" style="margin-top:10px">相近分类：' +
          alt.map(function (a) { return esc(a.n) + '（' + a.c + '）'; }).join('、') + '</div>' : '') +
        '</div></div>';
    }

    s += '<div class="section" style="padding-bottom:10px"><div class="btn-row">' +
      '<button class="btn ghost" data-act="fav" data-id="' + id + '">' + (starred ? '★ 已收藏' : '☆ 收藏这个岗位') + '</button>' +
      '<button class="btn" data-act="back">返回</button></div></div>';
    s += '</div>';
    return s;
  }

  /* ---------------- 视图：岗位库 ---------------- */
  function viewJobs() {
    var list = JOBS.filter(function (j) {
      if (state.track === '全部') return true;
      if (state.track === '收藏') return favs.indexOf(j.id) >= 0;
      return j.track === state.track;
    });
    var s = '<div class="screen">';
    s += topbar('岗位库', '<span class="tiny muted">' + JOBS.length + ' 个</span>', false);
    s += '<div class="chips" style="margin-top:4px;flex-wrap:nowrap;overflow-x:auto;padding-bottom:6px">';
    ['全部', '收藏'].concat(TRACKS).forEach(function (t) {
      var on = state.track === t ? ' on' : '';
      var label = t === '全部' ? '全部' : (t === '收藏' ? '★ 收藏' : (TRACK_ICON[t] || '') + ' ' + t);
      s += '<button class="chip sm' + on + '" style="flex:none" data-act="track" data-t="' + esc(t) + '">' + esc(label) + '</button>';
    });
    s += '</div>';

    if (!list.length) {
      s += '<div class="empty">' + (state.track === '收藏' ? '还没收藏岗位。进岗位详情点右上角的 ☆。' : '这个方向暂时没有岗位。') + '</div>';
    }

    var shown = list.slice(0, state.jobsLimit || 60);
    shown.forEach(function (j) {
      var p = profile ? scoreJob(j, profile) : null;
      s += '<a class="jobcard" href="#/job/' + j.id + '">' +
        '<div class="top"><div style="flex:1;min-width:0">' +
        '<h3>' + esc(j.name) + '</h3>' +
        '<div class="track">' + (TRACK_ICON[j.track] || '') + ' ' + esc(j.track) +
        ' · 应届友好度 ' + esc(j.friendly) + '</div></div>' +
        (p ? ring(pct(p.coverage)) : '') + '</div>' +
        '<div class="tl">' + esc(j.tagline) + '</div>' +
        '<div class="foot">' + (j.salary ? '<span class="chip tag">入门 ' + kRange(j.salary.junior) + '</span>' : '') +
        '<span class="chip tag">' + (j.skills || []).length + ' 项技能</span></div></a>';
    });
    if (list.length > shown.length) {
      s += '<button class="btn ghost" style="margin-top:12px" data-act="jobsmore">再看 60 个（还有 ' + (list.length - shown.length) + ' 个）</button>';
    }
    s += '</div>';
    return s;
  }

  /* ---------------- 视图：搜索 ---------------- */
  function viewSearch() {
    var s = '<div class="screen">';
    s += topbar('搜一搜', '', false);
    s += '<div class="seg two" style="margin-top:2px">' +
      '<button class="' + (state.mode === 'job' ? 'on' : '') + '" data-act="mode" data-m="job">搜岗位关键字</button>' +
      '<button class="' + (state.mode === 'jd' ? 'on' : '') + '" data-act="mode" data-m="jd">贴一段招聘要求</button>' +
      '</div>';

    s += '<div class="searchbar"><div class="searchwrap"><span class="mag">⌕</span>' +
      (state.mode === 'jd'
        ? '<textarea class="input" id="q" data-field="q" placeholder="把 JD / 招聘要求整段粘进来，我告诉你它像哪个岗位">' + esc(state.q) + '</textarea>'
        : '<input class="input" id="q" data-field="q" placeholder="岗位名、技能，比如「会计 证书」" value="' + esc(state.q) + '" autocomplete="off">') +
      '</div></div>';

    s += '<div id="hits" style="margin-top:16px"></div>';
    s += '</div>';
    return s;
  }

  function renderHits() {
    var box = document.getElementById('hits');
    if (!box) return;
    var q = state.q.trim();
    if (!q) {
      var hot = SKILLS.slice(0, 0);
      box.innerHTML = '<div class="card"><b style="font-size:14px">可以这样搜</b>' +
        '<div class="chips" style="margin-top:10px">' +
        ['会计', '新媒体', 'Java', '护士', '教师资格证', '数据分析', '出差', '不加班', '稳定', '应届生']
          .map(function (x) { return '<button class="chip sm" data-act="quick" data-q="' + esc(x) + '">' + esc(x) + '</button>'; }).join('') +
        '</div><p class="tiny muted" style="margin-top:10px">搜的是 60 个岗位的真实描述、技能要求和学习路线，不是招聘广告。</p></div>';
      return;
    }
    var res = searchDocs(q, 12);
    if (!res.length) {
      box.innerHTML = '<div class="empty">没搜到「' + esc(q) + '」。<br>换个说法试试，比如只搜「会计」「剪辑」「护士」。</div>';
      return;
    }
    var html = '<div class="card">';
    if (state.mode === 'jd') {
      var hitSkills = [];
      SKILLS.forEach(function (sk) {
        if (q.indexOf(sk.name) >= 0) hitSkills.push(sk.name);
      });
      html += '<p class="tiny muted">这段描述里认出了 ' + (hitSkills.length ? hitSkills.slice(0, 8).join('、') : '少量') +
        ' 相关技能。下面按相似度排：</p><div class="hr"></div>';
    }
    res.forEach(function (r) {
      var sn = snippet(r.job, q);
      html += '<a class="hit" href="#/job/' + r.job.id + '" style="display:block;color:inherit;text-decoration:none">' +
        '<h4>' + highlight(r.job.name, q) + ' <span class="tiny muted">· ' + esc(r.job.track) + '</span></h4>' +
        '<div class="snip"><span class="tiny muted">[' + sn.label + ']</span> ' + sn.html + '</div>' +
        '<div class="meta">' + (r.job.salary ? '入门 ' + kRange(r.job.salary.junior) + ' · ' : '') +
        '应届友好度 ' + esc(r.job.friendly) + '</div></a>';
    });
    html += '</div>';

    // 顺带在职业大典里找同名的国家分类
    var ddHits = DD.list.filter(function (x) { return x.n.indexOf(q) >= 0; }).slice(0, 5);
    if (ddHits.length) {
      html += '<div class="card" style="margin-top:12px"><div class="tiny muted" style="margin-bottom:4px">职业大典里还有这些：</div>' +
        ddHits.map(ddRow).join('') + '</div>';
    }
    box.innerHTML = html;
  }  /* ---------------- 视图：职业大典 ---------------- */
  var CAT_SHORT = { '1': '机关企事业负责人', '2': '专业技术', '3': '办事人员', '4': '服务人员', '5': '农林牧渔', '6': '生产制造', '7': '军队人员', '8': '其他' };

  function dadianFilter() {
    var q = (state.dq || '').trim();
    var cat = state.dcat || '全部';
    return DD.list.filter(function (x) {
      if (cat !== '全部' && x.c.split('-')[0] !== cat) return false;
      if (!q) return true;
      return (x.n + ' ' + x.d + ' ' + (x.w || []).join(' ')).indexOf(q) >= 0;
    });
  }

  function ddRow(x) {
    var tag = x.tag ? '<span class="ddtag' + (x.tag.charAt(0) === 'L' ? ' l' : '') + '">' + x.tag + '</span>' : '';
    return '<a class="ddrow" href="#/dadian/' + x.c + '">' +
      '<div class="body"><b>' + esc(x.n) + tag + '</b>' +
      '<div class="meta">' + x.c + ' · ' + esc(x.small || x.big) + '</div></div>' +
      '<span class="arw">›</span></a>';
  }

  function viewDadian() {
    var q = (state.dq || '').trim();
    var browsing = !q && state.dcat === '全部';
    var s = '<div class="screen">';
    s += topbar('职业大典', '<span class="tiny muted">' + DD_TOTAL + ' 个职业</span>', false);
    s += '<p class="lead" style="margin-top:2px;font-size:13.5px">《中华人民共和国职业分类大典（2022 年版）》收录的国家标准职业。' +
      '很多你听过、却不确定算不算「正经职业」的岗位，都能在这里查到官方定义和具体工作任务。</p>';
    s += '<div class="searchbar"><div class="searchwrap"><span class="mag">⌕</span>' +
      '<input class="input" id="dq" data-field="dq" placeholder="搜职业名，比如「电工」「药师」「剪辑」" value="' + esc(state.dq) + '" autocomplete="off"></div></div>';

    if (browsing) {
      s += '<div class="catgrid">' + DD.cats.map(function (c) {
        return '<button class="catcard" data-act="dcat" data-c="' + c.code + '">' +
          '<b>' + esc(CAT_SHORT[c.code] || c.name) + '</b>' +
          '<span>' + esc(c.name) + '</span>' +
          '<em>' + c.count + ' 个职业</em></button>';
      }).join('') + '</div>';
      s += '<p class="tiny muted" style="margin-top:14px">也可以直接在上面搜：' +
        '“电工”“药师”“剪辑”“快递”“面点师”——大典里连这些都有官方定义。</p>';
    } else {
      s += '<div style="display:flex;align-items:center;gap:8px;margin-top:12px">' +
        '<button class="chip sm" data-act="dcat" data-c="全部">‹ 全部分类</button>' +
        '<span class="tiny muted">' + (q ? '搜索「' + esc(q) + '」' : '') + '</span></div>';
      s += '<div id="ddlist"></div>';
    }

    s += '<p class="tiny muted" style="margin-top:14px">S = 数字职业，L = 绿色职业（大典 2022 版标注）。数据整理自人社部公开文本。</p>';
    s += '</div>';
    return s;
  }

  function renderDadianList() {
    var box = document.getElementById('ddlist');
    if (!box) return;
    var list = dadianFilter();
    var h = '<div class="total">' + (state.dq ? '找到 ' + list.length + ' 个' : '共 ' + list.length + ' 个') + '</div>';
    h += '<div class="card" style="padding:2px 14px">';
    if (!list.length) h += '<div class="empty">没搜到。换个短一点的词试试，比如只搜「师」或「工」。</div>';
    list.slice(0, state.ddLimit).forEach(function (x) { h += ddRow(x); });
    h += '</div>';
    if (list.length > state.ddLimit) {
      h += '<button class="btn ghost" style="margin-top:12px" data-act="ddmore">再看 40 个（还有 ' +
        (list.length - state.ddLimit) + ' 个）</button>';
    }
    box.innerHTML = h;
  }

  function ddDescParts(x) {
    var d = x.d || '';
    var cut = d.indexOf('本职业包含但不限于下列工种');
    if (cut > 0) d = d.slice(0, cut);
    var i = d.indexOf('主要工作任务');
    var intro = i >= 0 ? d.slice(0, i) : d;
    var rest = i >= 0 ? d.slice(i).replace(/^主要工作任务[:：]?/, '') : '';
    var tasks = rest ? rest.split(/\s*\d+\s*[.．]\s*/).filter(function (t) { return t.replace(/[；;。\s]/g, '').length; }) : [];
    tasks = tasks.map(function (t) { return t.replace(/^[；;\s]+/, '').replace(/[；;。\s]+$/, ''); });
    return { intro: intro.replace(/[。\s]+$/, '。'), tasks: tasks };
  }

  function viewDadianItem(code) {
    var x = DD_CODE[code];
    if (!x) { go('#/dadian'); return ''; }
    var parts = ddDescParts(x);
    var s = '<div class="screen">' + topbar('职业详情', '', true);

    s += '<div class="detail-hero">' +
      '<div class="track">' + esc(x.c) + (x.tag ? ' · ' + esc(x.tag) : '') + '</div>' +
      '<h1>' + esc(x.n) + '</h1>' +
      '<div class="crumb">' + esc(x.big) + ' › ' + esc(x.mid) + ' › ' + esc(x.small) + '</div>' +
      '</div>';

    s += '<div class="section"><div class="section-hd"><h2>官方定义</h2></div><div class="card">' +
      '<p class="desc">' + esc(parts.intro) + '</p></div></div>';

    if (parts.tasks.length) {
      s += '<div class="section"><div class="section-hd"><h2>主要工作任务</h2>' +
        '<span class="sub">' + parts.tasks.length + ' 条</span></div><div class="card"><ul class="plain tasks">' +
        parts.tasks.map(function (t) { return '<li>' + esc(t) + '</li>'; }).join('') + '</ul></div></div>';
    }

    if (x.w && x.w.length) {
      s += '<div class="section"><div class="section-hd"><h2>包含的工种</h2></div><div class="chips">' +
        x.w.map(function (w) { return '<span class="chip tag">' + esc(w) + '</span>'; }).join('') + '</div></div>';
    }

    var jobs = (DD_JOBS[code] || []).map(function (id) { return JOB[id]; }).filter(Boolean);
    if (jobs.length) {
      s += '<div class="section"><div class="section-hd"><h2>在本应用里对应的岗位</h2></div>';
      jobs.forEach(function (j) {
        var p = profile ? scoreJob(j, profile) : null;
        s += '<a class="jobcard" href="#/job/' + j.id + '">' +
          '<div class="top"><div style="flex:1;min-width:0">' +
          '<h3>' + esc(j.name) + '</h3>' +
          '<div class="track">' + (TRACK_ICON[j.track] || '') + ' ' + esc(j.track) + '</div></div>' +
          (p ? ring(pct(p.coverage)) : '') + '</div>' +
          '<div class="tl">' + esc(j.tagline) + '</div></a>';
      });
      s += '</div>';
    }

    s += '<div class="section"><div class="card"><p class="tiny muted">' +
      '以上定义与工作任务来自《中华人民共和国职业分类大典（2022 年版）》，原文由人社部组织编制。' +
      '大典是职业分类的「标准答案」，但它不告诉你薪资、门槛和怎么入门——那些看岗位详情页。</p></div></div>';
    s += '</div>';
    return s;
  }

  /* ---------------- 视图：关于 ---------------- */
  function viewAbout() {
    return '<div class="screen">' + topbar('关于这个应用', '', true) +
      '<div class="card" style="margin-top:4px"><b>它是什么</b><p class="lead" style="margin-top:6px">' +
      '一个反向的求职工具：不问你「想做什么」，先看你会什么，再告诉你世界上有哪些岗位和你对得上。</p></div>' +
      '<div class="card"><b>数据从哪来</b><p class="lead" style="margin-top:6px">' +
      JOBS.length + ' 个岗位、' + SKILLS.length + ' 项技能，是按公开的招聘要求、行业讨论和从业者描述整理的。' +
      '薪资是参考区间，不是统计年鉴上的数字；同一岗位在不同城市、不同规模的公司差别很大。</p></div>' +
      '<div class="card"><b>职业大典</b><p class="lead" style="margin-top:6px">' +
      '「职业大典」页的 ' + DD_TOTAL + ' 个职业，来自《中华人民共和国职业分类大典（2022 年版）》社会公示稿（人社部编制）的公开整理版。' +
      '它给的是国家标准的职业定义和主要工作任务，不含薪资与门槛。岗位与它之间是「最接近」的对应，不是一一对应。</p></div>' +
      '<div class="card"><b>它不能做什么</b><p class="lead" style="margin-top:6px">' +
      '它不认识你，也不知道你家里的情况、你怕什么、你能忍多久。推荐只是把选项摊开，选择还得你自己做。</p></div>' +
      '<div class="card"><b>隐私</b><p class="lead" style="margin-top:6px">' +
      '所有信息只存在你这台设备的浏览器里，不上传任何服务器。断网也能用。</p></div>' +
      '</div>';
  }

  /* ---------------- 路由 ---------------- */
  function parseHash() {
    var h = (location.hash || '#/').replace(/^#/, '');
    var parts = h.split('/').filter(Boolean);
    if (!parts.length) return { view: 'home' };
    if (parts[0] === 'wizard') return { view: 'wizard', step: Math.max(0, Math.min(2, parseInt(parts[1] || '0', 10) || 0)) };
    if (parts[0] === 'rec' || parts[0] === 'result') return { view: profile ? 'result' : 'home' };
    if (parts[0] === 'job') return { view: 'job', id: parts[1] };
    if (parts[0] === 'jobs') return { view: 'jobs' };
    if (parts[0] === 'search') return { view: 'search' };
    if (parts[0] === 'dadian') return { view: parts[1] ? 'dadianitem' : 'dadian', dcode: parts[1] };
    if (parts[0] === 'about') return { view: 'about' };
    return { view: 'home' };
  }

  var lastKey = '';
  function route() {
    var r = parseHash();
    state.view = r.view;
    if (r.id) state.jobId = r.id;
    var html = '';
    if (r.view === 'home') html = viewHome();
    else if (r.view === 'wizard') html = viewWizard(r.step);
    else if (r.view === 'result') html = viewResult();
    else if (r.view === 'job') html = viewJob(r.id);
    else if (r.view === 'jobs') html = viewJobs();
    else if (r.view === 'search') html = viewSearch();
    else if (r.view === 'dadian') html = viewDadian();
    else if (r.view === 'dadianitem') html = viewDadianItem(r.dcode);
    else if (r.view === 'about') html = viewAbout();

    app.innerHTML = html + tabbar();

    var key = location.hash;
    if (key !== lastKey) { window.scrollTo(0, 0); lastKey = key; }
    if (r.view === 'search') renderHits();
    if (r.view === 'dadian') renderDadianList();
    // 进到「勾技能」这一步时，如果展开的分类在屏幕下方，把它滚到眼前
    if (r.view === 'wizard' && r.step === 1 && app.querySelector) {
      var acc = app.querySelector('.acc.open');
      if (acc && acc.getBoundingClientRect().top > (window.innerHeight || 800) * 0.55) {
        acc.scrollIntoView({ block: 'start' });
      }
    }
  }

  /* ---------------- 交互 ---------------- */
  document.addEventListener('click', function (e) {
    var t = e.target.closest('[data-go]');
    if (t) {
      var to = t.getAttribute('data-go');
      e.preventDefault();
      if (location.hash === to) route(); else go(to);
      return;
    }
    var b = e.target.closest('[data-act]');
    if (!b) return;
    var act = b.getAttribute('data-act');

    if (act === 'back') { back(); return; }

    if (act === 'set') {
      var k = b.getAttribute('data-k'), v = b.getAttribute('data-v');
      draft[k] = (k === 'hours') ? parseInt(v, 10) : v;
      save(LS.draft, draft);
      route();
      return;
    }

    if (act === 'lvl') {
      var id = b.getAttribute('data-id'), lv = parseInt(b.getAttribute('data-lv'), 10);
      draft.skills = draft.skills || {};
      if (draft.skills[id] === lv) delete draft.skills[id]; else draft.skills[id] = lv;
      save(LS.draft, draft);
      route();
      return;
    }

    if (act === 'acc') {
      var cat = b.getAttribute('data-cat');
      state.openCat = state.openCat === cat ? '' : cat;
      route();
      return;
    }

    if (act === 'infer') {
      var inf = inferSkills(draft.major);
      draft.skills = draft.skills || {};
      var added = 0;
      Object.keys(inf).forEach(function (sid) {
        if (!draft.skills[sid]) { draft.skills[sid] = 1; added++; }
      });
      save(LS.draft, draft);
      if (!added) alert('没认出这个专业，你可以手动往下勾。');
      route();
      return;
    }

    if (act === 'wizard-next') { go('#/wizard/1'); return; }

    if (act === 'finish') {
      var skills = {};
      Object.keys(draft.skills || {}).forEach(function (sid) { if (SKILL[sid]) skills[sid] = draft.skills[sid]; });
      var major = (draft.major || '').trim();
      var auto = false;
      // 一门都没勾：按专业先垫几项基础技能，至少让结果有点依据
      if (!Object.keys(skills).length && major) {
        var inf = inferSkills(major);
        Object.keys(inf).forEach(function (sid) { skills[sid] = 1; });
        auto = Object.keys(skills).length > 0;
      }
      profile = {
        edu: draft.edu, status: draft.status, major: major,
        skills: skills, mode: draft.mode, people: draft.people,
        hours: draft.hours, certs: draft.certs, auto: auto, at: Date.now()
      };
      save(LS.profile, profile);
      go('#/result');
      return;
    }

    if (act === 'fav') {
      var fid = b.getAttribute('data-id');
      var i = favs.indexOf(fid);
      if (i >= 0) favs.splice(i, 1); else favs.push(fid);
      save(LS.fav, favs);
      route();
      return;
    }

    if (act === 'track') {
      state.track = b.getAttribute('data-t');
      state.jobsLimit = 60;
      route();
      return;
    }

    if (act === 'jobsmore') {
      state.jobsLimit = (state.jobsLimit || 60) + 60;
      route();
      return;
    }

    if (act === 'dcat') {
      state.dcat = b.getAttribute('data-c');
      state.ddLimit = 40;
      route();
      return;
    }

    if (act === 'ddmore') {
      state.ddLimit += 40;
      route();
      return;
    }

    if (act === 'mode') {
      state.mode = b.getAttribute('data-m');
      state.q = '';
      route();
      return;
    }

    if (act === 'quick') {
      state.q = b.getAttribute('data-q');
      var inp = document.getElementById('q');
      if (inp) inp.value = state.q;
      renderHits();
      return;
    }
  });

  document.addEventListener('input', function (e) {
    var el = e.target;
    if (el.getAttribute('data-field') === 'major') { draft.major = el.value; save(LS.draft, draft); }
    if (el.getAttribute('data-field') === 'certs') { draft.certs = el.value; save(LS.draft, draft); }
    if (el.getAttribute('data-field') === 'q') {
      state.q = el.value;
      renderHits();
    }
    if (el.getAttribute('data-field') === 'dq') {
      var wasBrowsing = !(state.dq || '').trim() && state.dcat === '全部';
      state.dq = el.value;
      state.ddLimit = 40;
      if (wasBrowsing) {
        route();
        var input = document.getElementById('dq');
        if (input) {
          input.focus();
          try { input.setSelectionRange(input.value.length, input.value.length); } catch (err) {}
        }
      } else {
        renderDadianList();
      }
    }
  });

  window.addEventListener('hashchange', route);

  /* ---------------- 启动 ---------------- */
  if ('serviceWorker' in navigator && location.protocol.indexOf('http') === 0) {
    window.addEventListener('load', function () {
      navigator.serviceWorker.register('sw.js').catch(function () {});
    });
  }
  route();
})();
