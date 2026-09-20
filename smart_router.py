"""Smart-Router: 智能题型路由 — 适配暑假守护项目"""
import re
import logging

logger = logging.getLogger(__name__)


class QuestionTypeRouter:
    """智能答案提取器：根据题型规范化学生答案"""

    _EXTRACTORS = {
        'choice': '_extract_choice',
        'judge': '_extract_judge',
        'fill': '_extract_fill',
        'reading': '_extract_reading',
        'sentence': '_extract_sentence',
        'composition': '_extract_composition',
        'writing': '_extract_composition',
        'true_false': '_extract_judge',
    }

    _JUDGE_CORRECT_SET = {'√', '✓', '✔', '对', '正确', 'T', 'true', 'True', 'v', 'V'}
    _JUDGE_WRONG_SET = {'×', '✗', '✘', '错', '错误', 'F', 'false', 'False', 'x', 'X'}

    @classmethod
    def extract(cls, raw_answer, question_type, standard_answer=None, question_index_in_area=None):
        """根据题型提取标准化答案"""
        if not raw_answer or not raw_answer.strip():
            return raw_answer or ''
        extractor_name = cls._EXTRACTORS.get(question_type, '_extract_default')
        extractor = getattr(cls, extractor_name)
        result = extractor(raw_answer, standard_answer, question_index_in_area=question_index_in_area)
        if result != raw_answer and result:
            logger.debug(f'[ROUTER] {question_type}: "{str(raw_answer)[:40]}" → "{str(result)[:40]}"')
        return result

    @classmethod
    def _extract_choice(cls, raw_answer, standard_answer=None, question_index_in_area=None):
        """选择题：提取 A/B/C/D"""
        cleaned = raw_answer.strip()
        if len(cleaned) <= 3 and cleaned.isalpha() and all(c.isascii() for c in cleaned):
            return cleaned.upper()
        matches = re.findall(r'[A-Da-d]', raw_answer)
        if matches:
            if question_index_in_area is not None and 0 <= question_index_in_area < len(matches):
                return matches[question_index_in_area].upper()
            return matches[0].upper()
        return cleaned

    @classmethod
    def _extract_judge(cls, raw_answer, standard_answer=None, question_index_in_area=None):
        """判断题：提取 √/×"""
        cleaned = raw_answer.strip()
        if cleaned in ('√', '×'):
            return cleaned
        if len(cleaned) <= 2:
            if cleaned in cls._JUDGE_CORRECT_SET:
                return '√'
            if cleaned in cls._JUDGE_WRONG_SET:
                return '×'
            return cleaned

        found = []
        for char in raw_answer:
            if char in cls._JUDGE_CORRECT_SET:
                found.append('√')
            elif char in cls._JUDGE_WRONG_SET:
                found.append('×')
        if found:
            if question_index_in_area is not None and 0 <= question_index_in_area < len(found):
                return found[question_index_in_area]
            if len(found) == 1:
                return found[0]
            return ''.join(found)

        cn_correct = re.findall(r'对|正确|是对的', raw_answer)
        cn_wrong = re.findall(r'错|错误|是不对的', raw_answer)
        if cn_correct and not cn_wrong:
            return '√'
        if cn_wrong and not cn_correct:
            return '×'

        return cleaned

    @classmethod
    def _extract_fill(cls, raw_answer, standard_answer=None, question_index_in_area=None):
        """填空题：处理混合题型（填空+选择）"""
        if standard_answer:
            _is_mixed = cls._is_mixed_fill_choice(standard_answer)
            if _is_mixed:
                _parts = cls._split_mixed_answer(raw_answer, standard_answer)
                if len(_parts) > 1:
                    _idx = question_index_in_area if question_index_in_area is not None else 0
                    if _idx < len(_parts):
                        return _parts[_idx]
        return raw_answer.strip()

    @classmethod
    def _is_mixed_fill_choice(cls, standard_answer):
        if not standard_answer:
            return False
        _std_parts = re.split(r'[；;]', standard_answer)
        if len(_std_parts) < 2:
            return False
        for p in _std_parts:
            p_clean = re.sub(r'[（()）\d]', '', p).strip()
            if p_clean and len(p_clean) <= 5 and re.match(r'^[A-Da-d]$', p_clean):
                return True
        return False

    @classmethod
    def _split_mixed_answer(cls, raw_answer, standard_answer):
        _std_parts = re.split(r'[；;]', standard_answer)
        _choice_letters = re.findall(r'[A-Da-d]', raw_answer)
        if not _choice_letters:
            return [raw_answer.strip()]
        _fill_part = raw_answer
        for _m in re.finditer(r'[A-Da-d]', raw_answer):
            _pos = _m.start()
            _after = raw_answer[_pos + 1:].strip()
            _before = raw_answer[:_pos].rstrip('；;，,、\n\r ')
            if not _after or _after.startswith('）') or _after.startswith(')'):
                _fill_part = _before
                break
        _results = [_fill_part.strip()]
        for _cl in _choice_letters:
            _results.append(_cl.upper())
        return _results

    @classmethod
    def _extract_reading(cls, raw_answer, standard_answer=None, question_index_in_area=None):
        return raw_answer.strip()

    @classmethod
    def _extract_sentence(cls, raw_answer, standard_answer=None, question_index_in_area=None):
        return raw_answer.strip()

    @classmethod
    def _extract_composition(cls, raw_answer, standard_answer=None, question_index_in_area=None):
        return raw_answer.strip()

    @classmethod
    def _extract_default(cls, raw_answer, standard_answer=None, question_index_in_area=None):
        return raw_answer.strip()

    # ===== 智能题型检测 =====
    @classmethod
    def detect_question_type(cls, question_text, standard_answer):
        """根据题目内容和标准答案自动推断题型"""
        # 选择题：标准答案是单个字母
        if isinstance(standard_answer, str) and standard_answer.upper() in ('A', 'B', 'C', 'D'):
            return 'choice'

        # 判断题：标准答案是判断符号
        if standard_answer in ('√', '×', '正确', '错误', '对', '错'):
            return 'judge'

        # 数学题：含数学符号
        if isinstance(standard_answer, str) and re.search(r'[\d+\-×÷=]', standard_answer):
            if any(kw in question_text for kw in ['比较', '____', '（）', '(', ')', '>', '<', '=']):
                return 'fill'

        # 阅读题
        if any(kw in question_text for kw in ['阅读理解', '阅读', '根据短文', '根据文章']):
            return 'reading'

        # 看图写话/作文
        if any(kw in question_text for kw in ['看图写话', '作文', '写一写', '写一段']):
            return 'composition'

        return 'fill'

    @classmethod
    def normalize_answer(cls, question_type, student_answer, standard_answer):
        """一键规范化：检测题型 + 提取答案 + 标准化"""
        if not question_type or question_type == 'unknown':
            question_type = cls.detect_question_type('', standard_answer)
        extracted = cls.extract(student_answer, question_type, standard_answer)
        return question_type, extracted


question_type_router = QuestionTypeRouter()


# ===== 股票预测任务路由 =====
import os, json, subprocess, sys

BASE = os.path.dirname(os.path.abspath(__file__))
MEMORY = os.path.join(BASE, '_memory')

ROUTES = {
    'liuren': {
        'keywords': ['六壬','排盘','大六壬','课式','吉凶','占一课','预测明天','明天涨跌','走势','起课','三传','四课'],
        'module': 'stock_daily_predict.py',
        'desc': '六壬排盘预测'
    },
    'ml': {
        'keywords': ['ML','机器学习','技术分析','特征','模型','集成','HGB','RandomForest'],
        'module': 'ml_stock_predict.py',
        'desc': 'ML集成预测'
    },
    'market': {
        'keywords': ['行情','上证','指数','收盘','大盘','同花顺','akshare'],
        'module': 'market_news.py',
        'desc': '实时行情采集'
    },
    'report': {
        'keywords': ['日报','报表','周报','统计','推送','通知'],
        'module': 'stock_report_generator.py',
        'desc': '报表生成+推送'
    },
    'compare': {
        'keywords': ['对比','比较','准确率','谁准','对照','六壬vsML'],
        'module': 'tech_analysis_predict.py',
        'desc': '六壬vsML对比'
    },
    'schedule': {
        'keywords': ['调度','定时','自动','守护','运行','启动'],
        'module': 'auto_scheduler.py',
        'desc': '调度系统'
    },
    'screen': {
        'keywords': ['选股','股票池','排行榜','推荐','TOP'],
        'module': 'stock_screener.py',
        'desc': '量化选股'
    },
    'dashboard': {
        'keywords': ['仪表盘','页面','前端','显示','dashboard'],
        'module': 'stock_dashboard.py',
        'desc': '仪表盘'
    },
    'evolve': {
        'keywords': ['训练','自进化','复盘','纠正','学习'],
        'module': 'self_evolve.py',
        'desc': '自进化训练'
    }
}

class StockTaskRouter:
    """智能预测任务路由"""
    
    @classmethod
    def route(cls, user_query: str) -> tuple:
        """根据用户问题返回任务类型和模块"""
        query = user_query.lower()
        scores = {}
        for task, cfg in ROUTES.items():
            score = 0
            for kw in cfg['keywords']:
                if kw in query:
                    score += 1
            if score > 0:
                scores[task] = score
        if not scores:
            return ('unknown', 'stock_daily_predict.py')
        best = max(scores, key=scores.get)
        return (best, ROUTES[best]['module'], ROUTES[best]['desc'])
    
    @classmethod
    def execute(cls, task_type: str, *args) -> dict:
        """执行路由到的模块"""
        if task_type not in ROUTES:
            return {'error': f'未知任务: {task_type}'}
        
        module = ROUTES[task_type]['module']
        full_path = os.path.join(BASE, module)
        
        if not os.path.exists(full_path):
            return {'error': f'模块不存在: {full_path}'}
        
        try:
            result = subprocess.run(
                [sys.executable, full_path] + list(args),
                capture_output=True, text=True, cwd=BASE,
                encoding='utf-8', errors='replace', timeout=120
            )
            return {
                'task': task_type,
                'module': module,
                'success': result.returncode == 0,
                'output': result.stdout[:2000],
                'error': result.stderr[:500]
            }
        except Exception as e:
            return {'error': str(e)}
    
    @classmethod
    def status(cls) -> dict:
        """获取所有模块状态"""
        status = {}
        for task, cfg in ROUTES.items():
            module_path = os.path.join(BASE, cfg['module'])
            status[task] = {
                'module': cfg['module'],
                'desc': cfg['desc'],
                'exists': os.path.exists(module_path)
            }
        # 检查调度器和仪表盘
        try:
            import socket
            s = socket.socket()
            s.settimeout(1)
            result = s.connect_ex(('127.0.0.1', 5556))
            s.close()
            status['dashboard']['running'] = (result == 0)
        except:
            status['dashboard']['running'] = False
        
        return status


stock_task_router = StockTaskRouter()