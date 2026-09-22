# -*- coding: utf-8 -*-
"""单课择日文书导出（套用「完美模板.docx」）。

模板是一份横向、书法字体（李白赋诗游龙惊鸿）、含印章图的正式课格文书，
占位符如下（均在单个 run 内，可 run 级替换）：
    {{标题}} {{仙命}} {{山向}} {{来龙}} {{四柱}}
    {{六壬课格}} {{批语}} {{避忌}} {{地理师}} {{日期}}
另有文字占位「[印章]」需清除（真实印章图在「日期」段落内联，不动它）。

本模块无 Flask 依赖，便于独立单测；端点 stock_dashboard.py:/api/export/wenshu 调用 build_wenshu()。
"""
import io
import os
from datetime import datetime

TPL_NAME = '完美模板.docx'

# 模板占位符 → 兜底默认值（data 未提供时用）
_FALLBACK = {
    '{{标题}}': '仪度六壬择日课单',
    '{{仙命}}': '待定',
    '{{山向}}': '待定',
    '{{来龙}}': '待定',
    '{{四柱}}': '待定',
    '{{六壬课格}}': '待定',
    '{{批语}}': '课格平和，无大凶之象，可斟酌使用。',
    '{{避忌}}': '无重大避忌',
    '{{地理师}}': '仪度六壬',
    '{{日期}}': '',  # 动态填当前日期
}


def default_tpl_path():
    """模板在项目根目录（engine/ 的上一级）。"""
    here = os.path.dirname(os.path.abspath(__file__))  # engine/
    root = os.path.dirname(here)
    return os.path.join(root, TPL_NAME)


# ── 中文数字日期（落款"岁次X年X月X日"，用中文不用阿拉伯数字）──
_CN_DIGITS = '〇一二三四五六七八九'
_GAN = '甲乙丙丁戊己庚辛壬癸'
_ZHI = '子丑寅卯辰巳午未申酉戌亥'


def _ganzhi_year(y):
    """公历年 → 干支纪年（2026 → 丙午）"""
    return _GAN[(y - 4) % 10] + _ZHI[(y - 4) % 12]


def _cn_month(m):
    if m < 10:
        return _CN_DIGITS[m]
    return {10: '十', 11: '十一', 12: '十二'}[m]


def _cn_day(d):
    if d < 10:
        return _CN_DIGITS[d]
    if d < 20:
        return '十' + ('' if d == 10 else _CN_DIGITS[d % 10])
    if d < 30:
        return '二十' + ('' if d == 20 else _CN_DIGITS[d % 10])
    return '三十' + ('' if d == 30 else _CN_DIGITS[d % 10])


def _cn_date(dt):
    """datetime → '丙午年八月十六日'（干支纪年 + 中文月日）"""
    return f'{_ganzhi_year(dt.year)}年{_cn_month(dt.month)}月{_cn_day(dt.day)}日'


def _cn_year(y):
    """公历年份 → 中文数字（2026 → 二〇二六）"""
    return ''.join(_CN_DIGITS[int(c)] for c in str(y))


def _cn_gongli(date_val):
    """公历日期 → 中文公历（'2026-08-17' → '二〇二六年八月十七日'），普通人看懂干支的注明。"""
    import re as _re
    y = mo = d = None
    if isinstance(date_val, str):
        m = _re.search(r'(\d{4})[年\-/\.](\d{1,2})[月\-/\.](\d{1,2})', date_val.strip())
        if m:
            y, mo, d = int(m.group(1)), int(m.group(2)), int(m.group(3))
    elif hasattr(date_val, 'year'):
        y, mo, d = date_val.year, date_val.month, date_val.day
    if not y:
        return ''
    return f'{_cn_year(y)}年{_cn_month(mo)}月{_cn_day(d)}日'


def _gongli_suffix(data):
    """四柱行的公历注明后缀：'（二〇二六年八月十七日）'；无 date 则空串。"""
    gl = _cn_gongli(data.get('date') or '')
    return f'（{gl}）' if gl else ''


# ── 繁体转换（古法：文书正文用繁体；CSS 字体名/JS/HTML 结构保持简体）──
_T2T = None
# 自定义用字：庇荫 → 蔭（标准繁体；古字「䕃」U+4543 与「廕」U+5ED5 在文征明字体里缺字，
# 用它们会回退系统字体破坏笔意，故用字体覆盖的「蔭」）
_T2T_POST = {'廕': '蔭'}


def _t(s):
    """简体 → 繁体（文书正文用）。opencc 不可用时原样返回。"""
    global _T2T
    if _T2T is None:
        try:
            from opencc import OpenCC
            _T2T = OpenCC('s2t')
        except Exception:
            _T2T = False
    if not _T2T or s is None:
        return s
    out = _T2T.convert(str(s))
    if _T2T_POST:
        for a, b in _T2T_POST.items():
            if a in out:
                out = out.replace(a, b)
    return out


def _name(p):
    """从课格/格局条目安全取名称：兼容 str / {格局名称} / {name}。"""
    if not p:
        return ''
    if isinstance(p, str):
        return p
    return p.get('格局名称') or p.get('name') or p.get('name') or ''


def _extract_sizhu(detail):
    sizhu = detail.get('sizhu', {}) or {}
    y = sizhu.get('年', '') or ''
    mo = sizhu.get('月', '') or ''
    d = sizhu.get('日', '') or ''
    h = sizhu.get('时', '') or ''
    parts = []
    if y:
        parts.append(f'{y}年')
    if mo:
        parts.append(f'{mo}月')
    if d:
        parts.append(f'{d}日')
    if h:
        parts.append(f'{h}时')
    return ''.join(parts) or '待定'


def _extract_shanxiang(data, detail):
    mountain = (data.get('mountain') or '').strip()
    xiang = (detail.get('xiang_shou') or '').strip()
    if not mountain:
        return '待定'
    if xiang:
        return f'{mountain}山（向{xiang}）'
    return f'{mountain}山'


def _extract_liuren_kege(detail):
    sc = detail.get('sanchuan', {}) or {}
    keti = (sc.get('课体') or '').strip()
    kege_list = sc.get('课格列表') or []
    names = [n for n in (_name(k) for k in kege_list) if n]
    parts = []
    if keti:
        parts.append(keti)
    parts.extend(names)
    return '、'.join(parts) if parts else '待定'


def _trim(text, limit=30):
    """精简文本到 limit 字，超出加「…」（日课单面向普通人群，批语不宜过长）。"""
    text = (text or '').strip()
    if len(text) <= limit:
        return text
    return text[:limit] + '…'


def _extract_piyu(detail):
    # 优先取综合批语文言（已由 _build_zonghe_piyu 生成古法短句，非引擎技术摘要）
    zp = detail.get('zonghe_piyu') or {}
    if isinstance(zp, dict) and zp.get('wen'):
        return _trim(zp['wen'], 50)
    yidu = detail.get('yidu', {}) or {}
    ev = (yidu.get('eval') or '').strip()
    if ev:
        return _trim(ev, 30)
    return '课格平和，无大凶之象，可斟酌使用。'


# ── 择日类型分组 → 课单字段/开篇语（不同择日类型用不同课单格式）──
TYPE_GROUP = {
    '立碑': '阴宅', '安葬': '阴宅', '阴宅动土': '阴宅', '迁坟': '阴宅', '催龙补气': '阴宅', '召山买土': '阴宅',
    '婚嫁': '婚嫁',
    '新居入宅': '阳宅', '安门': '阳宅', '作灶': '阳宅', '安床': '阳宅',
    '动土修造': '阳宅', '阳宅动土': '阳宅', '上梁盖屋': '阳宅', '开工': '阳宅',
    '开业': '人事', '签约交易': '人事', '出行': '人事', '祭祀祈福': '人事', '求嗣': '人事',
    '提车': '人事', '买房过户': '人事', '入学开学': '人事', '考试': '人事', '测孩子成绩': '人事',
    # 六壬占类（指定日分析 /api/zeri/analyze 导出文书时传入，映射到对应课单格式）
    '求财': '人事', '功名': '人事', '疾病': '人事', '官讼': '人事', '胎产': '人事',
    '婚姻': '婚嫁', '家宅': '阳宅',
    '杂占': '人事', '天时': '人事', '终身': '人事', '流年': '人事', '一课二事': '人事', '亡盗': '人事',
}

# 每组显示的字段（顺序即文书显示顺序；四柱/批语/避忌 三项所有类型固定，不在此列）
# 元组 = 合并成一行（按元组顺序排列，字段之间空 4 全角字符）；字符串 = 独立一行
GROUP_FIELDS = {
    '阴宅': [('来龙', '坐山', '向')],
    '婚嫁': ['男命', '女命'],
    '阳宅': ['坐山', '向', '主命'],
    '人事': ['主命'],
}

# 合并行字段之间的间隔（4 个全角空格，竖排中 = 4 字高的空白）
_JOIN_GAP = '\u3000\u3000\u3000\u3000'

_FIELD_LABEL = {'仙命': '仙命', '坐山': '坐山', '向': '向山', '来龙': '来龙',
                '男命': '男命', '女命': '女命', '主命': '主命'}

_OPENING_HEAD = '伏以，天地定位，山向合机；理气相通，福泽攸关。谨奉《穿山透地真传》之旨，依《仪度六壬选日要诀》之法，'
GROUP_OPENING_TAIL = {
    '阴宅': '为孝眷择取{type}吉期，安妥先灵，庇荫后昆。',
    '婚嫁': '为佳偶择取{type}吉期，鸾凤和鸣，宜室宜家。',
    '阳宅': '为宅主择取{type}吉期，安宅纳福，家道兴隆。',
    '人事': '为事主择取{type}吉期，趋吉避凶，福泽绵长。',
}


def _group_of(zetiri_type):
    return TYPE_GROUP.get((zetiri_type or '').strip(), '阴宅')


def _field_value(data, detail, key):
    if key == '仙命':
        return (data.get('xianming') or '').strip() or '待定'
    if key == '坐山':
        return (data.get('mountain') or '').strip() or '待定'
    if key == '向':
        return (detail.get('xiang_shou') or '').strip() or '待定'
    if key == '来龙':
        return (data.get('lailong') or '').strip() or '待定'
    if key == '男命':
        return (data.get('nan_ming') or '').strip() or '待定'
    if key == '女命':
        return (data.get('nv_ming') or '').strip() or '待定'
    if key == '主命':
        return (data.get('ben_ming') or '').strip() or '待定'
    return '待定'


def _strip_rule_tag(s):
    """剥掉内部规则编号前缀（如「R1 变格：…」→「变格：…」）。

    理由：R1~R6 是 `keti_arbitration` 的**内部裁定链编号**，专业界面（仪表盘卡片）
    保留可追溯；但**客户课单**是给人看的正式文书，出现编号不知所指。
    """
    import re as _re
    return _re.sub(r'^\s*R\d+\s*[：:]?\s*', '', str(s or '')).strip()


def _zhuge_rangjie_lines(detail):
    """🆕 2026-09-22：文书追加「主格裁定」「宜禳趋避」两行（🔴 零评分影响，只展示）。

    ⛔ 无内容时**返回空列表** —— 不为「引擎没裁定」的课硬凑字段（憨爷：反感噪音）。
    依据：主格裁定 `engine/keti_arbitration.arbitrate`（中L3460「以用为主」等六条）；
    禳解 `engine/rangjie_engine.suggest`（中L1841／L2201／L2305／L2450／L9371）。
    """
    out = []
    try:
        zg = detail.get('zhuge') or {}
        if zg.get('主格'):
            txt = '%s（%s）' % (zg.get('主格', ''), zg.get('主格性质') or '平')
            d = [x for x in (zg.get('降等') or []) if x]
            # 降等首条若只是在解释主格本身（含主格名），则不再重复（客户课单不堆术语）
            _d0 = _strip_rule_tag(d[0]) if d else ''
            if _d0 and (zg.get('主格', '') not in _d0):
                txt += '；' + _d0
            out.append(('主格裁定', _trim(txt, 42)))
        rj = detail.get('rangjie') or {}
        if rj.get('宜禳'):
            fa = '／'.join([x for x in (rj.get('禳法') or []) if x][:2])
            txt = (fa or '宜禳') + '，' + ('有救' if rj.get('有救') else '无救')
            out.append(('宜禳趋避', _trim(txt, 42)))
        # 祷所取象：只取「方位＋建筑类」（客户看得懂的部分），
        # ⛔ 神格/天将/原文行号属专业界面内容，不进客户课单。
        gs = detail.get('guishen_xiang') or {}
        if gs.get('象域') and (gs.get('候选') or []):
            c0 = gs['候选'][0]
            _gs = '%s之%s' % (c0.get('方位') or '', c0.get('建筑类') or '')
            out.append(('祷所', _trim(_gs.strip('之'), 30)))
    except Exception:
        return []
    return out


def _field_lines(data, detail):
    """按择日类型分组，返回字段行 [(label, value), ...]（label/value 转繁体）。

    label 为 None 表示合并行（value 已含「字段：值」拼接，字段间空 4 全角字符）。
    """
    group = _group_of(data.get('zetiri_type'))
    lines = []
    for item in GROUP_FIELDS[group]:
        if isinstance(item, tuple):
            parts = [f'{_FIELD_LABEL[k]}：{_field_value(data, detail, k)}' for k in item]
            lines.append((None, _t(_JOIN_GAP.join(parts))))
        else:
            lines.append((_t(_FIELD_LABEL[item]), _t(_field_value(data, detail, item))))
    # 🆕 2026-09-22：主格裁定 / 宜禳趋避（有则加，无则不加）
    for _lb, _vl in _zhuge_rangjie_lines(detail):
        lines.append((_t(_lb), _t(_vl)))
    return lines


def _opening(data):
    """按择日类型生成开篇语。"""
    zetiri_type = (data.get('zetiri_type') or '立碑').strip()
    group = _group_of(zetiri_type)
    tail = GROUP_OPENING_TAIL[group].format(type=zetiri_type)
    return _OPENING_HEAD + tail


def build_mapping(data, detail):
    """根据 data + detail 生成占位符 → 文本 映射（文本统一转繁体，古法）。"""
    mapping = {
        '{{标题}}': _t((data.get('title') or '').strip() or _FALLBACK['{{标题}}']),
        '{{仙命}}': _t((data.get('xianming') or '').strip() or _FALLBACK['{{仙命}}']),
        '{{山向}}': _t(_extract_shanxiang(data, detail)),
        '{{来龙}}': _t((data.get('lailong') or '').strip() or _FALLBACK['{{来龙}}']),
        '{{四柱}}': _t(_extract_sizhu(detail)) + _gongli_suffix(data),
        '{{六壬课格}}': _t(_extract_liuren_kege(detail)),
        '{{批语}}': _t(_extract_piyu(detail)),
        '{{避忌}}': _t((data.get('biji') or '').strip() or _FALLBACK['{{避忌}}']),
        '{{地理师}}': _t((data.get('dili_shi') or '').strip() or _FALLBACK['{{地理师}}']),
        '{{日期}}': _t(_cn_date(datetime.now())),
        '[印章]': '',  # 文字占位清除；真实印章图在「日期」段落内联，保留
    }
    return mapping


def _replace_in_paragraph(para, mapping):
    for run in para.runs:
        txt = run.text
        if not txt:
            continue
        new = txt
        for k, v in mapping.items():
            if k in new:
                new = new.replace(k, v)
        if new != txt:
            run.text = new


def _clone_para_text(src_el, text):
    """复制段落元素，替换全部文字为 text，保留 run 样式（书法字体等）。"""
    from docx.oxml.ns import qn as _qn
    from docx.oxml import OxmlElement as _OE
    import copy as _copy
    new_el = _copy.deepcopy(src_el)
    runs = new_el.findall(_qn('w:r'))
    for r in runs[1:]:
        new_el.remove(r)
    if runs:
        r = runs[0]
        for child in list(r):
            if child.tag != _qn('w:rPr'):
                r.remove(child)
        t = _OE('w:t')
        t.text = text
        t.set(_qn('xml:space'), 'preserve')
        r.append(t)
    else:
        r = _OE('w:r')
        t = _OE('w:t')
        t.text = text
        t.set(_qn('xml:space'), 'preserve')
        r.append(t)
        new_el.append(r)
    return new_el


def _set_para_text(para, text):
    """原地把段落文字改为 text（保留第一个 run 的样式）。"""
    from docx.oxml.ns import qn as _qn
    from docx.oxml import OxmlElement as _OE
    runs = para._p.findall(_qn('w:r'))
    for r in runs[1:]:
        para._p.remove(r)
    if runs:
        r = runs[0]
        for child in list(r):
            if child.tag != _qn('w:rPr'):
                r.remove(child)
        t = _OE('w:t')
        t.text = text
        t.set(_qn('xml:space'), 'preserve')
        r.append(t)


def build_wenshu(data):
    """生成文书 docx，返回 BytesIO。

    data: {
        title, xianming, lailong, biji, dili_shi, mountain,
        zetiri_type, nan_ming, nv_ming, ben_ming,
        detail: <api/zeri/analyze 完整返回>（至少含 sizhu / xiang_shou / sanchuan / summary）
    }
    """
    from docx import Document
    from docx.oxml.ns import qn as _qn
    from docx.oxml import OxmlElement as _OE

    tpl = default_tpl_path()
    if not os.path.exists(tpl):
        raise FileNotFoundError(f'模板不存在：{tpl}')

    detail = data.get('detail') or {}
    mapping = build_mapping(data, detail)

    doc = Document(tpl)

    # 1. 占位符替换（段落 + 表格防御性兜底）
    for para in doc.paragraphs:
        _replace_in_paragraph(para, mapping)
    for tbl in doc.tables:
        for row in tbl.rows:
            for cell in row.cells:
                for para in cell.paragraphs:
                    _replace_in_paragraph(para, mapping)

    # 1b. 开篇语按择日类型动态替换（模板开篇写死"立碑"）
    opening_text = _opening(data)
    for para in doc.paragraphs:
        if para.text.strip().startswith('伏以'):
            _set_para_text(para, opening_text)
            break

    # 2. 落款日期精简：去"日期："前缀、"勒石"后缀、"榖旦"→"谷旦"
    for para in doc.paragraphs:
        for run in para.runs:
            for a, b in (('日期：', ''), ('勒石', ''), ('榖旦', '谷旦')):
                if a in run.text:
                    run.text = run.text.replace(a, b)

    # 2b. 落款署名去名字（名号由印章承载）+ 印章图从日期段落移到署名段落
    from docx.oxml.ns import qn as _qn2
    sign_para = None
    date_para = None
    for p in doc.paragraphs:
        t = p.text
        if '沐手谨择' in t:
            for run in p.runs:
                if '沐手谨择' in run.text and not run.text.startswith('沐手谨择'):
                    run.text = run.text[run.text.index('沐手谨择'):]
            sign_para = p
        if '谷旦' in t and date_para is None:
            date_para = p
    if sign_para is not None and date_para is not None and date_para is not sign_para:
        for r in list(date_para._p.findall(_qn2('w:r'))):
            if r.find(_qn2('w:drawing')) is not None or r.find(_qn2('w:pict')) is not None:
                date_para._p.remove(r)
                sign_para._p.append(r)
                break

    # 3. 动态字段：删除模板固定字段段落（仙命/山向/来龙），按择日类型插入新字段段落
    xian_el = None        # 「仙命」段落，作新字段段落样式模板
    sizhu_para = None     # 「择取岁次」段落，作插入锚点
    for p in list(doc.paragraphs):
        t = p.text.strip()
        if t.startswith('仙命') and xian_el is None:
            xian_el = p._element
        if t.startswith('择取岁次') and sizhu_para is None:
            sizhu_para = p

    for p in list(doc.paragraphs):
        t = p.text.strip()
        if t.startswith(('仙命', '山向', '来龙')):
            p._element.getparent().remove(p._element)

    if sizhu_para is not None and xian_el is not None:
        for label, val in _field_lines(data, detail):
            text = val if label is None else f'{label}：{val}'
            sizhu_para._element.addprevious(_clone_para_text(xian_el, text))

    # 4. 删「六壬课格」行；正文段落首行缩进 2 字符（标题/落款/日期不缩进）
    _indent_prefixes = ('伏以', '仙命', '坐山', '向山', '来龙', '男命', '女命',
                        '主命', '择取岁次', '批语', '避忌',
                        '主格裁定', '宜禳趋避', '祷所')   # 🆕 2026-09-22
    for _para in list(doc.paragraphs):
        _pt = _para.text.strip()
        if not _pt:
            continue
        if _pt.startswith('六壬课格'):
            _para._element.getparent().remove(_para._element)
            continue
        if _pt.startswith(_indent_prefixes):
            _pPr = _para._p.get_or_add_pPr()
            for _ind in _pPr.findall(_qn('w:ind')):
                _pPr.remove(_ind)
            _ind = _OE('w:ind')
            _ind.set(_qn('w:firstLineChars'), '200')   # 2 字符
            _ind.set(_qn('w:firstLine'), '480')        # 兜底绝对缩进 480 twips
            _rPr = _pPr.find(_qn('w:rPr'))
            if _rPr is not None:
                _rPr.addprevious(_ind)
            else:
                _pPr.append(_ind)

    # 8. 全文转繁体（古法；幂等——mapping 值已繁体，模板残留简体一并转）
    for _para in doc.paragraphs:
        for _run in _para.runs:
            if _run.text:
                _run.text = _t(_run.text)

    buf = io.BytesIO()
    doc.save(buf)
    buf.seek(0)
    return buf


# ──────────────────────────────────────────────────────────────
# HTML 竖排文书（预览器/WPS/Word 看到的版式一致，1:1 复刻模板视觉效果）
# ──────────────────────────────────────────────────────────────
def _get_tpl_seal_data_uri():
    """从模板提取印章图 image1.png（落款章「儀度玄造」），转 data:image/png;base64 内嵌。"""
    import zipfile, base64 as _b64
    tpl = default_tpl_path()
    if not os.path.exists(tpl):
        return ''
    try:
        with zipfile.ZipFile(tpl) as z:
            data = z.read('word/media/image1.png')
        return 'data:image/png;base64,' + _b64.b64encode(data).decode('ascii')
    except Exception:
        return ''


def _get_seal_data_uri():
    """从项目根目录 _seal_moyin_raw.png（起手章，用户 PDF 提取的古篆方印）读图，转 data:image/png;base64 内嵌。"""
    import base64 as _b64
    p = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '_seal_moyin_raw.png')
    if not os.path.exists(p):
        return ''
    try:
        with open(p, 'rb') as f:
            return 'data:image/png;base64,' + _b64.b64encode(f.read()).decode('ascii')
    except Exception:
        return ''


# ── 文征明楷书字体内嵌（@font-face base64，保证任何电脑/PDF 都显示文征明楷书）──
FONT_FAMILY = '文征明楷书'
FONT_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                         '_fonts', 'SentyWEN2017.ttf')
_FONT_B64 = None


def _font_face_css():
    """返回 @font-face CSS（内嵌 SentyWEN2017 文征明楷书）。字体缺失时返回空串。"""
    global _FONT_B64
    if _FONT_B64 is None:
        _FONT_B64 = ''
        if os.path.exists(FONT_PATH):
            try:
                import base64 as _b
                with open(FONT_PATH, 'rb') as _f:
                    _FONT_B64 = _b.b64encode(_f.read()).decode('ascii')
            except Exception:
                _FONT_B64 = ''
    if not _FONT_B64:
        return ''
    return ("@font-face{font-family:'" + FONT_FAMILY + "';"
            "src:url(data:font/truetype;base64," + _FONT_B64 + ")format('truetype');}")


def build_wenshu_html(data):
    """生成 HTML 竖排文书（视觉 1:1 复刻完美模板：横向 Letter + 米黄底 + 红框 + 竖排从右到左 + 书法字体 + 印章）。

    data 字段同 build_wenshu。返回 str（完整 HTML，含 <!DOCTYPE>）。
    """
    detail = data.get('detail') or {}
    mapping = build_mapping(data, detail)
    seal_uri = _get_seal_data_uri()          # 起手章：_seal_moyin_raw.png（啟之美傳）
    tpl_seal_uri = _get_tpl_seal_data_uri()  # 落款章：完美模板.docx 里的 image1.png（儀度玄造）

    def esc(s):
        return (str(s or '').replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;'))

    title = esc(mapping['{{标题}}'])
    sizhu = esc(mapping['{{四柱}}'])
    piyu = esc(mapping['{{批语}}'])
    biji = esc(mapping['{{避忌}}'])
    dilishi = esc(mapping['{{地理师}}'])
    # 落款地理师行：用户填了才显示（竖排中位于「沐手謹擇」上方，前缀与 docx 模板「地理師：」一致）
    dilishi_tag = (f'<div style="font-size:var(--fs);line-height:1.7;letter-spacing:-11px;">地理師：{dilishi}</div>'
                   if (data.get('dili_shi') or '').strip() else '')
    date_ = esc(mapping['{{日期}}'])
    opening = esc(_t(_opening(data)))

    # 动态字段行（按择日类型分组；label=None 为合并行，value 已含字段拼接与间隔）
    field_lines_html = ''
    for label, val in _field_lines(data, detail):
        if label is None:
            field_lines_html += f'    <div class="line merged">{esc(val)}</div>\n'
        else:
            field_lines_html += f'    <div class="line">{label}：{esc(val)}</div>\n'

    seal_img = f'<img class="sign-seal" src="{tpl_seal_uri}" alt="儀度玄造印">' if tpl_seal_uri else ''
    font_css = _font_face_css()
    # 标题旁的古篆方印（PDF 提取的「啟之美傳」）：紧贴标题列左侧、顶部对齐
    title_seal_img = f'<img class="title-seal" src="{seal_uri}" alt="敬东湖居士印">' if seal_uri else ''

    html = f'''<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="UTF-8">
<title>{title}</title>
<style>
  {font_css}
  html, body {{ margin: 0; padding: 0; background: #666; font-family: 'Microsoft YaHei', sans-serif; }}
  body {{ display: flex; justify-content: center; align-items: center; min-height: 100vh; padding: 24px; box-sizing: border-box; }}
  .paper {{
    writing-mode: vertical-rl;
    -webkit-writing-mode: vertical-rl;
    display: flex;
    flex-direction: column;
    --fs: 19px;
    /* 宣纸：米黄底 + 极淡纤维噪点（SVG feTurbulence） */
    background-color: #FCD5B5;
    background-image: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='260' height='260'><filter id='n'><feTurbulence type='fractalNoise' baseFrequency='0.85' numOctaves='2' stitchTiles='stitch'/></filter><rect width='260' height='260' filter='url(%23n)' opacity='0.09'/></svg>");
    color: #241a12;
    font-family: '文征明楷书', '李白赋诗游龙惊鸿', 'STKaiti', '华文行楷', '楷体', 'KaiTi', serif;
    width: 11in;
    height: 8.5in;
    padding: 46px 52px;
    box-sizing: border-box;
    position: relative;
    /* 双层暗朱红框：内细线2px + 5px米黄间隙 + 外粗线4px */
    box-shadow:
      inset 0 0 0 2px #C1272D,
      inset 0 0 0 8px #FCD5B5,
      inset 0 0 0 12px #C1272D;
    overflow: hidden;
    text-orientation: mixed;
    -webkit-print-color-adjust: exact;
    print-color-adjust: exact;
  }}
  /* 四角如意纹（L 形加粗角线，对齐外粗框 12px） */
  .paper::before {{
    content: '';
    position: absolute;
    inset: 12px;
    pointer-events: none;
    background:
      linear-gradient(#C1272D,#C1272D) 0 0 / 30px 5px no-repeat,
      linear-gradient(#C1272D,#C1272D) 0 0 / 5px 30px no-repeat,
      linear-gradient(#C1272D,#C1272D) 100% 0 / 30px 5px no-repeat,
      linear-gradient(#C1272D,#C1272D) 100% 0 / 5px 30px no-repeat,
      linear-gradient(#C1272D,#C1272D) 0 100% / 30px 5px no-repeat,
      linear-gradient(#C1272D,#C1272D) 0 100% / 5px 30px no-repeat,
      linear-gradient(#C1272D,#C1272D) 100% 100% / 30px 5px no-repeat,
      linear-gradient(#C1272D,#C1272D) 100% 100% / 5px 30px no-repeat;
  }}
  .content {{
    /* 乌丝栏：极淡竖栏线，古籍界格感 */
    background-image: repeating-linear-gradient(to left, transparent, transparent 32px, rgba(193,39,45,0.06) 32px, rgba(193,39,45,0.06) 33px);
  }}
  .footer {{
    align-self: flex-end;
    margin-block-start: 56px;
  }}
  .title {{
    font-size: 32px;
    font-weight: bold;
    margin-block-end: 26px;
    letter-spacing: 0px;
    line-height: 1.3;
    text-align: center;
  }}
  .title-seal {{
    position: absolute;
    width: 56px;
    height: 58px;
    z-index: 3;
    pointer-events: none;
    opacity: 0.85;
    /* JS 未跑时（如 chromium headless 打印虚拟时间不够）的合理默认位置：开篇首字附近 */
    left: 850px;
    top: 80px;
  }}
  .seal-target {{ /* 印章骑盖的定位锚点（开篇首字） */ }}
  .opening, .line {{
    font-size: var(--fs);
    line-height: 1.7;
    letter-spacing: -11px;
    margin-block-end: 24px;  /* 列间距≈1字宽；字距=19×1.7-5≈27px，与列距协调 */
    text-indent: 2em;
  }}
  .merged {{ white-space: nowrap; }}  /* 合并行：强制不换列，超高一列时由 JS 收字距/缩字号适配 */
  .sign-line {{
    display: flex;
    flex-direction: row;
    align-items: center;
    justify-content: center;
    gap: 14px;
    margin-block-end: 14px;
    font-size: var(--fs);
    line-height: 1.7;
    letter-spacing: -11px;
  }}
  .sign-text {{ /* 居中对齐：去掉顶部缩进，让"沐手谨择"从 text 块顶部起，整体与印章+日期列垂直居中 */ }}
  .date-line {{
    font-size: var(--fs);
    line-height: 1.7;
    letter-spacing: -11px;
    margin-block-end: 0;
    text-indent: 2em;
  }}
  .sign-seal {{
    width: 72px;
    height: 72px;
    opacity: 0.88;
    transform: rotate(-2deg);
    filter: saturate(1.12) contrast(1.05);
  }}
  @page {{
    size: 11in 8.5in;
    margin: 0;
  }}
  @media print {{
    body {{ padding: 0; background: #fff; }}
  }}
</style>
</head><body>
<div class="paper">
  <div class="content">
    <div class="title">{title}</div>
    {title_seal_img}
    <div class="opening"><span class="seal-target">{opening[0]}</span>{opening[1:]}</div>
{field_lines_html}    <div class="line">擇取歲次{sizhu}</div>
    <div class="line">批語：{piyu}</div>
    <div class="line">避忌事宜：{biji}</div>
  </div>
  <div class="footer">
    <div class="sign-line">{seal_img}<div class="sign-text">{dilishi_tag}沐手謹擇</div></div>
    <div class="date-line">歲次{date_}穀旦</div>
  </div>
</div>
<script>
window.addEventListener('load', function(){{
  var paper = document.querySelector('.paper');

  // 自适应缩字：正文太多溢出纸张时，逐档缩小正文字号（下限 13px），同步缩小行距
  var content = document.querySelector('.content');
  var footer = document.querySelector('.footer');
  if (content && footer && paper) {{
    var fs = 19;
    var minFs = 13;
    function overflowed() {{
      var pr = paper.getBoundingClientRect();
      var cr = content.getBoundingClientRect();
      var fr = footer.getBoundingClientRect();
      return cr.left < pr.left - 1 || cr.right > pr.right + 1 ||
             cr.top < pr.top - 1 || cr.bottom > pr.bottom + 1 ||
             fr.left < pr.left - 1 || fr.right > pr.right + 1;
    }}
    while (overflowed() && fs > minFs) {{
      fs -= 1;
      paper.style.setProperty('--fs', fs + 'px');
    }}
  }}

  // 合并行（来龙/坐山/向山等）强制一列不换行：内容超高时先收字距(line-height)、再缩字号（下限 12px）
  var merged = document.querySelector('.line.merged');
  if (merged && content) {{
    var maxMH = content.getBoundingClientRect().height - 44;  // 列高 - 首列缩进2字余量
    function mergedH() {{
      var r = document.createRange();
      r.selectNodeContents(merged);
      return r.getBoundingClientRect().height;
    }}
    var mLh = 1.5, mFs = parseInt(getComputedStyle(merged).fontSize, 10) || 19;
    var cur = mergedH();
    while (cur > maxMH && (mLh > 1.05 || mFs > 12)) {{
      if (mLh > 1.05) {{
        mLh = Math.max(1.05, mLh - 0.05);
        merged.style.lineHeight = mLh;
      }} else {{
        mFs -= 1;
        merged.style.fontSize = mFs + 'px';
      }}
      cur = mergedH();
    }}
  }}

  // 印章浮于文字上方（骑章）：定位到开篇首字「伏」上，中心重合压字
  // 等字体加载完后**同步**定位（不用 setTimeout，chromium 打印虚拟时间会推进微任务；
  // 设 fallback 短超时应对极少见的不跑情况）
  function _positionSeal() {{
    var target = document.querySelector('.seal-target');
    var seal = document.querySelector('.title-seal');
    if (!target || !seal) return;
    var r = target.getBoundingClientRect();
    var pr = paper.getBoundingClientRect();
    var ox = 8, oy = -16;
    seal.style.left = (r.left - pr.left + (r.width - seal.offsetWidth) / 2 + ox) + 'px';
    seal.style.top = (r.top - pr.top + (r.height - seal.offsetHeight) / 2 + oy) + 'px';
  }}
  if (document.fonts && document.fonts.ready) {{
    document.fonts.ready.then(_positionSeal);
  }}
  setTimeout(_positionSeal, 50);
  setTimeout(_positionSeal, 300);
}});
</script>
</body></html>'''
    return html


# ──────────────────────────────────────────────────────────────
# HTML → PDF（无头浏览器打印，保留宣纸纹理/印章/四角边框等视觉效果）
# ──────────────────────────────────────────────────────────────
def _find_chromium():
    """查找 chromium/chrome 可执行文件。"""
    import glob
    home = os.path.expanduser('~')
    candidates = []
    for key in ('CHROME_PATH', 'CHROMIUM_PATH'):
        env = os.environ.get(key)
        if env:
            candidates.append(env)
    candidates += [
        os.path.join(home, 'AppData/Local/ms-playwright/chromium_headless_shell-1226/chrome-headless-shell-win64/chrome-headless-shell.exe'),
        '/usr/bin/chromium', '/usr/bin/chromium-browser', '/usr/bin/chromium-headless-shell',
        '/usr/bin/google-chrome', '/usr/bin/google-chrome-stable',
    ]
    candidates += glob.glob(os.path.join(home, 'AppData/Local/ms-playwright/chromium_headless_shell-*/*/chrome-headless-shell.exe'))
    candidates += glob.glob(os.path.join(home, 'AppData/Local/ms-playwright/chromium-*/*/chrome.exe'))
    for c in candidates:
        if c and os.path.exists(c):
            return c
    return None


def html_to_pdf(html_str, timeout=90):
    """HTML → PDF（chromium headless 打印）。返回 bytes。"""
    import subprocess, tempfile
    chrome = _find_chromium()
    if not chrome:
        raise RuntimeError('未找到 chromium/chrome，无法生成 PDF（可设 CHROME_PATH 环境变量指定路径）')
    # 临时文件放 $HOME（snap 版 chromium 受 AppArmor 限制只能写 $HOME；
    # 写 /tmp 会被 snap 挂载命名空间隔离，文件不落盘导致 PDF 丢失）
    _tmp_home = os.path.expanduser('~') or '/tmp'
    with tempfile.NamedTemporaryFile('w', suffix='.html', delete=False, encoding='utf-8', dir=_tmp_home) as f:
        f.write(html_str)
        html_path = f.name
    pdf_path = html_path + '.pdf'
    try:
        subprocess.run(
            [chrome, '--headless', '--no-sandbox', '--disable-gpu',
             '--print-to-pdf=' + pdf_path, '--no-pdf-header-footer',
             '--run-all-compositor-stages-before-draw', '--virtual-time-budget=8000',
             'file:///' + html_path.replace('\\', '/')],
            check=True, capture_output=True, timeout=timeout,
        )
        with open(pdf_path, 'rb') as f:
            return f.read()
    finally:
        for p in (html_path, pdf_path):
            try:
                if os.path.exists(p):
                    os.unlink(p)
            except Exception:
                pass
