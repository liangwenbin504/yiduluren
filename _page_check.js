
// 预加载课格规则
fetch("/api/keti_rules").then(r=>r.json()).then(d=>{window._ketiRules=d;}).catch(()=>{});

// 全局用户状态对象（供各模块读取）
window._currentUser = { mobile: '', name: '', vip_plan: '', is_vip: false, is_beta: false };

// 自动 token 验证：支持跨设备自动识别终身免费等用户身份
(function autoVerifyToken() {
  var urlParams = new URLSearchParams(window.location.search);
  var token = urlParams.get('token');
  
  // 优先使用 URL 中的 token
  if (token) {
    fetch('/api/user/verify_token?token=' + encodeURIComponent(token))
      .then(function(r) { return r.json(); })
      .then(function(j) {
        if (j && j.success) {
          // 保存用户信息到 localStorage
          localStorage.setItem('zeri_mobile', j.mobile);
          localStorage.setItem('zeri_name', j.name || '');
          localStorage.setItem('zeri_vip_plan', j.vip_plan || '');
          localStorage.setItem('zeri_auto_login', '1');
          
          // 更新全局用户状态
          window._currentUser = {
            mobile: j.mobile,
            name: j.name || '',
            vip_plan: j.vip_plan || '',
            is_vip: j.is_vip,
            is_beta: j.is_beta
          };
          
          // 清除 URL 中的 token 参数（可选，保持 URL 整洁）
          var cleanUrl = window.location.pathname;
          window.history.replaceState({}, '', cleanUrl);
          
          // 显示欢迎提示
          setTimeout(function() {
            var tip = document.createElement('div');
            tip.style.cssText = 'position:fixed;top:20px;right:20px;background:linear-gradient(135deg,#fbbf24,#f59e0b);color:#fff;padding:12px 20px;border-radius:10px;box-shadow:0 4px 20px rgba(245,158,11,0.4);z-index:9999;font-weight:600;max-width:280px;animation:slideIn 0.3s ease;';
            tip.innerHTML = '🎉 欢迎 <b>' + j.name + '</b>！<br><span style="font-size:12px;opacity:0.9;">' + (j.vip_plan || '用户') + '权益已激活</span>';
            document.body.appendChild(tip);
            setTimeout(function() { tip.style.opacity = '0'; tip.style.transition = 'opacity 0.3s'; }, 3000);
            setTimeout(function() { tip.remove(); }, 3500);
          }, 500);
          
          // 触发用户中心刷新（如果已打开）
          if (typeof ucLoadStatus === 'function') {
            setTimeout(function() { ucLoadStatus(); }, 800);
          }
          // 触发择日页面刷新权益状态
          if (typeof initZeri === 'function') {
            setTimeout(function() { 
              var tabs = document.querySelectorAll('.tab-btn');
              tabs.forEach(function(t) {
                if (t.dataset.tab === 'zeri-learn' && t.classList.contains('active')) {
                  initZeri();
                }
              });
            }, 1000);
          }
        }
      })
      .catch(function() {});
  } else {
    // 其次检查 localStorage 中是否有保存的 token
    var savedMobile = localStorage.getItem('zeri_mobile');
    var savedVipPlan = localStorage.getItem('zeri_vip_plan');
    
    // 如果已保存用户信息，自动验证一次确保权益有效
    if (savedMobile) {
      // 更新全局状态
      window._currentUser.mobile = savedMobile;
      window._currentUser.name = localStorage.getItem('zeri_name') || '';
      window._currentUser.vip_plan = savedVipPlan || '';
      
      fetch('/api/user/info', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ mobile: savedMobile })
      })
      .then(function(r) { return r.json(); })
      .then(function(j) {
        if (j && j.is_vip) {
          // 更新本地存储的权益信息
          localStorage.setItem('zeri_vip_plan', j.vip_plan);
          window._currentUser.vip_plan = j.vip_plan;
          window._currentUser.is_vip = true;
          window._currentUser.is_beta = j.is_beta;
        } else {
          // 权益已失效，清除本地信息
          localStorage.removeItem('zeri_mobile');
          localStorage.removeItem('zeri_name');
          localStorage.removeItem('zeri_vip_plan');
          window._currentUser = { mobile: '', name: '', vip_plan: '', is_vip: false, is_beta: false };
        }
      })
      .catch(function() {});
    }
  }
})();

const API = '';

// 【2026-08-02 梳理】账户功能 tab（持仓监控/绩效统计）跟随顶栏虚拟账户子系统。
// 在 tab 按钮上显示当前子系统小字角标；交易记录为全子系统合并流水，不加角标（2026-08 审查对齐）。
// 子系统全局状态统一使用 g_subsystem（L~3623 声明，switchGlobalSubsystem 维护）。
function syncAccountTabBadge() {
  const label = (g_subsystem === 'liuren') ? '🔮六壬' : '📈量化';
  const color = (g_subsystem === 'liuren') ? '#7c3aed' : '#16a34a';
  ['positions','perf'].forEach(function(tid){
    const b = document.querySelector('.tab-btn[data-tab="' + tid + '"]');
    if (!b) return;
    b.innerHTML = b.innerHTML.replace(/<small class="subsys-tag"[^>]*>.*?<\/small>/g, '');
    b.insertAdjacentHTML('beforeend', '<small class="subsys-tag" style="font-size:9px;color:'+color+';margin-left:3px;font-weight:600;">'+label+'</small>');
  });
}

// ====== Tab 切换（含模式感知） ======
var _uiMode = 'zeri'; // 'zeri' | 'trading'
var _ZERI_TABS = ['zeri-learn','ai-learn','user-center'];

function switchUCTab(name) {
  document.querySelectorAll('.uctab-btn').forEach(b => b.classList.toggle('active', b.dataset.uctab === name));
  document.querySelectorAll('.uc-content').forEach(c => c.classList.toggle('active', c.id === 'uc-' + name));
  if (name === 'status') ucLoadStatus();
  if (name === 'scan') ucLoadScan();
  if (name === 'member') ucLoadMember();
}

function switchTab(tabId) {
  document.querySelectorAll('.tab-btn').forEach(b => b.classList.toggle('active', b.dataset.tab === tabId));
  document.querySelectorAll('.tab-content').forEach(c => c.classList.toggle('active', c.id === 'tab-' + tabId));
  syncAccountTabBadge();

  /* 模式自动切换：点交易类 tab → 切到交易模式；点择日类 tab → 切回择日模式 */
  var targetMode = (_ZERI_TABS.indexOf(tabId) >= 0) ? 'zeri' : 'trading';
  if (targetMode !== _uiMode) { _uiMode = targetMode; applyUIMode(); }

  if (tabId === 'zeri-learn') { loadTrainingStatus(); }
  if (tabId === 'ai-learn') { loadAILEarnData(); }
  if (tabId === 'user-center') { loadUserCenter(); }
  
  if (tabId === 'screener') {
    if (!window._stockKgInited) initStockKnowledge();
    Promise.all([
      _marketTiming ? Promise.resolve() : fetchMarketTiming(),
      _dualPhaseLoaded ? Promise.resolve() : fetchDualPhaseData(),
      _screenerLoaded ? Promise.resolve() : fetchScreenerData(),
      _multiStockLoaded ? Promise.resolve() : fetchMultiStockData()
    ]).then(() => {
      renderMarketTiming();
      renderDualPhaseTable();
      renderScreenerTable();
      renderMultiStockTable();
      loadReviewStatusOnTabSwitch();
    });
  }
  if (tabId === 'positions') { loadPositions(); }
  if (tabId === 'perf') { loadPerformance(); }
  window.scrollTo({top:0, behavior:'smooth'});
}

// ═════════════════════════════════════════════════════════════
// 用户中心 JS（内测/扫码按次/会员）—— 与 /api/zeri/* 、/api/user/* 、/api/member/* 对接
// ═════════════════════════════════════════════════════════════
var _ucSel = {};   // 当前选择的会员档与周期（会员tab）

function loadUserCenter() {
  // 默认切到"我的状态"
  ucLoadStatus();
  // 预热其它面板（定价表/会员卡片/收款码）
  ucLoadScan();
  ucLoadMember();
  // 从本地记住手机号
  var m = localStorage.getItem('zeri_mobile') || '';
  ['ucMobile','ucMemberMobile','ucBetaMobile'].forEach(function(id){
    var el = document.getElementById(id); if (el && !el.value) el.value = m;
  });
  var n = localStorage.getItem('zeri_name') || '';
  var e2 = document.getElementById('ucName'); if (e2 && !e2.value) e2.value = n;
}

function _post(url, body) {
  return fetch(url, {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(body||{})})
    .then(r => r.json().catch(() => ({})));
}
function _get(url) {
  return fetch(url).then(r => r.json().catch(() => ({})));
}
function _amsg(id, text, color) {
  var el = document.getElementById(id); if (!el) return;
  el.innerHTML = text || ''; if (color) el.style.color = color;
}
function ucShowContact(paid) {
  var el = document.getElementById('ucContact'); if (!el) return;
  // 仅付费会员（含激活成功后）可见，防止无关人员打扰
  el.style.display = paid ? 'block' : 'none';
}

// ═════════════════════════════════════════════════════════
// 顶部滚动公告（可关闭，localStorage 记忆）
// 内测期( _ANNOUNCE_MSG )/正式期( _ANNOUNCE_PAID )两套文案按日期自动切换；某文案置空则对应时期不显示公告
// ═════════════════════════════════════════════════════════
// 内测免费截止日 —— 与 config.BETA_WINDOW_END(2026-09-30) 保持一致；其后自动切换为收费公告
var _ANNOUNCE_BETA_END = '2026-09-30T23:59:59';
// 内测期公告（2026-09-30 前显示）
var _ANNOUNCE_MSG = '🎉 内测免费期 <b>2026-08-24 至 2026-09-30</b>，择日测算全部免费！' +
  '内测结束后恢复扫码付费（3 天内跨度仍免费），开通会员不限次数更划算，欢迎注册体验。';
// 正式收费期公告（2026-10-01 起自动切换，无需人工改）
var _ANNOUNCE_PAID = '📣 系统已正式上线：达标择日按跨度阶梯收费（3 天内免费、3~15 天 9.8 元…），' +
  '开通会员不限次数更划算；愿为您择好吉日，好运常在！🙏';
// 当前处于内测期则返回 true（按日期自动判断，收费自动生效由后端 date 逻辑把关）
function _announceInBeta() {
  return new Date().getTime() <= new Date(_ANNOUNCE_BETA_END).getTime();
}
function _initAnnounce() {
  var bar = document.getElementById('announceBar');
  if (!bar) return;
  var msg = _announceInBeta() ? _ANNOUNCE_MSG : _ANNOUNCE_PAID;
  if (!msg || msg === '') { bar.style.display = 'none'; return; }
  if (localStorage.getItem('announce_dismissed_v1') === '1') { bar.style.display = 'none'; return; }
  var tr = document.getElementById('announceTrack');
  if (tr) {
    var sp = '<span style="padding-right:80px;">' + msg + '</span>';
    tr.innerHTML = sp + sp; // 两份内容实现无缝循环滚动
    bar.style.display = 'block';
  }
}
function dismissAnnounce() {
  var bar = document.getElementById('announceBar');
  if (bar) bar.style.display = 'none';
  localStorage.setItem('announce_dismissed_v1', '1');
}

// ═════════════════════════════════════════════════════════
// "我的状态" 会员到期 / 按次解锁 实时倒计时
// ═════════════════════════════════════════════════════════
var _ucCDItems = [], _ucCDTimer = null;
function _ucStartCD() {
  if (_ucCDTimer) clearInterval(_ucCDTimer);
  _ucCDTimer = setInterval(_ucTickCD, 1000);
}
function _ucTickCD() {
  _ucCDItems.forEach(function(it){
    var el = document.getElementById(it.domId); if (!el || !it.target) return;
    var diff = it.target - Date.now();
    if (diff <= 0) { el.innerHTML = it.vip ? '已到期，请及时续费' : '已失效，请重新扫码'; return; }
    var d = Math.floor(diff/86400000), h = Math.floor(diff%86400000/3600000),
        m = Math.floor(diff%3600000/60000), s = Math.floor(diff%60000/1000);
    el.innerHTML = it.vip
      ? (d + ' 天 ' + h + ' 小时')
      : (h + ' 小时 ' + m + ' 分 ' + s + ' 秒');
  });
}

function ucLoadStatus() {
  var m = (document.getElementById('ucMobile')||{}).value || window._currentUser.mobile || localStorage.getItem('zeri_mobile') || '';
  var body = document.getElementById('ucAccBody');
  if (!body) return;
  if (!m) { body.innerHTML = '<span style="color:#999;">请输入手机号后点击"查询 / 关联"查看账户状态。</span>'; return; }
  // 自动填充到表单
  var mobileEl = document.getElementById('ucMobile');
  if (mobileEl && !mobileEl.value) mobileEl.value = m;
  var nameEl = document.getElementById('ucName');
  if (nameEl && !nameEl.value) nameEl.value = window._currentUser.name || localStorage.getItem('zeri_name') || '';
  
  _post('/api/user/info', {mobile:m}).then(function(j){
    if (!j || j.error) { body.innerHTML = '<span style="color:#b91c1c;">' + (j&&j.error||'查询失败') + '</span>'; return; }
    var h = '';
    h += '内测免费：' + (j.is_beta ? '✅ 是（本机/内测/白名单）' : '❌ 否') + '<br>';
    h += '会员：' + (j.is_vip ? ('✅ ' + j.vip_plan) : '❌ 否');
    if (j.is_vip) h += '（剩余 ' + (j.vip_left>=9999?'∞':j.vip_left) + ' 次）';
    h += '<br>';
    // 倒计时项目（每次刷新重建）
    _ucCDItems = [];
    if (j.is_vip && j.vip_expire) {
      var vt = new Date(String(j.vip_expire).replace(' ', 'T')).getTime();
      if (vt) _ucCDItems.push({domId:'ucCDVip', target:vt, vip:true});
      h += '会员到期：<b id="ucCDVip" style="color:#d97706;">…</b>（剩余倒计时）<br>';
    } else {
      h += '会员到期：—<br>';
    }
    h += '按次解锁：';
    if (j.unlocked && j.unlock_expire) {
      var ut = new Date(String(j.unlock_expire).replace(' ', 'T')).getTime();
      if (ut) _ucCDItems.push({domId:'ucCDUnlock', target:ut, vip:false});
      h += '✅ <b id="ucCDUnlock" style="color:#16a34a;">…</b>（剩余）';
    } else if (j.unlocked) {
      h += '✅ 剩余 ' + j.unlock_hours + ' 小时';
    } else {
      h += '❌ 未解锁';
    }
    h += '<br>';
    body.innerHTML = h;
    if (_ucCDItems.length) { _ucStartCD(); _ucTickCD(); } else { _ucCDItems = []; }
  });
}

function ucBindQuery() {
  var m = (document.getElementById('ucMobile')||{}).value || '';
  var n = (document.getElementById('ucName')||{}).value || '';
  if (!m) { alert('请先填写手机号'); return; }
  if (m.length !== 11 || !/^\d{11}$/.test(m)) { alert('手机号需为11位数字'); return; }
  _post('/api/user/register', {mobile:m, name:n}).then(function(j){
    localStorage.setItem('zeri_mobile', m); localStorage.setItem('zeri_name', n);
    _amsg('ucAccBody', '注册/关联成功。' + (j.is_vip?'您已是会员。':'') , '#16a34a');
    ucLoadStatus();
  });
}

function ucLoadScan() {
  _get('/api/zeri/price_table').then(function(j){
    var tb = document.getElementById('ucScanTable'); if (!tb || !j) return;
    var rows = (j.scan_tiers||[]).filter(function(t){ return t.price > 0; })
      .map(function(t){ return '<tr><td>'+t.desc+'</td><td>¥'+t.price+' /次</td></tr>'; }).join('');
    var freeRows = (j.scan_tiers||[]).filter(function(t){ return t.price === 0 && t.tier!=='60y'; })
      .map(function(t){ return '<tr><td>'+t.desc+'</td><td style="color:#16a34a;">免费</td></tr>'; }).join('');
    tb.innerHTML = freeRows + rows;
    // 免费规则
    var fl = document.getElementById('ucScanMsg');
    var extra = '<span style="color:#999;font-size:12px;">免费规则：跨度≤3天免费；另每日限免' + (j.daily_free?j.daily_free.limit:'1') + '次。</span> ';
    // 收款码
    var qr = document.getElementById('ucScanQR');
    if (qr) qr.src = '/static/pay_qr.png?t=' + Date.now();
  });
}

function ucScanUnlock() {
  var m = (document.getElementById('ucMobile')||{}).value || localStorage.getItem('zeri_mobile') || '';
  var amount = parseFloat((document.getElementById('ucScanAmount')||{}).value);
  var tx = (document.getElementById('ucScanTx')||{}).value || '';
  if (!amount || isNaN(amount)) { alert('请输入付款金额'); return; }
  _post('/api/zeri/unlock', {mobile:m, amount:amount, tx_no:tx, tier:''}).then(function(j){
    if (j.success) _amsg('ucScanMsg','✅ ' + j.message, '#16a34a');
    else _amsg('ucScanMsg','❌ ' + (j.error||'解锁失败，请核对金额是否匹配档位'), '#b91c1c');
  });
}

function ucLoadMember() {
  _get('/api/member/plans').then(function(j){
    var box = document.getElementById('ucMemberPlans'); if (!box || !j) return;
    var names = {vip48:'会员·体验档', vip98:'会员·尊享档'};
    var notes = {vip48:'每月5次 + 限1年跨度', vip98:'不限次数 + 不限跨度'};
    var html = '';
    ['vip98','vip48'].forEach(function(plan){
      var p = j.plans[plan]||{}; 
      html += '<div style="border:1px solid '+(plan==='vip98'?'#d97706':'#e5e7eb')+';border-radius:10px;padding:14px;'+(plan==='vip98'?'background:#fffbeb;':'')+'">'
        + '<div style="font-weight:600;font-size:15px;">'+(names[plan]||plan)+'</div>'
        + '<div style="font-size:12px;color:#888;margin:4px 0 8px;">'+(notes[plan]||'')+'</div>'
        + '<div style="font-size:13px;color:#333;line-height:1.8;">'
        + '月 ¥'+(p.m||'-')+' ｜ 季 ¥'+(p.q||'-')+' ｜ 年 ¥'+(p.y||'-')
        + '</div>'
        + '<div style="margin-top:8px;display:flex;gap:4px;">'
        + ['m','q','y'].map(function(per){ return '<button onclick="ucSelMember(\''+plan+'\',\''+per+'\')" id="sel_'+plan+'_'+per+'" data-a="'+plan+'_'+per+'" style="flex:1;padding:6px;border:1px solid #ddd;border-radius:6px;background:#fff;cursor:pointer;font-size:12px;">'+per+'</button>'; }).join('')
        + '</div></div>';
    });
    box.innerHTML = html;
    if (_ucSel.plan && _ucSel.period) ucSelMember(_ucSel.plan, _ucSel.period);
  });
  // 已是付费会员 → 展示会员专属客服通道
  var m = (document.getElementById('ucMemberMobile')||{}).value || localStorage.getItem('zeri_mobile') || '';
  if (m) _post('/api/user/info', {mobile:m}).then(function(j){ ucShowContact(j && j.is_vip); });
  else ucShowContact(false);
}

function ucSelMember(plan, per) {
  _ucSel.plan = plan; _ucSel.period = per;
  document.querySelectorAll('#ucMemberPlans [data-a]').forEach(function(b){
    var on = b.getAttribute('data-a') === (plan+'_'+per);
    b.style.background = on ? (plan==='vip98'?'#d97706':'#7c3aed') : '#fff';
    b.style.color = on ? '#fff' : '#333';
    b.style.borderColor = on ? 'transparent' : '#ddd';
  });
}

function ucMemberBuy() {
  var m = (document.getElementById('ucMemberMobile')||{}).value || localStorage.getItem('zeri_mobile') || '';
  if (!_ucSel.plan || !_ucSel.period) { alert('请先选择会员档位与周期'); return; }
  if (m.length !== 11 || !/^\d{11}$/.test(m)) { alert('请填写正确的11位手机号作为购买凭证'); return; }
  localStorage.setItem('zeri_mobile', m);
  var planName = _ucSel.plan==='vip98' ? '尊享档' : '体验档';
  var periodName = {m:'月',q:'季',y:'年'}[_ucSel.period];
  if (!confirm('确认提交：会员·' + planName + '（' + periodName + '）？付款后由系统管理员人工核对到账并开通。')) return;
  _post('/api/member/activate', {mobile:m, plan:_ucSel.plan, period:_ucSel.period, tx_no:''}).then(function(j){
    if (j.success) { _amsg('ucMemberMsg', '✅ ' + j.message, '#92400e'); ucShowContact(true); }
    else _amsg('ucMemberMsg', '❌ ' + (j.error||'开通失败'), '#b91c1c');
  });
}

function ucBetaVerify() {
  var m = (document.getElementById('ucBetaMobile')||{}).value || '';
  var n = (document.getElementById('ucBetaName')||{}).value || '';
  var c = (document.getElementById('ucBetaCode')||{}).value || '';
  if (!m || !n) { alert('请填写手机号和姓名'); return; }
  if (m.length !== 11 || !/^\d{11}$/.test(m)) { alert('手机号需为11位数字'); return; }
  _post('/api/user/verify', {mobile:m, name:n, code:c}).then(function(j){
    if (j.success) { localStorage.setItem('zeri_mobile', m); localStorage.setItem('zeri_name', n); _amsg('ucBetaMsg','✅ '+j.message,'#115e59'); }
    else _amsg('ucBetaMsg','❌ '+(j.error||'验证未通过'),'#b91c1c');
  });
}

function switchSubtab(name) {
  document.querySelectorAll('.subtab-btn').forEach(b => b.classList.toggle('active', b.dataset.subtab === name));
  document.querySelectorAll('.sub-content').forEach(c => c.classList.toggle('active', c.id === 'sub-' + name));
  if (name === 'quant') loadQuantPrediction();
  if (name === 'liuren20d') loadLiuren20dPrediction();
  if (name === 'compare') loadCompareData();
}
function switchSubtab2(name) {
  document.querySelectorAll('.subtab-btn2').forEach(b => b.classList.toggle('active', b.dataset.subtab2 === name));
  document.querySelectorAll('.sub-content2').forEach(c => c.classList.toggle('active', c.id === 'sub2-' + name));
  if (name === 'zeri') { initPlSelects(); }
  if (name === 'ai') { loadKnowledgeCases(); }
}
function openAdvancedZeri(){
  _uiMode = 'zeri';
  applyUIMode();
  switchTab('zeri-learn');
  switchSubtab2('zeri');
}
function openTradingMode(){
  _uiMode = 'trading';
  applyUIMode();
  switchTab('overview');
}
function toggleVtStrip(){
  var b=document.getElementById('vtBody');
  var c=document.querySelector('#vtToggle .vt-caret');
  if(b.style.display==='none'){ b.style.display='block'; if(c)c.style.transform='rotate(90deg)'; }
  else { b.style.display='none'; if(c)c.style.transform='rotate(0deg)'; }
}

// ====== 模式感知 UI：applyUIMode / backToZeri ======
function applyUIMode() {
  var tradingGroup = document.getElementById('tradingGroup');
  var btnTrading = document.getElementById('btnTrading');
  if (_uiMode === 'trading') {
    document.body.classList.add('ui-trading');
    document.getElementById('btnBackZeri').style.display = '';
    if (btnTrading) btnTrading.style.display = 'none';
    if (tradingGroup) tradingGroup.style.display = 'inline-flex';
  } else {
    document.body.classList.remove('ui-trading');
    document.getElementById('btnBackZeri').style.display = 'none';
    if (btnTrading) btnTrading.style.display = '';
    if (tradingGroup) tradingGroup.style.display = 'none';
  }
}
function backToZeri() { openAdvancedZeri(); }

// ═════════ 批量择日（迁移自原始「仪度六壬择日」系统） ═════════

// ── 2026-08-25 禄马贵人条件择日：权益梯度（免费/内测1组·体验2组·尊享6组）──
var PL_LMG_MAX_JS = 1;
function plLmgToggle() {
  var on = document.getElementById('plLmgToggle').checked;
  document.getElementById('plLmgBody').style.display = on ? 'block' : 'none';
  if (on) {
    var m = localStorage.getItem('zeri_mobile') || '';
    if (m) _post('/api/user/info', {mobile: m}).then(function(j){
      if (j && j.vip_plan === '尊享档') { PL_LMG_MAX_JS = 6; document.getElementById('plLmgFree') && (document.getElementById('plLmgFree').style.display = 'none'); }
      else if (j && j.vip_plan === '终身免费') { PL_LMG_MAX_JS = 6; document.getElementById('plLmgFree') && (document.getElementById('plLmgFree').style.display = 'none'); }
      else if (j && j.vip_plan === '体验档') { PL_LMG_MAX_JS = 2; document.getElementById('plLmgFree') && (document.getElementById('plLmgFree').style.display = 'none'); }
      else { PL_LMG_MAX_JS = 1; document.getElementById('plLmgFree') && (document.getElementById('plLmgFree').style.display = 'block'); }
    }).catch(function(){ PL_LMG_MAX_JS = 1; document.getElementById('plLmgFree') && (document.getElementById('plLmgFree').style.display = 'block'); });
  }
}
function plLmgGroups() {
  return Array.prototype.slice.call(document.querySelectorAll('.plLmgG:checked')).map(function(cb){ return cb.value; });
}
// ② 智能推荐（免费·内测免选组）：设置 auto 标志，交由后端按求事方向挑最优一课/最优组
var PL_LMG_AUTO = 0;
// ③ 超选预览钩子：勾选超权益时不硬拦截，标记预览（后端放行算分+横幅提示升级）
var PL_LMG_OVERSEE = 0;
function plLmgAuto() {
  PL_LMG_AUTO = 1;
  var errEl = document.getElementById('plError');
  if (document.getElementById('plLmgQiushi') && !document.getElementById('plLmgQiushi').value) {
    errEl.textContent = '🎯 请先在上方选择"求事方向"（求官/求财/求动），再点系统推荐。';
    errEl.classList.add('show'); setTimeout(function(){ errEl.classList.remove('show'); }, 4000);
    return;
  }
  plBatchZeri();
}
(function(){
  document.querySelectorAll('.plLmgG').forEach(function(cb){
    cb.addEventListener('change', function(){
      var n = plLmgGroups().length;
      var errEl = document.getElementById('plError');
      if (n > PL_LMG_MAX_JS) {
        // ③ 超选预览钩子：允许保留超额勾选，标记预览（后端放行算分+横幅提示升级）
        PL_LMG_OVERSEE = 1;
        errEl.textContent = '👁 已选 ' + n + ' 组（当前权益仅 ' + PL_LMG_MAX_JS + ' 组）：本组将按"超选预览"算分，结果仅供体验，升级会员可持久使用。';
        errEl.classList.add('show');
        setTimeout(function(){ errEl.classList.remove('show'); }, 5000);
      } else if (n >= 1) {
        PL_LMG_OVERSEE = 0;
      }
    });
  });
})();
var PL_SHAN = ['壬','子','癸','丑','艮','寅','甲','卯','乙','辰','巽','巳','丙','午','丁','未','坤','申','庚','酉','辛','戌','乾','亥'];
var PL_XIANG = {'壬':'丙','子':'午','癸':'丁','丑':'未','艮':'坤','寅':'申','甲':'庚','卯':'酉','乙':'辛','辰':'戌','巽':'乾','巳':'亥','丙':'壬','午':'子','丁':'癸','未':'丑','坤':'艮','申':'寅','庚':'甲','酉':'卯','辛':'乙','戌':'辰','乾':'巽','亥':'巳'};
var PL_DIZHI = ['子','丑','寅','卯','辰','巳','午','未','申','酉','戌','亥'];
var PL_GANZHI60 = (function(){ var g='甲乙丙丁戊己庚辛壬癸', z='子丑寅卯辰巳午未申酉戌亥', r=[]; for(var i=0;i<60;i++){ r.push(g[i%10]+z[i%12]); } return r; })();
var _plInited = false;
var _plResults = null;
var _plDetailData = null; // 当前点开的单课详情（供「导出文书」套用完美模板）

function _fillSelect(id, arr, firstLabel) {
  var el = document.getElementById(id); if (!el) return;
  var html = '';
  if (firstLabel) html += '<option value="">' + firstLabel + '</option>';
  arr.forEach(function(v){ html += '<option value="' + v + '">' + v + '</option>'; });
  el.innerHTML = html;
}
// ═══ 合并后：指定/批量 共用配置卡 同步 + 模式切换 ═══
// 共享配置卡（择日类型/坐山/来龙/经度）→ 同步到 单课(zeri*) 与 批量(pl*) 两套隐藏 selects，并联动两模式的字段显隐
function syncZeriShared() {
  var t = document.getElementById('zType') ? document.getElementById('zType').value : '';
  var m = document.getElementById('zMountain') ? document.getElementById('zMountain').value : '';
  var l = document.getElementById('zLailong') ? document.getElementById('zLailong').value : '';
  var lon = document.getElementById('zLongitude') ? document.getElementById('zLongitude').value : '105.4';
  if (document.getElementById('plType')) document.getElementById('plType').value = t;
  if (document.getElementById('plMountain')) document.getElementById('plMountain').value = m;
  if (document.getElementById('plLailong')) document.getElementById('plLailong').value = l;
  if (document.getElementById('plLongitude')) document.getElementById('plLongitude').value = lon;
  // 向山显示（共享卡 + 批量隐藏卡 同步）
  if (document.getElementById('zXiang')) document.getElementById('zXiang').textContent = (m && PL_XIANG[m]) ? PL_XIANG[m] : '--';
  if (document.getElementById('plXiangshan')) document.getElementById('plXiangshan').textContent = (m && PL_XIANG[m]) ? PL_XIANG[m] : '--';
  // 共享来龙行显隐（仅阴宅类需要）
  var isYin = (ZERI_YINZHAI.indexOf(t) >= 0);
  if (document.getElementById('zLailongRow')) document.getElementById('zLailongRow').style.display = isYin ? 'block' : 'none';
  // 类型说明（共享卡底部提示两模式通用）
  // 触发批量模式的字段联动（本命/年命/目标/文书 等行显隐）
  if (typeof plOnTypeChange === 'function') plOnTypeChange();
}

function initPlSelects() {
  if (_plInited) return; _plInited = true;
  _fillSelect('plMountain', PL_SHAN, '请选择坐山');
  _fillSelect('plLailong', PL_SHAN, '请选择来龙（二十四山）');
  _fillSelect('plNanNianming', PL_GANZHI60, '请选择男年命');
  _fillSelect('plNvNianming', PL_GANZHI60, '请选择女年命');
  _fillSelect('plBenMing', PL_GANZHI60, '未指定（可选）');
  _fillSelect('plXianming', PL_DIZHI, '未指定（可选）');
  _fillSelect('plFuzhuBenMing', PL_DIZHI, '未指定（可选）');
  document.getElementById('plMountain').addEventListener('change', function(){
    var s = this.value;
    document.getElementById('plXiangshan').textContent = (s && PL_XIANG[s]) ? PL_XIANG[s] : '--';
  });
  plOnTypeChange();
  syncZeriShared();
}
// 亡盗·寻物速断（2026-09-06 独立入口）：输入物件 → /api/lost/find 自动起课 → 类神吉应
function zeriLostFind() {
  var item = (document.getElementById('lostItem').value || '').trim();
  if (!item) { alert('请先输入丢失的物件名'); document.getElementById('lostItem').focus(); return; }
  var box = document.getElementById('lostResult');
  box.innerHTML = '<span style="color:#9fb3d1;">起课占断中…（按当前时辰自动起课）</span>';
  fetch('/api/lost/find?item=' + encodeURIComponent(item))
    .then(function (r) { return r.json(); })
    .then(function (d) {
      if (d.error) { box.innerHTML = '<span style="color:#fca5a5;">' + d.error + '</span>'; return; }
      var cls = d.end === '吉' ? '#7ee2b8' : (d.end === '凶' ? '#fca5a5' : '#fbbf24');
      var tag = d.end === '吉' ? '✅ 可寻' : (d.end === '凶' ? '❌ 难寻' : '➖ 待寻');
      var sc = (d.sanchuan || {});
      box.innerHTML =
        '<div style="display:flex;gap:12px;align-items:center;flex-wrap:wrap;">' +
        '<span style="color:' + cls + ';font-weight:600;font-size:15px;">' + tag + '</span>' +
        '<span>类神：<b>' + d.leishen + '</b></span>' +
        '<span style="color:#9fb3d1;">课体：' + (d.keti || '—') + '</span>' +
        '<span style="color:#9fb3d1;">三传：' + sc.初传 + ' ' + sc.中传 + ' ' + sc.末传 + '</span></div>' +
        '<div style="margin-top:4px;">' + d.narr + '</div>' +
        '<div style="font-size:11px;color:#8fa3c8;margin-top:4px;">' + d.sizhu + ' ｜ ' + d.date + ' ' + d.shichen + '时</div>' +
        '<div style="font-size:11px;color:#8fa3c8;">出处：' + d.src + '</div>';
    })
    .catch(function (e) { box.innerHTML = '<span style="color:#fca5a5;">请求失败：' + e + '</span>'; });
}
var PL_TYPE_TARGETS = {
  '立碑':['求富贵'], '安葬':['求富贵','求子'], '婚嫁':['求婚姻'], '开业':['求财','求官'],
  '新居入宅':['求财','求富贵'], '动土修造':['求富贵'], '阳宅动土':['求富贵'], '阴宅动土':['求富贵','求子'],
  '安门':['求富贵'], '作灶':['求财'], '安床':['求子','求婚姻'], '出行':['求富贵'], '提车':['求财','求富贵'],
  '买房过户':['求财','求富贵'], '开工':['求财','求官'], '入学开学':['求学问'], '考试':['求学问','求官'],
  '测孩子成绩':['求学问'], '迁坟':['求富贵'], '催龙补气':['求富贵'], '召山买土':['求富贵'],
  '祭祀祈福':['求富贵','求学问'],
  '求嗣':['求子'], '签约交易':['求财','求官'], '上梁盖屋':['求富贵']
};
var PL_TYPE_HINTS = {
  '立碑':'坟山坐山 + 来龙定局，重在安灵荫后、福泽绵长。',
  '安葬':'坟山坐山 + 来龙为体，重在安宁荫后、子孙昌盛。',
  '婚嫁':'以男女双方年命定坐山（选男年命对应山向），重在夫妻和合、百年好合。',
  '开业':'以店铺坐向为体，重在财官兴旺、客源广进。',
  '新居入宅':'以住宅坐山为体，重在家宅平安、人财两旺（您关注的新居类型）。',
  '动土修造':'以坐山 / 来龙为体，重在兴工平安、顺利无虞。',
  '安门':'以门向（向首）为要，重在纳气清吉、家宅平安。',
  '作灶':'以灶位为要，重在饮食丰足、家人康宁。',
  '安床':'以床位为要，重在安眠和合、求子得嗣。',
  '出行':'以日干贵人 / 驿马为要（坐山可代方位），重在路途顺遂、出入平安。',
  '提车':'以车主本命为要，重在提车顺遂、出入平安、财不暗耗。',
  '阳宅动土':'以住宅坐山为体，重在兴工动土平安、根基稳固。',
  '阴宅动土':'以坟山坐山+来龙为体，重在开山破土顺遂、安妥先灵。',
  '买房过户':'以购房者本命为体，重在置业安居、过户顺利、财源有续。',
  '开工':'以公司/工厂坐向为体，重在开工大吉、事业兴旺、财官两旺。',
  '入学开学':'以学子本命为体，重在开蒙启智、学业有成、师长和合。',
  '考试':'以考生本命为体，重在考场顺遂、临场发挥、金榜题名。',
  '测孩子成绩':'以孩子本命 + 日干文昌星/长生为类神（文昌照临成绩佳），重在学业表现、发挥稳定。',
  '迁坟':'以坟山坐山+来龙为体，重在迁葬顺遂、福荫后昆。',
  '催龙补气':'以来龙+坐山为体，重在龙脉得合气而催旺、荫及子孙。',
  '召山买土':'以坐山+向首为体，重在动土取土不冲山向、土气归山。',
  '祭祀祈福':'以神位 / 本命为体，重在祈福纳祥、感应通灵。',
  '求嗣':'以床 / 堂位为体，重在求子得孕、血脉绵长。',
  '签约交易':'以坐山 / 来龙为体，重在财官成交、谋事有成。',
  '上梁盖屋':'以坐山为体，重在屋宇稳固、人宅两安。'
};
function plOnTypeChange() {
  var t = document.getElementById('plType').value;
  var isHun = (t === '婚嫁');
  var isYin = (['立碑','安葬','阴宅动土','迁坟','催龙补气','召山买土'].indexOf(t) >= 0);
  // 以本命年命为主的类型：出行/新居入宅/祭祀祈福/求嗣/安门/作灶/安床（评分接入本命禄马贵到山到向+拱命格+出行驿马）
  var needBenMing = (['新居入宅','出行','提车','祭祀祈福','求嗣','安门','作灶','安床','买房过户','入学开学','考试','测孩子成绩','催龙补气','召山买土'].indexOf(t) >= 0);
  document.getElementById('plNianmingRow').style.display = isHun ? 'flex' : 'none';
  document.getElementById('plBenMingRow').style.display = (!isHun && needBenMing) ? 'flex' : 'none';
  document.getElementById('plMubiaoRow').style.display = isHun ? 'none' : 'flex';
  // 来龙：仅阴宅类显示（2026-08-17 憨爷：无关选项不显示）
  document.getElementById('plLailongRow').style.display = isYin ? 'block' : 'none';
  // 文书行（仙命/地理师）：阴宅类+婚嫁显示，其他隐藏
  document.getElementById('plWenshuRow').style.display = (isYin || isHun) ? 'flex' : 'none';
  // 每类默认求课目标
  var vals = PL_TYPE_TARGETS[t] || [];
  document.querySelectorAll('#plMubiaoRow input[type=checkbox]').forEach(function(cb){
    cb.checked = (vals.indexOf(cb.value) >= 0);
  });
  // 类型说明（追加目标摘要：类型已隐含目标，目标多选行隐藏后用户仍可见）
  var hint = PL_TYPE_HINTS[t] || '';
  if (vals.length) hint += (hint ? ' ｜ ' : '') + '目标：' + vals.join('+');
  document.getElementById('plTypeHint').textContent = hint;
}

// 择日策略切换：显示/隐藏权重滑块
function onZeriStrategyChange() {
  var strategy = document.getElementById('plStrategy').value;
  var doushouWrap = document.getElementById('plDoushouWeightWrap');
  var liurenWrap = document.getElementById('plLiurenWeightWrap');
  var summary = document.getElementById('plWeightSummary');
  
  if (strategy === 'custom') {
    doushouWrap.style.display = 'inline-flex';
    liurenWrap.style.display = 'inline-flex';
    summary.style.display = 'block';
    updateWeightDisplay();
  } else {
    doushouWrap.style.display = 'none';
    liurenWrap.style.display = 'none';
    summary.style.display = 'none';
    
    // 根据预设模式设置权重
    var doushouSlider = document.getElementById('plDoushouWeight');
    var liurenSlider = document.getElementById('plLiurenWeight');
    if (strategy === 'doushou_first') {
      doushouSlider.value = 70; liurenSlider.value = 30;
    } else if (strategy === 'liuren_first') {
      doushouSlider.value = 30; liurenSlider.value = 70;
    } else {
      doushouSlider.value = 50; liurenSlider.value = 50;
    }
    document.getElementById('plDoushouWeightVal').textContent = doushouSlider.value;
    document.getElementById('plLiurenWeightVal').textContent = liurenSlider.value;
  }
}

// 更新权重显示（滑块联动）
function updateWeightDisplay() {
  var doushouW = parseInt(document.getElementById('plDoushouWeight').value);
  var liurenW = parseInt(document.getElementById('plLiurenWeight').value);
  
  // 联动：两者之和为100
  var total = doushouW + liurenW;
  if (total > 0) {
    document.getElementById('plDoushouWeightVal').textContent = doushouW;
    document.getElementById('plLiurenWeightVal').textContent = liurenW;
    
    // 更新公式显示
    var dsPct = (doushouW / total * 100).toFixed(0);
    var lrPct = (liurenW / total * 100).toFixed(0);
    document.getElementById('plWeightFormula').textContent = 
      '斗首×' + doushouW + '% + 六壬×' + liurenW + '% = 加权分';
  }
}

function plGetDateRange() {
  var sy = parseInt(document.getElementById('plStartYear').value);
  var sm = parseInt(document.getElementById('plStartMonth').value);
  var sd = parseInt(document.getElementById('plStartDay').value);
  var ey = parseInt(document.getElementById('plEndYear').value);
  var em = parseInt(document.getElementById('plEndMonth').value);
  var ed = parseInt(document.getElementById('plEndDay').value);
  if (!sy || !sm || !sd || !ey || !em || !ed) return null;
  function pad(n){ return (n<10?'0':'')+n; }
  return {
    start_date: sy + '-' + pad(sm) + '-' + pad(sd),
    end_date: ey + '-' + pad(em) + '-' + pad(ed),
  };
}

// ====== 择日模式切换（日期范围 / 禄马贵人） ======
var _zeriMode = 'range';
function switchZeriMode(mode) {
  _zeriMode = mode;
  var tabRange = document.getElementById('modeTabRange');
  var tabLmg = document.getElementById('modeTabLmg');
  var panelRange = document.getElementById('modeRangeOnly');
  var panelLmg = document.getElementById('modeLmgOnly');
  var btnExport = document.getElementById('plExport');
  var btnExportPpt = document.getElementById('plExportPpt');
  if (mode === 'range') {
    tabRange.style.background = 'linear-gradient(135deg,#6366f1,#8b5cf6)';
    tabRange.style.color = '#fff';
    tabLmg.style.background = 'transparent';
    tabLmg.style.color = '#9fb3d1';
    panelRange.style.display = '';
    panelLmg.style.display = 'none';
    btnExport.style.display = 'none';
    btnExportPpt.style.display = 'none';
  } else {
    tabLmg.style.background = 'linear-gradient(135deg,#f59e0b,#d97706)';
    tabLmg.style.color = '#fff';
    tabRange.style.background = 'transparent';
    tabRange.style.color = '#9fb3d1';
    panelRange.style.display = 'none';
    panelLmg.style.display = '';
    btnExport.style.display = 'none';
    btnExportPpt.style.display = 'none';
  }
  // 同步类型/坐山到隐藏字段
  syncZeriShared();
}

// ====== 禄马贵人条件择日（专用API） ======
function plBatchZeriLmg() {
  var type = document.getElementById('plType').value;
  var mountain = document.getElementById('plMountain').value;
  var errEl = document.getElementById('plError');
  errEl.classList.remove('show'); errEl.textContent = '';
  if (!mountain) { errEl.textContent = '请先选择坐山！'; errEl.classList.add('show'); return; }

  var qiushi = document.getElementById('plLmgQiushi2').value;
  if (!qiushi) { errEl.textContent = '禄马贵人择日必须选择求事方向！'; errEl.classList.add('show'); return; }

  var startY = parseInt(document.getElementById('plLmgStartYear').value) || 2026;
  var startM = parseInt(document.getElementById('plLmgStartMonth').value) || 8;
  var startD = parseInt(document.getElementById('plLmgStartDay').value) || 26;
  var scanDays = parseInt(document.getElementById('plLmgScanDays').value) || 90;

  var lmgStart = startY + '-' + String(startM).padStart(2,'0') + '-' + String(startD).padStart(2,'0');
  var lmgEndDate = new Date(startY, startM-1, startD);
  lmgEndDate.setDate(lmgEndDate.getDate() + scanDays);
  var lmgEnd = lmgEndDate.getFullYear() + '-' + String(lmgEndDate.getMonth()+1).padStart(2,'0') + '-' + String(lmgEndDate.getDate()).padStart(2,'0');

  var body = {
    start_date: lmgStart, end_date: lmgEnd,
    mountain: mountain, jiri_count: 10,
    zetiri_type: type,
    mubiao: [],
    lailong: document.getElementById('plLailong') ? document.getElementById('plLailong').value : '',
    longitude: document.getElementById('plLongitude') ? document.getElementById('plLongitude').value : '105.4',
    lmg_qiushi: qiushi,
    lmg_auto: 1,
    lmg_priority: 'lmg_to_shanxiang_13ke',
    mode: 'lmg'
  };

  document.getElementById('plLoading').classList.add('show');
  document.getElementById('plResult').classList.remove('show');

  fetch('/api/zeri/batch', {
    method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(body)
  }).then(function(r){ return r.json(); }).then(function(resp){
    document.getElementById('plLoading').classList.remove('show');
    if (!resp.success) { errEl.textContent = resp.error || '择日失败'; errEl.classList.add('show'); return; }
    _plResults = resp.results || [];
    document.getElementById('plResultInfo').textContent =
      '🏵 禄马贵人择日：范围 ' + lmgStart + ' ~ ' + lmgEnd + '，命中 ' + _plResults.length + ' 个吉期';
    renderPlList(_plResults);
  }).catch(function(e){
    document.getElementById('plLoading').classList.remove('show');
    errEl.textContent = '请求失败：' + e.message;
    errEl.classList.add('show');
  });
}

function plBatchZeri() {
  var type = document.getElementById('plType').value;
  var mountain = document.getElementById('plMountain').value;
  var count = parseInt(document.getElementById('plCount').value) || 10;
  var range = plGetDateRange();
  var errEl = document.getElementById('plError');
  errEl.classList.remove('show'); errEl.textContent = '';

  if (!mountain) { errEl.textContent = '请先选择坐山（婚嫁请选男年命对应山向）！'; errEl.classList.add('show'); return; }
  if (!range) { errEl.textContent = '请填写完整的起始/结束日期！'; errEl.classList.add('show'); return; }

  document.getElementById('plLoading').classList.add('show');
  document.getElementById('plResult').classList.remove('show');
  document.getElementById('plGo').disabled = true;
  document.getElementById('plExport').style.display = 'none';

  // 收集求课目标（婚嫁时目标行隐藏，强制以求婚姻参与仪度评分）
  var mubiao = [];
  document.querySelectorAll('#plMubiaoRow input[type=checkbox]:checked').forEach(function(cb){ mubiao.push(cb.value); });
  if (type === '婚嫁') mubiao = ['求婚姻'];
  // 主命（本命年命）：出行/新居等类型参与年命评分
  var benMing = document.getElementById('plBenMing') ? document.getElementById('plBenMing').value : '';
  var benMingAge = document.getElementById('plBenMingAge') ? document.getElementById('plBenMingAge').value : '';
  var benMingSex = (document.getElementById('plBenMingSex') && document.getElementById('plBenMingSex').value) || '男';
  
  // 收集择日策略参数
  var strategy = document.getElementById('plStrategy') ? document.getElementById('plStrategy').value : 'balanced';
  var doushouWeight = 50, liurenWeight = 50;
  if (strategy === 'doushou_first') {
    doushouWeight = 70; liurenWeight = 30;
  } else if (strategy === 'liuren_first') {
    doushouWeight = 30; liurenWeight = 70;
  } else if (strategy === 'custom') {
    doushouWeight = parseInt(document.getElementById('plDoushouWeight').value) || 50;
    liurenWeight = parseInt(document.getElementById('plLiurenWeight').value) || 50;
  }
  
  var body = { start_date: range.start_date, end_date: range.end_date, mountain: mountain, jiri_count: count, zetiri_type: type, mubiao: mubiao, ben_ming: benMing, ben_ming_age: benMingAge, ben_ming_sex: benMingSex,
               lailong: document.getElementById('plLailong') ? document.getElementById('plLailong').value : '',
               longitude: document.getElementById('plLongitude') ? document.getElementById('plLongitude').value : '105.4',
               zeri_strategy: strategy,
               doushou_weight: doushouWeight,
               liuren_weight: liurenWeight };
  // 禄马贵人条件择日：默认自动推荐（按求事方向挑最优组）
  var lmgOn = true;
  var wantAuto = true;
  if (lmgOn) {
    body.lmg_qiushi = document.getElementById('plLmgQiushi') ? document.getElementById('plLmgQiushi').value : '';
    body.mobile = localStorage.getItem('zeri_mobile') || '';
    body.lmg_auto = 1;
    if (PL_LMG_OVERSEE === 1) body.lmg_oversee = 1;
    PL_LMG_AUTO = 0; PL_LMG_OVERSEE = 0;
  }

  fetch('/api/zeri/batch', {
    method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(body)
  }).then(function(r){ return r.json(); }).then(function(resp){
    document.getElementById('plLoading').classList.remove('show');
    document.getElementById('plGo').disabled = false;
    if (!resp.success) { errEl.textContent = resp.error || '批量择日失败'; errEl.classList.add('show'); return; }
    _plResults = resp.results || [];
    document.getElementById('plResultInfo').textContent =
      (resp.meta ? ('范围 ' + resp.meta.start_date + ' ~ ' + resp.meta.end_date + '，遍历 ' + resp.meta.days + ' 天') : '') +
      '，命中 ' + _plResults.length + ' 个吉期';
    // 2026-08-21 范围格局统计（古籍合参美格/凶格命中次数，遍历全部候选）
    var st = resp.stats || {};
    var mgKeys = Object.keys(st.meige || {}), xgKeys = Object.keys(st.xiong || {});
    var stHtml = '';
    if (mgKeys.length || xgKeys.length) {
      var mgTxt = mgKeys.map(function(k){ return '<b style="color:#7ee2b8;">' + k + '</b>×' + st.meige[k]; }).join('　');
      var xgTxt = xgKeys.map(function(k){ return '<b style="color:#ff6b6b;">' + k + '</b>×' + st.xiong[k]; }).join('　');
      stHtml = '<div style="padding:10px 12px;background:rgba(255,255,255,.03);border:1px solid #3a3a6a;border-radius:8px;font-size:12.5px;line-height:1.9;">' +
        '<div style="font-weight:700;color:#8ea2ff;margin-bottom:4px;">📊 范围格局统计（' + (resp.meta ? resp.meta.candidates : '') + ' 个候选课）</div>' +
        (mgTxt ? '<div>✨ 美格/吉格：' + mgTxt + '</div>' : '') +
        (xgTxt ? '<div>⚠️ 凶格警示：' + xgTxt + '</div>' : '') +
        '</div>';
    }
    document.getElementById('plStats').innerHTML = stHtml;
    renderPlList(_plResults);
    // 2026-08-25 智能推荐 + 超选预览钩子：顶部横幅
    var lg = resp.lmg;
    if (lg) {
      var banner = '';
      if (lg.recommend && lg.auto) {
        banner = '<div style="padding:10px 12px;margin-bottom:8px;background:#1a2440;border:1px solid #fbbf24;border-radius:8px;font-size:12.5px;color:#fde68a;line-height:1.8;">' +
          '🎯 系统推荐（免费/内测 · 免选组）：求事方向「' + (lg.recommend.qiushi || '不限') + '」→ 最优一课为 ' +
          '<b style="color:#fff;">' + lg.recommend.date + ' ' + lg.recommend.shichen + '时</b>，推荐侧重位置组 ' +
          '<b style="color:#7ee2b8;">「' + (lg.recommend.group || '-') + '」</b>，禄马贵人细分分 <b style="color:#7ee2b8;">' + (lg.recommend.bonus || 0) + '</b>' +
          (lg.recommend.hit ? '（✅ ≥60 命中标绿）' : '（未达60）') +
          '<div style="font-size:11.5px;color:#93a4c4;margin-top:4px;">采纳后默认锁定该1组（尊享可全选6组）。</div></div>';
      } else if (lg.oversee) {
        var prevLeft = '';
        if (typeof lg.preview_daily_left === 'number' && lg.preview_daily_left >= 0) {
          prevLeft = '今日剩余 <b style="color:#fbbf24;">' + lg.preview_daily_left + (lg.preview_limit ? ' / ' + lg.preview_limit : '') + '</b> 次预览 · ';
        }
        banner = '<div style="padding:10px 12px;margin-bottom:8px;background:#1a2440;border:1px solid #8ea2ff;border-radius:8px;font-size:12.5px;color:#c3d2f5;line-height:1.8;">' +
          '👁 超选预览：您勾选了 <b style="color:#fff;">' + lg.selected + '</b> 组，当前权益仅 <b style="color:#fbbf24;">' + lg.granted + ' 组</b>。已按全量预览排序（本组结果仅作体验）；' + prevLeft +
          '开通尊享可全选6组持久使用。</div>';
      }
      if (banner) document.getElementById('plStats').innerHTML = stHtml + banner;
    }
    document.getElementById('plResult').classList.add('show');
    document.getElementById('plExport').style.display = 'inline-block';
    document.getElementById('plExportPpt').style.display = 'inline-block';
  }).catch(function(e){
    document.getElementById('plLoading').classList.remove('show');
    document.getElementById('plGo').disabled = false;
    errEl.textContent = '请求异常：' + e; errEl.classList.add('show');
  });
}
function plSatZeri() {
  var type = document.getElementById('plType').value;
  var mountain = document.getElementById('plMountain').value;
  var errEl = document.getElementById('plError');
  errEl.classList.remove('show'); errEl.textContent = '';
  if (!mountain) { errEl.textContent = '请先选择坐山！'; errEl.classList.add('show'); return; }
  var ds = parseInt(document.getElementById('plSatDs').value) || 100;
  var lr = parseInt(document.getElementById('plSatLr').value) || 100;
  var yq = parseInt(document.getElementById('plSatYq').value) || 100;
  var cnt = parseInt(document.getElementById('plSatCnt').value) || 3;
  var days = parseInt(document.getElementById('plSatDays').value) || 1095;
  var fastAb = parseInt(document.getElementById('plSatFastAbandon').value) || 365;
  // 起始日期（复用面板起始日期）
  var range = plGetDateRange();
  if (!range) { errEl.textContent = '请填写完整的起始日期！'; errEl.classList.add('show'); return; }
  // 目标/主命（复用现有输入）
  var mubiao = [];
  document.querySelectorAll('#plMubiaoRow input[type=checkbox]:checked').forEach(function(cb){ mubiao.push(cb.value); });
  if (type === '婚嫁') mubiao = ['求婚姻'];
  var benMing = document.getElementById('plBenMing') ? document.getElementById('plBenMing').value : '';
  var benMingAge = document.getElementById('plBenMingAge') ? document.getElementById('plBenMingAge').value : '';
  var benMingSex = (document.getElementById('plBenMingSex') && document.getElementById('plBenMingSex').value) || '男';
  var body = { start_date: range.start_date, mountain: mountain, zetiri_type: type, mubiao: mubiao,
               ben_ming: benMing, ben_ming_age: benMingAge, ben_ming_sex: benMingSex,
               lailong: document.getElementById('plLailong') ? document.getElementById('plLailong').value : '',
               longitude: document.getElementById('plLongitude') ? document.getElementById('plLongitude').value : '105.4',
               min_doushou: ds, min_liuren: lr, min_yanqin: yq, target_count: cnt,
               max_days: days, fast_abandon_days: fastAb };
  document.getElementById('plLoading').classList.add('show');
  document.getElementById('plResult').classList.remove('show');
  document.getElementById('plSatGo').disabled = true;
  fetch('/api/zeri/satisfy', {
    method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(body)
  }).then(function(r){ return r.json(); }).then(function(resp){
    document.getElementById('plLoading').classList.remove('show');
    document.getElementById('plSatGo').disabled = false;
    if (resp.error) { errEl.textContent = resp.error; errEl.classList.add('show'); return; }
    var info = document.getElementById('plSatInfo');
    if (resp.requires_pay) {
      info.innerHTML = '💳 <b>该档位需付费解锁</b>：' + (resp.tier_desc || resp.tier) + '　<b style="color:#fbbf24;">' + resp.price + ' 元/次</b>（按次解锁，24小时内有效）。' +
        '<br>请在本会话中回复「<b style="color:#7ee2b8;">付费解锁</b>」，傻妞会发起微信支付，成功后自动放行，你再点一次「🎯 达标择日」即可。' +
        '<br><span style="color:#94a3b8;">免费额度：最多扫 ≤1年（' + (resp.free_days||365) + ' 天）无需付费。</span>';
      info.style.display = 'block';
      document.getElementById('plResult').classList.remove('show');
      return;
    }
    var hl = resp.hit_level || {};
    var hitTxt = '斗首≥' + hl.doushou + '　六壬≥' + hl.liuren + '　演禽≥' + hl.yanqin;
    var line = '';
    if (resp.results && resp.results.length) {
      line = '🎯 达标命中：档位 ' + hitTxt + (resp.lowered ? '　（<b>已自动降档</b>，更严格档位在该天数内未凑齐）' : '') +
             '　｜　从 ' + resp.start_date + ' 起第 <b>' + resp.scanned_days + '</b> 天命中 ' + resp.results.length + ' 个' +
             (resp.unlock_note ? '　' + resp.unlock_note : '');
    } else {
      line = '😔 各档位扫描 ' + resp.max_days + ' 天均未命中，已降到最低档（' + hitTxt + '）。' + (resp.message || '请放宽达标条件或增加最大天数。');
    }
    info.innerHTML = line;
    info.style.display = 'block';
    _plResults = resp.results || [];
    renderPlList(_plResults);
    document.getElementById('plResult').classList.add('show');
  }).catch(function(e){
    document.getElementById('plLoading').classList.remove('show');
    document.getElementById('plSatGo').disabled = false;
    errEl.textContent = '请求异常：' + e; errEl.classList.add('show');
  });
}
/** 24山批量优化：扫 1/3/5 年 × 全24山，每山取最优候选（对接后端 /api/zeri/optimize） */
function zeriBatchOptimize() {
  var years = parseInt(document.getElementById('zeriOptYears').value) || 3;
  var statusEl = document.getElementById('zeriOptStatus');
  var resultEl = document.getElementById('zeriResult');
  var btn = document.querySelector('button[onclick*="zeriBatchOptimize"]');
  if (btn) { btn.disabled = true; btn.textContent = '⏳ 优化中...'; }
  if (statusEl) statusEl.textContent = '⏳ 正在扫描 ' + years + '年 × 24山（三阶段漏斗：斗首快筛 → 到山到向 → 完整六壬），可能需要数十秒到数分钟...';
  fetch('/api/zeri/optimize', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ years: years, p1: 500, p2: 50, p3: 20 })
  }).then(function(r){ return r.json(); }).then(function(d){
    if (btn) { btn.disabled = false; btn.textContent = '🚀 开始优化'; }
    if (!d.success) {
      if (statusEl) statusEl.textContent = '❌ 优化失败: ' + (d.error || '未知错误');
      return;
    }
    var summary = d.summary || {};
    var mountains = Object.keys(summary).sort();
    if (statusEl) statusEl.textContent = '✅ 完成：' + years + '年 × ' + mountains.length + ' 山' + (d.output_file ? '　📄 ' + d.output_file : '');
    if (!mountains.length) {
      resultEl.innerHTML = '<div style="color:#94a3b8;padding:14px;">未找到任何候选吉日，可尝试减少扫描年限或放宽筛选。</div>';
      return;
    }
    var html = '';
    html += '<div style="margin-top:12px;background:rgba(245,158,11,.06);border:1px dashed #f59e0b;border-radius:8px;padding:12px 14px;">';
    html += '<div style="font-size:13px;font-weight:600;color:#f59e0b;margin-bottom:8px;">🏔️ 24山批量优化结果（' + years + '年 · 每山取前5候选）</div>';
    mountains.forEach(function(mtn){
      var cands = summary[mtn] || [];
      if (!cands.length) return;
      html += '<div style="margin:8px 0;padding:8px 10px;background:rgba(255,255,255,.03);border-radius:6px;border-left:3px solid #f59e0b;">';
      html += '<div style="font-size:12px;font-weight:700;color:#fbbf24;margin-bottom:4px;">' + mtn + '山（' + cands.length + '个候选）</div>';
      cands.forEach(function(c){
        var gc = plGradeColor(c.grade);
        html += '<div style="font-size:12px;color:#c7d2fe;line-height:1.8;">' +
          '<b style="color:#fff;">' + (c.date||'') + ' ' + (c.shichen||'') + '时</b>　' +
          '<span style="color:#9fb3d1;">' + (c.sizhu||'--') + '</span>　' +
          '<b style="color:#fbbf24;">' + (c.total_score||0) + '分</b> ' +
          '<span style="background:' + gc + '33;color:' + gc + ';border-radius:4px;padding:0 5px;font-size:11px;">' + (c.grade||'') + '</span>' +
          ' <span style="font-size:10px;color:#8b9bb8;" title="统一评分口径：总分 = 斗首加分 + 禄马莅临到山到向骨架 + 六壬课格加分">斗首' + (c.phase1_score||0) + ' + 到向' + (c.phase2_score||0) + ' + 六壬' + (c.phase3_score||0) + ' · 拱格' + (c.gong_count||0) + ' · 活禄马' + (c.huoma_count||0) + '</span>' +
          (c.leishen_detail && c.leishen_detail.end ?
            (function(){ var _lc3 = {'吉':'#7ee2b8','凶':'#ff6b6b','平':'#fbbf24'}[c.leishen_detail.end] || '#999';
              var _li3 = {'吉':'✅','凶':'❌','平':'➖'}[c.leishen_detail.end] || '';
              return ' <span style="font-size:10px;color:' + _lc3 + ';" title="' + (c.leishen_detail.narr||'') + '">' + _li3 + ' ' + (c.leishen_detail.end||'') + '类神</span>'; })() : '') +
          '</div>';
      });
      html += '</div>';
    });
    html += '</div>';
    resultEl.innerHTML = html;
  }).catch(function(e){
    if (btn) { btn.disabled = false; btn.textContent = '🚀 开始优化'; }
    if (statusEl) statusEl.textContent = '❌ 请求异常: ' + e;
  });
}

function plGradeColor(g) {
  if (!g) return '#9fb3d1';
  if (g.indexOf('上') >= 0) return '#fbbf24';
  if (g.indexOf('吉') >= 0) return '#7ee2b8';
  if (g === '平') return '#9fb3d1';
  return '#ff6b6b';
}
function plDsdxTxt(dsdx) {
  // 禄马贵人到山到向 → HTML 片段；兼容两种结构：
  //   batch: {lu:{zhi,to_shan:bool,to_xiang:bool}, ma:{...}, guiren:{zhi[],to_shan[],to_xiang[]}}
  //   analyze: {lu:{lu_zhi,to_shan:bool,to_xiang:bool}, ma:{ma_zhi,...}, guiren:{guiren_zhi[],...}}
  if (!dsdx) return '';
  function one(label, o) {
    if (!o) return '';
    var z = o.zhi || o.lu_zhi || o.ma_zhi || '';
    var parts = [];
    if (o.to_shan && o.to_shan !== false && (!o.to_shan.length || o.to_shan.length > 0)) parts.push('<b style="color:#7ee2b8;">→山</b>');
    if (o.to_xiang && o.to_xiang !== false && (!o.to_xiang.length || o.to_xiang.length > 0)) parts.push('<b style="color:#7ee2b8;">→向</b>');
    if (!parts.length) parts.push('<span style="color:#666;">未到</span>');
    return label + z + parts.join('');
  }
  var gr = dsdx.guiren || {};
  var gz = (gr.zhi || gr.guiren_zhi || []).join(',');
  var gParts = [];
  if ((gr.to_shan || []).length) gParts.push('<b style="color:#7ee2b8;">→山' + gr.to_shan.join('、') + '</b>');
  if ((gr.to_xiang || []).length) gParts.push('<b style="color:#7ee2b8;">→向' + gr.to_xiang.join('、') + '</b>');
  if (!gParts.length) gParts.push('<span style="color:#666;">未到</span>');
  return '<span style="white-space:nowrap;">' + one('禄', dsdx.lu) + '</span>　' +
         '<span style="white-space:nowrap;">' + one('马', dsdx.ma) + '</span>　' +
         '<span style="white-space:nowrap;">贵人' + gz + gParts.join('') + '</span>';
}
function plNmTxt(nm) {
  // 主命（本命年命）评估摘要：batch 返回 {used, ben_ming, ben_ming_zhi, luma_qualified,
  //   ben_ming_shang_shen, xing_nian, xing_nian_shang_shen, gongming_ge, ma_on_ming, adj}
  if (!nm || !nm.used) return '';
  var parts = [];
  if (nm.ben_ming) parts.push('<b style="color:#f0abfc;">' + nm.ben_ming + '命</b>');
  if (nm.ben_ming_shang_shen) parts.push('上神' + nm.ben_ming_shang_shen);
  if (nm.xing_nian) parts.push('行年' + nm.xing_nian + '(上神' + (nm.xing_nian_shang_shen || '') + ')');
  if (nm.luma_qualified != null) parts.push('本命禄马贵' + (nm.luma_qualified ? '<b style="color:#7ee2b8;">✓到山到向</b>' : '<span style="color:#666;">✗</span>'));
  if (nm.gongming_ge) parts.push('拱年命格');
  if (nm.ma_on_ming) parts.push('驿马临命(利出行)');
  var s = parts.join('　');
  if (nm.adj) s += '　<b style="color:#fbbf24;">年命+' + nm.adj + '</b>';
  return s;
}
function renderPlList(list) {
  var wrap = document.getElementById('plList');
  if (!list || !list.length) { wrap.innerHTML = '<div style="color:#999;text-align:center;padding:20px;">该范围未命中合格吉日，可放宽日期范围或换坐山重试。</div>'; return; }
  wrap.innerHTML = list.map(function(it, i){
    var gc = plGradeColor(it.grade);
    var ds = it.doushou_classes || {};
    var dsTxt = typeof ds === 'object' ? (Object.keys(ds).map(function(k){ return k + ds[k]; }).join(' ')) : (ds || '');
    var tags = [];
    if (it.luma_grade) {
      var lg = it.luma_grade;
      var lvColor = {'L3':'#f59e0b','L2':'#7ee2b8','L1':'#a78bfa','L0':'#6b7280'}[lg.level] || '#999';
      var lvIcon = {'L3':'🔥','L2':'✅','L1':'⚪','L0':'⬜'}[lg.level] || '';
      tags.push('<span style="color:' + lvColor + ';font-weight:600;">' + lvIcon + ' ' + lg.name + '</span>');
      // 四柱明细
      if (it.luma_guiren) {
        var lg2 = it.luma_guiren;
        var marks = [['年',lg2.nian_qualified],['月',lg2.yue_qualified],['日',lg2.ri_qualified],['时',lg2.shi_qualified]]
          .map(function(p){ return p[0] + (p[1] ? '<b style="color:#7ee2b8;">✓</b>' : '<span style="color:#666;">✗</span>'); }).join('');
        tags.push('四柱到山到向：' + marks);
      }
    } else if (it.luma_guiren) {
      var lg = it.luma_guiren;
      var marks = [['年',lg.nian_qualified],['月',lg.yue_qualified],['日',lg.ri_qualified],['时',lg.shi_qualified]]
        .map(function(p){ return p[0] + (p[1] ? '<b style="color:#7ee2b8;">✓</b>' : '<span style="color:#666;">✗</span>'); }).join('');
      tags.push('四柱禄马贵人(到山到向)：' + marks + '　三传禄马' + (lg.sanchuan_luma||0) + '个');
    }
    // 2026-08-25 禄马贵人条件择日命中/加权
    if (it.lmg && it.lmg.used) {
      var lmgd = it.lmg;
      var posTxt = (lmgd.hit_groups && lmgd.hit_groups.length) ? '<b style="color:#3ddc84;">' + lmgd.hit_groups.join('、') + '</b>组命中(≥60)' : '均未到60';
      tags.push('🏵 禄马贵人条件：' + (lmgd.qiushi || '不限') + '　倾向加权<b style="color:#fbbf24;">' + lmgd.bonus + '</b>　' + posTxt);
    }
    if (it.daoshan_details) tags.push('日禄马：' + plDsdxTxt(it.daoshan_details));
    if (it.nianming && it.nianming.used) tags.push('主命：' + plNmTxt(it.nianming));
    if (it.yidu_score != null && it.yidu_score > 0) tags.push('仪度评分：<b style="color:#fbbf24;">' + it.yidu_score + '</b>(' + (it.yidu_eval||'') + ')');
    if (dsTxt) tags.push('斗首：<b>' + dsTxt + '</b>');
    if (it.keti) tags.push('课体：<b style="color:#a78bfa;">' + it.keti + '</b>');
    // 2026-09-06 三维顶格择日（斗首/演禽/六壬 独立分 + 顶格标）
    if (it.doushou_score != null && it.yanqin_score != null) {
      tags.push('三维：<b style="color:#f59e0b;">斗首' + it.doushou_score + '</b> · <b style="color:#7ee2b8;">演禽' + it.yanqin_score + '</b> · <b style="color:#a78bfa;">六壬' + (it.liuren_score || 0) + '</b>' + (it.triple_top ? ' <b style="color:#fbbf24;">★顶格</b>' : ''));
    }
    if (it.gong_names && it.gong_names.length) tags.push('拱格：<b>' + it.gong_names.join('、') + '</b>');
    // 2026-09-06 择日类型类神吉应（安葬/作灶…事件类神入课：徽标 + 叙事摘要，悬停看全）
    if (it.leishen_detail && it.leishen_detail.end) {
      var _ld = it.leishen_detail;
      var _lc = {'吉':'#7ee2b8','凶':'#f87171','平':'#fbbf24'}[_ld.end] || '#999';
      var _li = {'吉':'✅','凶':'❌','平':'➖'}[_ld.end] || '';
      var _ln = (_ld.narr || '');
      tags.push('<span style="color:' + _lc + ';font-weight:600;" title="类神' + ((_ld.zhi_list||[]).join('、')||'—') + '；' + _ln + '">' + _li + ' ' + (_ld.zeri_type || '') + '类神' + _ld.end + '</span>' +
                '<span style="color:#9fa8c0;font-size:11px;" title="' + _ln + '">' + (_ln.length > 24 ? _ln.slice(0, 24) + '…' : _ln) + '</span>');
    }
    // 达成矩阵（2026-08-17：13吉课/禄马贵发传/到向 分层展示；杀师标红）
    if (it.jike_13 && it.jike_13.hits && it.jike_13.hits.length) tags.push('13吉课：<b style="color:#7ee2b8;">' + it.jike_13.hits.join('、') + '</b>');
    // 2026-08-21 古籍合参美格/凶格徽标（候选 hecan.zeri_rules.hits，悬停看叙事）
    var zrHits = ((it.hecan || {}).zeri_rules || {}).hits || [];
    if (zrHits.length) {
      tags.push(zrHits.map(function(h){
        var col = (h['结论'] === '凶') ? '#ff6b6b' : '#7ee2b8';
        return '<span style="color:' + col + ';font-size:11px;border:1px solid ' + col + '66;border-radius:4px;padding:0 5px;margin:0 2px;cursor:help;" title="' + (h['叙事'] || '') + '">' + (h['标签'] || h.id || '') + '</span>';
      }).join(''));
    }
    if (it.constraint_matrix && it.constraint_matrix.bonus) {
      var _b = it.constraint_matrix.bonus;
      if (_b.luma_fachuan) tags.push('禄马贵发传：<b style="color:#fbbf24;">' + _b.luma_fachuan + '</b>');
      if (_b.luma_duoxiang) tags.push('到山到向：<b style="color:#fbbf24;">' + _b.luma_duoxiang + '/4</b>');
    }
    if (it.shashi && it.shashi.is_shashi) tags.push('<b style="color:#f87171;">⚠杀师日</b>');
    if (it.yanqin_score != null) tags.push('演禽：<b>' + it.yanqin_score + '</b>');
    if (it.yanqin_patterns && it.yanqin_patterns.length) tags.push('演禽格局：<b>' + it.yanqin_patterns.join('、') + '</b>');
    if (it.yanqin_siqin && Object.keys(it.yanqin_siqin).length) {
      var sqTxt = ['年','月','日','时'].map(function(k){
        var x = it.yanqin_siqin[k + '禽'];
        if (!x) return '';
        var star = x.禽星 || x.宿 || '';
        var jx = (x.吉凶 && x.吉凶 !== '平') ? '<span style="color:#f87171;">' + x.吉凶 + '</span>' : '';
        return k + star + jx;
      }).filter(Boolean).join('　');
      if (sqTxt) tags.push('四禽：' + sqTxt);
    }
    var lmgHit = (it.lmg && it.lmg.used && it.lmg.hit);
    var _rowStyle = lmgHit ? 'border:1px solid #3ddc84;background:rgba(61,220,132,.10);' : '';
    
    // 计算加权分和双列分数显示
    var strategy = document.getElementById('plStrategy') ? document.getElementById('plStrategy').value : 'balanced';
    var doushouW = 50, liurenW = 50;
    if (strategy === 'doushou_first') { doushouW = 70; liurenW = 30; }
    else if (strategy === 'liuren_first') { doushouW = 30; liurenW = 70; }
    else if (strategy === 'custom') {
      doushouW = parseInt(document.getElementById('plDoushouWeight').value) || 50;
      liurenW = parseInt(document.getElementById('plLiurenWeight').value) || 50;
    }
    var dsScore = it.doushou_score || it.phase1_score || 0;
    var lrScore = it.liuren_score || 0;
    var totalW = doushouW + liurenW;
    var weightedScore = totalW > 0 ? ((dsScore * doushouW + lrScore * liurenW) / totalW).toFixed(1) : it.total_score;
    
    // 根据策略高亮对应分数
    var dsStyle = (doushouW >= liurenW) ? 'background:rgba(251,191,36,.15);border:1px solid #fbbf24;color:#fbbf24;' : 'opacity:0.7;color:#fbbf24;';
    var lrStyle = (liurenW > doushouW) ? 'background:rgba(126,226,184,.15);border:1px solid #7ee2b8;color:#7ee2b8;' : 'opacity:0.7;color:#7ee2b8;';
    
    return '<div class="pl-item" style="cursor:pointer;' + _rowStyle + '" onclick="plShowDetailByIndex(' + i + ')" title="点击查看完整课格详情">' +
      '<div class="pl-head">' +
        '<span><span class="pl-date">#' + (i+1) + ' ' + it.date + ' ' + it.shichen + '时</span>' +
        (lmgHit ? '<span style="color:#3ddc84;font-size:11px;margin-left:6px;border:1px solid #3ddc84;border-radius:4px;padding:0 5px;font-weight:700;background:rgba(61,220,132,.14);">🏵 ' + it.lmg.hit_groups.join('、') + '命中</span>' : '') +
        (it.shashi && it.shashi.is_shashi ? '<span style="color:#f87171;font-size:11px;margin-left:6px;border:1px solid #ef4444;border-radius:4px;padding:0 4px;font-weight:700;" title="' + (it.shashi.note||'') + '">⚠️' + it.shashi.level + '</span>' : '') +
        (it.day_offset ? '<span style="color:#f0abfc;font-size:11px;margin-left:6px;border:1px solid #4c3a8c;border-radius:4px;padding:0 4px;">起始+第' + it.day_offset + '天</span>' : '') +
        '<span class="pl-sizhu">' + (it.sizhu || '') + '</span></span>' +
        '<span style="display:flex;gap:6px;align-items:center;">' +
          '<span style="font-size:11px;padding:3px 7px;border-radius:4px;' + dsStyle + 'font-weight:600;" title="斗首分（权重' + doushouW + '%）">🔥' + dsScore + '</span>' +
          '<span style="font-size:11px;padding:3px 7px;border-radius:4px;' + lrStyle + 'font-weight:600;" title="六壬分（权重' + liurenW + '%）">🔮' + lrScore + '</span>' +
          '<span class="pl-score" title="加权分' + doushouW + '%斗首 + ' + liurenW + '%六壬 = ' + weightedScore + '">' + weightedScore + '</span> <span class="pl-grade" style="background:' + gc + '33;color:' + gc + ';">' + (it.grade || '') + '</span>' +
        '</span>' +
      '</div>' +
      '<div class="pl-tags">' + (tags.join('　') || '—') + '</div>' +
    '</div>';
  }).join('');
}
function plShowDetailByIndex(idx) {
  // 列表项点击入口：用全局 _plResults[idx] 取项（避免 HTML 内联 onclick 中 it{i} 变量作用域失效）
  if (!_plResults || !_plResults[idx]) return;
  return plShowDetail(_plResults[idx]);
}
function plShowDetail(it) {
  if (typeof it === 'string') { // 兼容旧调用：传的是日期
    var dateStr = arguments[1], shichen = arguments[2] || it;
    it = { date: dateStr, shichen: shichen };
  }
  var dateStr = it.date, shichen = it.shichen;
  var mountain = document.getElementById('plMountain').value;
  window._plDetailHint = ''; // 换一课清空外应记忆（类象链入参）
  var el = document.getElementById('plDetail');
  el.innerHTML = '<div style="text-align:center;color:#9fb3d1;padding:16px;">⏳ 正在加载 ' + dateStr + ' ' + shichen + '时 完整课格…</div>';
  fetch('/api/zeri/analyze?date=' + encodeURIComponent(dateStr) + '&mountain=' + encodeURIComponent(mountain) + '&shichen=' + encodeURIComponent(shichen) + '&liupai=liuren,doushou,yanqin')
    .then(function(r){ return r.json(); })
    .then(function(d){
      if (d.error) { el.innerHTML = '<div style="color:#ff6b6b;padding:12px;">加载失败：' + d.error + '</div>'; return; }
      _plDetailData = { detail: d, date: dateStr, shichen: shichen, mountain: mountain, it: it };
      el.innerHTML = plRenderDetail(d, dateStr, shichen, it);
    })
    .catch(function(e){ el.innerHTML = '<div style="color:#ff6b6b;padding:12px;">请求异常：' + e + '</div>'; });
}
function _plName(p) {
  // 安全从格局 dict 里取名称：兼容字符串 / {格局名称}/{name}
  if (!p) return '';
  if (typeof p === 'string') return p;
  return p['格局名称'] || p.name || p['name'] || '';
}
function _plJxColor(jx) {
  if (jx === '吉' || jx === '大吉') return '#7ee2b8';
  if (jx === '中吉') return '#fbbf24';
  if (jx === '凶' || jx === '大凶') return '#ff6b6b';
  return '#9fb3d1';
}
function zrHitsBadgesHtml(zrHits) {
  // 2026-08-21 择日合参美格/凶格徽标：吉=绿✨ 凶=红⚠，悬停显示叙事+出处
  if (!zrHits || !zrHits.length) return '';
  return zrHits.map(function(h){
    var xiong = (h['结论'] === '凶');
    var col = xiong ? '#ff6b6b' : '#7ee2b8';
    var bg = xiong ? 'rgba(255,107,107,.08)' : 'rgba(126,226,184,.08)';
    var lbl = h['标签'] || h.id || '';
    var tip = (h['叙事'] || '') + (h['出处'] ? '　【' + h['出处'] + '】' : '');
    return '<span style="display:inline-block;margin:2px 4px 2px 0;padding:2px 9px;border-radius:10px;font-size:11.5px;font-weight:600;color:' + col + ';background:' + bg + ';border:1px solid ' + col + '66;cursor:help;" title="' + tip + '">' +
      (xiong ? '⚠' : '✨') + ' ' + lbl + ' <span style="opacity:.6;font-weight:400;">' + (h.id || '') + '</span></span>';
  }).join('');
}
function guliCardHtml(g) {
  // 2026-08-21 古例印证栏（项目核心：同课古例 → A 基调直迁 / B 占类桥 / C 应期重算）
  if (!g || !g.matched) return '';
  var s = '<div style="margin:8px 0;background:rgba(168,85,247,.06);border-radius:8px;padding:10px;border:1px solid #7c3aed;border-left:3px solid #a855f7;">';
  s += '<div style="font-size:13px;font-weight:700;color:#c4b5fd;margin-bottom:6px;">📜 古例印证（同课 ' + (g.cases||[]).length + ' 例 · 置信度 ' + (g['置信度']||'') + '）</div>';
  var caseTxt = (g.cases||[]).map(function(c){
    return c.day_ganzhi + '日' + (c.yue_jiang||'') + '将' + c.shichen + '时 ' + c.source + '·' + c.zhanlei + '占 ' +
      '<span style="color:' + ((c.label==='凶')?'#ff6b6b':'#7ee2b8') + ';">' + (c.label||'未详') + '</span>';
  }).join('　');
  if (caseTxt) s += '<div style="font-size:12px;color:#a78bfa;margin-bottom:6px;">🔑 ' + caseTxt + '</div>';
  if ((g['基调']||[]).length) {
    s += '<div style="font-size:12.5px;color:#e9d5ff;line-height:1.8;margin-bottom:4px;"><b>① 基调（课体/毕法直迁）：</b>' + g['基调'].join('<br>') + '</div>';
  }
  if ((g['变通']||[]).length) {
    s += '<div style="font-size:12.5px;color:#ddd6fe;line-height:1.8;margin-bottom:4px;"><b>② 变通（占类桥翻译）：</b>' + g['变通'].join('<br>') + '</div>';
  }
  if ((g['应期']||[]).length) {
    s += '<div style="font-size:12.5px;color:#fbcfe8;line-height:1.8;"><b>③ 应期（按主命重算）：</b>' + g['应期'].join('；') + '</div>';
  }
  s += '</div>';
  return s;
}
// ═════════ 类象链推演（2026-09-11 上线：课象→类神锚定→阴神链→现代象→收敛）═════════
// 纯叙事层参考（环境所断），不赋吉凶、不进评分链；数据源后端 result['chain_leixiang']
function _clEsc(s) {
  return String(s == null ? '' : s).replace(/[&<>"]/g, function(c){
    return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c];
  });
}
function chainLeixiangHtml(cl, dateStr, shichen) {
  if (!cl || cl.error) return '';
  var chains = cl['链'] || [], cands = cl['收敛候选'] || [];
  var matches = cl['推演匹配'] || [], xw = cl['行为风水'] || {}, qc = cl['七处'] || {};
  if (!chains.length && !cands.length && !matches.length) return '';
  var C_MAIN = '#22d3ee', C_TXT = '#e0f2fe', C_DIM = '#94a3b8';
  var h = '<div id="clBlock" style="margin:10px 0;background:rgba(14,165,233,.05);border-radius:8px;padding:10px;border:1px solid #0e7490;border-left:3px solid ' + C_MAIN + ';">';
  h += '<div style="font-size:13px;font-weight:700;color:#67e8f9;margin-bottom:6px;">🔗 类象链推演（现代叙事）' +
    (cl['占类'] ? '<span style="font-size:11px;color:' + C_DIM + ';font-weight:400;margin-left:6px;">占类：' + _clEsc(cl['占类']) + '</span>' : '') +
    '</div>';
  // 外应入参（用户填「起课时看到/发生了什么」，如 见狗→戌）
  h += '<div style="display:flex;gap:6px;align-items:center;margin-bottom:8px;">' +
    '<input id="clHint" type="text" placeholder="外应（可选）：起课时看到/发生了什么，如 戌 / 见狗 / 手机响" value="' + _clEsc(window._plDetailHint || '') + '" style="flex:1;min-width:150px;background:#1f1f3a;border:1px solid #155e75;color:#e2e8f0;border-radius:6px;padding:5px 8px;font-size:12px;">' +
    '<button onclick="plRefreshChain()" style="background:#0891b2;color:#fff;border:none;padding:6px 12px;border-radius:6px;cursor:pointer;font-size:12px;font-weight:600;">重新推演</button></div>';
  if (cl['叙事']) h += '<div style="font-size:12.5px;color:' + C_TXT + ';line-height:1.8;background:rgba(255,255,255,.04);border-radius:6px;padding:8px;margin-bottom:8px;">' + _clEsc(cl['叙事']) + '</div>';
  // 七处锚定（勾选=有值；划线=空）
  var QI = ['行年','本命','行命上神','日上神','支上神','三传','先锋门'], bits = [];
  for (var qi = 0; qi < QI.length; qi++) {
    var qk = QI[qi], qv = qc[qk];
    var qhit = !!(qv && (!Array.isArray(qv) || qv.length));
    var qtxt = Array.isArray(qv) ? qv.join('、') : (qv || '');
    bits.push('<span style="color:' + (qhit ? C_MAIN : '#4b5563') + ';border:1px solid ' + (qhit ? '#0e7490' : '#374151') + ';border-radius:4px;padding:0 6px;' + (qhit ? '' : 'text-decoration:line-through;') + '">' + qk + (qtxt ? ' ' + _clEsc(qtxt) : '') + '</span>');
  }
  h += '<div style="font-size:11px;color:' + C_DIM + ';margin-bottom:8px;line-height:2;"><b style="color:#8ea2ff;">七处锚定</b>　' + bits.join('　') + '</div>';
  // 阴神链（逐层展开）
  if (chains.length) {
    h += '<div style="font-size:11px;color:#8ea2ff;font-weight:600;margin-bottom:4px;">阴神链（逐层展开）</div>';
    for (var ci = 0; ci < chains.length; ci++) {
      var rows = (chains[ci]['链'] || []), segs = [];
      for (var ri = 0; ri < rows.length; ri++) {
        var r0 = rows[ri], hit = (r0['命中七处'] || []).length > 0;
        segs.push('<span style="' + (hit ? 'color:' + C_MAIN + ';font-weight:700;' : 'color:#cbd5e1;') + '">' +
          _clEsc(r0['地支'] || '') + (r0['天将'] ? '<span style="color:#fbbf24;font-size:10px;">乘' + _clEsc(r0['天将']) + '</span>' : '') +
          (r0['遁干'] ? '<span style="color:#94a3b8;font-size:10px;">遁' + _clEsc(r0['遁干']) + '</span>' : '') + '</span>');
      }
      h += '<div style="font-size:12px;color:#e2e8f0;background:rgba(255,255,255,.03);border-radius:6px;padding:5px 8px;margin-bottom:3px;line-height:1.9;">' +
        '<span style="font-size:10px;color:#7dd3fc;border:1px solid #0e7490;border-radius:4px;padding:0 5px;margin-right:6px;">' + _clEsc(chains[ci]['起点来源'] || '') + '</span>' +
        segs.join(' <span style="color:#475569;">→</span> ') + '</div>';
    }
  }
  // 收敛候选
  if (cands.length) {
    h += '<div style="font-size:11px;color:#8ea2ff;font-weight:600;margin:6px 0 4px;">收敛候选（按七处命中 + 证据强度）</div>';
    for (var di = 0; di < cands.length; di++) {
      var c0 = cands[di], xiangs = (c0['现代象'] || []).slice(0, 5), hz = (c0['命中七处'] || []);
      h += '<div style="font-size:12px;background:rgba(30,30,58,.6);border-radius:6px;padding:6px 8px;margin-bottom:3px;line-height:1.8;">' +
        '<b style="color:' + (hz.length ? '#7ee2b8' : '#e2e8f0') + ';">' + _clEsc(c0['地支'] || '') + '乘' + _clEsc(c0['天将'] || '') + '</b>' +
        (c0['遁干'] ? '<span style="color:#94a3b8;font-size:11px;">遁' + _clEsc(c0['遁干']) + '</span>' : '') +
        (c0['坐宫'] ? '<span style="color:#64748b;font-size:11px;">（坐' + _clEsc(c0['坐宫']) + '）</span>' : '') +
        (c0['空亡'] ? '<span style="color:#ff6b6b;font-size:10px;">⚠空</span>' : '') +
        (hz.length ? '<span style="font-size:10px;color:#67e8f9;margin-left:6px;">命中七处：' + _clEsc(hz.join('、')) + '</span>' : '') +
        (xiangs.length ? '<div style="color:#fde68a;margin-top:2px;">候选象：' + _clEsc(xiangs.join('、')) + '</div>' : '') + '</div>';
    }
  }
  // 组合推演（多要素命中）
  if (matches.length) {
    h += '<div style="font-size:11px;color:#8ea2ff;font-weight:600;margin:6px 0 4px;">组合推演（多要素命中）</div><div style="line-height:2;">';
    for (var mi = 0; mi < matches.length; mi++) {
      var m0 = matches[mi], lv = m0['等级'] || '';
      var lcol = (lv === '已验证') ? '#7ee2b8' : ((lv === '待验证') ? '#fbbf24' : '#9fb3d1');
      var mk = (lv === '待验证') ? '△' : ((lv === '已验证') ? '✓' : '');
      h += '<span title="' + _clEsc('命中要素：' + (m0['命中要素'] || []).join('、') + (m0['备注'] ? '　' + m0['备注'] : '')) + '" style="display:inline-block;margin:2px 4px 2px 0;padding:2px 8px;border-radius:10px;font-size:11.5px;color:' + lcol + ';background:' + lcol + '1a;border:1px solid ' + lcol + '66;cursor:help;">' + mk + ' ' + _clEsc(m0['事物'] || '') + ' <span style="opacity:.65;font-weight:400;">' + _clEsc(m0['命中率'] || '') + '</span></span>';
    }
    h += '</div>';
  }
  // 行为风水（仅命中七处节点给解）
  var sug = (xw['建议'] || []);
  if (sug.length) {
    h += '<div style="font-size:11px;color:#8ea2ff;font-weight:600;margin:6px 0 4px;">行为风水（按七处给解）</div>';
    for (var si = 0; si < sug.length; si++) {
      var s0 = sug[si];
      h += '<div style="font-size:12px;color:#d1fae5;background:rgba(16,185,129,.06);border:1px solid #14532d;border-radius:6px;padding:6px 8px;margin-bottom:3px;line-height:1.8;">' +
        '<b style="color:#6ee7b7;">' + _clEsc(s0['病位'] || '') + '</b>' +
        ((s0['状态'] || []).length ? '　<span style="font-size:10px;color:#fbbf24;">' + _clEsc(s0['状态'].join('/')) + '</span>' : '') +
        (s0['方位参考'] ? '　<span style="font-size:10px;color:#94a3b8;">方位：' + _clEsc(s0['方位参考']) + '</span>' : '');
      var gs = s0['通用解法'] || [];
      for (var gi = 0; gi < gs.length; gi++) h += '<div style="color:#a7f3d0;">▸ ' + _clEsc(gs[gi]) + '</div>';
      if (s0['原例参考']) h += '<div style="color:#6ee7b7;font-size:11px;">▸ 原例：' + _clEsc(s0['原例参考']) + (s0['出处'] ? '（' + _clEsc(s0['出处']) + '）' : '') + '</div>';
      h += '</div>';
    }
  }
  var tz = (xw['通则'] || []);
  if (tz.length) h += '<div style="font-size:11px;color:' + C_DIM + ';line-height:1.8;margin-top:2px;">通则：' + _clEsc(tz.join('；')) + '</div>';
  h += '<div style="font-size:10.5px;color:#64748b;margin-top:6px;">⚠ ' + _clEsc(cl['边界'] || '纯叙事层参考，不赋吉凶、不进评分链') + '（赵师原话：其他环境不能这么断）</div>';
  h += '</div>';
  return h;
}
// 外应重推：仅刷新类象链区块（带 hint_zhi 重新请求 analyze）
function plRefreshChain() {
  if (!_plDetailData) return;
  var el = document.getElementById('clBlock');
  var hint = ((document.getElementById('clHint') || {}).value || '').trim();
  window._plDetailHint = hint;
  var dt = _plDetailData;
  var url = '/api/zeri/analyze?date=' + encodeURIComponent(dt.date) + '&mountain=' + encodeURIComponent(dt.mountain) +
    '&shichen=' + encodeURIComponent(dt.shichen) + '&liupai=liuren,doushou,yanqin' +
    (hint ? '&hint_zhi=' + encodeURIComponent(hint) : '');
  if (el) el.innerHTML = '<div style="color:#9fb3d1;padding:8px;">⏳ 正在按外应重新推演…</div>';
  fetch(url).then(function(r){ return r.json(); }).then(function(d){
    if (d.error) { if (el) el.innerHTML = '<div style="color:#ff6b6b;padding:8px;">推演失败：' + _clEsc(d.error) + '</div>'; return; }
    dt.detail = d; window._zeriData = d;
    var tmp = document.createElement('div');
    tmp.innerHTML = chainLeixiangHtml(d.chain_leixiang, dt.date, dt.shichen);
    var fresh = tmp.firstChild;
    if (fresh && el && el.parentNode) el.parentNode.replaceChild(fresh, el);
  }).catch(function(e){
    if (el) el.innerHTML = '<div style="color:#ff6b6b;padding:8px;">请求异常：' + _clEsc(e) + '</div>';
  });
}
function plRenderDetail(d, dateStr, shichen, it) {
  var sizhu = d.sizhu || {};
  var yq = d.yanqin_full || {};
  var dh = d.doushou_full || {};
  var html = '<div style="background:#2a2a4a;border-radius:8px;padding:14px;border-top:2px solid #667eea;">';
  // 三流派课格弹窗数据源（合并自指定日分析：六壬/斗首/演禽 完整课格弹出查看）
  window._zeriData = d;
  html += '<div style="font-size:14px;font-weight:700;color:#fff;margin-bottom:8px;">📖 ' + dateStr + ' ' + shichen + '时 · 完整课格</div>';
  // 四柱 + 总分
  html += '<div style="font-size:12px;color:#c7d2fe;margin-bottom:8px;">四柱：' + (sizhu['年']||'') + ' ' + (sizhu['月']||'') + ' ' + (sizhu['日']||'') + ' ' + (sizhu['时']||'') + '　｜　综合评分 <b style="color:#fbbf24;">' + (d.score||'') + '</b>（' + (d.grade||'') + '）</div>';
  // 2026-09-06 择日类型类神吉应（安葬/作灶…事件类神入课：徽标 + 完整叙事）
  if (d.leishen_detail && d.leishen_detail.end) {
    var _ld2 = d.leishen_detail;
    var _c2 = {'吉':'#7ee2b8','凶':'#ff6b6b','平':'#fbbf24'}[_ld2.end] || '#999';
    var _i2 = {'吉':'✅','凶':'❌','平':'➖'}[_ld2.end] || '';
    var _ls2 = ((_ld2.zhi_list||[]).join('、') || '—');
    html += '<div style="margin:8px 0;padding:8px 12px;background:rgba(255,255,255,.04);border:1px solid ' + _c2 + '55;border-left:3px solid ' + _c2 + ';border-radius:8px;font-size:12.5px;">' +
      '<b style="color:' + _c2 + ';">' + _i2 + ' 类神吉应（' + (_ld2.zeri_type||'') + '）' + _ld2.end + '</b>　' +
      '<span style="color:#9fb3d1;">类神：' + _ls2 + '</span><br>' +
      '<span style="color:#e2e8f0;line-height:1.7;">' + (_ld2.narr||'') + '</span></div>';
  }
  // 汇总卡：综合得分 + 三流派对照 + 杀师日警示（合并自指定日分析）
  html += _zeriSummary(d);
  // 三流派课格弹窗按钮（合并自指定日分析；点击弹出完整课格）
  html += '<div style="display:flex;gap:12px;flex-wrap:wrap;margin-top:14px;">'+
    '<button onclick="openZeriModal(\'liuren\')" style="flex:1;min-width:180px;background:#2a2a4a;border:1px solid #4a3a6a;border-top:3px solid #8b5cf6;color:#c4b5fd;border-radius:10px;padding:12px;cursor:pointer;font-size:14px;font-weight:600;">🔮 六壬课格 <span style="display:block;font-size:12px;color:#888;font-weight:400;margin-top:2px;">' + (d.score||'') + '分 · ' + (d.grade||'') + '</span></button>'+
    (d.doushou_full && !d.doushou_full.error ? '<button onclick="openZeriModal(\'doushou\')" style="flex:1;min-width:180px;background:#2a2a4a;border:1px solid #4a3a2a;border-top:3px solid #f59e0b;color:#ffd28a;border-radius:10px;padding:12px;cursor:pointer;font-size:14px;font-weight:600;">🔥 斗首课格 <span style="display:block;font-size:12px;color:#888;font-weight:400;margin-top:2px;">' + d.doushou_full.score + '分 · ' + (d.doushou_full.grade||'') + '</span></button>' : '')+
    (d.yanqin_full && !d.yanqin_full.error ? '<button onclick="openZeriModal(\'yanqin\')" style="flex:1;min-width:180px;background:#2a2a4a;border:1px solid #2a4a3a;border-top:3px solid #10b981;color:#7ee2b8;border-radius:10px;padding:12px;cursor:pointer;font-size:14px;font-weight:600;">🦅 演禽课格 <span style="display:block;font-size:12px;color:#888;font-weight:400;margin-top:2px;">' + d.yanqin_full.score + '分</span></button>' : '')+
    '</div>';
  // 综合批语栏（斗首/演禽/六壬 → 文言主批语 + 白话括注，普通人看得懂）
  var zp = d.zonghe_piyu || {};
  // 古籍合参警示层（2026-08-19：后端 hecan 字段，警示/佐证/择日合参三栏）
  // 应期结构化卡片（2026-08-20：粒度徽标+法门+文本）
  if (d.yingqi_struct && d.yingqi_struct.length) {
    var GRAN_COL = {'日': '#22c55e', '旬': '#a78bfa', '月': '#60a5fa', '年': '#f59e0b', '速迟': '#f472b6', '方位': '#34d399'};
    html += '<div style="margin:8px 0;padding:8px 10px;background:rgba(255,255,255,.03);border:1px solid #3a3a6a;border-radius:8px;">';
    html += '<div style="font-size:13px;font-weight:600;color:#8ea2ff;margin-bottom:6px;">⏳ 应期（何时应验）</div>';
    for (var qi = 0; qi < d.yingqi_struct.length; qi++) {
      var it = d.yingqi_struct[qi] || {};
      var gc = GRAN_COL[it.粒度] || '#94a3b8';
      html += '<div style="margin:4px 0;padding:5px 8px;background:rgba(30,30,58,.6);border-radius:6px;display:flex;gap:8px;align-items:flex-start;flex-wrap:wrap;">';
      html += '<span style="flex:none;font-size:11px;color:#fff;background:' + gc + ';border-radius:4px;padding:1px 6px;">' + (it.粒度 || '') + '</span>';
      html += '<span style="flex:none;font-size:12px;color:#c4b5fd;">' + (it.法 || '') + '</span>';
      html += '<span style="font-size:12px;color:#e0e0e0;line-height:1.55;min-width:0;">' + (it.文本 || '') + '</span>';
      html += '</div>';
    }
    html += '</div>';
  }
  var hc = d.hecan || {};
  var warns = hc['警告'] || [];
  var proofs = hc['佐证'] || [];
  var zrn = (hc.zeri_rules || {}).narr || '';
  if (warns.length) {
    html += '<div style="margin:8px 0;background:rgba(255,160,60,.06);border-radius:8px;padding:10px;border:1px solid #b45309;border-left:3px solid #f59e0b;">';
    html += '<div style="font-size:13px;font-weight:700;color:#fbbf24;margin-bottom:6px;">⚠ 古籍合参警示</div>';
    for (var wi=0; wi<warns.length; wi++) html += '<div style="font-size:12.5px;color:#fde68a;line-height:1.8;">· ' + warns[wi] + '</div>';
    html += '</div>';
  }
  if (proofs.length) {
    html += '<div style="margin:8px 0;background:rgba(34,197,94,.05);border-radius:8px;padding:10px;border:1px solid #15803d;border-left:3px solid #22c55e;">';
    html += '<div style="font-size:13px;font-weight:700;color:#4ade80;margin-bottom:6px;">✅ 古籍合参佐证</div>';
    for (var pi=0; pi<proofs.length; pi++) html += '<div style="font-size:12.5px;color:#bbf7d0;line-height:1.8;">· ' + proofs[pi] + '</div>';
    html += '</div>';
  }
  var zrHits = (hc.zeri_rules || {}).hits || [];
  var zrBadges = zrHitsBadgesHtml(zrHits);
  if (zrBadges) {
    html += '<div style="margin:8px 0;background:rgba(99,102,241,.05);border-radius:8px;padding:10px;border:1px solid #4f46e5;border-left:3px solid #818cf8;">';
    html += '<div style="font-size:13px;font-weight:700;color:#8ea2ff;margin-bottom:6px;">🏷️ 择日合参格局（美格徽标 ' + zrHits.length + '）</div>';
    html += '<div style="line-height:1.9;">' + zrBadges + '</div>';
    html += '</div>';
  }
  if (zrn) {
    html += '<div style="margin:8px 0;background:rgba(99,102,241,.05);border-radius:8px;padding:10px;border:1px solid #4f46e5;border-left:3px solid #818cf8;">';
    html += '<div style="font-size:12.5px;color:#c7d2fe;line-height:1.8;">🔍 ' + zrn + '</div>';
    html += '</div>';
  }
  html += guliCardHtml(hc.guli);
  if (zp.wen) {
    html += '<div style="margin:10px 0;background:rgba(255,255,255,.04);border-radius:8px;padding:10px;border:1px solid #3a3a6a;border-left:3px solid #a855f7;">';
    html += '<div style="font-size:13px;font-weight:700;color:#c4b5fd;margin-bottom:6px;">📜 综合批语</div>';
    html += '<div style="font-size:13px;color:#e2e8f0;line-height:1.9;">' + zp.wen + '</div>';
    if (zp.bai) html += '<div style="font-size:12px;color:#94a3b8;line-height:1.8;margin-top:6px;">白话：' + zp.bai + '</div>';
    html += '</div>';
  }
  // 四课三传排盘（仅点击课日时显示）
  if (d.sike && d.sike.length) {
    html += '<div style="margin:10px 0;background:rgba(255,255,255,.03);border-radius:8px;padding:10px;border:1px solid #3a3a6a;">';
    // 规范六壬排盘（仿原 qkShow 风格：四课 2×2 + 课体大字 + 三传方格 + 课格 + 毕法赋）
    var sc = d.sanchuan || {};
    var sc3 = sc['三传'] || [];
    var tj3 = sc['三传天将'] || [];
    var gz3 = sc['三传干支'] || [];
    var lq3 = sc['三传六亲'] || [];
    var kw3 = sc['三传空亡'] || [];
    var names = ['初传','中传','末传'];
    var keti = sc['课体'] || '';
    var kg = sc['课格列表'] || [];
    var bf = sc['毕法赋命中'] || [];

    // ① 传统六壬排盘（天盘 | 四课 | 三传 横向一行，仿传统排盘样式）
    var sk = d.sike || [];
    var tdp2 = d.tiandi_pan || {};
    var tjm2 = d.tianjiang_map || {};
    var yj2 = d.yuejiang || '';

    // 课体（紧凑横标，置于横排区上方）
    if (keti) html += '<div style="font-size:12px;margin-bottom:5px;"><b style="color:#a78bfa;">课体：</b><span style="color:#fff;">' + keti + '</span></div>';

    // 横向一行：天盘 | 四课 | 三传
    html += '<div style="display:flex;gap:10px;flex-wrap:wrap;align-items:flex-start;margin-bottom:10px;">';

    // A. 天盘环宫图（4×4 环形，四角空；固定地盘宫位：巳午未申/辰·酉/卯·戌/寅丑子亥）
    if (tdp2 && Object.keys(tdp2).length) {
      html += '<div style="flex:1.1 1 0;min-width:190px;">';
      html += '<div style="margin-bottom:3px;font-size:10px;color:#8ea2ff;font-weight:600;">天盘（月将' + (yj2||'--') + '加' + (d.shichen||'--') + '时）</div>';
      html += '<div style="display:grid;grid-template-columns:repeat(4,1fr);gap:2px;">';
      var order = [['巳','午','未','申'],['辰','','','酉'],['卯','','','戌'],['寅','丑','子','亥']];
      for (var rr=0; rr<4; rr++) {
        for (var cc=0; cc<4; cc++) {
          var diZhi = order[rr][cc];
          if (!diZhi) { html += '<div></div>'; continue; }
          var tiZhi = tdp2[diZhi] || '';
          var tjName = tjm2[tiZhi] || '';
          html += '<div style="text-align:center;background:rgba(255,255,255,.03);border:1px solid #2a2f4a;border-radius:4px;padding:3px 1px;">' +
            '<div style="font-size:13px;color:#fff;font-weight:700;line-height:1.2;">' + tiZhi + '</div>' +
            '<div style="font-size:9px;color:#fbbf24;line-height:1.2;">' + tjName + '</div>' +
            '<div style="font-size:8px;color:#667;line-height:1.1;">' + diZhi + '</div>' +
          '</div>';
        }
      }
      html += '</div></div>';
    }

    // B. 四课传统排（从右到左：第一二三四课；每课 天将/上神/下神 三行）
    if (sk.length) {
      html += '<div style="flex:1.1 1 0;min-width:190px;">';
      html += '<div style="margin-bottom:3px;font-size:10px;color:#8ea2ff;font-weight:600;">四课（右起第一课）</div>';
      html += '<div style="display:grid;grid-template-columns:repeat(4,1fr);gap:2px;">';
      for (var kj=0; kj<4; kj++) {
        var ke = sk[3-kj] || [];
        var up = ke[1]||''; var dn = ke[2]||''; var tj = ke[3]||'';
        html += '<div style="text-align:center;background:rgba(255,255,255,.03);border:1px solid #2a2f4a;border-radius:4px;padding:3px 1px;">' +
          '<div style="font-size:9px;color:#fbbf24;line-height:1.3;">' + tj + '</div>' +
          '<div style="font-size:14px;color:#fff;font-weight:700;line-height:1.2;">' + up + '</div>' +
          '<div style="font-size:12px;color:#d7def0;line-height:1.2;">' + dn + '</div>' +
        '</div>';
      }
      html += '</div></div>';
    }

    // D. 三传传统排（竖排三行：传名 六亲 干支 天将）
    if (sc3.length) {
      html += '<div style="flex:0.8 1 0;min-width:130px;">';
      html += '<div style="margin-bottom:3px;font-size:10px;color:#8ea2ff;font-weight:600;">三传</div>';
      for (var ci=0; ci<3; ci++) {
        var chuan = sc3[ci] || '';
        var lq = lq3[ci] || '';
        var gz = gz3[ci] || chuan;
        var tj2 = tj3[ci] || '';
        var kw = kw3[ci] || '';
        html += '<div style="display:flex;align-items:center;gap:8px;background:rgba(255,255,255,.03);border:1px solid #2a2f4a;border-radius:4px;padding:4px 8px;margin-bottom:3px;">' +
          '<span style="font-size:10px;color:#94a3b8;min-width:32px;">' + names[ci] + '</span>' +
          '<span style="font-size:11px;color:#7ee2b8;min-width:26px;">' + lq + '</span>' +
          '<span style="font-size:14px;color:#fff;font-weight:700;flex:1;">' + gz + '</span>' +
          '<span style="font-size:11px;color:#fbbf24;">' + tj2 + '</span>' +
          (kw ? '<span style="font-size:9px;color:#ff6b6b;">⚠空</span>' : '') +
        '</div>';
      }
      html += '</div>';
    }

    html += '</div>';  // 结束横向一行

    // ④ 课格（用项目课格判断引擎 kege_details 的吉凶着色 + 断语 tooltip）
    if (kg.length) {
      var kd = sc['课格详情'] || {};
      html += '<div style="margin-bottom:6px;font-size:12px;color:#9fb3d1;">课格：' + kg.map(function(k){
        var nm = (typeof k==='string') ? k : (k['格局名称']||k['name']||'');
        var info = (typeof k==='object' && k) ? k : (kd[nm] || {});
        var jx = info['吉凶'] || '';
        var dy = info['断语'] || info['定义'] || '';
        var col = (jx==='凶'||jx==='大凶') ? '#ff6b6b' : ((jx==='吉'||jx==='大吉') ? '#7ee2b8' : '#e0b36a');
        return '<b style="color:' + col + ';" title="' + (jx?('吉凶：'+jx+'　'):'') + dy + '">' + nm + '</b>';
      }).join(' · ') + '</div>';
    }
    // ⑤ 知识库断语（KeKeDuanyu 仪度评分：上吉/中吉/平 + 课传美格）
    if (d.yidu && d.yidu.score != null) {
      var yd = d.yidu;
      var ycol = yd.score >= 60 ? '#7ee2b8' : (yd.score >= 40 ? '#e0b36a' : '#ff6b6b');
      html += '<div style="margin-bottom:6px;font-size:12px;color:#9fb3d1;">📖 仪度断语：<b style="color:' + ycol + ';">' + yd.eval + '</b>（评分 <b style="color:#fbbf24;">' + yd.score + '</b>）' +
        (yd.ke_chuan_mei && yd.ke_chuan_mei.length ? '　课传美格：' + yd.ke_chuan_mei.join('、') : '') + '</div>';
      if (yd.wujue && Object.keys(yd.wujue).length) {
        var wj = Object.keys(yd.wujue).map(function(k){ return k + ' <b style="color:#fbbf24;">+' + yd.wujue[k] + '</b>'; }).join('　');
        html += '<div style="margin-bottom:6px;font-size:11px;color:#9fb3d1;">　五大要诀：' + wj + '</div>';
      }
    }
    // ⑥ 毕法赋（金黄 + 断法依据，来自 judge_bifa 引擎）
    if (bf.length || (d.bifa_judged && d.bifa_judged['匹配法句'] && d.bifa_judged['匹配法句'].length)) {
      html += '<div style="font-size:12px;color:#9fb3d1;">毕法赋：' + bf.map(function(b){ return '<b style="color:#fbbf24;">' + b + '</b>'; }).join(' · ') + '</div>';
      html += bifaJudgedHtml(d);
      // 毕法赋占类过滤（2026-08-17 精细版）：展示按当前占类保留的断语（剔除的划线标注）
      if (d.bifa_filtered && d.bifa_filtered.kept && d.bifa_filtered.dropped && d.bifa_filtered.dropped.length) {
        var _keptTxt = d.bifa_filtered.kept.length ? d.bifa_filtered.kept.join('、') : '（无专属断语，仅通用）';
        html += '<div style="font-size:11px;color:#8b9bb8;">　已按占类「' + d.bifa_filtered.zhanlei + '」过滤：保留 <b style="color:#7ee2b8;">' + _keptTxt + '</b>　剔除 <span style="color:#5a6b8c;">' +
                d.bifa_filtered.dropped.map(function(x){return '<span style="text-decoration:line-through;">' + x + '</span>';}).join('、') + '</span></div>';
      }
    }
    html += '</div>';
  }
  // 类象链推演（2026-09-11 上线：纯叙事层，紧跟排盘；外应入参在区块内）
  html += chainLeixiangHtml(d.chain_leixiang, dateStr, shichen);
  // 列表项关键信息（课体 / 四柱禄马贵人 / 仪度评分 —— 与批量择日列表一致）
  if (it) {
    var extra = [];
    if (it.keti) extra.push('课体：<b style="color:#a78bfa;">' + it.keti + '</b>');
    if (it.luma_guiren) {
      var lg = it.luma_guiren;
      var marks = [['年',lg.nian_qualified],['月',lg.yue_qualified],['日',lg.ri_qualified],['时',lg.shi_qualified]]
        .map(function(p){ return p[0] + (p[1] ? '<b style="color:#7ee2b8;">✓</b>' : '<span style="color:#666;">✗</span>'); }).join('');
      extra.push('四柱禄马贵人(到山到向)：' + marks + '　三传禄马' + (lg.sanchuan_luma||0) + '个');
    }
    if (it.yidu_score != null && it.yidu_score > 0) extra.push('仪度评分：<b style="color:#fbbf24;">' + it.yidu_score + '</b>(' + (it.yidu_eval||'') + ')');
    if (it.liuxiang) extra.push('月柱六相：<b style="color:#7ee2b8;">' + it.liuxiang + '</b>');
    if (it.nianming && it.nianming.used) extra.push('主命：' + plNmTxt(it.nianming));
    if (extra.length) html += '<div style="font-size:12px;color:#9fb3d1;margin-bottom:8px;background:rgba(255,255,255,.04);border-radius:6px;padding:8px;">' + extra.join('　') + '</div>';
  }
  // 禄马贵人到山到向
  if (d.daoshan_daoxiang) {
    html += '<div style="font-size:12px;color:#9fb3d1;margin-bottom:6px;">禄马贵人：' + plDsdxTxt(d.daoshan_daoxiang) + '</div>';
  }
  // 太阳躔度·合方之法（sun_chanhe 逐柱明细；《仪度六壬择日要诀》"先查/合方之法"：天体躔合加临到山向）
  var _scd = (d.luma_detail && d.luma_detail.sun_chanhe_details) || null;
  if (_scd) {
    var _scP = ['年','月','日','时'], _scRows = [];
    for (var pi=0; pi<_scP.length; pi++) {
      var pk = _scP[pi], r = _scd[pk]; if (!r) continue;
      var _its = (r.items||[]).map(function(x){
        var m2 = (x.to_shan ? '到山' : '') + (x.to_xiang ? '照向' : '');
        return '<span style="' + (m2 ? 'color:#7ee2b8;font-weight:600;' : '') + '">' + x.type + x.zhi + '(' + (x.xiu||'') + ')→' + x.daoshan_zhi + (m2 ? ' <b>'+m2+'</b>' : '') + '</span>';
      }).join('　');
      var _hit = r.qualified ? '✅' : '';
      _scRows.push('<div style="font-size:11px;color:#8b9bb8;line-height:1.7;">' + _hit + ' ' + pk + '柱：' + (_its || '无禄马贵') + '</div>');
    }
    if (_scRows.length) {
      var _scB = (d.luma_detail && d.luma_detail.sun_chanhe_bonus) ? '　<b style="color:#fbbf24;">+'+d.luma_detail.sun_chanhe_bonus+'分</b>' : '';
      html += '<div style="font-size:11px;color:#6b7f9f;margin-bottom:6px;background:rgba(255,255,255,.03);border-radius:6px;padding:6px 8px;">' +
        '<b style="color:#a78bfa;">☀️ 太阳躔度·合方之法</b>（天体躔合到山/向）' + _scB + '<br/>' + _scRows.join('') + '</div>';
    }
  }
  // 日月合塑/日月对望（《仪度六壬择日要诀》吊天星第二课："日月两轮照乾坤"；2026-09-05 步骤2）
  var _ryd = (d.luma_detail && d.luma_detail.riyue_hesu_details) || null;
  var _ryT = (d.luma_detail && d.luma_detail.riyue_hesu_type) || '';
  var _ryB = (d.luma_detail && d.luma_detail.riyue_hesu_bonus) || 0;
  if (_ryd && _ryT !== '无' && _ryT !== '') {
    var _ryIcon = (_ryT === '合塑') ? '🌞🌙' : '🌓';
    var _ryColor = (_ryT === '合塑') ? '#f97316' : '#38bdf8';
    var _ryRows = [];
    var _ryDesc = _ryd.description || '';
    if ((_ryd.hits || []).length) {
      _ryRows.push('<div style="font-size:11px;color:#7ee2b8;font-weight:600;">' + _ryd.hits.join('；') + '</div>');
    }
    html += '<div style="font-size:11px;color:#6b7f9f;margin-bottom:6px;background:rgba(255,255,255,.04);border-radius:6px;padding:6px 8px;border:1px solid ' + _ryColor + '55;">' +
      '<b style="color:' + _ryColor + ';">' + _ryIcon + ' 日月' + _ryT + '</b>（日月到山向·福力最巨大）　<b style="color:#fbbf24;">+'+_ryB+'分</b><br/>' +
      '<div style="font-size:11px;color:#8b9bb8;line-height:1.7;">' + (_ryDesc || '') + '</div>' + _ryRows.join('') + '</div>';
  }
  // 斗首（含具名吉格）
  if (dh && !dh.error) {
    var dsPat = (dh.patterns||[]).map(function(p){
      return '<b style="color:' + _plJxColor(p['吉凶']) + ';" title="' + (p['描述']||'') + '　条件：' + (p['条件']||'') + '">' + _plName(p) + '</b>';
    }).join('、');
    html += '<div style="font-size:12px;color:#9fb3d1;margin-bottom:6px;">斗首：评分 <b style="color:#fbbf24;">' + (dh.score||'') + '</b>（' + (dh.grade||'') + '）' +
      (dsPat ? '　具名吉格：' + dsPat : '') + '</div>';
  }
  // 加分项明细（2026-09-05：统一口径 总分=禄马贵人到山到向骨架 + 加分项；四柱结构/本命/课体/演禽等逐项）
  var _mp = d.matched_patterns || [];
  if (_mp.length) {
    html += '<div style="font-size:11px;color:#6b7f9f;margin-bottom:6px;background:rgba(255,255,255,.03);border-radius:6px;padding:6px 8px;">' +
      '<b style="color:#a78bfa;">➕ 加分项明细</b>（<b style="color:#fbbf24;">' + (d.bonus != null ? d.bonus : '') + '</b>分 · ' + _mp.length + ' 项）<br/>' +
      '<div style="display:flex;flex-wrap:wrap;gap:4px;margin-top:4px;line-height:1.8;">' +
      _mp.map(function(x){
        var _col = x.indexOf('+') === 0 ? '#7ee2b8' : (x.indexOf('-') === 0 ? '#f87171' : '#9fb3d1');
        return '<span style="color:' + _col + ';background:rgba(255,255,255,.05);border-radius:4px;padding:0 6px;">' + x + '</span>';
      }).join('') + '</div></div>';
  }
  // 四柱结构格局（天地同流/天元一气/三朋/五常/秀气/三合/三奇等；2026-09-05 接入）
  var _szp = d.sizhu_patterns || [];
  if (_szp.length) {
    html += '<div style="font-size:11px;color:#6b7f9f;margin-bottom:6px;background:rgba(255,255,255,.03);border-radius:6px;padding:6px 8px;">' +
      '<b style="color:#a78bfa;">🏯 斗首四柱结构</b>' + _szp.map(function(p){
        var _jc = (p['吉凶'] === '大吉') ? '#7ee2b8' : '#9fb3d1';
        return '<span style="color:' + _jc + ';" title="' + (p['条件']||'') + '">' + p['格局名称'] + '</span>';
      }).join('　') + '</div>';
  }
  // 演禽窃要（《要诀》秘传：坐山宿 + 三传宿生克/到山/高禽比旺；无加分项不显示）
  var _yqd = d.yanqin_detail || {};
  if (_yqd && (_yqd.shan_xiu || ((_yqd.hits||[]).length))) {
    var _yqHits = (_yqd.hits||[]).map(function(h){
      var _c = h.relation === '到山' ? '#7ee2b8' : (h.relation === '相生' ? '#38bdf8' : '#9fb3d1');
      return '<span style="color:' + _c + ';">' + h.position + h.zhi + '(' + (h.xiu||'') + ')' + (h.wx||'') + h.relation + '</span>';
    }).join('　');
    var _yqPo = _yqd.po_gong && _yqd.po_gong.吉凶 ? ('　日禽泊' + (_yqd.po_gong.宫||'') + '宫' + (_yqd.po_gong.吉凶==='吉'?'得地':'失地')) : '';
    html += '<div style="font-size:11px;color:#6b7f9f;margin-bottom:6px;background:rgba(255,255,255,.03);border-radius:6px;padding:6px 8px;">' +
      '<b style="color:#a78bfa;">🦅 演禽窃要</b>　坐山宿 <b style="color:#fbbf24;">' + (_yqd.shan_xiu||'') + '</b>' + (_yqd.shan_wx||'') +
      (_yqHits ? '<br/>' + _yqHits : '') + (_yqPo || '') + '</div>';
  }
  // 演禽
  if (yq && !yq.error) {
    var sp = yq.patterns || [];
    var named = sp.filter(function(p){ return ['锁泊具名格','演禽飞伏','演禽组合贵格'].indexOf(p['类别']) >= 0; });
    html += '<div style="font-size:12px;color:#9fb3d1;margin-bottom:6px;">演禽：评分 <b style="color:#fbbf24;">' + (yq.score||'') + '</b>' +
      (named.length ? '　具名/飞伏格：' + named.map(function(p){ return '<b style="color:' + _plJxColor(p['吉凶']) + ';">' + _plName(p) + '</b>'; }).join('、') : '') + '</div>';
  }
  // 断语摘要
  if (d.summary) {
    html += '<div style="font-size:12px;color:#e0e0e0;background:rgba(255,255,255,.04);border-radius:6px;padding:8px;margin-top:6px;">' + d.summary + '</div>';
  }
  // 案例回填（合并自指定日分析：结局导向记录实际结果，积累各类型自语料）
  var _ztType = d.zetiri_type || (document.getElementById('plType') ? document.getElementById('plType').value : '');
  window._zeriFeedback = {
    date: dateStr, mountain: d.mountain || mountain, shichen: shichen,
    zetiri_type: _ztType,
    zhanlei: TYPE_TO_ZHANLEI[_ztType] || '其他',
    ben_ming: (document.getElementById('plBenMing') ? document.getElementById('plBenMing').value : ''),
    lailong: (document.getElementById('plLailong') ? document.getElementById('plLailong').value : '')
  };
  html += '<div style="margin-top:10px;background:rgba(16,185,129,.06);border:1px dashed #2a5a4a;border-radius:8px;padding:10px;">' +
    '<div style="font-size:12px;font-weight:700;color:#7ee2b8;margin-bottom:6px;">📝 案例回填（积累自语料）</div>' +
    '<div style="font-size:11px;color:#94a3b8;margin-bottom:8px;line-height:1.6;">按<b>最终实际结果</b>填（事情应验后），勿按当时判断填；填得越多，引擎越懂这类事。</div>' +
    '<div style="display:flex;gap:8px;align-items:center;flex-wrap:wrap;">' +
    '<select id="fbLabel" style="background:#1f1f3a;border:1px solid #2a5a4a;color:#7ee2b8;border-radius:6px;padding:5px 8px;font-size:12px;">' +
    '<option value="">选择结果</option><option value="吉">吉（顺利/应验）</option><option value="凶">凶（不顺/破败）</option><option value="平">平（无吉无凶）</option></select>' +
    '<input id="fbNote" type="text" placeholder="备注（可选）：如 提车次日追尾 / 入学分班顺利" style="flex:1;min-width:160px;background:#1f1f3a;border:1px solid #2a4a5a;color:#e2e8f0;border-radius:6px;padding:5px 8px;font-size:12px;">' +
    '<button onclick="zeriFeedbackSubmit()" style="background:#10b981;color:#fff;border:none;padding:6px 14px;border-radius:6px;cursor:pointer;font-size:12px;font-weight:600;">提交记录</button>' +
    '<span id="fbStatus" style="font-size:11px;color:#7ee2b8;"></span></div></div>';
  // 导出文书（套用完美模板.docx）
  html += '<div style="margin-top:12px;text-align:right;border-top:1px dashed #3a3a6a;padding-top:10px;">' +
    '<button class="pl-export" onclick="plExportWenshu()" style="background:linear-gradient(135deg,#a855f7,#7c3aed);">📜 导出文书（完美模板）</button>' +
    '</div>';
  html += '</div>';
  return html;
}
function plExportDocx() { plExport('docx'); }
function plExportPptx() { plExport('pptx'); }
function plExport(kind) {
  if (!_plResults || !_plResults.length) { alert('暂无吉日列表可导出'); return; }
  var type = document.getElementById('plType').value;
  var mountain = document.getElementById('plMountain').value;
  var ext = kind === 'pptx' ? 'pptx' : 'docx';
  fetch('/api/export/' + ext, {
    method: 'POST', headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({ title: '仪度六壬择日吉期列表', zetiri_type: type, mountain: mountain, items: _plResults })
  }).then(function(r){
    if (!r.ok) return r.json().then(function(d){ throw new Error(d.error || '导出失败'); });
    var cd = r.headers.get('Content-Disposition') || '';
    // 优先取 RFC 5987 的 filename*=UTF-8''…（中文文件名），否则回退 filename=（ASCII 兜底）
    var mStar = cd.match(/filename\*=UTF-8''([^;]*)/i);
    var fname;
    if (mStar) {
      fname = decodeURIComponent(mStar[1].replace(/['"]/g, ''));
    } else {
      var m = cd.match(/filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/);
      fname = m ? m[1].replace(/['"]/g, '') : ('仪度六壬择日_' + type + '.' + ext);
    }
    return r.blob().then(function(blob){ return { blob: blob, fname: fname }; });
  }).then(function(o){
    var a = document.createElement('a');
    a.href = URL.createObjectURL(o.blob);
    a.download = o.fname;
    document.body.appendChild(a); a.click(); a.remove();
    setTimeout(function(){ URL.revokeObjectURL(a.href); }, 3000);
  }).catch(function(e){ alert('导出失败：' + e.message); });
}
var _plWenshuBody = null; // 当前文书导出参数（供弹窗「下载 docx」复用）

function plExportWenshu() {
  if (!_plDetailData || !_plDetailData.detail) { alert('请先点开某个吉日查看详情，再导出文书'); return; }
  var type = document.getElementById('plType').value;
  var xianming = (document.getElementById('plXianming') ? document.getElementById('plXianming').value : '').trim();
  var fuzhuBenMing = (document.getElementById('plFuzhuBenMing') ? document.getElementById('plFuzhuBenMing').value : '').trim();
  var diliShi = (document.getElementById('plDilishi') ? document.getElementById('plDilishi').value : '').trim();
  var nan = (document.getElementById('plNanNianming') ? document.getElementById('plNanNianming').value : '').trim();
  var nv = (document.getElementById('plNvNianming') ? document.getElementById('plNvNianming').value : '').trim();
  var benMing = (document.getElementById('plBenMing') ? document.getElementById('plBenMing').value : '').trim();
  if (!benMing && xianming) benMing = xianming; // 主命留空回退「仙命/主命」输入框

  var body = {
    detail: _plDetailData.detail,
    date: _plDetailData.date, shichen: _plDetailData.shichen, mountain: _plDetailData.mountain,
    zetiri_type: type,
    lailong: document.getElementById('plLailong') ? document.getElementById('plLailong').value : '',
    xianming: xianming, fuzhu_benming: fuzhuBenMing, nan_ming: nan, nv_ming: nv, ben_ming: benMing,
    dili_shi: diliShi
  };
  _plWenshuBody = body;

  fetch('/api/export/wenshu_html', {
    method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(body)
  }).then(function(r){ return r.json(); })
    .then(function(d){
      if (d.error) throw new Error(d.error);
      showWenshuModal(d.html);
    })
    .catch(function(e){ alert('文书生成失败：' + e.message); });
}

function showWenshuModal(html) {
  var old = document.getElementById('wenshuModal');
  if (old) old.remove();
  var ov = document.createElement('div');
  ov.id = 'wenshuModal';
  ov.style.cssText = 'position:fixed;inset:0;background:rgba(0,0,0,.65);z-index:10000;display:flex;align-items:center;justify-content:center;';
  ov.innerHTML =
    '<div style="background:#1a1a2e;border-radius:12px;width:95%;max-width:1140px;max-height:94vh;display:flex;flex-direction:column;box-shadow:0 12px 48px rgba(0,0,0,.55);">' +
    '<div style="display:flex;justify-content:space-between;align-items:center;padding:12px 16px;border-bottom:1px solid #333;">' +
      '<span style="color:#fff;font-size:15px;font-weight:600;">📜 择日文书预览</span>' +
      '<button onclick="document.getElementById(\'wenshuModal\').remove()" style="background:none;border:none;color:#999;font-size:24px;cursor:pointer;line-height:1;">&times;</button>' +
    '</div>' +
    '<iframe id="wenshuFrame" style="flex:1;width:100%;height:68vh;border:none;background:#555;"></iframe>' +
    '<div style="padding:12px 16px;border-top:1px solid #333;text-align:right;">' +
      '<button onclick="plDownloadWenshuPdf()" style="background:linear-gradient(135deg,#10b981,#059669);border:none;color:#fff;padding:9px 20px;border-radius:8px;cursor:pointer;font-weight:600;">⬇️ 下载 PDF</button>' +
      '<button onclick="document.getElementById(\'wenshuModal\').remove()" style="background:#333;border:none;color:#ccc;padding:9px 16px;border-radius:8px;cursor:pointer;margin-left:8px;">关闭</button>' +
    '</div>' +
    '</div>';
  document.body.appendChild(ov);
  document.getElementById('wenshuFrame').srcdoc = html;
}

function plDownloadWenshuPdf() {
  if (!_plWenshuBody) { alert('暂无文书数据'); return; }
  fetch('/api/export/wenshu_pdf', {
    method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(_plWenshuBody)
  }).then(function(r){
    if (!r.ok) return r.json().then(function(d){ throw new Error(d.error || '下载失败'); });
    var cd = r.headers.get('Content-Disposition') || '';
    var mStar = cd.match(/filename\*=UTF-8''([^;]*)/i);
    var fname;
    if (mStar) { fname = decodeURIComponent(mStar[1].replace(/['"]/g, '')); }
    else { var m = cd.match(/filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/); fname = m ? m[1].replace(/['"]/g, '') : '仪度六壬择日课单.pdf'; }
    return r.blob().then(function(blob){ return { blob: blob, fname: fname }; });
  }).then(function(o){
    var a = document.createElement('a');
    a.href = URL.createObjectURL(o.blob);
    a.download = o.fname;
    document.body.appendChild(a); a.click(); a.remove();
    setTimeout(function(){ URL.revokeObjectURL(a.href); }, 3000);
  }).catch(function(e){ alert('下载失败：' + e.message); });
}
/* 六壬预测内部二级子页切换（独立机制，不与全局 sub-content2 冲突） */
function switchLiurenSub(name) {
  document.querySelectorAll('.liuren-sub').forEach(c => c.classList.toggle('active', c.id === 'liuren-sub-' + name));
  document.querySelectorAll('.liuren-sub-btn').forEach(b => b.classList.toggle('active', b.dataset.lsub === name));
  if (name === 'backtest') { loadLiurenBacktest(); }
}
function loadLiurenBacktest() {
  const wrap = document.getElementById('liurenBacktestWrap');
  wrap.innerHTML = '<div style="text-align:center;color:#999;padding:30px;">⏳ 正在加载回测报告…</div>';
  fetch('/api/liuren_backtest')
    .then(r => r.json())
    .then(resp => {
      if (!resp.success) { wrap.innerHTML = '<div style="color:#c0392b;padding:20px;">加载失败：' + resp.error + '</div>'; return; }
      wrap.innerHTML = renderLiurenBacktest(resp.data);
    })
    .catch(e => { wrap.innerHTML = '<div style="color:#c0392b;padding:20px;">请求异常：' + e + '</div>'; });
}
function btPct(x) { return (x * 100).toFixed(1) + '%'; }
function btPval(x) { if (x < 0.001) return '0.000*'; return x.toFixed(3); }
function btAccBar(acc) {
  const w = Math.max(2, Math.min(100, acc * 100));
  const col = acc >= 0.5 ? '#6366f1' : '#e8920c';
  return '<div class="bt-bar"><div class="bt-50line"></div><span style="width:' + w + '%;background:' + col + '"></span></div><div style="font-size:11px;margin-top:2px;color:#666;">' + btPct(acc) + '</div>';
}
function renderLiurenBacktest(d) {
  const o = d.overall, m3 = o.M3;
  const dr = d.date_range || ['?', '?'];
  const labels = { M1: '原20d引擎(朴素)', M2: '融合①②③', M3: '融合+CBR', M4: 'CBR单独' };
  let mRows = '';
  ['M1', 'M2', 'M3', 'M4'].forEach(k => {
    const m = o[k];
    const brier = m.brier ? m.brier.toFixed(3) : '—';
    const ci = m.ci95 ? '[' + btPct(m.ci95[0]) + ',' + btPct(m.ci95[1]) + ']' : '—';
    mRows += '<tr><td><b>' + labels[k] + '</b></td><td>' + btPct(m.coverage) + '</td><td>' + btAccBar(m.accuracy) +
      '</td><td>' + ci + '</td><td>' + btPval(m.p_value) + '</td><td>' + btPct(m.down_bias) + '</td><td>' + brier + '</td></tr>';
  });
  let cRows = '';
  Object.keys(d.by_cycle || {}).forEach(name => {
    const c = d.by_cycle[name], cm = c.M3;
    cRows += '<tr><td><b>' + name + '</b></td><td>' + c.n + '</td><td>' + btPct(c.actual_down_rate) + '</td><td>' + btAccBar(cm.accuracy) + '</td><td>' + btPval(cm.p_value) + '</td><td>' + btPct(cm.down_bias) + '</td></tr>';
  });
  let bRows = '';
  Object.keys(d.by_trailing_band || {}).forEach(name => {
    const c = d.by_trailing_band[name], cm = c.M3;
    bRows += '<tr><td><b>' + name + '</b></td><td>' + c.n + '</td><td>' + btPct(c.actual_down_rate) + '</td><td>' + btAccBar(cm.accuracy) + '</td></tr>';
  });
  let yRows = '';
  Object.keys(d.by_year || {}).sort().forEach(y => {
    const c = d.by_year[y], cm = c.M3;
    yRows += '<tr><td><b>' + y + '</b></td><td>' + c.n + '</td><td>' + btPct(c.actual_down_rate) + '</td><td>' + btAccBar(cm.accuracy) + '</td><td>' + btPval(cm.p_value) + '</td></tr>';
  });
  const cycles = Object.keys(d.by_cycle || {});
  const years = Object.keys(d.by_year || {});
  return '' +
    '<div class="bt-banner">⚠️ <b>数据说明：</b>本回测由引擎算法对上证指数 ' + dr[0] + ' ~ ' + dr[1] + ' 共 <b>' + d.n_total + '</b> 个交易日<b>从头重算</b>得出，真实日线来自「' + d.source + '」。它反映引擎代码的<b>真实表现</b>，<b>并非</b>系统中近期各类别自动预测（调试期存储记录，含 BUG，不可作为参考）。标签规则：' + d.label_rule + '。</div>' +
    '<div class="bt-card"><h3>📌 核心结论（引擎有效边界）</h3><div class="bt-concl">' +
      '<div class="row"><span class="tag tag-warn">方向预测无效</span><span>M3(融合+CBR) 全样本决断准确率 <b>' + btPct(m3.accuracy) + '</b>，p=' + btPval(m3.p_value) + '，与抛硬币无统计差异；22 个年份、' + cycles.length + ' 个牛熊周期均围绕 50% 波动，<b>无稳定方向 alpha</b>。</span></div>' +
      '<div class="row"><span class="tag tag-ok">偏置中和有效</span><span>朴素引擎 M1 与 CBR M4 含 <b>' + btPct(o.M1.down_bias) + '</b> / <b>' + btPct(o.M4.down_bias) + '</b> 结构性看跌偏置（若交易必亏）；融合层(支柱①②③校准)把看跌偏置纠正至 <b>' + btPct(m3.down_bias) + '</b>，把"必亏"变成"公平硬币"。</span></div>' +
      '<div class="row"><span class="tag tag-info">CBR 定位解释层</span><span>CBR 的边际贡献仅为概率校准（Brier ' + o.M2.brier.toFixed(3) + '→' + m3.brier.toFixed(3) + '），方向不变 → 印证"综合叙事"权重保持中性 1.0，<b>不可放大为信号</b>。</span></div>' +
    '</div></div>' +
    '<div class="bt-card"><h3>📊 四方法对比（全样本 ' + d.n_total + ' 日）</h3>' +
      '<table class="bt-tbl"><thead><tr><th>方法</th><th>覆盖率</th><th>决断准确率</th><th>95%CI</th><th>p值</th><th>看跌偏置</th><th>Brier</th></tr></thead><tbody>' + mRows + '</tbody></table>' +
      '<div style="font-size:11px;color:#999;margin-top:8px;">注：p值检验"准确率是否显著高于 50%"。CI 跨越 50% 即无显著 edge。红色竖线=50% 基准。</div>' +
    '</div>' +
    '<div class="bt-card"><h3>🐂🐻 分牛熊周期（M3 融合+CBR）</h3>' +
      '<table class="bt-tbl"><thead><tr><th>周期</th><th>n</th><th>实际跌占比</th><th>M3准确率</th><th>p值</th><th>M3看跌偏置</th></tr></thead><tbody>' + cRows + '</tbody></table>' +
    '</div>' +
    '<div class="bt-card"><h3>📈 分市场阶段（trailing 120日收益带）</h3>' +
      '<table class="bt-tbl"><thead><tr><th>市场阶段</th><th>n</th><th>实际跌占比</th><th>M3准确率</th></tr></thead><tbody>' + bRows + '</tbody></table>' +
    '</div>' +
    '<div class="bt-card"><details class="bt-collapsible"><summary>🗓️ 展开分年度明细（' + years.length + ' 年）</summary>' +
      '<table class="bt-tbl" style="margin-top:10px;"><thead><tr><th>年份</th><th>n</th><th>实际跌占比</th><th>M3准确率</th><th>p值</th></tr></thead><tbody>' + yRows + '</tbody></table>' +
    '</details></div>';
}
function toggleSection(id) {
  var s = document.getElementById(id);
  if (s) s.classList.toggle('expanded');
}

// 量化选股器数据加载
let _screenerResults = [];
let _screenerLoaded = false;
function fetchScreenerData() {
  return fetch(API+'/api/screener/result')
    .then(r => r.json())
    .then(data => {
      if (!data.success) { _screenerResults = []; return; }
      _screenerResults = data.results || [];
      _screenerLoaded = true;
      _screenerMeta = {
        scanned_at: data.scanned_at || '',
        message: data.message || ''
      };
    })
    .catch(err => { _screenerResults = []; console.error('选股加载失败:', err); });
}
let _screenerMeta = {};

// 大六壬推荐数据加载
let _multiStockPredictions = [];
let _multiStockLoaded = false;
let _multiStockMeta = {};
function fetchMultiStockData() {
  return fetch(API+'/api/multi_stock')
    .then(r => r.json())
    .then(data => {
      if (!data.success) { _multiStockPredictions = []; return; }
      _multiStockPredictions = data.predictions || [];
      _multiStockLoaded = true;
      _multiStockMeta = {
        date: data.date || '',
        rizhu: data.rizhu || '',
        shichen: data.shichen || '',
        file: data.file || '',
        message: data.message || ''
      };
    })
    .catch(err => { _multiStockPredictions = []; console.error('大六壬推荐加载失败:', err); });
}

// 双阶段验证数据加载
let _dualPhaseResults = [];
let _dualPhaseVerified = [];
let _dualPhaseWatching = [];
let _dualPhaseLoaded = false;
let _dualPhaseMeta = {};
let _marketTiming = null;
function fetchDualPhaseData() {
  return fetch(API+'/api/dual_phase')
    .then(r => r.json())
    .then(data => {
      if (!data.success) { _dualPhaseResults = []; _dualPhaseVerified = []; _dualPhaseWatching = []; return; }
      _dualPhaseResults = data.all || [];
      _dualPhaseVerified = data.verified || [];
      _dualPhaseWatching = data.watch || [];
      _dualPhaseLoaded = true;
      _dualPhaseMeta = {
        date: data.date || '',
        file: data.file || '',
        verified_count: data.verified_count || 0,
        watch_count: data.watch_count || 0,
        total_count: data.total_count || 0,
        message: data.message || '',
        skipped_reason: data.skipped_reason || ''
      };
      // 如果双阶段结果里包含择时信息，优先用它
      if (data.market_timing && data.market_timing.signal) {
        _marketTiming = data.market_timing;
      }
    })
    .catch(err => { _dualPhaseResults = []; _dualPhaseVerified = []; _dualPhaseWatching = []; console.error('双阶段加载失败:', err); });
}

// ① 加载大盘择时信号
function fetchMarketTiming() {
  return fetch(API+'/api/market_timing')
    .then(r => r.json())
    .then(data => {
      if (data.success && data.signal) {
        _marketTiming = data;
      }
    })
    .catch(err => { console.error('择时信号加载失败:', err); });
}

function renderMarketTiming() {
  const badge = document.getElementById('timingBadge');
  const content = document.getElementById('timingContent');
  const dualBadge = document.getElementById('dualPhaseBadge');
  if (!badge || !content) return;

  if (!_marketTiming || !_marketTiming.signal) {
    badge.textContent = '暂无数据';
    content.innerHTML = '<div style="color:#999;">暂无大盘择时数据，请等待调度器每日 09:00 自动预测</div>';
    return;
  }

  const signal = _marketTiming.signal;
  /* 涨跌配色全站统一（2026-08 审查）：涨=红/跌=绿（A股行情惯例），与预测记录/事件起课等一致 */
  const signalMap = {
    'bull':  { label: '📈 看涨', color: '#dc2626', bg: '#fee2e2' },
    'bear':  { label: '📉 看跌', color: '#16a34a', bg: '#dcfce7' },
    'neutral': { label: '➡️ 震荡', color: '#6b7280', bg: '#f3f4f6' },
  };
  const s = signalMap[signal] || signalMap['neutral'];
  badge.textContent = s.label;
  badge.style.background = s.bg;
  badge.style.color = s.color;

  if (dualBadge) {
    if (signal === 'bear') {
      dualBadge.textContent = '⚠️ 大盘看跌';
      dualBadge.style.background = '#16a34a';
    } else if (signal === 'bull') {
      dualBadge.textContent = '📈 大盘看涨';
      dualBadge.style.background = '#dc2626';
    }
  }

  let html = '<div style="margin-bottom:6px;">';
  html += '<b>目标日：</b>' + (_marketTiming.target_date || '--') + ' | ';
  html += '<b>日柱：</b>' + (_marketTiming.rizhu || '--') + ' | ';
  html += '<b>占时：</b>' + (_marketTiming.shichen || '--');
  html += '</div>';
  html += '<div style="margin-bottom:6px;">';
  html += '<b>吉凶：</b><span style="color:' + s.color + ';font-weight:600;">' + (_marketTiming.jixiong || '--') + '</span> | ';
  html += '<b>趋势：</b><span style="color:' + s.color + ';font-weight:600;">' + (_marketTiming.trend || '--') + '</span>';
  html += '</div>';
  if (_marketTiming.analysis) {
    html += '<div style="background:#f8fafc;padding:8px 12px;border-radius:6px;font-size:12px;color:#475569;margin-top:8px;">';
    html += '<b>分析：</b>' + _marketTiming.analysis;
    html += '</div>';
  }
  if (signal === 'bear') {
    html += '<div style="background:#f0fdf4;border:1px solid #bbf7d0;color:#166534;padding:8px 12px;border-radius:6px;margin-top:8px;font-weight:600;">';
    html += '⚠️ 大盘看跌，建议空仓观望。双重验证选股今日暂停（仅保留历史数据用于对照学习）。';
    html += '</div>';
  } else if (signal === 'bull') {
    html += '<div style="background:#fef2f2;border:1px solid #fecaca;color:#991b1b;padding:8px 12px;border-radius:6px;margin-top:8px;font-weight:600;">';
    html += '✅ 大盘看涨，适合积极选股。高置信标的可满仓操作。';
    html += '</div>';
  } else {
    html += '<div style="background:#f9fafb;border:1px solid #e5e7eb;color:#374151;padding:8px 12px;border-radius:6px;margin-top:8px;font-weight:600;">';
    html += '➡️ 震荡市，精选个股为主。仅参与高置信度标的，控制仓位。';
    html += '</div>';
  }
  content.innerHTML = html;
}

// 人工占一课（活时法）
function triggerHuoshiPaipan(e) {
  const btn = e.target;
  const orig = btn.innerHTML;
  btn.innerHTML = '⏳ 求天机中...';
  btn.disabled = true;
  fetch(API+'/api/huoshi_paipan', {method:'POST'})
    .then(r => r.json())
    .then(data => {
      const resultDiv = document.getElementById('huoshiResult');
      const badge = document.getElementById('huoshiBadge');
      if (data.success) {
        badge.textContent = data.shichen + '时';
        badge.style.background = '#0ea5e9';
        badge.style.color = '#fff';
        resultDiv.style.display = 'block';
        resultDiv.innerHTML =
          '<div style="margin-bottom:8px;">' +
            '<b style="color:#0ea5e9;">📅 ' + data.timestamp + '</b> | ' +
            '<b>方法：</b>' + data.method + ' | ' +
            '<b>占时：</b><span style="color:#0ea5e9;font-weight:600;font-size:15px;">' + data.shichen + '时</span> | ' +
            '<b>日柱：</b>' + data.rizhu +
          '</div>' +
          '<div style="font-size:11px;color:#666;margin-bottom:8px;">🔮 ' + data.source + '</div>' +
          '<pre style="white-space:pre-wrap;font-family:Consolas,monospace;background:#f8fafc;padding:10px;border-radius:6px;font-size:12px;">' + data.paipan_text + '</pre>' +
          (data.cbr && data.cbr.length ? '<div style="margin-top:10px;padding:10px;background:#fefce8;border:1px solid #eab308;border-radius:6px;">' +
            '<div style="font-size:13px;font-weight:700;color:#a16207;margin-bottom:6px;">📚 相似古例（依样断课参考）</div>' +
            data.cbr.slice(0, 3).map(function(m){
              return '<div style="font-size:12px;color:#444;margin-bottom:6px;padding:6px;background:#fff;border-radius:4px;border:1px solid #fde68a;">' +
                '<span style="color:#a16207;font-weight:700;">' + m.similarity + '分</span> ' +
                '<b>' + m.case_id + '</b> [' + m.zhanlei + '/' + m.label + '] 三传' + m.sanchuan.join('') + '<br>' +
                '<span style="color:#666;">' + (m.duanyu || '').slice(0, 80) + '…</span></div>';
            }).join('') + '</div>' : '');
      } else {
        resultDiv.style.display = 'block';
        resultDiv.innerHTML = '<span style="color:#dc2626;">❌ 排盘失败：' + data.error + '</span>';
      }
    })
    .catch(err => {
      const resultDiv = document.getElementById('huoshiResult');
      resultDiv.style.display = 'block';
      resultDiv.innerHTML = '<span style="color:#dc2626;">❌ 请求失败：' + err + '</span>';
    })
    .finally(() => {
      btn.innerHTML = orig;
      btn.disabled = false;
    });
}

// 渲染双阶段验证表格
function renderDualPhaseTable() {
  const tbody = document.getElementById('dualPhaseBody');
  const meta = document.getElementById('dualPhaseMeta');
  const cntEl = document.getElementById('dualPhaseBadge');
  if (!tbody) return;

  // 漏洞3修复：大盘看空时显示明确提示
  if (_dualPhaseMeta.skipped_reason) {
    cntEl.textContent = '暂停';
    meta.textContent = '';
    tbody.innerHTML = '<tr><td colspan="8" style="text-align:center;padding:24px;">' +
      '<div style="color:#dc2626;font-size:16px;font-weight:600;margin-bottom:8px;">⚠️ ' + _dualPhaseMeta.skipped_reason + '</div>' +
      '<div style="color:#999;font-size:12px;">大盘看空期间不执行量化选股+六壬精选，仅运行硬编码股票池用于对照学习</div>' +
      '</td></tr>';
    return;
  }

  const verifiedCnt = _dualPhaseVerified.length;
  const watchCnt = _dualPhaseWatching.length;
  cntEl.textContent = verifiedCnt + '只通过 / ' + watchCnt + '只观察';

  let metaStr = '';
  if (_dualPhaseMeta.date) {
    metaStr = '🕐 ' + _dualPhaseMeta.date + ' | ✅通过 ' + verifiedCnt + ' / 👀观察 ' + watchCnt + ' / 共 ' + _dualPhaseMeta.total_count;
  } else if (_dualPhaseMeta.message) {
    metaStr = _dualPhaseMeta.message;
  }
  meta.textContent = metaStr;

  // 无验证通过的
  if (!verifiedCnt && !watchCnt) {
    if (_dualPhaseResults.length > 0) {
      tbody.innerHTML = '<tr><td colspan="8" style="text-align:center;color:#bbb;padding:20px;">暂无双阶段选股结果，请等待调度器在 09:10 自动执行</td></tr>';
    } else {
      tbody.innerHTML = '<tr><td colspan="8" style="text-align:center;color:#bbb;padding:20px;">'+(_dualPhaseMeta.message||'暂无双阶段选股结果，请等待调度器在 09:10 自动执行')+'</td></tr>';
    }
    return;
  }

  // 先显示通过，再显示观察
  let rows = '';
  if (verifiedCnt > 0) {
    rows += _dualPhaseVerified.map(r => renderDualPhaseRow(r, 'verified')).join('');
  }
  if (watchCnt > 0) {
    if (verifiedCnt > 0) {
      rows += '<tr><td colspan="8" style="background:#fef3c7;font-size:11px;color:#92400e;padding:4px 10px;">👀 以下为观察级标的（置信度40-50%或吉凶不明），仅供参考</td></tr>';
    }
    rows += _dualPhaseWatching.map(r => renderDualPhaseRow(r, 'watch')).join('');
  }
  tbody.innerHTML = rows;
}

function renderDualPhaseRow(r, level) {
  const score = r.screener_score || 0;
  const trend = r.liuren_trend || '--';
  const jx = r.liuren_jixiong || '--';
  const conf = r.liuren_confidence || 0;
  const posLevel = r.position_level || '--';
  const posPct = r.position_pct != null ? r.position_pct : null;
  const scoreCls = score >= 50 ? 'text-up' : score < 20 ? 'text-down' : '';
  const confPct = (conf * 100).toFixed(0) + '%';
  const confCls = conf >= 0.7 ? 'text-up' : conf >= 0.5 ? '' : 'text-down';
  const trendCls = trend.includes('涨') ? 'text-up' : trend.includes('跌') ? 'text-down' : '';
  const rank = (level === 'verified' || level === 'watch') ? (r.screener_rank || '-') : '-';
  let levelTag = '';
  if (level === 'verified') {
    levelTag = ' <span style="color:#16a34a;font-size:10px;">✅双通过</span>';
  } else if (level === 'watch') {
    levelTag = ' <span style="color:#d97706;font-size:10px;">👀观察</span>';
  }

  let posTag = '';
  if (posPct != null) {
    if (posPct >= 70) {
      posTag = '<span style="color:#16a34a;font-weight:600;">' + posLevel + ' (' + posPct + '%)</span>';
    } else if (posPct >= 30) {
      posTag = '<span style="color:#d97706;font-weight:600;">' + posLevel + ' (' + posPct + '%)</span>';
    } else if (posPct > 0) {
      posTag = '<span style="color:#6b7280;">' + posLevel + ' (' + posPct + '%)</span>';
    } else {
      posTag = '<span style="color:#dc2626;">' + posLevel + '</span>';
    }
  } else {
    posTag = posLevel;
  }

  return `<tr>
    <td style="text-align:center;font-weight:600;color:#b8860b;">${rank}</td>
    <td style="font-family:monospace;">${r.code||'--'}</td>
    <td>${r.name||'--'}${levelTag}</td>
    <td class="${scoreCls}" style="font-weight:600;">${(score>=0?'+':'')+score.toFixed(1)}</td>
    <td class="${trendCls}" style="font-weight:600;">${trend}</td>
    <td>${jx}</td>
    <td class="${confCls}" style="font-weight:600;">${confPct}</td>
    <td style="background:#fffbeb;font-weight:600;">${posTag}</td>
  </tr>`;
}

// 渲染量化选股器表格
function renderScreenerTable() {
  const tbody = document.getElementById('screenerTable');
  const meta = document.getElementById('screenerMeta');
  const cntEl = document.getElementById('screenerCount');
  if (!tbody) return;
  cntEl.textContent = _screenerResults.length + '只';
  let metaStr = '';
  if (_screenerMeta.scanned_at) {
    try {
      const d = new Date(_screenerMeta.scanned_at);
      metaStr = '🕐 最近扫描: ' + d.toLocaleString('zh-CN', {hour12:false});
    } catch(e) { metaStr = '🕐 最近扫描: ' + _screenerMeta.scanned_at; }
  }
  meta.textContent = metaStr;
  if (!_screenerResults.length) {
    tbody.innerHTML = '<tr><td colspan="6" style="text-align:center;color:#bbb;padding:20px;">'+(_screenerMeta.message||'暂无选股结果，请等待调度器在 09:10 自动扫描')+'</td></tr>';
    return;
  }
  tbody.innerHTML = _screenerResults.map(r => {
    const scoreCls = r.score >= 50 ? 'text-up' : r.score < 20 ? 'text-down' : '';
    const hasLiuren = _multiStockPredictions.some(p => p.symbol === r.code);
    const liurenTag = hasLiuren ? ' <span style="color:#8b5cf6;font-size:10px;">🧭六壬</span>' : '';
    return `<tr>
      <td style="text-align:center;font-weight:600;color:#667eea;">${r.rank||'-'}</td>
      <td style="font-family:monospace;">${r.code||'--'}</td>
      <td>${r.name||'--'}${liurenTag}</td>
      <td class="${scoreCls}" style="font-weight:600;">${((r.score!=null&&!isNaN(r.score)) ? ((r.score>=0?'+':'')+r.score.toFixed(1)) : '--')}</td>
      <td>${r.advice||'--'}</td>
      <td>
        <button class="srch-btn" style="padding:4px 10px;font-size:12px;" onclick="showStockDetail('${r.code}','${r.name||''}')">查看详情</button>
        <button class="buy-btn" style="padding:4px 10px;font-size:12px;margin-left:4px;${r.score < 50 ? 'background:#fff;border:1px solid #f59e0b;color:#b45309;' : 'background:#ef4444;color:#fff;border:none;'}border-radius:4px;cursor:pointer;" onclick="screenerBuy('${r.code}','${(r.name||'').replace(/'/g,"\\'")}',${r.score||0})">买入</button>
      </td>
    </tr>`;
  }).join('');
}

// 渲染大六壬推荐表格
function renderMultiStockTable() {
  const tbody = document.getElementById('multiStockTable');
  const meta = document.getElementById('multiStockMeta');
  const cntEl = document.getElementById('multiStockCount');
  if (!tbody) return;
  cntEl.textContent = _multiStockPredictions.length + '只';
  let metaStr = '';
  if (_multiStockMeta.date) metaStr += '📅 预测日期: ' + _multiStockMeta.date;
  if (_multiStockMeta.rizhu) metaStr += '  | 日柱: ' + _multiStockMeta.rizhu;
  if (_multiStockMeta.shichen) metaStr += '  | 占时: ' + _multiStockMeta.shichen;
  if (_multiStockMeta.file) metaStr += '  | 📄 ' + _multiStockMeta.file;
  meta.textContent = metaStr;
  if (!_multiStockPredictions.length) {
    tbody.innerHTML = '<tr><td colspan="6" style="text-align:center;color:#bbb;padding:14px;">'+(_multiStockMeta.message||'暂无预测记录')+'</td></tr>';
    return;
  }
  tbody.innerHTML = _multiStockPredictions.map(p => {
    const trendCls = (p.trend||'').indexOf('涨')>=0 ? 'text-up' : (p.trend||'').indexOf('跌')>=0 ? 'text-down' : '';
    const jxCls = p.jixiong==='吉' ? 'text-up' : p.jixiong==='凶' ? 'text-down' : '';
    const conf = (p.confidence != null && !isNaN(p.confidence)) ? (p.confidence*100).toFixed(0) : '--';
    const inScreener = _screenerResults.some(r => r.code === p.symbol);
    const screenerTag = inScreener ? ' <span style="color:#3b82f6;font-size:10px;">📊量化</span>' : '';
    return `<tr>
      <td style="font-family:monospace;">${p.symbol||'--'}</td>
      <td>${p.name||'--'}${screenerTag}</td>
      <td class="${trendCls}">${p.trend||'--'}</td>
      <td class="${jxCls}">${p.jixiong||'--'}</td>
      <td>${conf}%</td>
      <td><button class="srch-btn" style="padding:4px 10px;font-size:12px;" onclick="showStockDetail('${p.symbol}','${p.name||''}')">查看详情</button></td>
    </tr>`;
  }).join('');
}
    
function fetchTimeout(url, ms) {
  return new Promise((resolve, reject) => {
    var timer = setTimeout(() => reject(new Error('timeout')), ms);
    fetch(url).then(r=>{clearTimeout(timer); resolve(r);}).catch(e=>{clearTimeout(timer); reject(e);});
  });
}

// 【2026-08-02 修复】每个渲染独立容错：单个面板渲染抛错不再连累「预测记录」等其它面板静默空白。
function safeRender(name, fn) {
  try { fn(); }
  catch (e) { console.error('render [' + name + '] failed:', e); }
}

// 预测记录独立加载：无论其它面板如何，预测记录面板始终尝试渲染
async function loadPredictionsIndependent() {
  try {
    const preds = await fetch(API+'/api/predictions').then(r=>r.json()).catch(err=>{console.error('preds err:', err); return [];});
    renderPreds(Array.isArray(preds) ? preds : []);
  } catch (e) {
    console.error('loadPredictionsIndependent failed:', e);
  }
}

async function loadAll() {
  // 后台标签页跳过轮询，回到前台后下个周期（≤15s）自动恢复
  if (document.hidden) return;
  // 预测记录独立先行，避免被后续渲染异常吞掉
  loadPredictionsIndependent();

  try {
    const [sum, trades, market, marketHist, gap] = await Promise.all([
      fetch(API+'/api/summary').then(r=>r.json()).catch(err=>{console.error('summary err:', err); return {portfolios:[], today_prediction:{}};}),
      fetch(API+'/api/trades').then(r=>r.json()).catch(err=>{console.error('trades err:', err); return [];}),
      fetchTimeout(API+'/api/market',3000).then(r=>r.json()).catch(err=>{console.error('market err:', err); return {};}),
      fetchTimeout(API+'/api/market_history',3000).then(r=>r.json()).catch(err=>{console.error('marketHist err:', err); return [];}),
      fetchTimeout(API+'/api/gap_analysis',2000).then(r=>r.json()).catch(()=>null),
    ]);

    // 渲染各模块，逐个独立容错
    if (sum) {
      safeRender('summary', () => renderSummary(sum));
      safeRender('portfolios', () => renderPortfolios(sum.portfolios || []));
      safeRender('todayPred', () => renderTodayPred(sum.today_prediction || {}));
    }
    safeRender('trades', () => renderTrades(trades || []));   // 确保交易表格始终渲染
    safeRender('market', () => renderMarket(market || {}));
    safeRender('marketChart', () => renderMarketChart(marketHist || []));

    if (gap && gap.status !== 'unavailable' && !gap.error) {
      safeRender('gap', () => {
        renderGapSummary(gap);
        renderGapDistChart(gap);
        renderGapTrendChart(gap);
        renderGapTrendTable(gap);
        renderGapDetails(gap);
        document.getElementById('gapTime').textContent = '更新: ' + (gap.computed_at || '');
      });
    } else {
      // 无数据时显示中文占位提示
      safeRender('gapEmpty', () => renderGapSummaryEmpty());
    }
  } catch (e) {
    console.error('loadAll error:', e);
  }
}

function renderSummary(s) {
  // 【2026-08-02 重构】总览卡3：总数/已对照/正确/部分/错误/准确率（与记录表格同源同口径）
  const total = s.total_predictions || 0;
  const sT = document.getElementById('sTotal');
  if (sT) sT.textContent = total;
  const sT2 = document.getElementById('sTotal2');
  if (sT2) sT2.textContent = total;
  const sC = document.getElementById('sChecked');
  if (sC) sC.textContent = s.checked;
  const sW = document.getElementById('sWrong');
  if (sW) sW.textContent = (s.correct||0) + ' / ' + (s.partial||0) + ' / ' + (s.wrong||0);
  const sA = document.getElementById('sAccuracy');
  if (sA) sA.textContent = s.accuracy + '%';

  // 按类别拆分表格
  const tbody = document.getElementById('catBody');
  if (!tbody) return;
  if (!s.by_category || s.by_category.length === 0) {
    tbody.innerHTML = '<tr><td colspan="7" style="text-align:center;color:#bbb;padding:12px;">暂无数据</td></tr>';
    return;
  }
  tbody.innerHTML = s.by_category.map(c => `
    <tr>
      <td>${c.label}</td>
      <td>${c.total}</td>
      <td>${c.checked}</td>
      <td class="correct">${c.correct}</td>
      <td class="partial">${c.partial}</td>
      <td class="wrong">${c.wrong}</td>
      <td class="accuracy">${c.accuracy}%</td>
    </tr>
  `).join('');

  // 六壬起课预测涨跌分析
  const trendBody = document.getElementById('liurenTrendBody');
  if (!trendBody) return;
  if (!s.liuren_trend_stats || s.liuren_trend_stats.length === 0) {
    trendBody.innerHTML = '<tr><td colspan="7" style="text-align:center;color:#bbb;padding:12px;">暂无六壬起课预测数据</td></tr>';
  } else {
    trendBody.innerHTML = s.liuren_trend_stats.map(t => `
      <tr>
        <td style="font-weight:600;color:#7c3aed;">${t.trend}</td>
        <td>${t.total}</td>
        <td>${t.checked}</td>
        <td class="correct">${t.correct}</td>
        <td class="partial">${t.partial}</td>
        <td class="wrong">${t.wrong}</td>
        <td class="accuracy">${t.accuracy}%</td>
      </tr>
    `).join('');
  }
}

// ====== 六亲/遁干/旬空 共享计算（2026-08 审查收敛：原 modal 与 liuren20d 各持一份重复实现） ======
// 规则与后端 engine/liuqin_engine.py（LiuQinCalculator）及 liuren_analysis_engine.py 一致；
// 当 API 响应带 analysis.liuqin（后端引擎已算好）时优先用后端数据，仅缺省时回退本函数。
var _GAN60 = '甲乙丙丁戊己庚辛壬癸', _ZHI12 = '子丑寅卯辰巳午未申酉戌亥';
var _WUSHU = {'甲':'甲','乙':'丙','丙':'戊','丁':'庚','戊':'壬','己':'甲','庚':'丙','辛':'戊','壬':'庚','癸':'壬'};
var _WX_DZ = {'子':'水','丑':'土','寅':'木','卯':'木','辰':'土','巳':'火','午':'火','未':'土','申':'金','酉':'金','戌':'土','亥':'水'};
var _WX_G = {'甲':'木','乙':'木','丙':'火','丁':'火','戊':'土','己':'土','庚':'金','辛':'金','壬':'水','癸':'水'};
var _XUNKONG = {'甲子':'戌亥','甲戌':'申酉','甲申':'午未','甲午':'辰巳','甲辰':'寅卯','甲寅':'子丑'};
/** 遁干：日干五合起旬遁，得地支所遁天干 */
function _dunG(riGan, dz){ var si = _GAN60.indexOf(_WUSHU[riGan] || '甲'); return _GAN60[(si + _ZHI12.indexOf(dz)) % 10]; }
/** 六亲：生我=父母 / 我生=子孙 / 克我=官鬼 / 我克=妻财 / 同我=兄弟（长名，与后端分析一致） */
function _liuQ(riGan, dz){
  var gw = _WX_G[riGan], dw = _WX_DZ[dz]; if (!gw || !dw) return '';
  if (gw === dw) return '兄弟';
  if ((gw==='木'&&dw==='火')||(gw==='火'&&dw==='土')||(gw==='土'&&dw==='金')||(gw==='金'&&dw==='水')||(gw==='水'&&dw==='木')) return '子孙';
  if ((gw==='木'&&dw==='土')||(gw==='火'&&dw==='金')||(gw==='土'&&dw==='水')||(gw==='金'&&dw==='木')||(gw==='水'&&dw==='火')) return '妻财';
  if ((gw==='木'&&dw==='金')||(gw==='火'&&dw==='水')||(gw==='土'&&dw==='木')||(gw==='金'&&dw==='火')||(gw==='水'&&dw==='土')) return '官鬼';
  return '父母';
}
/** 旬空：返回当前甲旬两个空亡地支 */
function _xunKong(riGan, riZhi){
  // 【2026-08 修复】原算法仅对旬首日有效（如辛卯应空午未却返回空），
  // 现按正确规则：找到日柱所在甲旬（旬首干支顺推 zd 步，天干差须等于地支步数），
  // 旬空 = 旬首地支顺数第 10、11 位。
  var gi = _GAN60.indexOf(riGan), zi = _ZHI12.indexOf(riZhi);
  if (gi < 0 || zi < 0) return [];
  var heads = [['甲','子'],['甲','戌'],['甲','申'],['甲','午'],['甲','辰'],['甲','寅']];
  for (var i = 0; i < heads.length; i++) {
    var gk = heads[i][0], zk = heads[i][1];
    var zd = (_ZHI12.indexOf(riZhi) - _ZHI12.indexOf(zk) + 12) % 12;
    var gd = (_GAN60.indexOf(riGan) - _GAN60.indexOf(gk) + 10) % 10;
    if (zd < 10 && gd === zd) {
      return [ _ZHI12[(_ZHI12.indexOf(zk) + 10) % 12], _ZHI12[(_ZHI12.indexOf(zk) + 11) % 12] ];
    }
  }
  return [];
}

function renderMarket(m) {
  if (m.error || !m.price) return;
  document.getElementById('mPrice').textContent = m.price.toFixed(2);
  const chg = document.getElementById('mChange');
  chg.textContent = (m.change > 0 ? '+' : '') + m.change.toFixed(2) + ' (' + (m.change_pct > 0 ? '+' : '') + m.change_pct.toFixed(2) + '%)';
  chg.className = 'change ' + (m.change >= 0 ? 'up' : 'down');
  document.getElementById('mRange').textContent = '高:' + m.high.toFixed(2) + ' 低:' + m.low.toFixed(2) + '  ' + m.date;
}

function renderPortfolios(ports) {
  // 【2026-08-02 重构】账户资金卡：紧凑 stat-row 展示（量化/六壬两账户），与持仓监控 tab 同源
  const body = document.getElementById('portfolioBody');
  if (!body) return;
  const catNames = { "量化": "量化", "liuren": "六壬", "manual": "天机起课" };
  if (!ports || !Object.keys(ports).length) {
    body.innerHTML = '<div class="stat-row"><span class="label">暂无账户数据</span></div>';
    return;
  }
  let html = '';
  for (const key of Object.keys(ports)) {
    const p = ports[key];
    if (!p) continue;
    const name = catNames[key] || p.name || key;
    const retCls = p.total_return_pct >= 0 ? 'up' : 'down';
    const retPrefix = p.total_return_pct >= 0 ? '+' : '';
    const posCount = (p.positions && p.positions.length) ? p.positions.length : 0;
    html += '<div class="stat-row" style="border-bottom:1px dashed #eee;padding-bottom:6px;margin-bottom:6px;">' +
      '<span class="label"><strong>' + name + '</strong> <span style="color:#bbb;font-size:11px;">持仓' + posCount + '只</span></span>' +
      '<span class="value" style="font-size:13px;">¥' + (p.total_asset||0).toFixed(0) +
        ' <span class="' + retCls + '" style="font-size:11px;">' + retPrefix + (p.total_return_pct||0).toFixed(2) + '%</span></span>' +
      '</div>';
  }
  // 汇总行
  const ta = Object.values(ports).reduce((a, p) => a + (p.total_asset||0), 0);
  html += '<div class="total-row"><span class="label">两账户总资产</span><span class="value" style="font-size:17px;">¥' + ta.toFixed(0) + '</span></div>';
  html += '<div style="margin-top:10px;text-align:right;">' +
    '<a href="javascript:void(0)" onclick="switchTab(\'positions\')" style="font-size:12px;color:#16a34a;">查看持仓监控 →</a></div>';
  body.innerHTML = html;
}

function renderTodayPred(tp) {
  // 【2026-08-02 重构】总览卡1「进行中预测」：展示最新一条有效预测（与记录表格第一条一致）
  const setV = (id, v) => { const el = document.getElementById(id); if (el) el.textContent = v || '--'; };
  const catNames = { "manual": "天机起课", "量化": "量化", "liuren": "六壬" };
  if (!tp) {
    setV('tpCat', '--'); setV('tpTarget', '--'); setV('tpTrend', '--');
    setV('tpJixiong', '--'); setV('tpStatus', '暂无记录');
    return;
  }
  setV('tpCat', catNames[tp.category] || tp.category);
  setV('tpTarget', tp.target_date || tp.date || '--');
  setV('tpTrend', tp.trend_prediction || '--');
  setV('tpJixiong', tp.jixiong || '--');
  setV('tpStatus', tp.status === 'completed' ? '已回检' : (tp.actual_result ? '已回检' : '待回检'));
}

// 【2026-08-02 词汇统一·全局】方向归一化：看涨↔涨 / 看跌↔跌 / 震荡↔平 / up↔涨 / down↔跌 / neutral↔平 / 看多↔涨 / 看空↔跌
// 全站所有方向显示共用此函数，避免各 tab 词汇打架（记录表格/总览/详情弹窗/择时信号一致）
function normDir(v) {
  if (!v) return v || '';
  const s = String(v);
  if (s.indexOf('看涨') >= 0 || s.indexOf('涨') >= 0 || s === 'up' || s.indexOf('bull') >= 0 || s.indexOf('看多') >= 0) return '涨';
  if (s.indexOf('看跌') >= 0 || s.indexOf('跌') >= 0 || s === 'down' || s.indexOf('bear') >= 0 || s.indexOf('看空') >= 0) return '跌';
  if (s.indexOf('震荡') >= 0 || s.indexOf('平') >= 0 || s === 'neutral' || s.indexOf('中性') >= 0) return '平';
  return v;
}

function renderPreds(preds) {
  // 【2026-07-31 清理】机械固定时/六亲/random 等旧类别已在诚实回测中被证伪停用，
  // 即使历史备份(如 stock_predictions.json.bak_pre_tianji)被重新加载，也一律过滤，
  // 避免污染"次日预测"面板。仅保留天机起课(manual)与量化(量化)等有效类别。
  const DEPRECATED = new Set(['fixed_time','ri_gan_pian_cai','ri_zhi_pian_cai','ri_gan_shi_shen','ri_zhi_shi_shen','ri_gan_zheng_yin','ri_gan_pian_yin','ri_zhi_zheng_yin','ri_zhi_pian_yin','random','ml_predict']);
  if (!Array.isArray(preds)) preds = [];
  preds = preds.filter(function(p){ return p && !DEPRECATED.has(p.category); });
  const catNames = {manual:'天机起课', '量化':'量化', liuren:'六壬'};
  document.getElementById('predCount').textContent = preds.length + '条';
  const tbody = document.getElementById('predTable');
  tbody.innerHTML = preds.map(d => {
    const trendN = normDir(d.trend_prediction);
    const actualN = normDir(d.actual_result);
    let verdict = '';
    let vcls = '';
    if (d.actual_result) {
      if (trendN === actualN) { verdict = '正确'; vcls = 'tag-correct'; }
      else if (d.actual_result && d.trend_prediction && normDir(d.trend_prediction).indexOf(actualN) >= 0) { verdict = '部分'; vcls = 'tag-partial'; }
      else { verdict = '错误'; vcls = 'tag-wrong'; }
    }
    
    // 预测周期格式化（含周期类型标签）
    let targetDate = '';
    if (d.target_date) {
      const td = d.target_date;
      // 计算周期类型
      let periodType = '';
      let periodColor = '';
      let daysDiff = '';
      try {
        const target = new Date(td);
        const today = new Date();
        today.setHours(0, 0, 0, 0);
        const diffMs = target - today;
        const diffDays = Math.ceil(diffMs / (1000 * 60 * 60 * 24));
        daysDiff = Math.abs(diffDays) + '天';
        
        if (diffDays <= 1) {
          periodType = '当日';
          periodColor = '#dc2626';
        } else if (diffDays <= 7) {
          periodType = '周度';
          periodColor = '#f59e0b';
        } else if (diffDays <= 30) {
          periodType = '月度';
          periodColor = '#8b5cf6';
        } else {
          periodType = '远期';
          periodColor = '#0891b2';
        }
      } catch(e) {
        periodType = '';
      }
      
      const periodTag = periodType 
        ? `<span style="background:${periodColor};color:#fff;padding:1px 6px;border-radius:3px;font-size:10px;font-weight:500;margin-right:4px;">${periodType}</span>`
        : '';
      
      targetDate = `<span style="background:#e0e7ff;color:#4338ca;padding:2px 8px;border-radius:4px;font-size:11px;font-weight:600;">${periodTag}📅 ${td}</span>`;
    } else if (d.date) {
      targetDate = `<span style="background:#f3f4f6;color:#6b7280;padding:2px 8px;border-radius:4px;font-size:11px;">📅 ${d.date}</span>`;
    }
    
    // 毕法赋红色标记
    let bifaFlag = '';
    let rowStyle = '';
    if (d.bifa_red_count > 0) {
      bifaFlag = ' <span style="background:#dc2626;color:#fff;padding:1px 5px;border-radius:3px;font-size:10px;" title="漏报：'+d.bifa_reds.join(', ')+'">🔴'+d.bifa_red_count+'</span>';
      rowStyle = 'border-left:3px solid #dc2626; background:rgba(220,38,38,0.08);';
    }
    return `<tr style="cursor:pointer;${rowStyle}" data-id="${d.id || ''}" onclick="showDetail('${d.id || ''}')">
      <td>${d.predict_time || ''}</td>
      <td>${targetDate}</td>
      <td>${catNames[d.category] || d.category}${bifaFlag}</td>
      <td class="${trendN === '涨' ? 'text-up' : trendN === '跌' ? 'text-down' : ''}">${trendN}</td>
      <td>${d.jixiong || ''}</td>
      <td>${d.ref_price || ''}</td>
      <td class="${actualN === '涨' ? 'text-up' : actualN === '跌' ? 'text-down' : ''}">${d.actual_result ? actualN : '<span class="text-muted">待收盘</span>'}</td>
      <td>${d.actual_price || ''}</td>
      <td>${verdict ? '<span class="tag-result '+vcls+'">'+verdict+'</span>' : ''}</td>
    </tr>`;
  }).join('');
}

async function showDetail(predId) {
  if (!predId) return;
  const modal = document.getElementById('detailModal');
  try {
    const resp = await fetch(API+'/api/prediction/'+encodeURIComponent(predId));
    const d = await resp.json();
    if (d.error) { alert(d.error); return; }

    // 【2026-07-31 清理】旧机械类别已停用，仅保留天机起课等有效类别名称映射。
    const catNames = {manual:'天机起课', '量化':'量化', liuren:'六壬'};
    const cat = catNames[d.category] || d.category || '--';

    // 【2026-08-02 修复】默认展示六壬区块（课理分析/综合判断/推理过程）；量化类别在下方分支隐藏
    document.getElementById('liurenSections').style.display = '';

    // 【2026-08-02 修复】量化类别走专属渲染（标的信息+量化指标），不套六壬模板
    if (d.category === '量化') {
      document.getElementById('modalTitle').textContent = '📈 ' + (d.name||'量化') + ' — ' + (normDir(d.trend_prediction) || '--');
      document.getElementById('modalSubtitle').textContent = d.predict_time + '  |  开课日期: ' + (d.date || '--') + '  |  ' + '预测目标: ' + (d.target_date || d.date || '--') + '  |  ID: ' + d.id;
      // 结果条
      document.getElementById('modalResult').innerHTML =
        '<div class="item"><span class="lbl">趋势</span><span class="val">' + (normDir(d.trend_prediction) || '--') + '</span></div>' +
        '<div class="item"><span class="lbl">综合评分</span><span class="val">' + (d.score != null ? d.score.toFixed(1) : '--') + '</span></div>' +
        '<div class="item"><span class="lbl">置信度</span><span class="val">' + (d.confidence != null ? d.confidence + '%' : '--') + '</span></div>' +
        (d.price != null ? '<div class="item"><span class="lbl">基准价</span><span class="val">' + d.price.toFixed(2) + '</span></div>' : '');
      // 量化指标卡 + 趋势对比 + 评分仪表（全套增强）
      const trendColor = d.ma_trend === 'strong_bearish' ? '#27ae60' : (d.ma_trend === 'bearish' ? '#f59e0b' : (d.ma_trend === 'bullish' ? '#e74c3c' : (d.ma_trend === 'strong_bullish' ? '#dc2626' : '#6b7280')));
      const trendCN = {strong_bullish:'强势上涨', bullish:'温和上涨', neutral:'震荡', bearish:'温和下跌', strong_bearish:'强势下跌'}[d.ma_trend] || d.ma_trend || '--';
      const fmt = v => v == null ? '--' : (typeof v === 'number' ? v.toFixed(2) : v);

      // —— 辅助：方向映射 / 实际方向 / 交易日倒计时 / 进度条 ——
      /* 涨跌配色全站统一：涨=红/跌=绿 */
      const DIR = {
        strong_bearish:{cn:'强势下跌',arrow:'↓',color:'#27ae60',lvl:-2},
        bearish:{cn:'温和下跌',arrow:'↓',color:'#f59e0b',lvl:-1},
        neutral:{cn:'震荡',arrow:'→',color:'#6b7280',lvl:0},
        bullish:{cn:'温和上涨',arrow:'↑',color:'#e74c3c',lvl:1},
        strong_bullish:{cn:'强势上涨',arrow:'↑',color:'#dc2626',lvl:2},
      };
      const pInfo = DIR[d.ma_trend] || {cn:(d.trend_prediction||'--'),arrow:'→',color:'#6b7280',lvl:0};
      const sign = l => l>0?1:(l<0?-1:0);
      const actualDir = res => {
        if(res==null) return null;
        const s=String(res);
        if(s.indexOf('涨')>=0) return {cn:'上涨',arrow:'↑',color:'#e74c3c',lvl:1};
        if(s.indexOf('跌')>=0) return {cn:'下跌',arrow:'↓',color:'#27ae60',lvl:-1};
        if(s.indexOf('震荡')>=0||s.indexOf('平')>=0) return {cn:'震荡',arrow:'→',color:'#6b7280',lvl:0};
        return {cn:s,arrow:'→',color:'#6b7280',lvl:0};
      };
      const aInfo = actualDir(d.actual_result);
      const tradingDaysLeft = targetStr => {
        if(!targetStr) return null;
        const tgt=new Date(String(targetStr).replace(/-/g,'/'));
        const today=new Date();
        const cur=new Date(today.getFullYear(),today.getMonth(),today.getDate());
        cur.setDate(cur.getDate()+1); let n=0;
        while(cur<=tgt){ const w=cur.getDay(); if(w!==0&&w!==6) n++; cur.setDate(cur.getDate()+1); }
        return n;
      };
      const barRow = (label,val,color) =>
        '<div style="margin-bottom:8px;">'+
          '<div style="display:flex;justify-content:space-between;font-size:11px;color:#64748b;margin-bottom:3px;"><span>'+label+'</span><span>'+Math.round(val)+'%</span></div>'+
          '<div style="height:8px;background:#e5e7eb;border-radius:4px;overflow:hidden;"><div style="height:100%;width:'+Math.max(0,Math.min(100,val))+'%;background:'+color+';border-radius:4px;"></div></div>'+
        '</div>';

      // —— 实际方向区块内容（有回检→命中标记；无→待验证+倒计时）——
      let aHtml;
      if(aInfo){
        const hit = sign(aInfo.lvl)===sign(pInfo.lvl);
        aHtml = '<div style="font-size:22px;font-weight:800;color:'+aInfo.color+'">'+aInfo.arrow+'</div>'+
                '<div style="font-size:13px;font-weight:600;color:'+aInfo.color+'">'+aInfo.cn+'</div>'+
                '<div style="margin-top:6px;font-size:11px;font-weight:700;color:'+(hit?'#16a34a':'#dc2626')+'">'+(hit?'✓ 命中':'✗ 失准')+'</div>';
      } else {
        const left = tradingDaysLeft(d.target_date);
        const cd = (left!=null && left>0) ? ('距验证还有 <b style="color:#475569;">'+left+'</b> 个交易日') : '已到期，待系统回检';
        aHtml = '<div style="font-size:16px;font-weight:700;color:#94a3b8;margin-top:6px;">待验证</div>'+
                '<div style="font-size:11px;color:#94a3b8;margin-top:6px;line-height:1.5;">目标 '+d.target_date+'<br>'+cd+'</div>';
      }

      // —— 趋势对比卡（预测 vs 实际）——
      const cmpHtml =
        '<div style="background:#f8f9fc;border-radius:8px;padding:14px 16px;margin-top:12px;">'+
          '<div style="font-size:13px;font-weight:600;color:#475569;margin-bottom:10px;">🔄 趋势对比（预测 vs 实际）</div>'+
          '<div style="display:flex;gap:12px;align-items:stretch;">'+
            '<div style="flex:1;background:#fff;border-radius:6px;padding:10px;text-align:center;border:1px solid #e2e8f0;">'+
              '<div style="font-size:11px;color:#94a3b8;margin-bottom:6px;">预测方向</div>'+
              '<div style="font-size:24px;font-weight:800;color:'+pInfo.color+'">'+pInfo.arrow+'</div>'+
              '<div style="font-size:13px;font-weight:600;color:'+pInfo.color+'">'+pInfo.cn+'</div>'+
            '</div>'+
            '<div style="display:flex;align-items:center;justify-content:center;font-size:16px;color:#cbd5e1;font-weight:700;">VS</div>'+
            '<div style="flex:1;background:#fff;border-radius:6px;padding:10px;text-align:center;border:1px solid #e2e8f0;">'+
              '<div style="font-size:11px;color:#94a3b8;margin-bottom:6px;">实际方向</div>'+ aHtml +
            '</div>'+
          '</div>'+
        '</div>';

      // —— 多空评分仪表 ——
      const spct = Math.max(0, Math.min(100, (d.score+100)/2));
      const gaugeHtml =
        '<div style="background:#f8f9fc;border-radius:8px;padding:14px 16px;margin-top:12px;">'+
          '<div style="font-size:13px;font-weight:600;color:#475569;margin-bottom:14px;">📐 多空评分仪表（'+(d.score!=null?d.score.toFixed(1):'--')+'）</div>'+
          '<div style="position:relative;height:22px;border-radius:11px;background:linear-gradient(90deg,#dc2626 0%,#f97316 25%,#e5e7eb 47%,#e5e7eb 53%,#86efac 75%,#15803d 100%);"></div>'+
          '<div style="position:relative;height:0;">'+
            '<div style="position:absolute;top:-28px;left:'+spct+'%;transform:translateX(-50%);font-size:13px;line-height:1;color:#0f172a;">▼</div>'+
          '</div>'+
          '<div style="display:flex;justify-content:space-between;font-size:10px;color:#94a3b8;margin-top:4px;"><span>-100 深跌</span><span>0</span><span>+100 深涨</span></div>'+
        '</div>';

      // —— 信号强度 + 置信度 双条 ——
      const strength = d.score!=null ? Math.min(100, Math.abs(d.score)) : 0;
      const conf = d.confidence!=null ? d.confidence : 0;
      const barsHtml =
        '<div style="background:#f8f9fc;border-radius:8px;padding:14px 16px;margin-top:12px;">'+
          '<div style="font-size:13px;font-weight:600;color:#475569;margin-bottom:10px;">📊 信号强度与置信度</div>'+
          barRow('信号强度（|评分|）', strength, '#f59e0b') +
          barRow('置信度', conf, '#3b82f6') +
        '</div>';

      const gridHtml =
        '<div style="display:flex;gap:8px;margin-bottom:12px;font-size:12px;">' +
          '<span style="background:#eee;border-radius:3px;padding:3px 10px;">标的 <b>' + (d.name||'--') + '</b></span>' +
          '<span style="background:#eee;border-radius:3px;padding:3px 10px;">代码 <b>' + (d.etf||'--') + '</b></span>' +
          '<span style="background:#eee;border-radius:3px;padding:3px 10px;">方法 <b>' + (d.method||'量化') + '</b></span>' +
        '</div>' +
        '<div style="background:#f8f9fc;border-radius:8px;padding:14px 16px;">' +
          '<div style="font-size:13px;font-weight:600;color:#16a34a;margin-bottom:10px;">📊 量化指标</div>' +
          '<div style="display:grid;grid-template-columns:1fr 1fr;gap:8px 16px;font-size:13px;">' +
            '<div><span style="color:#6b7280;">20日动量：</span><b>' + fmt(d.momentum_20d) + '</b></div>' +
            '<div><span style="color:#6b7280;">波动率：</span><b>' + fmt(d.volatility) + '</b></div>' +
            '<div><span style="color:#6b7280;">RSI(14)：</span><b>' + fmt(d.rsi) + '</b></div>' +
            '<div><span style="color:#6b7280;">建议仓位：</span><b>' + fmt(d.position) + '%</b></div>' +
            '<div style="grid-column:1/-1;"><span style="color:#6b7280;">均线趋势：</span><b style="color:' + trendColor + ';">' + trendCN + '</b></div>' +
          '</div>' +
        '</div>' +
        cmpHtml + gaugeHtml + barsHtml;
      document.getElementById('modalGrid').innerHTML = gridHtml;
      // 量化类别：隐藏全部六壬相关区块（课理分析/综合判断/推理过程），不显示任何六壬内容
      document.getElementById('liurenSections').style.display = 'none';
      const modal = document.getElementById('detailModal');
      modal.classList.add('show');
      return;
    }

    document.getElementById('modalTitle').textContent = '🔮 ' + cat + ' — ' + (normDir(d.trend_prediction) || '--');
    document.getElementById('modalSubtitle').textContent = d.predict_time + '  |  开课日期: ' + (d.date || '--') + '  |  ' + '预测目标: ' + (d.target_date || d.date || '--') + '  |  ID: ' + d.id;

    // 结果条（方向统一走 normDir：看跌→跌、看涨→涨、震荡→平）
    document.getElementById('modalResult').innerHTML =
      '<div class="item"><span class="lbl">趋势</span><span class="val">' + (normDir(d.trend_prediction) || '--') + '</span></div>' +
      '<div class="item"><span class="lbl">吉凶</span><span class="val">' + (d.jixiong || '--') + '</span></div>' +
      (d.actual_result ? '<div class="item"><span class="lbl">实际结果</span><span class="val">' + normDir(d.actual_result) + '</span></div>' : '') +
      (d.actual_details && d.actual_details.price ? '<div class="item"><span class="lbl">实际价</span><span class="val">' + d.actual_details.price.toFixed(2) + '</span></div>' : '');

    // === 天机趋势对比卡（心动预测 vs 实际，验证六壬方向能力 vs 55.3% 基线）===
    const TJDIR = {down:{cn:'跌',arrow:'↓',color:'#27ae60',lvl:-1}, up:{cn:'涨',arrow:'↑',color:'#e74c3c',lvl:1}, flat:{cn:'平',arrow:'→',color:'#6b7280',lvl:0}};
    const _pI = TJDIR[d.tianji_updown] || {cn:normDir(d.trend_prediction)||'--',arrow:'→',color:'#6b7280',lvl:0};
    const _sign = l => l>0?1:(l<0?-1:0);
    const _aDir = res => {
      if(res==null) return null;
      if(res==='up') return {cn:'涨',arrow:'↑',color:'#e74c3c',lvl:1};
      if(res==='down') return {cn:'跌',arrow:'↓',color:'#27ae60',lvl:-1};
      return {cn:normDir(res),arrow:'→',color:'#6b7280',lvl:0};
    };
    const _tLeft = tstr => {
      if(!tstr) return null;
      const tgt=new Date(String(tstr).replace(/-/g,'/'));
      const today=new Date();
      const cur=new Date(today.getFullYear(),today.getMonth(),today.getDate());
      cur.setDate(cur.getDate()+1); let n=0;
      while(cur<=tgt){ const w=cur.getDay(); if(w!==0&&w!==6) n++; cur.setDate(cur.getDate()+1); }
      return n;
    };
    let _aHtml;
    const _aI = _aDir(d.actual_direction);
    if(_aI){
      const _hit = _sign(_aI.lvl)===_sign(_pI.lvl);
      _aHtml = '<div style="font-size:22px;font-weight:800;color:'+_aI.color+'">'+_aI.arrow+'</div>'+
               '<div style="font-size:13px;font-weight:600;color:'+_aI.color+'">'+_aI.cn+'</div>'+
               '<div style="margin-top:6px;font-size:11px;font-weight:700;color:'+(_hit?'#16a34a':'#dc2626')+'">'+( _hit?'✓ 命中':'✗ 失准')+'</div>';
    } else {
      const _left = _tLeft(d.target_date);
      const _cd = (_left!=null && _left>0) ? ('距验证还有 <b style="color:#475569;">'+_left+'</b> 个交易日') : '已到期，待系统回检';
      _aHtml = '<div style="font-size:16px;font-weight:700;color:#94a3b8;margin-top:6px;">待验证</div>'+
               '<div style="font-size:11px;color:#94a3b8;margin-top:6px;line-height:1.5;">目标 '+d.target_date+'<br>'+_cd+'</div>';
    }
    const tjCmpHtml =
      '<div style="background:#f8f9fc;border-radius:8px;padding:14px 16px;margin-bottom:12px;">'+
        '<div style="font-size:13px;font-weight:600;color:#475569;margin-bottom:10px;">🔄 心动预测 vs 实际方向（验证六壬方向能力 vs 55.3% 基线）</div>'+
        '<div style="display:flex;gap:12px;align-items:stretch;">'+
          '<div style="flex:1;background:#fff;border-radius:6px;padding:10px;text-align:center;border:1px solid #e2e8f0;">'+
            '<div style="font-size:11px;color:#94a3b8;margin-bottom:6px;">心动预测</div>'+
            '<div style="font-size:24px;font-weight:800;color:'+_pI.color+'">'+_pI.arrow+'</div>'+
            '<div style="font-size:13px;font-weight:600;color:'+_pI.color+'">'+_pI.cn+'</div>'+
          '</div>'+
          '<div style="display:flex;align-items:center;justify-content:center;font-size:16px;color:#cbd5e1;font-weight:700;">VS</div>'+
          '<div style="flex:1;background:#fff;border-radius:6px;padding:10px;text-align:center;border:1px solid #e2e8f0;">'+
            '<div style="font-size:11px;color:#94a3b8;margin-bottom:6px;">实际方向</div>'+ _aHtml +
          '</div>'+
        '</div>'+
      '</div>';

    // === 参数行 ===
    let gridHtml = tjCmpHtml + '<div style="display:flex;gap:8px;margin-bottom:12px;font-size:12px;">' +
      '<span style="background:#eee;border-radius:3px;padding:3px 10px;">日柱 <b>'+(d.rizhu||'--')+'</b></span>' +
      '<span style="background:#eee;border-radius:3px;padding:3px 10px;">月将 <b>'+(d.yue_jiang||'--')+'</b></span>' +
      '<span style="background:#eee;border-radius:3px;padding:3px 10px;">占时 <b>'+(d.shi_chen||'--')+'</b></span>' +
      '<span style="background:#eee;border-radius:3px;padding:3px 10px;">课体 <b>'+(d.keti||'--')+'</b></span>' +
      '<span style="background:#eee;border-radius:3px;padding:3px 10px;">发用 <b>'+(d.fayong||'--')+'</b></span>' +
      '</div>';

    // === 三大块: 天地盘 | 四课 | 三传 (CSS Grid 均分) ===
    gridHtml += '<div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:10px;align-items:start;">';

    // -- 天地盘 (左, 只显示天盘+天将, 地盘固定不显示) --
    if (d.tiandi_pan && Object.keys(d.tiandi_pan).length) {
        var diLayout = [['巳','午','未','申'],['辰','','','酉'],['卯','','','戌'],['寅','丑','子','亥']];
        var tp = '<div style="background:#f8f9fc;border-radius:6px;padding:6px;">';
        tp += '<div style="font-size:10px;color:#999;margin-bottom:4px;">🗺 天盘</div>';
        tp += '<table style="border-collapse:collapse;font-size:12px;">';
        for(var r=0;r<4;r++){
            tp += '<tr>';
            for(var c=0;c<4;c++){
                var di = diLayout[r][c];
                if(!di){ tp += '<td></td>'; continue; }
                var pi = d.tiandi_pan[di]||{};
                var tpan = (typeof pi==='object'?(pi['天盘']||pi.tianpan||''):pi)||di;
                var tjiang = (typeof pi==='object'?(pi['天将']||pi.tianjiang||''):'');
                var tjShort = {'贵':'贵','蛇':'蛇','雀':'雀','合':'合','勾':'勾','龙':'龙','空':'空','虎':'虎','常':'常','玄':'玄','阴':'阴','后':'后'}[tjiang]||tjiang;
                tp += '<td style="border:1px solid #eee;padding:2px 4px;text-align:center;min-width:34px;">'+
                    '<div style="color:#999;font-size:9px;">'+tjShort+'</div>'+
                    '<div style="font-weight:700;font-size:14px;color:#f59e0b;">'+tpan+'</div></td>';
            }
            tp += '</tr>';
        }
        tp += '</table></div>';
        gridHtml += tp;
    } else {
        gridHtml += '<div style="background:#f8f9fc;border-radius:6px;padding:6px;font-size:10px;color:#999;">天盘<br>月将'+(d.yue_jiang||'?')+'加时'+(d.shi_chen||'?')+'</div>';
    }

    // 构建12地支→天将完整映射 (贵神裸算)
    var dzTj = {};
    var rg2=(d.rizhu||'甲')[0];
    var guiren={'甲':'丑','戊':'丑','庚':'丑','乙':'子','己':'申','丙':'亥','丁':'酉','壬':'巳','癸':'卯','辛':'午'};
    var gz=guiren[rg2]||'丑', sc2=(d.shi_chen||'子');
    var Z12='子丑寅卯辰巳午未申酉戌亥', TJ='贵蛇雀合勾龙空虎常玄阴后';
    var gi=Z12.indexOf(gz);
    // 真太阳时日落计算
    var doy=new Date().getFullYear()%4==0?new Date(new Date().getFullYear(),0,0):new Date(new Date().getFullYear(),0,0);
    // 简化: 根据月将推断月份
    var yj_m={'子':11,'丑':12,'寅':1,'卯':2,'辰':3,'巳':4,'午':5,'未':6,'申':7,'酉':8,'戌':9,'亥':10};
    var month=yj_m[(d.yue_jiang||'未')]||7;
    var day=new Date(2026,month-1,15);  // 取月中
    var doy=Math.floor((day-new Date(2026,0,0))/86400000);
    var decl=23.45*Math.sin((360/365*(284+doy))*Math.PI/180);
    var cosH=-Math.tan(25.1*Math.PI/180)*Math.tan(decl*Math.PI/180);
    cosH=Math.max(-1,Math.min(1,cosH));
    var halfday=Math.acos(cosH)*180/Math.PI/15;
    var B=360/365*(doy-81)*Math.PI/180;
    var eot=9.87*Math.sin(2*B)-7.53*Math.cos(B)-1.5*Math.sin(B);
    var noonLocal=12*60+4*(120-105.5)+eot;
    var sunsetH=(noonLocal+halfday*60)/60;
    var scH={'子':23,'丑':1,'寅':3,'卯':5,'辰':7,'巳':9,'午':11,'未':13,'申':15,'酉':17,'戌':19,'亥':21};
    var isDay=(scH[sc2]||0)+2 <= sunsetH;
    for(var j=0;j<12;j++){
        var di=Z12[(isDay?(gi+j):(gi+12-j))%12];
        dzTj[di]=TJ[j];
    }
    // 三传天将覆盖(仅非空)
    (d.sanchuan_tianjiang||[]).forEach(function(stj){
        if(stj.indexOf('(')>=0){
            var ddz=stj.split('(')[0].trim(), dtj=stj.split('(')[1].split(')')[0].trim();
            if(dtj) dzTj[ddz]=dtj;  // 仅当天将非空才覆盖
        }
    });

    // -- 四课 (中) — 统一格式：4列网格，顶栏天将标签/蓝字地支/干支组合/底栏课号 --
    var sikeTp = '';
    if(d.sike && d.sike.length){
        // 天将短名映射 → 显示用标签
        var tjLabelMap = {'贵':'贵人','蛇':'螣蛇','雀':'朱雀','合':'六合','勾':'勾陈','龙':'青龙','空':'天空','虎':'白虎','常':'太常','玄':'玄武','阴':'太阴','后':'天后',
            '贵人':'贵人','腾蛇':'螣蛇','朱雀':'朱雀','六合':'六合','勾陈':'勾陈','青龙':'青龙','天空':'天空','白虎':'白虎','太常':'太常','玄武':'玄武','太阴':'太阴','天后':'天后'};
        sikeTp = '<div style="background:#f8f9fc;border-radius:8px;padding:10px 12px;">'+
            '<div style="font-size:11px;color:#999;margin-bottom:8px;font-weight:600;">📋 四课</div>'+
            '<table style="width:100%;border-collapse:collapse;table-layout:fixed;">'+
            '<tr>';  // 顶栏：天将标签
        var headerLabels = [];
        for(var si=3;si>=0;si--){
            var s=d.sike[si], up=s[1]||'';
            var tj=dzTj[up]||'', lbl=tjLabelMap[tj]||tj||' ';
            headerLabels.push('<td style="text-align:center;font-size:10px;color:#94a3b8;padding:2px 0 6px;">'+lbl+'</td>');
        }
        sikeTp += headerLabels.join('') + '</tr><tr>';  // 地支行
        var dzRow = [];
        for(var si=3;si>=0;si--){
            var s=d.sike[si], up=s[1]||'';
            dzRow.push('<td style="text-align:center;font-size:18px;font-weight:700;color:#60a5fa;padding:4px 0;">'+up+'</td>');
        }
        sikeTp += dzRow.join('') + '</tr><tr>';  // 干支组合行
        var gzRow = [];
        for(var si=3;si>=0;si--){
            var s=d.sike[si], up=s[1]||'', down=s[2]||'';
            gzRow.push('<td style="text-align:center;font-size:11px;color:#6b7280;padding:2px 0 6px;">'+down+'</td>');
        }
        sikeTp += gzRow.join('') + '</tr><tr>';  // 课号行
        var numRow = [];
        var keNames = ['第一课','第二课','第三课','第四课'];
        for(var si=3;si>=0;si--){
            numRow.push('<td style="text-align:center;font-size:9px;color:#9ca3af;padding:2px 0;">'+keNames[3-si]+'</td>');
        }
        sikeTp += numRow.join('') + '</tr></table></div>';
    }
    gridHtml += sikeTp;

    // -- 三传 (右) --（六亲/遁干/旬空 统一走共享函数 _dunG/_liuQ/_xunKong）
    var rg=(d.rizhu||'甲')[0], rz=(d.rizhu||'子').slice(-1);
    var xk=_xunKong(rg, rz);
    function dunG(dz){ return _dunG(rg, dz); }
    function liuQ(dz){ return _liuQ(rg, dz); }
    var scHtml = '';
    if(d.sanchuan && d.sanchuan.length){
        scHtml = '<div style="background:#f8f9fc;border-radius:8px;padding:10px 12px;">'+
            '<div style="font-size:11px;color:#999;margin-bottom:8px;font-weight:600;">🔗 三传</div>'+
            '<table style="width:100%;border-collapse:collapse;font-size:13px;">'+
            '<tr style="color:#9ca3af;font-size:10px;">'+
            '<td style="padding:4px 0 8px;width:22%;">六亲</td>'+
            '<td style="padding:4px 0 8px;width:39%;">地支</td>'+
            '<td style="padding:4px 0 8px;width:39%;">天将</td></tr>';
        for(var i=0;i<d.sanchuan.length;i++){
            var dz=d.sanchuan[i], tj=(d.sanchuan_tianjiang||[])[i]||'', dg=dunG(dz);
            var isXK=xk.indexOf(dz)>=0, gdz=isXK?'○'+dz:dg+dz, lqName=liuQ(dz);
            scHtml += '<tr style="border-top:1px solid #eee;">'+
                '<td style="padding:6px 0;color:#6b7280;">'+lqName+'</td>'+
                '<td style="padding:6px 0;font-weight:700;color:#d97706;font-family:monospace;font-size:14px;">'+gdz+'</td>'+
                '<td style="padding:6px 0;color:#6b7280;">'+tj+'</td></tr>';
        }
        scHtml += '</table></div>';
    }
    gridHtml += scHtml;

    gridHtml += '</div>';  // 闭合三大块grid

    document.getElementById('modalGrid').innerHTML = gridHtml;

    // 课理分析
    var analysisText = '暂无详细分析';
    if (d.analysis) {
      if (typeof d.analysis === 'string') {
        analysisText = d.analysis;
      } else if (typeof d.analysis === 'object') {
        // 兼容旧数据 dict 格式：提取课体断语作为摘要
        var kd = d.analysis.keti_duanyu;
        if (kd) {
          var ketiName = kd.keti_name || d.keti || '?';
          var ketiLevel = kd.level || kd['等级'] || '?';
          var ketiDuanyu = kd.duanyu || kd['断语'] || kd.zonglun || '无';
          analysisText = '课体: ' + ketiName
            + '（' + ketiLevel + '）\n'
            + '断语: ' + ketiDuanyu;
          if (kd.is_daxiong) analysisText += '\n⚠️ 为大凶课！';
          
          // 三传课格信息
          var sk = kd.sanchuan_kege || {};
          var kegeList = sk.课格列表 || [];
          if (kegeList.length > 0) {
            analysisText += '\n\n═══ 三传课格 ═══';
            kegeList.forEach(function(kg) {
              var detail = sk.课格详情[kg] || {};
              analysisText += '\n【' + kg + '】' + (detail.吉凶 ? ' [' + detail.吉凶 + ']' : '');
              var ss = detail.股市信号 || {};
              if (ss.倾向) {
                analysisText += '\n  股市信号: ' + ss.倾向 + ' (强度' + (ss.信号强度||0).toFixed(1) + ')';
                if (ss.解读) analysisText += '\n  ' + ss.解读;
                if (ss.风险提示) analysisText += '\n  ⚠ ' + ss.风险提示;
              }
            });
            var signals = sk.股市信号 || {};
            if (signals.操作建议) {
              analysisText += '\n\n💡 ' + signals.操作建议;
            }
          }
        } else {
          analysisText = JSON.stringify(d.analysis, null, 2);
        }
      }
    }
    document.getElementById('modalAnalysis').textContent = analysisText;

    // 推理过程：优先用 reasoning_chain（17步），为空则回退到 prediction.reasons
    const rc = d.reasoning_chain || {};
    const rcKeys = Object.keys(rc).length;
    const reasons = (d.prediction && d.prediction.reasons) || [];
    let rcHtml = '';
    
    if (rcKeys > 0) {
      // 有推理链数据，按17步模板渲染
      const order = ['课体','四课加临','用神五气','三传','六亲分析','天将分析','五行','旬空','旺衰','神煞','刑冲合害','八杀','十二气财星','身强身弱','趋势判断','应期','风险提示'];
      rcHtml = '<div style="margin-bottom:4px;color:#94a3b8;font-size:11px;">完成 '+(d.rc_filled||rcKeys)+'/'+order.length+' 步（结构化推理）</div>';
      let totalFilled = 0;
      for (let i=0; i<order.length; i++) {
        const key = order[i];
        const val = rc[key] || '';
        if (val) {
          totalFilled++;
          rcHtml += '<div class="step"><div class="step-title">✅ '+(i+1)+'. '+key+'</div><div class="step-content">'+val+'</div></div>';
        } else {
          rcHtml += '<div class="step" style="opacity:0.3"><div class="step-title">⬜ '+(i+1)+'. '+key+'</div><div class="step-content" style="color:#666;">— 未填充</div></div>';
        }
      }
    } else if (reasons.length > 0) {
      // 无推理链，但有条目式原因列表
      rcHtml = '<div style="margin-bottom:4px;color:#94a3b8;font-size:11px;">📊 综合评分推理（共 ' + reasons.length + ' 条）</div>';
      reasons.forEach(function(r, i) {
        rcHtml += '<div class="step"><div class="step-title">📌 因素 '+(i+1)+'</div><div class="step-content">'+r+'</div></div>';
      });
    } else {
      // 完全无数据
      rcHtml = '<div style="padding:20px;text-align:center;color:#999;">暂无推理过程数据（运行起课预测后生成）</div>';
    }
    document.getElementById('modalReasoning').innerHTML = rcHtml;

    // === 综合判断 (混合推理：本地 DeepSeek 深度裁决 + 确定性规则判 + 知识点证据链) ===
    const h = d.holistic_synthesis || {};
    const hb = document.getElementById('modalHolistic');
    if (hb) {
      const llm = h.llm_verdict || {};
      const hasLlm = llm && (llm.narrative || llm.zongduan);
      if (h && (h.trend || (h.axes && Object.keys(h.axes).length) || hasLlm)) {
        const trendColor = (llm.trend||h.trend)==='涨' ? '#ef4444' : ((llm.trend||h.trend)==='跌' ? '#22c55e' : '#eab308');
        const useTrend = llm.trend || h.trend || '-';
        const useConf = (llm.confidence!=null ? llm.confidence : h.confidence);
        // 辨证五轴（确定性）
        const ax = h.axes || {};
        const axOrder = ['动静','刚柔','主客','虚实','始终'];
        let axHtml = '';
        for (const k of axOrder) {
          const v = ax[k] || {};
          axHtml += '<span style="background:#1e293b;border:1px solid #334155;border-radius:4px;padding:2px 8px;font-size:11px;margin:2px 4px 2px 0;display:inline-block;">'
            + '<b>'+k+'</b> '+(v.dir||'?')+' <i style="color:#f59e0b;font-style:normal;">('+(v.signed>0?'+':'')+(v.signed||0)+')</i></span>';
        }
        // 规则判证据链
        const ev = h.evidence || [];
        let evHtml = ev.map(function(e){ return '<li style="margin:2px 0;">'+e+'</li>'; }).join('');
        // 引例（CBR）
        const rcs = h.retrieved_cases || [];
        let rcHtml = rcs.slice(0,2).map(function(c){
          return '<div style="font-size:11px;color:#cbd5e1;background:#1e293b;border-left:3px solid #f59e0b;border-radius:3px;padding:5px 8px;margin-top:5px;">'
            + '📜 《'+c.name+'》['+c.source+'] 相似度'+c.score+'：'+ (c.interpretation||'').slice(0,130) +'</div>';
        }).join('');

        // —— 双轨：① DeepSeek 深度裁决（主叙事） ② 确定性规则判（可折叠） ——
        let llmBlock = '';
        if (hasLlm) {
          const degraded = h.llm_degraded ? '<span style="font-size:10px;color:#f87171;border:1px solid #f87171;border-radius:3px;padding:0 5px;margin-left:6px;">模型不可用·已降级规则判</span>' : '';
          llmBlock =
            '<div style="border:1px solid #334155;border-radius:8px;padding:10px;background:linear-gradient(135deg,#0b1220,#111827);margin-bottom:10px;">'
            + '<div style="display:flex;align-items:center;gap:10px;flex-wrap:wrap;margin-bottom:6px;">'
              + '<span style="font-size:11px;color:#38bdf8;">🜂 深度裁决 · 本地 DeepSeek</span>'
              + '<span style="font-size:18px;font-weight:800;color:'+trendColor+';">'+useTrend+'</span>'
              + '<span style="font-size:11px;color:#94a3b8;">置信 '+ (useConf!=null?useConf:'-') +'</span>'
              + (h.llm_model? '<span style="font-size:10px;color:#64748b;">'+h.llm_model+'</span>':'') + degraded
            + '</div>'
            + (llm.zongduan ? '<div style="font-size:13px;font-weight:600;color:#e2e8f0;margin-bottom:5px;line-height:1.5;">'+llm.zongduan+'</div>' : '')
            + (llm.narrative ? '<div style="font-size:12px;color:#cbd5e1;line-height:1.75;white-space:pre-wrap;">'+llm.narrative+'</div>' : '')
            + (llm.axes_narrative ? '<div style="font-size:11px;color:#94a3b8;line-height:1.7;margin-top:6px;border-top:1px dashed #334155;padding-top:6px;">🧭 '+llm.axes_narrative+'</div>' : '')
            + '</div>';
        }

        // 确定性规则判（折叠）
        let ruleBlock =
          '<details style="margin-bottom:8px;"><summary style="cursor:pointer;font-size:11px;color:#94a3b8;">⚙ 确定性规则判（壬归寻原·辨证五轴·课例裁决）</summary>'
            + '<div style="margin-top:6px;">'
              + '<div style="font-size:12px;color:#cbd5e1;background:#0f172a;border-radius:6px;padding:8px;margin-bottom:8px;line-height:1.6;">'+ (h.zongduan||'') +'</div>'
              + (axHtml ? '<div style="margin-bottom:8px;">'+ axHtml +'</div>' : '')
              + (evHtml ? '<div style="font-size:11px;color:#94a3b8;margin-bottom:6px;">辨证依据：<ul style="margin:4px 0 0 16px;padding:0;line-height:1.7;">'+evHtml+'</ul></div>' : '')
              + (rcHtml ? '<div style="margin-top:4px;">'+rcHtml+'</div>' : '')
            + '</div></details>';

        hb.innerHTML = llmBlock + ruleBlock;
      } else {
        hb.innerHTML = '<div style="font-size:11px;color:#999;">本次预测无综合判断数据（重新运行起课预测生成）</div>';
      }
    }

    modal.classList.add('show');
    document.body.style.overflow = 'hidden';
  } catch (e) {
    alert('加载失败: ' + e.message);
  }
}

function closeModal() {
  document.getElementById('detailModal').classList.remove('show');
  document.body.style.overflow = '';
}
// 点击遮罩关闭
document.getElementById('detailModal').addEventListener('click', function(e) {
  if (e.target === this) closeModal();
});

function renderTrades(trades) {
  document.getElementById('tradeCount').textContent = trades.length + '笔';
  const tbody = document.getElementById('tradeTable');
  tbody.innerHTML = trades.map(t => {
    const pnl = parseFloat(t.pnl) || 0;
    const act = (t.action || '').toString();
    const isBuy = (act === '买入' || act === '买' || act === 'buy');
    // 【2026-08-02 语义】持仓中=买入流水（浮动盈亏）；已平仓=平仓记录（已实现盈亏，含买入信息提示）
    let pnlCell = pnl ? (pnl > 0 ? '+' : '') + pnl.toFixed(2) : '-';
    let extra = '';
    if (act === '平仓') {
      pnlCell = (pnl > 0 ? '+' : '') + pnl.toFixed(2);
      if (t.buy_time) extra = '<div style="font-size:10px;color:#999;">买入 ' + (t.buy_time||'') + ' @' + (parseFloat(t.buy_price)||0).toFixed(2) + '</div>';
    }
    return `<tr>
      <td>${t.time || ''}</td>
      <td>${t.category || ''}</td>
      <td style="color:${isBuy ? '#e74c3c' : '#27ae60'}">${t.action || ''}</td>
      <td>¥${parseFloat(t.price).toFixed(2)}</td>
      <td>${t.amount || 0}</td>
      <td class="${pnl > 0 ? 'text-up' : pnl < 0 ? 'text-down' : ''}">${pnlCell}${extra}</td>
    </tr>`;
  }).join('');

  // 交易统计栏
  let buyCnt = 0, sellCnt = 0, totalPnl = 0;
  trades.forEach(t => {
    const act = (t.action || '').toString();
    if (act === '买入' || act === '买' || act === 'buy') buyCnt++;
    else if (act === '平仓' || act === '卖' || act === 'sell') sellCnt++;
    const pnl = parseFloat(t.pnl) || 0;
    totalPnl += pnl;
  });
  document.getElementById('tsTotal').textContent = trades.length;
  document.getElementById('tsBuy').textContent = buyCnt;
  document.getElementById('tsSell').textContent = sellCnt;
  const pnlEl = document.getElementById('tsPnl');
  pnlEl.textContent = (totalPnl > 0 ? '+' : '') + totalPnl.toFixed(2);
  pnlEl.className = 'num ' + (totalPnl > 0 ? 'up' : totalPnl < 0 ? 'down' : 'neutral');
}

// ═══════════════ 双子系统切换 ═══════════════
var g_subsystem = 'quant';  // 全局：当前查看的子系统

function switchGlobalSubsystem(sys) {
  g_subsystem = sys;
  syncAccountTabBadge();
  // 更新顶栏徽章状态：激活的亮色，未激活的半透明
  var qBadge = document.getElementById('quantModeBadge');
  var lBadge = document.getElementById('liurenModeBadge');
  if (sys === 'quant') {
    if (qBadge) qBadge.style.opacity = '1';
    if (lBadge) lBadge.style.opacity = '0.5';
  } else {
    if (qBadge) qBadge.style.opacity = '0.5';
    if (lBadge) lBadge.style.opacity = '1';
  }
  // 同步持仓监控tab的切换按钮
  var btnQ = document.getElementById('subBtnQuant');
  var btnL = document.getElementById('subBtnLiuren');
  if (btnQ && btnL) {
    if (sys === 'quant') {
      btnQ.style.background = '#e8f5e9'; btnQ.style.color = '#2e7d32'; btnQ.classList.add('active');
      btnL.style.background = 'transparent'; btnL.style.color = '#8e44ad'; btnL.classList.remove('active');
    } else {
      btnL.style.background = '#f3e5f5'; btnL.style.color = '#6a1b9a'; btnL.classList.add('active');
      btnQ.style.background = 'transparent'; btnQ.style.color = '#2e7d32'; btnQ.classList.remove('active');
    }
  }
  // 同步绩效统计tab的切换按钮
  var pBtnQ = document.getElementById('perfSubBtnQuant');
  var pBtnL = document.getElementById('perfSubBtnLiuren');
  if (pBtnQ && pBtnL) {
    if (sys === 'quant') {
      pBtnQ.style.background = '#e8f5e9'; pBtnQ.style.color = '#2e7d32'; pBtnQ.classList.add('active');
      pBtnL.style.background = 'transparent'; pBtnL.style.color = '#8e44ad'; pBtnL.classList.remove('active');
    } else {
      pBtnL.style.background = '#f3e5f5'; pBtnL.style.color = '#6a1b9a'; pBtnL.classList.add('active');
      pBtnQ.style.background = 'transparent'; pBtnQ.style.color = '#2e7d32'; pBtnQ.classList.remove('active');
    }
  }
  // 如果当前在持仓或绩效tab，自动刷新数据；否则自动跳转到持仓监控tab（交易记录为合并流水，不按子系统展示）
  var activeTab = document.querySelector('.tab-content.active');
  if (activeTab) {
    if (activeTab.id === 'tab-positions') loadPositions();
    else if (activeTab.id === 'tab-perf') loadPerformance();
    else {
      // 不在子系统相关tab时，自动跳转到持仓监控
      switchTab('positions');
    }
  }
}

function switchSubsystem(sys) {
  switchGlobalSubsystem(sys);
  loadPositions();
}

function switchPerfSubsystem(sys) {
  switchGlobalSubsystem(sys);
  loadPerformance();
}

// ═══════════════ 选股持仓监控 ═══════════════
function screenerBuy(code, name, score) {
  var warn = '';
  if (score < 50) {
    warn = '\n⚠️ 警告：该股票量化评分仅 ' + score + '（低于买入阈值 50），属人工强制买入，请确认您已自行研判。';
  }
  if (!confirm(`确认买入 ${name}(${code}) 评分:${score} ？\n将以实时价格买入，默认1000股。${warn}\n\n当前操作账户: ${g_subsystem==='quant'?'量化':'六壬'}`)) return;
  var shares = prompt('买入股数（100的整数倍）:', '1000');
  if (!shares || parseInt(shares) < 100) { alert('最少买入100股（1手）'); return; }
  var apiPath = '/api/' + g_subsystem + '/manual_buy';
  fetch(API+apiPath, {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({code: code, name: name, shares: parseInt(shares)})
  })
  .then(function(r){ return r.json(); })
  .then(function(d){
    if (d.success) { alert('✅ ' + d.message); loadPositions(); }
    else { alert('❌ ' + (d.message || d.error || '买入失败')); }
  })
  .catch(function(e){ alert('请求失败: ' + e); });
}

function screenerSell(positionId, name) {
  if (!confirm(`确认平仓 ${name} ？将以实时价格卖出。\n\n当前操作账户: ${g_subsystem==='quant'?'量化':'六壬'}`)) return;
  var apiPath = '/api/' + g_subsystem + '/manual_sell';
  fetch(API+apiPath, {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({position_id: positionId})
  })
  .then(function(r){ return r.json(); })
  .then(function(d){
    if (d.success) { alert('✅ ' + d.message); loadPositions(); }
    else { alert('❌ ' + (d.message || d.error || '平仓失败')); }
  })
  .catch(function(e){ alert('请求失败: ' + e); });
}

// 持仓行"走势"按钮：切到「选股·个股」Tab 并展开该股K线图
function viewStockTrend(code, name) {
  switchTab('screener');
  setTimeout(function(){ showStockDetail(code, name); }, 120);
}

function loadPositions() {
  var apiPath = '/api/' + g_subsystem + '/positions';
  fetch(API+apiPath)
    .then(function(r){ return r.json(); })
    .then(function(data){
      if (!data.success) { console.error('持仓加载失败:', data.error); return; }
      renderPositions(data);
    })
    .catch(function(err){ console.error('持仓加载失败:', err); });
}

function renderPositions(data) {
  var config = data.config || {};
  var positions = data.positions || [];
  var closed = data.closed_trades || [];
  var summary = data.summary || {};
  var isLiuren = g_subsystem === 'liuren';

  // 统计栏
  document.getElementById('psCount').textContent = summary.holding_count || 0;
  document.getElementById('psCost').textContent = '¥' + ((summary.total_cost || 0)/10000).toFixed(1) + '万';
  document.getElementById('psMktVal').textContent = '¥' + ((summary.total_market_value || 0)/10000).toFixed(1) + '万';
  var pnlEl = document.getElementById('psPnl');
  var totalPnl = summary.total_pnl || 0;
  pnlEl.textContent = (totalPnl > 0 ? '+' : '') + totalPnl.toFixed(0);
  pnlEl.className = 'num ' + (totalPnl > 0 ? 'up' : totalPnl < 0 ? 'down' : 'neutral');

  // 累计交易费用 (A股佣金+印花税+过户费, 扣费后净盈亏)
  document.getElementById('psFees').textContent = '¥' + ((summary.total_fees || 0)).toFixed(0);

  // 持仓数量
  document.getElementById('posCount').textContent = positions.length + '只';

  // 持仓表格 - 动态表头
  var posTbody = document.getElementById('posTable');
  var posTable = posTbody.parentNode;
  var theadRow = posTable.querySelector('thead tr');
  var cols = ['代码','名称','买入价','现价','数量','金额','盈亏','盈亏%','到期日','来源','建议','操作'];
  if (isLiuren) { cols.splice(11, 0, '六壬信号'); }
  theadRow.innerHTML = cols.map(function(c){ return '<th>' + c + '</th>'; }).join('');
  
  if (!positions.length) {
    posTbody.innerHTML = '<tr><td colspan="' + cols.length + '" style="text-align:center;color:#bbb;padding:20px;">暂无' + (isLiuren?'六壬':'量化') + '持仓，每日 16:05 自动建仓</td></tr>';
  } else {
    posTbody.innerHTML = positions.map(function(p){
      var pnl = p.pnl || 0;
      var pnlPct = p.pnl_pct || 0;
      var pnlCls = pnl > 0 ? 'text-up' : pnl < 0 ? 'text-down' : '';
      var srcLabel = p.source === 'manual' ? '手动' : '自动';
      var lrCell = '';
      if (isLiuren) {
        var lrTrend = p.liuren_trend || '--';
        var lrJx = p.liuren_jixiong || '--';
        var lrConf = p.liuren_confidence ? (p.liuren_confidence*100).toFixed(0)+'%' : '--';
        var lrColor = lrTrend.indexOf('涨')>=0 ? 'color:#e74c3c' : lrTrend.indexOf('跌')>=0 ? 'color:#27ae60' : 'color:#999';
        lrCell = '<td style="' + lrColor + ';font-size:12px;">' + lrTrend + '/' + lrJx + ' <span style="color:#999;">' + lrConf + '</span></td>';
      }
      return '<tr>' +
        '<td style="font-family:monospace;">' + p.code + '</td>' +
        '<td>' + p.name + '</td>' +
        '<td>¥' + p.buy_price + '</td>' +
        '<td>¥' + (p.current_price || p.buy_price) + '</td>' +
        '<td>' + p.shares + '</td>' +
        '<td>¥' + ((p.amount||0)/10000).toFixed(1) + '万</td>' +
        '<td class="' + pnlCls + '" style="font-weight:600;">' + (pnl > 0 ? '+' : '') + pnl.toFixed(0) + '</td>' +
        '<td class="' + pnlCls + '" style="font-weight:600;">' + (pnlPct > 0 ? '+' : '') + pnlPct.toFixed(2) + '%</td>' +
        '<td>' + (p.hold_until||'--') + '</td>' +
        '<td>' + srcLabel + '</td>' +
        '<td>' + (p.advice||'--') + '</td>' +
        lrCell +
        '<td>' +
          '<button class="trend-btn" style="padding:4px 10px;font-size:12px;background:#3b82f6;color:#fff;border:none;border-radius:4px;cursor:pointer;margin-right:6px;" onclick="viewStockTrend(\'' + p.code + '\',\'' + (p.name||'').replace(/'/g,"\\'") + '\')">📈走势</button>' +
          '<button class="sell-btn" style="padding:4px 10px;font-size:12px;background:#27ae60;color:#fff;border:none;border-radius:4px;cursor:pointer;" onclick="screenerSell(\'' + p.id + '\',\'' + (p.name||'').replace(/'/g,"\\'") + '\')">平仓</button>' +
        '</td>' +
        '</tr>';
    }).join('');
  }

  // 已平仓记录
  document.getElementById('closedCount').textContent = (closed.length) + '笔';
  const closedTbody = document.getElementById('closedTable');
  if (!closed.length) {
    closedTbody.innerHTML = '<tr><td colspan="10" style="text-align:center;color:#bbb;padding:20px;">暂无平仓记录</td></tr>';
  } else {
    closedTbody.innerHTML = closed.map(p => {
      const pnl = p.pnl || 0;
      const pnlPct = p.pnl_pct || 0;
      const pnlCls = pnl > 0 ? 'text-up' : pnl < 0 ? 'text-down' : '';
      return `<tr>
        <td style="font-family:monospace;">${p.code}</td>
        <td>${p.name}</td>
        <td>¥${p.buy_price}</td>
        <td>¥${p.close_price||'--'}</td>
        <td class="${pnlCls}" style="font-weight:600;">${pnl > 0 ? '+' : ''}${pnl.toFixed(0)}</td>
        <td class="${pnlCls}" style="font-weight:600;">${pnlPct > 0 ? '+' : ''}${pnlPct.toFixed(2)}%</td>
        <td>${p.close_reason||'--'}</td>
        <td>${p.close_time||'--'}</td>
        <td>${p.advice||'--'}</td>
        <td><button class="trend-btn" style="padding:4px 10px;font-size:12px;background:#3b82f6;color:#fff;border:none;border-radius:4px;cursor:pointer;" onclick="viewStockTrend('${p.code}','${(p.name||'').replace(/'/g,"\\'")}')">📈走势</button></td>
      </tr>`;
    }).join('');
  }
}

// ═══════════════ 绩效统计 ═══════════════
function loadPerformance() {
  var apiPath = '/api/' + g_subsystem + '/performance';
  fetch(API+apiPath)
    .then(function(r){ return r.json(); })
    .then(function(data){
      if (!data.success) { console.error('绩效加载失败:', data.error); return; }
      renderPerformance(data);
    })
    .catch(function(err){ console.error('绩效加载失败:', err); });
}

function renderPerformance(data) {
  // 统计栏
  document.getElementById('pfTotal').textContent = data.total_trades || 0;
  document.getElementById('pfWinRate').textContent = (data.win_rate||0) + '%';
  document.getElementById('pfAvgRet').textContent = (data.avg_return_pct > 0 ? '+' : '') + (data.avg_return_pct||0) + '%';
  const totalPnl = data.total_pnl || 0;
  const pnlShow = document.getElementById('pfTotalPnl');
  pnlShow.textContent = '¥' + (totalPnl > 0 ? '+' : '') + totalPnl.toFixed(0);
  pnlShow.className = 'num ' + (totalPnl > 0 ? 'up' : totalPnl < 0 ? 'down' : 'neutral');
  document.getElementById('pfMaxDD').textContent = '¥' + (data.max_drawdown||0).toFixed(0);

  // 按建议分档
  const byAdvice = data.by_advice || {};
  const adviceTbody = document.getElementById('perfByAdvice');
  adviceTbody.innerHTML = Object.entries(byAdvice).map(([k,v]) => {
    const pnlCls = (v.avg_return||0) > 0 ? 'text-up' : 'text-down';
    return `<tr>
      <td>${k}</td><td>${v.trades}</td>
      <td>${v.win_rate}%</td>
      <td class="${pnlCls}">${(v.avg_return>0?'+':'')+v.avg_return}%</td>
      <td class="${pnlCls}">¥${v.avg_pnl.toFixed(0)}</td>
    </tr>`;
  }).join('') || '<tr><td colspan="5" style="text-align:center;color:#bbb;">暂无数据</td></tr>';

  // 按来源分档
  const bySource = data.by_source || {};
  const srcTbody = document.getElementById('perfBySource');
  srcTbody.innerHTML = Object.entries(bySource).map(([k,v]) => {
    const label = k==='auto'?'🤖自动':'🖐手动';
    const pnlCls = (v.total_pnl||0) > 0 ? 'text-up' : 'text-down';
    return `<tr>
      <td>${label}</td><td>${v.trades}</td>
      <td>${v.win_rate}%</td>
      <td class="${pnlCls}">¥${(v.total_pnl||0).toFixed(0)}</td>
    </tr>`;
  }).join('') || '<tr><td colspan="4" style="text-align:center;color:#bbb;">暂无数据</td></tr>';

  // 月度收益
  const monthly = data.monthly_pnl || {};
  const monthTbody = document.getElementById('perfMonthly');
  monthTbody.innerHTML = Object.entries(monthly).sort().map(([k,v]) => {
    const pnlCls = v > 0 ? 'text-up' : v < 0 ? 'text-down' : '';
    return `<tr><td>${k}</td><td class="${pnlCls}" style="font-weight:600;">¥${(v>0?'+':'')+v.toFixed(0)}</td></tr>`;
  }).join('') || '<tr><td colspan="2" style="text-align:center;color:#bbb;">暂无数据</td></tr>';

  // 配置信息
  const config = data.config || {};
  document.getElementById('perfConfig').innerHTML = `
    💰 总资金: ¥${((config.total_capital||0)/10000).toFixed(0)}万 &nbsp;
    📅 持仓周期: ${config.hold_days||5}天 &nbsp;
    🎯 止盈: +${((config.stop_profit||0)*100).toFixed(0)}% &nbsp;
    🛑 止损: ${((config.stop_loss||0)*100).toFixed(0)}% &nbsp;
    📊 买入阈值: score≥${config.buy_threshold||50}
    ${data.message ? '<br>⚠️ ' + data.message : ''}
  `;
}

let _marketChart = null;  // 实例缓存，防止重复 init 导致宽度锁死
function renderMarketChart(data) {
  if (data.error || !data || !data.length) return;
  const dom = document.getElementById('marketChart');
  if (!dom) return;
  // 销毁旧实例再创建新的，避免多个 ECharts 实例叠加导致 canvas 宽度异常
  if (_marketChart) { _marketChart.dispose(); _marketChart = null; }
  const chart = echarts.init(dom);
  _marketChart = chart;
  const dates = data.map(d => d.date);
  const closes = data.map(d => d.close);
  const highs = data.map(d => d.high);
  const lows = data.map(d => d.low);
  const isUp = closes[closes.length-1] >= closes[0];
  chart.setOption({
    tooltip: { trigger:'axis', axisPointer:{type:'cross'} },
    grid: { left:'3%', right:'3%', bottom:'8%', top:'3%', containLabel:true },
    xAxis: { type:'category', data:dates, axisLabel:{rotate:45,fontSize:10} },
    yAxis: { type:'value', scale:true, splitLine:{lineStyle:{type:'dashed',color:'#eee'}} },
    dataZoom: [{ type:'inside', start:0, end:100 }],
    series: [{
      name:'收盘价', type:'line', data:closes, smooth:true,
      lineStyle: { width:2, color: isUp ? '#e74c3c' : '#27ae60' },
      areaStyle: { color: new echarts.graphic.LinearGradient(0,0,0,1, [
        { offset:0, color: isUp ? 'rgba(231,76,60,0.2)' : 'rgba(39,174,96,0.2)' },
        { offset:1, color: isUp ? 'rgba(231,76,60,0.02)' : 'rgba(39,174,96,0.02)' }
      ])},
      markLine: { data:[{ type:'average', name:'均价' }], label:{fontSize:11} }
    }, {
      name:'最高价', type:'line', data:highs, smooth:true,
      lineStyle:{width:1,color:'rgba(0,0,0,0.08)',type:'dashed'}, symbol:'none',
      emphasis:{focus:'series'}
    }, {
      name:'最低价', type:'line', data:lows, smooth:true,
      lineStyle:{width:1,color:'rgba(0,0,0,0.08)',type:'dashed'}, symbol:'none',
      emphasis:{focus:'series'}
    }]
  });
  // 延迟 resize：确保 DOM 布局稳定后再计算容器宽度，解决图表不铺满的问题
  setTimeout(() => { if (chart && !chart.isDisposed()) chart.resize(); }, 80);
}
// 全局 resize 时同步刷新大盘图
window.addEventListener('resize', () => { if (_marketChart && !_marketChart.isDisposed()) _marketChart.resize(); });

// ====== 差距分析看板 ======
function _safeNum(v, fallback) {
  return (v !== undefined && v !== null && v !== '') ? v : (fallback || '--');
}
function renderGapSummary(ga) {
  const bar = document.getElementById('gapSummaryBar');
  if (!bar) return;
  const improving = ga.improving && ga.improving.length;
  bar.innerHTML = `
    <div class="gap-summary-item">
      <div class="lbl">训练总课数</div>
      <div class="num neutral">${_safeNum(ga.total_cases, '--')}</div>
    </div>
    <div class="gap-summary-item">
      <div class="lbl">有差距自评</div>
      <div class="num neutral">${_safeNum(ga.has_note_rate, '--')}%</div>
    </div>
    <div class="gap-summary-item">
      <div class="lbl">入门期差距/课</div>
      <div class="num worsen">${_safeNum(ga.gap_rate_first, '--')}</div>
    </div>
    <div class="gap-summary-item">
      <div class="lbl">精进期差距/课</div>
      <div class="num improve">${_safeNum(ga.gap_rate_last, '--')}</div>
    </div>
    <div class="gap-summary-item">
      <div class="lbl">总体降幅</div>
      <div class="num improve">${_safeNum(ga.improvement_pct, '--')}%</div>
    </div>
    <div class="gap-summary-item">
      <div class="lbl">收录经验数</div>
      <div class="num neutral">${_safeNum(ga.total_lessons, '--')}</div>
    </div>
  `;
}

/** 无数据/模块不可用时的占位显示 */
function renderGapSummaryEmpty() {
  const bar = document.getElementById('gapSummaryBar');
  if (!bar) return;
  bar.innerHTML = `
    <div style="grid-column:1/-1;text-align:center;padding:20px;color:#94a3b8;font-size:13px;">
      📋 暂无自学习训练数据<br/>
      <span style="font-size:11px;">（需完成至少一轮自学习训练后，此处才会展示 AI 推理差距分析）</span>
    </div>
  `;
  // 清空图表区域
  ['gapDistChart','gapTrendChart','gapTrendTableWrap'].forEach(id => {
    var el = document.getElementById(id);
    if (el) el.innerHTML = '<div style="text-align:center;padding:30px;color:#cbd5e0;font-size:12px;">暂无数据</div>';
  });
}

let _gapDistChart = null;
function renderGapDistChart(ga) {
  const dom = document.getElementById('gapDistChart');
  if (!dom) return;
  if (_gapDistChart) { _gapDistChart.dispose(); _gapDistChart = null; }
  const chart = echarts.init(dom);
  _gapDistChart = chart;
  const dist = ga.gap_distribution || [];
  const types = dist.map(d => d.type);
  const rates = dist.map(d => d.rate);
  chart.setOption({
    tooltip: { trigger:'axis', axisPointer:{type:'shadow'}, formatter: function(p) {
      const d = dist[p[0].dataIndex];
      return (d.type || '') + '<br/>出现次数: ' + (d.count || 0) + '<br/>频率: ' + (d.rate || 0) + '%';
    }},
    grid: { left:'3%', right:'8%', bottom:'12%', top:'5%', containLabel:true },
    xAxis: { type:'category', data:types, axisLabel:{rotate:35,fontSize:10} },
    yAxis: { type:'value', name:'频率(%)', max:100, axisLabel:{fontSize:10} },
    series: [{
      type:'bar', data:rates,
      barWidth:'60%',
      itemStyle: {
        color: function(p) {
          const colors = ['#e74c3c','#e67e22','#f39c12','#27ae60','#3498db','#667eea','#9b59b6','#e84393','#1abc9c','#95a5a6'];
          return colors[p.dataIndex % colors.length];
        }
      },
      label: { show: true, position:'top', formatter: function(p){return p.value+'%';}, fontSize:9 }
    }]
  });
  setTimeout(() => { if (chart && !chart.isDisposed()) chart.resize(); }, 80);
}
window.addEventListener('resize', () => { if (_gapDistChart && !_gapDistChart.isDisposed()) _gapDistChart.resize(); });

let _gapTrendChart = null;
function renderGapTrendChart(ga) {
  const dom = document.getElementById('gapTrendChart');
  if (!dom) return;
  if (_gapTrendChart) { _gapTrendChart.dispose(); _gapTrendChart = null; }
  const chart = echarts.init(dom);
  _gapTrendChart = chart;
  const segs = ga.segment_data || [];
  if (!segs.length) { return; }

  // 取前6种主要差距类型
  const mainTypes = (ga.trends || []).slice(0, 6);
  const segLabels = segs.map(s => s.label.replace(/\(.*\)/,''));
  const colors = ['#e74c3c','#f39c12','#3498db','#27ae60','#9b59b6','#e67e22'];

  const series = mainTypes.map((t, i) => ({
    name: t.type,
    type: 'line',
    smooth: true,
    symbol: 'circle',
    symbolSize: 6,
    lineStyle: { width: 2, color: colors[i] },
    itemStyle: { color: colors[i] },
    data: segs.map(s => {
      const g = s.gaps.find(g => g.type === t.type);
      return g ? g.rate : 0;
    })
  }));

  chart.setOption({
    tooltip: { trigger:'axis' },
    legend: { data: mainTypes.map(t => t.type), bottom:0, textStyle:{fontSize:10}, itemWidth:14, itemHeight:10 },
    grid: { left:'3%', right:'3%', bottom:'22%', top:'5%', containLabel:true },
    xAxis: { type:'category', data: segLabels, axisLabel:{fontSize:10} },
    yAxis: { type:'value', name:'差距频率(%)', axisLabel:{fontSize:10} },
    series: series
  });
  setTimeout(() => { if (chart && !chart.isDisposed()) chart.resize(); }, 80);
}
window.addEventListener('resize', () => { if (_gapTrendChart && !_gapTrendChart.isDisposed()) _gapTrendChart.resize(); });

function renderGapTrendTable(ga) {
  const wrap = document.getElementById('gapTrendTableWrap');
  const segs = ga.segment_data || [];
  const mainTypes = (ga.trends || []).slice(0, 8);
  if (!segs.length) { wrap.innerHTML = ''; return; }

  let html = '<table class="gap-trend-table"><thead><tr><th>阶段</th>';
  for (const t of mainTypes) html += '<th>' + t.type + '</th>';
  html += '<th>经验/课</th></tr></thead><tbody>';

  for (const s of segs) {
    html += '<tr><td>' + s.label + '</td>';
    for (const t of mainTypes) {
      const g = s.gaps.find(g => g.type === t.type);
      const rate = g ? g.rate : 0;
      const cls = rate < 30 ? 'good' : rate > 60 ? 'bad' : '';
      html += '<td class="' + cls + '">' + rate + '%</td>';
    }
    html += '<td>' + s.avg_lessons + '</td></tr>';
  }

  // 趋势行
  html += '<tr style="background:#f0f2ff;font-weight:600;"><td>变化趋势</td>';
  for (const t of mainTypes) {
    const chg = t.change || 0;
    const cls = chg < 0 ? 'good' : chg > 3 ? 'bad' : '';
    html += '<td class="' + cls + '">' + (chg > 0 ? '+' : '') + chg + '%</td>';
  }
  html += '<td></td></tr></tbody></table>';

  // 底部总结
  html += '<div style="font-size:12px;color:#888;padding:4px 0;">';
  if (ga.improving && ga.improving.length) {
    html += '✅ 进步方面: ';
    html += ga.improving.map(i => i.type + '(' + i.change + '%)').join('、');
  }
  if (ga.worsening && ga.worsening.length) {
    html += '<br/>⚠️ 需加强: ';
    html += ga.worsening.map(i => i.type + '(+' + Math.abs(i.change) + '%)').join('、');
  }
  html += '</div>';

  wrap.innerHTML = html;
}

function renderGapDetails(ga) {
  const list = document.getElementById('gapDetailList');
  const samples = ga.detail_samples || [];
  if (!samples.length) { list.innerHTML = '<div style="color:#999;padding:10px;">暂无详情数据</div>'; return; }

  list.innerHTML = samples.map(s => {
    const lessonsHtml = s.lessons && s.lessons.length
      ? '<ol class="di-lessons">' + s.lessons.map(l => '<li>' + l + '</li>').join('') + '</ol>'
      : '';
    return '<div class="gap-detail-item">' +
      '<div class="di-header">' +
        '<span class="di-id">第' + s.idx + '例 [' + s.id + ']</span>' +
        '<span class="di-cats">原著:' + s.original_category + ' → AI判:' + s.ai_category + '</span>' +
      '</div>' +
      '<div class="di-note">差距自评: ' + s.note + '</div>' +
      lessonsHtml +
    '</div>';
  }).join('');
}

let gapDetailsVisible = false;
function toggleGapDetails() {
  gapDetailsVisible = !gapDetailsVisible;
  document.getElementById('gapDetailList').style.display = gapDetailsVisible ? 'block' : 'none';
  document.getElementById('gapToggleBtn').textContent = gapDetailsVisible ? '▼ 收起差距详情样例' : '▶ 展开差距详情样例';
}

// 打开日报（内嵌 modal iframe，避免弹窗被浏览器拦截）
function openReport() {
  var d = new Date();
  var ds = d.getFullYear()+'-'+String(d.getMonth()+1).padStart(2,'0')+'-'+String(d.getDate()).padStart(2,'0');
  var frame = document.getElementById('reportFrame');
  var title = document.getElementById('reportModalTitle');
  if (title) title.textContent = '📋 股票预测日报 — ' + ds;
  if (frame) frame.src = '/report/' + ds;
  var m = document.getElementById('reportModal');
  if (m) { m.classList.add('show'); document.body.style.overflow = 'hidden'; }
}

function closeReportModal() {
  var m = document.getElementById('reportModal');
  if (m) {
    m.classList.remove('show');
    var f = document.getElementById('reportFrame');
    if (f) f.src = 'about:blank';  // 停止加载，释放资源
    document.body.style.overflow = '';
  }
}
// 点击遮罩关闭日报 modal
document.getElementById('reportModal').addEventListener('click', function(e) {
  if (e.target === this) closeReportModal();
});

// ═════════ 择日分析（指定日分析已并入批量择日） ════════

function initZeri() {
  // 填充择日配置卡（类型/坐山/来龙/经度）并同步到批量隐藏 selects
  var zt = document.getElementById('zType');
  if (zt) {
    var zopts = ['立碑','安葬','婚嫁','开业','新居入宅','动土修造','阳宅动土','阴宅动土','安门','作灶','安床','出行','提车','买房过户','开工','入学开学','考试','测孩子成绩','迁坟','催龙补气','召山买土','祭祀祈福','求嗣','签约交易','上梁盖屋'];
    zt.innerHTML = zopts.map(function(v){ return '<option value="'+v+'">'+v+'</option>'; }).join('');
  }
  _fillSelect('zMountain', PL_SHAN, '请选择坐山');
  _fillSelect('zLailong', PL_SHAN, '请选择来龙（二十四山）');
  var zlon = document.getElementById('zLongitude'); if (zlon) zlon.value = '105.4';
  syncZeriShared();
}

// 择日类型 → 占事自动映射（单课联动；阴宅类映射"其他-杂占"通用断语）
var TYPE_TO_ZHANLEI = {
  '立碑':'其他','安葬':'其他','阴宅动土':'其他','迁坟':'其他','催龙补气':'其他','召山买土':'其他',
  '婚嫁':'婚姻','开业':'求财','签约交易':'求财','买房过户':'求财','开工':'求财',
  '新居入宅':'家宅','安门':'家宅','作灶':'家宅','安床':'家宅','动土修造':'家宅','上梁盖屋':'家宅','阳宅动土':'家宅','祭祀祈福':'家宅',
  '出行':'出行','提车':'出行','入学开学':'功名','考试':'功名','测孩子成绩':'功名','求嗣':'胎产'
};
// 阴宅类（需要来龙）
var ZERI_YINZHAI = ['立碑','安葬','阴宅动土','迁坟','催龙补气','召山买土'];
initZeri();
initPlSelects(); // 批量隐藏下拉（plMountain 等）页面加载即填充，避免未点子标签时无选项导致坐山校验失败

function zeriFeedbackSubmit() {
  var fb = window._zeriFeedback;
  var label = document.getElementById('fbLabel').value;
  var note = document.getElementById('fbNote').value;
  var st = document.getElementById('fbStatus');
  if (!fb || !label) { st.textContent = '⚠️ 请选择实际结果'; st.style.color = '#fbbf24'; return; }
  fetch('/api/zeri/case_feedback', { method: 'POST', headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({ date: fb.date, mountain: fb.mountain, shichen: fb.shichen,
      zetiri_type: fb.zetiri_type, zhanlei: fb.zhanlei, ben_ming: fb.ben_ming,
      lailong: fb.lailong, label: label, note: note }) })
    .then(r => r.json())
    .then(d => {
      if (d.error) { st.textContent = '❌ ' + d.error; st.style.color = '#f87171'; return; }
      st.textContent = '✅ 已记录 ' + d.id + '（累计 ' + d.total + ' 条）';
      st.style.color = '#7ee2b8';
      document.getElementById('fbNote').value = '';
    })
    .catch(function(e){ st.textContent = '❌ ' + e; st.style.color = '#f87171'; });
}

// ── 汇总卡：综合得分 + 综合评价 + 三流派对照（2026-08-15 憨爷定版，断语全部来自引擎）──
function _zeriSummary(data) {
  var dscore = (data.doushou_full && !data.doushou_full.error) ? data.doushou_full.score : null;
  var yscore = (data.yanqin_full && !data.yanqin_full.error) ? data.yanqin_full.score : null;
  var sc = data.score>=80?'#2ed573':data.score>=60?'#ffa502':'#ff6b6b';
  var dcol = dscore>=80?'#2ed573':dscore>=60?'#ffa502':'#ff6b6b';
  var ycol = yscore>=80?'#2ed573':yscore>=60?'#ffa502':'#ff6b6b';
  var html = '';
  // 杀师日警示（2026-08-17 憨爷：当用日是杀师日要提醒；妨害地师本人，红色醒目）
  if (data.shashi && data.shashi.is_shashi) {
    var ssz = data.shashi.hits.map(function(h){ return h[0] + '（' + h[1] + '）'; }).join('；');
    html += '<div style="margin-top:10px;background:rgba(239,68,68,.12);border:1px solid #ef4444;border-left:4px solid #ef4444;border-radius:8px;padding:10px 14px;">'+
      '<div style="font-size:13px;font-weight:700;color:#f87171;">⚠️ ' + data.shashi.level + '：' + ssz + '</div>'+
      '<div style="font-size:11px;color:#e0b3b3;margin-top:4px;line-height:1.6;">' + data.shashi.note + '</div></div>';
  }
  html += '<div style="display:flex;gap:20px;flex-wrap:wrap;margin-top:12px;background:#1e2a4a;border-radius:10px;padding:14px 18px;">';
  html += '<div style="text-align:center;min-width:130px;border-right:1px solid #2a3a5a;padding-right:18px;">'+
    '<div style="font-size:12px;color:#999;">综合得分</div>'+
    '<div style="font-size:38px;font-weight:700;color:'+sc+';">'+data.score+'</div>'+
    '<div style="font-size:15px;color:'+sc+';">'+data.grade+'</div></div>';
  html += '<div style="flex:1;min-width:240px;">';
  html += '<div style="font-size:12px;color:#999;margin-bottom:6px;">三流派对照（一课三判）</div>';
  html += '<div style="display:flex;gap:8px;flex-wrap:wrap;">'+
    '<span style="background:#8b5cf6;border-radius:6px;padding:4px 10px;font-size:12px;">🔮 六壬 <b style="font-size:15px;">'+data.score+'</b> '+data.grade+'</span>'+
    (dscore!=null?'<span style="background:#f59e0b;border-radius:6px;padding:4px 10px;font-size:12px;">🔥 斗首 <b style="font-size:15px;color:'+dcol+';">'+dscore+'</b></span>':'')+
    (yscore!=null?'<span style="background:#10b981;border-radius:6px;padding:4px 10px;font-size:12px;">🦅 演禽 <b style="font-size:15px;color:'+ycol+';">'+yscore+'</b></span>':'')+
    '</div>';
  html += '<div style="font-size:12px;color:#c7d2fe;margin-top:8px;">四柱: '+data.sizhu['年']+' '+data.sizhu['月']+' '+data.sizhu['日']+' '+data.sizhu['时']+' ｜ '+data.mountain+'山(坐'+data.shan_jia+'向'+data.xiang_shou+')</div>';
  // 十三吉课 + 禄马贵联动（2026-08-17 憨爷：禄马贵到山到向还须命中吉课格才圆满）
  if (data.jike_13 && data.jike_13.is_jike) {
    var jk = data.jike_13;
    if ((data.luma_pillar||0) > 0) {
      html += '<div style="font-size:12px;color:#7ee2b8;margin-top:4px;">✨ 圆满发福：禄马贵到山到向（'+data.luma_pillar+'柱）+ 吉课格「'+jk.hits.join('、')+'」</div>';
    } else {
      html += '<div style="font-size:12px;color:#e0b36a;margin-top:4px;">✨ 吉课格「'+jk.hits.join('、')+'」（但禄马贵未到山到向，力减）</div>';
    }
  } else if ((data.luma_pillar||0) > 0) {
    html += '<div style="font-size:12px;color:#e0b36a;margin-top:4px;">⚠️ 禄马贵到山到向（'+data.luma_pillar+'柱），但非十三吉课格，未圆满</div>';
  }
  // 真太阳时提示（2026-08-17：所选时辰=当地真太阳时辰，展示对应北京时间范围）
  if (data.true_solar && data.true_solar.beijing_range) {
    var ts = data.true_solar;
    html += '<div style="font-size:11px;color:#7dd3fc;margin-top:4px;">☀️ 真太阳时: '+ts.shichen+'时(当地) = 北京时间 '+ts.beijing_range+' (经度'+ts.longitude+'°, 校正'+ts.correction_minutes+'分)</div>';
  }
  // 文昌类神（测孩子成绩/学业类，2026-08-17 憨爷：日干文昌星与长生为类神）
  if (data.wenchang && data.wenchang.fired) {
    var wc = data.wenchang;
    var wcCol = (wc.score>0)?'#2ed573':(wc.score<0?'#ff6b6b':'#95a5a6');
    html += '<div style="font-size:11px;color:'+wcCol+';margin-top:4px;">📚 文昌类神: '+wc.level+' '+(wc.details||[]).join('；')+'</div>';
  }
  // 现代类型特判（提车/买房/开工/动土/入学等，2026-08-17 憨爷：古籍没有的现代类差异化判断）
  if (data.type_special && data.type_special.fired) {
    var ts = data.type_special;
    var tsCol = (ts.score>0)?'#2ed573':(ts.score<0?'#ff6b6b':'#95a5a6');
    html += '<div style="font-size:11px;color:'+tsCol+';margin-top:4px;">🎯 类型特判: '+ts.level+' '+(ts.details||[]).join('；')+'</div>';
  }
  html += '<div style="font-size:12px;color:#aaa;margin-top:4px;line-height:1.6;">综合评价: '+(data.summary||'')+'</div>';
  html += '</div></div>';
  return html;
}

// ── 课格弹窗（2026-08-15 憨爷：折叠改弹出，内容完整显示）──
function openZeriModal(pai) {
  var d = window._zeriData || (window._plDetailData && window._plDetailData.detail);
  if (!d) return;
  var title = '', body = '';
  if (pai === 'liuren') {
    title = '🔮 六壬课格（' + d.score + '分 · ' + d.grade + '）';
    body = '<div style="margin-bottom:8px;font-size:12px;color:#c7d2fe;">四柱：' + d.sizhu['年'] + ' ' + d.sizhu['月'] + ' ' + d.sizhu['日'] + ' ' + d.sizhu['时'] + '　｜　' + d.mountain + '山（坐' + d.shan_jia + '向' + d.xiang_shou + '）</div>';
    body += liurenPaipanHtml(d);   // 古法完整排盘：天盘环宫 / 四课 / 三传 / 课格 / 断语 / 毕法赋
    // ── 特殊课格 + 变格（贵登天门/罡塞鬼户/乘轩落马/交车刑等，按吉凶着色）──
    var skg = d.special_kege;
    var bjg = d.bianjie_kege;
    var skgNames = (skg && skg['匹配课格']) || [];
    var skgDetail = (skg && skg['课格详情']) || {};
    var bjNames = (bjg && bjg['匹配变格']) || [];
    var bjDetail = (bjg && bjg['变格详情']) || {};
    var merged = [];
    skgNames.forEach(function(n){ merged.push({name:n, info: skgDetail[n] || {}}); });
    bjNames.forEach(function(n){ merged.push({name:n, info: bjDetail[n] || {}}); });
    if (merged.length) {
      var skgHtml = merged.map(function(m){
        var info = m.info || {};
        var lv = info['等级'] || '';
        var desc = info['描述'] || '';
        var c = (lv === '大吉' || lv === '吉' || lv === '上吉') ? '#7ee2b8' : (lv === '大凶' || lv === '凶') ? '#ff6b6b' : (lv === '生男') ? '#7ec8ff' : (lv === '生女') ? '#ff9ecb' : '#ffa502';
        return '<span style="display:inline-block;background:rgba(255,255,255,.04);border-left:3px solid ' + c + ';border-radius:4px;padding:3px 8px;margin:2px;font-size:12px;" title="' + desc + '"><b style="color:' + c + '">' + m.name + '</b>' + (lv ? ' <span style="color:#888;font-size:11px;">[' + lv + ']</span>' : '') + '</span>';
      }).join('');
      body += '<div style="margin-top:8px;padding:8px 10px;background:rgba(255,255,255,.03);border:1px solid #3a3a6a;border-radius:8px;">' +
        '<div style="font-size:12px;font-weight:600;color:#8ea2ff;margin-bottom:4px;">🔮 特殊课格 · 变格</div>' + skgHtml + '</div>';
    }
    // ── 神将类象（三传/干上/支上 天将所乘地支的类象——应属相·应物）──
    var lx = d.leixiang;
    if (lx && lx.length) {
      var lxHtml = lx.map(function(item){
        var parts = [];
        if (item.属相) parts.push('<b style="color:#7ec8ff">属' + item.属相 + '</b>');
        if (item.天将) parts.push('<span style="color:#ffa502">' + item.天将 + '</span>');
        if (item.吉凶) parts.push('<span style="color:' + (item.吉凶 === '凶将' ? '#ff6b6b' : '#7ee2b8') + '">' + item.吉凶 + '</span>');
        if (item.所主) parts.push('<span style="color:#aaa">' + item.所主 + '</span>');
        if (item.乘神断语) parts.push('<span style="color:#e0e0e0">' + item.乘神断语 + '</span>');
        var detail = [];
        var lxi = item.类象;
        if (lxi && typeof lxi === 'object') {
          if (lxi.天神) detail.push('神：' + lxi.天神);
          if (lxi.人物) detail.push('人：' + lxi.人物);
          if (lxi.事件) detail.push('事：' + lxi.事件);
          if (lxi.身体) detail.push('身：' + lxi.身体);
          if (lxi.疾病) detail.push('病：' + lxi.疾病);
          if (lxi.地理) detail.push('地：' + lxi.地理);
          if (lxi.物品) detail.push('物：' + lxi.物品);
          if (lxi.食物) detail.push('食：' + lxi.食物);
        } else if (item.类象) {
          detail.push('类象：' + item.类象);
        }
        if (item.乘神寓意) detail.push('乘神：' + item.乘神寓意);
        if (item.姓氏) detail.push('姓：' + item.姓氏);
        return '<div style="padding:4px 0;border-bottom:1px dashed #2a2a4a;">' +
          '<span style="color:#888;font-size:11px;">' + item.位置 + ' ' + item.地支 + '</span> ' +
          parts.join(' · ') +
          (detail.length ? '<div style="font-size:11px;color:#999;margin-top:2px;">' + detail.join('；') + '</div>' : '') +
          '</div>';
      }).join('');
      body += '<div style="margin-top:8px;padding:8px 10px;background:rgba(255,255,255,.03);border:1px solid #3a3a6a;border-radius:8px;">' +
        '<div style="font-size:12px;font-weight:600;color:#8ea2ff;margin-bottom:4px;">🐘 神将类象（应属相·应物）</div>' + lxHtml + '</div>';
    }
    // ── 应期（结构化卡片：粒度徽标 + 法门 + 文本；何时应验，非吉凶方向）──
    if (d.yingqi_struct && d.yingqi_struct.length) {
      var GRAN_COL = {'日': '#22c55e', '旬': '#a78bfa', '月': '#60a5fa', '年': '#f59e0b', '速迟': '#f472b6', '方位': '#34d399'};
      body += '<div style="margin-top:8px;padding:8px 10px;background:rgba(255,255,255,.03);border:1px solid #3a3a6a;border-radius:8px;">';
      body += '<div style="font-size:12px;font-weight:600;color:#8ea2ff;margin-bottom:6px;">⏳ 应期（何时应验）</div>';
      for (var qi = 0; qi < d.yingqi_struct.length; qi++) {
        var it = d.yingqi_struct[qi] || {};
        var gc = GRAN_COL[it.粒度] || '#94a3b8';
        body += '<div style="margin:4px 0;padding:5px 8px;background:rgba(30,30,58,.6);border-radius:6px;">' +
          '<div style="display:flex;gap:8px;align-items:flex-start;flex-wrap:wrap;">' +
          '<span style="flex:none;font-size:11px;color:#fff;background:' + gc + ';border-radius:4px;padding:1px 6px;">' + (it.粒度 || '') + '</span>' +
          '<span style="flex:none;font-size:12px;color:#c4b5fd;">' + (it.法 || '') + '</span>' +
          '<span style="font-size:12px;color:#e0e0e0;line-height:1.55;white-space:pre-wrap;min-width:0;">' + (it.文本 || '') + '</span>' +
          '</div></div>';
      }
      body += '</div>';
    } else if (d.yingqi) {
      body += '<div style="margin-top:8px;padding:8px 10px;background:rgba(255,255,255,.03);border:1px solid #3a3a6a;border-radius:8px;">' +
        '<div style="font-size:12px;font-weight:600;color:#8ea2ff;margin-bottom:4px;">⏳ 应期（何时应验）</div>' +
        '<div style="font-size:12px;color:#e0e0e0;white-space:pre-wrap;line-height:1.6;">' + d.yingqi + '</div>' +
        '</div>';
    }
    body += '<div style="margin-top:8px;font-size:12px;color:#aaa;">到山到向：' + d.daoshan_daoxiang.total_count + '项　活禄马：' + d.huoma_huolu.count + '项　拱格：' + d.gong_patterns.length + '个　' +
      (d.summary ? '<div style="margin-top:4px;color:#e0e0e0;">' + d.summary + '</div>' : '') + '</div>';
    // ── 占类断语（P3：按占事给专属断语，2026-08-15）──
    var zd = d.zhanlei_duanyu;
    if (zd && zd.duanyu_lines && zd.duanyu_lines.length) {
      body += '<div style="margin-top:10px;padding:10px 12px;background:rgba(139,92,246,.12);border:1px solid #4a3a6a;border-radius:8px;">' +
        '<div style="font-size:13px;font-weight:600;color:#c4b5fd;margin-bottom:6px;">📜 ' + (d.zhanlei || '其他') + '占 · 专属断语（断案知识库，非通用）</div>' +
        '<div style="font-size:12px;color:#e0e0e0;line-height:1.7;max-height:260px;overflow-y:auto;">' +
        zd.duanyu_lines.map(function(l){ return '<div style="margin-bottom:3px;">' + l + '</div>'; }).join('') +
        '</div></div>';
    }
  } else if (pai === 'doushou') {
    var ds = d.doushou_full;
    title = '🔥 斗首课格（' + ds.score + '分 · ' + (ds.grade || '') + '）';
    var stars = '';
    for (var k in ds.sizhu_stars) {
      var sv = ds.sizhu_stars[k];
      stars += '<span style="display:inline-block;background:rgba(255,255,255,.05);border-radius:5px;padding:3px 8px;margin:2px;font-size:12px;">' + k + ' ' + sv['干支'] + ' → ' + sv['化气'] + ' · <b>' + sv['星曜'] + '</b></span>';
    }
    var pats = (ds.patterns || []);
    var structPats = pats.filter(function(p){ return p['类别'] === '四柱结构'; });
    var starPats = pats.filter(function(p){ return p['类别'] !== '四柱结构'; });
    function renderPatRow(plist, t) {
      if (!plist.length) return '';
      var items = plist.map(function(p){
        var c = p['吉凶'] === '大吉' ? '#f59e0b' : p['吉凶'] === '吉' ? '#2ed573' : '#ff6b6b';
        var desc = p['描述'] ? ' <span style="color:#888;font-size:11px;">· ' + p['描述'] + '</span>' : '';
        return '<span style="display:inline-block;background:rgba(255,255,255,.04);border-radius:5px;padding:3px 8px;margin:2px;font-size:12px;border-left:3px solid ' + c + ';"><b style="color:' + c + '">' + p['格局名称'] + '</b>' + desc + '</span>';
      }).join('');
      return '<div style="margin-bottom:4px;">' + (t ? '<span style="font-size:11px;color:#888">' + t + '</span> ' : '') + items + '</div>';
    }
    var patHtml = renderPatRow(structPats, '📐 四柱结构格局') + renderPatRow(starPats, '⭐ 五星课格');
    if (!pats.length) patHtml = '<span style="color:#666">无特殊格局</span>';
    body = '<div style="font-size:12px;color:#aaa;margin-bottom:8px;">' + d.mountain + '山 · 山家五行 <b style="color:#ffd28a;">' + ds.shan_wuxing + '</b>（炉传斗首 · 独立评分）</div>' +
      '<div style="margin-bottom:6px;">' + stars + '</div>' +
      '<div style="font-size:12px;color:#ddd;">' + patHtml + '</div>' +
      (ds.duanyu && ds.duanyu.length ? '<div style="margin-top:8px;padding:8px 10px;background:rgba(245,158,11,.1);border-radius:6px;font-size:13px;color:#ffd28a;"><b>断语：</b>' + ds.duanyu.join('；') + '</div>' : '');
  } else if (pai === 'yanqin') {
    var yq = d.yanqin_full;
    title = '🦅 演禽课格（' + yq.score + '分 · 日禽 ' + yq.riqin_algo + '）';
    var qins = '';
    var qkeys = [['年禽','年宿吉凶'],['月禽','月宿吉凶'],['日禽','日宿吉凶'],['时禽','时宿吉凶']];
    for (var qi = 0; qi < qkeys.length; qi++) {
      var qk = qkeys[qi][0], jk = qkeys[qi][1];
      var xiu = yq.si_qin[qk] || '';
      var xing = (yq.si_qin_xing || {})[qk + '星'] || '';
      var jx = (yq.xiu_jixiong || {})[jk] || '';
      var jcol = jx === '吉' ? '#2ed573' : jx === '凶' ? '#ff6b6b' : '#ffa502';
      qins += '<span style="display:inline-block;background:rgba(255,255,255,.05);border-radius:5px;padding:3px 8px;margin:2px;font-size:12px;">' + qk.replace('禽','') + ' ' + xiu + xing.replace(xiu,'') + ' <b style="color:' + jcol + '">[' + jx + ']</b></span>';
    }
    var sk = (yq.shengke || {}), skTxt = '';
    for (var s in sk) { skTxt += s + '=' + sk[s] + ' '; }
    var ypatsAll = (yq.patterns || []);
    var NAMED_CATS = ['锁泊具名格','演禽飞伏','演禽组合贵格'];
    var ypats = ypatsAll.filter(function(p){ return NAMED_CATS.indexOf(p['类别']) < 0; })
      .map(function(p){ return '<span style="color:#2ed573">' + p['格局名称'] + '</span>'; }).join(' ') || '无';
    function mgRender(list){
      return list.map(function(p){
        var c = (p['吉凶']==='吉'||p['吉凶']==='大吉')?'#2ed573':(p['吉凶']==='凶'||p['吉凶']==='大凶')?'#ff6b6b':(p['吉凶']==='中吉')?'#7ee2b8':'#ffa502';
        return '<span style="display:inline-block;background:rgba(255,255,255,.05);border-left:3px solid ' + c + ';border-radius:3px;padding:2px 6px;margin:2px;font-size:12px;"><b style="color:' + c + '">' + p['格局名称'] + '</b> <span style="color:#bbb;">' + p['描述'] + '</span></span>';
      }).join('');
    }
    var mgTxt = mgRender(ypatsAll.filter(function(p){ return p['类别'] === '锁泊具名格'; }));
    var ffTxt = mgRender(ypatsAll.filter(function(p){ return p['类别'] === '演禽飞伏'; }));
    var zhTxt = mgRender(ypatsAll.filter(function(p){ return p['类别'] === '演禽组合贵格'; }));
    var pg = yq.po_gong || {}, pgTxt = '';
    var pgKeys = ['年禽','月禽','日禽','时禽'];
    for (var pi = 0; pi < pgKeys.length; pi++) {
      var pk = pgKeys[pi], pv = pg[pk] || {};
      var pgj = pv['吉凶'] || '';
      var pgc = pgj === '吉' ? '#2ed573' : pgj === '凶' ? '#ff6b6b' : '#ffa502';
      pgTxt += pk.replace('禽','') + '<b style="color:' + pgc + '">' + pv['宫'] + '</b> ';
    }
    var qy = yq.qiyuan || {}, qyHtml = '';
    if (Object.keys(qy).length) {
      var jx2 = qy['时禽吉凶(28宿表)'] || '';
      var jc2 = jx2 === '吉' ? '#2ed573' : jx2 === '凶' ? '#ff6b6b' : '#ffa502';
      var qh = qy['七元将头'] || {};
      var td1 = qy['吞啖_日对时'] || '', td2 = qy['吞啖_时对日'] || '';
      var tdColor = function(x){ return x === '吞' ? '#2ed573' : x === '被吞' ? '#ff6b6b' : x === '互吞' ? '#ffa502' : '#aaa'; };
      var fu = qy['降伏_日对时'] || '';
      var fd = qy['番禽倒将'] || {};
      qyHtml = '<div style="margin-top:8px;font-size:12px;color:#aaa;border-top:1px dashed #3a3a5a;padding-top:6px;">' +
        '<div style="color:#7ee2b8;font-weight:600;margin-bottom:4px;">🪶 七元演禽（逐字录入）</div>' +
        '时禽·通用 <b>' + (qy['时禽_通用']||'') + '</b>（28宿 <b style="color:' + jc2 + '">' + jx2 + '</b>）｜旧法 <b>' + (qy['时禽_旧法']||'') + '</b><br>' +
        '七元将头：本将 <b>' + (qh['本将']||'') + '</b>（序号' + (qh['本将序号']!=null?qh['本将序号']:'') + '）｜干支序号 ' + (qh['干支序号']!=null?qh['干支序号']:'') + '｜元 <span style="color:#ffa502">' + (qh['元']||'') + '</span><br>' +
        '吞啖：日对时 <b style="color:' + tdColor(td1) + '">' + td1 + '</b>｜时对日 <b style="color:' + tdColor(td2) + '">' + td2 + '</b><br>' +
        '降伏·日对时：<b style="color:' + (fu==='伏'?'#2ed573':fu==='平'?'#aaa':'#ffa502') + '">' + fu + '</b><br>' +
        '番禽(我) <b style="color:#7ee2b8">' + (fd['番禽(我)']||'') + '</b>｜倒将副(彼副) <b>' + (fd['倒将副(彼副)']||'') + '</b>｜到将正(彼正) <b>' + (fd['到将正(彼正)']||'') + '</b><br>' +
        '气将(符头) <b style="color:#ffa502">' + (fd['气将(符头)']||'') + '</b> <span style="color:#888;font-size:11px;">（番禽=(时禽+(时禽-气将))%28）</span></div>';
    }
    body = '<div style="font-size:12px;color:#aaa;margin-bottom:6px;">' + qins + '</div>' +
      '<div style="font-size:12px;color:#ddd;margin-bottom:4px;">锁泊十二宫：' + pgTxt + '</div>' +
      (mgTxt ? '<div style="font-size:12px;color:#7ee2b8;font-weight:600;margin:2px 0 4px;">🔮 锁泊具名格（九泊玄格）</div><div style="margin-bottom:6px;">' + mgTxt + '</div>' : '') +
      (ffTxt ? '<div style="font-size:12px;color:#7ee2b8;font-weight:600;margin:2px 0 4px;">⚔️ 演禽飞伏（番禽/到将·战阵）</div><div style="margin-bottom:6px;">' + ffTxt + '</div>' : '') +
      (zhTxt ? '<div style="font-size:12px;color:#7ee2b8;font-weight:600;margin:2px 0 4px;">👑 演禽组合贵格</div><div style="margin-bottom:6px;">' + zhTxt + '</div>' : '') +
      '<div style="font-size:12px;color:#ddd;margin-bottom:4px;">生克：' + (skTxt || '无') + '</div>' +
      '<div style="font-size:12px;color:#ddd;">格局：' + ypats + '</div>' +
      (yq.duanyu && yq.duanyu.length ? '<div style="margin-top:8px;padding:8px 10px;background:rgba(16,185,129,.1);border-radius:6px;font-size:13px;color:#7ee2b8;"><b>断语：</b>' + yq.duanyu.join('；') + '</div>' : '') +
      qyHtml;
  }
  document.getElementById('zeriModalTitle').textContent = title;
  document.getElementById('zeriModalBody').innerHTML = body;
  document.getElementById('zeriModalWrap').style.display = 'flex';
}
function closeZeriModal() {
  document.getElementById('zeriModalWrap').style.display = 'none';
}

// ── 毕法赋断法依据渲染（judge_bifa 引擎输出：法句 + 分类 + 断法依据 + 应用 + 示例）──
function bifaJudgedHtml(d) {
  var bj = d.bifa_judged;
  if (!bj || !bj['断法'] || !bj['断法'].length) return '';
  var h = '<div style="margin:6px 0 6px 10px;padding:6px 8px;background:rgba(251,191,36,.06);border-left:2px solid #fbbf24;border-radius:4px;">';
  bj['断法'].forEach(function(x){
    var fy = x['断法依据'] || '';
    var yy = x['应用'] || '';
    var sl = x['示例'] || '';
    var fl = x['分类'] || '';
    h += '<div style="margin:3px 0;font-size:12px;line-height:1.55;">' +
      '<b style="color:#fbbf24;">' + (x['法句']||'') + '</b>' +
      (fl ? ' <span style="color:#8ea2ff;font-size:10px;">[' + fl + ']</span>' : '') +
      (fy ? '　<span style="color:#e6e9f2;">' + fy + '</span>' : '') +
      '</div>';
    if (yy) h += '<div style="font-size:11px;color:#94a3b8;margin-left:16px;">应用：' + yy + '</div>';
    if (sl) h += '<div style="font-size:11px;color:#94a3b8;margin-left:16px;">示例：' + sl + '</div>';
  });
  h += '</div>';
  return h;
}

// ── 古法完整六壬排盘（与批量择日详情同源：天盘环宫 / 四课传统排 / 三传竖排 / 课格 / 断语 / 毕法赋）──
function liurenPaipanHtml(d) {
  var sc = d.sanchuan || {};
  var sk = d.sike || [];
  var tdp2 = d.tiandi_pan || {};
  var tjm2 = d.tianjiang_map || {};
  var yj2 = d.yuejiang || '';
  var sc3 = sc['三传'] || [];
  var tj3 = sc['三传天将'] || [];
  var gz3 = sc['三传干支'] || [];
  var lq3 = sc['三传六亲'] || [];
  var kw3 = sc['三传空亡'] || [];
  var names = ['初传', '中传', '末传'];
  var keti = sc['课体'] || '';
  var kg = sc['课格列表'] || [];
  var bf = sc['毕法赋命中'] || [];
  var html = '';
  if (keti) html += '<div style="font-size:13px;margin-bottom:5px;"><b style="color:#a78bfa;">课体：</b><span style="color:#fff;font-size:15px;font-weight:600;">' + keti + '</span></div>';
  html += '<div style="display:flex;gap:10px;flex-wrap:wrap;align-items:flex-start;margin-bottom:10px;">';
  // A. 天盘环宫图（4×4 环形，四角空）
  if (tdp2 && Object.keys(tdp2).length) {
    html += '<div style="flex:1.1 1 0;min-width:190px;">' +
      '<div style="margin-bottom:3px;font-size:10px;color:#8ea2ff;font-weight:600;">天盘（月将' + (yj2||'--') + '加' + (d.shichen||'--') + '时）</div>' +
      '<div style="display:grid;grid-template-columns:repeat(4,1fr);gap:2px;">';
    var order = [['巳','午','未','申'],['辰','','','酉'],['卯','','','戌'],['寅','丑','子','亥']];
    for (var rr = 0; rr < 4; rr++) {
      for (var cc = 0; cc < 4; cc++) {
        var diZhi = order[rr][cc];
        if (!diZhi) { html += '<div></div>'; continue; }
        var tiZhi = tdp2[diZhi] || '';
        var tjName = tjm2[tiZhi] || '';
        html += '<div style="text-align:center;background:rgba(255,255,255,.03);border:1px solid #2a2f4a;border-radius:4px;padding:3px 1px;">' +
          '<div style="font-size:13px;color:#fff;font-weight:700;line-height:1.2;">' + tiZhi + '</div>' +
          '<div style="font-size:9px;color:#fbbf24;line-height:1.2;">' + tjName + '</div>' +
          '<div style="font-size:8px;color:#667;line-height:1.1;">' + diZhi + '</div></div>';
      }
    }
    html += '</div></div>';
  }
  // B. 四课传统排（右起第一课）
  if (sk.length) {
    html += '<div style="flex:1.1 1 0;min-width:190px;">' +
      '<div style="margin-bottom:3px;font-size:10px;color:#8ea2ff;font-weight:600;">四课（右起第一课）</div>' +
      '<div style="display:grid;grid-template-columns:repeat(4,1fr);gap:2px;">';
    for (var kj = 0; kj < 4; kj++) {
      var ke = sk[3 - kj] || [];
      var up = ke[1] || ''; var dn = ke[2] || ''; var tj = ke[3] || '';
      html += '<div style="text-align:center;background:rgba(255,255,255,.03);border:1px solid #2a2f4a;border-radius:4px;padding:3px 1px;">' +
        '<div style="font-size:9px;color:#fbbf24;line-height:1.3;">' + tj + '</div>' +
        '<div style="font-size:14px;color:#fff;font-weight:700;line-height:1.2;">' + up + '</div>' +
        '<div style="font-size:12px;color:#d7def0;line-height:1.2;">' + dn + '</div></div>';
    }
    html += '</div></div>';
  }
  // D. 三传传统排（竖排：传名 六亲 干支 天将）
  if (sc3.length) {
    html += '<div style="flex:0.8 1 0;min-width:130px;">' +
      '<div style="margin-bottom:3px;font-size:10px;color:#8ea2ff;font-weight:600;">三传</div>';
    for (var ci = 0; ci < 3; ci++) {
      var chuan = sc3[ci] || '';
      var lq = lq3[ci] || '';
      var gz = gz3[ci] || chuan;
      var tj2 = tj3[ci] || '';
      var kw = kw3[ci] || '';
      html += '<div style="display:flex;align-items:center;gap:8px;background:rgba(255,255,255,.03);border:1px solid #2a2f4a;border-radius:4px;padding:4px 8px;margin-bottom:3px;">' +
        '<span style="font-size:10px;color:#94a3b8;min-width:32px;">' + names[ci] + '</span>' +
        '<span style="font-size:11px;color:#7ee2b8;min-width:26px;">' + lq + '</span>' +
        '<span style="font-size:14px;color:#fff;font-weight:700;flex:1;">' + gz + '</span>' +
        '<span style="font-size:11px;color:#fbbf24;">' + tj2 + '</span>' +
        (kw ? '<span style="font-size:9px;color:#ff6b6b;">⚠空</span>' : '') +
        '</div>';
    }
    html += '</div>';
  }
  html += '</div>';
  // 课格（吉凶着色 + 断语）
  if (kg.length) {
    var kd = sc['课格详情'] || {};
    html += '<div style="margin-bottom:6px;font-size:12px;color:#9fb3d1;">课格：' + kg.map(function(k){
      var nm = (typeof k === 'string') ? k : (k['格局名称'] || k['name'] || '');
      var info = (typeof k === 'object' && k) ? k : (kd[nm] || {});
      var jx = info['吉凶'] || '';
      var dy = info['断语'] || info['定义'] || '';
      var col = (jx === '凶' || jx === '大凶') ? '#ff6b6b' : ((jx === '吉' || jx === '大吉') ? '#7ee2b8' : '#e0b36a');
      return '<b style="color:' + col + ';" title="' + (jx ? ('吉凶：' + jx + '　') : '') + dy + '">' + nm + '</b>';
    }).join(' · ') + '</div>';
  }
  // 知识库断语（KeKeDuanyu 仪度评分）
  if (d.yidu && d.yidu.score != null) {
    var yd = d.yidu;
    var ycol = yd.score >= 60 ? '#7ee2b8' : (yd.score >= 40 ? '#e0b36a' : '#ff6b6b');
    html += '<div style="margin-bottom:6px;font-size:12px;color:#9fb3d1;">📖 仪度断语：<b style="color:' + ycol + ';">' + yd.eval + '</b>（评分 <b style="color:#fbbf24;">' + yd.score + '</b>）' +
      (yd.ke_chuan_mei && yd.ke_chuan_mei.length ? '　课传美格：' + yd.ke_chuan_mei.join('、') : '') + '</div>';
    if (yd.wujue && Object.keys(yd.wujue).length) {
      var wj = Object.keys(yd.wujue).map(function(k){ return k + ' <b style="color:#fbbf24;">+' + yd.wujue[k] + '</b>'; }).join('　');
      html += '<div style="margin-bottom:6px;font-size:11px;color:#9fb3d1;">　五大要诀：' + wj + '</div>';
    }
  }
  // 毕法赋
  if (bf.length || (d.bifa_judged && d.bifa_judged['匹配法句'] && d.bifa_judged['匹配法句'].length)) {
    html += '<div style="font-size:12px;color:#9fb3d1;">毕法赋：' + bf.map(function(b){ return '<b style="color:#fbbf24;">' + b + '</b>'; }).join(' · ') + '</div>';
    html += bifaJudgedHtml(d);
  }
  return html;
}

// ═════════ 个股搜索与行情 ════════
let stockSearchTimer = null;
let stockSearchKeyword = '';
function searchStock() {
  const kw = document.getElementById('stockSearchInput').value.trim();
  const dd = document.getElementById('stockDropdown');
  if (!kw) { dd.classList.remove('show'); dd.innerHTML = ''; return; }
  // 防抖
  clearTimeout(stockSearchTimer);
  stockSearchTimer = setTimeout(() => {
    if (kw === stockSearchKeyword) return;  // 避免重复请求
    stockSearchKeyword = kw;
    fetch(API+'/api/stock/search?keyword='+encodeURIComponent(kw))
      .then(r => r.json())
      .then(data => {
        if (!data.success || !data.results || !data.results.length) {
          dd.innerHTML = '<div class="dd-empty">未找到匹配的股票</div>';
          dd.classList.add('show');
          return;
        }
        dd.innerHTML = data.results.slice(0, 20).map(r =>
          '<div class="dd-item" onclick="showStockQuote(\''+r.code+'\')">'+
            '<span>'+r.name+'</span><span class="dd-code">'+r.code+'</span>'+
          '</div>'
        ).join('');
        dd.classList.add('show');
      })
      .catch(err => {
        dd.innerHTML = '<div class="dd-empty">搜索失败：'+err.message+'</div>';
        dd.classList.add('show');
      });
  }, 250);
}

// 点击其他区域关闭下拉
document.addEventListener('click', function(e) {
  if (!e.target.closest('.stock-search-box')) {
    const dd = document.getElementById('stockDropdown');
    if (dd) dd.classList.remove('show');
  }
});

function showStockQuote(code) {
  document.getElementById('stockDropdown').classList.remove('show');
  const card = document.getElementById('quoteCard');
  card.classList.add('show');
  // 重置
  ['qcName','qcCode','qcPrice','qcChange','qcOpen','qcPrev','qcHigh','qcLow','qcChangeAmt','qcVolume','qcAmount','qcTurnover','qcMktcap']
    .forEach(id => document.getElementById(id).textContent = '--');
  document.getElementById('qcChange').className = 'qc-change';

  fetch(API+'/api/stock/quote?code='+encodeURIComponent(code))
    .then(r => r.json())
    .then(data => {
      if (!data.success || !data.quote) {
        alert('获取行情失败');
        return;
      }
      const q = data.quote;
      document.getElementById('qcName').textContent = q.name || '--';
      document.getElementById('qcCode').textContent = q.code || code;
      const priceEl = document.getElementById('qcPrice');
      priceEl.textContent = (q.price != null) ? q.price.toFixed(2) : '--';
      priceEl.style.color = (q.change >= 0) ? '#e74c3c' : '#27ae60';
      const chgEl = document.getElementById('qcChange');
      const chgPct = q.change || 0;
      chgEl.textContent = (chgPct >= 0 ? '+' : '') + chgPct.toFixed(2) + '%  ' + (q.change_amount >= 0 ? '+' : '') + (q.change_amount || 0).toFixed(2);
      chgEl.className = 'qc-change ' + (chgPct >= 0 ? 'up' : 'down');
      document.getElementById('qcOpen').textContent = (q.open != null) ? q.open.toFixed(2) : '--';
      document.getElementById('qcPrev').textContent = (q.prev_close != null) ? q.prev_close.toFixed(2) : '--';
      document.getElementById('qcHigh').textContent = (q.high != null) ? q.high.toFixed(2) : '--';
      document.getElementById('qcLow').textContent = (q.low != null) ? q.low.toFixed(2) : '--';
      document.getElementById('qcChangeAmt').textContent = (q.change_amount != null) ? (q.change_amount >= 0 ? '+' : '') + q.change_amount.toFixed(2) : '--';
      document.getElementById('qcVolume').textContent = formatBigNumber(q.volume);
      document.getElementById('qcAmount').textContent = formatBigNumber(q.amount);
      document.getElementById('qcTurnover').textContent = (q.turnover_rate != null) ? q.turnover_rate.toFixed(2) + '%' : '--';
      document.getElementById('qcMktcap').textContent = formatMarketCap(q.market_cap);
      // 渲染个股图（先用实时行情渲染单日摘要，再异步拉K线历史）
      renderStockChart(q);
      // 异步拉取日K线历史，拿到后渲染蜡烛图
      fetchTimeout(API+'/api/stock/kline?code='+encodeURIComponent(code)+'&days=60', 5000)
        .then(r => r.json())
        .then(data => {
          if (data.success && data.kline && data.kline.length > 0) {
            renderStockKline(q.name || code, data.kline);
          }
        })
        .catch(err => console.error('kline fetch err:', err));
    })
    .catch(err => alert('获取行情失败：'+err.message));
}

function formatBigNumber(n) {
  if (n == null) return '--';
  n = parseFloat(n);
  if (isNaN(n)) return '--';
  if (n >= 1e8) return (n/1e8).toFixed(2) + '亿';
  if (n >= 1e4) return (n/1e4).toFixed(2) + '万';
  return n.toFixed(0);
}
function formatMarketCap(n) {
  if (n == null) return '--';
  n = parseFloat(n);
  if (isNaN(n)) return '--';
  if (n >= 1e8) return (n/1e8).toFixed(2) + '亿';
  return n.toFixed(0);
}

let _stockChart = null;
let _stockChartDeferred = false;

function renderStockChart(quote) {
  const dom = document.getElementById('stockChart');
  if (!dom) return;
  // 宽度守卫：容器太窄时延迟重试（display:none→block后浏览器尚未完成布局）
  const w = dom.clientWidth || dom.offsetWidth;
  if (w < 50) {
    if (!_stockChartDeferred) {
      _stockChartDeferred = true;
      setTimeout(() => {
        _stockChartDeferred = false;
        renderStockChart(quote);
      }, 150);
    }
    return;
  }
  // 复用echarts实例
  if (_stockChart) {
    _stockChart.resize();
  } else {
    _stockChart = echarts.init(dom);
    window.addEventListener('resize', () => { if (_stockChart) _stockChart.resize(); });
    // 监听容器尺寸变化（如侧边栏折叠等）
    if (window.ResizeObserver) {
      const ro = new ResizeObserver(() => { if (_stockChart) _stockChart.resize(); });
      ro.observe(dom);
    }
  }
  const chart = _stockChart;
  if (!quote || quote.price == null || isNaN(quote.price)) {
    chart.clear();
    chart.setOption({ title: { text: '暂无行情数据', left:'center', top:'center', textStyle:{color:'#999',fontSize:14} } });
    return;
  }

  const open = quote.open || 0, close = quote.price || 0;
  const high = quote.high || 0, low = quote.low || 0, prev = quote.prev_close || 0;
  const changePct = prev > 0 ? (close - prev) / prev * 100 : 0;
  const isUp = close >= prev;
  const color = isUp ? '#e74c3c' : '#27ae60';
  const colorLight = isUp ? 'rgba(231,76,60,0.15)' : 'rgba(39,174,96,0.15)';
  const stockName = quote.name || quote.code || '';

  chart.clear();

  // 单日行情专用可视化：
  // 使用区间柱（low-high）+ 开盘收盘标记 + 昨收参考线
  // 比单根K线更清晰地展示当日价格区间
  chart.setOption({
    tooltip: {
      trigger: 'axis',
      formatter: function(params) {
        const p = params[0];
        return `<b>${stockName}</b><br/>
          今开: ${open.toFixed(2)}<br/>
          最高: ${high.toFixed(2)}<br/>
          最低: ${low.toFixed(2)}<br/>
          最新: ${close.toFixed(2)}<br/>
          涨跌: ${changePct>=0?'+':''}${changePct.toFixed(2)}%`;
      }
    },
    grid: { left:'10%', right:'10%', bottom:'18%', top:'8%', containLabel:true },
    xAxis: {
      type: 'category',
      data: [stockName],
      axisLabel: { fontSize: 14, fontWeight: 600, color: '#333' },
      axisLine: { lineStyle: { color: '#ddd' } },
      axisTick: { show: false }
    },
    yAxis: {
      type: 'value',
      scale: true,
      axisLabel: { fontSize: 12, color: '#888' },
      splitLine: { lineStyle: { type: 'dashed', color: '#f0f0f0' } }
    },
    series: [
      // 昨日收盘参考线
      {
        name: '昨收',
        type: 'line',
        data: [prev],
        symbol: 'none',
        lineStyle: { color: '#95a5a6', type: 'dashed', width: 2 },
        markLine: {
          symbol: 'none',
          silent: true,
          data: [{ yAxis: prev }],
          lineStyle: { color: '#95a5a6', type: 'dashed', width: 2 },
          label: {
            formatter: '昨收 ' + prev.toFixed(2),
            position: 'end',
            fontSize: 11,
            color: '#95a5a6'
          }
        }
      },
      // 当日价格区间柱（low到high的柱状背景）
      {
        name: '当日区间',
        type: 'bar',
        data: [[low, high]],
        barWidth: 40,
        itemStyle: {
          color: colorLight,
          borderColor: color,
          borderWidth: 2,
          borderRadius: [4, 4, 4, 4]
        },
        // 在柱子上标记开盘价和收盘价
        markPoint: {
          symbol: 'pin',
          symbolSize: 45,
          data: [
            { name: '今开', value: open.toFixed(2), xAxis: 0, yAxis: open,
              itemStyle: { color: '#f39c12' },
              label: { formatter: '开', fontSize: 10, color: '#fff' } },
            { name: '最新', value: close.toFixed(2), xAxis: 0, yAxis: close,
              itemStyle: { color: color },
              label: { formatter: changePct>=0?'+':'' + changePct.toFixed(2) + '%', fontSize: 11, color: '#fff', fontWeight: 'bold' } }
          ]
        },
        // 在柱子上画一条线连接开收盘
        markLine: {
          symbol: 'none',
          silent: true,
          data: [{
            yAxis: [open, close],
            lineStyle: { color: color, width: 3, type: 'solid' }
          }]
        }
      }
    ],
    // 底部信息栏：关键价位文字
    graphic: [{
      type: 'group',
      bottom: 5,
      left: 'center',
      children: [{
        type: 'text',
        style: {
          text: `今开 ${open.toFixed(2)}   最高 ${high.toFixed(2)}   最低 ${low.toFixed(2)}   昨收 ${prev.toFixed(2)}`,
          fontSize: 12,
          fill: '#666',
          textAlign: 'center'
        }
      }]
    }]
  });
}

// ── 个股日K蜡烛图（历史走势）──
let _stockKlineChart = null;
function renderStockKline(name, kline) {
  const dom = document.getElementById('stockChart');
  if (!dom || !kline || !kline.length) return;
  // 销毁旧实例（可能是之前 renderStockChart 创建的单日柱状图）
  if (_stockKlineChart) { _stockKlineChart.dispose(); _stockKlineChart = null; }
  if (_stockChart) { _stockChart.dispose(); _stockChart = null; }
  const chart = echarts.init(dom);
  _stockKlineChart = chart;

  const dates = kline.map(d => d.date);
  const opens = kline.map(d => d.open);
  const highs = kline.map(d => d.high);
  const lows = kline.map(d => d.low);
  const closes = kline.map(d => d.close);
  const volumes = kline.map(d => d.volume);
  const amounts = kline.map(d => d.amount);

  // 计算均线
  function calcMA(dayCount, data) {
    var result = [];
    for (var i = 0; i < data.length; i++) {
      if (i < dayCount - 1) { result.push('-'); continue; }
      var sum = 0;
      for (var j = 0; j < dayCount; j++) { sum += data[i - j]; }
      result.push(+(sum / dayCount).toFixed(2));
    }
    return result;
  }
  const ma5 = calcMA(5, closes);
  const ma10 = calcMA(10, closes);
  const ma20 = calcMA(20, closes);

  // 涨跌色
  const upColor = '#e74c3c';
  const downColor = '#27ae60';

  // K线数据格式: [open, close, low, high]
  const candleData = kline.map((d, i) => [d.open, d.close, d.low, d.high]);

  // 成交量颜色（与涨跌一致）
  const volColors = closes.map((c, i) => (i > 0 && c >= closes[i-1]) ? upColor : downColor);

  chart.setOption({
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'cross' },
      formatter: function(params) {
        var idx = params[0].dataIndex;
        var d = kline[idx];
        if (!d) return '';
        var chg = idx > 0 ? ((d.close - closes[idx-1]) / closes[idx-1] * 100) : 0;
        return `<b>${name}</b> ${d.date}<br/>`
          + `开盘: ${d.open.toFixed(2)}<br/>`
          + `最高: ${d.high.toFixed(2)}<br/>`
          + `最低: ${d.low.toFixed(2)}<br/>`
          + `收盘: ${d.close.toFixed(2)}<br/>`
          + `涨跌: ${chg>=0?'+':''}${chg.toFixed(2)}%<br/>`
          + `成交量: ${formatBigNumber(d.volume)}<br/>`
          + `成交额: ${formatBigNumber(d.amount)}`;
      }
    },
    legend: {
      data: ['日K', 'MA5', 'MA10', 'MA20', '成交量'],
      top: 0,
      textStyle: { fontSize: 11 },
      itemWidth: 14,
      itemHeight: 8
    },
    grid: [
      { left: '8%', right: '8%', top: '12%', height: '55%' },   // K线区
      { left: '8%', right: '8%', top: '72%', height: '15%' }     // 成交量区
    ],
    xAxis: [
      { type: 'category', data: dates, gridIndex: 0,
        axisLabel: { show: false }, axisTick: { show: false }, axisLine: { lineStyle: { color: '#ddd' } } },
      { type: 'category', data: dates, gridIndex: 1,
        axisLabel: { rotate: 45, fontSize: 9, color: '#888' },
        axisTick: { show: false }, axisLine: { lineStyle: { color: '#ddd' } } }
    ],
    yAxis: [
      { scale: true, gridIndex: 0, splitLine: { lineStyle: { color: '#f0f0f0', type: 'dashed' } },
        axisLabel: { fontSize: 10 } },
      { scale: true, gridIndex: 1, splitLine: { show: false },
        axisLabel: { fontSize: 9, color: '#888' } }
    ],
    dataZoom: [
      { type: 'inside', xAxisIndex: [0, 1], start: Math.max(0, 100 - kline.length * 1.5), end: 100 },
      { type: 'slider', xAxisIndex: [0, 1], top: '87%', height: 18,
        borderColor: '#eee', fillerColor: 'rgba(52,152,219,0.1)',
        handleStyle: { color: '#3498db' }, textStyle: { fontSize: 9 } }
    ],
    series: [
      {
        name: '日K', type: 'candlestick', xAxisIndex: 0, yAxisIndex: 0,
        data: candleData,
        itemStyle: {
          color: upColor,       // 阳线实体（涨）
          color0: downColor,    // 阴线实体（跌）
          borderColor: upColor,  // 阳线边框
          borderColor0: downColor
        },
        markPoint: {
          // 标记最新一天
          data: [{
            coord: [dates.length - 1, closes[closes.length - 1]],
            value: '最新',
            symbol: 'pin',
            symbolSize: 30,
            itemStyle: { color: closes[closes.length-1] >= (closes[closes.length-2]||closes[closes.length-1]) ? upColor : downColor },
            label: { fontSize: 8, color: '#fff' }
          }]
        }
      },
      {
        name: 'MA5', type: 'line', xAxisIndex: 0, yAxisIndex: 0,
        data: ma5, smooth: true, symbol: 'none',
        lineStyle: { width: 1, color: '#f39c12' }, lineStyle: { opacity: 0.7 }
      },
      {
        name: 'MA10', type: 'line', xAxisIndex: 0, yAxisIndex: 0,
        data: ma10, smooth: true, symbol: 'none',
        lineStyle: { width: 1, color: '#3498db' }, lineStyle: { opacity: 0.7 }
      },
      {
        name: 'MA20', type: 'line', xAxisIndex: 0, yAxisIndex: 0,
        data: ma20, smooth: true, symbol: 'none',
        lineStyle: { width: 1, color: '#9b59b6' }, lineStyle: { opacity: 0.7 }
      },
      {
        name: '成交量', type: 'bar', xAxisIndex: 1, yAxisIndex: 1,
        data: volumes.map((v, i) => ({
          value: v,
          itemStyle: { color: volColors[i], opacity: 0.8 }
        })),
        barWidth: '60%'
      }
    ]
  });

  // 延迟 resize 确保铺满容器
  setTimeout(() => { if (chart && !chart.isDisposed()) chart.resize(); }, 80);
}
// 全局 resize 同步刷新个股K线图
window.addEventListener('resize', () => { if (_stockKlineChart && !_stockKlineChart.isDisposed()) _stockKlineChart.resize(); });

// ═════════ 个股详情面板 ════════
// 展开个股详情面板（点击选股结果行/大六壬推荐行调用）
function showStockDetail(code, name) {
  const panel = document.getElementById('stockDetailPanel');
  panel.style.display = 'block';
  const titleEl = document.getElementById('stockDetailTitle');
  titleEl.textContent = (name ? name + ' ' : '') + '(' + code + ')';
  // 同步填充搜索框
  document.getElementById('stockSearchInput').value = code;
  // 检查该股是否在大六壬推荐列表中（一课多断优先；缺省回退双阶段精选的六壬裁决）
  const liurenPred = _multiStockPredictions.find(p => p.symbol === code);
  const dpPred = _dualPhaseVerified.find(function(r){ return (r.code || r.symbol) === code; });
  const analysisBox = document.getElementById('stockLiurenAnalysis');
  const analysisText = document.getElementById('stockLiurenText');
  if (liurenPred) {
    analysisBox.style.display = 'block';
    analysisText.innerHTML = '<div><strong>趋势预测：</strong><span style="color:' + ((liurenPred.trend||'').indexOf('涨')>=0 ? '#e74c3c' : (liurenPred.trend||'').indexOf('跌')>=0 ? '#27ae60' : '#888') + '">' + (liurenPred.trend||'--') + '</span>　<strong>吉凶：</strong>' + (liurenPred.jixiong||'--') + '　<strong>置信度：</strong>' + (liurenPred.confidence*100).toFixed(0) + '%</div>' +
      '<div style="margin-top:8px;">' + (liurenPred.analysis||'') + '</div>';
  } else if (dpPred && (dpPred.liuren_trend || dpPred.liuren_jixiong)) {
    const dTrend = dpPred.liuren_trend || '--';
    const dConf = dpPred.liuren_confidence != null ? (dpPred.liuren_confidence*100).toFixed(0)+'%' : '--';
    analysisBox.style.display = 'block';
    analysisText.innerHTML = '<div><strong>六壬裁决（双阶段精选）：</strong><span style="color:' + (dTrend.indexOf('涨')>=0 ? '#e74c3c' : dTrend.indexOf('跌')>=0 ? '#27ae60' : '#888') + '">' + dTrend + '</span>　<strong>吉凶：</strong>' + (dpPred.liuren_jixiong||'--') + '　<strong>置信度：</strong>' + dConf + '</div>' +
      '<div style="margin-top:8px;color:#666;font-size:12px;">该股通过量化海选 + 六壬精选双重验证（' + (dpPred.screener_score!=null ? '量化评分 ' + dpPred.screener_score + '，' : '') + (dpPred.position_level ? '建议仓位 ' + dpPred.position_level + (dpPred.position_pct!=null ? ' (' + dpPred.position_pct + '%)' : '') : '') + '）。</div>';
  } else {
    analysisBox.style.display = 'none';
  }
  // 加载行情（需等面板布局完成后再渲染图表，否则echarts读到的容器宽度为0）
  requestAnimationFrame(() => {
    requestAnimationFrame(() => {
      showStockQuote(code);
      // 保险：延迟50ms再强制resize一次，确保图表在面板布局完成后正确填充
      setTimeout(() => { if (_stockChart) _stockChart.resize(); }, 50);
    });
  });
  // 平滑滚动到详情面板
  setTimeout(() => panel.scrollIntoView({behavior:'smooth', block:'start'}), 100);
}

// ═════════ 六壬股市类象知识面板（静态） ════════
function toggleKgGroup(gid){ var el=document.getElementById(gid); el.classList.toggle('expanded'); }

function initStockKnowledge() {
  window._stockKgInited = true;
  const dizhi = [
    ['子','资金、散户、水下、低位、银行'],
    ['丑','券商、基金、机构、银根'],
    ['寅','开市、开盘、上涨、龙头'],
    ['卯','突破、放量、门户、通道'],
    ['辰','震荡、盘整、横盘、平台'],
    ['巳','拉升、急涨、火速行情、投机'],
    ['午','天量、大阳线、涨停、高潮'],
    ['未','阴跌、回落、回调、套牢'],
    ['申','下跌、破位、空头、出货'],
    ['酉','收盘、缩量、整理、金叉'],
    ['戌','跌停、崩盘、套牢盘、ST股'],
    ['亥','潜伏、底仓、暗流、对倒']
  ];
  const shenjiang = [
    ['贵人(丑)','国家队、白马股、绩优股'],
    ['螣蛇(巳)','妖股、庄股、异常波动'],
    ['朱雀(午)','消息面、利好利空、公告'],
    ['六合(卯)','横盘、整理、多空平衡'],
    ['勾陈(辰)','套牢、死叉、阻力位'],
    ['青龙(寅)','上升趋势、牛市、主力'],
    ['天空(戌)','虚假突破、主力骗线'],
    ['白虎(申)','暴跌、恐慌盘、踩踏'],
    ['太常(未)','慢牛、消费股、分红'],
    ['玄武(亥)','内幕交易、潜伏盘、老鼠仓'],
    ['太阴(酉)','阴跌、杀估值、缩量'],
    ['天后(子)','流动性宽松、放水、利好']
  ];
  const keti = [
    ['龙德课','大盘蓝筹走强，宜价值投资'],
    ['富贵课','利好驱动上涨，宜顺势而为'],
    ['三光课','多方发力上行，短期看涨'],
    ['三阳课','多方主导，趋势向好'],
    ['三奇课','突发利好，走势异常'],
    ['六仪课','基本面优良，稳健上行'],
    ['轩盖课','权重股搭台，题材股唱戏'],
    ['铸印发课','底部放量启动，中线看好'],
    ['龙战课','多空激战，剧烈波动'],
    ['九丑课','利空突袭，恐慌下跌'],
    ['天网课','套牢盘沉重，难以突破'],
    ['死奇课','走势破位，止损离场']
  ];
  const renderCards = arr => arr.map(([k,v]) => `<div class="k-card"><div class="kc-key">${k}</div><div class="kc-desc">${v}</div></div>`).join('');
  document.getElementById('kgDizhi').innerHTML = renderCards(dizhi);
  document.getElementById('kgShenjiang').innerHTML = renderCards(shenjiang);
  document.getElementById('kgKeti').innerHTML = renderCards(keti);
}

// 自动刷新
let autoTimer;
function startAutoRefresh() {
  syncAccountTabBadge();
  loadAll();
  autoTimer = setInterval(loadAll, 15000);
}
startAutoRefresh();

// 折叠面板（点击 h2 标题可切换展开/折叠，默认全部展开）
(function(){
  var secs = document.querySelectorAll('.section, .gap-section');
  secs.forEach(function(sec, i){
    var h2 = sec.querySelector('h2');
    if(!h2) return;
    // 带显式 .section-toggle（sec-collapsible 机制）的区块由 toggleSection 独立管理，
    // 不挂 h2 折叠，避免两个折叠机制互相打架（2026-08 审查修复）
    if(sec.querySelector('.section-toggle')) return;
    h2.insertAdjacentHTML('afterbegin', '<span class="toggle-arrow">▼</span>');
    var body = document.createElement('div');
    body.className = 'section-body';
    while(h2.nextSibling) body.appendChild(h2.nextSibling);
    sec.appendChild(body);
    h2.onclick = function(){ sec.classList.toggle('collapsed'); };
  });
})();

// ====== 决策仪表盘 ======
function loadCompareData() {
  fetch(API+'/api/liuren_history').then(r=>r.json()).then(hd=>{
    var date = '';
    if(hd.history && hd.history.length > 0) {
      date = hd.history[0].cycle_start || '';
    }
    fetch(API+'/api/decision_matrix?date='+date).then(r=>r.json()).then(d=>{
      if(!d.success) return;
      renderDecisionMatrix(d.data);
    }).catch(err=>console.error(err));
  }).catch(()=>{
    fetch(API+'/api/decision_matrix').then(r=>r.json()).then(d=>{
      if(!d.success) return;
      renderDecisionMatrix(d.data);
    }).catch(err=>console.error(err));
  });
}

function renderDecisionMatrix(data) {
  if(!data) return;
  document.getElementById('dmCycle').textContent = data.cycle_start || '--';
  document.getElementById('dmLiuren').textContent = data.liuren_macro.trend + ' (' + data.liuren_macro.confidence + '%)';
  document.getElementById('dmLiuren').style.color = data.liuren_macro.trend.indexOf('涨')>=0 ? '#e74c3c' : '#27ae60';
  document.getElementById('dmQuantConf').textContent = data.quant_overview.confidence + '%';
  var stats = data.stats || {};
  document.getElementById('dmAdvice').innerHTML = '🟢L1:'+(stats.high||0)+' 🟡L2:'+(stats.mid||0)+' 🔴需六壬:'+(stats.need_liuren||0);
  
  var rows = data.decisions || [];
  var h = '<div style="overflow-x:auto;"><table style="width:100%;border-collapse:collapse;">';
  h += '<thead><tr style="background:#f5f5f5;"><th>股票/指数</th><th>级</th><th>量化趋势</th><th>量化置信</th><th>六壬方向</th><th>主信号</th><th>建议</th><th>操作</th></tr></thead><tbody>';
  rows.forEach(function(r){
    var lvlColor = r.conf_color || {1:'#27ae60',2:'#f39c12',3:'#e74c3c'}[r.level]||'#999';
    var rowBg = r.row_color || '';
    h += '<tr style="background:'+rowBg+';">';
    h += '<td style="padding:6px;font-weight:600;">'+r.stock+'</td>';
    h += '<td style="color:'+lvlColor+';font-weight:700;">L'+r.level+'</td>';
    h += '<td>'+normDir(r.quant_trend)+'</td>';
    h += '<td style="color:'+lvlColor+';font-weight:700;">'+r.quant_conf+'%</td>';
    h += '<td>'+normDir(r.liuren_trend)+'</td><td>'+normDir(r.main_signal)+'</td>';
    h += '<td style="font-weight:700;font-size:13px;">'+r.advice+'</td>';
    h += '<td>';
    if(r.need_liuren) {
      h += '<button onclick="runLiurenForStock(\''+r.stock+'\')" style="background:#8b5cf6;color:#fff;border:none;padding:4px 10px;border-radius:4px;cursor:pointer;font-size:12px;">🔮 六壬预测</button>';
    } else {
      h += '<span style="color:#999;font-size:12px;">量化足矣</span>';
    }
    h += '</td></tr>';
  });
  h += '</tbody></table></div>';
  document.getElementById('decisionTable').innerHTML = h;
}

/** 决策矩阵「🔮 六壬预测」：对指定个股给出真实六壬裁决。
 *  在现有预测池中定位该股（一课多断 > 双阶段精选 > 观察池 > 量化池），
 *  打开个股详情并展示其六壬判断；本地未命中时回退搜索接口按名称/代码解析。 */
function runLiurenForStock(stockName) {
  if (!stockName) return;
  var hit = null;
  var pools = [_multiStockPredictions, _dualPhaseVerified, _dualPhaseWatching, _screenerResults];
  for (var pi = 0; pi < pools.length && !hit; pi++) {
    var pool = pools[pi] || [];
    for (var i = 0; i < pool.length; i++) {
      var it = pool[i];
      var nm = it.name || it.stock || '';
      var cd = it.symbol || it.code || '';
      if (nm === stockName || cd === stockName ||
          (nm && stockName && nm.indexOf(stockName) >= 0) ||
          (nm && stockName && stockName.indexOf(nm) >= 0)) { hit = it; break; }
    }
  }
  var code = hit ? (hit.symbol || hit.code || '') : '';
  var name = hit ? (hit.name || stockName) : stockName;
  if (!code) {
    // 本地预测池未命中 → 用搜索接口解析名称/代码
    fetch(API + '/api/stock/search?keyword=' + encodeURIComponent(stockName))
      .then(function(r){ return r.json(); })
      .then(function(d){
        if (d.success && d.results && d.results.length) {
          switchTab('screener');
          setTimeout(function(){ showStockDetail(d.results[0].code, d.results[0].name || stockName); }, 120);
        } else {
          alert('未找到股票 [' + stockName + ']，无法展开六壬分析');
        }
      })
      .catch(function(){ alert('查找股票失败，请稍后重试'); });
    return;
  }
  switchTab('screener');
  setTimeout(function(){ showStockDetail(code, name); }, 120);
}

function runDecisionMatrix(e) {
  var btn = e.target;
  btn.disabled = true; btn.textContent = '⏳ 分析中...';
  fetch(API+'/api/liuren_history').then(r=>r.json()).then(hd=>{
    var date = hd.history && hd.history.length>0 ? hd.history[0].cycle_start : '';
    return fetch(API+'/api/decision_matrix?date='+date);
  }).then(r=>r.json()).then(d=>{
    btn.disabled = false; btn.textContent = '🔄 运行决策矩阵';
    if(!d.success){ alert('分析失败: '+d.error); return; }
    renderDecisionMatrix(d.data);
  }).catch(err=>{btn.disabled=false;btn.textContent='🔄 运行决策矩阵'; alert('请求失败');});
}





;

function loadTrainingStatus(){
  if (document.hidden) return;  // 后台标签页跳过轮询
  fetch('/api/training_status').then(r=>r.json()).then(d=>{
    if(d.error) return;
    document.getElementById('stTotal').textContent = d.total_predictions;
    document.getElementById('stLR').textContent = d.liuren_accuracy+'%';
    document.getElementById('stModel').textContent = d.observation_start || '--';
    // 折叠条同步（ML/训练样本已移除：ML 路径证伪停用 2026-08-15）
    document.getElementById('stLR2').textContent = d.liuren_accuracy+'%';
    document.getElementById('stModel2').textContent = d.observation_start || '--';

    // 六壬观察模式状态
    var modeBadge = document.getElementById('liurenModeBadge');
    var obsText = document.getElementById('liurenObserveText');
    var obsPct = document.getElementById('liurenObservePct');
    var aiSum = document.getElementById('aiSummaryText');
    if(d.liuren_reference_only){
      if(modeBadge){ modeBadge.textContent='🔮 六壬验证'; }
      // 计算经验积累进度
      var start = new Date(d.observation_start);
      var years = d.validation_years || 3;
      var totalMs = years * 365 * 24 * 3600 * 1000;
      var elapsed = Date.now() - start.getTime();
      var pct = Math.max(0, Math.min(100, Math.round(elapsed / totalMs * 100)));
      var days = Math.max(0, Math.floor(elapsed / (24*3600*1000)));
      var remainDays = Math.max(0, Math.round((totalMs - elapsed) / (24*3600*1000)));
      if(obsText) obsText.textContent = '观察起始 '+d.observation_start+' · 已积累 '+days+' 天 · 还需约 '+remainDays+' 天（'+years+'年验证期）达标后可参与决策';
      if(obsPct) obsPct.textContent = pct+'%';
      if(aiSum) aiSum.textContent = '六壬观察验证：已积累 '+days+' 天 / '+years+'年（'+pct+'%）· 还差 '+remainDays+' 天';
    } else {
      if(modeBadge){ modeBadge.textContent='🔮 六壬参与'; }
      if(obsText) obsText.textContent = '六壬已参与决策（验证通过）';
      if(obsPct) obsPct.textContent = '✓';
      if(aiSum) aiSum.textContent = '六壬已参与决策（验证通过）';
    }
    // 同步知识库案例数
    if(d.knowledge_total_cases !== undefined){
      var badge = document.getElementById('knowledgeCasesBadge');
      if(badge) badge.textContent = '共 '+d.knowledge_total_cases+' 条';
    }
  }).catch(function(){});
}

// ====== 知识库案例列表 ======
function loadKnowledgeCases() {
  var container = document.getElementById('kCCasesList');
  if(!container) return;
  container.innerHTML = '<div style="text-align:center;padding:30px;color:#999;">加载中...</div>';
  
  var source = document.getElementById('kcSourceFilter') ? document.getElementById('kcSourceFilter').value : '';
  var zhanshi = document.getElementById('kcZhanshiFilter') ? document.getElementById('kcZhanshiFilter').value : '';
  var grade = document.getElementById('kcGradeFilter') ? document.getElementById('kcGradeFilter').value : '';
  var url = '/api/knowledge/cases?limit=50';
  if(source) url += '&source=' + encodeURIComponent(source);
  if(zhanshi) url += '&zhanshi=' + encodeURIComponent(zhanshi);
  
  fetch(url).then(r=>r.json()).then(d=>{
    if(!d.success){
      container.innerHTML = '<div style="text-align:center;padding:30px;color:#e74c3c;">加载失败: '+d.error+'</div>';
      return;
    }
    
    // 等级筛选
    var cases = d.cases;
    if(grade){
      cases = cases.filter(function(c){ return c.grade === grade; });
    }
    
    // 更新来源统计
    var statsDiv = document.getElementById('kCSourceStats');
    if(statsDiv && d.source_stats){
      var statsHtml = Object.entries(d.source_stats).map(([k,v]) => 
        '<span style="margin-right:10px;">'+k+': '+v+'</span>'
      ).join('');
      statsDiv.innerHTML = statsHtml || '';
    }
    
    var badge = document.getElementById('knowledgeCasesBadge');
    if(badge) badge.textContent = '共 '+d.total+' 条';
    
    if(!cases || cases.length === 0){
      container.innerHTML = '<div style="text-align:center;padding:30px;color:#999;">暂无案例数据</div>';
      return;
    }
    
    // 渲染案例列表 - 深色模式
    var html = '';
    cases.forEach(function(c) {
      var gradeColor = c.grade === '上上吉' ? '#f87171' : 
                       c.grade === '上吉' ? '#fb923c' :
                       c.grade === '中吉' ? '#fbbf24' :
                       c.grade === '吉' ? '#4ade80' :
                       c.grade === '平' ? '#94a3b8' : '#ef4444';
      
      var sanchuanHtml = '';
      if(c.sanchuan){
        var sc = c.sanchuan;
        if(sc.first || sc.second || sc.third){
          sanchuanHtml = ' · 三传: ' + (sc.first || '-') + ' → ' + (sc.second || '-') + ' → ' + (sc.third || '-');
        }
      }
      
      var sourceIcon = c.source.indexOf('择日') >= 0 ? '📅' :
                       c.source.indexOf('天机') >= 0 ? '🔮' :
                       c.is_manual ? '✏️' : '📖';
      
      html += '<div style="border:1px solid #334155;border-radius:8px;padding:12px;margin-bottom:10px;background:#0f172a;transition:all .2s;" onmouseover="this.style.borderColor=\'#6366f1\'" onmouseout="this.style.borderColor=\'#334155\'">' +
              '<div style="display:flex;justify-content:space-between;align-items:start;">' +
              '<div style="flex:1;">' +
              '<div style="font-size:13px;font-weight:600;color:#e2e8f0;margin-bottom:4px;">' +
              sourceIcon + ' ' + c.title +
              (c.is_manual ? ' <span style="background:#78350f;color:#fbbf24;font-size:10px;padding:1px 6px;border-radius:10px;">手动</span>' : '') +
              '</div>' +
              '<div style="font-size:11px;color:#94a3b8;margin-bottom:6px;">' +
              '<span>📅 ' + (c.cast_datetime || c.date) + '</span>' +
              (c.mountain ? ' · <span>🏔️ ' + c.mountain + '山</span>' : '') +
              (c.keti ? ' · <span style="color:#a5b4fc;">📖 ' + c.keti + '</span>' : '') +
              sanchuanHtml +
              '</div>' +
              '</div>' +
              '<div style="text-align:right;min-width:80px;">' +
              '<div style="font-size:16px;font-weight:700;color:' + gradeColor + ';">' + c.grade + '</div>' +
              '<div style="font-size:11px;color:#64748b;">评分 ' + c.total_score + '</div>' +
              '</div>' +
              '</div>' +
              '</div>';
    });
    container.innerHTML = html;
  }).catch(function(err){
    container.innerHTML = '<div style="text-align:center;padding:30px;color:#e74c3c;">请求失败: '+err.message+'</div>';
  });
}

// ====== AI学习数据加载 ======
function loadAILEarnData() {
  loadKnowledgeCases();
  
  // 加载统计数据
  fetch('/api/knowledge/cases?limit=500').then(r=>r.json()).then(d=>{
    if(!d.success) return;
    
    var cases = d.cases || [];
    var total = d.total || cases.length;
    
    // 更新顶部统计
    document.getElementById('aiTotalCases').textContent = total;
    
    // 择日案例数
    var zeriCount = cases.filter(function(c){ return c.source && c.source.indexOf('择日') >= 0; }).length;
    document.getElementById('aiZeriCases').textContent = zeriCount;
    
    // 课体统计
    var ketiMap = {};
    cases.forEach(function(c){
      if(c.keti){
        ketiMap[c.keti] = (ketiMap[c.keti] || 0) + 1;
      }
    });
    document.getElementById('aiKetiCount').textContent = Object.keys(ketiMap).length;
    
    // 最近更新
    if(cases.length > 0){
      var latestDate = cases[0].date || cases[0].cast_datetime || '--';
      document.getElementById('aiLastUpdate').textContent = latestDate;
    }
    
    // 渲染课体分布
    renderKetiAnalysis(ketiMap);
    
    // 渲染等级分布
    renderGradeAnalysis(cases);
    
  }).catch(function(){});
}

function renderKetiAnalysis(ketiMap) {
  var container = document.getElementById('ketiAnalysis');
  if(!container) return;
  
  var entries = Object.entries(ketiMap).sort(function(a,b){ return b[1] - a[1]; });
  
  if(entries.length === 0){
    container.innerHTML = '<div style="text-align:center;padding:40px;color:#64748b;">暂无课体数据</div>';
    return;
  }
  
  var maxCount = entries[0][1];
  var colors = ['#6366f1','#8b5cf6','#ec4899','#f59e0b','#10b981','#06b6d4','#f97316','#ef4444'];
  
  var html = '<div style="display:flex;flex-direction:column;gap:12px;max-width:600px;margin:0 auto;">';
  entries.forEach(function([keti, count], idx){
    var pct = Math.round(count / maxCount * 100);
    var color = colors[idx % colors.length];
    html += '<div style="display:flex;align-items:center;gap:12px;">' +
            '<div style="width:80px;font-size:13px;color:#cbd5e1;text-align:right;">' + keti + '</div>' +
            '<div style="flex:1;background:#334155;border-radius:6px;height:24px;overflow:hidden;">' +
            '<div style="width:' + pct + '%;background:' + color + ';height:100%;border-radius:6px;display:flex;align-items:center;justify-content:flex-end;padding-right:8px;color:#fff;font-size:11px;box-shadow:0 0 8px ' + color + '40;">' + count + '</div>' +
            '</div>' +
            '</div>';
  });
  html += '</div>';
  container.innerHTML = html;
}

function renderGradeAnalysis(cases) {
  var container = document.getElementById('gradeAnalysis');
  if(!container) return;
  
  var gradeMap = {};
  cases.forEach(function(c){
    if(c.grade){
      gradeMap[c.grade] = (gradeMap[c.grade] || 0) + 1;
    }
  });
  
  if(Object.keys(gradeMap).length === 0){
    container.innerHTML = '<div style="text-align:center;padding:40px;color:#64748b;">暂无等级数据</div>';
    return;
  }
  
  var gradeOrder = ['上上吉','上吉','中吉','吉','平','小凶','凶','大凶'];
  var gradeColors = {
    '上上吉': '#f87171',
    '上吉': '#fb923c',
    '中吉': '#fbbf24',
    '吉': '#4ade80',
    '平': '#94a3b8',
    '小凶': '#fb923c',
    '凶': '#f87171',
    '大凶': '#ef4444'
  };
  
  var sortedEntries = gradeOrder.filter(function(g){ return gradeMap[g]; }).map(function(g){ return [g, gradeMap[g]]; });
  
  var total = cases.length;
  var html = '<div style="display:flex;gap:20px;flex-wrap:wrap;justify-content:center;max-width:800px;margin:0 auto;">';
  
  sortedEntries.forEach(function([grade, count]){
    var pct = Math.round(count / total * 100);
    var color = gradeColors[grade] || '#94a3b8';
    html += '<div style="text-align:center;background:#0f172a;border:1px solid #334155;border-radius:10px;padding:12px 16px;min-width:80px;">' +
            '<div style="font-size:24px;font-weight:700;color:' + color + ';text-shadow:0 0 10px ' + color + '40;">' + count + '</div>' +
            '<div style="font-size:12px;color:#e2e8f0;margin:4px 0;font-weight:500;">' + grade + '</div>' +
            '<div style="width:60px;height:6px;background:#334155;border-radius:3px;overflow:hidden;margin:0 auto;">' +
            '<div style="width:' + pct + '%;background:' + color + ';height:100%;"></div>' +
            '</div>' +
            '<div style="font-size:10px;color:#94a3b8;margin-top:2px;">' + pct + '%</div>' +
            '</div>';
  });
  
  html += '</div>';
  container.innerHTML = html;
}

function refreshKnowledgeIndex() {
  fetch('/api/knowledge/refresh', {method:'POST'}).then(r=>r.json()).then(d=>{
    if(d.success){
      alert('知识库已重建索引！\n案例数: '+d.stats.total_cases);
      loadKnowledgeCases();
      loadAILEarnData();
    } else {
      alert('刷新失败: '+d.error);
    }
  }).catch(function(err){
    alert('请求失败: '+err.message);
  });
}

function toggleAiDetail() {
  var body = document.getElementById('aiDetailBody');
  var caret = document.getElementById('aiFoldCaret');
  if (body.style.display === 'none') {
    body.style.display = 'block';
    caret.style.transform = 'rotate(90deg)';
  } else {
    body.style.display = 'none';
    caret.style.transform = 'rotate(0deg)';
  }
}
setInterval(loadTrainingStatus, 30000);
loadTrainingStatus();
applyUIMode(); /* 初始化：默认择日模式，隐藏交易元素 */
_initAnnounce(); /* 顶部滚动公告（可关闭） */

// ====== 量化预测(5天) ======
function loadQuantPrediction() {
  fetch(API+'/api/quant_20d').then(r=>r.json()).then(d=>{
    if(!d.success) return;
    if(d.source === '已保存历史' || (d.data && d.data.cycle_start)) {
      var btn = document.querySelector('button[onclick*=\"runQuantPrediction\"]');
      if(btn){ btn.disabled=true; btn.textContent='✅ 已预测(5天)'; btn.style.background='#27ae60'; }
    }
    renderQuantPrediction(d.data);
  }).catch(err=>console.error(err));
  
  fetch(API+'/api/quant_history').then(r=>r.json()).then(d=>{
    if(!d.success) return;
    renderQuantHistory(d.history);
  }).catch(err=>console.error(err));
}

function renderQuantPrediction(data) {
  if(!data) return;
  document.getElementById('qStart').textContent = data.cycle_start || '--';
  document.getElementById('qEnd').textContent = data.cycle_end || '--';
  document.getElementById('qTrend').textContent = normDir(data.trend_prediction) || '--';
  document.getElementById('qConf').textContent = (data.confidence||0)+'%';
  document.getElementById('qBest').textContent = data.best_etf ? data.best_etf.name : '--';
  document.getElementById('qPos').textContent = data.best_etf ? (data.best_etf.position+'%') : '--';
  
  const tbody = document.getElementById('quantEtfBody');
  if(data.all_etfs && data.all_etfs.length) {
    tbody.innerHTML = data.all_etfs.map(etf => `
      <tr>
        <td><strong>${etf.name}</strong></td>
        <td>${etf.price}</td>
        <td class="${etf.momentum_20d>0?'text-up':'text-down'}">${etf.momentum_20d}%</td>
        <td>${etf.volatility}%</td>
        <td>${etf.rsi}</td>
        <td>${etf.ma_trend||'--'}</td>
        <td>${etf.position}%</td>
        <td><strong>${etf.score}</strong></td>
      </tr>
    `).join('');
  }
}

function renderQuantHistory(history) {
  const tbody = document.getElementById('quantHistoryBody');
  if(!history || !history.length) {
    tbody.innerHTML = '<tr><td colspan="6" style="text-align:center;color:#999;">暂无历史</td></tr>';
    return;
  }
  tbody.innerHTML = history.map(h => `
    <tr>
      <td>${h.cycle_start}</td>
      <td>${h.cycle_end}</td>
      <td>${h.trend_prediction?normDir(h.trend_prediction):'--'}</td>
      <td>${(h.confidence||0)}%</td>
      <td>${h.best_etf?h.best_etf.name:'--'}</td>
      <td>${h.average_score||0}</td>
    </tr>
  `).join('');
}

function runQuantPrediction(e) {
  const btn = e.target;
  btn.disabled = true; btn.textContent = '⏳ 运行中...';
  fetch(API+'/api/quant_20d').then(r=>r.json()).then(d=>{
    if(!d.success){ btn.disabled=false; btn.textContent='🔄 运行量化预测'; alert('预测失败: '+d.error); return; }
    btn.disabled = true; btn.textContent = '✅ 已预测(5天)'; btn.style.background = '#27ae60';
    renderQuantPrediction(d.data);
  }).catch(err=>{ btn.disabled=false; btn.textContent='🔄 运行量化预测'; alert('请求失败'); });
}

// ====== 六壬预测(5天) ======
function loadLiuren20dPrediction() {
  // 加载天机起课统计（新面板核心）
  loadTianjiStats();
  // 天机应期日历提醒（2026-09-08）
  loadTianjiYingqi();
  // 事件起课台账 + 条件基线（独立体系）
  loadEventBoard();

  var hasMainPrediction = false;
  var noticeEl = document.getElementById('liurenDataNotice');

  fetch(API+'/api/liuren_20d?auto=1').then(r=>r.json()).then(d=>{
    if(d.data) {
      hasMainPrediction = true;
      // 当前周期有预测 → 正常显示，无提示
      noticeEl.style.display = 'none';
      renderLiuren20dPrediction(d.data);
    }
  }).catch(err=>console.error(err)).finally(() => {
    fetch(API+'/api/liuren_history').then(r=>r.json()).then(d=>{
      if(!d.success || !d.history || d.history.length === 0) {
        // 完全没有任何历史数据
        if(!hasMainPrediction) {
          noticeEl.style.display = 'block';
          noticeEl.style.background = '#fff3cd';
          noticeEl.style.color = '#856404';
          noticeEl.style.border = '1px solid #ffeeba';
          noticeEl.innerHTML = '📋 <b>当前周期尚未进行天机起课</b>。请在上方填入心动日期+时辰后点击「录入天机起课」。';
          // 清空各字段 + 重置按钮为初始状态
          document.getElementById('lStart').textContent = '--';
          document.getElementById('lKeti').textContent = '--';
          document.getElementById('lSanchuan').textContent = '--';
          document.getElementById('lTianjiang').textContent = '--';
          document.getElementById('lTrend').textContent = '--';
          document.getElementById('lConf').textContent = '--';
          document.getElementById('liurenFinalConclusion').style.display = 'none';
          document.getElementById('tianjiCastResult').style.display = 'none';
          document.getElementById('liurenBtnArea').innerHTML = '<button id="liurenPredictBtn" class="op-btn zeri" onclick="castTianji(event)" style="background:#667eea;color:#fff;padding:10px 24px;border-radius:8px;border:none;cursor:pointer;font-weight:600;">✨ 录入天机起课</button>';
        }
        return;
      }
      renderLiurenHistory(d.history);
      // 有历史记录 → 按当前周期是否已起课显示按钮状态
      _setLiurenPredictedState(hasMainPrediction);

      // 没有当前周期预测时，显示历史数据 + 明确提示
      if(!hasMainPrediction) {
        var latest = d.history[0];
        var latestDate = (latest.cycle_start || latest.date || '未知日期');
        noticeEl.style.display = 'block';
        noticeEl.style.background = '#e8f4fd';
        noticeEl.style.color = '#0c5460';
        noticeEl.style.border = '1px solid #bee5eb';
        noticeEl.innerHTML = '⚠️ <b>当前周期（' + _todayStr() + '）尚未进行六壬起课预测</b>，以下显示为最近一次历史预测记录（日期：' + latestDate + '）。如需最新预测，请点击「开始预测」按钮。';
        renderLiuren20dPrediction(latest);
      } else {
        noticeEl.style.display = 'none';
      }
    }).catch(err=>console.error(err));
  });
}

/** 返回今天日期字符串 YYYY-MM-DD */
function _todayStr() {
  var d = new Date();
  var m = String(d.getMonth()+1).padStart(2,'0');
  var day = String(d.getDate()).padStart(2,'0');
  return d.getFullYear() + '-' + m + '-' + day;
}

function renderSanchuanKege(data) {
  // 从 analysis.keti_duanyu.sanchuan_kege 提取三传课格信息
  const kd = (data.analysis && data.analysis.keti_duanyu) || {};
  const sk = kd.sanchuan_kege || {};
  const kegeList = sk.课格列表 || [];
  const kegeDetails = sk.课格详情 || {};
  const signals = sk.股市信号 || {};
  const summary = kd.sanchuan_kege_summary || '';
  
  if (kegeList.length === 0) {
    // 尝试直接用三传检测（前端回退）
    var sc = data.san_chuan || [];
    if (sc.length >= 3) {
      var jcs = [{set: ['申','子','辰'], name: '润下课(水局)'}, {set: ['寅','午','戌'], name: '炎上课(火局)'}, {set: ['亥','卯','未'], name: '曲直课(木局)'}, {set: ['巳','酉','丑'], name: '从革课(金局)'}];
      var found = jcs.filter(function(j) { return j.set.sort().join(',') === sc.slice().sort().join(','); });
      if (found.length > 0) {
        return '<div><strong>三传课格(前端):</strong> <span style="color:#2980b9;">' + found[0].name + '</span></div>';
      }
    }
    return '';
  }
  
  var html = ['<div><strong>三传课格:</strong>'];
  kegeList.forEach(function(kg, i) {
    var detail = kegeDetails[kg] || {};
    var jx = detail.吉凶 || '';
    // 吉系: 吉/小吉/大吉/上吉/平偏吉 → 绿; 凶系: 凶/中凶/大凶/平偏凶 → 红; 其他 → 黄
    var color = '#f39c12';
    if (/^(吉|小吉|大吉|上吉|平偏吉)$/.test(jx)) color = '#27ae60';
    else if (/^(凶|中凶|大凶|平偏凶)$/.test(jx)) color = '#e74c3c';
    html.push(' <span style="color:' + color + ';font-weight:bold;border:1px solid ' + color + ';padding:1px 6px;border-radius:3px;margin:0 2px;">' + kg + '</span>');
  });
  html.push('</div>');
  
  // 添加股市信号
  if (signals.综合倾向 && signals.综合倾向 !== '平') {
    var signalColor = (signals.综合倾向 === '涨' || signals.综合倾向 === '震荡偏涨') ? '#e74c3c' : '#27ae60';
    html.push('<div><strong>课格信号:</strong> <span style="color:' + signalColor + ';font-weight:bold;">' + signals.综合倾向 + '</span> (强度: ' + (signals.信号强度||0).toFixed(2) + ')</div>');
    if (signals.操作建议) {
      html.push('<div style="font-size:11px;color:#888;margin-top:2px;"><em>' + signals.操作建议 + '</em></div>');
    }
  }
  
  return html.join('');
}

function renderBifaRules(data) {
  // 从 analysis.keti_duanyu.bifa 提取毕法赋法条信息
  const kd = (data.analysis && data.analysis.keti_duanyu) || {};
  const bf = kd.bifa || {};
  const rules = bf['匹配法条'] || [];
  const details = bf['法条详情'] || {};
  const signals = bf['股市信号'] || {};
  const summary = kd.bifa_summary || '';
  
  if (rules.length === 0) return '';
  
  // 颜色：涨→红/跌→绿/震荡→黄
  var sigColor = '#f39c12';
  if (signals.综合倾向 === '涨') sigColor = '#e74c3c';
  else if (signals.综合倾向 === '跌') sigColor = '#27ae60';
  
  var html = ['<div style="margin-top:6px;padding-top:6px;border-top:1px dashed #ddd;">'];
  html.push('<strong>毕法赋:</strong>');
  
  rules.forEach(function(name) {
    var d = details[name] || {};
    var rid = d.id || '?';
    var sig = d['股市信号'] || '?';
    var badgeColor = '#f39c12';
    if (sig === '涨') badgeColor = '#e74c3c';
    else if (sig === '跌') badgeColor = '#27ae60';
    
    html.push(' <span style="display:inline-block;color:' + badgeColor + ';border:1px solid ' + badgeColor + ';padding:1px 5px;border-radius:3px;margin:2px;font-size:11px;" title="' + (d['规则']||'') + '">#' + rid + ' ' + name + '</span>');
  });
  
  html.push('</div>');
  
  // 毕法赋综合信号
  if (signals.综合倾向 && signals.综合倾向 !== '平') {
    html.push('<div style="font-size:11px;margin-top:2px;"><strong>毕法信号:</strong> <span style="color:' + sigColor + ';font-weight:bold;">' + signals.综合倾向 + '</span> (' + (signals.信号强度||0).toFixed(2) + ')</div>');
  }
  
  return html.join('');
}

function renderLiuren20dPrediction(data) {
  if(!data) return;
  const bi = data.basic_info || {};
  document.getElementById('lStart').textContent = data.cycle_start || '--';
  document.getElementById('lYuejiang').textContent = bi.yuejiang ? `${bi.yuejiang}(${bi.yuejiang_name||''})` : '--';
  document.getElementById('lKeti').textContent = data.keti || '--';
  document.getElementById('lSanchuan').textContent = data.san_chuan ? data.san_chuan.join('→') : '--';
  document.getElementById('lTrend').textContent = data.prediction ? normDir(data.prediction.trend) : '--';
  document.getElementById('lConf').textContent = data.prediction ? (data.prediction.confidence+'%') : '--';
  
  document.getElementById('liurenBasicInfo').innerHTML = `
    <div><strong>四柱:</strong> ${bi.ri_gan}${bi.ri_zhi}日 · ${bi.shichen}时</div>
    <div><strong>月将:</strong> ${bi.yuejiang} (${bi.yuejiang_name||''})</div>
    <div><strong>课体:</strong> ${data.keti} (${data.qifa||''})</div>
    <div><strong>三传:</strong> ${(data.san_chuan||[]).join(' → ')}</div>
    ${renderSanchuanKege(data)}
    ${renderBifaRules(data)}
  `;
  
  // === 四课：统一表格格式（顶栏天将/蓝字地支/干支组合/底栏课号）===
  const sike = data.si_ke || [];
  const analysis_tj = (data.analysis && data.analysis.tianjiang) || {};
  const sanchuan_tj_list = data.sanchuan_tianjiang || [];
  if(sike.length > 0){
    // 构建地支→天将映射（从sanchuan_tianjiang或analysis.tianjiang）
    var sikeTjMap = {};
    // 尝试从四课天将数据获取
    if(data.sike_tianjiang){
      data.sike_tianjiang.forEach(function(st){ sikeTjMap[st.zhi||'']=st.jiang||''; });
    }
    // 天将短名→显示名
    var tjDisp = {'贵':'贵人','蛇':'螣蛇','雀':'朱雀','合':'六合','勾':'勾陈','龙':'青龙','空':'天空','虎':'白虎','常':'太常','玄':'玄武','阴':'太阴','后':'天后',
      '贵人':'贵人','腾蛇':'螣蛇','朱雀':'朱雀','六合':'六合','勾陈':'勾陈','青龙':'青龙','天空':'天空','白虎':'白虎','太常':'太常','玄武':'玄武','太阴':'太阴','天后':'天后'};
    var sikeHtml = '<table style="width:100%;border-collapse:collapse;table-layout:fixed;background:#f8f9fc;border-radius:8px;padding:10px 12px;">'+
      '<caption style="font-size:11px;color:#999;margin-bottom:8px;font-weight:600;text-align:left;padding-left:4px;">📋 四课</caption>'+
      '<tr>';  // 天将标题行
    var sikeHdr=[], sikeDz=[], sikeGz=[], sikeNum=[];
    const keLabels = ['第一课','第二课','第三课','第四课'];
    for(var si=sike.length-1;si>=0;si--){
      const sk=sike[si];
      const top=Array.isArray(sk)?(sk[1]||'?'):(sk.top||'?');
      const bottom=Array.isArray(sk)?(sk[2]||'?'):(sk.bottom||'?');
      const tj=sikeTjMap[top]||'';
      const lbl=tjDisp[tj]||tj||' ';
      sikeHdr.push('<td style="text-align:center;font-size:10px;color:#94a3b8;padding:2px 0 6px;">'+lbl+'</td>');
      sikeDz.push('<td style="text-align:center;font-size:18px;font-weight:700;color:#60a5fa;padding:4px 0;">'+top+'</td>');
      sikeGz.push('<td style="text-align:center;font-size:11px;color:#6b7280;padding:2px 0 6px;">'+bottom+'</td>');
      sikeNum.push('<td style="text-align:center;font-size:9px;color:#9ca3af;padding:2px 0;">'+keLabels[sike.length-1-si]+'</td>');
    }
    sikeHtml += sikeHdr.join('')+'</tr><tr>'+sikeDz.join('')+'</tr><tr>'+sikeGz.join('')+'</tr><tr>'+sikeNum.join('')+'</tr></table>';
    document.getElementById('liurenSike').innerHTML = sikeHtml;
  } else {
    document.getElementById('liurenSike').innerHTML = '<span style="color:#999;">暂无四课数据</span>';
  }
  
  const analysis = data.analysis || {};
  const lq = analysis.liuqin || [];
  const ws = analysis.wangshuai || [];
  const kq = analysis.kong_info || {};
  
  // === 三传：统一表格格式（六亲 | 地支(橙) | 天将）===
  const sc = data.san_chuan || data.sanchuan || [];
  if(sc.length > 0){
    // 六亲计算：优先用后端 analysis.liuqin（引擎输出），缺省回退共享 _liuQ/_dunG/_xunKong
    var rg2=(data.rizhu||data.basic_info?.ri_gan||'乙')[0];
    var rz2=(data.rizhu||data.basic_info?.ri_zhi||'子').slice(-1);
    var xk2=_xunKong(rg2, rz2);

    var scRows = '';
    for(var j=0;j<sc.length;j++){
      var dz2=sc[j], tj2=(sanchuan_tj_list[j])||(analysis_tj[['初传','中传','末传'][j]])||'', dg2=_dunG(rg2, dz2);
      var isXK2=xk2.indexOf(dz2)>=0, gdz2=isXK2?'○'+dz2:dg2+dz2, lqName2=(lq&&lq[j]&&lq[j]['六亲'])||_liuQ(rg2, dz2);
      scRows += '<tr style="border-top:1px solid #eee;">'+
        '<td style="padding:6px 0;color:#6b7280;">'+lqName2+'</td>'+
        '<td style="padding:6px 0;font-weight:700;color:#d97706;font-family:monospace;font-size:14px;">'+gdz2+'</td>'+
        '<td style="padding:6px 0;color:#6b7280;">'+tj2+'</td></tr>';
    }
    document.getElementById('liurenSanchuan').innerHTML =
      '<table style="width:100%;border-collapse:collapse;font-size:13px;background:#f8f9fc;border-radius:8px;padding:10px 12px;">'+
      '<caption style="font-size:11px;color:#999;margin-bottom:8px;font-weight:600;text-align:left;padding-left:4px;">🔗 三传</caption>'+
      '<tr style="color:#9ca3af;font-size:10px;">'+
      '<td style="padding:4px 0 8px;width:22%;">六亲</td><td style="padding:4px 0 8px;width:39%;">地支</td><td style="padding:4px 0 8px;width:39%;">天将</td></tr>'+
      scRows + '</table>';
    // 旺衰和旬空信息移入下方补充行（保留原有数据不丢失，复用上方已声明的 ws/kq）
    if(ws.length > 0 || Object.keys(kq).length > 0){
      var extraHtml = '<div style="margin-top:8px;font-size:11px;color:#6b7280;line-height:1.8;">';
      if(ws.length > 0) extraHtml += '<span style="margin-right:16px;">旺衰: '+ws.map(function(w){return w.地支+'('+w.旺衰+')'}).join(' → ')+'</span>';
      if(Object.keys(kq).length > 0) extraHtml += '<span>旬空: 初传'+(kq['初传']?'落空':'不空')+', 中传'+(kq['中传']?'落空':'不空')+', 末传'+(kq['末传']?'落空 ⚠️':'不空')+'</span>';
      extraHtml += '</div>';
      document.getElementById('liurenSanchuan').innerHTML += extraHtml;
    }
  } else {
    document.getElementById('liurenSanchuan').innerHTML = '<span style="color:#999;">暂无三传数据</span>';
  }
  
  const reasons = (data.prediction && data.prediction.reasons) || [];
  document.getElementById('liurenReasoning').innerHTML = reasons.map((r,i) =>
    `<div style="padding:4px 0;">${i+1}. ${r}</div>`
  ).join('') || '<div>暂无推理过程</div>';
  
  const fullAnalysis = [];
  // 维度1: 课体等级（训练库课体断语）
  if(analysis.keti_duanyu && analysis.keti_duanyu.keti_name) {
    const kd = analysis.keti_duanyu;
    const levelColor = {'上吉':'#27ae60','大吉':'#27ae60','中吉':'#2ecc71','小吉':'#f1c40f','吉':'#f1c40f','平':'#95a5a6','凶':'#e74c3c','小凶':'#e74c3c','中凶':'#c0392b','大凶':'#8e44ad'};
    const color = levelColor[kd.level] || '#95a5a6';
    fullAnalysis.push('<strong>1. 课体等级（训练库）:</strong>');
    fullAnalysis.push(`<div style="margin:4px 0;padding:8px 12px;background:#f8f9fc;border-left:3px solid ${color};border-radius:4px;">`);
    fullAnalysis.push(`<div><strong style="color:${color};">${kd.keti_name} [${kd.level}]</strong> · 64课经: <strong style="color:${color};">${kd.ke_64_level}</strong>${kd.is_daxiong?' ⚠️大凶':''}</div>`);
    if(kd.duanyu) fullAnalysis.push(`<div style="margin-top:4px;color:#555;">断语: ${kd.duanyu}</div>`);
    if(kd.zonglun) fullAnalysis.push(`<div style="margin-top:2px;color:#777;font-size:12px;">总论: ${kd.zonglun.substring(0,80)}${kd.zonglun.length>80?'...':''}</div>`);
    if(kd.ke_64_xiangyue) fullAnalysis.push(`<div style="margin-top:2px;color:#777;font-size:12px;">象曰: ${kd.ke_64_xiangyue.substring(0,60)}${kd.ke_64_xiangyue.length>60?'...':''}</div>`);
    fullAnalysis.push('</div>');
  }
  // 维度2: 六亲
  if(analysis.liuqin && analysis.liuqin.length) {
    fullAnalysis.push('<strong>2. 六亲:</strong> ' + analysis.liuqin.map(i=>i.地支+'('+i.六亲+')').join(' → '));
  }
  // 维度3: 旺衰
  if(analysis.wangshuai && analysis.wangshuai.length) {
    fullAnalysis.push('<strong>3. 旺衰:</strong> ' + analysis.wangshuai.map(i=>i.地支+'('+i.旺衰+')').join(' → '));
  }
  // 维度4: 空亡
  fullAnalysis.push('<strong>4. 空亡:</strong> 初传'+(kq['初传']?'落空 ⚠️':'不空')+', 中传'+(kq['中传']?'落空 ⚠️':'不空')+', 末传'+(kq['末传']?'落空 ⚠️':'不空'));
  // 维度5: 三传关系
  if(analysis.relationships && analysis.relationships.length) {
    fullAnalysis.push('<strong>5. 三传关系:</strong>');
    analysis.relationships.forEach(r => {
      const tags = [];
      if(r['五行关系']) tags.push(r['五行关系']);
      if(r['六合']) tags.push('六合');
      if(r['六冲']) tags.push('六冲');
      if(r['三刑']) tags.push('三刑');
      if(r['六害']) tags.push('六害');
      fullAnalysis.push(`<div>  ${r.from}→${r.to}: ${tags.join(', ')||'无特殊关系'}</div>`);
    });
  }
  // 维度6: 四课加临
  if(analysis.sike_qi && analysis.sike_qi.关系) {
    fullAnalysis.push('<strong>6. 四课加临:</strong> ' + analysis.sike_qi.关系 + (analysis.sike_qi.分析?' — '+analysis.sike_qi.分析:''));
  }
  // 维度7: 用神五气
  if(analysis.yong_shen && analysis.yong_shen.分析) {
    fullAnalysis.push('<strong>7. 用神五气:</strong> ' + (analysis.yong_shen.用神||'') + '(' + (analysis.yong_shen.旺衰||'') + ') — ' + analysis.yong_shen.分析.substring(0,60));
  }
  // 维度8: 三传制救
  if(analysis.sanchuan_zhijiu && analysis.sanchuan_zhijiu.关系) {
    fullAnalysis.push('<strong>8. 三传制救:</strong> ' + analysis.sanchuan_zhijiu.关系 + (analysis.sanchuan_zhijiu.分析?' — '+analysis.sanchuan_zhijiu.分析:''));
  }
  // 维度9: 贵神吉凶
  if(analysis.guishen_jixiong && Object.keys(analysis.guishen_jixiong).length) {
    const gjItems = [];
    for(const [chuan, info] of Object.entries(analysis.guishen_jixiong)) {
      const tj = (typeof info === 'object') ? (info.天将||'') : info;
      if(tj) gjItems.push(`${chuan}:${tj}`);
    }
    if(gjItems.length) fullAnalysis.push('<strong>9. 贵神吉凶:</strong> ' + gjItems.join(', '));
  }
  // 维度10: 八杀体系
  if(analysis.ba_sha && Object.keys(analysis.ba_sha).length) {
    const bs = analysis.ba_sha;
    const shaList = Array.isArray(bs.杀) ? bs.杀 : (bs.杀 ? [bs.杀] : []);
    const validSha = shaList.filter(s => s && s !== '无');
    if(validSha.length) {
      fullAnalysis.push('<strong>10. 八杀体系:</strong> <span style="color:#e74c3c;">' + validSha.join(', ') + ' ⚠️</span>');
    } else {
      fullAnalysis.push('<strong>10. 八杀体系:</strong> 无凶杀');
    }
  }
  // 维度11: 十二气财星
  if(analysis.cai_shi_er_qi && analysis.cai_shi_er_qi.财星状态) {
    fullAnalysis.push('<strong>11. 十二气财星:</strong> ' + analysis.cai_shi_er_qi.财星状态 + (analysis.cai_shi_er_qi.分析?' — '+String(analysis.cai_shi_er_qi.分析).substring(0,50):''));
  }
  // 维度12: 身强身弱
  if(analysis.shen_qiang_ruo && analysis.shen_qiang_ruo.状态) {
    fullAnalysis.push('<strong>12. 身强身弱:</strong> ' + analysis.shen_qiang_ruo.状态);
  }
  // 附加: 神煞
  if(analysis.shen_sha && Object.keys(analysis.shen_sha).length) {
    const ss = analysis.shen_sha;
    const ssItems = [];
    for(const [k, v] of Object.entries(ss)) {
      if(v && v !== '无' && v !== '') ssItems.push(`${k}:${v}`);
    }
    if(ssItems.length) fullAnalysis.push('<strong>附. 神煞:</strong> ' + ssItems.join(', '));
  }
  document.getElementById('liurenAnalysis').innerHTML = fullAnalysis.join('') || '<div>暂无分析数据</div>';

  // 训练库匹配（全数据源）
  var evo = analysis.evo_data;
  var kd = analysis.keti_duanyu;
  console.log('[EVO] evo_data=', evo);
  var h = '';

  if (kd && kd.keti_name) {
    var lvlColor = {'上吉':'#27ae60','大吉':'#27ae60','中吉':'#2ecc71','小吉':'#f1c40f','吉':'#f1c40f','平':'#95a5a6','凶':'#e74c3c','小凶':'#e74c3c','中凶':'#c0392b','大凶':'#8e44ad'};
    var c = lvlColor[kd.level] || '#95a5a6';
    h += '<div style="padding:4px 0;"><strong>🔮 训练库课体:</strong> <span style="color:'+c+';font-weight:bold;">'+kd.keti_name+' ['+kd.level+']</span>';
    h += ' · 64课经: <span style="color:'+c+';">'+kd.ke_64_level+'</span>'+(kd.is_daxiong?' ⚠️大凶':'')+'</div>';
    if (kd.duanyu) h += '<div style="padding:2px 0;color:#555;font-size:13px;">断语: '+kd.duanyu.substring(0,100)+'</div>';
    if (kd.zonglun) h += '<div style="padding:2px 0;color:#777;font-size:12px;">总论: '+kd.zonglun.substring(0,100)+'</div>';
  }
  if (analysis.tianjiang) {
    var tj = analysis.tianjiang;
    h += '<div style="padding:4px 0;"><strong>⚔️ 训练库天将:</strong> ' + [tj.初传,tj.中传,tj.末传].filter(Boolean).join(' → ') + ' (' + tj.昼夜 + tj.顺逆 + ')</div>';
  }

  if (evo && typeof evo === 'object') {
    if (evo.case_kb_matched > 0) {
      h += '<div style="padding:4px 0;">📚 <strong>古案例匹配:</strong> ' + evo.case_kb_matched + '案 (三传 ' + (evo.sc_key||'') + ')</div>';
    } else {
      h += '<div style="padding:4px 0;color:#999;">📚 古案例库: 三传在675案中无直接匹配（12维推理已覆盖此课）</div>';
    }
    if (evo.factor_impacts !== 0) h += '<div style="padding:4px 0;">📊 <strong>因子修正:</strong> ' + (evo.factor_impacts>0?'+':'') + evo.factor_impacts + '分</div>';
    if (evo.corrections_applied > 0) h += '<div style="padding:4px 0;">✋ <strong>人工纠正:</strong> ' + evo.corrections_applied + '条</div>';
    if (evo.evo_boost !== 0) h += '<div style="padding:4px 0;">🧬 <strong>综合修正:</strong> ' + (evo.evo_boost>0?'+':'') + evo.evo_boost + '分</div>';
    var ts = evo.trainer_summary;
    if (ts) {
      h += '<div style="margin-top:4px;padding-top:4px;border-top:1px dashed #ccc;color:#888;font-size:11px;">';
      h += '🏋️ ' + (ts.case_kb_total||0) + '古案 + ' + (ts.corrections_count||0) + '纠正 + ' + (ts.evolution_data_size||0) + '进化 | 基准准确率' + (ts.insights_accuracy||0) + '%';
      h += '</div>';
    }
  }
  document.getElementById('liurenEvoData').innerHTML = h;
  
  // 课格股市规则渲染
  if(window._ketiRules && kd && kd.keti_name) {
    var kb = kd.keti_name.replace('课','').split('，')[0].trim();
    var rules = window._ketiRules[kb];
    if(rules) {
      var rh = '<div style="font-weight:bold;margin-bottom:4px;">📖 ' + kb + '课 · 股市判断</div>';
      for(var rk in rules) {
        rh += '<div style="padding:2px 0;font-size:12px;">• <strong>' + rk + '</strong>: ' + rules[rk] + '</div>';
      }
      document.getElementById('liurenKetiRule').innerHTML = rh;
    } else {
      document.getElementById('liurenKetiRule').innerHTML = '<div style="color:#999;">课格「' + kb + '」暂无股市规则</div>';
    }
  }
   '<div style="color:#999;">训练库数据加载中...</div>';
  
  // 最终结论
  var fc = document.getElementById('liurenFinalConclusion');
  if(fc && data.prediction) {
    fc.style.display = 'block';
    var trend = data.prediction.trend || '--';
    var vet = document.getElementById('lFinalVerdict');
    vet.textContent = trend;
    vet.style.color = (trend.indexOf('涨')>=0) ? '#ff4444' : (trend.indexOf('跌')>=0) ? '#00ff88' : '#ffaa00';
    var det = document.getElementById('lFinalDetail');
    det.textContent = '评分: ' + (data.prediction.score||0) + ' | 置信度: ' + (data.prediction.confidence||0) + '% | 课体: ' + (data.keti||'');
  }

  // 融合判断（支柱①②③）
  renderFusedJudgment(data);
  // 综合叙事（支柱④ CBR + 壬归寻原）
  renderHolisticJudgment(data);

}

function renderHolisticJudgment(data) {
  var sec = document.getElementById('holisticSection');
  var card = document.getElementById('holisticCard');
  if(!sec || !card) return;
  var hj = data && data.holistic_judgment;
  if(!hj || hj.error) { sec.style.display = 'none'; return; }
  sec.style.display = 'block';
  var trend = hj.trend || '--';
  var tColor = (trend.indexOf('涨')>=0) ? '#e74c3c' : (trend.indexOf('跌')>=0) ? '#27ae60' : '#f39c12';
  var score = hj.score; var conf = Math.round((hj.confidence||0)*100);
  // 总断
  var html = '';
  html += '<div style="display:flex;gap:18px;align-items:center;flex-wrap:wrap;margin-bottom:10px;">';
  html += '  <div style="min-width:110px;"><div style="font-size:12px;color:#888;">叙事趋势</div><div style="font-size:26px;font-weight:900;color:'+tColor+';">'+trend+'</div></div>';
  html += '  <div style="text-align:center;"><div style="font-size:11px;color:#888;">得分</div><div style="font-size:18px;font-weight:700;color:#b9770e;">'+(score===undefined?'--':score)+'</div></div>';
  html += '  <div style="text-align:center;"><div style="font-size:11px;color:#888;">置信度</div><div style="font-size:18px;font-weight:700;color:#2980b9;">'+conf+'%</div></div>';
  html += '</div>';
  // 辨证五轴
  var axes = hj.axes || {};
  var axZh = {'动静':'动静轴','刚柔':'刚柔轴','主客':'主客轴','虚实':'虚实轴','始终':'始终轴'};
  var axItems = [];
  for(var ak in axZh){
    var av = axes[ak];
    if(!av) continue;
    var dir = av.dir || '--';
    var signed = av.signed;
    var sColor = (signed>0)?'#e74c3c':(signed<0)?'#27ae60':'#95a5a6';
    axItems.push('<span style="display:inline-block;margin:0 10px 6px 0;font-size:12px;"><strong>'+axZh[ak]+':</strong> <span style="color:'+sColor+';font-weight:700;">'+dir+' ('+(signed>=0?'+':'')+signed+')</span></span>');
  }
  if(axItems.length){
    html += '<div style="background:#fffdf6;border:1px solid #f0e2bf;border-radius:6px;padding:8px 12px;margin-bottom:10px;line-height:1.9;">';
    html += '  <strong style="color:#b9770e;">⚖️ 辨证五轴：</strong><br>'+axItems.join('');
    html += '</div>';
  }
  // 总断
  if(hj.zongduan){
    html += '<div style="background:#fffaf0;border-left:3px solid #d4a017;border-radius:4px;padding:8px 12px;margin-bottom:10px;color:#5b4a2a;line-height:1.7;">';
    html += '  <strong style="color:#b9770e;">📖 总断（壬归·寻原）：</strong><br>'+hj.zongduan;
    html += '</div>';
  }
  // CBR 引例
  var cases = hj.retrieved_cases || [];
  if(cases.length){
    html += '<div style="font-size:12px;color:#888;margin-bottom:4px;"><strong style="color:#b9770e;">📚 CBR 相似古例（'+cases.length+'）：</strong></div>';
    cases.forEach(function(c){
      html += '<div style="background:#fffef9;border:1px solid #f0e2bf;border-radius:6px;padding:8px 12px;margin-bottom:6px;">';
      html += '  <div style="font-weight:700;color:#8a6d1a;">'+ (c.name||'未命名') +' <span style="font-weight:400;color:#999;font-size:11px;">['+(c.source||'')+'] · 相似度'+(c.score!==undefined?c.score:'-')+' · '+(c.reason||'')+'</span></div>';
      if(c.interpretation) html += '  <div style="font-size:12px;color:#6b5b35;margin-top:3px;line-height:1.6;">'+c.interpretation+'</div>';
      html += '</div>';
    });
  }
  // 双视角提示
  var fj = data.fused_judgment || {};
  if(fj.trend && fj.trend !== trend){
    html += '<div style="margin-top:8px;font-size:12px;color:#777;background:#f8f9fc;border-radius:6px;padding:6px 12px;">';
    html += '  🔍 <strong>双视角提示：</strong>概率层(①②③)判「'+fj.trend+'」与叙事层(④)判「'+trend+'」存在差异，属正常——前者为证据融合概率，后者为辨证+古例锚定，请结合研判。';
    html += '</div>';
  }
  card.innerHTML = html;
}

function renderFusedJudgment(data) {
  var sec = document.getElementById('fusedJudgmentSection');
  var card = document.getElementById('fusedJudgmentCard');
  if(!sec || !card) return;
  var fj = data && data.fused_judgment;
  if(!fj) { sec.style.display = 'none'; return; }
  sec.style.display = 'block';
  var trend = fj.trend || '--';
  var pUp = Math.round((fj.prob_up||0)*100);
  var pDown = Math.round((fj.prob_down||0)*100);
  var pFlat = Math.round((fj.prob_flat||0)*100);
  // 中文惯例：涨红 · 跌绿
  var tColor = (trend.indexOf('涨')>=0) ? '#e74c3c' : (trend.indexOf('跌')>=0) ? '#27ae60' : '#f39c12';
  var conf = Math.round((fj.confidence||0)*100);
  var conflict = Math.round((fj.conflict||0)*100);
  var sigCount = fj.signal_count || (fj.active_signals?fj.active_signals.length:0);
  var gateLog = (fj.gate_log||[]).slice(0,8).map(function(g){return '• '+g;}).join('<br>') || '（无门控命中）';
  var html = '';
  html += '<div style="display:flex;gap:24px;flex-wrap:wrap;align-items:center;">';
  html += '  <div style="min-width:120px;"><div style="font-size:12px;color:#888;">融合趋势判定</div><div style="font-size:30px;font-weight:900;color:'+tColor+';">'+trend+'</div></div>';
  html += '  <div style="flex:1;min-width:240px;">';
  html += '    <div style="display:flex;height:24px;border-radius:6px;overflow:hidden;font-size:11px;color:#fff;font-weight:600;">';
  html += '      <div style="width:'+pUp+'%;background:#e74c3c;display:flex;align-items:center;justify-content:center;">'+(pUp>8?('涨'+pUp+'%'):'')+'</div>';
  html += '      <div style="width:'+pFlat+'%;background:#95a5a6;display:flex;align-items:center;justify-content:center;">'+(pFlat>8?('平'+pFlat+'%'):'')+'</div>';
  html += '      <div style="width:'+pDown+'%;background:#27ae60;display:flex;align-items:center;justify-content:center;">'+(pDown>8?('跌'+pDown+'%'):'')+'</div>';
  html += '    </div>';
  html += '    <div style="font-size:11px;color:#999;margin-top:4px;">概率条按中文惯例：涨红 · 平灰 · 跌绿</div>';
  html += '  </div>';
  html += '  <div style="display:flex;gap:18px;">';
  html += '    <div style="text-align:center;"><div style="font-size:11px;color:#888;">置信度</div><div style="font-size:20px;font-weight:700;color:#2980b9;">'+conf+'%</div></div>';
  html += '    <div style="text-align:center;"><div style="font-size:11px;color:#888;">证据冲突</div><div style="font-size:20px;font-weight:700;color:#8e44ad;">'+conflict+'%</div></div>';
  html += '    <div style="text-align:center;"><div style="font-size:11px;color:#888;">激活信号</div><div style="font-size:20px;font-weight:700;">'+sigCount+'</div></div>';
  html += '  </div>';
  html += '</div>';
  html += '<div style="margin-top:12px;font-size:12px;color:#555;background:#f8f9fc;border-radius:6px;padding:8px 12px;">';
  html += '  <strong style="color:#764ba2;">🎛️ 门控命中（支柱①）：</strong><br>'+gateLog;
  html += '</div>';
  html += '<div style="margin-top:6px;font-size:12px;color:#555;background:#f0fdf4;border-radius:6px;padding:8px 12px;">';
  html += '  <strong style="color:#27ae60;">🎓 校准说明（支柱③）：</strong> 引擎组可靠度加权已生效（训练库逆向校准）；逻辑回归概率映射暂未接入 live（特征空间需重训）。';
  html += '</div>';
  card.innerHTML = html;
}

function renderLiurenHistory(history) {
  const tbody = document.getElementById('liurenHistoryBody');
  if(!history || !history.length) {
    tbody.innerHTML = '<tr><td colspan="7" style="text-align:center;color:#999;">暂无历史</td></tr>';
    return;
  }
  tbody.innerHTML = history.map(h => {
    const bi = h.basic_info || {};
    const kd = (h.analysis && h.analysis.keti_duanyu) || {};
    const sk = kd.sanchuan_kege || {};
    const kegeList = sk.课格列表 || [];
    const kegeStr = kegeList.length > 0 ? kegeList.join('/') : '--';
    return `<tr>
      <td>${h.cycle_start}</td>
      <td>${bi.yuejiang||'--'}</td>
      <td>${h.keti||'--'}</td>
      <td>${(h.san_chuan||[]).join('→')||'--'}</td>
      <td><span style="font-size:10px;color:#2980b9;">${kegeStr}</span></td>
      <td>${h.prediction?normDir(h.prediction.trend):'--'}</td>
      <td>${h.prediction?(h.prediction.confidence+'%'):'--'}</td>
    </tr>`;
  }).join('');
}

// ====== 事件起课（独立体系，与天机分离；2026-08-15） ======
function runHeartbeat(){
  var st = document.getElementById('heartbeatStatus');
  st.textContent = '检测中...';
  fetch(API+'/api/event/heartbeat').then(r=>r.json()).then(d=>{
    st.textContent = d.note || d.error || '完成';
    if(d.event || d.cast){ loadEventBoard(); }
  }).catch(function(e){ st.textContent = '心跳失败'; console.error(e); });
}
function detectEvent(){
  var dateVal = document.getElementById('eventDateInput').value;
  var url = API+'/api/event/detect';
  if(dateVal) url += '?date='+dateVal;
  fetch(url).then(r=>r.json()).then(d=>{
    var box = document.getElementById('eventDetectResult');
    if(!d.success){ box.innerHTML='<div style="color:#dc2626;background:#fee2e2;padding:8px 12px;border-radius:6px;">检测失败: '+(d.error||'')+'</div>'; return; }
    if(!d.data || !d.data.length){ box.innerHTML='<div style="color:#6b7280;background:#f3f4f6;padding:8px 12px;border-radius:6px;">'+ (d.note||'无异动') +'</div>'; return; }
    var ev = d.data[0];
    var lvlMap = {weak:'弱记录',main:'主触发',strong:'强标注'};
    var lvl = lvlMap[ev.level]||ev.level;
    var color = ev.level==='strong' ? '#dc2626' : (ev.level==='main' ? '#d97706' : '#6b7280');
    box.innerHTML = '<div style="padding:10px 14px;border-radius:8px;border:1px solid #ddd6fe;background:#f5f3ff;">'
      + '<strong>'+ev.date+'</strong> '+ev.name+' <span style="color:'+(ev.change_pct>=0?'#dc2626':'#059669')+';font-weight:600;">'+ev.change_pct+'%</span>'
      + ' | 强度 <strong style="color:'+color+'">'+ev.sigma+'σ（'+lvl+'）</strong>'
      + ' | 事件ID: <code>'+ev.event_id+'</code>'
      + (ev.cast_id ? ' | ✅ 已起课 <code>'+ev.cast_id+'</code>' : '')
      + '</div>';
    window._lastEventId = ev.event_id;
  }).catch(function(e){ console.error(e); });
}
function castEvent(){
  var dateVal = document.getElementById('eventDateInput').value;
  var shichen = document.getElementById('eventShichenInput').value;
  if(!dateVal){ alert('请选择事件日期'); return; }
  if(!shichen){ alert('请选择心动时辰'); return; }
  if(!window._lastEventId){ alert('请先点击「🔍 检测事件」'); return; }
  fetch(API+'/api/event/cast',{method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({date:dateVal,shichen:shichen,event_id:window._lastEventId})})
  .then(r=>r.json()).then(d=>{
    var box = document.getElementById('eventCastResult');
    if(!d.success){ box.innerHTML='<div style="color:#dc2626;background:#fee2e2;padding:8px 12px;border-radius:6px;">'+ (d.error||'起课失败') +'</div>'; return; }
    var c = d.cast||{}, p = c.prediction||{};
    box.innerHTML = '<div style="color:#065f46;background:#d1fae5;padding:10px 14px;border-radius:8px;">✅ '+d.message
      +'<br>课体: '+p.keti+' | 三传: '+(p.san_chuan||[]).join('→')+' | 预测: '+p.trend+'（'+p.confidence+'%）</div>';
    loadEventBoard();
  }).catch(function(e){ console.error(e); });
}
function quickCast(eventId, date){
  document.getElementById('eventDateInput').value = date;
  window._lastEventId = eventId;
  detectEvent();
}
function loadEventBoard(){
  Promise.all([
    fetch(API+'/api/event/events?limit=8').then(r=>r.json()),
    fetch(API+'/api/event/evaluate').then(r=>r.json())
  ]).then(function(rs){
    var box = document.getElementById('eventBoard');
    var evD = rs[0]||{}, evlD = rs[1]||{};
    var html = '<div style="font-weight:600;margin-bottom:6px;color:#6d28d9;">📋 事件台账 + 条件基线</div>';
    var bl = evlD.baselines||{};
    var up5 = bl.up&&bl.up['5d'], dn5 = bl.down&&bl.down['5d'];
    html += '<div style="font-size:12px;color:#475569;margin-bottom:8px;">条件基线（动态2σ口径）: 向上事件后5日涨 '
      + (up5!=null?up5+'%':'--') + ' | 向下事件后5日涨 ' + (dn5!=null?dn5+'%':'--') + '</div>';
    var evs = evD.events||[];
    if(evs.length){
      html += '<table style="width:100%;font-size:12px;border-collapse:collapse;"><tr style="background:#ede9fe;"><th style="padding:6px;text-align:left;">日期</th><th style="text-align:left;">涨跌</th><th>σ强度</th><th>级别</th><th>起课</th></tr>';
      evs.forEach(function(e){
        var lvlMap = {weak:'弱',main:'主',strong:'强'};
        var lvl = lvlMap[e.level]||e.level;
        html += '<tr style="border-bottom:1px solid #eee;"><td style="padding:5px;">'+e.date+'</td>'
          +'<td style="color:'+(e.change_pct>=0?'#dc2626':'#059669')+'">'+e.change_pct+'%</td>'
          +'<td>'+e.sigma+'σ</td><td>'+lvl+'</td>'
          +'<td>'+(e.cast_id ? '✅ '+e.cast_id : '<button onclick="quickCast(\''+e.event_id+'\',\''+e.date+'\')" style="padding:2px 8px;border:1px solid #7c3aed;color:#7c3aed;background:#fff;border-radius:4px;cursor:pointer;font-size:11px;">起课</button>')+'</td></tr>';
      });
      html += '</table>';
    } else {
      html += '<div style="color:#94a3b8;">暂无事件记录</div>';
    }
    box.innerHTML = html;
  }).catch(function(e){ console.error(e); });
}

/** 天机起课录入（替代原 runLiurenPrediction） */
function castTianji(e) {
  console.log(">>> 天机起课录入", e);
  const btnArea = document.getElementById('liurenBtnArea');
  btnArea.innerHTML = '<button class="op-btn zeri" disabled style="background:#95a5a6;color:#fff;padding:10px 24px;border-radius:8px;border:none;cursor:not-allowed;font-weight:600;">⏳ 铸课中...</button>';
  const dateVal = document.getElementById('liurenDateInput').value;
  const shichenVal = document.getElementById('liurenShichenInput').value;
  if(!dateVal){ alert('请选择心动日期'); btnArea.innerHTML=_resetCastBtn(); return; }
  if(!shichenVal){ alert('请选择心动时辰'); btnArea.innerHTML=_resetCastBtn(); return; }

  fetch(API + '/api/tianji_cast', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({date: dateVal, shichen: shichenVal}),
  }).then(r=>r.json()).then(d=>{
    if(!d.success){
      btnArea.innerHTML = _resetCastBtn();
      alert('录入失败: '+d.error); return;
    }
    // 录入成功
    _setTianjiCastedState();
    // 显示录入结果消息
    var resArea = document.getElementById('tianjiCastResult');
    resArea.style.display = 'block';
    resArea.style.background = '#d1fae5';
    resArea.style.color = '#065f46';
    resArea.textContent = d.message;
    // 用天机数据填充顶部卡片
    if(d.data){
      var rec = d.data;
      document.getElementById('lStart').textContent = '#' + rec.period_index + ' (' + rec.period_start + '~' + rec.period_end + ')';
      document.getElementById('lKeti').textContent = (rec.tianji_chart||{}).keti || '--';
      document.getElementById('lSanchuan').textContent = ((rec.tianji_chart||{}).sanchuan||[]).join('→') || '--';
      document.getElementById('lTianjiang').textContent = ((rec.tianji_chart||{}).tianjiang||[]).join('→') || '--';
      var trendText = rec.tianji_trend || '--';
      var updown = rec.tianji_updown || '';
      var el = document.getElementById('lTrend');
      el.textContent = trendText;
      el.style.color = updown==='up'?'#ef4444':(updown==='down'?'#22c55e':'#666');
      document.getElementById('lConf').textContent = (rec.tianji_conf||0) + '';
    }
    // 同时触发完整引擎展示（用同一日期+时辰调 /api/liuren_20d 看完整解盘）
    fetch(API + '/api/liuren_20d?date=' + dateVal + '&shichen=' + shichenVal + '&force=1')
      .then(r2=>r2.json()).then(d2=>{
        if(d2.success && d2.data){
          renderLiuren20dPrediction(d2.data);
          // 融合结论区
          var fc = d2.data.fused_judgment;
          if(fc && !fc.error){
            var fcon = document.getElementById('liurenFinalConclusion');
            fcon.style.display = 'block';
            document.getElementById('lFinalVerdict').textContent = fc.trend || '--';
            document.getElementById('lFinalDetail').textContent =
              'P涨='+(fc.prob_up||0).toFixed(3)+' P跌='+(fc.prob_down||0).toFixed(3)+
              ' 置信='+(fc.confidence||0).toFixed(2);
          }
        }
        // 刷新统计
        loadTianjiStats();
      }).catch(()=>{});
  }).catch(err=>{
    btnArea.innerHTML = _resetCastBtn();
    alert('请求失败');
  });
}

function _resetCastBtn(){
  return '<button id="liurenPredictBtn" class="op-btn zeri" onclick="castTianji(event)" style="background:#667eea;color:#fff;padding:10px 24px;border-radius:8px;border:none;cursor:pointer;font-weight:600;">✨ 录入天机起课</button>';
}

function _setTianjiCastedState(){
  var btnArea = document.getElementById('liurenBtnArea');
  btnArea.innerHTML =
    '<button class="op-btn zeri" disabled style="background:#27ae60;color:#fff;padding:10px 20px;border-radius:8px;border:none;cursor:not-allowed;font-weight:600;">✅ 已录入</button>' +
    '<button class="op-btn zeri" onclick="_enableRecast()" style="background:#e67e22;color:#fff;padding:10px 20px;border-radius:8px;border:none;cursor:pointer;font-weight:600;margin-left:8px;">🔄 再录一次</button>';
}

/** 加载六壬预测历史后的按钮状态：当前周期已起课 → 已录入+再录一次；仅历史存在 → 保持录入按钮（横幅会解释） */
function _setLiurenPredictedState(hasCurrent){
  var btnArea = document.getElementById('liurenBtnArea');
  if (!btnArea) return;
  if (hasCurrent) { _setTianjiCastedState(); }
  else { btnArea.innerHTML = _resetCastBtn(); }
}

function _enableRecast(){
  var btnArea = document.getElementById('liurenBtnArea');
  btnArea.innerHTML = _resetCastBtn();
}

/** 加载天机起课统计（心动时辰）— 结构化看板 vs 55.3% 基线 */
function loadTianjiStats(){
  fetch(API + '/api/tianji_stats')
    .then(r=>r.json())
    .then(d=>{
      if(!d.success) return;
      var sb = d.scoreboard || {};
      var area = document.getElementById('tianjiStatsArea');
      var textEl = document.getElementById('tianjiStatsText');
      area.style.display = 'block';

      var nb = (sb.naive_baseline!=null) ? (sb.naive_baseline*100).toFixed(1) : '55.3';
      var nSet = sb.n_settled||0, nUnv = sb.n_unverified||0;
      var acc = (sb.acc_committed!=null && !isNaN(sb.acc_committed)) ? (sb.acc_committed*100).toFixed(1) : '—';
      var ci = sb.ci95||[0,0];
      var pN = (sb.p_vs_naive!=null) ? sb.p_vs_naive : 1;
      var verdict, vColor;
      if(nSet < 5){
        verdict = '样本不足（需≥数十），暂不能下结论'; vColor = '#64748b';
      } else if(pN < 0.05 && parseFloat(acc) > parseFloat(nb)){
        verdict = '✅ 显著高于 '+nb+'% 基线 — 六壬（心动）方向能力成立'; vColor = '#16a34a';
      } else if(pN < 0.05 && parseFloat(acc) < parseFloat(nb)){
        verdict = '⚠️ 显著低于 '+nb+'% 基线'; vColor = '#dc2626';
      } else {
        verdict = '未显著高于 '+nb+'% 基线（p='+pN.toFixed(3)+'）'; vColor = '#f59e0b';
      }

      var html = '';
      html += '<div style="display:flex;gap:10px;flex-wrap:wrap;margin-bottom:8px;">';
      html += statBox('已结算', nSet, '#0f172a');
      html += statBox('待验证', nUnv, '#94a3b8');
      html += statBox('坚定命中率', acc+'%', (parseFloat(acc)>parseFloat(nb))?'#16a34a':'#dc2626');
      html += statBox('95%CI', ci[0].toFixed(1)+'~'+ci[1].toFixed(1)+'%', '#475569');
      html += statBox('p vs '+nb+'%', pN.toFixed(3), pN<0.05?'#16a34a':'#64748b');
      html += '</div>';
      html += '<div style="font-size:13px;font-weight:700;color:'+vColor+';margin:6px 0 10px;">'+verdict+'</div>';

      var samples = sb.samples||[];
      if(samples.length){
        html += '<div style="font-size:12px;color:#64748b;margin-bottom:4px;">样本明细（心动预测 → 实际 / 命中）：</div>';
        html += '<div style="font-size:12px;line-height:1.7;color:#334155;">';
        samples.forEach(function(s){
          var predCn = s.pred==='down'?'看跌':(s.pred==='up'?'看涨':(s.pred||'—'));
          var actCn = s.actual==='down'?'跌':(s.actual==='up'?'涨':(s.actual==null?'待验证':'—'));
          var hitMark = (s.hit===true)?'<span style="color:#16a34a;">✓</span>':((s.hit===false)?'<span style="color:#dc2626;">✗</span>':'<span style="color:#94a3b8;">·</span>');
          html += '· '+s.cast_date+' '+s.shichen+'时：'+predCn+' → '+actCn+' '+hitMark+'<br>';
        });
        html += '</div>';
      }

      if(d.due_period){
        html += '<div style="margin-top:10px;font-size:12px;color:#0c5460;background:#e8f4fd;border:1px solid #bee5eb;border-radius:6px;padding:6px 10px;">🔔 下一个待起课周期：#'+d.due_period.period_index+'（'+d.due_period.period_start+'~'+d.due_period.period_end+'）— 已进入起课窗口，可录入！</div>';
      }
      textEl.innerHTML = html;
    })
    .catch(()=>{});
}
function statBox(label, val, color){
  return '<div style="background:#fff;border:1px solid #e2e8f0;border-radius:8px;padding:8px 12px;min-width:92px;">'+
    '<div style="font-size:10px;color:#94a3b8;margin-bottom:2px;">'+label+'</div>'+
    '<div style="font-size:18px;font-weight:800;color:'+color+';">'+val+'</div></div>';
}

/* ── 天机应期日历提醒（2026-09-08）── */
var _yingqiIcsData = null;
function loadTianjiYingqi(){
  fetch(API + '/api/tianji_yingqi')
    .then(function(r){ return r.json(); })
    .then(function(d){
      var area = document.getElementById('tianjiYingqiArea');
      if(!area) return;
      if(!d || !d.success){
        area.style.display = 'none';
        return;
      }
      var stages = d.stages || [];
      if(!stages.length){
        area.style.display = 'block';
        document.getElementById('tianjiYqEmpty').style.display = 'block';
        document.getElementById('tianjiYqStages').innerHTML = '';
        return;
      }
      area.style.display = 'block';
      document.getElementById('tianjiYqEmpty').style.display = 'none';
      var upDown = (d.updown==='up'?'📈 看涨':(d.updown==='down'?'📉 看跌':'—'));
      document.getElementById('tianjiYqCastTag').textContent =
        '（'+d.cast_date+' '+d.shichen+'时 · '+upDown+' · 课定周期 '+d.period_len+' 交易日）';
      document.getElementById('tianjiYqNarrative').textContent =
        (d.narrative || '') + '  结算窗口：' + (d.period||[]).join(' ~ ');
      var html = '';
      var today = new Date();
      today.setHours(0,0,0,0);
      stages.forEach(function(s, i){
        var ds = s.date_str || '';
        var daysLeft = '—';
        if(ds){
          var dt = new Date(ds+'T00:00:00');
          daysLeft = Math.round((dt - today)/86400000) + ' 天后';
          if(daysLeft.indexOf('-')===0) daysLeft = '已过';
        }
        var color = s.timing==='速' ? '#16a34a' : (s.timing==='中' ? '#b45309' : '#92400e');
        var wk = '';
        if(ds){ var w = ['日','一','二','三','四','五','六'][new Date(ds+'T00:00:00').getDay()]; wk = ' 周'+w; }
        html += '<div style="display:flex;align-items:center;gap:10px;background:#fff;border:1px solid #f5d9a8;border-left:4px solid '+color+';border-radius:8px;padding:8px 12px;">'+
          '<span style="font-size:14px;font-weight:800;color:'+color+';min-width:88px;">'+s.trigger_gz+' 日</span>'+
          '<span style="color:#92400e;font-weight:600;min-width:44px;">'+s.timing+'</span>'+
          '<span style="color:#444;font-size:12px;flex:1;">'+s.method+'</span>'+
          '<span style="color:#7c2d12;font-size:12px;font-weight:600;">'+(ds?ds+wk:'未现')+'</span>'+
          '<span style="color:#a16207;font-size:11px;min-width:52px;text-align:right;">'+daysLeft+'</span>'+
          '</div>';
      });
      document.getElementById('tianjiYqStages').innerHTML = html;
      // 【2026-09-09 接入展示】毕法赋命中/凶象语义提示（源 /api/tianji_yingqi.bifa_hits）
      var bfEl = document.getElementById('tianjiYqBifa');
      var bfHits = d.bifa_hits || [];
      if (bfEl && bfHits.length) {
        var xiongMap = {
          '支坟财并旅程稽': '凶象：支墓作财入传，主行情滞涨/商贩折本/进程受阻——兑现有迟延',
          '制鬼之位乃良医': '中平：三传有制鬼之神，逢凶有解',
          '喜惧空亡乃妙机': '警示：传中见空亡，吉凶减半、须待填实/冲空应期',
          '旬内空亡逐类推': '警示：空亡入传按类应（财空/鬼空/生空），应期后移',
          '妄用三传灾福异': '警示：传中多自刑涉克比，涉害择比须慎用，勿执一法',
        };
        var parts = [];
        bfHits.forEach(function(h){
          var hint = xiongMap[h] || '';
          var color = (hint.indexOf('凶象') === 0) ? '#b91c1c' : '#92400e';
          parts.push('<div><span style="font-weight:700;color:'+color+';">毕法·'+h+'</span>'+
            (hint ? ' <span style="color:#78350f;">'+hint.replace(/^[^：]*：/,'')+'</span>' : '')+'</div>');
        });
        bfEl.innerHTML = '<div style="font-weight:700;color:#92400e;margin-bottom:4px;">📜 毕法赋课理提示（'+bfHits.length+'条命中）</div>' + parts.join('');
        bfEl.style.display = 'block';
      } else if (bfEl) {
        bfEl.style.display = 'none';
      }
      _yingqiIcsData = d;
    })
    .catch(function(){});
}
function exportYingqiIcs(){
  if(!_yingqiIcsData) return;
  var d = _yingqiIcsData;
  var lines = ['BEGIN:VCALENDAR','VERSION:2.0','PRODID:-//yidu-liuren//tianji-yingqi//CN','BEGIN:VEVENT',
    'UID:yidu-tianji-'+d.cast_date+'-'+Date.now(),
    'SUMMARY:天机应期('+(d.updown==='up'?'看涨':'看跌')+')-'+d.cast_date,
    'DESCRIPTION:'+(d.narrative||'').replace(/[;,]/g,'\\$&'),
    'DTSTART;VALUE=DATE:'+d.cast_date.replace(/-/g,''),
    'DTEND;VALUE=DATE:'+((d.period||[])[1]||d.cast_date).replace(/-/g,''),
    'END:VEVENT'];
  (d.stages||[]).forEach(function(s, i){
    if(!s.date_str) return;
    lines.push('BEGIN:VEVENT');
    lines.push('UID:yidu-tianji-'+d.cast_date+'-stage-'+i);
    lines.push('SUMMARY:应期['+s.timing+']'+s.trigger_gz+'日('+s.method+')');
    lines.push('DESCRIPTION:'+('约'+s.days+'日 · '+s.method).replace(/[;,]/g,'\\$&'));
    lines.push('DTSTART;VALUE=DATE:'+s.date_str.replace(/-/g,''));
    lines.push('DTEND;VALUE=DATE:'+s.date_str.replace(/-/g,''));
    lines.push('END:VEVENT');
  });
  lines.push('END:VCALENDAR');
  var blob = new Blob([lines.join('\r\n')], {type:'text/calendar;charset=utf-8'});
  var a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = 'tianji_yingqi_'+d.cast_date+'.ics';
  document.body.appendChild(a); a.click(); document.body.removeChild(a);
}

// ====== 六壬精选审核功能 ======
var _reviewTaskId = null;
var _reviewData = null;

function loadReviewStatusOnTabSwitch() {
  if (_reviewTaskId) {
    fetch(API + '/api/liuren_review/status?task_id=' + _reviewTaskId)
      .then(function(r) { return r.json(); })
      .then(function(d) {
        if (d.success && d.has_task && d.task) {
          _reviewData = d.task;
          showReviewResult(d.task);
        }
      })
      .catch(function() {});
  }
}

async function startLiurenReview() {
  var shichen = document.getElementById('reviewShichen').value;
  var source = document.getElementById('reviewSource').value;
  var timeoutHours = parseInt(document.getElementById('reviewTimeout').value) || 48;

  // 获取待审核股票列表（按「选股来源」选择：量化TOP10 / 量化TOP15 / 双阶段精选池）
  var toItem = function(r) {
    return { code: r.code || r.symbol, name: r.name || '', score: r.screener_score || r.score || 0 };
  };
  var sTop = (_screenerResults && _screenerResults.length) ? _screenerResults : [];
  var stocks = [];
  if (source === 'screener_top10' && sTop.length) {
    stocks = sTop.slice(0, 10).map(toItem);
  } else if (source === 'screener_top15' && sTop.length) {
    stocks = sTop.slice(0, 15).map(toItem);
  } else if (_dualPhaseVerified && _dualPhaseVerified.length > 0) {
    stocks = _dualPhaseVerified.map(toItem);
  } else if (sTop.length) {
    stocks = sTop.slice(0, 10).map(toItem);
  }

  if (stocks.length === 0) {
    alert('暂无可审核的股票，请先运行量化选股');
    return;
  }

  var rizhu = (_dualPhaseMeta && _dualPhaseMeta.rizhu) ? _dualPhaseMeta.rizhu : '';

  var badge = document.getElementById('liurenReviewBadge');
  badge.textContent = '起课中...';
  badge.style.background = '#f59e0b';

  try {
    var r = await fetch(API + '/api/liuren_review/start', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ stocks: stocks, shichen: shichen, rizhu: rizhu, source: source, timeout_hours: timeoutHours })
    });
    var d = await r.json();

    if (!d.success) {
      alert('起课失败: ' + d.error);
      badge.textContent = '待起课';
      badge.style.background = '#7c3aed';
      return;
    }

    _reviewTaskId = d.task_id;
    _reviewData = d.task;
    showReviewResult(d.task);

    badge.textContent = '审核中';
    badge.style.background = '#16a34a';
  } catch (err) {
    alert('请求失败: ' + err);
    badge.textContent = '待起课';
    badge.style.background = '#7c3aed';
  }
}

function showReviewResult(task) {
  document.getElementById('reviewResultArea').style.display = 'block';

  var paipanInfo = document.getElementById('reviewPaipanInfo');
  var taskIdShort = (task.task_id || '');
  if (taskIdShort.length > 8) taskIdShort = taskIdShort.substring(0, 8);
  paipanInfo.textContent =
    '日柱: ' + (task.rizhu || '--') + ' | 占时: ' + (task.shichen || '--') + ' | 任务: ' + taskIdShort;

  var statusBadge = document.getElementById('reviewStatusBadge');
  if (task.status === 'reviewed') {
    statusBadge.textContent = '已完成';
    statusBadge.style.background = '#16a34a';
    statusBadge.style.color = '#fff';
  } else if (task.status === 'skipped') {
    statusBadge.textContent = '已跳过';
    statusBadge.style.background = '#9ca3af';
    statusBadge.style.color = '#fff';
  } else {
    statusBadge.textContent = '审核中';
    statusBadge.style.background = '#f59e0b';
    statusBadge.style.color = '#fff';
  }

  if (task.expires_at) {
    startReviewCountdown(task.expires_at);
  }

  renderReviewTable(task);
}

var _reviewCountdownTimer = null;
function startReviewCountdown(expiresAt) {
  var countdownEl = document.getElementById('reviewCountdown');
  function update() {
    var now = new Date();
    var expires = new Date(expiresAt);
    var diff = expires - now;
    if (diff <= 0) {
      countdownEl.textContent = '已超时';
      if (_reviewCountdownTimer) { clearInterval(_reviewCountdownTimer); _reviewCountdownTimer = null; }
      return;
    }
    var hours = Math.floor(diff / 3600000);
    var minutes = Math.floor((diff % 3600000) / 60000);
    countdownEl.textContent = hours + '时' + minutes + '分';
  }
  update();
  if (_reviewCountdownTimer) clearInterval(_reviewCountdownTimer);
  _reviewCountdownTimer = setInterval(update, 60000);
}

function renderReviewTable(task) {
  var tbody = document.getElementById('reviewTableBody');
  var predictions = task.predictions || task.stocks || [];

  if (predictions.length === 0) {
    tbody.innerHTML = '<tr><td colspan="10" style="text-align:center;color:#999;padding:20px;">暂无审核数据</td></tr>';
    return;
  }

  var isReadOnly = task.status === 'reviewed' || task.status === 'skipped';

  tbody.innerHTML = predictions.map(function(p, i) {
    var aiTrend = p.ai_trend || p.trend || '--';
    var aiJixiong = p.ai_jixiong || p.jixiong || '--';
    var aiConf = p.ai_confidence != null ? (p.ai_confidence * 100).toFixed(0) + '%' : '--';
    var humanTrend = p.human_trend || aiTrend;
    var humanJixiong = p.human_jixiong || aiJixiong;
    var note = (p.review_note || '').replace(/"/g, '&quot;');

    var disabled = isReadOnly ? ' disabled' : '';

    return '<tr>' +
      '<td>' + (i + 1) + '</td>' +
      '<td>' + (p.code || '') + '</td>' +
      '<td>' + (p.name || '') + '</td>' +
      '<td style="background:#fef3c7;">' + aiTrend + '</td>' +
      '<td style="background:#fef3c7;">' + aiJixiong + '</td>' +
      '<td style="background:#fef3c7;">' + aiConf + '</td>' +
      '<td style="background:#ede9fe;">' +
        '<select class="review-human-trend" data-index="' + i + '" style="padding:4px 6px;border:1px solid #c4b5fd;border-radius:4px;font-size:12px;"' + disabled + '>' +
          '<option value="看涨"' + (humanTrend === '看涨' ? ' selected' : '') + '>看涨</option>' +
          '<option value="看跌"' + (humanTrend === '看跌' ? ' selected' : '') + '>看跌</option>' +
          '<option value="震荡"' + (humanTrend === '震荡' ? ' selected' : '') + '>震荡</option>' +
        '</select>' +
      '</td>' +
      '<td style="background:#ede9fe;">' +
        '<select class="review-human-jixiong" data-index="' + i + '" style="padding:4px 6px;border:1px solid #c4b5fd;border-radius:4px;font-size:12px;"' + disabled + '>' +
          '<option value="吉"' + (humanJixiong === '吉' ? ' selected' : '') + '>吉</option>' +
          '<option value="凶"' + (humanJixiong === '凶' ? ' selected' : '') + '>凶</option>' +
          '<option value="平"' + (humanJixiong === '平' ? ' selected' : '') + '>平</option>' +
        '</select>' +
      '</td>' +
      '<td style="background:#ede9fe;">' +
        '<input class="review-note" data-index="' + i + '" value="' + note + '" style="width:120px;padding:4px 6px;border:1px solid #c4b5fd;border-radius:4px;font-size:12px;" placeholder="备注"' + disabled + '>' +
      '</td>' +
      '<td>' + (isReadOnly ? '<span style="color:#999;font-size:11px;">已完成</span>' :
        '<button onclick="confirmReviewRow(' + i + ')" style="background:#16a34a;color:#fff;border:none;padding:3px 8px;border-radius:3px;cursor:pointer;font-size:11px;margin-right:3px;">确认</button>' +
        '<button onclick="flipReviewRow(' + i + ')" style="background:#dc2626;color:#fff;border:none;padding:3px 8px;border-radius:3px;cursor:pointer;font-size:11px;">翻转</button>') +
      '</td>' +
    '</tr>';
  }).join('');
}

function confirmReviewRow(index) {
  var sel = document.querySelector('.review-human-trend[data-index="' + index + '"]');
  var selJx = document.querySelector('.review-human-jixiong[data-index="' + index + '"]');
  if (!sel) return;
  var row = sel.closest('tr');
  var tds = row.querySelectorAll('td');
  sel.value = tds[3].textContent.trim();
  if (selJx) selJx.value = tds[4].textContent.trim();
}

function flipReviewRow(index) {
  var sel = document.querySelector('.review-human-trend[data-index="' + index + '"]');
  if (!sel) return;
  if (sel.value === '看涨') sel.value = '看跌';
  else if (sel.value === '看跌') sel.value = '看涨';
  else sel.value = '看涨';
}

function batchConfirmAll() {
  document.querySelectorAll('.review-human-trend').forEach(function(sel) {
    var row = sel.closest('tr');
    var tds = row.querySelectorAll('td');
    sel.value = tds[3].textContent.trim();
  });
  document.querySelectorAll('.review-human-jixiong').forEach(function(sel) {
    var row = sel.closest('tr');
    var tds = row.querySelectorAll('td');
    sel.value = tds[4].textContent.trim();
  });
}

function batchFlipAll() {
  document.querySelectorAll('.review-human-trend').forEach(function(sel) {
    if (sel.value === '看涨') sel.value = '看跌';
    else if (sel.value === '看跌') sel.value = '看涨';
  });
}

function resetAllToAI() {
  batchConfirmAll();
}

async function saveReview() {
  if (!_reviewTaskId) { alert('没有进行中的审核任务'); return; }

  var trendSels = document.querySelectorAll('.review-human-trend');
  var jxSels = document.querySelectorAll('.review-human-jixiong');
  var noteInputs = document.querySelectorAll('.review-note');

  var reviews = [];
  var predictions = _reviewData ? (_reviewData.predictions || _reviewData.stocks || []) : [];

  trendSels.forEach(function(sel, i) {
    var pred = predictions[i] || {};
    reviews.push({
      code: pred.code || '',
      human_trend: sel.value,
      human_jixiong: jxSels[i] ? jxSels[i].value : '--',
      review_note: noteInputs[i] ? noteInputs[i].value : ''
    });
  });

  try {
    var r = await fetch(API + '/api/liuren_review/save', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ task_id: _reviewTaskId, reviews: reviews, reviewer: 'user' })
    });
    var d = await r.json();

    if (d.success) {
      alert('审核已保存！结果已存入训练库。');
      var badge = document.getElementById('reviewStatusBadge');
      badge.textContent = '已完成';
      badge.style.background = '#16a34a';
      badge.style.color = '#fff';
      document.querySelectorAll('.review-human-trend, .review-human-jixiong, .review-note').forEach(function(el) {
        el.disabled = true;
      });
    } else {
      alert('保存失败: ' + d.error);
    }
  } catch (err) {
    alert('请求失败: ' + err);
  }
}

async function skipReview() {
  if (!_reviewTaskId) { alert('没有进行中的审核任务'); return; }
  if (!confirm('确定跳过六壬精选审核？超时后将自动采用AI判断。')) return;

  try {
    var r = await fetch(API + '/api/liuren_review/skip', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ task_id: _reviewTaskId, reason: '用户手动跳过' })
    });
    var d = await r.json();

    if (d.success) {
      alert('已跳过六壬精选');
      document.getElementById('reviewResultArea').style.display = 'none';
      document.getElementById('liurenReviewBadge').textContent = '已跳过';
      document.getElementById('liurenReviewBadge').style.background = '#9ca3af';
      _reviewTaskId = null;
      _reviewData = null;
    } else {
      alert('操作失败: ' + d.error);
    }
  } catch (err) {
    alert('请求失败: ' + err);
  }
}

