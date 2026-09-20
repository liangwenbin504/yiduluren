#!/usr/bin/env python3
"""LangGraphDAG v4.0 - Data-Bound Anti-Hallucination Pipeline"""
import json, os, sys
from typing import TypedDict
from datetime import date, datetime, timedelta
from langgraph.graph import StateGraph, START, END

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    from dotenv import load_dotenv; load_dotenv()
except: pass

def _now():
    return datetime.utcnow() + timedelta(hours=8)

def _solar_now():
    return _now() + timedelta(minutes=-58)

def _rizhu(d):
    ref = date(2020, 1, 1)
    tg = '甲乙丙丁戊己庚辛壬癸'
    dz = '子丑寅卯辰巳午未申酉戌亥'
    n = (d - ref).days % 60
    return tg[(9 + n) % 10] + dz[(3 + n) % 12]

def _yuejiang(m, d):
    # 2026-08-17 清理：精确中气换将（原固定节气日近似表，且与 full_pai_pan 农历月表不一致）
    try:
        from engine.yuejiang_engine import YueJiangCalculator
        yj, _name = YueJiangCalculator().get_yuejiang_by_date(d.year, d.month, d.day)
        return yj
    except Exception:
        doy = d.timetuple().tm_yday
        jq = [5,19,34,49,65,80,95,111,126,142,158,174,
              190,206,222,238,254,270,286,302,318,334,350,366]
        yj = ['子','丑','寅','卯','辰','巳','午','未','申','酉','戌','亥'] * 3
        idx = sum(1 for dn in jq if doy >= dn)
        return yj[idx + 1]

DDE = {'甲':'寅','乙':'申','丙':'巳','丁':'亥','戊':'巳','己':'亥','庚':'申','辛':'巳','壬':'亥','癸':'巳'}
DLU = {'甲':'寅','乙':'卯','丙':'巳','丁':'午','戊':'巳','己':'午','庚':'申','辛':'酉','壬':'亥','癸':'子'}
DMU = {'甲':'未','乙':'未','丙':'戌','丁':'丑','戊':'戌','己':'丑','庚':'丑','辛':'辰','壬':'辰','癸':'未'}
TX_JI = {'春':'戌','夏':'丑','秋':'辰','冬':'未'}

class StockState(TypedDict):
    paipan: str
    llm_analysis: str
    ml_result: str
    market_data: str

def node_pai_pan(state: StockState) -> dict:
    td = _now().date()
    sc_list = ['子','丑','寅','卯','辰','巳','午','未','申','酉','戌','亥']
    sc = sc_list[((_solar_now().hour + 1) // 2) % 12]
    yj = _yuejiang(td.month, td)
    rz = _rizhu(td)
    rg, rz_zhi = rz[0], rz[1]
    
    # 2026-08-17 清理：V2 权威引擎 + 精确月将直传（原 full_pai_pan 用农历月简化月将）
    from engine.sike_sanchuan_engine import SiKeSanChuanCalculator2
    from engine.gui_ren_daynight import get_gui_ren_pan, get_sunset_info, is_daytime

    r = SiKeSanChuanCalculator2().calculate(rg, rz_zhi, yj, sc)
    sc3_all = [r['sanchuan'].get('初传', ''), r['sanchuan'].get('中传', ''),
               r['sanchuan'].get('末传', '')]
    sc3 = [c for c in sc3_all if c]
    keti = r['sanchuan'].get('课体', '')
    pan = get_gui_ren_pan(rg, sc)
    tj = [pan.get(s, '') for s in sc3]
    sike = [{'name': n, 'top': s, 'bottom': x} for n, s, x, _ in r['sike']]
    sunset = {'sunset': '19:32', 'day_shichen': '丑寅卯辰巳午未申酉'}
    season = {1:'春',2:'春',3:'春',4:'夏',5:'夏',6:'夏',7:'秋',8:'秋',9:'秋',10:'冬',11:'冬',12:'冬'}.get(td.month,'夏')
    
    info = '=== 排盘数据(禁止编造三传/课体/天将!) ===\n'
    info += td.strftime('%Y-%m-%d') + ' 日柱:' + rz + ' 日干:' + rg + '\n'
    info += '月将:' + yj + ' 占时:' + sc + ' 课体:' + keti + '\n'
    info += '日德:' + DDE.get(rg,'') + ' 日禄:' + DLU.get(rg,'') + ' 日墓:' + DMU.get(rg,'') + '\n'
    info += '天喜:' + TX_JI.get(season,'') + ' 日落:' + sunset['sunset'] + '\n'
    info += '四课: '
    for sk in sike:
        info += sk['name'] + ':' + sk['top'] + '(' + pan.get(sk['top'],'') + ')>' + sk['bottom'] + ' '
    info += '\n三传:' + '->'.join(sc3) + '\n'
    info += '天将:' + ' '.join(sc3[i]+'('+tj[i]+')' for i in range(len(sc3))) + '\n'
    info += '旬空:辰巳(甲午旬) 驿马:寅\n'
    
    return {'paipan': info}

def node_llm(state: StockState) -> dict:
    paipan = state.get('paipan', '')
    try:
        # 统一客户端：DeepSeek V4-Flash + 预测场景(thinking=high)
        from deepseek_client import DeepSeekClient, SCENE_PREDICTION
        ds = DeepSeekClient()
        from stock_daily_predict import SYSTEM_PROMPT
        prompt = '禁止编造! 必须与排盘数据完全一致!\n\n' + paipan + '\n请进行17步完整推理预测明日走势。'
        resp = ds.call(
            [{'role': 'system', 'content': SYSTEM_PROMPT},
             {'role': 'user', 'content': prompt}],
            scene=SCENE_PREDICTION,
        )
        if resp.get('success'):
            return {'llm_analysis': resp['content']}
        return {'llm_analysis': f'LLM调用失败: {resp.get("error", "")[:100]}'}
    except Exception as e:
        return {'llm_analysis': f'LLM异常: {e}'}

def node_ml(state: StockState) -> dict:
    try:
        import ml_stock_predict
        p = ml_stock_predict.predict_today()
        return {'ml_result': p.get('trend','?') + ' ' + str(p.get('confidence',0))}
    except:
        return {'ml_result': 'N/A'}

def node_market(state: StockState) -> dict:
    try:
        import akshare as ak
        df = ak.stock_zh_index_daily(symbol='sh000001')
        return {'market_data': str(df.iloc[-1]['close'])}
    except:
        return {'market_data': '0'}

class PredictionPipeline:
    def __init__(self):
        g = StateGraph(StockState)
        g.add_node('p', node_pai_pan)
        g.add_node('l', node_llm)
        g.add_node('m', node_ml)
        g.add_node('k', node_market)
        g.add_edge(START, 'p')
        g.add_edge('p', 'l')
        g.add_edge('l', 'm')
        g.add_edge('m', 'k')
        g.add_edge('k', END)
        self.app = g.compile()
    
    def run(self, target_date=None):
        if target_date is None:
            target_date = _now().strftime('%Y-%m-%d')
        r = self.app.invoke({'paipan':'','llm_analysis':'','ml_result':'','market_data':''})
        print('=' * 60)
        print('  LangGraphDAG - ' + target_date)
        print('=' * 60)
        print(r.get('paipan','')[:500])
        print('--- LLM 17维推理 ---')
        print(r.get('llm_analysis','')[:800])
        print('--- ML ---')
        print(r.get('ml_result',''))
        print('--- Market ---')
        print(r.get('market_data',''))
        return r
    
    def status(self):
        return {'status': 'ready', 'anti_hallucination': True}

if __name__ == '__main__':
    PredictionPipeline().run()
