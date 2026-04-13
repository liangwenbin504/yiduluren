#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
仪度六壬择日系统 - API服务器
完整版本，包含所有API端点
"""

import io
import sys
import os

# 定义项目根目录（必须在其他代码之前）
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

# PythonAnywhere 环境下不使用文件日志，直接输出到控制台
# _log_file = open('api_server.log', 'w', encoding='utf-8')

def log_print(msg):
    """日志输出函数 - PythonAnywhere环境下直接输出到控制台"""
    print(msg)
    # PythonAnywhere 会自动捕获 print 输出到日志文件
    # if '_log_file' in globals():
    #     _log_file.write(str(msg) + '\n')
    #     _log_file.flush()

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import sys
from datetime import datetime
import traceback

# 尝试导入win32com用于修复文档
try:
    import win32com.client as win32
    import pythoncom
    WIN32COM_AVAILABLE = True
except ImportError:
    WIN32COM_AVAILABLE = False


def fix_document_seal_after_export(doc_path):
    """导出文档后，立即修复印章图片，强制设置为浮于文字上方"""
    if not WIN32COM_AVAILABLE:
        print("⚠️  win32com不可用，跳过文档修复")
        return False
    
    try:
        print(f"🔧 自动修复文档印章: {os.path.basename(doc_path)}")
        
        # 初始化 COM（多线程环境必须）
        try:
            pythoncom.CoInitialize()
            print("  - COM已初始化")
        except:
            pass
        
        # 启动Word
        word = win32.Dispatch("Word.Application")
        word.Visible = False
        word.DisplayAlerts = 0
        
        try:
            # 打开文档
            doc = word.Documents.Open(os.path.abspath(doc_path))
            
            print(f"  - 找到 {doc.InlineShapes.Count} 个嵌入型图片")
            print(f"  - 找到 {doc.Shapes.Count} 个浮动图片")
            
            # 1. 转换所有嵌入型图片为浮动
            for i in range(doc.InlineShapes.Count, 0, -1):
                try:
                    inline_shape = doc.InlineShapes(i)
                    if inline_shape.Type == 3:  # wdInlineShapePicture
                        print(f"    - 转换嵌入型图片 {i} 为浮动型")
                        shape = inline_shape.ConvertToShape()
                        shape.WrapFormat.Type = 3  # wdWrapFront
                        shape.ZOrder(0)
                        print(f"    - 图片 {i} 已设置为浮于文字上方")
                except Exception as e:
                    print(f"    ⚠️  转换图片 {i} 时出错: {e}")
            
            # 2. 确保所有浮动图片都是浮于文字上方
            for i in range(1, doc.Shapes.Count + 1):
                try:
                    shape = doc.Shapes(i)
                    shape.WrapFormat.Type = 3  # wdWrapFront
                    shape.ZOrder(0)
                    print(f"    - 浮动图片 {i} 已确认为浮于文字上方 (Type=3, ZOrder=0)")
                except Exception as e:
                    print(f"    ⚠️  设置图片 {i} 时出错: {e}")
            
            # 保存文档
            doc.Save()
            doc.Close()
            print(f"✅ 文档印章修复完成: {os.path.basename(doc_path)}")
            return True
            
        except Exception as e:
            print(f"❌ 修复失败: {e}")
            traceback.print_exc()
            return False
        finally:
            try:
                word.Quit()
            except:
                pass
            
    except Exception as e:
        print(f"❌ 发生错误: {e}")
        traceback.print_exc()
        return False

# 添加核心模块路径（只从 engine/ 目录导入）
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'engine'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'core_modules'))

app = Flask(__name__)
CORS(app)

# ==================== 导入引擎模块 ====================
try:
    from sizhu_engine import get_sizhu, get_year_ganzhi, get_month_ganzhi, get_day_ganzhi, get_hour_ganzhi
    print("✅ sizhu_engine 导入成功")
except Exception as e:
    print(f"❌ sizhu_engine 导入失败: {e}")
    get_sizhu = None

try:
    from douhou_analyzer import DouhouKegeAnalyzer
    print("✅ douhou_analyzer 导入成功")
except Exception as e:
    print(f"❌ douhou_analyzer 导入失败: {e}")
    DouhouKegeAnalyzer = None

try:
    from yanqin_analyzer import YanQinAnalyzer
    print("✅ yanqin_analyzer 导入成功")
except Exception as e:
    print(f"❌ yanqin_analyzer 导入失败: {e}")
    YanQinAnalyzer = None

try:
    from sike_sanchuan_engine import SiKeSanChuanCalculator
    print("✅ sike_sanchuan_engine 导入成功")
except Exception as e:
    print(f"❌ sike_sanchuan_engine 导入失败: {e}")
    SiKeSanChuanCalculator = None

try:
    from daliuren_engine import DaLiuRenEngine
    print("✅ daliuren_engine 导入成功")
except Exception as e:
    print(f"❌ daliuren_engine 导入失败: {e}")
    DaLiuRenEngine = None

try:
    from kejing_scoring import KeJingScoring
    print("✅ kejing_scoring 导入成功")
except Exception as e:
    print(f"❌ kejing_scoring 导入失败: {e}")
    KeJingScoring = None

try:
    from daliuren_luma_guiren import DaLiuRenLuMaGuiRen
    print("✅ daliuren_luma_guiren 导入成功")
except Exception as e:
    print(f"❌ daliuren_luma_guiren 导入失败: {e}")
    DaLiuRenLuMaGuiRen = None

try:
    from engine.kekeduanyu import KeKeDuanyu
    print("✅ kekeduanyu 导入成功")
except Exception as e:
    print(f"❌ kekeduanyu 导入失败: {e}")
    KeKeDuanyu = None

try:
    from gui_ren_engine import GuiRenCalculator
    print("✅ gui_ren_engine 导入成功")
except Exception as e:
    print(f"❌ gui_ren_engine 导入失败: {e}")
    GuiRenCalculator = None

try:
    from comprehensive_scorer import ComprehensiveScorer
    print("✅ comprehensive_scorer 导入成功")
except Exception as e:
    print(f"❌ comprehensive_scorer 导入失败: {e}")
    ComprehensiveScorer = None

# ==================== 导入导出模块 ====================
# 优先使用python-docx版本（更稳定）
try:
    from export_docx_docx import export_docx_document
    print("✅ export_docx_docx 导入成功（python-docx版本）")
except Exception as e:
    print(f"⚠️ export_docx_docx 导入失败: {e}，尝试导入win32com版本...")
    try:
        from export_docx import export_docx_document
        print("✅ export_docx 导入成功（win32com版本）")
    except Exception as e2:
        print(f"❌ export_docx 导入失败: {e2}")
        export_docx_document = None

# ==================== 导入断语库模块 ====================
try:
    from liuren_keti_duanyu import LiuRenKetiDuanyu
    print("✅ liuren_keti_duanyu 导入成功")
    LiuRenKetiDuanyu_Instance = LiuRenKetiDuanyu()
except Exception as e:
    print(f"❌ liuren_keti_duanyu 导入失败: {e}")
    LiuRenKetiDuanyu_Instance = None

try:
    from engine.ai_evaluation import AIEvaluation
    print("✅ ai_evaluation 导入成功")
    # 通义千问 API Key 配置
    QWEN_API_KEY = "***REMOVED***"
    AIEvaluation_Instance = AIEvaluation(enable_ai=True, api_key=QWEN_API_KEY)
    print(f"✅ 通义千问AI评价已启用: {AIEvaluation_Instance.ai_available}")
except Exception as e:
    print(f"❌ ai_evaluation 导入失败: {e}")
    AIEvaluation_Instance = None

# ==================== 全局辅助函数 ====================
def arrange_tiandi_pan(yuejiang, shichen):
    """默认天地盘布局函数"""
    return {'天盘': {}, '地盘': {}}

# 尝试导入完整的天地盘布局生成器
try:
    from src.utils.dizhi_layout_generator import arrange_tiandi_pan as import_arrange_tiandi_pan
    arrange_tiandi_pan = import_arrange_tiandi_pan
except ImportError:
    pass

# ==================== API端点 ====================

@app.route('/')
def index():
    """首页"""
    return send_from_directory('.', 'index.html')

@app.route('/<path:filename>')
def serve_static(filename):
    """静态文件服务"""
    try:
        import urllib.parse
        filename = urllib.parse.unquote(filename)
        # 使用 PROJECT_ROOT 绝对路径
        file_path = os.path.join(PROJECT_ROOT, filename)
        if os.path.exists(file_path):
            return send_from_directory(PROJECT_ROOT, filename)
        else:
            return jsonify({'error': 'File not found', 'path': file_path}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """健康检查"""
    return jsonify({
        'status': 'ok',
        'timestamp': datetime.now().isoformat(),
        'server': '仪度六壬择日 API服务器',
        'modules': {
            'SiKeSanChuanCalculator': SiKeSanChuanCalculator is not None,
            'KeJingScoring': KeJingScoring is not None,
            'DouhouKegeAnalyzer': DouhouKegeAnalyzer is not None,
            'YanQinAnalyzer': YanQinAnalyzer is not None
        }
    })

@app.route('/api/sizhu', methods=['GET'])
def calculate_sizhu():
    """计算四柱"""
    try:
        year = int(request.args.get('year', 2026))
        month = int(request.args.get('month', 1))
        day = int(request.args.get('day', 1))
        hour = int(request.args.get('hour', 12))
        
        # 将小时转换为时辰
        # 时辰对照表
        shichen_map = {
            23: '子', 0: '子',
            1: '丑', 2: '丑',
            3: '寅', 4: '寅',
            5: '卯', 6: '卯',
            7: '辰', 8: '辰',
            9: '巳', 10: '巳',
            11: '午', 12: '午',
            13: '未', 14: '未',
            15: '申', 16: '申',
            17: '酉', 18: '酉',
            19: '戌', 20: '戌',
            21: '亥', 22: '亥'
        }
        shichen = shichen_map.get(hour, '午')
        
        if get_sizhu is None:
            return jsonify({'error': 'sizhu_engine 未加载'}), 500
        
        result = get_sizhu(year, month, day, shichen)
        
        # 转换为主界面期望的格式
        sizhu_data = {
            'yearPillar': result.get('年柱', ''),
            'monthPillar': result.get('月柱', ''),
            'dayPillar': result.get('日柱', ''),
            'hourPillar': result.get('时柱', ''),
            'yearGan': result.get('年柱', '')[0] if result.get('年柱') else '',
            'yearZhi': result.get('年柱', '')[1] if result.get('年柱') else '',
            'monthGan': result.get('月柱', '')[0] if result.get('月柱') else '',
            'monthZhi': result.get('月柱', '')[1] if result.get('月柱') else '',
            'dayGan': result.get('日柱', '')[0] if result.get('日柱') else '',
            'dayZhi': result.get('日柱', '')[1] if result.get('日柱') else '',
            'hourGan': result.get('时柱', '')[0] if result.get('时柱') else '',
            'hourZhi': result.get('时柱', '')[1] if result.get('时柱') else ''
        }
        
        return jsonify({
            'success': True,
            'sizhu': sizhu_data,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        print(f"❌ 计算四柱失败: {e}")
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/doushou/full_analyze', methods=['POST'])
def doushou_full_analyze():
    """斗首完整分析"""
    try:
        data = request.json
        
        if DouhouKegeAnalyzer is None:
            return jsonify({'error': 'douhou_analyzer 未加载'}), 500
        
        # 提取参数
        mountain = data.get('mountain', '')
        sizhu = data.get('sizhu', {})
        
        # 如果没有提供四柱，尝试从日期列表中提取
        if not sizhu and 'dates' in data and len(data['dates']) > 0:
            first_date = data['dates'][0]
            sizhu = {
                '年柱': first_date.get('year_pillar', ''),
                '月柱': first_date.get('month_pillar', ''),
                '日柱': first_date.get('day_pillar', ''),
                '时柱': first_date.get('hour_pillar', '')
            }
        
        analyzer = DouhouKegeAnalyzer()
        result = analyzer.analyze_kege(mountain, sizhu)
        
        return jsonify({
            'success': True,
            'result': result,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        print(f"❌ 斗首分析失败: {e}")
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

def calculate_mubiao_bonus(mubiao, doushou_result, daliuren_result, luma_guiren_info, mountain):
    """计算目标匹配奖励分数和仪度六壬综合评分
    mubiao: 目标列表 ['求官', '求财', '求富贵', '求子', '求学问', '求婚姻']
    doushou_result: 斗首分析结果
    daliuren_result: 大六壬结果 (sizhu_result)
    luma_guiren_info: 禄马贵人信息
    mountain: 坐山
    返回: (bonus_score, matched_mubiao_list, yidu_score_result)
    """
    bonus = 0
    matched = []
    yidu_score_result = None

    if not KeKeDuanyu:
        return 0, [], None

    yidu_score_result = KeKeDuanyu.analyze_yidu_score(
        mountain=mountain,
        sizhu=daliuren_result,
        doushou_result=doushou_result,
        luma_guiren_info=luma_guiren_info,
        mubiao=mubiao
    )

    bonus = yidu_score_result.get('综合评分', 0)
    matched = []

    if mubiao:
        doushou_patterns = doushou_result.get('课格格局', [])
        doushou_pattern_str = ' '.join(doushou_patterns) if doushou_patterns else ''

        for m in mubiao:
            if m == '求官':
                if '禄马贵人' in yidu_score_result.get('评价', '') or '官' in doushou_pattern_str:
                    matched.append('求官')
            elif m == '求财':
                if '武财' in doushou_pattern_str or '财' in doushou_pattern_str:
                    matched.append('求财')
            elif m == '求富贵':
                if yidu_score_result.get('综合评分', 0) >= 40:
                    matched.append('求富贵')
            elif m == '求子':
                if yidu_score_result.get('综合评分', 0) >= 30:
                    matched.append('求子')
            elif m == '求学问' or m == '求文昌':
                if '朱雀' in str(yidu_score_result.get('课传美格', [])):
                    matched.append('求学问')
            elif m == '求婚姻':
                if yidu_score_result.get('综合评分', 0) >= 30:
                    matched.append('求婚姻')

    return bonus, matched, yidu_score_result

@app.route('/api/doushou/full_range_analyze', methods=['POST'])
def doushou_full_range_analyze():
    """完整日期范围分析 - 使用测试成功的逻辑"""
    try:
        data = request.json
        
        mountain = data.get('mountain', '子山')
        start_date_str = data.get('start_date', '2026-01-01')
        end_date_str = data.get('end_date', '2026-12-31')
        min_daliuren_score = data.get('min_daliuren_score', 70)
        max_results = data.get('max_results', 10)
        mubiao = data.get('mubiao', [])

        log_print(f"[DEBUG] 完整日期范围分析: {start_date_str} 至 {end_date_str}")
        log_print(f"[DEBUG] 坐山: {mountain}")
        log_print(f"[DEBUG] 用户目标: {mubiao}")
        
        from datetime import datetime, timedelta
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
        except Exception as e:
            return jsonify({'error': f'日期格式错误: {e}'}), 400
        
        # 初始化
        douhou_analyzer = DouhouKegeAnalyzer()
        sike_calc = SiKeSanChuanCalculator()
        kejing_scorer = KeJingScoring()
        yanqin_analyzer = YanQinAnalyzer()
        luma_guiren_calc = DaLiuRenLuMaGuiRen()
        
        # 完整的天地盘函数
        def arrange_tiandi_pan_local(yuejiang: str, shichen: str) -> dict:
            DIZHI_LOCAL = ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥']
            shi_index = DIZHI_LOCAL.index(shichen)
            yuejiang_index = DIZHI_LOCAL.index(yuejiang)
            zi_position = (shi_index - yuejiang_index) % 12
            tian_pan = []
            for i in range(12):
                tian_index = (i - zi_position) % 12
                tian_pan.append(DIZHI_LOCAL[tian_index])
            result = {}
            for i in range(12):
                result[DIZHI_LOCAL[i]] = tian_pan[i]
            return result
        
        # 节气日期
        ZHONGQI_DATES = [
            (1, 20, '子'),
            (2, 19, '亥'),
            (3, 21, '戌'),
            (4, 20, '酉'),
            (5, 21, '申'),
            (6, 21, '未'),
            (7, 23, '午'),
            (8, 23, '巳'),
            (9, 23, '辰'),
            (10, 24, '卯'),
            (11, 22, '寅'),
            (12, 22, '丑'),
        ]
        
        # 时辰列表
        shichen_list = ['子', '丑', '寅', '卯', '辰', '巳', 
                       '午', '未', '申', '酉', '戌', '亥']
        
        # 时辰映射
        shichen_map = {
            23: '子', 0: '子',
            1: '丑', 2: '丑',
            3: '寅', 4: '寅',
            5: '卯', 6: '卯',
            7: '辰', 8: '辰',
            9: '巳', 10: '巳',
            11: '午', 12: '午',
            13: '未', 14: '未',
            15: '申', 16: '申',
            17: '酉', 18: '酉',
            19: '戌', 20: '戌',
            21: '亥', 22: '亥'
        }
        
        # 月柱六相优先级
        LIUXIANG_PRIORITY = {
            '武财': 5,
            '元辰': 4,
            '廉贞': 3,
            '贪官': 2,
            '破鬼': 1
        }
        
        results = []
        current_date = start_date
        total_days = 0
        total_candidates = 0
        total_shichen = 0
        first_iteration = True
        mountain_char = mountain[0] if mountain else '子'
        
        log_print(f"[DEBUG] 开始筛选...")
        
        while current_date <= end_date:
            date_str = current_date.strftime('%Y-%m-%d')
            
            for shichen in shichen_list:
                try:
                    # 获取四柱
                    year = current_date.year
                    month = current_date.month
                    day = current_date.day
                    hour = shichen_list.index(shichen) * 2
                    shichen_for_sizhu = shichen_map.get(hour, '午')
                    sizhu_result = get_sizhu(year, month, day, shichen_for_sizhu)
                    
                    # 斗首分析
                    doushou_result = douhou_analyzer.analyze_kege(mountain_char, sizhu_result)
                    doushou_score = doushou_result.get('综合评分', 50)
                    doushou_patterns = doushou_result.get('课格格局', [])
                    doushou_duanyu = doushou_result.get('吉凶断语', [])
                    
                    liuxiang_analysis = doushou_result.get('六相六替分析', {})
                    sizhu_liuxiang = liuxiang_analysis.get('四柱六相', {})
                    yuezhu_info = sizhu_liuxiang.get('月柱', {})
                    yuezhu_liuxiang = yuezhu_info.get('六相', '')
                    yuezhu_liuxiang_priority = LIUXIANG_PRIORITY.get(yuezhu_liuxiang, 0)
                    
                    # 大六壬评分
                    daliuren_score = 50
                    daliuren_keti = '--'
                    daliuren_detail = None
                    luma_guiren_info = None
                    is_daxiong = False
                    is_qualified = False
                    qualification_status = ''
                    
                    ri_gan = sizhu_result.get('日柱', '甲子')[0]
                    ri_zhi = sizhu_result.get('日柱', '甲子')[1]
                    
                    # 计算月将
                    yuejiang = '子'
                    for m, d, yj in ZHONGQI_DATES:
                        if (current_date.month > m) or (current_date.month == m and current_date.day >= d):
                            yuejiang = yj
                    
                    # 天地盘
                    tiandi_pan = arrange_tiandi_pan_local(yuejiang, shichen)
                    
                    # 四课三传
                    sike = sike_calc.qi_sike(ri_gan, ri_zhi, tiandi_pan)
                    sanchuan = sike_calc.fa_sanchuan(sike, ri_gan, ri_zhi, tiandi_pan)
                    keti = sanchuan.get('课体', '')
                    daliuren_keti = keti
                    
                    # 课经评分
                    keti_name = keti.replace('课', '') if keti else ''
                    kejing_score = kejing_scorer.calculate_score(keti_name) * 10
                    
                    daliuren_detail = {
                        '课体': keti,
                        '三传': sanchuan,
                        '起法': sanchuan.get('起法', '')
                    }
                    
                    # 禄马贵人评分
                    nian_gan = sizhu_result.get('年柱', '甲子')[0]
                    nian_zhi = sizhu_result.get('年柱', '甲子')[1]
                    yue_gan = sizhu_result.get('月柱', '甲子')[0]
                    yue_zhi = sizhu_result.get('月柱', '甲子')[1]
                    shi_gan = sizhu_result.get('时柱', '甲子')[0]
                    shi_zhi = sizhu_result.get('时柱', '甲子')[1]
                    
                    new_score_result = luma_guiren_calc.calculate_new_score(
                        mountain_char, shichen,
                        nian_gan, nian_zhi,
                        yue_gan, yue_zhi,
                        ri_gan, ri_zhi,
                        shi_gan, shi_zhi,
                        sanchuan,
                        [keti] if keti else None
                    )
                    
                    daliuren_score = new_score_result['final_score']
                    is_daxiong = new_score_result['is_daxiong']
                    is_qualified = not is_daxiong and daliuren_score >= min_daliuren_score
                    qualification_status = new_score_result['status']
                    
                    luma_guiren_info = {
                        'qualified_count': new_score_result['pillar_qualified_count'],
                        'status': new_score_result['status'],
                        'nian_qualified': new_score_result['nian_qualified'],
                        'yue_qualified': new_score_result['yue_qualified'],
                        'ri_qualified': new_score_result['ri_qualified'],
                        'shi_qualified': new_score_result['shi_qualified'],
                        'sanchuan_luma_count': new_score_result['sanchuan_luma_count'],
                        'sanchuan_qualified': new_score_result['sanchuan_qualified'],
                        'is_qualified': is_qualified,
                        'qualification_status': qualification_status,
                        'ri_luma_guiren_in_sanchuan': new_score_result['sanchuan_luma_count'] >= 1,
                        'double_qualified_count': new_score_result['pillar_qualified_count'],
                        'ke_ti_level': new_score_result['ke_ti_level'],
                        'ke_ti_deduction': new_score_result['ke_ti_deduction'],
                        'is_daxiong': is_daxiong
                    }
                    
                    # 演禽评分
                    yanqin_score = 50
                    yanqin_info = '--'
                    year_zhi = sizhu_result.get('年柱', '甲子')[1]
                    month_zhi = sizhu_result.get('月柱', '甲子')[1]
                    day_zhi = sizhu_result.get('日柱', '甲子')[1]
                    hour_zhi = sizhu_result.get('时柱', '甲子')[1]
                    
                    yanqin_result = yanqin_analyzer.analyze_four_qin(year_zhi, month_zhi, day_zhi, hour_zhi)
                    if yanqin_result:
                        yanqin_score = yanqin_result.get('综合评分', 50)
                        yanqin_info = f"{yanqin_result.get('四禽禽星', {}).get('日禽星', '--')}"
                    
                    # 第一个日期的调试信息
                    if first_iteration:
                        log_print(f"[DEBUG] 第一个日期: {date_str} {shichen}")
                        log_print(f"  - 斗首评分: {doushou_score}")
                        log_print(f"  - 大六壬评分: {daliuren_score}, 课体: {keti}")
                        log_print(f"  - 演禽评分: {yanqin_score}")
                        first_iteration = False
                    
                    # 计算总分
                    total_score = (doushou_score + daliuren_score + yanqin_score) / 3
                    
                    # 筛选条件
                    doushou_ok = doushou_score >= 50
                    daliuren_ok = daliuren_score >= min_daliuren_score
                    yanqin_ok = yanqin_score >= 50
                    
                    if is_daxiong:
                        continue
                    
                    if doushou_ok and daliuren_ok and yanqin_ok:
                        total_candidates += 1

                        mubiao_bonus = 0
                        matched_mubiao = []
                        yidu_score_result = None
                        if mubiao:
                            mubiao_bonus, matched_mubiao, yidu_score_result = calculate_mubiao_bonus(
                                mubiao, doushou_result, sizhu_result, luma_guiren_info, mountain
                            )

                        results.append({
                            'date': date_str,
                            'shichen': shichen,
                            'sizhu': sizhu_result,
                            'doushou_score': doushou_score,
                            'daliuren_score': daliuren_score,
                            'yanqin_score': yanqin_score,
                            'total_score': total_score,
                            'daliuren_keti': daliuren_keti,
                            'yanqin_info': yanqin_info,
                            'patterns': doushou_patterns,
                            'duanyu': doushou_duanyu,
                            'daliuren_detail': daliuren_detail,
                            'mountain': mountain,
                            'yuezhu_liuxiang': yuezhu_liuxiang,
                            'yuezhu_liuxiang_priority': yuezhu_liuxiang_priority,
                            'is_qualified': daliuren_ok,
                            'qualification_status': qualification_status,
                            'ri_luma_guiren_in_sanchuan': new_score_result['sanchuan_luma_count'] >= 1,
                            'luma_guiren_info': luma_guiren_info,
                            'mubiao_bonus': mubiao_bonus,
                            'matched_mubiao': matched_mubiao,
                            'yidu_score': yidu_score_result
                        })
                        
                        log_print(f"✅ 找到吉期: {date_str} {shichen} - 斗首: {doushou_score}, 六壬: {daliuren_score}, 演禽: {yanqin_score}, 总分: {total_score:.1f}")
                    
                    total_shichen += 1
                
                except Exception as e:
                    log_print(f"❌ 处理 {date_str} {shichen} 时出错: {e}")
                    import traceback
                    traceback.print_exc()
                    continue
            
            total_days += 1
            current_date += timedelta(days=1)
        
        log_print(f"[DEBUG] 共遍历: {total_days} 天, {total_shichen} 个时辰")
        log_print(f"[DEBUG] 找到候选: {total_candidates} 个吉期")
        log_print(f"[DEBUG] 结果数: {len(results)}")

        def sort_key(x):
            has_mubiao = len(x.get('matched_mubiao', [])) > 0 if mubiao else False
            return (
                -x['yuezhu_liuxiang_priority'],
                -x['doushou_score'],
                -int(has_mubiao),
                -x.get('mubiao_bonus', 0),
                x['date'],
                -x['total_score']
            )

        results.sort(key=sort_key)
        results = results[:max_results]
        
        return jsonify({
            'success': True,
            'results': results,
            'total_days': total_days,
            'total_candidates': total_candidates,
            'filter_rules': {
                '六壬评分标准': f'大六壬评分 >= {min_daliuren_score}（满分100：四柱禄马贵人全到山到向+三传禄马贵人之二；每少一项扣3分）',
                '课体扣分规则': '上上吉/上吉/中吉课不扣分，小吉课扣5分，平课扣15分（最终<=70），小凶课扣35分，中凶课扣40分（最终<=50），大凶课直接排除',
                '斗首评分标准': '斗首评分 >= 50（不凶即可）',
                '演禽评分标准': '演禽评分 >= 50（放宽条件）',
                '月柱六相优先': '武财>元辰>廉贞>贪官>破鬼'
            },
            'score_weights': {
                '斗首': 0.3,
                '大六壬': 0.4,
                '演禽': 0.3
            },
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        log_print(f"[ERROR] 完整日期范围分析失败: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/yanqin/four_qin', methods=['GET'])
def yanqin_four_qin():
    """演禽四禽分析"""
    try:
        year_zhi = request.args.get('year_zhi', '子')
        month_zhi = request.args.get('month_zhi', '寅')
        day_zhi = request.args.get('day_zhi', '子')
        hour_zhi = request.args.get('hour_zhi', '子')
        
        if YanQinAnalyzer is None:
            return jsonify({'error': 'yanqin_analyzer 未加载'}), 500
        
        analyzer = YanQinAnalyzer()
        result = analyzer.analyze_four_qin(year_zhi, month_zhi, day_zhi, hour_zhi)
        
        return jsonify({
            'success': True,
            'data': result,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        print(f"❌ 演禽分析失败: {e}")
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/tiandipan', methods=['GET'])
def calculate_tiandipan():
    """计算天地盘"""
    try:
        year = int(request.args.get('year', 2026))
        month = int(request.args.get('month', 1))
        day = int(request.args.get('day', 1))
        hour = int(request.args.get('hour', 12))
        
        if SiKeSanChuanCalculator is None:
            return jsonify({'error': 'sike_sanchuan_engine 未加载'}), 500
        
        calculator = SiKeSanChuanCalculator()
        result = calculator.calculate(year, month, day, hour)
        
        return jsonify({
            'success': True,
            'data': result,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        print(f"❌ 计算天地盘失败: {e}")
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/daliuren', methods=['GET'])
def calculate_daliuren():
    """计算大六壬"""
    try:
        year = int(request.args.get('year', 2026))
        month = int(request.args.get('month', 1))
        day = int(request.args.get('day', 1))
        hour = int(request.args.get('hour', 12))
        
        if DaLiuRenEngine is None:
            return jsonify({'error': 'daliuren_engine 未加载'}), 500
        
        engine = DaLiuRenEngine()
        result = engine.calculate(year, month, day, hour)
        
        return jsonify({
            'success': True,
            'data': result,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        print(f"❌ 计算大六壬失败: {e}")
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/guiren', methods=['GET'])
def calculate_guiren():
    """计算贵人"""
    try:
        year = int(request.args.get('year', 2026))
        month = int(request.args.get('month', 1))
        day = int(request.args.get('day', 1))
        hour = int(request.args.get('hour', 12))
        
        if GuiRenCalculator is None:
            return jsonify({'error': 'gui_ren_engine 未加载'}), 500
        
        calculator = GuiRenCalculator()
        result = calculator.calculate(year, month, day, hour)
        
        return jsonify({
            'success': True,
            'data': result,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        print(f"❌ 计算贵人失败: {e}")
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/comprehensive_score', methods=['POST'])
def comprehensive_score():
    """综合评分"""
    try:
        data = request.json
        
        if ComprehensiveScorer is None:
            return jsonify({'error': 'comprehensive_scorer 未加载'}), 500
        
        scorer = ComprehensiveScorer()
        result = scorer.score(data)
        
        return jsonify({
            'success': True,
            'data': result,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        print(f"❌ 综合评分失败: {e}")
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/export/docx', methods=['POST'])
def export_docx():
    """导出 DOCX 文档"""
    try:
        data = request.json
        
        print("=" * 80)
        print("📄 收到导出请求")
        print(f"📄 请求数据: {data}")
        print("=" * 80)
        
        if export_docx_document is None:
            return jsonify({'error': 'export_docx 未加载'}), 500
        
        # 导出文档（函数内部会自己生成文件名并保存）
        print("📄 开始调用 export_docx_document...")
        result = export_docx_document(data)
        
        print(f"📄 导出结果: {result}")
        
        if result and isinstance(result, dict):
            # 检查是否成功
            if result.get('success') == False:
                return jsonify({'error': result.get('error', '导出失败')}), 500
            
            filename = result.get('filename')
            file_path = result.get('file_path')
            
            if not filename:
                return jsonify({'error': '导出失败：未生成文件名'}), 500
            
            # ========================================
            # 关键：导出后立即修复印章图片！
            # ========================================
            # if file_path and os.path.exists(file_path):
            #     print("🔧 导出完成，立即修复印章图片...")
            #     fix_document_seal_after_export(file_path)
            
            return jsonify({
                'success': True,
                'filename': filename,
                'download_url': f'/api/export/download/{filename}',
                'timestamp': datetime.now().isoformat()
            })
        else:
            return jsonify({'error': '导出文档失败：未知错误'}), 500
    except Exception as e:
        print(f"❌ 导出文档失败：{e}")
        print("=" * 80)
        print("❌ 详细错误堆栈：")
        print("=" * 80)
        traceback.print_exc()
        print("=" * 80)
        return jsonify({'error': str(e)}), 500

def _traditional_duanyu_handler():
    """获取传统断语的处理函数"""
    try:
        data = request.json
        
        if AIEvaluation_Instance is None:
            return jsonify({'error': 'ai_evaluation 未加载'}), 500
        
        # 提取参数
        keti_list = data.get('课格列表', [])
        luma_info = data.get('luma_info', None)
        daliuren_detail = data.get('daliuren_detail', None)
        doushou_kege = data.get('斗首课格', None)
        doushou_score = data.get('斗首评分', None)
        liuren_score = data.get('六壬评分', None)
        yanqin = data.get('演禽', None)
        
        print(f"📌 传统断语API调用")
        print(f"📌 课格列表: {keti_list}")
        print(f"📌 斗首课格: {doushou_kege}")
        print(f"📌 斗首评分: {doushou_score}")
        print(f"📌 六壬评分: {liuren_score}")
        print(f"📌 演禽: {yanqin}")
        
        # 生成综合断语
        traditional_duanyu_text = AIEvaluation_Instance.generate_traditional_evaluation(data)
        
        print(f"📌 生成的传统断语长度: {len(traditional_duanyu_text)}")
        print(f"📌 传统断语预览: {traditional_duanyu_text[:200]}")
        
        return jsonify({
            'success': True,
            'traditional_duanyu': traditional_duanyu_text,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        print(f"❌ 获取传统断语失败: {e}")
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/ai/traditional_duanyu', methods=['POST'])
def traditional_duanyu():
    """获取传统断语"""
    return _traditional_duanyu_handler()

@app.route('/api/ai/traditional_duanyu', methods=['POST'])
def traditional_duanyu_api():
    """获取传统断语（带/api前缀）"""
    return _traditional_duanyu_handler()

@app.route('/api/export/download/<path:filename>', methods=['GET'])
def download_docx(filename):
    """下载DOCX文档"""
    try:
        # 优先从下载文件夹查找，其次从项目目录查找
        downloads_dir = os.path.join(os.path.expanduser('~'), 'Downloads')
        project_dir = os.path.dirname(__file__)
        
        # 确保文件名正确解码
        import urllib.parse
        filename = urllib.parse.unquote(filename)
        
        # 先检查下载文件夹
        if os.path.exists(os.path.join(downloads_dir, filename)):
            directory = downloads_dir
        else:
            directory = project_dir
        
        print(f"📤 下载文档: {filename}")
        print(f"📁 目录: {directory}")
        print(f"📄 文件是否存在: {os.path.exists(os.path.join(directory, filename))}")
        return send_from_directory(directory, filename, as_attachment=True)
    except Exception as e:
        print(f"❌ 下载文档失败: {e}")
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

# ==================== 服务器启动 ====================

def start_server():
    """启动服务器"""
    print("=" * 80)
    print("仪度六壬择日系统 - API服务器")
    print("=" * 80)
    print(f"访问地址: http://localhost:5000")
    print(f"健康检查: http://localhost:5000/api/health")
    print("=" * 80)
    
    print("使用 Flask 开发服务器启动...")
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)

if __name__ == '__main__':
    start_server()
