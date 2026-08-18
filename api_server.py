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
import shutil

# 尝试导入 python-docx
try:
    from docx import Document
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False

# 尝试导入win32com用于修复文档
try:
    import win32com.client as win32
    import pythoncom
    WIN32COM_AVAILABLE = True
except ImportError:
    WIN32COM_AVAILABLE = False


def _extract_doushou_keti(doushou_result):
    """从斗首分析结果中提取课格名称"""
    if not doushou_result:
        return ''

    # 1. 优先使用 '课格' 字段
    keti = doushou_result.get('课格', '')
    if keti:
        return keti

    # 2. 使用 'keti' 字段
    keti = doushou_result.get('keti', '')
    if keti:
        return keti

    # 3. 从 '课格格局' 列表中提取第一个格局名称
    patterns = doushou_result.get('课格格局', [])
    if patterns and len(patterns) > 0:
        if isinstance(patterns[0], dict):
            return patterns[0].get('格局名称', '')
        elif isinstance(patterns[0], str):
            return patterns[0]

    # 4. 如果列表中有多个格局，组合前两个作为课格描述
    if patterns and len(patterns) > 1:
        names = []
        for p in patterns[:2]:
            if isinstance(p, dict):
                name = p.get('格局名称', '')
            else:
                name = str(p)
            if name:
                names.append(name)
        if names:
            return '、'.join(names)

    return ''


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

# 添加核心模块路径
sys.path.insert(0, PROJECT_ROOT)
sys.path.insert(0, os.path.join(PROJECT_ROOT, 'engine'))

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
    from sike_sanchuan_engine import SiKeSanChuanCalculator2
    print("✅ sike_sanchuan_engine(V2) 导入成功")
except Exception as e:
    print(f"❌ sike_sanchuan_engine 导入失败: {e}")
    SiKeSanChuanCalculator2 = None

try:
    # 三传课格检测器（玄胎/铸印/斫轮/盘珠等，仅供前端显示，不赋吉凶）
    from sanchuan_kege import SanChuanKegeDetector as SanchuanKegeDetector
    print("✅ sanchuan_kege 导入成功")
except Exception as e:
    print(f"❌ sanchuan_kege 导入失败: {e}")
    SanchuanKegeDetector = None

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
# 优先 python-docx 版本；失败则回退 win32com 版本（core_modules 已废弃，移除其分支）
try:
    from export_docx_docx import export_docx_document
    print("✅ export_docx_docx 导入成功（python-docx版本）")
except Exception as e:
    print(f"⚠️ export_docx_docx 导入失败: {e}，回退 win32com 版本...")
    try:
        from export_docx import export_docx_document
        print("✅ export_docx 导入成功（win32com版本）")
    except Exception as e3:
        print(f"❌ export_docx 导入失败: {e3}")
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
    # 通义千问 API Key — 从环境变量读取
    import os as _os
    from dotenv import load_dotenv as _load_dotenv
    _load_dotenv()
    QWEN_API_KEY = _os.environ.get("QWEN_API_KEY", "")
    DS_API_KEY = _os.environ.get("DEEPSEEK_API_KEY", "")
    if QWEN_API_KEY:
        AIEvaluation_Instance = AIEvaluation(enable_ai=True, api_key=QWEN_API_KEY)
        print(f"✅ AI评价: 通义千问已启用")
    elif DS_API_KEY:
        AIEvaluation_Instance = AIEvaluation(enable_ai=True, api_key="")
        print(f"✅ AI评价: DeepSeek已启用（QWEN未配）")
    else:
        AIEvaluation_Instance = AIEvaluation(enable_ai=False)
        print(f"⚠️ AI评价: 未配置密钥（QWEN或DeepSeek任一即可）")
except Exception as e:
    print(f"❌ ai_evaluation 导入失败: {e}")
    AIEvaluation_Instance = None

# ==================== 导入传统六壬引擎 ====================
try:
    from liuren_traditional_engine import LiurenTraditionalEngine
    print("✅ liuren_traditional_engine 导入成功")
    TraditionalLiurenEngine_Instance = LiurenTraditionalEngine()
except Exception as e:
    print(f"❌ liuren_traditional_engine 导入失败: {e}")
    TraditionalLiurenEngine_Instance = None

try:
    from liuren_auto_learner import LiurenAutoLearner
    print("✅ liuren_auto_learner 导入成功")
    AutoLearner_Instance = LiurenAutoLearner()
    # 尝试加载已有知识库
    try:
        AutoLearner_Instance.load_knowledge()
        print("✅ 知识库加载成功")
    except Exception as ek:
        print(f"⚠️ 知识库加载失败（首次运行）: {ek}")
except Exception as e:
    print(f"❌ liuren_auto_learner 导入失败: {e}")
    AutoLearner_Instance = None

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
    return send_from_directory('.', 'index_v2.html')

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
            'SiKeSanChuanCalculator2': SiKeSanChuanCalculator2 is not None,
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
    mubiao_kege_bonus = {}

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

    if mubiao:
        doushou_patterns = doushou_result.get('课格格局', [])
        doushou_pattern_str = ' '.join(doushou_patterns) if doushou_patterns else ''

        sizhu = daliuren_result or {}
        day_zhu = sizhu.get('日柱', '')

        for m in mubiao:
            mubiao_kege_bonus[m] = 0

            if m == '求官':
                if '禄马' in doushou_pattern_str or '禄马齐发' in doushou_pattern_str:
                    matched.append('求官')
                    mubiao_kege_bonus[m] = 30
                elif luma_guiren_info.get('ri_qualified', False) and luma_guiren_info.get('qualified_count', 0) >= 2:
                    matched.append('求官')
                    mubiao_kege_bonus[m] = 20
                elif '元辰' in doushou_pattern_str:
                    matched.append('求官')
                    mubiao_kege_bonus[m] = 10

            elif m == '求财':
                if '武财' in doushou_pattern_str:
                    matched.append('求财')
                    mubiao_kege_bonus[m] = 30
                elif '元辰' in doushou_pattern_str:
                    matched.append('求财')
                    mubiao_kege_bonus[m] = 20
                elif luma_guiren_info.get('qualified_count', 0) >= 2:
                    matched.append('求财')
                    mubiao_kege_bonus[m] = 10

            elif m == '求富贵':
                if '禄马齐发' in doushou_pattern_str or '全元联曜' in doushou_pattern_str:
                    matched.append('求富贵')
                    mubiao_kege_bonus[m] = 30
                elif yidu_score_result.get('综合评分', 0) >= 40:
                    matched.append('求富贵')
                    mubiao_kege_bonus[m] = 20
                elif luma_guiren_info.get('qualified_count', 0) >= 3:
                    matched.append('求富贵')
                    mubiao_kege_bonus[m] = 15

            elif m == '求子':
                if '天喜' in doushou_pattern_str or '红鸾' in doushou_pattern_str:
                    matched.append('求子')
                    mubiao_kege_bonus[m] = 30
                elif '廉贞' in doushou_pattern_str or '廉子' in doushou_pattern_str:
                    matched.append('求子')
                    mubiao_kege_bonus[m] = 20
                elif yidu_score_result.get('综合评分', 0) >= 30:
                    matched.append('求子')
                    mubiao_kege_bonus[m] = 10

            elif m == '求学问' or m == '求文昌':
                if '文昌' in doushou_pattern_str or '朱雀' in doushou_pattern_str or '科第' in doushou_pattern_str:
                    matched.append('求学问')
                    mubiao_kege_bonus[m] = 30
                elif '华盖' in doushou_pattern_str:
                    matched.append('求学问')
                    mubiao_kege_bonus[m] = 20
                elif yidu_score_result.get('综合评分', 0) >= 30:
                    matched.append('求学问')
                    mubiao_kege_bonus[m] = 10

            elif m == '求婚姻':
                if '红鸾' in doushou_pattern_str or '天喜' in doushou_pattern_str:
                    matched.append('求婚姻')
                    mubiao_kege_bonus[m] = 30
                elif '武财' in doushou_pattern_str:
                    matched.append('求婚姻')
                    mubiao_kege_bonus[m] = 20
                elif yidu_score_result.get('综合评分', 0) >= 30:
                    matched.append('求婚姻')
                    mubiao_kege_bonus[m] = 10

        bonus = sum(mubiao_kege_bonus.values())

    return bonus, matched, yidu_score_result

@app.route('/api/doushou/full_range_analyze', methods=['POST'])
def doushou_full_range_analyze():
    """完整日期范围分析 - 使用测试成功的逻辑

    ⚠️ 已废弃（2026-08-17 理顺标注）：旧版内联天地盘/节气实现，与 engine 版并行。
    生产前端走 :5555 stock_dashboard.py 的 /api/zeri/batch（sike_sanchuan 排盘 + 完整引擎管线）。
    本路由保留仅为兼容历史调用，新开发请勿复用。
    """
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
        sike_calc = SiKeSanChuanCalculator2()
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
                    sanchuan = sike_calc.fa_sanchuan(sike, ri_gan, ri_zhi, tiandi_pan, shichen)
                    keti = sanchuan.get('课体', '')
                    daliuren_keti = keti

                    # 特殊课格检测（玄胎/铸印/斫轮/盘珠等，仅供前端显示，不赋吉凶）
                    _kege_list = []
                    _kr = {}
                    if SanchuanKegeDetector:
                        try:
                            _sc = [sanchuan.get('初传', ''), sanchuan.get('中传', ''), sanchuan.get('末传', '')]
                            _det = SanchuanKegeDetector()
                            _kr = _det.detect(_sc, ri_gan=ri_gan, ri_zhi=ri_zhi, keti_raw=keti)
                            _kege_list = _kr.get('课格列表', [])
                            if _kege_list:
                                daliuren_keti = (keti + ' · ' if keti else '') + ' · '.join(_kege_list)
                        except Exception as _e:
                            print(f"特殊课格检测失败(comprehensive_score)：{_e}")

                    # 课经评分
                    keti_name = keti.replace('课', '') if keti else ''
                    kejing_score = kejing_scorer.calculate_score(keti_name) * 10
                    
                    daliuren_detail = {
                        '课体': keti,
                        '课格列表': _kege_list,
                        '课格详情': _kr.get('课格详情', {}) if isinstance(_kr, dict) else {},
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

                    # 调试：记录所有课体和评分
                    if total_shichen < 5:
                        log_print(f"  {date_str} {shichen}: 课体={keti}, 六壬评分={daliuren_score}, 大凶={is_daxiong}, 斗首={doushou_score}, 演禽={yanqin_score}")

                    # 不再完全排除大凶课，而是降低其分数
                    # if is_daxiong:
                    #     continue

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
                            'doushou_keti': _extract_doushou_keti(doushou_result),
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
        
        if SiKeSanChuanCalculator2 is None:
            return jsonify({'error': 'sike_sanchuan_engine 未加载'}), 500
        
        calculator = SiKeSanChuanCalculator2()
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
    """计算大六壬（P1：停用 DaLiuRenEngine 起课，统一到 V2 起课引擎）"""
    try:
        year = int(request.args.get('year', 2026))
        month = int(request.args.get('month', 1))
        day = int(request.args.get('day', 1))
        hour = int(request.args.get('hour', 12))
        
        if SiKeSanChuanCalculator2 is None:
            return jsonify({'error': 'sike_sanchuan_engine(V2) 未加载'}), 500
        
        engine = SiKeSanChuanCalculator2()
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
    """导出 DOCX 文档

    ⚠️ 已废弃（2026-08-17 理顺标注）：本服务为旧版（:8000/:5000），生产前端 stock_dashboard.html
    只走 :5555 stock_dashboard.py 的 /api/export/docx（吉期表格版）。本路由保留仅为兼容历史调用，
    新开发请勿复用；后续可整体移除。
    """
    try:
        data = request.json

        print("=" * 80)
        print("📄 收到导出请求")
        print(f"📄 请求数据: {data}")
        print("=" * 80)

        if not DOCX_AVAILABLE:
            return jsonify({'error': 'python-docx 未安装'}), 500

        # 直接使用内联逻辑
        result = inline_export_docx(data)

        if result.get('success') == False:
            return jsonify({'error': result.get('error', '导出失败')}), 500

        filename = result.get('filename')
        file_path = result.get('file_path')

        if not filename or not file_path:
            return jsonify({'error': '导出失败：未生成文件'}), 500

        if not os.path.exists(file_path):
            return jsonify({'error': f'文件不存在: {file_path}'}), 500

        return send_from_directory(
            os.path.dirname(file_path),
            filename,
            as_attachment=True
        )
    except Exception as e:
        print(f"❌ 导出文档失败：{e}")
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


def inline_export_docx(data):
    """内联导出函数 - 直接生成docx文档"""
    try:
        basic = data.get('basic', {})
        mountain = data.get('mountain', {})
        sizhu = data.get('sizhu', {})
        doushou = data.get('doushou', {})
        liuren = data.get('liuren', {})
        luma = data.get('luma', {})

        doc = Document()

        year_pillar = sizhu.get('year', '') or ''
        month_pillar = sizhu.get('month', '') or ''
        day_pillar = sizhu.get('day', '') or ''
        hour_pillar = sizhu.get('hour', '') or ''

        def format_pillar(p):
            if not p:
                return ''
            if len(p) >= 2 and p[1] in ['年', '月', '日', '时']:
                return p[:2]
            return p

        year_str = format_pillar(year_pillar)
        month_str = format_pillar(month_pillar)
        day_str = format_pillar(day_pillar)
        hour_str = format_pillar(hour_pillar)
        sizhu_str = f"{year_str}年{month_str}月{day_str}日{hour_str}时"

        zuoshan = mountain.get('name', '') or mountain.get('display', '') or ''
        doushou_keti = doushou.get('keti', '') or ''

        daliuren_keti = ''
        if isinstance(liuren, dict):
            daliuren_keti = liuren.get('keti', '') or liuren.get('课体', '')

        patterns = doushou.get('patterns', [])
        if isinstance(patterns, str):
            patterns = [patterns]
        pattern_str = ' '.join(patterns) if patterns else ''

        if '武财' in pattern_str:
            peiyu = '日柱武财入命，财源广进，宜求财创业。'
        elif '元辰' in pattern_str:
            peiyu = '元辰旺相，诸事大吉，阴阳和畅，福泽绵绵。'
        elif '贪官' in pattern_str:
            peiyu = '贪官临命，须防小人，宜守不宜攻。'
        elif '破鬼' in pattern_str:
            peiyu = '破鬼耗泄，宜静不宜动，谨慎行事。'
        elif '廉贞' in pattern_str:
            peiyu = '廉贞入命，需防刑伤，择日调理可化解。'
        else:
            peiyu = '课格平和，无大凶之象，可斟酌使用。'

        xianming = f"{year_str}年" if year_str else '待定'

        # 标题
        title_para = doc.add_paragraph()
        title_para.alignment = 1  # CENTER
        title_run = title_para.add_run('仪度六壬择日课单')
        title_run.font.size = 24
        title_run.bold = True

        # 开篇语
        opening = doc.add_paragraph()
        opening.alignment = 2  # RIGHT
        opening.add_run('伏以，天地定位，山向合机；理气相通，福泽攸关。谨奉《穿山透地真传》之旨，依《仪度六壬选日要诀》之法，为孝眷择取吉期，安妥先灵，庇荫后昆。')

        # 仙命
        doc.add_paragraph(f'仙命：{xianming}')

        # 山向
        doc.add_paragraph(f'山向：{zuoshan}')

        # 来龙
        doc.add_paragraph(f'来龙：待定')

        # 四柱
        doc.add_paragraph(f'择取岁次{sizhu_str}')

        # 六壬课格
        keti_info = doushou_keti
        if daliuren_keti:
            keti_info = f"{doushou_keti} / {daliuren_keti}" if doushou_keti else daliuren_keti
        if not keti_info:
            keti_info = '待定'
        doc.add_paragraph(f'六壬课格：{keti_info}')

        # 批语
        doc.add_paragraph(f'批语：{peiyu}')

        # 避忌
        doc.add_paragraph(f'避忌事宜：无重大避忌')

        # 地理师
        sig_para = doc.add_paragraph()
        sig_para.alignment = 2  # RIGHT
        sig_para.add_run('仪度六壬沐手谨择')

        # 日期
        date_para = doc.add_paragraph()
        date_para.alignment = 2  # RIGHT
        current_date = datetime.now().strftime('%Y年%m月%d日')
        date_para.add_run(f'日期：岁次{current_date}榖旦 勒石')

        filename = f'仪度六壬_{datetime.now().strftime("%Y%m%d_%H%M%S")}.docx'
        file_path = os.path.join(os.path.expanduser('~'), filename)
        doc.save(file_path)

        return {'success': True, 'filename': filename, 'file_path': file_path}

    except Exception as e:
        import traceback
        traceback.print_exc()
        return {'success': False, 'error': str(e)}


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
        print(f"📌 坐山: {data.get('mountain', '未提供')}")
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

@app.route('/api/ai/zhanshi_judge', methods=['POST'])
def zhanshi_judge():
    """AI占事智能判断"""
    try:
        data = request.json

        # 提取参数
        sizhu = data.get('sizhu', '')  # 四柱
        sike = data.get('sike', '')  # 四课
        sanchuan = data.get('sanchuan', '')  # 三传
        keti = data.get('keti', '')  # 课体
        zhanshi = data.get('zhanshi', '')  # 占事类型
        stock_code = data.get('stock_code', '')  # 股票代码（股市占事）

        print(f"🔮 AI占事判断API调用")
        print(f"📌 四柱: {sizhu}")
        print(f"📌 四课: {sike}")
        print(f"📌 三传: {sanchuan}")
        print(f"📌 课体: {keti}")
        print(f"📌 占事: {zhanshi}")
        if stock_code:
            print(f"📌 股票代码: {stock_code}")

        # 调用AI判断
        from engine.liuren_ai_judge import LiuRenAIJudge
        judge = LiuRenAIJudge()

        result = judge.quick_judge(
            sizhu=sizhu,
            sike=sike,
            sanchuan=sanchuan,
            keti=keti,
            zhanshi=zhanshi,
            stock_code=stock_code
        )

        print(f"📌 AI判断结果长度: {len(result) if result else 0}")

        return jsonify({
            'success': True,
            'result': result,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        print(f"❌ AI占事判断失败: {e}")
        traceback.print_exc()
        return jsonify({'error': str(e), 'success': False}), 500

@app.route('/api/training/query', methods=['GET'])
def query_training_cases():
    """查询训练案例"""
    try:
        zhanshi = request.args.get('zhanshi', '')
        limit = int(request.args.get('limit', 5))

        print(f"🔍 查询训练案例: 占事={zhanshi}, 限制={limit}")

        from engine.liuren_training_knowledge import LiuRenTrainingKnowledge
        kb = LiuRenTrainingKnowledge()

        if zhanshi:
            cases = kb.query_by_zhanshi(zhanshi)
        else:
            cases = kb.query_similar_cases(limit=limit)

        cases = cases[:limit]

        # 简化返回
        simple_cases = []
        for case in cases:
            simple_cases.append({
                'id': case.get('id', ''),
                '占事': case.get('占事', ''),
                '实际事情': case.get('实际事情', '')[:200] if case.get('实际事情') else '',
                '预测事情': case.get('预测事情', '')[:200] if case.get('预测事情') else ''
            })

        return jsonify({
            'success': True,
            'cases': simple_cases,
            'total': len(simple_cases)
        })
    except Exception as e:
        print(f"❌ 查询训练案例失败: {e}")
        traceback.print_exc()
        return jsonify({'error': str(e), 'success': False}), 500

@app.route('/api/training/stats', methods=['GET'])
def get_training_stats():
    """获取训练统计"""
    try:
        from engine.liuren_training_knowledge import LiuRenTrainingKnowledge
        kb = LiuRenTrainingKnowledge()
        stats = kb.get_statistics()

        return jsonify({
            'success': True,
            'stats': stats
        })
    except Exception as e:
        print(f"❌ 获取训练统计失败: {e}")
        traceback.print_exc()
        return jsonify({'error': str(e), 'success': False}), 500

@app.route('/api/liuren/signal', methods=['GET'])
def liuren_signal():
    """轻量级六壬大盘信号接口（供聚宽/米筐等外部量化平台调用）

    返回今日最新的六壬预测信号，包含吉凶/趋势/置信度/仓位建议。
    聚宽策略在 before_trading 中调用此接口决定当日仓位。
    """
    try:
        from datetime import date as _date
        import json as _json
        memory_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '_memory')
        preds_file = os.path.join(memory_dir, 'stock_predictions.json')
        preds = []
        if os.path.exists(preds_file):
            with open(preds_file, 'r', encoding='utf-8') as f:
                preds = _json.load(f)
        today = _date.today().isoformat()

        # 查找今日最新的预测记录
        today_pred = None
        for d in reversed(preds):
            pt = d.get('predict_time', '') or d.get('target_date', '')
            if pt.startswith(today):
                today_pred = d
                break

        if not today_pred:
            # 没有今日预测，返回中性信号
            return jsonify({
                'success': True,
                'has_signal': False,
                'message': '今日暂无六壬预测，默认中平半仓',
                'date': today,
                'jixiong': '中平',
                'trend_prediction': '震荡',
                'confidence': 0.5,
                'suggested_position': 0.5,
            })

        jixiong = (today_pred.get('jixiong') or '').strip()
        trend = (today_pred.get('trend_prediction') or '').strip()
        confidence = today_pred.get('confidence', 0.5)
        if not isinstance(confidence, (int, float)):
            confidence = 0.5

        # 仓位决策矩阵
        if jixiong == '吉' and confidence >= 0.6:
            suggested_position = 1.0
        elif jixiong == '吉' and confidence >= 0.5:
            suggested_position = 0.8
        elif jixiong == '中平':
            suggested_position = 0.5
        elif jixiong == '凶' and confidence >= 0.6:
            suggested_position = 0.0
        else:
            suggested_position = 0.3

        return jsonify({
            'success': True,
            'has_signal': True,
            'date': today,
            'jixiong': jixiong or '中平',
            'trend_prediction': trend or '震荡',
            'confidence': round(confidence, 3),
            'suggested_position': suggested_position,
            'category': today_pred.get('category', ''),
            'analysis': today_pred.get('analysis', '')[:200],  # 截断分析文本
        })
    except Exception as e:
        print(f"❌ 六壬信号接口失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'has_signal': False,
            'jixiong': '中平',
            'suggested_position': 0.5,
        }), 500


@app.route('/api/stock/search', methods=['GET'])
def stock_search():
    """搜索股票代码"""
    try:
        keyword = request.args.get('keyword', '')
        if not keyword:
            return jsonify({'success': False, 'error': '请提供搜索关键词'}), 400

        from engine.stock_analyzer import StockAnalyzer
        sa = StockAnalyzer()
        results = sa.search_stock(keyword)

        return jsonify({
            'success': True,
            'results': results
        })
    except Exception as e:
        print(f"❌ 股票搜索失败: {e}")
        return jsonify({'error': str(e), 'success': False}), 500


@app.route('/api/stock/quote', methods=['GET'])
def stock_quote():
    """获取股票实时行情"""
    try:
        code = request.args.get('code', '000001')
        name = request.args.get('name', '')

        from engine.stock_analyzer import StockAnalyzer
        sa = StockAnalyzer()
        quote = sa.get_realtime_quote(code)

        if not quote:
            return jsonify({'success': False, 'error': '未找到该股票'}), 404

        return jsonify({
            'success': True,
            'quote': quote
        })
    except Exception as e:
        print(f"❌ 获取股票行情失败: {e}")
        return jsonify({'error': str(e), 'success': False}), 500


@app.route('/api/stock/market', methods=['GET'])
def stock_market():
    """获取大盘指数行情（上证/深证等）"""
    try:
        from engine.stock_analyzer import StockAnalyzer
        sa = StockAnalyzer()
        overview = sa.get_market_overview()

        return jsonify({
            'success': True,
            'market': overview
        })
    except Exception as e:
        print(f"❌ 获取大盘行情失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/multi_stock', methods=['GET'])
def multi_stock_predictions():
    """获取大六壬一课多断最新预测结果

    读取 _memory/multi_stock_*.json 中最新的文件，
    返回 predictions 数组（含 symbol/name/trend/jixiong/confidence/analysis）。
    """
    try:
        from pathlib import Path
        memory_dir = Path(os.path.dirname(os.path.abspath(__file__))) / '_memory'
        # 列出所有 multi_stock_*.json 并按文件名（含时间戳）降序取最新
        files = sorted(memory_dir.glob('multi_stock_*.json'), reverse=True)
        if not files:
            return jsonify({
                'success': True,
                'date': None,
                'predictions': [],
                'message': '暂无大六壬一课多断预测记录'
            })

        import json as _json
        latest_file = files[0]
        with open(latest_file, 'r', encoding='utf-8') as f:
            data = _json.load(f)

        preds = data.get('predictions', [])
        # 统一字段，便于前端使用
        normalized = []
        for p in preds:
            normalized.append({
                'symbol': p.get('symbol', ''),
                'name': p.get('name', ''),
                'trend': p.get('trend', '?'),
                'jixiong': p.get('jixiong', '?'),
                'confidence': float(p.get('confidence', 0) or 0),
                'analysis': p.get('analysis', ''),
            })

        return jsonify({
            'success': True,
            'date': data.get('date', ''),
            'rizhu': data.get('rizhu', ''),
            'shichen': data.get('shichen', ''),
            'file': latest_file.name,
            'predictions': normalized
        })
    except Exception as e:
        print(f"❌ 获取大六壬一课多断预测失败: {e}")
        return jsonify({'success': False, 'error': str(e), 'predictions': []}), 500


@app.route('/api/ip/location', methods=['GET'])
def ip_location():
    """根据客户端 IP 获取地理位置（优先 IPIP.net 精确到地级市/州）"""
    try:
        import urllib.request
        import json
        import re

        client_ip = request.remote_addr or ''
        log_print(f"📍 IP定位请求: {client_ip}")

        use_ip = client_ip
        if not use_ip or use_ip in ('127.0.0.1', '::1', '::ffff:127.0.0.1'):
            use_ip = ''
            log_print("  → 本地请求，使用服务端公网IP查询")

        # ====== 主要数据源: IPIP.net（国内最精确，返回省/市/州级）======
        location_name = ''
        ip_found = ''
        isp_found = ''

        try:
            ipip_req = urllib.request.Request(
                'https://myip.ipip.net',
                headers={'User-Agent': 'Mozilla/5.0'},
            )
            ipip_resp = urllib.request.urlopen(ipip_req, timeout=8)
            ipip_text = ipip_resp.read().decode('utf-8', errors='replace').strip()

            match = re.search(r'来自于：(.+)', ipip_text)
            if match:
                parts = [p.strip() for p in match.group(1).split() if p.strip()]
                if parts:
                    location_name = ' '.join(parts)
                    log_print(f"  → IPIP.net: {location_name}")
                    ip_match = re.search(r'IP：(\S+)', ipip_text)
                    if ip_match:
                        ip_found = ip_match.group(1)
                    if len(parts) > 1:
                        isp_found = parts[-1] if len(parts) >= 2 else ''
        except Exception as e:
            log_print(f"  → IPIP.net 不可用: {e}")

        # ====== 辅助数据源: ip-api.com（提供坐标）======
        lat, lon = 0, 120
        country_en = ''

        try:
            api_req = urllib.request.Request(
                f"http://ip-api.com/json/{use_ip}?fields=status,country,lat,lon",
                headers={'User-Agent': 'Mozilla/5.0'},
            )
            api_resp = urllib.request.urlopen(api_req, timeout=5)
            api_data = json.loads(api_resp.read().decode('utf-8'))

            if api_data.get('status') == 'success':
                lat = api_data.get('lat', 0)
                lon = api_data.get('lon', 0)
                country_en = api_data.get('country', '')
                log_print(f"  → ip-api.com 坐标: {lat}, {lon}°E")
            else:
                log_print(f"  → ip-api.com 返回失败")
        except Exception as e:
            log_print(f"  → ip-api.com 不可用: {e}")

        result = {
            'success': True,
            'ip': ip_found or '',
            'location': location_name or country_en or '未知',
            'isp': isp_found,
            'latitude': lat,
            'longitude': lon,
        }
        log_print(f"  → 定位结果: {result.get('location')} ({lon}°E)")
        return jsonify(result)

    except Exception as e:
        log_print(f"❌ IP定位失败: {e}")
        return jsonify({'success': False, 'longitude': 120, 'location': '默认(东八区)'})


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

# ==================== 增强版六壬分析 API ====================

@app.route('/api/liuren/enhanced_analysis', methods=['POST'])
def liuren_enhanced_analysis():
    """增强版六壬分析（类象分析 + 应期判断）"""
    try:
        data = request.json
        
        print("🔮 增强版六壬分析请求")
        print(f"   占事类别: {data.get('category', '')}")
        print(f"   日干: {data.get('dayGan', '')}, 日支: {data.get('dayZhi', '')}")
        
        # 提取求测人信息
        qiuceren_info = data.get('qiucerenInfo', {})
        print(f"   求测人: {qiuceren_info.get('gender', '')} {qiuceren_info.get('age', '')}岁 {qiuceren_info.get('occupation', '')}")
        
        # 调用增强版占卜系统
        from enhanced_divination import EnhancedDivination
        
        # 构建查询信息
        query_info = {
            'ri_gan': data.get('dayGan', ''),
            'ri_zhi': data.get('dayZhi', ''),
            'year': '',
            'month': '',
            'date': '',
            'time': '',
            'yue_jiang': '',
            'question': data.get('category', ''),
            'gender': qiuceren_info.get('gender', ''),
            'age': qiuceren_info.get('age', 0),
            'occupation': qiuceren_info.get('occupation', ''),
            'residence': qiuceren_info.get('residence', ''),
            'era': qiuceren_info.get('era', '')
        }
        
        # 处理四课数据
        si_ke = []
        siKe_data = data.get('siKe', {})
        for i in ['ke1', 'ke2', 'ke3', 'ke4']:
            ke = siKe_data.get(i, {})
            if ke:
                si_ke.append({
                    'top': ke.get('top', '') or ke.get('shangGan', '') or ke.get('tianGan', ''),
                    'bottom': ke.get('bottom', '') or ke.get('xiaGan', '') or ke.get('diGan', '')
                })
        
        # 处理三传数据
        san_chuan = []
        sanChuan_data = data.get('sanChuan', {})
        tianJiang_data = data.get('sanChuanTianJiang', [])
        for i, chuan_name in enumerate(['chuChuan', 'zhongChuan', 'moChuan']):
            zhi = sanChuan_data.get(chuan_name, '')
            if zhi:
                san_chuan.append({
                    'zhi': zhi,
                    'tian_jiang': tianJiang_data[i] if i < len(tianJiang_data) else ''
                })
        
        # 创建增强版占卜实例
        diviner = EnhancedDivination(query_info)
        diviner.set_paipan(None, si_ke, san_chuan)
        result = diviner.analyze()
        
        return jsonify({
            'success': True,
            'data': {
                'qiucerenInfo': qiuceren_info,
                'classifications': result.get('classifications', {}),
                'yingqi': result.get('yingqi', {})
            },
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        print(f"❌ 增强版六壬分析失败: {e}")
        traceback.print_exc()
        return jsonify({'error': str(e), 'success': False}), 500

# ==================== 传统六壬引擎API端点 ====================

@app.route('/api/liuren/traditional/analyze', methods=['POST'])
def liuren_traditional_analyze():
    """传统六壬完整分析"""
    try:
        data = request.json
        
        if TraditionalLiurenEngine_Instance is None:
            return jsonify({'error': 'TraditionalLiurenEngine 未加载'}), 500
        
        print("🔮 传统六壬分析请求")
        
        # 构建分析数据
        analysis_data = {
            'ri_gan': data.get('ri_gan', data.get('dayGan', '')),
            'ri_zhi': data.get('ri_zhi', data.get('dayZhi', '')),
            'sanchuan': data.get('sanchuan', []),
            'si_ke': data.get('si_ke', []),
            'question': data.get('question', data.get('category', '')),
            'gender': data.get('gender', ''),
            'occupation': data.get('occupation', ''),
            'age': data.get('age', 0),
            'ke_ti': data.get('ke_ti', data.get('keti', ''))
        }
        
        # 从增强的前端数据中提取四课
        if not analysis_data['si_ke'] and 'siKe' in data:
            si_ke_list = []
            siKe_data = data.get('siKe', {})
            for i in ['ke1', 'ke2', 'ke3', 'ke4']:
                ke = siKe_data.get(i, {})
                if ke:
                    si_ke_list.append({
                        'top': ke.get('top', '') or ke.get('shangGan', '') or ke.get('tianGan', ''),
                        'bottom': ke.get('bottom', '') or ke.get('xiaGan', '') or ke.get('diGan', '')
                    })
            analysis_data['si_ke'] = si_ke_list
        
        # 从增强的前端数据中提取三传
        if not analysis_data['sanchuan'] and 'sanChuan' in data:
            san_chuan_list = []
            sanChuan_data = data.get('sanChuan', {})
            for chuan_name in ['chuChuan', 'zhongChuan', 'moChuan']:
                zhi = sanChuan_data.get(chuan_name, '')
                if zhi:
                    san_chuan_list.append(zhi)
            analysis_data['sanchuan'] = san_chuan_list
        
        # 从求测人信息中提取
        if 'qiucerenInfo' in data:
            qiuceren_info = data.get('qiucerenInfo', {})
            analysis_data['gender'] = analysis_data.get('gender', qiuceren_info.get('gender', ''))
            analysis_data['age'] = analysis_data.get('age', qiuceren_info.get('age', 0))
            analysis_data['occupation'] = analysis_data.get('occupation', qiuceren_info.get('occupation', ''))
        
        print(f"📌 分析数据:")
        print(f"   日干: {analysis_data['ri_gan']}, 日支: {analysis_data['ri_zhi']}")
        print(f"   三传: {analysis_data['sanchuan']}")
        print(f"   四课数量: {len(analysis_data['si_ke'])}")
        print(f"   占事: {analysis_data['question']}")
        print(f"   求测人: {analysis_data['gender']} {analysis_data['age']}岁 {analysis_data['occupation']}")
        
        # 调用传统六壬引擎
        result = TraditionalLiurenEngine_Instance.full_traditional_analysis(analysis_data)
        
        print(f"✅ 传统六壬分析完成")
        
        return jsonify({
            'success': True,
            'result': result,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        print(f"❌ 传统六壬分析失败: {e}")
        traceback.print_exc()
        return jsonify({'error': str(e), 'success': False}), 500

@app.route('/api/liuren/traditional/yingqi', methods=['POST'])
def liuren_traditional_yingqi():
    """传统六壬应期分析"""
    try:
        data = request.json
        
        if TraditionalLiurenEngine_Instance is None:
            return jsonify({'error': 'TraditionalLiurenEngine 未加载'}), 500
        
        sanchuan = data.get('sanchuan', [])
        ri_gan = data.get('ri_gan', data.get('dayGan', ''))
        ri_zhi = data.get('ri_zhi', data.get('dayZhi', ''))
        age = data.get('age', 0)
        
        # 从增强的前端数据中提取三传
        if not sanchuan and 'sanChuan' in data:
            sanChuan_data = data.get('sanChuan', {})
            sanchuan = [
                sanChuan_data.get('chuChuan', ''),
                sanChuan_data.get('zhongChuan', ''),
                sanChuan_data.get('moChuan', '')
            ]
            sanchuan = [z for z in sanchuan if z]
        
        result = TraditionalLiurenEngine_Instance.calculate_yingqi(sanchuan, ri_gan, ri_zhi, age)
        
        return jsonify({
            'success': True,
            'yingqi': result,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        print(f"❌ 传统六壬应期分析失败: {e}")
        traceback.print_exc()
        return jsonify({'error': str(e), 'success': False}), 500

@app.route('/api/liuren/auto_learner/learn', methods=['POST'])
def liuren_learner_learn():
    """自动学习器 - 学习案例"""
    try:
        data = request.json
        
        if AutoLearner_Instance is None:
            return jsonify({'error': 'AutoLearner 未加载'}), 500
        
        case = data.get('case', {})
        ai_analysis = data.get('ai_analysis', {})
        
        AutoLearner_Instance.learn_from_case(case, ai_analysis)
        AutoLearner_Instance.save_knowledge()
        
        return jsonify({
            'success': True,
            'message': '学习完成，知识库已保存',
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        print(f"❌ 自动学习失败: {e}")
        traceback.print_exc()
        return jsonify({'error': str(e), 'success': False}), 500

@app.route('/api/liuren/auto_learner/apply', methods=['POST'])
def liuren_learner_apply():
    """自动学习器 - 应用知识"""
    try:
        data = request.json
        
        if AutoLearner_Instance is None:
            return jsonify({'error': 'AutoLearner 未加载'}), 500
        
        result = AutoLearner_Instance.apply_knowledge(data)
        
        return jsonify({
            'success': True,
            'result': result,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        print(f"❌ 应用知识失败: {e}")
        traceback.print_exc()
        return jsonify({'error': str(e), 'success': False}), 500

# ==================== 混合推理系统API端点 ====================

# 初始化混合推理系统
try:
    from hybrid_reasoning_system_simple import HybridAPIHandler
    print("✅ 混合推理系统加载成功")
    HybridHandler = HybridAPIHandler()
except Exception as e:
    print(f"⚠️  混合推理系统加载失败: {e}")
    HybridHandler = None

@app.route('/api/liuren/hybrid/analyze', methods=['POST'])
def liuren_hybrid_analyze():
    """混合推理系统 - 完整分析"""
    try:
        if HybridHandler is None:
            return jsonify({'error': '混合推理系统未加载', 'success': False}), 500
        
        data = request.json
        print("🔮 混合推理分析请求")
        
        result = HybridHandler.handle_analysis_request(data)
        
        return jsonify(result)
        
    except Exception as e:
        print(f"❌ 混合推理分析失败: {e}")
        traceback.print_exc()
        return jsonify({'error': str(e), 'success': False}), 500

# ==================== P3: 按占事生成断语（2026-08-18）====================

@app.route('/api/liuren/zhanshi_duanyu', methods=['POST'])
def liuren_zhanshi_duanyu():
    """按具体占事生成六壬断语（解决一刀切）。

    body: {
      category: 'marriage' 或 zhanshi: '婚姻'（前端 13 类英文键，见 CATEGORY_MAP）,
      dayGan/dayZhi 或 year/month/day/hour（缺省时后端推导）,
      yuejiang/shichen 可选（缺省按日期推导）
    }
    返回: {success, data: {zhanshi, paipan, level, keti_duanyu, zhanshi_duanyu, bifa_duanyu, summary}}
    """
    try:
        data = request.json or {}
        category = data.get('category', '')
        zhanshi = data.get('zhanshi', '')
        zishu = data.get('zishu', '')  # 家宅子类：阳宅/阴宅/迁移（可选，缺省自动识别）
        ri_gan = data.get('dayGan', '') or data.get('ri_gan', '')
        ri_zhi = data.get('dayZhi', '') or data.get('ri_zhi', '')
        yuejiang = data.get('yuejiang', '')
        shichen = data.get('shichen', '')

        year = int(data.get('year', 0) or 0)
        month = int(data.get('month', 0) or 0)
        day = int(data.get('day', 0) or 0)
        hour = int(data.get('hour', 12) or 12)

        # 时辰映射（与 /api/sizhu 同口径）
        if not shichen:
            _sc_map = {23:'子',0:'子',1:'丑',2:'丑',3:'寅',4:'寅',5:'卯',6:'卯',7:'辰',8:'辰',
                       9:'巳',10:'巳',11:'午',12:'午',13:'未',14:'未',15:'申',16:'申',
                       17:'酉',18:'酉',19:'戌',20:'戌',21:'亥',22:'亥'}
            shichen = _sc_map.get(hour, '午')

        # 缺月将 → 中气精确口径
        if not yuejiang and year and month and day:
            try:
                from engine.daliuren_luma_guiren import DaLiuRenLuMaGuiRen
                yuejiang = DaLiuRenLuMaGuiRen().get_yuejiang_by_date(year, month, day)
            except Exception:
                yuejiang = ''

        # 缺日柱 → sizhu_engine 推导
        if (not ri_gan or not ri_zhi) and year and month and day:
            if get_sizhu is not None:
                sr = get_sizhu(year, month, day, shichen)
                if not ri_gan:
                    ri_gan = (sr.get('日柱', '') or '')[:1]
                if not ri_zhi:
                    ri_zhi = (sr.get('日柱', '') or '')[1:]

        if not (ri_gan and ri_zhi and yuejiang and shichen):
            return jsonify({'error': '排盘参数不完整（需 dayGan/dayZhi/yuejiang/shichen，或 year/month/day/hour）', 'success': False}), 400

        from engine.zhanshi_duanyu import generate, classify_zhaimu_sub
        # 家宅子类：显式 zishu 优先；缺省按占事描述自动识别（category==house 或 zhanshi==家宅 时）
        _zishu_eff = zishu
        if not _zishu_eff and (category in ('house',) or zhanshi == '家宅'):
            _zishu_eff = classify_zhaimu_sub(str(data.get('question', '')) + str(data.get('shishi', '')))
        result = generate(ri_gan, ri_zhi, yuejiang, shichen, zhanshi=zhanshi, category=category, zishu=_zishu_eff)
        if _zishu_eff:
            result['zishu'] = _zishu_eff
        return jsonify({'success': True, 'data': result})

    except Exception as e:
        print(f"❌ 占事断语生成失败: {e}")
        traceback.print_exc()
        return jsonify({'error': str(e), 'success': False}), 500


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
    app.run(host='0.0.0.0', port=8000, debug=False, threaded=True)

if __name__ == '__main__':
    start_server()
