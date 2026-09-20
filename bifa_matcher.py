#!/usr/bin/env python3
"""毕法赋自动匹配引擎 — 对每条预测扫描100条毕法赋"""
import json, os

# 日煞速查
DDE = {'甲':'寅','乙':'申','丙':'巳','丁':'亥','戊':'巳','己':'亥','庚':'申','辛':'巳','壬':'亥','癸':'巳'}
DLU = {'甲':'寅','乙':'卯','丙':'巳','丁':'午','戊':'巳','己':'午','庚':'申','辛':'酉','壬':'亥','癸':'子'}
DMU = {'甲':'未','乙':'未','丙':'戌','丁':'丑','戊':'戌','己':'丑','庚':'丑','辛':'辰','壬':'辰','癸':'未'}
TX_JI = {'春':'戌','夏':'丑','秋':'辰','冬':'未'}

def get_season(month):
    if month in (1,2,3): return '春'
    if month in (4,5,6): return '夏'
    if month in (7,8,9): return '秋'
    return '冬'

def match_bifa(prediction: dict) -> dict:
    """对一条预测匹配毕法赋规则"""
    matches = []
    rg = prediction.get('rizhu','')[:1] if prediction.get('rizhu') else ''
    rz = prediction.get('rizhu','')[-1:] if len(prediction.get('rizhu',''))>1 else ''
    yj = prediction.get('yue_jiang','')
    keti = str(prediction.get('keti',''))
    sc = prediction.get('sanchuan',[])
    tj = prediction.get('sanchuan_tianjiang',[])
    sike = prediction.get('sike',[])
    analysis = str(prediction.get('analysis',''))
    rc = prediction.get('reasoning_chain',{})
    rc_analysis = str(rc.get('神煞','')) + str(rc.get('天将分析','')) + str(rc.get('刑冲合害',''))
    
    # 从月将推断月份
    yj_num = {'子':11,'丑':12,'寅':1,'卯':2,'辰':3,'巳':4,'午':5,'未':6,'申':7,'酉':8,'戌':9,'亥':10}
    month = yj_num.get(yj,6)
    season = get_season(month)
    
    
    # 7. 旺禄临身 = 日禄在干上或在传
    dlu = DLU.get(rg, '')
    if dlu:
        # 干上(第一课)或传中有禄
        if sike and len(sike)>=1 and dlu in str(sike[0]):
            matches.append({'rule':7, 'name':'旺禄临身', 'signal':'观望',
                          'reason':f'日禄{dlu}临干上→守成勿妄作','auto':True})
        elif dlu in str(sc):
            matches.append({'rule':7, 'name':'日禄临传', 'signal':'中性偏稳',
                          'reason':f'日禄{dlu}在传→有支撑但不宜激进','auto':True})
    
    # 21. 交车相合 = 干上神与支上神相合 或 日干与日支上神相合
    if rg and rz and sike and len(sike)>=3:
        sk1 = str(sike[0])  # 干上
        sk3 = str(sike[2])  # 支上
        # 提取干上神和支上神（从 ('第一课', 'X', 'Y', '') 中提取X）
        import re
        m1 = re.findall(r"'([^']+)'", sk1)
        m3 = re.findall(r"'([^']+)'", sk3)
        ganshang = m1[1] if len(m1)>=2 else "" if len(m1)>=1 else ''
        zhishang = m3[1] if len(m3)>=2 else "" if len(m3)>=1 else ''
        if ganshang and zhishang:
            # 相合: 子丑/寅亥/卯戌/辰酉/巳申/午未
            he_pairs = {('子','丑'),('丑','子'),('寅','亥'),('亥','寅'),
                       ('卯','戌'),('戌','卯'),('辰','酉'),('酉','辰'),
                       ('巳','申'),('申','巳'),('午','未'),('未','午')}
            if (ganshang, zhishang) in he_pairs:
                matches.append({'rule':21, 'name':'交车相合', 'signal':'利好',
                              'reason':f'干上{ganshang}与支上{zhishang}相合→市场和谐交易利','auto':True})
# 60. 太阳射宅 = 月将临支上
    if sike and len(sike) >= 3:
        sk3 = str(sike[2])
        if yj and yj in sk3:
            matches.append({'rule':60, 'name':'太阳射宅', 'signal':'大利好',
                          'reason':f'月将{yj}临支上→市场向阳','auto':True})
    
    # 太阳照墓 = 日墓被月将照
    dmu = DMU.get(rg,'')
    if dmu and yj and dmu == yj:
        matches.append({'rule':60, 'name':'太阳照墓', 'signal':'利好',
                      'reason':f'月将{yj}临日墓{dmu}→破暗向明','auto':True})
    
    # 太阳照身 = 月将临干上
    if sike and len(sike) >= 1:
        sk1 = str(sike[0])
        if yj and yj in sk1:
            matches.append({'rule':60, 'name':'太阳照身', 'signal':'利好',
                          'reason':f'月将{yj}临干上→我方得势','auto':True})
    
    # 53. 两蛇夹墓
    dmu = DMU.get(rg,'')
    if dmu:
        sc_str = str(sc)
        tj_str = str(tj)
        if dmu in sc_str and tj_str.count('蛇') >= 1:
            # 墓在传中 + 至少一个螣蛇
            level = 'both' if tj_str.count('蛇') >= 2 else 'single'
            if level == 'both':
                matches.append({'rule':53, 'name':'两蛇夹墓', 'signal':'凶',
                              'reason':f'螣蛇夹日墓{dmu}→洗盘套牢难逃','auto':True})
            else:
                matches.append({'rule':53, 'name':'螣蛇临墓', 'signal':'警惕',
                              'reason':f'螣蛇临日墓{dmu}→谨慎但非必凶','auto':True})
    
    # 34. 苦去甘来(末传助初传)
    if len(sc) >= 3 and len(tj) >= 3:
        # 初传凶→末传吉 = 苦去甘来
        chu_xiong = any(x in (tj[0] if len(tj)>0 else '') if len(tj)>0 else "" for x in ['虎','蛇','玄','勾'])
        mo_ji = any(x in (tj[-1] if len(tj)>0 else '') if len(tj)>0 else "" for x in ['龙','贵','合','常','后'])
        if chu_xiong and mo_ji:
            matches.append({'rule':34, 'name':'苦去甘来', 'signal':'先跌后涨',
                          'reason':'初传凶将末传吉将→探底回升','auto':True})
    
    # 33. 有始无终(初吉末凶)
    chu_ji = any(x in (tj[0] if len(tj)>0 else '') if len(tj)>0 else "" for x in ['龙','贵','合'])
    mo_xiong = any(x in (tj[-1] if len(tj)>0 else '') if len(tj)>0 else "" for x in ['虎','蛇','玄','勾'])
    if chu_ji and mo_xiong:
        matches.append({'rule':33, 'name':'有始无终', 'signal':'先涨后跌',
                      'reason':'初传吉将末传凶将→冲高回落','auto':True})
    
    # 51. 魁度天门(戌加亥)
    if '戌' in str(sc) and '亥' in str(sc):
        matches.append({'rule':51, 'name':'魁度天门', 'signal':'阻力',
                      'reason':'戌+亥→遇阻回落','auto':True})
    
    # 天喜临财
    tx = TX_JI.get(season,'')
    if tx and tx in str(sc):
        # 天喜的位置是不是财
        matches.append({'rule':19, 'name':'天喜临传', 'signal':'大利好',
                      'reason':f'{season}季天喜{tx}在传中','auto':True})
    
    # 青龙临传
    has_long = any('龙' in str(t) for t in tj)
    has_shui = any(str(s) in ('子','亥') for s in sc)
    if has_long and has_shui:
        matches.append({'rule':92, 'name':'青龙得水', 'signal':'主升浪',
                      'reason':'青龙临水→跃天衢大涨','auto':True})
    elif has_long:
        matches.append({'rule':92, 'name':'青龙临传', 'signal':'偏多',
                      'reason':'青龙在传→资金推动','auto':True})
    
    # 86. 伏吟 / 85. 反吟
    if '伏吟' in keti:
        has_chong = any(w in str(sc) for w in ['丑未冲','冲刑'])
        if has_chong:
            matches.append({'rule':86, 'name':'伏吟+刑冲', 'signal':'反转',
                          'reason':'伏吟本静+刑冲→不动变必动','auto':True})
        else:
            matches.append({'rule':86, 'name':'伏吟', 'signal':'盘整',
                          'reason':'伏吟不动→横盘','auto':True})
    if '反吟' in keti:
        matches.append({'rule':85, 'name':'反吟', 'signal':'反转',
                      'reason':'反吟冲动→剧烈变化','auto':True})
    
    # 日禄临传
    dlu = DLU.get(rg,'')
    if dlu and dlu in str(sc):
        matches.append({'rule':7, 'name':'日禄临传', 'signal':'利好',
                      'reason':f'日禄{dlu}在传→资金支撑','auto':True})
    
    # 日德临传
    dde = DDE.get(rg,'')
    if dde and dde in str(sc):
        matches.append({'rule':99, 'name':'日德临传', 'signal':'利好',
                      'reason':f'日德{dde}在传→喜庆政策','auto':True})
    
    # 白虎当途(94)
    has_hu = any('虎' in str(t) for t in tj)
    has_gui = any(str(s) in str(rc.get('官鬼','')) for s in sc if s)
    if has_hu and has_gui:
        matches.append({'rule':94, 'name':'白虎当途', 'signal':'暴跌风险',
                      'reason':'白虎临传+官鬼在传→暴跌预警','auto':True})
    
    # 判断系统是否遗漏了这些规则（检查推理链中是否提到）
    for m in matches:
        m['mentioned'] = m['name'] in analysis or m['name'] in rc_analysis
    
    # 分类: red=大利好被遗漏, orange=一般匹配, green=已分析
    for m in matches:
        if m['auto'] and not m['mentioned'] and m['signal'] in ('大利好','利好'):
            m['level'] = 'red'  # 重要利好被遗漏
        elif m['auto'] and not m['mentioned']:
            m['level'] = 'orange'  # 其他遗漏
        else:
            m['level'] = 'green'  # 已分析
    
    return {'matches': matches, 'red_count': sum(1 for m in matches if m['level']=='red')}

if __name__ == '__main__':
    # 测试
    BASE = os.path.dirname(__file__)
    with open(os.path.join(BASE,'_memory','stock_predictions.json'), encoding='utf-8') as f:
        preds = json.load(f)
    for p in preds[-5:]:
        r = match_bifa(p)
        reds = [m for m in r['matches'] if m['level']=='red']
        if reds:
            print(f'{p.get("id","?")} [{p.get("category")}] 🔴{len(reds)}:' , ','.join(m["name"] for m in reds))
