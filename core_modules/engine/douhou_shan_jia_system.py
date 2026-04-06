#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
斗首择日二十四山课格断语系统（含评分）

依据《斗首择日秘本》整理二十四山各山的课格断语
评分标准：10 分制，5 分以下不宜使用
"""


class DouShouShanJiaKeGe:
    """斗首择日二十四山课格类"""
    
    def __init__(self):
        self.shan_jia_data = self._init_shan_jia_data()
    
    def _init_shan_jia_data(self):
        """初始化二十四山课格数据（含评分）"""
        return {
            '壬山': {
                'name': '壬山', 'wuxing': '土', 'yuan_chen': '甲己',
                'description': '壬山丙向土元辰，甲己干重化戊深',
                'duanyu': [
                    '甲己化戊土元辰，催丁生子富贵上吉',
                    '丙辛武才多富贵，乙庚单干正财丁',
                    '丁壬破鬼又阴府，戊癸贪官词讼频',
                    '寅巳午支合生旺，亥卯未局木相横',
                    '甲子日催丁生子富贵上吉',
                    '丙子日催丁府贵富比石崇生子',
                    '庚子日催丁生子大旺',
                    '辛未日催材丁、生子大旺',
                ],
                'jinji': '宜：寅卯辰巳申酉戌亥年元气相生比和大利\n忌：子丑午未元气相克为不利',
                'score': 8.0, 'usable': True
            },
            '子山': {
                'name': '子山', 'wuxing': '土', 'yuan_chen': '甲己',
                'description': '子山午向坤元母，造葬元辰甲己土',
                'duanyu': [
                    '甲己合化戌土元辰',
                    '乙庚廉子宜单干，丙辛武才犯阴府',
                    '丁壬破鬼戊癸贪，寅巳辰年发福武',
                    '甲子日富贵长久催丁生子人财大旺盛上吉',
                    '庚辰日魁星日建祠催贵人泮造书斋桥亭公馆衙出贵',
                    '甲辰日上吉富贵不替，魁星日催贵科甲',
                    '己亥日上上大吉',
                ],
                'jinji': '宜：寅卯辰巳申酉戌亥年元气比和相生吉利\n忌：子午丑未年元气冲克不吉',
                'score': 8.5, 'usable': True
            },
            '癸山': {
                'name': '癸山', 'wuxing': '火', 'yuan_chen': '戊癸',
                'description': '癸山戊癸元为火，乙庚财神最益我',
                'duanyu': [
                    '戊癸化丙火元辰',
                    '乙庚财神最益我，丁壬贪官生是非',
                    '丙辛破鬼阴府祸，甲己单干生贵子',
                    '甲己能制破鬼居年坐，巳酉丑年财局旺',
                    '甲子日上吉主才丁生子',
                    '己巳日主年半生子人财大旺',
                    '癸巳日主周年生子进财，富贵大发展七十二年',
                ],
                'jinji': '宜：丑巳申未酉亥年大利\n忌：子寅辰午戊年元气不和不利',
                'score': 8.0, 'usable': True
            },
            '丑山': {
                'name': '丑山', 'wuxing': '火', 'yuan_chen': '戊癸',
                'description': '丑山未向不宜财，戊癸柱中福自来',
                'duanyu': [
                    '戊癸柱中福自来，甲己单干催贵子',
                    '乙庚阴府便生灾，丙辛丁壬皆莫出',
                    '寅辰巳午亦和谐，大阳日日丑时到',
                    '禄在巳宫马在亥，天乙贵人酉亥找',
                    '甲子日主才丁生子',
                    '己巳日主一年半生子人财大旺',
                    '庚辰日文魁星日主催贵',
                ],
                'jinji': '宜：子卯辰申酉年元气比和相生大吉大利\n忌：丑未寅巳午戌亥年气相克不利',
                'score': 7.5, 'usable': True
            },
            '艮山': {
                'name': '艮山', 'wuxing': '木', 'yuan_chen': '丁壬',
                'description': '艮山元辰丁壬木，戊癸单干催子来',
                'duanyu': [
                    '丁壬化甲木元辰',
                    '柱中补助丁壬妙，甲己阴府旺生灾',
                    '乙庚丙辛休入局，主损人丁又退财',
                    '庚午庚戌山方杀，乙丑乙未消灭排',
                    '丁卯日半年生子进财卅年出贵二十四年月日登科甲',
                    '丁丑日半年生子，人财大旺，二十年出贵，廿四年出科甲',
                    '戊寅日三元正旺，周年生子人财大旺',
                ],
                'jinji': '宜：丑寅辰未申戌年元辰比和相生大吉\n忌：子卯巳午酉亥年元辰相克不利凶',
                'score': 7.5, 'usable': True
            },
            '寅山': {
                'name': '寅山', 'wuxing': '木', 'yuan_chen': '丁壬',
                'description': '寅山申向最宜财，甲己重逢福自来',
                'duanyu': [
                    '丁壬化甲木元辰',
                    '阴府丁壬休入局，戊癸单干亦可栽',
                    '四柱只宜元气旺，五行须要得和谐',
                    '巳酉丑年三杀占，乙庚破鬼丙辛灾',
                    '甲子日周年进不意之横财，三年后大发财',
                    '戊寅日周年生子人财大旺，三才进旺',
                    '壬寅日人财大旺半年生子三年出贵发科甲',
                ],
                'jinji': '宜：丑寅辰未申戌年元辰相生比和大利\n忌：子卯巳午餐酉亥年元气相克凶',
                'score': 7.5, 'usable': True
            },
            '甲山': {
                'name': '甲山', 'wuxing': '水', 'yuan_chen': '丙辛',
                'description': '甲山最要丙辛升，戊癸重干不旺名',
                'duanyu': [
                    '丙辛化壬水元辰',
                    '亥卯未连财丁旺，催丁只用一丁壬',
                    '甲己破鬼丁消灭，乙庚阴府官符侵',
                    '巳酉丑年三杀点，合生元气福禄临',
                    '丙子日三年内生子，发财发秀，廿四年人财大旺',
                    '壬午日年半生二子，廿四年大旺人丁',
                    '壬辰日年半生子廿四年人财大旺',
                ],
                'jinji': '宜：山寅卯午申年元气相生比和大利\n忌：丑辰巳未戌亥年元气相克不利',
                'score': 7.0, 'usable': True
            },
            '卯山': {
                'name': '卯山', 'wuxing': '水', 'yuan_chen': '丙辛',
                'description': '卯山酉向正辛元，丙辛辅助旺元辰',
                'duanyu': [
                    '丙辛化作壬水元辰',
                    '巳酉丑局犯三杀，申子辰合合进神',
                    '甲己乙庚休出见，丁壬用一便催财',
                    '丁卯丁酉犯消灭，戊癸阴府损人丁',
                    '壬申日年半生子，廿四年人财子孙房房大发',
                    '壬辰日年半生子房房子孙大旺，廿四年人财大发',
                    '丁亥日子孙大旺，元辰合禄',
                ],
                'jinji': '宜：子寅卯午申年元气相生比和大利\n忌：丑辰巳未戌亥酉年元气相克不利',
                'score': 7.5, 'usable': True
            },
            '乙山': {
                'name': '乙山', 'wuxing': '金', 'yuan_chen': '乙庚',
                'description': '乙山辛向元辰金，乙庚相见补元辰',
                'duanyu': [
                    '乙庚化庚金元辰',
                    '最喜丁壬化木林，辛丙阴府不宜出',
                    '戊癸干来怕损丁，甲己官司多损耗',
                    '火局相逢损自峰',
                    '壬申日时发福远大，三五年发财白手起家',
                    '壬辰日三年发财白手起家发福远大妇人持家',
                    '辛卯日周年生子',
                ],
                'jinji': '宜：子寅辰午未申戌年元气相生比和大利\n忌：卯巳酉亥年元气相克不利',
                'score': 7.0, 'usable': True
            },
            '辰山': {
                'name': '辰山', 'wuxing': '金', 'yuan_chen': '乙庚',
                'description': '辰山金元忌戊癸，相配得宜生富贵',
                'duanyu': [
                    '乙庚合庚金元辰',
                    '乙庚化合到元辰，最喜丁壬财局美',
                    '丙辛廉子犯阴府，甲己贪官番化鬼',
                    '巳酉丑局不宜全，火局熬煎怎受得',
                    '庚辰日催丁富贵周年生子，元辰催贵人洋科甲',
                    '壬辰日催富贵其力最大，三五年发大财',
                    '辛卯日催丁周年生子',
                ],
                'jinji': '宜：子辰申午未亥年元气比和相生大利\n忌：寅卯酉年元气相克戌年冲山皆不利',
                'score': 7.0, 'usable': True
            },
            '巽山': {
                'name': '巽山', 'wuxing': '土', 'yuan_chen': '甲己',
                'description': '巽山乾向怕逢元，甲己阴府灾杀先',
                'duanyu': [
                    '甲己化戊土元辰',
                    '丙辛申辰多富贵，乙庚一位福绵绵',
                    '丁壬破鬼多祸咎，戊癸单干损寿元',
                    '丙子丙午消灭日，大阳天帝喜登垣',
                    '丙寅日催富贵盈栗陈陶朱比列催贵科甲',
                    '庚辰日造祠催贵人泮登科甲催丁生子',
                    '癸巳日催官合贵人禄马登科甲',
                ],
                'jinji': '宜：山丑寅辰午未申戌年元气相生比和大利\n忌：卯巳酉亥年元气相克不利',
                'score': 7.0, 'usable': True
            },
            '巳山': {
                'name': '巳山', 'wuxing': '土', 'yuan_chen': '甲己',
                'description': '巳山元土亥相冲，丁壬戊癸鬼相攻',
                'duanyu': [
                    '甲己化合戊土元辰',
                    '甲己助元人富贵，乙庚阴府莫相逢',
                    '丙辛化水为财旺，五气相生造化功',
                    '禄马贵人来助合，催官催贵捷如风',
                    '己巳日时元合禄富贵久长',
                    '庚午日时催丁生子正元禄',
                    '甲午日时财旺，百日进财周年生子',
                ],
                'jinji': '宜：丑寅午未戌年元气相生比和大利\n忌：卯酉巳亥申子辰年元气相克不利',
                'score': 8.0, 'usable': True
            },
            '丙山': {
                'name': '丙山', 'wuxing': '火', 'yuan_chen': '戊癸',
                'description': '丙山戊癸火相帮，乙庚重出发财长',
                'duanyu': [
                    '戊癸化丙火元辰',
                    '丙辛丁壬犯贪破，寅巳午局元辰旺',
                    '甲己阴府祸须防，制伏禇凶降吉祥',
                    '辰丑之年皆大吉',
                    '乙丑日时进横财',
                    '庚午日时人财昌盛',
                    '乙巳日时财丁大旺元辰禄武财生',
                ],
                'jinji': '宜：午未丑亥巳年元气相生比和大利\n忌：寅卯申酉子辰年元气相克不利',
                'score': 7.5, 'usable': True
            },
            '午山': {
                'name': '午山', 'wuxing': '火', 'yuan_chen': '戊癸',
                'description': '午山元火喜逢财，戊癸助元富贵来',
                'duanyu': [
                    '戊癸化丙火元辰',
                    '甲已子孙宜一位，乙庚财局利名开',
                    '丙辛出见损人丁，丁壬人局又多灾',
                    '寅午巳辰年大利，申酉子年莫造葬',
                    '己巳日半年生子人财大旺催丁合禄元辰',
                    '癸巳日年生子进横财元辰合禄',
                    '乙巳日时主人财大旺',
                ],
                'jinji': '宜：丑巳午未戌亥年元气相生比和大利\n忌：子年冲山寅卯申酉年元气相克不利',
                'score': 8.0, 'usable': True
            },
            '丁山': {
                'name': '丁山', 'wuxing': '木', 'yuan_chen': '丁壬',
                'description': '丁山癸向木元辰，最喜柱中有丁壬',
                'duanyu': [
                    '丁壬化甲木元辰',
                    '甲己天干财神旺，丑寅卯亥地支真',
                    '戊癸单干催贵子，乙庚阴府祸来侵',
                    '丙辛切忌申子辰，造命相生福禄频',
                    '丁卯日年半生子半纪发财二十四年人财大旺',
                    '丁丑日半年日生子三四年人财大旺十三年出贵廿四年登科甲',
                    '壬寅日周年生子三年人财大盛，十三年出贵廿四年登科甲',
                ],
                'jinji': '宜：寅巳午亥年元辰相生比和大利\n忌：丑卯酉戌年元气相克不利',
                'score': 8.5, 'usable': True
            },
            '未山': {
                'name': '未山', 'wuxing': '木', 'yuan_chen': '丁壬',
                'description': '未山丑向木元辰，最喜补元要丁壬',
                'duanyu': [
                    '丁壬化甲木元辰',
                    '甲己武财旺富贵，时令春冬补禄盈',
                    '亥卯丑寅元生旺，更祥五气合冠盈',
                    '怕逢戊癸名阴府，贪破乙庚合丙辛',
                    '丁卯日周年生子十三年出贵廿四年登科甲人财大旺',
                    '丁亥日周年生子人财大发十三年出贵廿四年出科甲',
                    '壬寅日周年生子人财大旺',
                ],
                'jinji': '宜：寅卯巳酉亥年元气相生比和大利\n忌：子丑辰午未戌年元气相克不利',
                'score': 8.0, 'usable': True
            },
            '坤山': {
                'name': '坤山', 'wuxing': '水', 'yuan_chen': '丙辛',
                'description': '坤山切忌丙同辛，阴府克山有祸侵',
                'duanyu': [
                    '丙辛化壬水元辰',
                    '戊癸局全多富贵，丁壬一位正催丁',
                    '乙庚贪鬼尤当忌，甲己相逢实杀人',
                    '消灭庚子及庚午，合局之年任择评',
                    '壬午日周年生子五六年人财大旺十三年发科甲',
                    '壬辰日财丁大旺，周年生子廿四年富比陶贵朱',
                    '壬子日年半生二子廿四年人财大旺房房大发富上吉',
                ],
                'jinji': '宜：子卯巳午酉年元气相生比和大利\n忌：丑寅辰未申戌年元气相克不利',
                'score': 7.5, 'usable': True
            },
            '申山': {
                'name': '申山', 'wuxing': '水', 'yuan_chen': '丙辛',
                'description': '申山又怕助元辰，阴府排来畏丙辛',
                'duanyu': [
                    '丙辛化壬水元辰',
                    '戊癸双全财大旺，丁壬一字可催丁',
                    '甲己乙庚休出现，子申午戊旺财生',
                    '太阳天帝同来助，定产金门富贵人',
                    '壬申日百子千孙催丁生子富贵上吉',
                    '壬午日催丁生子廿四年人财大旺房房兴发',
                    '壬辰日催丁生子廿四年大旺房房好元辰',
                ],
                'jinji': '宜：子巳年酉年元气相生比和大利\n忌：丑寅辰未申戌年元气相克不利',
                'score': 7.0, 'usable': True
            },
            '庚山': {
                'name': '庚山', 'wuxing': '金', 'yuan_chen': '乙庚',
                'description': '庚山甲向元辰金，最喜乙庚补元辰',
                'duanyu': [
                    '乙庚化庚金元辰',
                    '催富丁壬财局美，丙辛一位速催丁',
                    '甲己辰戌贪消灭，戊癸破鬼阴府侵',
                    '巳酉未申元坐旺，寅午戌局损子孙',
                    '庚辰日财丁周年生子发财四五年财丁大旺',
                    '乙酉日催财丁大旺周年生子四五年大进横财',
                    '丙申日催丁富贵禄元辰生人财大旺富贵长久',
                ],
                'jinji': '宜：丑寅辰申酉戌年元气相生比和大利\n忌：子巳午亥午元气相克不利',
                'score': 8.0, 'usable': True
            },
            '酉山': {
                'name': '酉山', 'wuxing': '金', 'yuan_chen': '乙庚',
                'description': '酉山切莫补元辰，乙庚阴府定相刑',
                'duanyu': [
                    '乙庚化庚金元辰',
                    '丙辛单干催贵子，丁壬合局旺财神',
                    '甲己辰戌贪消灭，戊癸相交定杀人',
                    '亥卯未年犯三杀，辰巳申酉振家声',
                    '壬申日催丁生子富贵白手成家三四年大发财',
                    '乙酉日催财丁大旺正阴府',
                    '壬辰日白手成家三四年发财妇人撑持大发财',
                ],
                'jinji': '宜：丑寅辰未申酉戌年元气相生比和大利\n忌：子巳午亥年元气相克卯年冲山皆不利',
                'score': 7.0, 'usable': True
            },
            '辛山': {
                'name': '辛山', 'wuxing': '土', 'yuan_chen': '甲己',
                'description': '辛山乙向忌元辰，甲己单干不敢侵',
                'duanyu': [
                    '甲己化戊土元辰',
                    '戊寅戊申犯消灭，丙辛财局旺金银',
                    '乙庚一位催贵子，用有二干损子孙',
                    '寅午丑辰发富贵，丁壬戊癸祸临门',
                    '甲子日百日进财周年生子',
                    '丙寅日财盛人旺',
                    '庚辰日旺人丁生子造书房催贵',
                ],
                'jinji': '宜：丑辰巳酉戌年元气相生比和大利\n忌：子寅午申年元气相克不利',
                'score': 7.5, 'usable': True
            },
            '戌山': {
                'name': '戌山', 'wuxing': '土', 'yuan_chen': '甲己',
                'description': '戌山辰向土元辰，甲己二干补精神',
                'duanyu': [
                    '甲己化戊土元辰',
                    '丙辛化合催财富，乙庚单见可催丁',
                    '亥卯未年犯三岁，破鬼阴府共丁壬',
                    '戊癸单干休入局，官符口舌定相侵',
                    '甲子日催财进财周年生子',
                    '甲戌日百日进财周年生子',
                    '庚寅日人财大盛旺',
                ],
                'jinji': '宜：丑午未申酉戌年元气相生比大和大利\n忌：子巳午亥年元气相克辰年冲山不利',
                'score': 7.5, 'usable': True
            },
            '乾山': {
                'name': '乾山', 'wuxing': '火', 'yuan_chen': '戊癸',
                'description': '乾山巽向火元辰，癸戊辅元富贵临',
                'duanyu': [
                    '戊癸化丙火元辰',
                    '甲己单干催贵子，乙庚阴府祸相侵',
                    '丙辛丑未消灭破，贪官切忌犯丁壬',
                    '寅午巳未支最吉，天地到乾万事成',
                    '甲子日催丁生子',
                    '戊辰日催丁财大旺周年进横财生贵子',
                    '庚寅日催财得寡妇日进人口',
                ],
                'jinji': '宜：子丑寅辰午未申戌年元气相生比和大利\n忌：卯巳酉亥年元气不和相克不利',
                'score': 8.0, 'usable': True
            },
            '亥山': {
                'name': '亥山', 'wuxing': '火', 'yuan_chen': '戊癸',
                'description': '亥山巳向元辰火，最喜乙庚财旺好',
                'duanyu': [
                    '戊癸化火元辰',
                    '甲巳单干贵子孙，戊本双全犯阴府',
                    '破鬼原来用丙辛，丁壬出现家贫苦',
                    '甲子日催丁生子',
                    '乙丑日催富贵进横财人口大旺',
                    '庚子日催丁大旺',
                ],
                'jinji': '宜：子丑寅辰午未申戌年元气相生比和大利\n忌：卯巳酉亥四年元气相克不和不利',
                'score': 8.0, 'usable': True
            },
        }
    
    def get_shan_jia(self, shan_jia_name: str) -> dict:
        """获取山家信息"""
        return self.shan_jia_data.get(shan_jia_name, None)
    
    def get_all_shan_jia_names(self) -> list:
        """获取所有山家名称"""
        return list(self.shan_jia_data.keys())
    
    def get_shan_jia_score(self, shan_jia_name: str) -> float:
        """获取山家吉凶评分（10 分制）"""
        shan_jia = self.get_shan_jia(shan_jia_name)
        if shan_jia:
            return shan_jia.get('score', 5.0)
        return 0.0
    
    def is_shan_jia_usable(self, shan_jia_name: str) -> bool:
        """判断山家是否可用（5 分以上为可用）"""
        score = self.get_shan_jia_score(shan_jia_name)
        return score >= 5.0
    
    def get_score_description(self, score: float) -> str:
        """根据评分返回吉凶描述"""
        if score >= 9.0:
            return "上上大吉"
        elif score >= 8.0:
            return "上吉"
        elif score >= 7.0:
            return "中吉"
        elif score >= 6.0:
            return "小吉"
        elif score >= 5.0:
            return "吉凶参半"
        elif score >= 4.0:
            return "小凶"
        elif score >= 3.0:
            return "中凶"
        elif score >= 2.0:
            return "大凶"
        else:
            return "上凶"
    
    def analyze_shan_jia(self, shan_jia_name: str) -> str:
        """分析山家课格"""
        shan_jia = self.get_shan_jia(shan_jia_name)
        if not shan_jia:
            return f"未找到山家：{shan_jia_name}"
        
        score = shan_jia.get('score', 5.0)
        usable = shan_jia.get('usable', True)
        score_desc = self.get_score_description(score)
        
        report = []
        report.append("=" * 70)
        report.append(f"斗首二十四山：{shan_jia['name']}")
        report.append("=" * 70)
        report.append(f"\n【吉凶评分】{score:.1f}分 - {score_desc} {'✓ 可用' if usable else '✗ 不建议使用'}")
        report.append(f"\n【五行】{shan_jia['wuxing']}")
        report.append(f"\n【元辰】{shan_jia['yuan_chen']}")
        report.append(f"\n【课格】{shan_jia['description']}\n")
        report.append("【断语】")
        for i, duanyu in enumerate(shan_jia['duanyu'], 1):
            report.append(f"  {i}. {duanyu}")
        report.append(f"\n【禁忌】{shan_jia['jinji']}")
        report.append("=" * 70)
        
        return "\n".join(report)


def test_shan_jia():
    """测试二十四山课格系统"""
    analyzer = DouShouShanJiaKeGe()
    
    print("\n可用的山家：")
    for name in analyzer.get_all_shan_jia_names():
        score = analyzer.get_shan_jia_score(name)
        usable = analyzer.is_shan_jia_usable(name)
        desc = analyzer.get_score_description(score)
        print(f"  {name}: {score:.1f}分 ({desc}) {'✓' if usable else '✗'}")
    
    # 测试壬山
    print("\n" + "=" * 70)
    print("测试：壬山")
    print("=" * 70)
    report = analyzer.analyze_shan_jia('壬山')
    print(report)


if __name__ == '__main__':
    test_shan_jia()
