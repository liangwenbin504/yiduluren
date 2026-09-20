// v4 前端渲染自测：从 stock_dashboard.html 抽出 _yrCol / verdictCard 实渲染，
// 用真实探针数据断言「三行分层卡 + scope/旺衰标签」确实出现在 HTML 里。
// 用法：node _test_v4_card.js
const fs = require('fs');
const path = require('path');

const HTML = path.join(__dirname, 'stock_dashboard.html');
const lines = fs.readFileSync(HTML, 'utf8').split(/\r?\n/);

function findLine(re, from = 0) {
  for (let i = from; i < lines.length; i++) {
    if (re.test(lines[i])) return i + 1; // 1-based
  }
  return -1;
}
function slice(a, b) { return lines.slice(a - 1, b).join('\n'); }

const lYr = findLine(/^function _yrCol\s*\(/);
const lYrEnd = findLine(/^\}/, lYr) ;
const lVT = findLine(/^var V_TAIL_COL\s*=/);
const lVC = findLine(/^function verdictCard\s*\(/);
const lVCEnd = findLine(/^function plRenderDetail\s*\(/);
if ([lYr, lYrEnd, lVT, lVC, lVCEnd].some(x => x < 0)) {
  console.error('定位失败', { lYr, lYrEnd, lVT, lVC, lVCEnd });
  process.exit(2);
}

const stubs = `
var ZERI_SECT = {
  '六壬': {color:'#a5b4fc', role:'主旨', tip:'tip', weight:'w'},
  '斗首': {color:'#e0b36a', role:'基础', tip:'tip', weight:'w'},
  '演禽': {color:'#7ee2b8', role:'支节', tip:'tip', weight:'w'}
};
function plSectChip(n, s) { return '[CHIP:' + n + '=' + s + ']'; }
`;
const code = stubs + '\n' + slice(lYr, lYrEnd) + '\n' + slice(lVT, lVT) + '\n' + slice(lVC, lVCEnd - 1) +
  '\nmodule.exports = { verdictCard: verdictCard, _yrCol: _yrCol };\n';
const tmp = path.join(__dirname, '_tmp_v4_card_mod.js');
fs.writeFileSync(tmp, code, 'utf8');
const M = require(tmp);
fs.unlinkSync(tmp);

// ── 真实探针数据（2026-10-24 戌·婚嫁·卯山，本命癸亥 男 11 → 行年丑）──
const d = {
  zonghe_piyu: {
    detail: {
      verdict: {
        rows: [{ name: '六壬', side: '吉', score: 100.0, grade: '上上吉' },
               { name: '斗首', side: '中', score: null, grade: '' },
               { name: '演禽', side: '中', score: null, grade: '' }],
        tail: '以六壬（主旨）为准，六壬得吉，斗首、演禽为中平 —— 偏吉可用（次看基础与旁证）',
        tail_level: 'lean_ok', warns: [], rule: '判据…'
      },
      verdict_layered: {
        overall: { side: '吉', scope: '长期大局', basis: '课体·三传（六壬吉，斗首中，演禽中）' },
        benming: { side: '凶', scope: '终身', basis: '本命上神辰乘太阴', n: 1 },
        xingnian: { side: '吉', scope: '当年(仅)', basis: '行年上神午乘太常', n: 1 },
        summary: '整体吉、本命凶（终身）、行年吉（仅当年）。　—— 长期吉，唯终身基调有碍，宜徐徐图之。',
        rule: '分层判据：《通解》下「三传为大运，逐年视行年」…⛔ 局部不翻整体。'
      },
      yingren: {
        ji: [{ who: '行年丑之人', what: '行年上神午乘太常', note: '乘轩，有改拜之恩（无气：虚/迟/小）',
               src: '行年上神', side: '吉', ren: '行年', scope: '当年(仅)', wangshuai: '无气' },
             { who: '巳命人', what: '马神巳发传，发福应于巳年', note: '', src: '禄马发传',
               side: '吉', ren: '', scope: '长期大局', wangshuai: '' }],
        xiong: [{ who: '本命亥之人', what: '本命上神辰乘太阴', note: '遭淫，被乖争勾连争讼',
                  src: '本命上神', side: '凶', ren: '本命', scope: '终身', wangshuai: '有气' }],
        ref: [],
        note: '本课吉凶并见 —— 吉应落在上列之人／事，凶应亦落在上列之人／事…'
      },
      jiuzhu: {
        yue_jian: '戌', jieshen: '辰', effective: true,
        note: '救神：午（天医） → 乘太常（祭祀神、酒食、父母、衣冠） → 阴神亥·乘六合',
        rule: '①取救神（解神＝月建之冲；子孙；日德；吉将；生气；天医）…⛔ 本层纯叙事，不进评分链。',
        items: [
          { zhi: '午', name: '天医', via: '七处', kong: false, wangshuai: '休', gui: true,
            chain: '午（天医） → 乘太常（祭祀神、酒食、父母、衣冠） → 阴神亥·乘六合',
            advice: ['祭祷、祀先（太常本祭祀神）', '延医服药（子孙/天医为药，子为杀鬼之神）'],
            src: '通解_下 L13210 注⑧' },
          { zhi: '辰', name: '解神', via: '七处', kong: false, wangshuai: '旺', gui: false,
            chain: '辰（解神） → 乘太阴（阴神、阴私、暗昧之神） → 阴神酉·乘青龙',
            advice: ['敬祀鬼神（阴神主神祇星宿）'],
            src: '通解_下 L13210 注⑦「用神被月建冲破谓之解神」' },
          { zhi: '申', name: '生气', via: '七处', kong: false, wangshuai: '相', gui: false,
            chain: '申（生气） → 乘天空（佛位、虚诈、奴仆） → 阴神丑（明堂（勾陈主明堂））·乘螣蛇',
            advice: ['修斋设醮 · 评佛位（天空作官评佛位）',
                     '何处／何物：明堂（勾陈主明堂） → 公门、朝堂、封功决罪之事'],
            src: '通解_下 L13210 注⑫' }
        ]
      }
    }
  }
};

const h = M.verdictCard(d);
const checks = [
  ['总体·大局行', '总体 · 大局'],
  ['本命·终身行', '本命 · 终身'],
  ['行年·当年行', '行年 · 当年'],
  ['overall side chip', '[CHIP:六壬=吉]'],
  ['scope 长期大局', '长期大局'],
  ['scope 终身', '>终身<'],
  ['scope 当年(仅)', '当年(仅)'],
  ['basis 课体·三传', '课体·三传'],
  ['summary 全句', '长期吉，唯终身基调有碍，宜徐徐图之。'],
  ['规则折叠', '分层判据与原文出处'],
  ['吉应栏', '✅ 吉应 · 何人之何事'],
  ['凶应栏', '❌ 凶应 · 何人之何事'],
  ['entry scope chip(吉)', '行年上神午乘太常'],
  ['entry 旺衰 无气', '>无气<'],
  ['entry 旺衰 有气', '>有气<'],
  ['note 无气缀语', '（无气：虚/迟/小）'],
  // ── 救神具象化（后端 detail.jiuzhu）──
  ['救神段标题', '救神具象化 · 谁能解／如何解'],
  ['月建·解神回填', '月建戌'],
  ['救神 chain①（天医·太常）', '午（天医） → 乘太常'],
  ['救神 chain②（解神·太阴·阴神）', '辰（解神） → 乘太阴'],
  ['救神 chain③（阴神宫位·明堂）', '阴神丑（明堂'],
  ['救神 advice 祭祷祀先', '祭祷、祀先（太常本祭祀神）'],
  ['救神 advice 敬祀鬼神', '敬祀鬼神（阴神主神祇星宿）'],
  ['救神 advice 何处／何物', '何处／何物：明堂（勾陈主明堂）'],
  ['救神 via chip（七处）', '>七处<'],
  ['救神 鬼爻 chip', '>鬼爻<'],
  ['救神 旺衰 chip', '>休<'],
  ['救神 note', '救神：午（天医）'],
  ['救神判据折叠', '救神取用判据与原文出处']
];
let bad = 0;
console.log('verdictCard HTML 长度 =', h.length);
for (const [name, needle] of checks) {
  const ok = h.indexOf(needle) >= 0;
  if (!ok) bad++;
  console.log((ok ? '  ✅ ' : '  ❌ ') + name + '  ← "' + needle + '"');
}
// §8.3② 前端侧守卫：overall 吉时不得渲染出「整体凶」字样
if (h.indexOf('整体凶') >= 0) { bad++; console.log('  ❌ 出现「整体凶」字样'); }
else { console.log('  ✅ 未出现「整体凶」字样'); }

// 分层块应出现在吉应栏之前（顺序＝认知路径：总体 → 终身 → 当年 → 明细）
const iOv = h.indexOf('总体 · 大局'), iJi = h.indexOf('✅ 吉应');
if (iOv >= 0 && iJi >= 0 && iOv < iJi) console.log('  ✅ 分层块位于吉应/凶应栏之前（顺序正确）');
else { bad++; console.log('  ❌ 分层块顺序错误'); }

// 救神块顺序：分层块之后 → 吉应栏之前
const iJz = h.indexOf('救神具象化 · 谁能解');
if (iJz >= 0 && iJz > iOv && iJz < iJi) console.log('  ✅ 救神块位于「分层块之后、吉应栏之前」（顺序正确）');
else { bad++; console.log('  ❌ 救神块顺序错误 iJz=' + iJz + ' iOv=' + iOv + ' iJi=' + iJi); }

// 救神条目上限 3 条（前端 slice(0,3)）——第 4 条不得渲染
if (h.indexOf('子（地医）') < 0) console.log('  ✅ 救神条目按上限渲染（未越界）');
else { bad++; console.log('  ❌ 救神条目越界渲染'); }

// 救神 >3 条 ⇒ 其余折叠进 details
const d2 = JSON.parse(JSON.stringify(d));
d2.zonghe_piyu.detail.jiuzhu.items.push(
  { zhi: '子', name: '地医', via: '七处', kong: false, wangshuai: '死', gui: false,
    chain: '子（地医） → 乘朱雀 → 阴神巳', advice: ['延医服药'], src: '通解_下 L13210 注⑧' },
  { zhi: '卯', name: '吉将(天后)', via: '七处', kong: false, wangshuai: '囚', gui: false,
    chain: '卯（吉将(天后)） → 乘天后', advice: ['敬重长辈'], src: '通解_上 L5351' });
const h2 = M.verdictCard(d2);
if (h2.indexOf('其余救神（2 条）') >= 0 && h2.indexOf('子（地医）') >= 0)
  console.log('  ✅ 救神 >3 条 → 其余折叠（2 条）');
else { bad++; console.log('  ❌ 救神折叠失败'); }

console.log('\n' + (bad === 0 ? 'PASS（0 失败 / ' + (checks.length + 5) + ' 项）' : 'FAIL（' + bad + ' 项）'));
process.exit(bad === 0 ? 0 : 1);
