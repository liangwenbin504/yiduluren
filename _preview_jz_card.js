// 救神具象化卡「真实渲染」预览：抽出 verdictCard 实渲染 → 写 HTML（页面真底色 #2a2a4a）
// 供 chromium 截图做 UI 核对。用法：node _preview_jz_card.js
const fs = require('fs');
const path = require('path');

const HTML = path.join(__dirname, 'stock_dashboard.html');
const lines = fs.readFileSync(HTML, 'utf8').split(/\r?\n/);
function findLine(re, from = 0) {
  for (let i = from; i < lines.length; i++) if (re.test(lines[i])) return i + 1;
  return -1;
}
function slice(a, b) { return lines.slice(a - 1, b).join('\n'); }

const lYr = findLine(/^function _yrCol\s*\(/);
const lYrEnd = findLine(/^\}/, lYr);
const lVT = findLine(/^var V_TAIL_COL\s*=/);
const lVC = findLine(/^function verdictCard\s*\(/);
const lVCEnd = findLine(/^function plRenderDetail\s*\(/);
if ([lYr, lYrEnd, lVT, lVC, lVCEnd].some(x => x < 0)) { console.error('定位失败'); process.exit(2); }

const stubs = `
var ZERI_SECT = {
  '六壬': {color:'#a5b4fc', role:'主旨', tip:'', weight:''},
  '斗首': {color:'#e0b36a', role:'基础', tip:'', weight:''},
  '演禽': {color:'#7ee2b8', role:'支节', tip:'', weight:''}
};
function plSectChip(n, s) {
  var c = (ZERI_SECT[n]||{}).color || '#cbd5e1';
  return '<span style="font-size:12px;font-weight:700;color:'+c+';border:1px solid '+c+'66;border-radius:6px;padding:1px 6px;margin-right:4px;">'+n+' '+s+'</span>';
}
`;
const code = stubs + '\n' + slice(lYr, lYrEnd) + '\n' + slice(lVT, lVT) + '\n' + slice(lVC, lVCEnd - 1) +
  '\nmodule.exports = { verdictCard };\n';
const tmp = path.join(__dirname, '_tmp_jz_prev.js');
fs.writeFileSync(tmp, code, 'utf8');
const M = require(tmp);
fs.unlinkSync(tmp);

// 真实探针数据（2026-10-24 戌·婚嫁·卯山·本命癸亥 男 11 → 行年丑）
const d = { zonghe_piyu: { detail: {
  verdict: {
    rows: [{ name: '六壬', side: '吉', score: 100.0, grade: '上上吉' },
           { name: '斗首', side: '中', score: null, grade: '' },
           { name: '演禽', side: '中', score: null, grade: '' }],
    tail: '以六壬（主旨）为准，六壬得吉，斗首、演禽为中平 —— 偏吉可用（次看基础与旁证）',
    tail_level: 'lean_ok', warns: [], rule: ''
  },
  verdict_layered: {
    overall: { side: '吉', scope: '长期大局', basis: '课体·三传（六壬吉，斗首中，演禽中）' },
    benming: { side: '凶', scope: '终身', basis: '本命上神辰乘太阴', n: 1 },
    xingnian: { side: '吉', scope: '当年(仅)', basis: '行年上神午乘太常', n: 1 },
    summary: '整体吉、本命凶（终身）、行年吉（仅当年）。　—— 长期吉，唯终身基调有碍，宜徐徐图之。',
    rule: '分层判据：《通解》下「三传为大运，逐年视行年」…⛔ 局部不翻整体。'
  },
  jiuzhu: {
    yue_jian: '戌', jieshen: '辰', effective: true,
    note: '救神：午（天医） → 乘太常（祭祀神、酒食、父母、衣冠） → 阴神亥·乘六合',
    rule: '①取救神（解神＝月建之冲；子孙；日德；吉将；生气；天医），须落七处且不空亡才「能用」；'
        + '②看乘何将定人事（鬼乘天乙乃神祇／天后→长辈／太常·白虎→祭祀／天空→佛位）；'
        + '③再看【阴神】＝该支天盘上神，定更精细处所（午为离明·明堂→家堂神；丑为明堂；未主祭祀；寅申为寺观）；'
        + '④出化解之法。出处：通解_下 L13210、通解_上 L2498、通解_中 L6157/6158、通解_上 L3868、通解_上 L6169/6203。'
        + '⛔ 本层纯叙事，不进评分链。',
    items: [
      { zhi: '午', name: '天医', via: '七处', kong: false, wangshuai: '休', gui: true,
        chain: '午（天医） → 乘太常（祭祀神、酒食、父母、衣冠） → 阴神亥·乘六合',
        advice: ['祭祷、祀先（太常本祭祀神）', '延医服药（子孙/天医为药，子为杀鬼之神）'],
        src: '通解_下 L13210 注⑧（另有《断案疏正》前二辰一说）' },
      { zhi: '巳', name: '日德', via: '七处', kong: false, wangshuai: '休', gui: true,
        chain: '巳（日德） → 乘玄武（盗贼、暗昧、水祟） → 阴神戌·乘勾陈',
        advice: ['何人／何事：盗贼、暗昧、水祟'],
        src: '通解_上 L1001「贵德临身制鬼者反吉」' },
      { zhi: '辰', name: '解神', via: '七处', kong: false, wangshuai: '旺', gui: false,
        chain: '辰（解神） → 乘太阴（阴神、阴私、暗昧之神） → 阴神酉·乘青龙',
        advice: ['敬祀鬼神（阴神主神祇星宿）'],
        src: '通解_下 L13210 注⑦「用神被月建冲破谓之解神，又名四时空亡」' },
      { zhi: '申', name: '生气', via: '七处', kong: false, wangshuai: '相', gui: false,
        chain: '申（生气） → 乘天空（佛位、虚诈、奴仆） → 阴神丑（明堂（勾陈主明堂））·乘螣蛇',
        advice: ['修斋设醮 · 评佛位（天空作官评佛位）', '何处／何物：明堂（勾陈主明堂） → 公门、朝堂、封功决罪之事'],
        src: '通解_下 L13210 注⑫' },
      { zhi: '子', name: '地医', via: '七处', kong: false, wangshuai: '死', gui: false,
        chain: '子（地医） → 乘朱雀（文书、口舌、词讼） → 阴神巳（祭祀（日德生气））·乘玄武',
        advice: ['宜托人求贵暗祷', '延医服药（子孙/天医为药，子为杀鬼之神）',
                 '何处／何物：祭祀（日德生气） → 祭祀、禳谢之属'],
        src: '通解_下 L13210 注⑧' },
      { zhi: '卯', name: '吉将(天后)', via: '七处', kong: false, wangshuai: '囚', gui: false,
        chain: '卯（吉将(天后)） → 乘天后（后妃、老妇、翁婆、母、僧尼、私祷） → 阴神申（寺观（空中神祇））·乘天空',
        advice: ['敬重长辈（母/老妇/翁婆），或托僧尼私祷',
                 '何处／何物：寺观（空中神祇） → 寺观、虚无空中之神祇'],
        src: '通解_上 L5351「龙、常、阴、后、六合吉将…得一在末传，可化凶为吉」' }
    ]
  },
  yingren: {
    ji: [{ who: '行年丑之人', what: '行年上神午乘太常', note: '乘轩，有改拜之恩（无气：虚/迟/小）',
           src: '行年上神', side: '吉', ren: '行年', scope: '当年(仅)', wangshuai: '无气' }],
    xiong: [{ who: '本命亥之人', what: '本命上神辰乘太阴', note: '遭淫，被乖争勾连争讼',
              src: '本命上神', side: '凶', ren: '本命', scope: '终身', wangshuai: '有气' }],
    ref: [], note: '本课吉凶并见 —— 吉应落在上列之人／事，凶应亦落在上列之人／事。'
  }
} } };

const card = M.verdictCard(d);
const doc = '<!DOCTYPE html><html lang="zh-CN"><head><meta charset="utf-8">'
  + '<style>body{font-family:-apple-system,"Microsoft YaHei",sans-serif;background:#2a2a4a;margin:0;padding:14px;}'
  + 'summary{list-style:none;} summary::-webkit-details-marker{display:none;}</style></head><body>'
  + card + '</body></html>';
const out = path.join(__dirname, '_memory', '_jz_card_preview.html');
fs.writeFileSync(out, doc, 'utf8');
console.log('[written] ' + out + '  (' + doc.length + ' bytes)');
